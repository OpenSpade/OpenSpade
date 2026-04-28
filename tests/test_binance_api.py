import os
from openspade.gateway.binance_connector import BinanceConnector

# 获取API密钥
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')

if not api_key or not api_secret:
    print("Please set BINANCE_API_KEY and BINANCE_API_SECRET environment variables")
    exit(1)

# 创建BinanceConnector实例
connector = BinanceConnector(api_key, api_secret)

# 测试现货账户接口
print("Testing spot account API...")
try:
    spot_balance = connector.get_spot_balance()
    print(f"Spot USDT balance: {spot_balance}")
    
    spot_assets = connector.get_all_spot_assets()
    print(f"Spot assets count: {len(spot_assets)}")
    for asset in spot_assets:
        print(f"  {asset['asset']}: {asset['total']}")
    
except Exception as e:
    print(f"Error: {e}")

# 测试期货账户接口
print("\nTesting futures account API...")
try:
    futures_balance = connector.get_futures_balance()
    print(f"Futures USDT balance: {futures_balance}")
    
    futures_assets = connector.get_all_futures_assets()
    print(f"Futures assets count: {len(futures_assets)}")
    for asset in futures_assets:
        print(f"  {asset['asset']}: {asset['total']}")
    
except Exception as e:
    print(f"Error: {e}")

# 测试账户信息
print("\nTesting account info...")
try:
    account_info = connector.get_account_info()
    if account_info:
        print(f"Account info retrieved successfully")
        print(f"Initial margin: {account_info.get('initialMargin', 0)}")
        print(f"Maintenance margin: {account_info.get('maintMargin', 0)}")
    else:
        print("Failed to get account info")
except Exception as e:
    print(f"Error: {e}")
