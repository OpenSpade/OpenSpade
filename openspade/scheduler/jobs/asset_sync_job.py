import os
import time
from datetime import datetime
from typing import Dict

from openspade.gateway.binance_connector import BinanceConnector
from openspade.db.database_extension import (
    save_asset, log_asset_history, log_asset_sync, get_asset_statistics,
)
from openspade.scheduler import scheduled_job

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds


@scheduled_job('asset_sync', trigger='interval', seconds=300)
def sync_assets() -> Dict:
    """Sync spot and futures assets from Binance."""
    api_key = os.environ.get('BINANCE_API_KEY')
    api_secret = os.environ.get('BINANCE_API_SECRET')
    binance = BinanceConnector(api_key, api_secret)

    sync_data = {
        'sync_type': 'full',
        'status': 'success',
        'start_time': datetime.now().isoformat(),
        'records_synced': 0,
    }

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            assets_data = binance.get_all_assets()

            # Sync spot assets
            for asset in assets_data.get('spot', []):
                asset_data = {
                    'asset_type': 'spot',
                    'asset': asset['asset'],
                    'free': asset['free'],
                    'locked': asset['locked'],
                    'total': asset['total'],
                }
                save_asset(asset_data)
                log_asset_history(asset_data)
                sync_data['records_synced'] += 1

            # Sync futures assets
            for asset in assets_data.get('futures', []):
                asset_data = {
                    'asset_type': 'futures',
                    'asset': asset['asset'],
                    'free': asset['free'],
                    'locked': asset['locked'],
                    'total': asset['total'],
                }
                save_asset(asset_data)
                log_asset_history(asset_data)
                sync_data['records_synced'] += 1

            sync_data['end_time'] = datetime.now().isoformat()
            print(f"Asset sync completed. Synced {sync_data['records_synced']} records.")
            break  # success, exit retry loop

        except Exception as e:
            last_error = e
            print(f"Asset sync failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    else:
        # All retries exhausted
        sync_data['status'] = 'failed'
        sync_data['error_message'] = str(last_error)
        sync_data['end_time'] = datetime.now().isoformat()

    log_asset_sync(sync_data)
    return sync_data


def get_sync_status() -> Dict:
    """Get current asset sync status and statistics."""
    stats = get_asset_statistics()
    return {'asset_statistics': stats}
