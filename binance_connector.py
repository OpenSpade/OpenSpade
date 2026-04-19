import requests
import time
import hmac
import hashlib
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
        self._time_offset = 0
        self._sync_server_time()

    def _sync_server_time(self):
        """同步本地时间与Binance服务器时间"""
        try:
            local_ts = int(time.time() * 1000)
            response = requests.get(self.base_url + "/api/v3/time", timeout=5)
            if response.status_code == 200:
                server_ts = response.json()['serverTime']
                self._time_offset = server_ts - local_ts
                print(f"Server time synced, offset: {self._time_offset}ms")
            else:
                print(f"Failed to sync server time: {response.status_code}")
        except Exception as e:
            print(f"Failed to sync server time: {e}")

    def _get_timestamp(self) -> int:
        """获取校正后的时间戳"""
        return int(time.time() * 1000) + self._time_offset

    def _generate_signature(self, params: Dict) -> str:
        """生成API签名"""
        if not self.api_secret:
            return ""
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def get_spot_balance(self) -> float:
        if not self.api_key or not self.api_secret:
            return 0.0

        endpoint = "/api/v3/account"
        params = {"timestamp": self._get_timestamp(), "recvWindow": 60000}  # 60秒的时间窗口
        params['signature'] = self._generate_signature(params)

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
            else:
                print(f"API error: {response.status_code} - {response.text}")
            return 0.0
        except Exception as e:
            print(f"Failed to get spot balance: {e}")
            return 0.0

    def get_all_spot_assets(self) -> List[Dict]:
        if not self.api_key or not self.api_secret:
            return []

        endpoint = "/api/v3/account"
        params = {"timestamp": self._get_timestamp(), "recvWindow": 60000}  # 60秒的时间窗口
        params['signature'] = self._generate_signature(params)

        try:
            response = requests.get(
                self.base_url + endpoint,
                headers=self.headers,
                params=params
            )
            if response.status_code == 200:
                data = response.json()
                assets = []
                for balance in data.get('balances', []):
                    free = float(balance.get('free', 0))
                    locked = float(balance.get('locked', 0))
                    total = free + locked
                    if total > 0:
                        assets.append({
                            'asset': balance['asset'],
                            'free': free,
                            'locked': locked,
                            'total': total
                        })
                return assets
            else:
                print(f"API error: {response.status_code} - {response.text}")
            return []
        except Exception as e:
            print(f"Failed to get all spot assets: {e}")
            return []

    def get_futures_balance(self) -> float:
        if not self.api_key or not self.api_secret:
            return 0.0

        endpoint = "/fapi/v2/balance"

        try:
            params = {"timestamp": self._get_timestamp(), "recvWindow": 60000}  # 60秒的时间窗口
            params['signature'] = self._generate_signature(params)
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
            else:
                print(f"API error: {response.status_code} - {response.text}")
            return 0.0
        except Exception as e:
            print(f"Failed to get futures balance: {e}")
            return 0.0

    def get_all_futures_assets(self) -> List[Dict]:
        if not self.api_key or not self.api_secret:
            return []

        endpoint = "/fapi/v2/balance"

        try:
            params = {"timestamp": self._get_timestamp(), "recvWindow": 60000}  # 60秒的时间窗口
            params['signature'] = self._generate_signature(params)
            response = requests.get(
                self.futures_url + endpoint,
                headers=self.headers,
                params=params
            )
            if response.status_code == 200:
                data = response.json()
                assets = []
                for balance in data:
                    free = float(balance.get('availableBalance', 0))
                    locked = float(balance.get('crossWalletBalance', 0)) - free
                    total = float(balance.get('crossWalletBalance', 0))
                    if total > 0:
                        assets.append({
                            'asset': balance['asset'],
                            'free': free,
                            'locked': locked,
                            'total': total
                        })
                return assets
            else:
                print(f"API error: {response.status_code} - {response.text}")
            return []
        except Exception as e:
            print(f"Failed to get all futures assets: {e}")
            return []

    def get_all_assets(self) -> Dict:
        spot_assets = self.get_all_spot_assets()
        futures_assets = self.get_all_futures_assets()
        
        return {
            'spot': spot_assets,
            'futures': futures_assets,
            'timestamp': datetime.now().isoformat()
        }

    def get_total_assets(self) -> float:
        spot = self.get_spot_balance()
        futures = self.get_futures_balance()
        return spot + futures

    def get_account_info(self) -> Dict:
        if not self.api_key or not self.api_secret:
            return {}

        endpoint = "/fapi/v2/account"

        try:
            params = {"timestamp": self._get_timestamp(), "recvWindow": 60000}  # 60秒的时间窗口
            params['signature'] = self._generate_signature(params)
            response = requests.get(
                self.futures_url + endpoint,
                headers=self.headers,
                params=params
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(f"API error: {response.status_code} - {response.text}")
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
