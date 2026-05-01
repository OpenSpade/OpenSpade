import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
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
    from tabulate import tabulate
except ImportError:
    print("缺少tabulate库，请先安装：pip install tabulate")
    sys.exit(1)

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


class BinanceDelistingPredictor:
    """币安下架风险预测器"""

    Binance_API_BASE = "https://api.binance.com"

    DEFAULT_RISK_WEIGHTS = {
        "volume_decline": 0.35,
        "liquidity_depth": 0.25,
        "price_performance": 0.2,
        "trading_activity": 0.2,
    }

    # 请求频率控制
    MIN_REQUEST_INTERVAL = 0.1  # 100ms between requests

    def __init__(
            self,
            volume_threshold: float = 1_000_000,
            days_analysis: int = 30,
            max_workers: int = 5
    ):
        self.volume_threshold = volume_threshold
        self.days_analysis = days_analysis
        self.risk_weights = self.DEFAULT_RISK_WEIGHTS
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BinanceDelistingPredictor/1.0'
        })

        # 缓存
        self.klines_cache = {}
        self.depth_cache = {}
        self.last_request_time = 0

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
                self._rate_limit()  # 频率控制
                response = self.session.get(url, params=params, timeout=timeout)

                # 处理不同状态码
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limit
                    retry_after = int(response.headers.get("Retry-After", 5))
                    logger.warning(f"Rate limit hit. Retrying after {retry_after}s")
                    time.sleep(retry_after)
                    continue
                elif response.status_code >= 500:  # Server error
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

    def fetch_all_tickers(self) -> Dict[str, Dict]:
        """获取所有交易对的24小时行情"""
        data = self._safe_request(f"{self.Binance_API_BASE}/api/v3/ticker/24hr")
        return {item['symbol']: item for item in data} if data else {}

    def fetch_exchange_info(self) -> List[Dict]:
        """获取交易对信息"""
        data = self._safe_request(f"{self.Binance_API_BASE}/api/v3/exchangeInfo")
        return data.get("symbols", []) if data else []

    def get_klines(self, symbol: str) -> Optional[List[List]]:
        """获取K线数据（带缓存）"""
        if symbol not in self.klines_cache:
            data = self._safe_request(
                f"{self.Binance_API_BASE}/api/v3/klines",
                params={
                    "symbol": symbol,
                    "interval": "1d",
                    "limit": self.days_analysis
                }
            )
            self.klines_cache[symbol] = data
        return self.klines_cache[symbol]

    def get_depth(self, symbol: str) -> Optional[Dict]:
        """获取深度数据（带缓存）"""
        if symbol not in self.depth_cache:
            data = self._safe_request(
                f"{self.Binance_API_BASE}/api/v3/depth",
                params={
                    "symbol": symbol,
                    "limit": 100  # 增加深度级别
                }
            )
            self.depth_cache[symbol] = data
        return self.depth_cache[symbol]

    def calculate_volume_risk(self, quote_vol: float) -> float:
        """计算成交量风险"""
        if quote_vol <= 0:
            return 1.0

        # 使用对数刻度来更细致地评估风险
        if quote_vol >= self.volume_threshold:
            return 0.0
        elif quote_vol >= self.volume_threshold * 0.5:
            return 0.1
        elif quote_vol >= 100_000:
            return 0.3
        elif quote_vol >= 10_000:
            return 0.5
        elif quote_vol >= 1_000:
            return 0.8
        else:
            return 1.0

    def calculate_price_risk(self, klines: List[List]) -> float:
        """计算价格风险"""
        if not klines or len(klines) < 7:
            return 0.0

        closes = [float(k[4]) for k in klines]

        if closes[0] == 0:
            return 0.0

        # 整体价格变化
        total_change = (closes[-1] - closes[0]) / closes[0] * 100

        # 近期趋势（最后7天）
        if len(closes) >= 7:
            recent_change = (closes[-1] - closes[-7]) / closes[-7] * 100
        else:
            recent_change = total_change

        # 最大回撤
        max_price = max(closes)
        max_drawdown = (min(closes) - max_price) / max_price * 100

        # 综合评估
        risk = 0.0
        if total_change < -50 or max_drawdown < -70:
            risk = 1.0
        elif total_change < -30 or max_drawdown < -50:
            risk = 0.8
        elif total_change < -20 or recent_change < -30:
            risk = 0.6
        elif total_change < -10 or recent_change < -15:
            risk = 0.4
        elif total_change < 0:
            risk = 0.2

        return risk

    def calculate_activity_risk(self, klines: List[List]) -> float:
        """计算交易活跃度风险"""
        if not klines:
            return 1.0

        trades = [int(k[8]) for k in klines]

        if not trades:
            return 1.0

        # 低交易天数
        low_trade_days = sum(1 for t in trades if t < 50)

        # 零交易天数
        zero_trade_days = sum(1 for t in trades if t == 0)

        # 平均交易次数趋势
        avg_trades_recent = sum(trades[-7:]) / min(7, len(trades[-7:]))
        avg_trades_old = sum(trades[:7]) / min(7, len(trades[:7]))

        trade_decline = 0
        if avg_trades_old > 0:
            trade_decline = (avg_trades_old - avg_trades_recent) / avg_trades_old

        # 综合风险评分
        risk = (
                (low_trade_days / len(trades)) * 0.5 +
                (zero_trade_days / len(trades)) * 0.3 +
                min(1.0, max(0, trade_decline)) * 0.2
        )

        return min(1.0, risk)

    def calculate_liquidity_risk(self, depth: Dict) -> float:
        """计算流动性风险"""
        if not depth or "bids" not in depth or "asks" not in depth:
            return 0.5

        bids = depth.get("bids", [])
        asks = depth.get("asks", [])

        if not bids or not asks:
            return 1.0

        # 买卖价差
        best_bid = float(bids[0][0])
        best_ask = float(asks[0][0])

        if best_bid == 0:
            return 1.0

        spread = (best_ask - best_bid) / best_bid * 100

        # 订单簿深度（前20档）
        bid_depth = sum(float(b[1]) for b in bids[:20])
        ask_depth = sum(float(a[1]) for a in asks[:20])

        total_depth = bid_depth + ask_depth

        # 综合评估
        risk = 0.0

        # 价差风险
        if spread > 5:
            risk += 0.5
        elif spread > 2:
            risk += 0.3
        elif spread > 1:
            risk += 0.15

        # 深度风险
        if total_depth < 1:
            risk += 0.5
        elif total_depth < 10:
            risk += 0.3
        elif total_depth < 100:
            risk += 0.1

        return min(1.0, risk)

    def analyze_single_pair(self, symbol: str, ticker: Dict) -> Optional[Dict]:
        """分析单个交易对的下架风险"""
        try:
            # 快速预筛选
            quote_vol = float(ticker.get("quoteVolume", 0))
            if quote_vol > self.volume_threshold * 10:
                return None

            # 获取详细数据
            klines = self.get_klines(symbol)
            if not klines or len(klines) < 7:
                return None

            depth = self.get_depth(symbol)

            # 计算各项风险
            vol_risk = self.calculate_volume_risk(quote_vol)
            price_risk = self.calculate_price_risk(klines)
            activity_risk = self.calculate_activity_risk(klines)
            liq_risk = self.calculate_liquidity_risk(depth) if depth else 0.5

            # 加权综合评分
            weights = self.risk_weights
            score = (
                    vol_risk * weights["volume_decline"] +
                    liq_risk * weights["liquidity_depth"] +
                    price_risk * weights["price_performance"] +
                    activity_risk * weights["trading_activity"]
            )

            # 计算价格变化
            closes = [float(k[4]) for k in klines]
            price_change = ((closes[-1] - closes[0]) / closes[0] * 100) if closes[0] != 0 else 0

            return {
                "symbol": symbol,
                "score": round(score, 4),
                "vol_usd": quote_vol,
                "price_change_pct": round(price_change, 2),
                "details": {
                    "volume_risk": round(vol_risk, 3),
                    "liquidity_risk": round(liq_risk, 3),
                    "price_risk": round(price_risk, 3),
                    "activity_risk": round(activity_risk, 3),
                }
            }

        except Exception as e:
            logger.debug(f"Error analyzing {symbol}: {e}")
            return None

    def scan(self, quote_asset: str = "USDT", top_n: int = 20, min_score: float = 0.1) -> List[Dict]:
        """扫描所有交易对，返回风险最高的"""
        logger.info("Fetching market data...")

        tickers = self.fetch_all_tickers()
        if not tickers:
            logger.error("Failed to fetch tickers")
            return []

        symbol_info = self.fetch_exchange_info()
        if not symbol_info:
            logger.error("Failed to fetch exchange info")
            return []

        # 筛选目标交易对
        target_symbols = [
            s['symbol'] for s in symbol_info
            if s['status'] == 'TRADING' and s['quoteAsset'] == quote_asset
        ]

        logger.info(f"Analyzing {len(target_symbols)} {quote_asset} pairs...")

        results = []

        # 多线程分析
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_symbol = {
                executor.submit(self.analyze_single_pair, symbol, tickers.get(symbol, {})): symbol
                for symbol in target_symbols if symbol in tickers
            }

            for i, future in enumerate(as_completed(future_to_symbol)):
                symbol = future_to_symbol[future]
                try:
                    result = future.result()
                    if result and result['score'] >= min_score:
                        results.append(result)

                    if (i + 1) % 50 == 0:
                        logger.info(f"Progress: {i + 1}/{len(target_symbols)}")

                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")

        # 排序并返回
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_n]

    def print_results_table(self, results: List[Dict], quote_asset: str, table_format: str = "grid"):
        """使用PrettyTable打印格式化的结果表格"""
        if not results:
            print("没有找到符合条件的风险交易对。")
            return

        # 打印表头
        print(f"\n{'=' * 100}")
        print(f" 币安 {quote_asset} 交易对下架风险分析 TOP {len(results)}")
        print(f"{'=' * 100}")
        print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"风险权重: 成交量={self.risk_weights['volume_decline']:.0%}, "
              f"流动性={self.risk_weights['liquidity_depth']:.0%}, "
              f"价格={self.risk_weights['price_performance']:.0%}, "
              f"活跃度={self.risk_weights['trading_activity']:.0%}")

        # 使用PrettyTable创建表格
        table = PrettyTable()
        table.field_names = ["排名", "交易对", "风险评分", "24h成交量(USD)", "价格变化(%)",
                           "成交量风险", "流动性风险", "价格风险", "活跃度风险"]
        
        # 设置表格样式
        table.align = "l"  # 左对齐
        table.align["排名"] = "c"  # 排名居中
        table.align["风险评分"] = "c"  # 风险评分居中
        table.align["24h成交量(USD)"] = "r"  # 成交量右对齐
        table.align["价格变化(%)"] = "r"  # 价格变化右对齐
        table.align["成交量风险"] = "c"  # 风险值居中
        table.align["流动性风险"] = "c"
        table.align["价格风险"] = "c"
        table.align["活跃度风险"] = "c"
        
        # 添加数据行
        for i, pair in enumerate(results, 1):
            details = pair['details']
            # 根据风险评分高低添加颜色标记
            risk_level = "🔴" if pair['score'] > 0.7 else "🟡" if pair['score'] > 0.4 else "🟢"

            table.add_row([
                i,
                f"{risk_level} {pair['symbol']}",
                f"{pair['score']:.4f}",
                f"{pair['vol_usd']:,.2f}",
                f"{pair['price_change_pct']:.2f}%",
                f"{details['volume_risk']:.3f}",
                f"{details['liquidity_risk']:.3f}",
                f"{details['price_risk']:.3f}",
                f"{details['activity_risk']:.3f}"
            ])

        # 打印表格
        print(table)

        # 打印风险等级说明
        print(f"\n风险等级: 🔴 高风险(>0.7) 🟡 中等风险(>0.4) 🟢 低风险(≤0.4)")

        # 提示信息
        print(f"\n提示: 使用PrettyTable生成的表格支持自动列宽调整和美观的边框样式")

    def export_results(self, results: List[Dict], format: str = "json") -> str:
        """导出结果为文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "json":
            filename = f"delisting_risk_{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        elif format == "csv" and pd is not None:
            filename = f"delisting_risk_{timestamp}.csv"
            df = pd.DataFrame([{
                'symbol': r['symbol'],
                'score': r['score'],
                'volume_usd': r['vol_usd'],
                'price_change_pct': r['price_change_pct'],
                **r['details']
            } for r in results])
            df.to_csv(filename, index=False, encoding='utf-8-sig')
        else:
            return ""

        return filename

    def save_to_database(self, results: List[Dict], db_path: str = "delisting_risks.db"):
        """保存结果到SQLite数据库（可选功能）"""
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 创建表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS risk_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    symbol TEXT,
                    score REAL,
                    vol_usd REAL,
                    price_change_pct REAL,
                    volume_risk REAL,
                    liquidity_risk REAL,
                    price_risk REAL,
                    activity_risk REAL
                )
            ''')

            # 插入数据
            timestamp = datetime.now().isoformat()
            for pair in results:
                details = pair['details']
                cursor.execute('''
                    INSERT INTO risk_records 
                    (timestamp, symbol, score, vol_usd, price_change_pct,
                     volume_risk, liquidity_risk, price_risk, activity_risk)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    timestamp,
                    pair['symbol'],
                    pair['score'],
                    pair['vol_usd'],
                    pair['price_change_pct'],
                    details['volume_risk'],
                    details['liquidity_risk'],
                    details['price_risk'],
                    details['activity_risk']
                ))

            conn.commit()
            conn.close()
            logger.info(f"Results saved to database: {db_path}")
        except Exception as e:
            logger.error(f"Failed to save to database: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="币安下架风险预测器 - 分析并展示高风险交易对",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python script.py                          # 默认分析USDT交易对
  python script.py --quote BTC              # 分析BTC交易对
  python script.py --top 10 --table-format github  # 显示前10个，GitHub风格
  python script.py --export json            # 导出JSON文件
  python script.py --export csv --db        # 导出CSV并保存到数据库
        """
    )
    parser.add_argument("--quote", default="USDT", help="Quote asset (default: USDT)")
    parser.add_argument("--top", type=int, default=20, help="Number of top risky pairs to show")
    parser.add_argument("--threshold", type=float, default=1_000_000, help="Volume threshold (default: 1,000,000)")
    parser.add_argument("--days", type=int, default=30, help="Days to analyze (default: 30)")
    parser.add_argument("--export", choices=["json", "csv", "none"], default="none", help="Export format")
    parser.add_argument("--workers", type=int, default=5, help="Max worker threads (default: 5)")
    parser.add_argument("--db", action="store_true", help="Save results to SQLite database")

    args = parser.parse_args()

    # 创建预测器实例
    predictor = BinanceDelistingPredictor(
        volume_threshold=args.threshold,
        days_analysis=args.days,
        max_workers=args.workers
    )

    try:
        # 扫描风险交易对
        print("正在分析币安交易对下架风险...")
        risk_pairs = predictor.scan(quote_asset=args.quote, top_n=args.top)

        if not risk_pairs:
            print("没有找到符合条件的风险交易对。")
            return

        # 使用PrettyTable格式化打印结果
        predictor.print_results_table(risk_pairs, args.quote)

        # 导出结果
        if args.export != "none":
            filename = predictor.export_results(risk_pairs, format=args.export)
            if filename:
                print(f"结果已导出至: {filename}")

        # 保存到数据库
        if args.db:
            predictor.save_to_database(risk_pairs)

    except KeyboardInterrupt:
        print("\n\n程序被用户中断。")
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
        print(f"错误: {e}")


if __name__ == "__main__":
    main()