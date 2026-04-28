import argparse
import json
import os
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


class BinanceVolumeBreakoutScreener:
    """币安合约放量突破筛选器 - 筛选即将放量突破的交易对，用于网格趋势突破交易"""

    FAPI_BASE = "https://fapi.binance.com"

    TIMEFRAMES = ["1h", "4h", "1d"]
    TIMEFRAME_WEIGHTS = {"1d": 0.50, "4h": 0.30, "1h": 0.20}

    INDICATOR_WEIGHTS = {
        "volume_surge": 0.50,
        "ma_breakout": 0.50,
    }

    MIN_REQUEST_INTERVAL = 0.1  # 100ms between requests

    def __init__(
            self,
            min_volume_usd: float = 5_000_000,
            kline_limit: int = 100,
            max_workers: int = 5
    ):
        self.min_volume_usd = min_volume_usd
        self.kline_limit = kline_limit
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BinanceVolumeBreakoutScreener/1.0'
        })

        # 缓存
        self.klines_cache = {}
        self.last_request_time = 0

    # ──────────────────────────────────────────────
    # 请求工具
    # ──────────────────────────────────────────────

    def _rate_limit(self):
        """控制请求频率"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.MIN_REQUEST_INTERVAL:
            time.sleep(self.MIN_REQUEST_INTERVAL - elapsed)
        self.last_request_time = time.time()

    def _safe_request(self, url: str, params: dict = None, timeout: int = 10) -> Optional[dict]:
        """带重试逻辑的安全请求"""
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
        """获取USDT永续合约交易对信息"""
        data = self._safe_request(f"{self.FAPI_BASE}/fapi/v1/exchangeInfo")
        if not data:
            return []
        symbols = data.get("symbols", [])
        return [
            s for s in symbols
            if s.get("status") == "TRADING"
            and s.get("contractType") == "PERPETUAL"
            and s.get("quoteAsset") == "USDT"
        ]

    def fetch_futures_tickers(self) -> Dict[str, Dict]:
        """获取所有合约交易对的24小时行情"""
        data = self._safe_request(f"{self.FAPI_BASE}/fapi/v1/ticker/24hr")
        return {item['symbol']: item for item in data} if data else {}

    def get_klines(self, symbol: str, interval: str) -> Optional[List[List]]:
        """获取K线数据（带缓存）"""
        cache_key = (symbol, interval)
        if cache_key not in self.klines_cache:
            data = self._safe_request(
                f"{self.FAPI_BASE}/fapi/v1/klines",
                params={
                    "symbol": symbol,
                    "interval": interval,
                    "limit": self.kline_limit
                }
            )
            self.klines_cache[cache_key] = data
        return self.klines_cache[cache_key]

    # ──────────────────────────────────────────────
    # 指标计算
    # ──────────────────────────────────────────────

    def calculate_volume_surge_score(self, klines: List[List]) -> Dict:
        """
        计算放量评分
        K线格式: [open_time, open, high, low, close, volume, close_time, quote_vol, trades, ...]
        volume 在 index 5, quote_asset_volume 在 index 7

        注意: 最后一根K线为未完成的当前bar，成交量不完整，
        因此使用倒数第二根（最后完成的bar）作为"当前成交量"进行比较。
        """
        if not klines or len(klines) < 22:
            return {"score": 0.0, "volume_ratio": 0.0, "avg_volume": 0.0,
                    "current_volume": 0.0, "volume_trending_up": False}

        # 使用 quote asset volume (USDT) 更准确
        volumes = [float(k[7]) for k in klines]

        # 使用最后一根已完成的K线（倒数第2根）作为当前量
        current_volume = volumes[-2]
        # 20周期均量（排除当前bar和未完成bar）
        avg_volume = sum(volumes[-22:-2]) / 20

        if avg_volume <= 0:
            return {"score": 0.0, "volume_ratio": 0.0, "avg_volume": 0.0,
                    "current_volume": current_volume, "volume_trending_up": False}

        volume_ratio = current_volume / avg_volume

        # 5根已完成K线的成交量趋势判断（排除未完成bar）
        recent_5 = volumes[-6:-1]
        volume_trending_up = all(
            recent_5[i] >= recent_5[i - 1] for i in range(1, len(recent_5))
        )

        # 评分
        if volume_ratio >= 5.0:
            score = 1.0
        elif volume_ratio >= 3.0:
            score = 0.8
        elif volume_ratio >= 2.0:
            score = 0.6
        elif volume_ratio >= 1.5:
            score = 0.3
        elif volume_ratio >= 1.0:
            score = 0.1
        else:
            score = 0.0

        # 连续放量趋势加分
        if volume_trending_up:
            score = min(1.0, score + 0.1)

        return {
            "score": round(score, 3),
            "volume_ratio": round(volume_ratio, 2),
            "avg_volume": round(avg_volume, 2),
            "current_volume": round(current_volume, 2),
            "volume_trending_up": volume_trending_up,
        }

    def calculate_ma_breakout_score(self, klines: List[List]) -> Dict:
        """
        计算均线突破评分
        检测价格对 MA7, MA25, MA100 的突破情况及均线排列
        """
        if not klines or len(klines) < 25:
            return {"score": 0.0, "price": 0.0, "ma7": 0.0, "ma25": 0.0,
                    "ma100": 0.0, "above_ma7": False, "above_ma25": False,
                    "above_ma100": False, "bullish_alignment": False,
                    "recent_crossover": "无"}

        closes = [float(k[4]) for k in klines]
        current_price = closes[-1]

        # 计算均线
        ma7 = sum(closes[-7:]) / 7
        ma25 = sum(closes[-25:]) / 25
        ma100 = sum(closes[-100:]) / min(100, len(closes)) if len(closes) >= 25 else ma25

        above_ma7 = current_price > ma7
        above_ma25 = current_price > ma25
        above_ma100 = current_price > ma100

        # ── 子评分1：价格 vs 均线 (权重 0.4) ──
        price_vs_ma_score = 0.0
        if above_ma7:
            price_vs_ma_score += 0.375   # 0.15 / 0.4
        if above_ma25:
            price_vs_ma_score += 0.375
        if above_ma100:
            price_vs_ma_score += 0.25

        # ── 子评分2：近期突破检测 (权重 0.3) ──
        crossover_score = 0.0
        crossovers = []

        # MA7 突破：最近3根K线
        if len(closes) >= 10:
            for i in range(-3, 0):
                prev_close = closes[i - 1]
                curr_close = closes[i]
                prev_ma7 = sum(closes[i - 7:i]) / 7 if abs(i) <= len(closes) - 7 else None
                curr_ma7 = sum(closes[i - 6:i + 1]) / 7 if abs(i) <= len(closes) - 7 else None
                if prev_ma7 and curr_ma7 and prev_close <= prev_ma7 and curr_close > curr_ma7:
                    crossover_score += 0.333
                    crossovers.append("MA7")
                    break

        # MA25 突破：最近3根K线
        if len(closes) >= 30:
            for i in range(-3, 0):
                prev_close = closes[i - 1]
                curr_close = closes[i]
                prev_ma25 = sum(closes[i - 25:i]) / 25 if abs(i) <= len(closes) - 25 else None
                curr_ma25 = sum(closes[i - 24:i + 1]) / 25 if abs(i) <= len(closes) - 25 else None
                if prev_ma25 and curr_ma25 and prev_close <= prev_ma25 and curr_close > curr_ma25:
                    crossover_score += 0.333
                    crossovers.append("MA25")
                    break

        # MA100 突破：最近5根K线
        if len(closes) >= 100:
            for i in range(-5, 0):
                prev_close = closes[i - 1]
                curr_close = closes[i]
                prev_ma100 = sum(closes[i - 100:i]) / 100
                curr_ma100 = sum(closes[i - 99:i + 1]) / 100
                if prev_close <= prev_ma100 and curr_close > curr_ma100:
                    crossover_score += 0.334
                    crossovers.append("MA100")
                    break

        # ── 子评分3：均线排列 (权重 0.3) ──
        # 7>25>100: 完全多头排列
        # 100>7>25: 短期多头但尚未突破长期均线，蓄势待发
        # 7>25:     短期多头
        bullish_alignment = ma7 > ma25 > ma100
        approaching_breakout = ma100 > ma7 > ma25  # 100>7>25
        partial_alignment = ma7 > ma25

        if bullish_alignment:
            alignment_score = 1.0
        elif approaching_breakout:
            alignment_score = 0.6
        elif partial_alignment:
            alignment_score = 0.4
        else:
            alignment_score = 0.0

        # 综合评分
        score = (
            price_vs_ma_score * 0.4 +
            crossover_score * 0.3 +
            alignment_score * 0.3
        )

        crossover_str = "+".join(crossovers) if crossovers else "无"

        return {
            "score": round(score, 3),
            "price": round(current_price, 6),
            "ma7": round(ma7, 6),
            "ma25": round(ma25, 6),
            "ma100": round(ma100, 6),
            "above_ma7": above_ma7,
            "above_ma25": above_ma25,
            "above_ma100": above_ma100,
            "bullish_alignment": bullish_alignment,
            "approaching_breakout": approaching_breakout,
            "partial_alignment": partial_alignment,
            "recent_crossover": crossover_str,
        }

    # ──────────────────────────────────────────────
    # 多周期分析
    # ──────────────────────────────────────────────

    def analyze_single_pair(self, symbol: str, ticker: Dict) -> Optional[Dict]:
        """分析单个交易对的放量突破潜力"""
        try:
            # 预筛选：24h成交额过低的跳过
            quote_vol = float(ticker.get("quoteVolume", 0))
            if quote_vol < self.min_volume_usd:
                return None

            timeframe_details = {}
            timeframe_scores = {}

            for tf in self.TIMEFRAMES:
                klines = self.get_klines(symbol, tf)
                if not klines or len(klines) < 25:
                    timeframe_details[tf] = None
                    timeframe_scores[tf] = 0.0
                    continue

                vol_result = self.calculate_volume_surge_score(klines)
                ma_result = self.calculate_ma_breakout_score(klines)

                tf_score = (
                    vol_result["score"] * self.INDICATOR_WEIGHTS["volume_surge"] +
                    ma_result["score"] * self.INDICATOR_WEIGHTS["ma_breakout"]
                )

                timeframe_details[tf] = {
                    "volume": vol_result,
                    "ma": ma_result,
                    "tf_score": round(tf_score, 4),
                }
                timeframe_scores[tf] = tf_score

            # 加权综合评分
            composite_score = sum(
                timeframe_scores.get(tf, 0.0) * self.TIMEFRAME_WEIGHTS[tf]
                for tf in self.TIMEFRAMES
            )

            # 价格变化
            price_change_pct = float(ticker.get("priceChangePercent", 0))

            # 确定均线状态（优先使用日线信息）
            ma_status = self._get_ma_status(timeframe_details)

            return {
                "symbol": symbol,
                "composite_score": round(composite_score, 4),
                "vol_usd_24h": quote_vol,
                "price_change_pct": round(price_change_pct, 2),
                "ma_status": ma_status,
                "timeframes": timeframe_details,
                "timeframe_scores": timeframe_scores,
            }

        except Exception as e:
            logger.debug(f"Error analyzing {symbol}: {e}")
            return None

    def _get_ma_status(self, timeframe_details: Dict) -> str:
        """从多周期数据中提取均线状态摘要（优先使用日线）"""
        for tf in ["1d", "4h", "1h"]:
            detail = timeframe_details.get(tf)
            if detail and detail.get("ma"):
                ma = detail["ma"]
                if ma["bullish_alignment"]:
                    return "7>25>100"
                if ma.get("approaching_breakout"):
                    return "100>7>25"
                if ma.get("partial_alignment"):
                    return "7>25"
                parts = []
                if ma["above_ma7"]:
                    parts.append("↑7")
                if ma["above_ma25"]:
                    parts.append("↑25")
                if ma["above_ma100"]:
                    parts.append("↑100")
                if parts:
                    return " ".join(parts)
                return "—"
        return "—"

    # ──────────────────────────────────────────────
    # 扫描入口
    # ──────────────────────────────────────────────

    def scan(self, top_n: int = 20, min_score: float = 0.1) -> List[Dict]:
        """扫描所有USDT永续合约，返回放量突破潜力最高的交易对"""
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
        logger.info(f"共 {len(target_symbols)} 个USDT永续合约，开始多周期分析...")

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
        """使用PrettyTable打印格式化的结果表格"""
        if not results:
            print("没有找到符合条件的放量突破交易对。")
            return

        print(f"\n{'=' * 120}")
        print(f" 币安USDT永续合约 - 放量突破筛选 TOP {len(results)}")
        print(f"{'=' * 120}")
        print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"周期权重: 日线={self.TIMEFRAME_WEIGHTS['1d']:.0%}, "
              f"4小时={self.TIMEFRAME_WEIGHTS['4h']:.0%}, "
              f"1小时={self.TIMEFRAME_WEIGHTS['1h']:.0%}")
        print(f"指标权重: 放量={self.INDICATOR_WEIGHTS['volume_surge']:.0%}, "
              f"均线突破={self.INDICATOR_WEIGHTS['ma_breakout']:.0%}")

        table = PrettyTable()
        table.field_names = [
            "排名", "交易对", "综合评分",
            "24h成交额(USD)", "涨跌幅(%)",
            "1d量比", "4h量比", "1h量比",
            "均线状态", "近期突破"
        ]

        table.align = "l"
        table.align["排名"] = "c"
        table.align["综合评分"] = "c"
        table.align["24h成交额(USD)"] = "r"
        table.align["涨跌幅(%)"] = "r"
        table.align["1d量比"] = "c"
        table.align["4h量比"] = "c"
        table.align["1h量比"] = "c"
        table.align["均线状态"] = "c"
        table.align["近期突破"] = "c"

        for i, pair in enumerate(results, 1):
            # 突破强度标记
            if pair['composite_score'] > 0.7:
                level = "🔴"
            elif pair['composite_score'] > 0.4:
                level = "🟡"
            else:
                level = "🟢"

            # 各周期量比
            vol_ratios = {}
            crossovers = []
            for tf in self.TIMEFRAMES:
                detail = pair["timeframes"].get(tf)
                if detail:
                    vol_ratios[tf] = f"{detail['volume']['volume_ratio']:.1f}x"
                    if detail["ma"]["recent_crossover"] != "无":
                        crossovers.append(f"{tf}:{detail['ma']['recent_crossover']}")
                else:
                    vol_ratios[tf] = "—"

            crossover_str = ", ".join(crossovers) if crossovers else "无"

            table.add_row([
                i,
                f"{level} {pair['symbol']}",
                f"{pair['composite_score']:.4f}",
                f"{pair['vol_usd_24h']:,.0f}",
                f"{pair['price_change_pct']:.2f}%",
                vol_ratios.get("1d", "—"),
                vol_ratios.get("4h", "—"),
                vol_ratios.get("1h", "—"),
                pair["ma_status"],
                crossover_str,
            ])

        print(table)

        print(f"\n突破强度: 🔴 强(>0.7) 🟡 中(>0.4) 🟢 弱(≤0.4)")
        print(f"量比 = 当前成交量 / 20周期均量, >2.0x 视为明显放量")
        print(f"均线状态: 7>25>100 = 完全多头排列, 100>7>25 = 短期多头蓄势待突破MA100, 7>25 = 短期多头")

    def export_results(self, results: List[Dict], fmt: str = "json") -> str:
        """导出结果为文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if fmt == "json":
            filename = f"volume_breakout_{timestamp}.json"
            # 简化 timeframes 数据用于导出
            export_data = []
            for r in results:
                item = {
                    "symbol": r["symbol"],
                    "composite_score": r["composite_score"],
                    "vol_usd_24h": r["vol_usd_24h"],
                    "price_change_pct": r["price_change_pct"],
                    "ma_status": r["ma_status"],
                    "timeframe_scores": r["timeframe_scores"],
                }
                for tf in self.TIMEFRAMES:
                    detail = r["timeframes"].get(tf)
                    if detail:
                        item[f"{tf}_volume_ratio"] = detail["volume"]["volume_ratio"]
                        item[f"{tf}_volume_score"] = detail["volume"]["score"]
                        item[f"{tf}_ma_score"] = detail["ma"]["score"]
                        item[f"{tf}_crossover"] = detail["ma"]["recent_crossover"]
                export_data.append(item)

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

        elif fmt == "csv" and pd is not None:
            filename = f"volume_breakout_{timestamp}.csv"
            rows = []
            for r in results:
                row = {
                    "symbol": r["symbol"],
                    "composite_score": r["composite_score"],
                    "vol_usd_24h": r["vol_usd_24h"],
                    "price_change_pct": r["price_change_pct"],
                    "ma_status": r["ma_status"],
                }
                for tf in self.TIMEFRAMES:
                    detail = r["timeframes"].get(tf)
                    if detail:
                        row[f"{tf}_volume_ratio"] = detail["volume"]["volume_ratio"]
                        row[f"{tf}_ma_score"] = detail["ma"]["score"]
                        row[f"{tf}_crossover"] = detail["ma"]["recent_crossover"]
                rows.append(row)
            df = pd.DataFrame(rows)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
        else:
            return ""

        return filename

    def save_to_database(self, results: List[Dict], db_path: str = "volume_breakout.db"):
        """保存结果到SQLite数据库"""
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS breakout_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    symbol TEXT,
                    composite_score REAL,
                    vol_usd_24h REAL,
                    price_change_pct REAL,
                    ma_status TEXT,
                    score_1d REAL,
                    score_4h REAL,
                    score_1h REAL,
                    vol_ratio_1d REAL,
                    vol_ratio_4h REAL,
                    vol_ratio_1h REAL
                )
            ''')

            ts = datetime.now().isoformat()
            for pair in results:
                scores = pair.get("timeframe_scores", {})
                vol_ratios = {}
                for tf in self.TIMEFRAMES:
                    detail = pair["timeframes"].get(tf)
                    vol_ratios[tf] = detail["volume"]["volume_ratio"] if detail else 0.0

                cursor.execute('''
                    INSERT INTO breakout_records
                    (timestamp, symbol, composite_score, vol_usd_24h, price_change_pct,
                     ma_status, score_1d, score_4h, score_1h,
                     vol_ratio_1d, vol_ratio_4h, vol_ratio_1h)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    ts,
                    pair["symbol"],
                    pair["composite_score"],
                    pair["vol_usd_24h"],
                    pair["price_change_pct"],
                    pair["ma_status"],
                    scores.get("1d", 0.0),
                    scores.get("4h", 0.0),
                    scores.get("1h", 0.0),
                    vol_ratios.get("1d", 0.0),
                    vol_ratios.get("4h", 0.0),
                    vol_ratios.get("1h", 0.0),
                ))

            conn.commit()
            conn.close()
            logger.info(f"结果已保存到数据库: {db_path}")
        except Exception as e:
            logger.error(f"保存数据库失败: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="币安USDT永续合约放量突破筛选器 - 筛选即将放量突破的交易对，用于网格趋势突破",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python test_volume_breakout.py                          # 默认筛选前20个
  python test_volume_breakout.py --top 10                 # 显示前10个
  python test_volume_breakout.py --min-vol 10000000       # 最低1千万成交额
  python test_volume_breakout.py --export json            # 导出JSON文件
  python test_volume_breakout.py --export csv --db        # 导出CSV并保存数据库

筛选逻辑:
  多周期(1h/4h/1d)分析，权重: 日线50%, 4小时30%, 1小时20%
  指标: 放量评分(50%) + 均线突破评分(50%)
  放量: 当前成交量 vs 20周期均量, 2x以上视为放量
  均线突破: 价格突破MA7/MA25/MA100, 多头排列加分
        """
    )
    parser.add_argument("--top", type=int, default=20,
                        help="显示前N个结果 (default: 20)")
    parser.add_argument("--min-vol", type=float, default=5_000_000,
                        help="最低24h成交额(USD) (default: 5,000,000)")
    parser.add_argument("--klines", type=int, default=100,
                        help="每个周期获取的K线数量 (default: 100)")
    parser.add_argument("--workers", type=int, default=5,
                        help="最大并发线程数 (default: 5)")
    parser.add_argument("--min-score", type=float, default=0.1,
                        help="最低综合评分阈值 (default: 0.1)")
    parser.add_argument("--export", choices=["json", "csv", "none"], default="none",
                        help="导出格式 (default: none)")
    parser.add_argument("--db", action="store_true",
                        help="保存结果到SQLite数据库")

    args = parser.parse_args()

    screener = BinanceVolumeBreakoutScreener(
        min_volume_usd=args.min_vol,
        kline_limit=args.klines,
        max_workers=args.workers
    )

    try:
        print("正在扫描币安USDT永续合约放量突破信号...")
        results = screener.scan(top_n=args.top, min_score=args.min_score)

        if not results:
            print("没有找到符合条件的放量突破交易对。")
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
