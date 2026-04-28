import unittest
import sqlite3
import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
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
    DB_FILE
)

class TestDatabaseExtension(unittest.TestCase):
    """测试数据库扩展功能"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 测试数据库文件路径
        self.test_db_file = "test_openspade.db"
        # 确保测试数据库不存在
        if os.path.exists(self.test_db_file):
            os.remove(self.test_db_file)
        # 初始化数据库表
        init_capital_pool_tables(self.test_db_file)
    
    def tearDown(self):
        """测试后的清理工作"""
        # 删除测试数据库文件
        if os.path.exists(self.test_db_file):
            os.remove(self.test_db_file)
    
    def test_init_capital_pool_tables(self):
        """测试初始化资金池表"""
        # 检查数据库文件是否存在
        self.assertTrue(os.path.exists(self.test_db_file))
        
        # 检查表是否创建成功
        conn = sqlite3.connect(self.test_db_file)
        cursor = conn.cursor()
        
        # 检查capital_pool表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='capital_pool'")
        self.assertIsNotNone(cursor.fetchone())
        
        # 检查strategies表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='strategies'")
        self.assertIsNotNone(cursor.fetchone())
        
        # 检查fund_allocations表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fund_allocations'")
        self.assertIsNotNone(cursor.fetchone())
        
        # 检查capital_pool_log表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='capital_pool_log'")
        self.assertIsNotNone(cursor.fetchone())
        
        # 检查risk_records表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='risk_records'")
        self.assertIsNotNone(cursor.fetchone())
        
        # 检查risk_alerts表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='risk_alerts'")
        self.assertIsNotNone(cursor.fetchone())
        
        # 检查assets表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='assets'")
        self.assertIsNotNone(cursor.fetchone())
        
        # 检查asset_history表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='asset_history'")
        self.assertIsNotNone(cursor.fetchone())
        
        # 检查asset_sync_log表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='asset_sync_log'")
        self.assertIsNotNone(cursor.fetchone())
        
        # 检查是否创建了默认的main资金池
        cursor.execute("SELECT COUNT(*) FROM capital_pool WHERE pool_name = 'main'")
        self.assertEqual(cursor.fetchone()[0], 1)
        
        conn.close()
    
    def test_save_and_get_strategy(self):
        """测试保存和获取策略"""
        # 测试数据
        strategy_data = {
            'strategy_id': 'test_strategy_1',
            'strategy_type': 'mean_reversion',
            'symbol': 'BTCUSDT',
            'initial_amount': 1000.0,
            'current_amount': 1000.0,
            'state': 'active',
            'metadata': {'param1': 'value1', 'param2': 'value2'}
        }
        
        # 保存策略
        result = save_strategy(strategy_data, self.test_db_file)
        self.assertTrue(result)
        
        # 获取策略
        strategy = get_strategy('test_strategy_1', self.test_db_file)
        self.assertIsNotNone(strategy)
        self.assertEqual(strategy['strategy_id'], 'test_strategy_1')
        self.assertEqual(strategy['strategy_type'], 'mean_reversion')
        self.assertEqual(strategy['symbol'], 'BTCUSDT')
        self.assertEqual(strategy['initial_amount'], 1000.0)
        self.assertEqual(strategy['current_amount'], 1000.0)
        self.assertEqual(strategy['state'], 'active')
        self.assertEqual(strategy['metadata'], {'param1': 'value1', 'param2': 'value2'})
    
    def test_get_all_strategies(self):
        """测试获取所有策略"""
        # 保存两个策略
        strategy_data1 = {
            'strategy_id': 'test_strategy_1',
            'strategy_type': 'mean_reversion',
            'symbol': 'BTCUSDT',
            'initial_amount': 1000.0,
            'current_amount': 1000.0,
            'state': 'active',
            'metadata': {}
        }
        
        strategy_data2 = {
            'strategy_id': 'test_strategy_2',
            'strategy_type': 'momentum',
            'symbol': 'ETHUSDT',
            'initial_amount': 500.0,
            'current_amount': 500.0,
            'state': 'inactive',
            'metadata': {}
        }
        
        save_strategy(strategy_data1, self.test_db_file)
        save_strategy(strategy_data2, self.test_db_file)
        
        # 获取所有策略
        all_strategies = get_all_strategies(db_file=self.test_db_file)
        self.assertEqual(len(all_strategies), 2)
        
        # 获取指定状态的策略
        active_strategies = get_all_strategies('active', db_file=self.test_db_file)
        self.assertEqual(len(active_strategies), 1)
        self.assertEqual(active_strategies[0]['strategy_id'], 'test_strategy_1')
        
        inactive_strategies = get_all_strategies('inactive', db_file=self.test_db_file)
        self.assertEqual(len(inactive_strategies), 1)
        self.assertEqual(inactive_strategies[0]['strategy_id'], 'test_strategy_2')
    
    def test_update_and_get_pool_status(self):
        """测试更新和获取资金池状态"""
        # 测试数据
        pool_data = {
            'total_assets': 10000.0,
            'available_funds': 5000.0,
            'locked_funds': 5000.0,
            'allocation_ratio': 0.5
        }
        
        # 更新资金池状态
        result = update_pool_status(pool_data, self.test_db_file)
        self.assertTrue(result)
        
        # 获取资金池状态
        pool_status = get_pool_status(self.test_db_file)
        self.assertEqual(pool_status['total_assets'], 10000.0)
        self.assertEqual(pool_status['available_funds'], 5000.0)
        self.assertEqual(pool_status['locked_funds'], 5000.0)
        self.assertEqual(pool_status['allocation_ratio'], 0.5)
    
    def test_log_capital_operation(self):
        """测试记录资金操作"""
        # 测试数据
        operation_data = {
            'operation_type': 'deposit',
            'strategy_id': 'test_strategy_1',
            'strategy_type': 'mean_reversion',
            'amount': 1000.0,
            'pool_total_before': 5000.0,
            'pool_total_after': 6000.0,
            'pool_available_before': 2000.0,
            'pool_available_after': 3000.0
        }
        
        # 记录资金操作
        result = log_capital_operation(operation_data, self.test_db_file)
        self.assertTrue(result)
        
        # 验证记录是否保存
        conn = sqlite3.connect(self.test_db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM capital_pool_log WHERE operation_type = 'deposit'")
        self.assertEqual(cursor.fetchone()[0], 1)
        conn.close()
    
    def test_save_risk_record(self):
        """测试保存风险记录"""
        # 测试数据
        record_data = {
            'strategy_id': 'test_strategy_1',
            'entry_price': 50000.0,
            'entry_time': datetime.now().isoformat(),
            'initial_amount': 1000.0,
            'current_amount': 1000.0,
            'peak_amount': 1200.0,
            'stop_loss_price': 45000.0,
            'take_profit_price': 55000.0,
            'is_stopped': False,
            'stop_reason': None
        }
        
        # 保存风险记录
        result = save_risk_record(record_data, self.test_db_file)
        self.assertTrue(result)
        
        # 验证记录是否保存
        conn = sqlite3.connect(self.test_db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM risk_records WHERE strategy_id = 'test_strategy_1'")
        self.assertEqual(cursor.fetchone()[0], 1)
        conn.close()
    
    def test_log_risk_alert(self):
        """测试记录风险警报"""
        # 测试数据
        alert_data = {
            'risk_level': 'high',
            'alert_type': 'price_drop',
            'strategy_id': 'test_strategy_1',
            'message': 'Price dropped below threshold',
            'details': {'threshold': 45000.0, 'current_price': 44000.0}
        }
        
        # 记录风险警报
        result = log_risk_alert(alert_data, self.test_db_file)
        self.assertTrue(result)
        
        # 验证记录是否保存
        conn = sqlite3.connect(self.test_db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM risk_alerts WHERE risk_level = 'high'")
        self.assertEqual(cursor.fetchone()[0], 1)
        conn.close()
    
    def test_get_pool_statistics(self):
        """测试获取资金池统计信息"""
        # 保存一个策略
        strategy_data = {
            'strategy_id': 'test_strategy_1',
            'strategy_type': 'mean_reversion',
            'symbol': 'BTCUSDT',
            'initial_amount': 1000.0,
            'current_amount': 1000.0,
            'state': 'active',
            'metadata': {}
        }
        save_strategy(strategy_data, self.test_db_file)
        
        # 记录一个风险警报
        alert_data = {
            'risk_level': 'high',
            'alert_type': 'price_drop',
            'strategy_id': 'test_strategy_1',
            'message': 'Price dropped below threshold',
            'details': {}
        }
        log_risk_alert(alert_data, self.test_db_file)
        
        # 记录一个风险记录
        record_data = {
            'strategy_id': 'test_strategy_1',
            'entry_price': 50000.0,
            'entry_time': datetime.now().isoformat(),
            'initial_amount': 1000.0,
            'current_amount': 1000.0,
            'peak_amount': 1200.0,
            'stop_loss_price': 45000.0,
            'take_profit_price': 55000.0,
            'is_stopped': True,
            'stop_reason': 'Hit stop loss'
        }
        save_risk_record(record_data, self.test_db_file)
        
        # 获取统计信息
        stats = get_pool_statistics(self.test_db_file)
        self.assertEqual(stats['active_strategies'], 1)
        self.assertEqual(stats['total_strategies'], 1)
        self.assertEqual(stats['unresolved_alerts'], 1)
        self.assertEqual(stats['stopped_strategies'], 1)
    
    def test_save_and_get_assets(self):
        """测试保存和获取资产"""
        # 测试数据
        asset_data = {
            'asset_type': 'spot',
            'asset': 'USDT',
            'free': 1000.0,
            'locked': 500.0,
            'total': 1500.0
        }
        
        # 保存资产
        result = save_asset(asset_data, self.test_db_file)
        self.assertTrue(result)
        
        # 获取所有资产
        all_assets = get_assets(db_file=self.test_db_file)
        self.assertEqual(len(all_assets), 1)
        
        # 获取指定类型的资产
        spot_assets = get_assets('spot', db_file=self.test_db_file)
        self.assertEqual(len(spot_assets), 1)
        self.assertEqual(spot_assets[0]['asset'], 'USDT')
        
        futures_assets = get_assets('futures', db_file=self.test_db_file)
        self.assertEqual(len(futures_assets), 0)
    
    def test_log_asset_history(self):
        """测试记录资产历史"""
        # 测试数据
        asset_data = {
            'asset_type': 'spot',
            'asset': 'USDT',
            'free': 1000.0,
            'locked': 500.0,
            'total': 1500.0
        }
        
        # 记录资产历史
        result = log_asset_history(asset_data, self.test_db_file)
        self.assertTrue(result)
        
        # 验证记录是否保存
        conn = sqlite3.connect(self.test_db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM asset_history WHERE asset = 'USDT'")
        self.assertEqual(cursor.fetchone()[0], 1)
        conn.close()
    
    def test_log_asset_sync(self):
        """测试记录资产同步"""
        # 测试数据
        sync_data = {
            'sync_type': 'full',
            'status': 'success',
            'start_time': datetime.now().isoformat(),
            'end_time': datetime.now().isoformat(),
            'error_message': None,
            'records_synced': 5
        }
        
        # 记录资产同步
        result = log_asset_sync(sync_data, self.test_db_file)
        self.assertTrue(result)
        
        # 验证记录是否保存
        conn = sqlite3.connect(self.test_db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM asset_sync_log WHERE sync_type = 'full'")
        self.assertEqual(cursor.fetchone()[0], 1)
        conn.close()
    
    def test_get_asset_statistics(self):
        """测试获取资产统计信息"""
        # 保存两个资产
        spot_asset = {
            'asset_type': 'spot',
            'asset': 'USDT',
            'free': 1000.0,
            'locked': 500.0,
            'total': 1500.0
        }
        
        futures_asset = {
            'asset_type': 'futures',
            'asset': 'BTC',
            'free': 1.0,
            'locked': 0.5,
            'total': 1.5
        }
        
        save_asset(spot_asset, self.test_db_file)
        save_asset(futures_asset, self.test_db_file)
        
        # 记录资产同步
        sync_data = {
            'sync_type': 'full',
            'status': 'success',
            'start_time': datetime.now().isoformat(),
            'end_time': datetime.now().isoformat(),
            'error_message': None,
            'records_synced': 2
        }
        log_asset_sync(sync_data, self.test_db_file)
        
        # 获取资产统计信息
        stats = get_asset_statistics(self.test_db_file)
        self.assertEqual(stats['total_assets'], 2)
        self.assertEqual(stats['spot_total'], 1500.0)
        self.assertEqual(stats['futures_total'], 1.5)
        self.assertEqual(stats['total_portfolio'], 1501.5)

if __name__ == '__main__':
    unittest.main()
