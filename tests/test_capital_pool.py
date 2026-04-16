import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from capital_pool import (
    CapitalPool, Strategy, GridStrategy, DCAStrategy,
    StrategyType, StrategyState, FundAllocation
)
from risk_manager import (
    RiskManager, RiskConfig, RiskLevel, RiskAlert,
    CapitalPoolWithRisk
)


class TestCapitalPool(unittest.TestCase):
    def setUp(self):
        self.pool = CapitalPool(total_assets=10000.0)

    def test_initialization(self):
        self.assertEqual(self.pool.total_assets, 10000.0)
        self.assertEqual(self.pool.available_funds, 10000.0)
        self.assertEqual(self.pool.locked_funds, 0.0)
        self.assertEqual(self.pool.allocation_ratio, 0.0)

    def test_update_total_assets(self):
        diff = self.pool.update_total_assets(12000.0)
        self.assertEqual(diff, 2000.0)
        self.assertEqual(self.pool.total_assets, 12000.0)
        self.assertEqual(self.pool.available_funds, 12000.0)

    def test_allocate_funds_success(self):
        strategy = GridStrategy(
            strategy_id="test_grid",
            symbol="BTCUSDT",
            initial_amount=5000.0,
            grid_num=10,
            grid_range=0.05
        )
        result = self.pool.allocate_funds(strategy, 5000.0)
        self.assertTrue(result)
        self.assertEqual(self.pool.available_funds, 5000.0)
        self.assertEqual(self.pool.locked_funds, 5000.0)
        self.assertEqual(self.pool.allocation_ratio, 0.5)

    def test_allocate_funds_insufficient(self):
        strategy = GridStrategy(
            strategy_id="test_grid",
            symbol="BTCUSDT",
            initial_amount=5000.0
        )
        result = self.pool.allocate_funds(strategy, 15000.0)
        self.assertFalse(result)
        self.assertEqual(self.pool.available_funds, 10000.0)

    def test_release_funds(self):
        strategy = GridStrategy(
            strategy_id="test_grid",
            symbol="BTCUSDT",
            initial_amount=5000.0
        )
        self.pool.allocate_funds(strategy, 5000.0)
        released = self.pool.release_funds("test_grid")
        self.assertEqual(released, 5000.0)
        self.assertEqual(self.pool.available_funds, 10000.0)
        self.assertEqual(self.pool.locked_funds, 0.0)

    def test_release_funds_not_found(self):
        released = self.pool.release_funds("nonexistent")
        self.assertEqual(released, 0.0)

    def test_get_pool_status(self):
        status = self.pool.get_pool_status()
        self.assertEqual(status['total_assets'], 10000.0)
        self.assertEqual(status['available_funds'], 10000.0)
        self.assertEqual(status['locked_funds'], 0.0)
        self.assertEqual(status['allocation_ratio'], 0.0)


class TestGridStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = GridStrategy(
            strategy_id="grid_test",
            symbol="BTCUSDT",
            initial_amount=5000.0,
            grid_num=10,
            grid_range=0.10,
            reserved_ratio=0.20
        )

    def test_initialization(self):
        self.assertEqual(self.strategy.id, "grid_test")
        self.assertEqual(self.strategy.strategy_type, StrategyType.GRID)
        self.assertEqual(self.strategy.state, StrategyState.ACTIVE)

    def test_set_price_range(self):
        self.strategy.set_price_range(50000.0)
        self.assertEqual(self.strategy.current_price, 50000.0)
        self.assertEqual(self.strategy.lower_price, 47500.0)
        self.assertEqual(self.strategy.upper_price, 52500.0)

    def test_calculate_occupied_amount(self):
        self.strategy.set_price_range(50000.0)
        occupied = self.strategy.calculate_occupied_amount()
        expected = 5000.0 + (5000.0 * 0.20)
        self.assertAlmostEqual(occupied, expected)

    def test_on_price_break_down(self):
        self.strategy.set_price_range(50000.0)
        new_strategy = self.strategy.on_price_break(40000.0)
        self.assertIsNotNone(new_strategy)
        self.assertIsInstance(new_strategy, DCAStrategy)
        self.assertEqual(new_strategy.strategy_type, StrategyType.DCA)

    def test_on_price_break_up(self):
        self.strategy.set_price_range(50000.0)
        new_strategy = self.strategy.on_price_break(60000.0)
        self.assertIsNotNone(new_strategy)
        self.assertIsInstance(new_strategy, DCAStrategy)

    def test_on_price_not_break(self):
        self.strategy.set_price_range(50000.0)
        new_strategy = self.strategy.on_price_break(51000.0)
        self.assertIsNone(new_strategy)

    def test_execute_grid_trade(self):
        self.strategy.set_price_range(50000.0)
        result = self.strategy.execute_grid_trade("sell", 51000.0, 0.1)
        self.assertEqual(result['direction'], "sell")
        self.assertEqual(result['strategy_id'], "grid_test")
        self.assertGreater(self.strategy.profit_count, 0)

    def test_get_status(self):
        self.strategy.set_price_range(50000.0)
        status = self.strategy.get_status()
        self.assertEqual(status['strategy_id'], "grid_test")
        self.assertEqual(status['type'], "grid")
        self.assertEqual(status['grid_num'], 10)


class TestDCAStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = DCAStrategy(
            strategy_id="dca_test",
            symbol="ETHUSDT",
            initial_amount=3000.0,
            trigger_price=2000.0,
            trigger_reason="grid_broken"
        )

    def test_initialization(self):
        self.assertEqual(self.strategy.id, "dca_test")
        self.assertEqual(self.strategy.strategy_type, StrategyType.DCA)
        self.assertEqual(self.strategy.trigger_reason, "grid_broken")

    def test_calculate_occupied_amount(self):
        occupied = self.strategy.calculate_occupied_amount()
        expected = 3000.0 + (3000.0 * 0.10 * 3)
        self.assertAlmostEqual(occupied, expected)

    def test_execute_dca(self):
        result = self.strategy.execute_dca(2000.0)
        self.assertEqual(result['strategy_id'], "dca_test")
        self.assertGreater(result['shares'], 0)
        self.assertEqual(self.strategy.dca_count, 1)

    def test_execute_dca_multiple_times(self):
        self.strategy.execute_dca(2000.0)
        self.strategy.execute_dca(2100.0)
        self.strategy.execute_dca(1900.0)
        self.assertEqual(self.strategy.dca_count, 3)

    def test_get_profit_loss(self):
        self.strategy.execute_dca(2000.0)
        pnl = self.strategy.get_profit_loss(2200.0)
        self.assertIn('pnl', pnl)
        self.assertIn('pnl_ratio', pnl)

    def test_on_price_break_returns_none(self):
        new_strategy = self.strategy.on_price_break(2500.0)
        self.assertIsNone(new_strategy)

    def test_get_status(self):
        self.strategy.execute_dca(2000.0)
        status = self.strategy.get_status()
        self.assertEqual(status['strategy_id'], "dca_test")
        self.assertEqual(status['type'], "dca")
        self.assertEqual(status['trigger_reason'], "grid_broken")


class TestRiskConfig(unittest.TestCase):
    def test_default_config(self):
        config = RiskConfig()
        self.assertEqual(config.max_position_ratio, 0.8)
        self.assertEqual(config.max_single_position_ratio, 0.3)
        self.assertEqual(config.max_loss_per_strategy, 0.15)
        self.assertEqual(config.max_drawdown, 0.20)

    def test_custom_config(self):
        config = RiskConfig(
            max_position_ratio=0.6,
            max_loss_per_strategy=0.10,
            max_drawdown=0.15
        )
        self.assertEqual(config.max_position_ratio, 0.6)
        self.assertEqual(config.max_loss_per_strategy, 0.10)
        self.assertEqual(config.max_drawdown, 0.15)


