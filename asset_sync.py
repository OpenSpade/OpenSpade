import time
import threading
from datetime import datetime
from typing import Dict, List, Optional
from binance_connector import BinanceConnector
from database_extension import save_asset, log_asset_history, log_asset_sync, get_asset_statistics


class AssetSync:
    def __init__(self, api_key: str = None, api_secret: str = None):
        self.binance = BinanceConnector(api_key, api_secret)
        self.sync_interval = 300  # 默认5分钟同步一次
        self.running = False
        self.sync_thread = None
        self.last_sync_time: Optional[datetime] = None
        self.last_sync_result: Optional[Dict] = None
        self.retry_interval = 60  # 重试间隔
        self.max_retries = 3  # 最大重试次数

    def sync_assets(self, retry_count: int = 0) -> Dict:
        sync_data = {
            'sync_type': 'full',
            'status': 'success',
            'start_time': datetime.now().isoformat(),
            'records_synced': 0
        }

        try:
            assets_data = self.binance.get_all_assets()
            
            # 同步现货资产
            for asset in assets_data.get('spot', []):
                asset_data = {
                    'asset_type': 'spot',
                    'asset': asset['asset'],
                    'free': asset['free'],
                    'locked': asset['locked'],
                    'total': asset['total']
                }
                save_asset(asset_data)
                log_asset_history(asset_data)
                sync_data['records_synced'] += 1

            # 同步期货资产
            for asset in assets_data.get('futures', []):
                asset_data = {
                    'asset_type': 'futures',
                    'asset': asset['asset'],
                    'free': asset['free'],
                    'locked': asset['locked'],
                    'total': asset['total']
                }
                save_asset(asset_data)
                log_asset_history(asset_data)
                sync_data['records_synced'] += 1

            sync_data['end_time'] = datetime.now().isoformat()
            self.last_sync_time = datetime.now()
            self.last_sync_result = sync_data
            print(f"Asset sync completed successfully. Synced {sync_data['records_synced']} records.")

        except Exception as e:
            sync_data['status'] = 'failed'
            sync_data['error_message'] = str(e)
            sync_data['end_time'] = datetime.now().isoformat()
            print(f"Asset sync failed: {e}")
            
            # 重试机制
            if retry_count < self.max_retries:
                print(f"Retrying sync ({retry_count + 1}/{self.max_retries})...")
                time.sleep(self.retry_interval)
                return self.sync_assets(retry_count + 1)

        finally:
            log_asset_sync(sync_data)
            return sync_data

    def start_auto_sync(self, interval: int = None):
        if interval:
            self.sync_interval = interval

        if self.running:
            print("Auto sync is already running.")
            return

        self.running = True
        self.sync_thread = threading.Thread(target=self._auto_sync_loop, daemon=True)
        self.sync_thread.start()
        print(f"Auto sync started with interval {self.sync_interval} seconds.")

    def stop_auto_sync(self):
        if not self.running:
            print("Auto sync is not running.")
            return

        self.running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        print("Auto sync stopped.")

    def _auto_sync_loop(self):
        while self.running:
            self.sync_assets()
            # 使用更精确的时间控制
            start_time = time.time()
            while self.running and time.time() - start_time < self.sync_interval:
                time.sleep(1)

    def get_sync_status(self) -> Dict:
        stats = get_asset_statistics()
        return {
            'auto_sync_running': self.running,
            'sync_interval': self.sync_interval,
            'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
            'last_sync_result': self.last_sync_result,
            'asset_statistics': stats
        }

    def force_sync(self) -> Dict:
        """强制立即同步资产"""
        print("Forcing asset sync...")
        return self.sync_assets()

    def set_sync_interval(self, interval: int):
        """设置同步间隔"""
        if interval > 0:
            self.sync_interval = interval
            print(f"Sync interval updated to {interval} seconds.")
        else:
            print("Sync interval must be positive.")


if __name__ == "__main__":
    # 示例用法
    import os
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    sync = AssetSync(api_key, api_secret)
    
    # 手动同步一次
    print("Starting manual sync...")
    result = sync.sync_assets()
    print(f"Sync result: {result}")
    
    # 启动自动同步
    print("\nStarting auto sync...")
    sync.start_auto_sync(interval=300)  # 5分钟同步一次
    
    # 运行一段时间后停止
    try:
        time.sleep(60)  # 运行1分钟
    finally:
        sync.stop_auto_sync()
        print("Sync stopped.")
