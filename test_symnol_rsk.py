import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
except ImportError:
    print("缺少requests库，请先安装：pip install requests")
    sys.exit(1)

try:
    import pandas as pd
except ImportError:
    pd = None


class BinanceDelistingPredictor:
    Binance_API_BASE = "https://api.binance.com"

    # Adjusted eights
    DEFAULT_RISK_WEIGHTS = {
        "volume_decline": 0.35,
        "liquidity_depth": 0.25,
        "price_performance": 0.2,
        "trading_activity": 0.2,
    }

    def __init__(self, volume_threshold: float = 1_000_000, days_analysis: int = 30):
        self.volume_threshold = volume_threshold
        self.days_analysis = days_analysis
        self.risk_weights = self.DEFAULT_RISK_WEIGHTS
        self.session = requests.Session()
        self.klines_cache = {}
        self.depth_cache = {}

    def _safe_request(self, url, params=None, timeout=10):
        """
        Helper with retry logic for 429 errors
        """
        max_tries = 3
        for attempt in range(max_tries):
            try:
                response = self.session.get(url, params=params, timeout=timeout)
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 5))
                    print(f"Rate limit hit. Retrying after {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                print(f"Request error: {e}")
                if attempt == max_tries - 1:
                    print("Retrying...")
                    return None
                time.sleep(2 ** attempt)
        return None

    def fetch_all_tickers(self) -> Dict[str, Dict]:
        """
        Fetch all tickers once and map by symbol
        """
        data = self._safe_request(f"{self.Binance_API_BASE}/api/v3/ticker/24hr")
        if not data:
            return {}
        return {item['symbol']: item for item in data}

    def fetch_exchange_info(self) -> List[Dict]:
        """
        Get list of trading pairs and their details
        """
        data = self._safe_request(f"{self.Binance_API_BASE}/api/v3/exchangeInfo")
        if not data:
            return {}
        return data.get("symbols", [])

    def get_klines(self, symbol: str) -> Optional[List[Dict]]:
        """
        Cached klines fetcher
        """
        if symbol in self.klines_cache:
            return self.klines_cache[symbol]

        data = self._safe_request(f"{self.Binance_API_BASE}/api/v3/klines", params={
            "symbol": symbol,
            "interval": "1d",
            "limit": self.days_analysis
        })

        self.klines_cache[symbol] = data

        return data

    def get_depth(self, symbol: str) -> Optional[Dict]:
        """
        Cached depth fetcher
        """
        if symbol in self.depth_cache:
            return self.depth_cache[symbol]

        data = self._safe_request(f"{self.Binance_API_BASE}/api/v3/depth", params={
            "symbol": symbol,
            "limit": 20
        })

        self.depth_cache[symbol] = data

        return data

    def analyze_single_pair(self, symbol: str, ticker: Dict) -> Optional[Dict]:
        """
        Analyze a single trading pair, Designed to be run in threads
        """
        try:
            # 1. Volume Risk (Fast, from ticker)
            quote_vol = float(ticker.get("quoteVolume", 0))
            if quote_vol > self.volume_threshold * 5:
                return None  # Skip safe coins early
            vol_risk = 1.0 if quote_vol < 100_000 else (0.5 if quote_vol < 500_000 else 0.2)
            # 2.Price & Activity Risk (Needs klines)
            klines = self.get_klines(symbol)
            if not klines or len(klines) < 7:
                return None
            closes = [float(k[4]) for k in klines]
            vols = [float(k[7]) for k in klines]  # Quote volume in kline
            trades = [int(k[8]) for k in klines]  # Number of trades in kline

            # Price  Trend
            recent_close = closes[-1]
            old_close = closes[0]
            price_change = (recent_close - old_close) / old_close * 100 if old_close else 0

            price_risk = 0.0
            if price_change < -30:
                price_risk = 1.0
            elif price_change < -15:
                price_risk = 0.5
            elif price_change < 0:
                price_risk = 0.3

            # 2.Activity Risk (Volume & Trades)
            zero_trade_days = sum(1 for t in trades if t < 50)
            activity_risk = min(1.0, zero_trade_days / len(trades) * 2)

            # 3. Liquidity Risk (Needs depth)
            depth = self.get_depth(symbol)
            liq_risk = 0.5  # Default
            if depth and "bids" in depth and "asks" in depth:
                bids = depth["bids"]
                asks = depth["asks"]
                if bids and asks:
                    spread = (float(asks[0][0]) - float(bids[0][0])) / float(bids[0][0])
                    liq_risk = min(1.0, spread * 100)  # Simple spread-based risk

            # Composite Score

            weights = self.DEFAULT_RISK_WEIGHTS
            score = (vol_risk * weights["volume_decline"] + liq_risk * weights["liquidity_depth"] +
                     price_risk * weights["price_performance"] + activity_risk * weights["trading_activity"])

            return {
                "symbol": symbol,
                "score": round(score, 3),
                "vol_usd": quote_vol,
                "price_change_pct": round(price_change, 2),
                "details": {
                    "volume_risk": vol_risk,
                    "liquidity_risk": liq_risk,
                    "price_risk": price_risk,
                    "activity_risk": activity_risk,
                }
            }

        except Exception as e:
            # print(f"Error analyzing {symbol}: {e}")
            return None

    def scan(self, quote_asset="USDT", top_n=20):
        print("Fetching initial data...")
        tickers = self.fetch_all_tickers()
        symbol_info = self.fetch_exchange_info()

        # Filter for quote asset
        target_symbols = [
            s['symbol'] for s in symbol_info
            if s['status'] == 'TRADING' and s['quoteAsset'] == quote_asset
        ]

        print(f"Analyzing {len(target_symbols)} trading pairs with quote asset {quote_asset}...")

        results = []

        # Use
        # Note:

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_symbol = {
                executor.submit(self.analyze_single_pair, symbol, tickers.get(symbol, {})): symbol
                for symbol in target_symbols if symbol in tickers
            }
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    print(f"Error processing {symbol}: {e}")

        # Sort and return
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_n]


def main():
    predictor = BinanceDelistingPredictor()  # Lowered threshold for demo
    risk_pairs = predictor.scan(quote_asset="USDT", top_n=20)

    print("\n ----TOP RISKY PAIRS----")

    for p in risk_pairs:
        print(f"{p['symbol']}: Score={p['score']} | Vol={p['vol_usd']:.2f} USD | Price Change={p['price_change_pct']}%")


if __name__ == "__main__":
    main()