class TestRiskManager(unittest.TestCase):
    def setUp(self):
        self.risk_manager = RiskManager()
        self.config = RiskConfig(
            max_position_ratio=0.8,
            max_single_position_ratio=0.3,
            max_loss_per_strategy=0.15,
            max_drawdown=0.20
        )
        self.risk_manager = RiskManager(config=self.config)

    def test_initialization(self):
        self.assertEqual(self.risk_manager.status.risk_level, RiskLevel.LOW)

    def test_check_all_risks_normal(self):
        status = self.risk_manager.check_all_risks(
            portfolio_value=10000.0,
            allocations={"grid1": 3000.0},
            current_prices={"BTCUSDT": 50000.0}
        )
        self.assertEqual(status.risk_level, RiskLevel.LOW)

    def test_check_all_risks_position_overflow(self):
        status = self.risk_manager.check_all_risks(
            portfolio_value=10000.0,
            allocations={"grid1": 5000.0},
            current_prices={"BTCUSDT": 50000.0}
        )
        self.assertIn(RiskAlert.POSITION_FULL, status.active_alerts)

    def test_check_drawdown_warning(self):
        self.risk_manager._peak_portfolio_value = 10000.0
        self.risk_manager.status.current_drawdown = 0.15
        self.risk_manager._check_drawdown_risk(8500.0)
        self.assertIn(RiskAlert.DRAWDOWN_WARNING, self.risk_manager.status.active_alerts)

    def test_check_drawdown_stop(self):
        self.risk_manager._peak_portfolio_value = 10000.0
        self.risk_manager.status.current_drawdown = 0.25
        self.risk_manager._check_drawdown_risk(7500.0)
        self.assertIn(RiskAlert.DRAWDOWN_STOP, self.risk_manager.status.active_alerts)

    def test_register_strategy(self):
        record = self.risk_manager.register_strategy(
            strategy_id="test_strategy",
            entry_price=50000.0,
            entry_amount=5000.0,
            stop_loss_ratio=0.05,
            take_profit_ratio=0.15
        )
        self.assertEqual(record.strategy_id, "test_strategy")
        self.assertAlmostEqual(record.stop_loss_price, 47500.0)
        self.assertAlmostEqual(record.take_profit_price, 57500.0)

    def test_update_strategy_price_stop_loss(self):
        self.risk_manager.register_strategy(
            strategy_id="test_strategy",
            entry_price=50000.0,
            entry_amount=5000.0,
            stop_loss_ratio=0.05
        )
        alert = self.risk_manager.update_strategy_price("test_strategy", 47000.0)
        self.assertEqual(alert, RiskAlert.LOSS_STOP)
        self.assertTrue(self.risk_manager._risk_records["test_strategy"].is_stopped)

    def test_update_strategy_price_take_profit(self):
        self.risk_manager.register_strategy(
            strategy_id="test_strategy",
            entry_price=50000.0,
            entry_amount=5000.0,
            take_profit_ratio=0.10
        )
        alert = self.risk_manager.update_strategy_price("test_strategy", 56000.0)
        self.assertEqual(alert, RiskAlert.LOSS_STOP)

    def test_update_strategy_price_warning(self):
        self.risk_manager.register_strategy(
            strategy_id="test_strategy",
            entry_price=50000.0,
            entry_amount=5000.0,
            stop_loss_ratio=0.05
        )
        alert = self.risk_manager.update_strategy_price("test_strategy", 44000.0)
        self.assertEqual(alert, RiskAlert.LOSS_WARNING)

    def test_can_allocate_normal(self):
        result = self.risk_manager.can_allocate(
            amount=3000.0,
            total_value=10000.0,
            current_allocated=0.0
        )
        self.assertTrue(result)

    def test_can_allocate_exceeds_ratio(self):
        result = self.risk_manager.can_allocate(
            amount=9000.0,
            total_value=10000.0,
            current_allocated=0.0
        )
        self.assertFalse(result)

    def test_can_allocate_single_exceeds(self):
        result = self.risk_manager.can_allocate(
            amount=4000.0,
            total_value=10000.0,
            current_allocated=0.0
        )
        self.assertFalse(result)

    def test_can_allocate_insufficient_reserve(self):
        result = self.risk_manager.can_allocate(
            amount=9900.0,
            total_value=10000.0,
            current_allocated=0.0
        )
        self.assertFalse(result)

    def test_get_safe_allocation(self):
        safe_amount = self.risk_manager.get_safe_allocation(
            requested_amount=5000.0,
            total_value=10000.0,
            current_allocated=0.0
        )
        self.assertEqual(safe_amount, 3000.0)

    def test_get_safe_allocation_critical_level(self):
        self.risk_manager.status.risk_level = RiskLevel.CRITICAL
        safe_amount = self.risk_manager.get_safe_allocation(
            requested_amount=5000.0,
            total_value=10000.0,
            current_allocated=0.0
        )
        self.assertEqual(safe_amount, 0.0)

    def test_should_stop_strategy(self):
        self.risk_manager.register_strategy(
            strategy_id="test_strategy",
            entry_price=50000.0,
            entry_amount=5000.0,
            stop_loss_ratio=0.05
        )
        self.risk_manager.update_strategy_price("test_strategy", 47000.0)
        self.assertTrue(self.risk_manager.should_stop_strategy("test_strategy"))

    def test_get_risk_report(self):
        self.risk_manager.register_strategy(
            strategy_id="test_strategy",
            entry_price=50000.0,
            entry_amount=5000.0
        )
        report = self.risk_manager.get_risk_report()
        self.assertIn('risk_level', report)
        self.assertIn('position_ratio', report)
        self.assertIn('drawdown', report)
        self.assertEqual(report['total_strategies'], 1)


