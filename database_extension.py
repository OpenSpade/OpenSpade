import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional


DB_FILE = "binance_futures.db"


def init_capital_pool_tables():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS capital_pool (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pool_name TEXT DEFAULT 'main',
            total_assets REAL NOT NULL DEFAULT 0,
            available_funds REAL NOT NULL DEFAULT 0,
            locked_funds REAL NOT NULL DEFAULT 0,
            allocation_ratio REAL NOT NULL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS strategies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id TEXT UNIQUE NOT NULL,
            strategy_type TEXT NOT NULL,
            symbol TEXT NOT NULL,
            initial_amount REAL NOT NULL,
            current_amount REAL NOT NULL DEFAULT 0,
            state TEXT NOT NULL DEFAULT 'active',
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fund_allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id TEXT NOT NULL,
            strategy_type TEXT NOT NULL,
            allocated_amount REAL NOT NULL,
            occupied_amount REAL NOT NULL,
            reserved_amount REAL NOT NULL DEFAULT 0,
            state TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS capital_pool_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation_type TEXT NOT NULL,
            strategy_id TEXT,
            strategy_type TEXT,
            amount REAL NOT NULL,
            pool_total_before REAL,
            pool_total_after REAL,
            pool_available_before REAL,
            pool_available_after REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS risk_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id TEXT NOT NULL,
            entry_price REAL NOT NULL,
            entry_time TEXT NOT NULL,
            initial_amount REAL NOT NULL,
            current_amount REAL NOT NULL,
            peak_amount REAL NOT NULL,
            stop_loss_price REAL,
            take_profit_price REAL,
            is_stopped INTEGER DEFAULT 0,
            stop_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS risk_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            risk_level TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            strategy_id TEXT,
            message TEXT,
            details TEXT,
            is_resolved INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_type TEXT NOT NULL, -- spot, futures
            asset TEXT NOT NULL, -- USDT, BTC, etc.
            free REAL NOT NULL DEFAULT 0,
            locked REAL NOT NULL DEFAULT 0,
            total REAL NOT NULL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(asset_type, asset)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS asset_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_type TEXT NOT NULL,
            asset TEXT NOT NULL,
            free REAL NOT NULL,
            locked REAL NOT NULL,
            total REAL NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS asset_sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sync_type TEXT NOT NULL, -- full, incremental
            status TEXT NOT NULL, -- success, failed
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP,
            error_message TEXT,
            records_synced INTEGER DEFAULT 0
        )
    ''')

    cursor.execute("SELECT COUNT(*) FROM capital_pool WHERE pool_name = 'main'")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO capital_pool (pool_name, total_assets, available_funds, locked_funds) VALUES ('main', 0, 0, 0)"
        )

    conn.commit()
    conn.close()
    print("Capital pool tables initialized successfully")


def save_strategy(strategy_data: Dict) -> bool:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        metadata = strategy_data.get('metadata')
        if isinstance(metadata, dict):
            metadata = json.dumps(metadata)

        cursor.execute('''
            INSERT OR REPLACE INTO strategies
            (strategy_id, strategy_type, symbol, initial_amount, current_amount, state, metadata, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            strategy_data['strategy_id'],
            strategy_data['strategy_type'],
            strategy_data['symbol'],
            strategy_data['initial_amount'],
            strategy_data['current_amount'],
            strategy_data['state'],
            metadata,
            datetime.now().isoformat()
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Failed to save strategy: {e}")
        return False
    finally:
        conn.close()


def get_strategy(strategy_id: str) -> Optional[Dict]:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT strategy_id, strategy_type, symbol, initial_amount, current_amount, state, metadata, created_at, updated_at
        FROM strategies
        WHERE strategy_id = ?
    ''', (strategy_id,))

    row = cursor.fetchone()
    conn.close()

    if row:
        metadata = row[6]
        if isinstance(metadata, str):
            metadata = json.loads(metadata) if metadata else {}

        return {
            'strategy_id': row[0],
            'strategy_type': row[1],
            'symbol': row[2],
            'initial_amount': row[3],
            'current_amount': row[4],
            'state': row[5],
            'metadata': metadata,
            'created_at': row[6],
            'updated_at': row[7]
        }
    return None


def get_all_strategies(state: str = None) -> List[Dict]:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    if state:
        cursor.execute('''
            SELECT strategy_id, strategy_type, symbol, initial_amount, current_amount, state, metadata
            FROM strategies
            WHERE state = ?
            ORDER BY created_at DESC
        ''', (state,))
    else:
        cursor.execute('''
            SELECT strategy_id, strategy_type, symbol, initial_amount, current_amount, state, metadata
            FROM strategies
            ORDER BY created_at DESC
        ''')

    rows = cursor.fetchall()
    conn.close()

    strategies = []
    for row in rows:
        metadata = row[6]
        if isinstance(metadata, str):
            metadata = json.loads(metadata) if metadata else {}

        strategies.append({
            'strategy_id': row[0],
            'strategy_type': row[1],
            'symbol': row[2],
            'initial_amount': row[3],
            'current_amount': row[4],
            'state': row[5],
            'metadata': metadata
        })
    return strategies


def update_pool_status(pool_data: Dict) -> bool:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE capital_pool
            SET total_assets = ?, available_funds = ?, locked_funds = ?, allocation_ratio = ?, updated_at = ?
            WHERE pool_name = 'main'
        ''', (
            pool_data['total_assets'],
            pool_data['available_funds'],
            pool_data['locked_funds'],
            pool_data['allocation_ratio'],
            datetime.now().isoformat()
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Failed to update pool status: {e}")
        return False
    finally:
        conn.close()


def get_pool_status() -> Dict:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT total_assets, available_funds, locked_funds, allocation_ratio, updated_at
        FROM capital_pool
        WHERE pool_name = 'main'
    ''')

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            'total_assets': row[0],
            'available_funds': row[1],
            'locked_funds': row[2],
            'allocation_ratio': row[3],
            'updated_at': row[4]
        }
    return {}


def log_capital_operation(operation_data: Dict) -> bool:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO capital_pool_log
            (operation_type, strategy_id, strategy_type, amount, pool_total_before, pool_total_after,
             pool_available_before, pool_available_after, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            operation_data['operation_type'],
            operation_data.get('strategy_id'),
            operation_data.get('strategy_type'),
            operation_data['amount'],
            operation_data.get('pool_total_before'),
            operation_data.get('pool_total_after'),
            operation_data.get('pool_available_before'),
            operation_data.get('pool_available_after'),
            datetime.now().isoformat()
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Failed to log capital operation: {e}")
        return False
    finally:
        conn.close()


def save_risk_record(record_data: Dict) -> bool:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT OR REPLACE INTO risk_records
            (strategy_id, entry_price, entry_time, initial_amount, current_amount, peak_amount,
             stop_loss_price, take_profit_price, is_stopped, stop_reason, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            record_data['strategy_id'],
            record_data['entry_price'],
            record_data['entry_time'],
            record_data['initial_amount'],
            record_data['current_amount'],
            record_data['peak_amount'],
            record_data.get('stop_loss_price'),
            record_data.get('take_profit_price'),
            1 if record_data.get('is_stopped') else 0,
            record_data.get('stop_reason'),
            datetime.now().isoformat()
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Failed to save risk record: {e}")
        return False
    finally:
        conn.close()


def log_risk_alert(alert_data: Dict) -> bool:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        details = alert_data.get('details')
        if isinstance(details, dict):
            details = json.dumps(details)

        cursor.execute('''
            INSERT INTO risk_alerts
            (risk_level, alert_type, strategy_id, message, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            alert_data['risk_level'],
            alert_data['alert_type'],
            alert_data.get('strategy_id'),
            alert_data.get('message'),
            details,
            datetime.now().isoformat()
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Failed to log risk alert: {e}")
        return False
    finally:
        conn.close()


def get_pool_statistics() -> Dict:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM strategies WHERE state = 'active'")
    active_strategies = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM strategies")
    total_strategies = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(allocated_amount) FROM fund_allocations WHERE state = 'active'")
    total_allocated = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM risk_alerts WHERE is_resolved = 0")
    unresolved_alerts = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM risk_records WHERE is_stopped = 1")
    stopped_strategies = cursor.fetchone()[0]

    conn.close()

    return {
        'active_strategies': active_strategies,
        'total_strategies': total_strategies,
        'total_allocated': total_allocated,
        'unresolved_alerts': unresolved_alerts,
        'stopped_strategies': stopped_strategies
    }


def save_asset(asset_data: Dict) -> bool:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT OR REPLACE INTO assets
            (asset_type, asset, free, locked, total, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            asset_data['asset_type'],
            asset_data['asset'],
            asset_data['free'],
            asset_data['locked'],
            asset_data['total'],
            datetime.now().isoformat()
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Failed to save asset: {e}")
        return False
    finally:
        conn.close()


def get_assets(asset_type: str = None) -> List[Dict]:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    if asset_type:
        cursor.execute('''
            SELECT asset_type, asset, free, locked, total, updated_at
            FROM assets
            WHERE asset_type = ?
            ORDER BY asset
        ''', (asset_type,))
    else:
        cursor.execute('''
            SELECT asset_type, asset, free, locked, total, updated_at
            FROM assets
            ORDER BY asset_type, asset
        ''')

    rows = cursor.fetchall()
    conn.close()

    assets = []
    for row in rows:
        assets.append({
            'asset_type': row[0],
            'asset': row[1],
            'free': row[2],
            'locked': row[3],
            'total': row[4],
            'updated_at': row[5]
        })
    return assets


def log_asset_history(asset_data: Dict) -> bool:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO asset_history
            (asset_type, asset, free, locked, total, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            asset_data['asset_type'],
            asset_data['asset'],
            asset_data['free'],
            asset_data['locked'],
            asset_data['total'],
            datetime.now().isoformat()
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Failed to log asset history: {e}")
        return False
    finally:
        conn.close()


def log_asset_sync(sync_data: Dict) -> bool:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO asset_sync_log
            (sync_type, status, start_time, end_time, error_message, records_synced)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            sync_data['sync_type'],
            sync_data['status'],
            sync_data['start_time'],
            sync_data.get('end_time'),
            sync_data.get('error_message'),
            sync_data.get('records_synced', 0)
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Failed to log asset sync: {e}")
        return False
    finally:
        conn.close()


def get_asset_statistics() -> Dict:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM assets")
    total_assets = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(total) FROM assets WHERE asset_type = 'spot'")
    spot_total = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(total) FROM assets WHERE asset_type = 'futures'")
    futures_total = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM asset_sync_log WHERE status = 'success' AND start_time >= datetime('now', '-24 hours')")
    successful_syncs_24h = cursor.fetchone()[0]

    conn.close()

    return {
        'total_assets': total_assets,
        'spot_total': spot_total,
        'futures_total': futures_total,
        'total_portfolio': spot_total + futures_total,
        'successful_syncs_24h': successful_syncs_24h
    }


if __name__ == "__main__":
    init_capital_pool_tables()
    print("\nDatabase extension initialized successfully!")
    print("\nPool statistics:")
    stats = get_pool_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
