import argparse
import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

try:
    import requests
except ImportError:
    print("缺少requests库，请先安装：pip install requests")
    sys.exit(1)

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    from prettytable import PrettyTable
except ImportError:
    print("缺少prettytable库，请先安装：pip install prettytable")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BinanceGridSuitabilityScreener:
    """
    币安合约网格交易适配筛选器

    筛选适合网格交易的交易对，评估标准:
    - 价格在网格区间内的震荡频率（越频繁越好）
    - 历史价格在网格范围内的停留比例
    - 波动率是否匹配网格间距（太低不触发, 太高容易穿透）
    - 成交量/流动性是否充足

    网格参数:
    - 上限 = 当前价 × grid_upper_ratio (默认 1.2)
    - 下限 = 当前价 × grid_lower_ratio (默认 0.6)
    - 网格数量 = grid_count (默认 80, 等差)
    - 每格利润率 = (upper - lower) / grid_count / current_price
    """

    FAPI_BASE = "https://fapi.binance.com"

    # 评分权重
    DEFAULT_WEIGHTS = {
        "oscillation": 0.30,       # 震荡频率
        "range_containment": 0.25, # 区间停留比例
        "volatility_fitness": 0.25,# 波动率匹配度
        "volume": 0.20,            # 成交量/流动性
    }

    MIN_REQUEST_INTERVAL = 0.1

    def __init__(
            self,
            grid_upper_ratio: float = 1.2,
            grid_lower_ratio: float = 0.6,
            grid_count: int = 80,
            min_volume_usd: float = 5_000_000,
            days_analysis: int = 90,
            max_workers: int = 5
    ):
        self.grid_upper_ratio = grid_upper_ratio
        self.grid_lower_ratio = grid_lower_ratio
        self.grid_count = grid_count
        self.min_volume_usd = min_volume_usd
        self.days_analysis = days_analysis
        self.max_workers = max_workers
        self.weights = self.DEFAULT_WEIGHTS
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BinanceGridSuitabilityScreener/1.0'
        })

        # 缓存
        self.klines_cache = {}
        self.last_request_time = 0

    # ──────────────────────────────────────────────
    # 请求工具
    # ──────────────────────────────────────────────

    def _rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.MIN_REQUEST_INTERVAL:
            time.sleep(self.MIN_REQUEST_INTERVAL - elapsed)
        self.last_request_time = time.time()

    def _safe_request(self, url: str, params: dict = None, timeout: int = 10) -> Optional[dict]:
        max_tries = 3
        for attempt in range(max_tries):
            try:
                self._rate_limit()
                response = self.session.get(url, params=params, timeout=timeout)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 5))
                    logger.warning(f"Rate limit hit. Retrying after {retry_after}s")
                    time.sleep(retry_after)
                    continue
                elif response.status_code >= 500:
                    logger.warning(f"Server error {response.status_code}, attempt {attempt + 1}")
                    if attempt < max_tries - 1:
                        time.sleep(2 ** attempt)
                        continue
                else:
                    logger.error(f"Request failed: {response.status_code}")
                    return None
            except requests.Timeout:
                logger.warning(f"Timeout for {url}, attempt {attempt + 1}")
                if attempt < max_tries - 1:
                    time.sleep(2 ** attempt)
                    continue
            except requests.RequestException as e:
                logger.error(f"Request error: {e}")
                if attempt < max_tries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return None
        return None

    # ──────────────────────────────────────────────
    # 数据获取
    # ──────────────────────────────────────────────

    def fetch_futures_exchange_info(self) -> List[Dict]:
        data = self._safe_request(f"{self.FAPI_BASE}/fapi/v1/exchangeInfo")
        if not data:
            return []
        return [
            s for s in data.get("symbols", [])
            if s.get("status") == "TRADING"
            and s.get("contractType") == "PERPETUAL"
            and s.get("quoteAsset") == "USDT"
        ]

    def fetch_futures_tickers(self) -> Dict[str, Dict]:
        data = self._safe_request(f"{self.FAPI_BASE}/fapi/v1/ticker/24hr")
        return {item['symbol']: item for item in data} if data else {}

    def get_klines(self, symbol: str, interval: str = "1d") -> Optional[List[List]]:
        cache_key = (symbol, interval)
        if cache_key not in self.klines_cache:
            data = self._safe_request(
                f"{self.FAPI_BASE}/fapi/v1/klines",
                params={
                    "symbol": symbol,
                    "interval": interval,
                    "limit": self.days_analysis
                }
            )
            self.klines_cache[cache_key] = data
        return self.klines_cache[cache_key]

    # ──────────────────────────────────────────────
    # 网格参数计算
    # ──────────────────────────────────────────────

    def get_grid_params(self, current_price: float) -> Dict:
        """计算网格参数"""
        upper = current_price * self.grid_upper_ratio
        lower = current_price * self.grid_lower_ratio
        spacing = (upper - lower) / self.grid_count
        spacing_pct = spacing / current_price * 100
        return {
            "upper": upper,
            "lower": lower,
            "spacing": spacing,
            "spacing_pct": round(spacing_pct, 4),
            "grid_count": self.grid_count,
        }

    # ──────────────────────────────────────────────
    # 指标计算
    # ──────────────────────────────────────────────

    def calculate_oscillation_score(self, klines: List[List]) -> Dict:
        """
        震荡频率评分: 价格方向频繁反转说明适合网格。
        统计日线收盘价的方向变化次数 / 总天数。
        同时统计价格穿越中线(网格中点)的次数。
        """
        if not klines or len(klines) < 10:
            return {"score": 0.0, "direction_changes": 0, "midline_crosses": 0,
                    "change_ratio": 0.0}

        closes = [float(k[4]) for k in klines]
        current_price = closes[-1]
        midline = current_price * (self.grid_upper_ratio + self.grid_lower_ratio) / 2

        # 方向反转次数
        direction_changes = 0
        for i in range(2, len(closes)):
            prev_dir = closes[i - 1] - closes[i - 2]
            curr_dir = closes[i] - closes[i - 1]
            if prev_dir * curr_dir < 0:  # 方向改变
                direction_changes += 1

        change_ratio = direction_changes / (len(closes) - 2) if len(closes) > 2 else 0

        # 中线穿越次数
        midline_crosses = 0
        for i in range(1, len(closes)):
            if (closes[i - 1] < midline and closes[i] >= midline) or \
               (closes[i - 1] >= midline and closes[i] < midline):
                midline_crosses += 1

        # 评分: change_ratio 越接近0.5越好（完美震荡），越接近0或1越差
        # 0.3-0.6 是最佳范围
        if 0.35 <= change_ratio <= 0.55:
            score = 1.0
        elif 0.25 <= change_ratio <= 0.65:
            score = 0.7
        elif 0.15 <= change_ratio <= 0.75:
            score = 0.4
        else:
            score = 0.1

        # 中线穿越加分（穿越越多越好）
        cross_per_month = midline_crosses / max(1, len(closes) / 30)
        if cross_per_month >= 4:
            score = min(1.0, score + 0.15)
        elif cross_per_month >= 2:
            score = min(1.0, score + 0.05)

        return {
            "score": round(score, 3),
            "direction_changes": direction_changes,
            "midline_crosses": midline_crosses,
            "change_ratio": round(change_ratio, 3),
        }

    def calculate_range_containment_score(self, klines: List[List]) -> Dict:
        """
        区间停留评分: 历史价格在网格区间 [0.6x, 1.2x] 内停留的比例。
        用每根K线的 high/low 判断是否完全在区间内。
        """
        if not klines or len(klines) < 10:
            return {"score": 0.0, "in_range_pct": 0.0, "bars_in_range": 0,
                    "total_bars": 0, "max_excursion_pct": 0.0}

        closes = [float(k[4]) for k in klines]
        current_price = closes[-1]
        upper = current_price * self.grid_upper_ratio
        lower = current_price * self.grid_lower_ratio

        bars_in_range = 0
        bars_partial = 0  # K线部分在区间内
        max_high = 0
        min_low = float('inf')

        for k in klines:
            h = float(k[2])
            l = float(k[3])
            max_high = max(max_high, h)
            min_low = min(min_low, l)

            if l >= lower and h <= upper:
                bars_in_range += 1
            elif l <= upper and h >= lower:
                bars_partial += 1

        total_bars = len(klines)
        in_range_pct = bars_in_range / total_bars
        partial_pct = (bars_in_range + bars_partial) / total_bars

        # 最大偏离幅度
        max_excursion_up = (max_high - current_price) / current_price * 100
        max_excursion_down = (current_price - min_low) / current_price * 100
        max_excursion_pct = max(max_excursion_up, max_excursion_down)

        # 评分: 以完全在区间内的比例为主，部分在区间内的补充
        score = in_range_pct * 0.7 + partial_pct * 0.3

        return {
            "score": round(min(1.0, score), 3),
            "in_range_pct": round(in_range_pct * 100, 1),
            "bars_in_range": bars_in_range,
            "total_bars": total_bars,
            "max_excursion_pct": round(max_excursion_pct, 1),
        }

    def calculate_volatility_fitness_score(self, klines: List[List]) -> Dict:
        """
        波动率匹配度评分: 日波动率(ATR%)是否匹配网格间距。
        网格间距 = (1.2 - 0.6) / 80 = 0.75% of current price
        理想日ATR在 1-5% 之间 (每天触发1-7格)
        太低(<0.5%): 网格很少触发
        太高(>10%): 容易快速穿透整个网格
        """
        if not klines or len(klines) < 10:
            return {"score": 0.0, "atr_pct": 0.0, "daily_range_pct": 0.0,
                    "est_daily_grids": 0.0}

        closes = [float(k[4]) for k in klines]
        highs = [float(k[2]) for k in klines]
        lows = [float(k[3]) for k in klines]
        current_price = closes[-1]

        # 计算ATR(14) 百分比
        trs = []
        for i in range(1, len(klines)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1])
            )
            trs.append(tr)

        atr = sum(trs[-14:]) / min(14, len(trs[-14:])) if trs else 0
        atr_pct = (atr / current_price * 100) if current_price > 0 else 0

        # 平均日内振幅
        daily_ranges = [(highs[i] - lows[i]) / closes[i] * 100
                        for i in range(len(klines)) if closes[i] > 0]
        daily_range_pct = sum(daily_ranges) / len(daily_ranges) if daily_ranges else 0

        # 网格间距百分比
        grid_spacing_pct = (self.grid_upper_ratio - self.grid_lower_ratio) / self.grid_count * 100

        # 预估每日触发网格数
        est_daily_grids = atr_pct / grid_spacing_pct if grid_spacing_pct > 0 else 0

        # 评分: ATR% 在合适范围内得高分
        # 甜蜜区: 1.5%-6% (每天触发2-8格)
        if 1.5 <= atr_pct <= 6.0:
            score = 1.0
        elif 1.0 <= atr_pct <= 8.0:
            score = 0.7
        elif 0.5 <= atr_pct <= 12.0:
            score = 0.4
        elif atr_pct < 0.5:
            score = 0.1  # 波动太低，网格难以触发
        else:
            score = 0.2  # 波动过高，风险大

        return {
            "score": round(score, 3),
            "atr_pct": round(atr_pct, 2),
            "daily_range_pct": round(daily_range_pct, 2),
            "est_daily_grids": round(est_daily_grids, 1),
        }

    def calculate_volume_score(self, quote_vol: float) -> Dict:
        """
        成交量评分: 成交量越大，网格单越容易成交。
        """
        if quote_vol <= 0:
            return {"score": 0.0, "vol_usd": 0.0}

        if quote_vol >= 100_000_000:     # 1亿+
            score = 1.0
        elif quote_vol >= 50_000_000:    # 5千万+
            score = 0.8
        elif quote_vol >= 20_000_000:    # 2千万+
            score = 0.6
        elif quote_vol >= 10_000_000:    # 1千万+
            score = 0.4
        elif quote_vol >= 5_000_000:     # 500万+
            score = 0.2
        else:
            score = 0.1

        return {
            "score": round(score, 3),
            "vol_usd": quote_vol,
        }

    # ──────────────────────────────────────────────
    # 单对分析
    # ──────────────────────────────────────────────

    def analyze_single_pair(self, symbol: str, ticker: Dict) -> Optional[Dict]:
        """分析单个交易对的网格交易适配度"""
        try:
            quote_vol = float(ticker.get("quoteVolume", 0))
            if quote_vol < self.min_volume_usd:
                return None

            current_price = float(ticker.get("lastPrice", 0))
            if current_price <= 0:
                return None

            klines = self.get_klines(symbol, "1d")
            if not klines or len(klines) < 20:
                return None

            # 计算各项指标
            osc = self.calculate_oscillation_score(klines)
            rng = self.calculate_range_containment_score(klines)
            vol_fit = self.calculate_volatility_fitness_score(klines)
            vol_score = self.calculate_volume_score(quote_vol)

            # 加权综合评分
            composite = (
                osc["score"] * self.weights["oscillation"] +
                rng["score"] * self.weights["range_containment"] +
                vol_fit["score"] * self.weights["volatility_fitness"] +
                vol_score["score"] * self.weights["volume"]
            )

            # 网格参数
            grid_params = self.get_grid_params(current_price)

            price_change_pct = float(ticker.get("priceChangePercent", 0))

            return {
                "symbol": symbol,
                "composite_score": round(composite, 4),
                "current_price": current_price,
                "price_change_pct": round(price_change_pct, 2),
                "vol_usd_24h": quote_vol,
                "grid": grid_params,
                "details": {
                    "oscillation": osc,
                    "range_containment": rng,
                    "volatility_fitness": vol_fit,
                    "volume": vol_score,
                },
            }

        except Exception as e:
            logger.debug(f"Error analyzing {symbol}: {e}")
            return None

    # ──────────────────────────────────────────────
    # 扫描入口
    # ──────────────────────────────────────────────

    def scan(self, top_n: int = 20, min_score: float = 0.1) -> List[Dict]:
        """扫描所有USDT永续合约，返回最适合网格交易的交易对"""
        logger.info("正在获取市场数据...")

        tickers = self.fetch_futures_tickers()
        if not tickers:
            logger.error("获取行情数据失败")
            return []

        symbol_info = self.fetch_futures_exchange_info()
        if not symbol_info:
            logger.error("获取交易对信息失败")
            return []

        target_symbols = [s['symbol'] for s in symbol_info]
        logger.info(f"共 {len(target_symbols)} 个USDT永续合约，开始网格适配分析...")

        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_symbol = {
                executor.submit(self.analyze_single_pair, symbol, tickers.get(symbol, {})): symbol
                for symbol in target_symbols if symbol in tickers
            }

            for i, future in enumerate(as_completed(future_to_symbol)):
                symbol = future_to_symbol[future]
                try:
                    result = future.result()
                    if result and result['composite_score'] >= min_score:
                        results.append(result)

                    if (i + 1) % 50 == 0:
                        logger.info(f"进度: {i + 1}/{len(target_symbols)}")

                except Exception as e:
                    logger.error(f"处理 {symbol} 时出错: {e}")

        results.sort(key=lambda x: x['composite_score'], reverse=True)
        return results[:top_n]

    # ──────────────────────────────────────────────
    # 结果输出
    # ──────────────────────────────────────────────

    def print_results_table(self, results: List[Dict]):
        if not results:
            print("没有找到符合条件的网格交易对。")
            return

        grid_spacing_pct = (self.grid_upper_ratio - self.grid_lower_ratio) / self.grid_count * 100

        print(f"\n{'=' * 130}")
        print(f" 币安USDT永续合约 - 网格交易适配筛选 TOP {len(results)}")
        print(f"{'=' * 130}")
        print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"网格参数: 上限={self.grid_upper_ratio:.1f}x | "
              f"下限={self.grid_lower_ratio:.1f}x | "
              f"格数={self.grid_count} (等差) | "
              f"每格≈{grid_spacing_pct:.2f}%")
        print(f"分析周期: {self.days_analysis}天日线")
        print(f"评分权重: 震荡={self.weights['oscillation']:.0%}, "
              f"区间={self.weights['range_containment']:.0%}, "
              f"波动匹配={self.weights['volatility_fitness']:.0%}, "
              f"流动性={self.weights['volume']:.0%}")

        table = PrettyTable()
        table.field_names = [
            "排名", "交易对", "综合评分",
            "当前价", "24h成交额(USD)",
            "震荡分", "区间%", "ATR%", "预估日格数",
            "网格上限", "网格下限",
        ]

        table.align = "l"
        table.align["排名"] = "c"
        table.align["综合评分"] = "c"
        table.align["当前价"] = "r"
        table.align["24h成交额(USD)"] = "r"
        table.align["震荡分"] = "c"
        table.align["区间%"] = "c"
        table.align["ATR%"] = "c"
        table.align["预估日格数"] = "c"
        table.align["网格上限"] = "r"
        table.align["网格下限"] = "r"

        for i, pair in enumerate(results, 1):
            d = pair["details"]
            g = pair["grid"]

            if pair['composite_score'] > 0.7:
                level = "🟢"  # 非常适合
            elif pair['composite_score'] > 0.5:
                level = "🟡"  # 较适合
            else:
                level = "🔴"  # 一般

            table.add_row([
                i,
                f"{level} {pair['symbol']}",
                f"{pair['composite_score']:.4f}",
                f"{pair['current_price']:.4f}",
                f"{pair['vol_usd_24h']:,.0f}",
                f"{d['oscillation']['score']:.2f}",
                f"{d['range_containment']['in_range_pct']:.0f}%",
                f"{d['volatility_fitness']['atr_pct']:.1f}%",
                f"{d['volatility_fitness']['est_daily_grids']:.1f}",
                f"{g['upper']:.4f}",
                f"{g['lower']:.4f}",
            ])

        print(table)

        print(f"\n适配度: 🟢 优(>0.7) 🟡 良(>0.5) 🔴 一般(≤0.5)")
        print(f"震荡分: 方向反转频率, 越接近0.5越震荡 | 区间%: 日K在网格区间内的比例")
        print(f"ATR%: 14日平均真实波幅占比, 1.5%-6%为甜蜜区 | 预估日格数: 每天预估触发的网格数")

    def export_results(self, results: List[Dict], fmt: str = "json") -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if fmt == "json":
            filename = f"grid_suitability_{timestamp}.json"
            export_data = []
            for r in results:
                d = r["details"]
                g = r["grid"]
                export_data.append({
                    "symbol": r["symbol"],
                    "composite_score": r["composite_score"],
                    "current_price": r["current_price"],
                    "price_change_pct": r["price_change_pct"],
                    "vol_usd_24h": r["vol_usd_24h"],
                    "grid_upper": g["upper"],
                    "grid_lower": g["lower"],
                    "grid_spacing_pct": g["spacing_pct"],
                    "oscillation_score": d["oscillation"]["score"],
                    "direction_changes": d["oscillation"]["direction_changes"],
                    "midline_crosses": d["oscillation"]["midline_crosses"],
                    "range_containment_pct": d["range_containment"]["in_range_pct"],
                    "atr_pct": d["volatility_fitness"]["atr_pct"],
                    "est_daily_grids": d["volatility_fitness"]["est_daily_grids"],
                    "volume_score": d["volume"]["score"],
                })
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

        elif fmt == "csv" and pd is not None:
            filename = f"grid_suitability_{timestamp}.csv"
            rows = []
            for r in results:
                d = r["details"]
                g = r["grid"]
                rows.append({
                    "symbol": r["symbol"],
                    "composite_score": r["composite_score"],
                    "current_price": r["current_price"],
                    "vol_usd_24h": r["vol_usd_24h"],
                    "grid_upper": g["upper"],
                    "grid_lower": g["lower"],
                    "grid_spacing_pct": g["spacing_pct"],
                    "oscillation_score": d["oscillation"]["score"],
                    "range_containment_pct": d["range_containment"]["in_range_pct"],
                    "atr_pct": d["volatility_fitness"]["atr_pct"],
                    "est_daily_grids": d["volatility_fitness"]["est_daily_grids"],
                    "volume_score": d["volume"]["score"],
                })
            df = pd.DataFrame(rows)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
        else:
            return ""

        return filename

    def save_to_database(self, results: List[Dict], db_path: str = "grid_suitability.db"):
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS grid_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    symbol TEXT,
                    composite_score REAL,
                    current_price REAL,
                    vol_usd_24h REAL,
                    grid_upper REAL,
                    grid_lower REAL,
                    grid_spacing_pct REAL,
                    oscillation_score REAL,
                    range_containment_pct REAL,
                    atr_pct REAL,
                    est_daily_grids REAL,
                    volume_score REAL
                )
            ''')

            ts = datetime.now().isoformat()
            for r in results:
                d = r["details"]
                g = r["grid"]
                cursor.execute('''
                    INSERT INTO grid_records
                    (timestamp, symbol, composite_score, current_price, vol_usd_24h,
                     grid_upper, grid_lower, grid_spacing_pct,
                     oscillation_score, range_containment_pct, atr_pct,
                     est_daily_grids, volume_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    ts, r["symbol"], r["composite_score"], r["current_price"],
                    r["vol_usd_24h"], g["upper"], g["lower"], g["spacing_pct"],
                    d["oscillation"]["score"],
                    d["range_containment"]["in_range_pct"],
                    d["volatility_fitness"]["atr_pct"],
                    d["volatility_fitness"]["est_daily_grids"],
                    d["volume"]["score"],
                ))

            conn.commit()
            conn.close()
            logger.info(f"结果已保存到数据库: {db_path}")
        except Exception as e:
            logger.error(f"保存数据库失败: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="币安USDT永续合约网格交易适配筛选器 - 筛选最适合网格交易的交易对",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python test_grid_suitability.py                              # 默认筛选前20个
  python test_grid_suitability.py --top 10                     # 显示前10个
  python test_grid_suitability.py --upper 1.3 --lower 0.5      # 自定义网格范围
  python test_grid_suitability.py --grids 100                  # 100格
  python test_grid_suitability.py --days 60                    # 分析最近60天
  python test_grid_suitability.py --export json --db           # 导出JSON并存库

网格参数:
  默认: 上限=当前价×1.2, 下限=当前价×0.6, 80格等差
  每格利润率 = (上限-下限)/格数/当前价 ≈ 0.75%

评分逻辑:
  震荡频率(30%): 价格方向反转越频繁越适合网格
  区间停留(25%): 历史价格在网格范围内停留比例越高越好
  波动匹配(25%): ATR%在1.5-6%的甜蜜区得高分
  流动性(20%):  24h成交额越大，网格单越容易成交
        """
    )
    parser.add_argument("--top", type=int, default=20,
                        help="显示前N个结果 (default: 20)")
    parser.add_argument("--upper", type=float, default=1.2,
                        help="网格上限比例 (default: 1.2)")
    parser.add_argument("--lower", type=float, default=0.6,
                        help="网格下限比例 (default: 0.6)")
    parser.add_argument("--grids", type=int, default=80,
                        help="网格数量 (default: 80)")
    parser.add_argument("--min-vol", type=float, default=5_000_000,
                        help="最低24h成交额(USD) (default: 5,000,000)")
    parser.add_argument("--days", type=int, default=90,
                        help="分析的日线天数 (default: 90)")
    parser.add_argument("--workers", type=int, default=5,
                        help="最大并发线程数 (default: 5)")
    parser.add_argument("--min-score", type=float, default=0.1,
                        help="最低综合评分阈值 (default: 0.1)")
    parser.add_argument("--export", choices=["json", "csv", "none"], default="none",
                        help="导出格式 (default: none)")
    parser.add_argument("--db", action="store_true",
                        help="保存结果到SQLite数据库")

    args = parser.parse_args()

    screener = BinanceGridSuitabilityScreener(
        grid_upper_ratio=args.upper,
        grid_lower_ratio=args.lower,
        grid_count=args.grids,
        min_volume_usd=args.min_vol,
        days_analysis=args.days,
        max_workers=args.workers
    )

    try:
        print(f"正在扫描币安USDT永续合约网格交易适配度...")
        print(f"网格: 上限={args.upper:.1f}x, 下限={args.lower:.1f}x, {args.grids}格等差")
        results = screener.scan(top_n=args.top, min_score=args.min_score)

        if not results:
            print("没有找到符合条件的网格交易对。")
            return

        screener.print_results_table(results)

        if args.export != "none":
            filename = screener.export_results(results, fmt=args.export)
            if filename:
                print(f"\n结果已导出至: {filename}")

        if args.db:
            screener.save_to_database(results)

    except KeyboardInterrupt:
        print("\n\n程序被用户中断。")
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
        print(f"错误: {e}")


if __name__ == "__main__":
    main()