class TestCapitalPoolWithRisk(unittest.TestCase):
    def setUp(self):
        self.config = RiskConfig(
            max_position_ratio=0.8,
            max_single_position_ratio=0.3,
            max_loss_per_strategy=0.15
        )
        self.pool = CapitalPoolWithRisk(total_assets=10000.0, risk_config=self.config)

    def test_initialization(self):
        self.assertEqual(self.pool.total_assets, 10000.0)
        self.assertEqual(self.pool.risk_manager.status.risk_level, RiskLevel.LOW)

    def test_allocate_funds_with_risk_check(self):
        strategy = GridStrategy(
            strategy_id="grid_1",
            symbol="BTCUSDT",
            initial_amount=2000.0
        )
        success, msg = self.pool.allocate_funds(strategy, 2000.0)
        self.assertTrue(success)
        self.assertEqual(self.pool.available_funds, 8000.0)

    def test_allocate_funds_exceeds_risk_limit(self):
        strategy = GridStrategy(
            strategy_id="grid_1",
            symbol="BTCUSDT",
            initial_amount=9000.0
        )
        success, msg = self.pool.allocate_funds(strategy, 9000.0)
        self.assertFalse(success)
        self.assertIn("Risk limit", msg)

    def test_release_funds_with_reason(self):
        strategy = GridStrategy(
            strategy_id="grid_1",
            symbol="BTCUSDT",
            initial_amount=2000.0
        )
        self.pool.allocate_funds(strategy, 2000.0)
        self.pool.risk_manager.register_strategy(
            strategy_id="grid_1",
            entry_price=50000.0,
            entry_amount=2000.0,
            stop_loss_ratio=0.05
        )
        self.pool.risk_manager.update_strategy_price("grid_1", 47000.0)
        amount, reason = self.pool.release_funds("grid_1")
        self.assertGreater(amount, 0)
        self.assertIn("Risk triggered", reason)

    def test_convert_strategy_grid_to_dca(self):
        grid = GridStrategy(
            strategy_id="grid_1",
            symbol="BTCUSDT",
            initial_amount=2000.0
        )
        grid.set_price_range(50000.0)
        self.pool.allocate_funds(grid, 2000.0)

        new_strategy = grid.on_price_break(40000.0)
        self.assertIsNotNone(new_strategy)

        success, msg = self.pool.convert_strategy("grid_1", new_strategy, keep_ratio=0.7)
        self.assertTrue(success)

    def test_daily_risk_check(self):
        strategy = GridStrategy(
            strategy_id="grid_1",
            symbol="BTCUSDT",
            initial_amount=2000.0
        )
        self.pool.allocate_funds(strategy, 2000.0)

        result = self.pool.daily_risk_check({"BTCUSDT": 50000.0})
        self.assertIn('risk_status', result)
        self.assertIn('report', result)

    def test_get_pool_status_with_risk(self):
        status = self.pool.get_pool_status()
        self.assertIn('risk_level', status)
        self.assertEqual(status['risk_level'], 'low')


class TestStrategyConversion(unittest.TestCase):
    def test_grid_broken_converts_to_dca(self):
        pool = CapitalPool(total_assets=10000.0)

        grid = GridStrategy(
            strategy_id="grid_1",
            symbol="BTCUSDT",
            initial_amount=5000.0,
            grid_num=10,
            grid_range=0.05
        )
        grid.set_price_range(50000.0)

        pool.allocate_funds(grid, 5000.0)

        new_strategy = grid.on_price_break(45000.0)
        self.assertIsInstance(new_strategy, DCAStrategy)
        self.assertEqual(new_strategy.strategy_type, StrategyType.DCA)
        self.assertEqual(new_strategy.trigger_reason, "grid_broken")

    def test_multiple_grids_convert_independently(self):
        pool = CapitalPool(total_assets=20000.0)

        grid1 = GridStrategy(strategy_id="grid_1", symbol="BTCUSDT", initial_amount=5000.0)
        grid2 = GridStrategy(strategy_id="grid_2", symbol="ETHUSDT", initial_amount=5000.0)

        grid1.set_price_range(50000.0)
        grid2.set_price_range(3000.0)

        pool.allocate_funds(grid1, 5000.0)
        pool.allocate_funds(grid2, 5000.0)

        grid1.on_price_break(45000.0)
        grid2.on_price_break(3500.0)

        self.assertEqual(grid1.state, StrategyState.ACTIVE)
        self.assertEqual(grid2.state, StrategyState.ACTIVE)


if __name__ == '__main__':
    unittest.main(verbosity=2)
