import unittest
import sqlite3
import os
import sys
import shutil
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from openspade.db.database_extension import (
    init_capital_pool_tables,
    save_strategy,
    get_strategy,
    get_all_strategies,
    update_pool_status,
    get_pool_status,
    log_capital_operation,
    save_risk_record,
    log_risk_alert,
    get_pool_statistics,
    save_asset,
    get_assets,
    log_asset_history,
    log_asset_sync,
    get_asset_statistics,
)


REAL_DB_PATH = "/.openspade/database.db"
TEST_DB_FILE = "test_openspade_unit.db"


class TestOpenspadeDBOperations(unittest.TestCase):
    """Test suite for openspade.db database operations"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_db_file = TEST_DB_FILE
        if os.path.exists(self.test_db_file):
            os.remove(self.test_db_file)
        init_capital_pool_tables(self.test_db_file)

    def tearDown(self):
        """Clean up after tests"""
        if os.path.exists(self.test_db_file):
            os.remove(self.test_db_file)

    def test_init_tables_creates_all_required_tables(self):
        """Test that init_capital_pool_tables creates all required tables"""
        self.assertTrue(os.path.exists(self.test_db_file))
        conn = sqlite3.connect(self.test_db_file)
        cursor = conn.cursor()

        expected_tables = [
            'capital_pool', 'strategies', 'fund_allocations',
            'capital_pool_log', 'risk_records', 'risk_alerts',
            'assets', 'asset_history', 'asset_sync_log'
        ]

        for table in expected_tables:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,)
            )
            self.assertIsNotNone(cursor.fetchone(), f"Table {table} not found")

        conn.close()

    def test_init_creates_default_main_pool(self):
        """Test that initialization creates default 'main' capital pool"""
        conn = sqlite3.connect(self.test_db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM capital_pool WHERE pool_name = 'main'")
        count = cursor.fetchone()[0]
        conn.close()
        self.assertEqual(count, 1)

    def test_save_strategy_with_metadata(self):
        """Test saving a strategy with metadata"""
        strategy_data = {
            'strategy_id': 'test_strategy_meta',
            'strategy_type': 'trend_following',
            'symbol': 'BNBUSDT',
            'initial_amount': 500.0,
            'current_amount': 450.0,
            'state': 'active',
            'metadata': {'ema_period': 20, 'stop_loss': 0.02}
        }

        result = save_strategy(strategy_data, self.test_db_file)
        self.assertTrue(result)

        saved = get_strategy('test_strategy_meta', self.test_db_file)
        self.assertIsNotNone(saved)
        self.assertEqual(saved['strategy_id'], 'test_strategy_meta')
        self.assertEqual(saved['strategy_type'], 'trend_following')
        self.assertEqual(saved['symbol'], 'BNBUSDT')
        self.assertEqual(saved['initial_amount'], 500.0)
        self.assertEqual(saved['current_amount'], 450.0)
        self.assertEqual(saved['state'], 'active')
        self.assertEqual(saved['metadata'], {'ema_period': 20, 'stop_loss': 0.02})

    def test_save_strategy_replace_existing(self):
        """Test that saving strategy with same ID replaces existing"""
        strategy1 = {
            'strategy_id': 'replace_test',
            'strategy_type': 'momentum',
            'symbol': 'ETHUSDT',
            'initial_amount': 1000.0,
            'current_amount': 1000.0,
            'state': 'active',
            'metadata': {}
        }
        save_strategy(strategy1, self.test_db_file)

        strategy2 = {
            'strategy_id': 'replace_test',
            'strategy_type': 'momentum',
            'symbol': 'ETHUSDT',
            'initial_amount': 1000.0,
            'current_amount': 800.0,
            'state': 'inactive',
            'metadata': {}
        }
        result = save_strategy(strategy2, self.test_db_file)
        self.assertTrue(result)

        strategies = get_all_strategies(db_file=self.test_db_file)
        self.assertEqual(len(strategies), 1)
        self.assertEqual(strategies[0]['current_amount'], 800.0)
        self.assertEqual(strategies[0]['state'], 'inactive')

    def test_get_strategy_not_found(self):
        """Test getting non-existent strategy returns None"""
        result = get_strategy('nonexistent_strategy', self.test_db_file)
        self.assertIsNone(result)

    def test_get_all_strategies_empty(self):
        """Test getting all strategies when none exist"""
        strategies = get_all_strategies(db_file=self.test_db_file)
        self.assertEqual(len(strategies), 0)

    def test_get_all_strategies_filter_by_state(self):
        """Test filtering strategies by state"""
        strategies_data = [
            {'strategy_id': 's1', 'strategy_type': 'mean_reversion', 'symbol': 'BTCUSDT',
             'initial_amount': 1000.0, 'current_amount': 1000.0, 'state': 'active', 'metadata': {}},
            {'strategy_id': 's2', 'strategy_type': 'momentum', 'symbol': 'ETHUSDT',
             'initial_amount': 500.0, 'current_amount': 500.0, 'state': 'active', 'metadata': {}},
            {'strategy_id': 's3', 'strategy_type': 'trend_following', 'symbol': 'BNBUSDT',
             'initial_amount': 300.0, 'current_amount': 300.0, 'state': 'stopped', 'metadata': {}},
        ]
        for s in strategies_data:
            save_strategy(s, self.test_db_file)

        all_strategies = get_all_strategies(db_file=self.test_db_file)
        self.assertEqual(len(all_strategies), 3)

        active = get_all_strategies('active', db_file=self.test_db_file)
        self.assertEqual(len(active), 2)

        stopped = get_all_strategies('stopped', db_file=self.test_db_file)
        self.assertEqual(len(stopped), 1)

    def test_update_pool_status(self):
        """Test updating capital pool status"""
        pool_data = {
            'total_assets': 50000.0,
            'available_funds': 30000.0,
            'locked_funds': 20000.0,
            'allocation_ratio': 0.4
        }

        result = update_pool_status(pool_data, self.test_db_file)
        self.assertTrue(result)

        status = get_pool_status(self.test_db_file)
        self.assertEqual(status['total_assets'], 50000.0)
        self.assertEqual(status['available_funds'], 30000.0)
        self.assertEqual(status['locked_funds'], 20000.0)
        self.assertEqual(status['allocation_ratio'], 0.4)

    def test_get_pool_status_default(self):
        """Test getting default pool status after initialization"""
        status = get_pool_status(self.test_db_file)
        self.assertEqual(status['total_assets'], 0)
        self.assertEqual(status['available_funds'], 0)
        self.assertEqual(status['locked_funds'], 0)

    def test_log_capital_operation_deposit(self):
        """Test logging deposit operation"""
        operation_data = {
            'operation_type': 'deposit',
            'strategy_id': 'test_strategy',
            'strategy_type': 'mean_reversion',
            'amount': 5000.0,
            'pool_total_before': 10000.0,
            'pool_total_after': 15000.0,
            'pool_available_before': 8000.0,
            'pool_available_after': 13000.0
        }

        result = log_capital_operation(operation_data, self.test_db_file)
        self.assertTrue(result)

        conn = sqlite3.connect(self.test_db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM capital_pool_log WHERE operation_type = 'deposit'")
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[1], 'deposit')
        self.assertEqual(row[4], 5000.0)

    def test_log_capital_operation_withdrawal(self):
        """Test logging withdrawal operation"""
        operation_data = {
            'operation_type': 'withdrawal',
            'strategy_id': 'test_strategy',
            'strategy_type': 'momentum',
            'amount': 2000.0,
            'pool_total_before': 10000.0,
            'pool_total_after': 8000.0,
            'pool_available_before': 6000.0,
            'pool_available_after': 4000.0
        }

        result = log_capital_operation(operation_data, self.test_db_file)
        self.assertTrue(result)

        conn = sqlite3.connect(self.test_db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM capital_pool_log WHERE operation_type = 'withdrawal'")
        count = cursor.fetchone()[0]
        conn.close()
        self.assertEqual(count, 1)

    def test_save_and_get_risk_record(self):
        """Test saving and retrieving risk record"""
        entry_time = datetime.now().isoformat()
        record_data = {
            'strategy_id': 'risk_test_strategy',
            'entry_price': 45000.0,
            'entry_time': entry_time,
            'initial_amount': 1000.0,
            'current_amount': 1100.0,
            'peak_amount': 1200.0,
            'stop_loss_price': 40000.0,
            'take_profit_price': 50000.0,
            'is_stopped': False,
            'stop_reason': None
        }

        result = save_risk_record(record_data, self.test_db_file)
        self.assertTrue(result)

        conn = sqlite3.connect(self.test_db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM risk_records WHERE strategy_id = 'risk_test_strategy'")
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[1], 'risk_test_strategy')
        self.assertEqual(row[2], 45000.0)
        self.assertEqual(row[4], 1000.0)
        self.assertEqual(row[5], 1100.0)
        self.assertEqual(row[9], 0)

    def test_save_risk_record_stopped(self):
        """Test saving risk record for stopped strategy"""
        record_data = {
            'strategy_id': 'stopped_strategy',
            'entry_price': 50000.0,
            'entry_time': datetime.now().isoformat(),
            'initial_amount': 2000.0,
            'current_amount': 1800.0,
            'peak_amount': 2200.0,
            'stop_loss_price': 45000.0,
            'take_profit_price': 55000.0,
            'is_stopped': True,
            'stop_reason': 'stop_loss_triggered'
        }

        result = save_risk_record(record_data, self.test_db_file)
        self.assertTrue(result)

        conn = sqlite3.connect(self.test_db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT is_stopped, stop_reason FROM risk_records WHERE strategy_id = 'stopped_strategy'")
        row = cursor.fetchone()
        conn.close()

        self.assertEqual(row[0], 1)
        self.assertEqual(row[1], 'stop_loss_triggered')

    def test_log_risk_alert(self):
        """Test logging risk alert"""
        alert_data = {
            'risk_level': 'critical',
            'alert_type': 'drawdown_exceeded',
            'strategy_id': 'alert_test_strategy',
            'message': 'Drawdown exceeded 20%',
            'details': {'max_drawdown': 0.22, 'threshold': 0.20}
        }

        result = log_risk_alert(alert_data, self.test_db_file)
        self.assertTrue(result)

        conn = sqlite3.connect(self.test_db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM risk_alerts WHERE risk_level = 'critical'")
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[1], 'critical')
        self.assertEqual(row[2], 'drawdown_exceeded')

    def test_get_pool_statistics(self):
        """Test getting pool statistics"""
        strategy = {
            'strategy_id': 'stats_test',
            'strategy_type': 'momentum',
            'symbol': 'BTCUSDT',
            'initial_amount': 1000.0,
            'current_amount': 900.0,
            'state': 'active',
            'metadata': {}
        }
        save_strategy(strategy, self.test_db_file)

        alert = {
            'risk_level': 'medium',
            'alert_type': 'position_warning',
            'strategy_id': 'stats_test',
            'message': 'Position size warning',
            'details': {}
        }
        log_risk_alert(alert, self.test_db_file)

        risk_record = {
            'strategy_id': 'stats_test',
            'entry_price': 45000.0,
            'entry_time': datetime.now().isoformat(),
            'initial_amount': 1000.0,
            'current_amount': 900.0,
            'peak_amount': 1000.0,
            'stop_loss_price': 40000.0,
            'take_profit_price': 50000.0,
            'is_stopped': True,
            'stop_reason': 'manual'
        }
        save_risk_record(risk_record, self.test_db_file)

        stats = get_pool_statistics(self.test_db_file)

        self.assertEqual(stats['active_strategies'], 1)
        self.assertEqual(stats['total_strategies'], 1)
        self.assertEqual(stats['unresolved_alerts'], 1)
        self.assertEqual(stats['stopped_strategies'], 1)

    def test_save_and_get_assets(self):
        """Test saving and retrieving assets"""
        assets_data = [
            {'asset_type': 'spot', 'asset': 'USDT', 'free': 5000.0, 'locked': 1000.0, 'total': 6000.0},
            {'asset_type': 'spot', 'asset': 'BTC', 'free': 0.5, 'locked': 0.1, 'total': 0.6},
            {'asset_type': 'futures', 'asset': 'USDT', 'free': 3000.0, 'locked': 500.0, 'total': 3500.0},
        ]

        for asset in assets_data:
            result = save_asset(asset, self.test_db_file)
            self.assertTrue(result)

        all_assets = get_assets(db_file=self.test_db_file)
        self.assertEqual(len(all_assets), 3)

        spot_assets = get_assets('spot', db_file=self.test_db_file)
        self.assertEqual(len(spot_assets), 2)

        futures_assets = get_assets('futures', db_file=self.test_db_file)
        self.assertEqual(len(futures_assets), 1)

        usdt_spot = next((a for a in spot_assets if a['asset'] == 'USDT'), None)
        self.assertIsNotNone(usdt_spot)
        self.assertEqual(usdt_spot['total'], 6000.0)

    def test_save_asset_updates_existing(self):
        """Test that saving asset with same type and name updates existing"""
        asset1 = {'asset_type': 'spot', 'asset': 'ETH', 'free': 100.0, 'locked': 50.0, 'total': 150.0}
        save_asset(asset1, self.test_db_file)

        asset2 = {'asset_type': 'spot', 'asset': 'ETH', 'free': 200.0, 'locked': 50.0, 'total': 250.0}
        result = save_asset(asset2, self.test_db_file)
        self.assertTrue(result)

        assets = get_assets('spot', self.test_db_file)
        eth_asset = next((a for a in assets if a['asset'] == 'ETH'), None)
        self.assertEqual(eth_asset['total'], 250.0)

    def test_log_asset_history(self):
        """Test logging asset history"""
        history_data = {
            'asset_type': 'spot',
            'asset': 'BNB',
            'free': 50.0,
            'locked': 10.0,
            'total': 60.0
        }

        result = log_asset_history(history_data, self.test_db_file)
        self.assertTrue(result)

        conn = sqlite3.connect(self.test_db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM asset_history WHERE asset = 'BNB'")
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[1], 'spot')
        self.assertEqual(row[2], 'BNB')
        self.assertEqual(row[5], 60.0)

    def test_log_asset_sync(self):
        """Test logging asset sync operation"""
        sync_data = {
            'sync_type': 'incremental',
            'status': 'success',
            'start_time': datetime.now().isoformat(),
            'end_time': datetime.now().isoformat(),
            'error_message': None,
            'records_synced': 10
        }

        result = log_asset_sync(sync_data, self.test_db_file)
        self.assertTrue(result)

        conn = sqlite3.connect(self.test_db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM asset_sync_log WHERE sync_type = 'incremental'")
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[1], 'incremental')
        self.assertEqual(row[2], 'success')
        self.assertEqual(row[6], 10)

    def test_log_asset_sync_failed(self):
        """Test logging failed asset sync"""
        sync_data = {
            'sync_type': 'full',
            'status': 'failed',
            'start_time': datetime.now().isoformat(),
            'end_time': datetime.now().isoformat(),
            'error_message': 'Connection timeout',
            'records_synced': 0
        }

        result = log_asset_sync(sync_data, self.test_db_file)
        self.assertTrue(result)

        conn = sqlite3.connect(self.test_db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT status, error_message FROM asset_sync_log WHERE status = 'failed'")
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], 'failed')
        self.assertEqual(row[1], 'Connection timeout')

    def test_get_asset_statistics(self):
        """Test getting asset statistics"""
        assets = [
            {'asset_type': 'spot', 'asset': 'USDT', 'free': 5000.0, 'locked': 1000.0, 'total': 6000.0},
            {'asset_type': 'spot', 'asset': 'BTC', 'free': 1.0, 'locked': 0.5, 'total': 1.5},
            {'asset_type': 'futures', 'asset': 'USDT', 'free': 3000.0, 'locked': 500.0, 'total': 3500.0},
        ]

        for asset in assets:
            save_asset(asset, self.test_db_file)

        sync_data = {
            'sync_type': 'full',
            'status': 'success',
            'start_time': datetime.now().isoformat(),
            'end_time': datetime.now().isoformat(),
            'records_synced': 3
        }
        log_asset_sync(sync_data, self.test_db_file)

        stats = get_asset_statistics(self.test_db_file)

        self.assertEqual(stats['total_assets'], 3)
        self.assertEqual(stats['spot_total'], 6001.5)
        self.assertEqual(stats['futures_total'], 3500.0)
        self.assertEqual(stats['total_portfolio'], 6001.5 + 3500.0)


class TestRealOpenspadeDB(unittest.TestCase):
    """Integration tests that run against the real openspade.db database"""

    @classmethod
    def setUpClass(cls):
        """Set up connection to real database"""
        if os.path.exists(REAL_DB_PATH):
            cls.real_db_available = True
            conn = sqlite3.connect(REAL_DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            cls.tables = [row[0] for row in cursor.fetchall()]
            conn.close()
        else:
            cls.real_db_available = False

    def test_real_database_exists(self):
        """Test that real database file exists"""
        if not self.real_db_available:
            self.skipTest(f"Real database not found at {REAL_DB_PATH}")
        self.assertTrue(os.path.exists(REAL_DB_PATH))

    def test_real_database_has_required_tables(self):
        """Test that real database has all required tables"""
        if not self.real_db_available:
            self.skipTest(f"Real database not found at {REAL_DB_PATH}")

        required_tables = [
            'capital_pool', 'strategies', 'fund_allocations',
            'capital_pool_log', 'risk_records', 'risk_alerts',
            'assets', 'asset_history', 'asset_sync_log'
        ]

        for table in required_tables:
            self.assertIn(table, self.tables, f"Table {table} not found in real database")

    def test_real_database_pool_status(self):
        """Test reading pool status from real database"""
        if not self.real_db_available:
            self.skipTest(f"Real database not found at {REAL_DB_PATH}")

        status = get_pool_status(REAL_DB_PATH)
        self.assertIsInstance(status, dict)
        self.assertIn('total_assets', status)
        self.assertIn('available_funds', status)
        self.assertIn('locked_funds', status)

    def test_real_database_get_strategies(self):
        """Test reading strategies from real database"""
        if not self.real_db_available:
            self.skipTest(f"Real database not found at {REAL_DB_PATH}")

        strategies = get_all_strategies(db_file=REAL_DB_PATH)
        self.assertIsInstance(strategies, list)

        for strategy in strategies:
            self.assertIn('strategy_id', strategy)
            self.assertIn('strategy_type', strategy)
            self.assertIn('symbol', strategy)

    def test_real_database_get_assets(self):
        """Test reading assets from real database"""
        if not self.real_db_available:
            self.skipTest(f"Real database not found at {REAL_DB_PATH}")

        assets = get_assets(db_file=REAL_DB_PATH)
        self.assertIsInstance(assets, list)

        for asset in assets:
            self.assertIn('asset_type', asset)
            self.assertIn('asset', asset)
            self.assertIn('total', asset)

    def test_real_database_pool_statistics(self):
        """Test reading pool statistics from real database"""
        if not self.real_db_available:
            self.skipTest(f"Real database not found at {REAL_DB_PATH}")

        stats = get_pool_statistics(REAL_DB_PATH)
        self.assertIsInstance(stats, dict)
        self.assertIn('active_strategies', stats)
        self.assertIn('total_strategies', stats)
        self.assertIn('unresolved_alerts', stats)

    def test_real_database_asset_statistics(self):
        """Test reading asset statistics from real database"""
        if not self.real_db_available:
            self.skipTest(f"Real database not found at {REAL_DB_PATH}")

        stats = get_asset_statistics(REAL_DB_PATH)
        self.assertIsInstance(stats, dict)
        self.assertIn('total_assets', stats)
        self.assertIn('spot_total', stats)
        self.assertIn('futures_total', stats)


if __name__ == '__main__':
    unittest.main()
