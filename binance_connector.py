import requests
import time
from typing import Dict, Optional, List
from datetime import datetime


class BinanceConnector:
    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.binance.com"
        self.futures_url = "https://fapi.binance.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/json'
        }
        if api_key:
            self.headers['X-MBX-APIKEY'] = api_key

    def get_spot_balance(self) -> float:
        if not self.api_key:
            return 0.0

        endpoint = "/api/v3/account"
        params = {"timestamp": int(time.time() * 1000)}

        try:
            response = requests.get(
                self.base_url + endpoint,
                headers=self.headers,
                params=params
            )
            if response.status_code == 200:
                data = response.json()
                for balance in data.get('balances', []):
                    if balance['asset'] == 'USDT':
                        free = float(balance.get('free', 0))
                        locked = float(balance.get('locked', 0))
                        return free + locked
            return 0.0
        except Exception as e:
            print(f"Failed to get spot balance: {e}")
            return 0.0

    def get_futures_balance(self) -> float:
        endpoint = "/fapi/v2/balance"

        try:
            params = {"timestamp": int(time.time() * 1000)}
            response = requests.get(
                self.futures_url + endpoint,
                headers=self.headers,
                params=params
            )
            if response.status_code == 200:
                data = response.json()
                for balance in data:
                    if balance['asset'] == 'USDT':
                        return float(balance.get('availableBalance', 0)) + float(balance.get('marginBalance', 0))
            return 0.0
        except Exception as e:
            print(f"Failed to get futures balance: {e}")
            return 0.0

    def get_total_assets(self) -> float:
        spot = self.get_spot_balance()
        futures = self.get_futures_balance()
        return spot + futures

    def get_account_info(self) -> Dict:
        endpoint = "/fapi/v2/account"

        try:
            params = {"timestamp": int(time.time() * 1000)}
            response = requests.get(
                self.futures_url + endpoint,
                headers=self.headers,
                params=params
            )
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            print(f"Failed to get account info: {e}")
            return {}

    def get_positions(self) -> List[Dict]:
        account = self.get_account_info()
        if not account:
            return []

        return account.get('positions', [])

    def get_position_info(self, symbol: str) -> Optional[Dict]:
        positions = self.get_positions()
        for pos in positions:
            if pos.get('symbol') == symbol:
                return {
                    "symbol": pos.get('symbol'),
                    "positionAmt": float(pos.get('positionAmt', 0)),
                    "entryPrice": float(pos.get('entryPrice', 0)),
                    "unrealizedProfit": float(pos.get('unrealizedProfit', 0)),
                    "marginType": pos.get('marginType'),
                    "leverage": int(pos.get('leverage', 1))
                }
        return None

    def get_current_price(self, symbol: str) -> float:
        endpoint = "/fapi/v1/ticker/price"
        try:
            params = {"symbol": symbol}
            response = requests.get(
                self.futures_url + endpoint,
                params=params
            )
            if response.status_code == 200:
                data = response.json()
                return float(data.get('price', 0))
            return 0.0
        except Exception as e:
            print(f"Failed to get price for {symbol}: {e}")
            return 0.0

    def get_all_prices(self, symbols: List[str] = None) -> Dict[str, float]:
        endpoint = "/fapi/v1/ticker/price"
        try:
            response = requests.get(
                self.futures_url + endpoint,
                headers=self.headers
            )
            if response.status_code == 200:
                data = response.json()
                prices = {}
                for item in data:
                    symbol = item.get('symbol')
                    if symbols is None or symbol in symbols:
                        prices[symbol] = float(item.get('price', 0))
                return prices
            return {}
        except Exception as e:
            print(f"Failed to get all prices: {e}")
            return {}

    def get_portfolio_summary(self) -> Dict:
        total = self.get_total_assets()
        positions = self.get_positions()

        total_position_value = 0.0
        total_unrealized_pnl = 0.0
        active_positions = []

        for pos in positions:
            if float(pos.get('positionAmt', 0)) != 0:
                pos_amt = float(pos.get('positionAmt', 0))
                entry_price = float(pos.get('entryPrice', 0))
                unrealized_pnl = float(pos.get('unrealizedProfit', 0))
                pos_value = abs(pos_amt * entry_price)

                total_position_value += pos_value
                total_unrealized_pnl += unrealized_pnl

                active_positions.append({
                    "symbol": pos.get('symbol'),
                    "amount": pos_amt,
                    "entry_price": entry_price,
                    "current_value": pos_value,
                    "unrealized_pnl": unrealized_pnl,
                    "leverage": int(pos.get('leverage', 1)),
                    "margin_type": pos.get('marginType')
                })

        return {
            "total_assets": total,
            "total_position_value": total_position_value,
            "total_unrealized_pnl": total_unrealized_pnl,
            "available_balance": total - total_position_value,
            "active_positions": active_positions,
            "position_count": len(active_positions),
            "timestamp": datetime.now().isoformat()
        }
