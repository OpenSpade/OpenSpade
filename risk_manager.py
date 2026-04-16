from typing import TYPE_CHECKING
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from datetime import datetime


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskAlert(Enum):
    POSITION_FULL = "position_full"
    LOSS_WARNING = "loss_warning"
    LOSS_STOP = "loss_stop"
    DRAWDOWN_WARNING = "drawdown_warning"
    DRAWDOWN_STOP = "drawdown_stop"
    VOLATILITY_HIGH = "volatility_high"
    FUNDS_LOW = "funds_low"
    LEVERAGE_HIGH = "leverage_high"


@dataclass
class RiskConfig:
    max_position_ratio: float = 0.8
    max_single_position_ratio: float = 0.3
    max_loss_per_strategy: float = 0.15
    max_total_loss: float = 0.25
    loss_warning_threshold: float = 0.10
    max_drawdown: float = 0.20
    drawdown_warning: float = 0.15
    max_volatility: float = 0.30
    volatility_warning: float = 0.20
    max_leverage: int = 10
    leverage_warning: int = 5
    min_reserved_funds: float = 100.0


@dataclass
class RiskStatus:
    risk_level: RiskLevel = RiskLevel.LOW
    current_position_ratio: float = 0.0
    current_drawdown: float = 0.0
    current_volatility: float = 0.0
    active_alerts: List[RiskAlert] = field(default_factory=list)
    last_check_time: datetime = field(default_factory=datetime.now)


@dataclass
class StrategyRiskRecord:
    strategy_id: str
    entry_price: float
    entry_time: datetime
    initial_amount: float
    current_amount: float
    peak_amount: float
    stop_loss_price: float = 0.0
    take_profit_price: float = 0.0
    is_stopped: bool = False
    stop_reason: Optional[str] = None


class RiskManager:
    def __init__(self, config: Optional[RiskConfig] = None):
        self.config = config or RiskConfig()
        self.status = RiskStatus()
        self._risk_records: Dict[str, StrategyRiskRecord] = {}
        self._peak_portfolio_value: float = 0.0
        self._alert_callbacks: List[Callable[[RiskAlert, Dict], None]] = []
        self._risk_history: List[RiskStatus] = []

    def check_all_risks(
        self,
        portfolio_value: float,
        allocations: Dict[str, float],
        current_prices: Dict[str, float]
    ) -> RiskStatus:
        self.status = RiskStatus()
        self.status.last_check_time = datetime.now()

        if portfolio_value > self._peak_portfolio_value:
            self._peak_portfolio_value = portfolio_value

        self.status.current_drawdown = self._calculate_drawdown(portfolio_value)
        self.status.current_position_ratio = sum(allocations.values()) / portfolio_value if portfolio_value > 0 else 0

        self._check_position_risk(allocations, portfolio_value)
        self._check_drawdown_risk(portfolio_value)

        self._update_risk_level()
        self._risk_history.append(self.status)

        return self.status

    def _calculate_drawdown(self, current_value: float) -> float:
        if self._peak_portfolio_value == 0:
            return 0.0
        return (self._peak_portfolio_value - current_value) / self._peak_portfolio_value

    def _check_position_risk(self, allocations: Dict[str, float], total_value: float) -> None:
        for strategy_id, amount in allocations.items():
            ratio = amount / total_value if total_value > 0 else 0

            if ratio > self.config.max_single_position_ratio:
                if RiskAlert.POSITION_FULL not in self.status.active_alerts:
                    self.status.active_alerts.append(RiskAlert.POSITION_FULL)

            if strategy_id in self._risk_records:
                self._risk_records[strategy_id].current_amount = amount

    def _check_drawdown_risk(self, current_value: float) -> None:
        if self.status.current_drawdown >= self.config.max_drawdown:
            self.status.active_alerts.append(RiskAlert.DRAWDOWN_STOP)
        elif self.status.current_drawdown >= self.config.drawdown_warning:
            self.status.active_alerts.append(RiskAlert.DRAWDOWN_WARNING)

    def _update_risk_level(self) -> None:
        if RiskAlert.DRAWDOWN_STOP in self.status.active_alerts:
            self.status.risk_level = RiskLevel.CRITICAL
        elif RiskAlert.POSITION_FULL in self.status.active_alerts:
            self.status.risk_level = RiskLevel.HIGH
        elif RiskAlert.DRAWDOWN_WARNING in self.status.active_alerts:
            self.status.risk_level = RiskLevel.MEDIUM
        else:
            self.status.risk_level = RiskLevel.LOW

    def register_strategy(
        self,
        strategy_id: str,
        entry_price: float,
        entry_amount: float,
        stop_loss_ratio: float = 0.05,
        take_profit_ratio: float = 0.15
    ) -> StrategyRiskRecord:
        record = StrategyRiskRecord(
            strategy_id=strategy_id,
            entry_price=entry_price,
            entry_time=datetime.now(),
            initial_amount=entry_amount,
            current_amount=entry_amount,
            peak_amount=entry_amount,
            stop_loss_price=entry_price * (1 - stop_loss_ratio),
            take_profit_price=entry_price * (1 + take_profit_ratio)
        )

        self._risk_records[strategy_id] = record
        return record

    def update_strategy_price(self, strategy_id: str, current_price: float) -> Optional[RiskAlert]:
        if strategy_id not in self._risk_records:
            return None

        record = self._risk_records[strategy_id]

        price_ratio = current_price / record.entry_price
        record.current_amount = record.initial_amount * price_ratio

        if price_ratio > record.peak_amount / record.initial_amount:
            record.peak_amount = record.current_amount

        loss_ratio = (record.entry_price - current_price) / record.entry_price

        if current_price >= record.take_profit_price and not record.is_stopped:
            record.is_stopped = True
            record.stop_reason = "take_profit"
            return RiskAlert.LOSS_STOP

        if current_price <= record.stop_loss_price and not record.is_stopped:
            record.is_stopped = True
            record.stop_reason = "stop_loss"
            return RiskAlert.LOSS_STOP

        if loss_ratio >= self.config.max_loss_per_strategy:
            return RiskAlert.LOSS_WARNING

        return None

    def check_strategy_loss(self, strategy_id: str) -> float:
        if strategy_id not in self._risk_records:
            return 0.0

        record = self._risk_records[strategy_id]
        if record.initial_amount == 0:
            return 0.0

        return (record.initial_amount - record.current_amount) / record.initial_amount

    def should_stop_strategy(self, strategy_id: str) -> bool:
        if strategy_id not in self._risk_records:
            return False

        record = self._risk_records[strategy_id]

        if record.is_stopped:
            return True

        loss_ratio = self.check_strategy_loss(strategy_id)
        if loss_ratio >= self.config.max_loss_per_strategy:
            return True

        return False

    def can_allocate(self, amount: float, total_value: float, current_allocated: float) -> bool:
        new_total_ratio = (current_allocated + amount) / total_value
        if new_total_ratio > self.config.max_position_ratio:
            return False

        single_ratio = amount / total_value
        if single_ratio > self.config.max_single_position_ratio:
            return False

        available = total_value - current_allocated - amount
        if available < self.config.min_reserved_funds:
            return False

        return True

    def get_safe_allocation(
        self,
        requested_amount: float,
        total_value: float,
        current_allocated: float
    ) -> float:
        if self.status.risk_level == RiskLevel.CRITICAL:
            return 0.0

        single_ratio = requested_amount / total_value
        if single_ratio > self.config.max_single_position_ratio:
            return total_value * self.config.max_single_position_ratio

        max_additional = total_value * self.config.max_position_ratio - current_allocated
        if max_additional <= 0:
            return 0.0

        return min(requested_amount, max_additional)

    def check_leverage_risk(self, position_value: float, margin: float) -> Optional[RiskAlert]:
        if margin == 0:
            return RiskAlert.LEVERAGE_HIGH

        leverage = position_value / margin

        if leverage > self.config.max_leverage:
            return RiskAlert.LEVERAGE_HIGH
        elif leverage > self.config.leverage_warning:
            return RiskAlert.LEVERAGE_HIGH

        return None

    def get_safe_leverage(self, current_leverage: int) -> int:
        if self.status.risk_level == RiskLevel.CRITICAL:
            return 1
        elif self.status.risk_level == RiskLevel.HIGH:
            return min(2, current_leverage)
        elif self.status.risk_level == RiskLevel.MEDIUM:
            return min(5, current_leverage)
        else:
            return min(self.config.max_leverage, current_leverage)

    def add_alert_callback(self, callback: Callable[[RiskAlert, Dict], None]) -> None:
        self._alert_callbacks.append(callback)

    def trigger_alert(self, alert: RiskAlert, data: Dict) -> None:
        for callback in self._alert_callbacks:
            try:
                callback(alert, data)
            except Exception as e:
                print(f"Alert callback failed: {e}")

    def get_risk_report(self) -> Dict:
        return {
            "risk_level": self.status.risk_level.value,
            "position_ratio": f"{self.status.current_position_ratio:.2%}",
            "drawdown": f"{self.status.current_drawdown:.2%}",
            "volatility": f"{self.status.current_volatility:.2%}",
            "active_alerts": [alert.value for alert in self.status.active_alerts],
            "total_strategies": len(self._risk_records),
            "stopped_strategies": sum(1 for r in self._risk_records.values() if r.is_stopped),
            "peak_portfolio_value": self._peak_portfolio_value,
            "last_check": self.status.last_check_time.isoformat()
        }

    def get_all_records(self) -> List[StrategyRiskRecord]:
        return list(self._risk_records.values())


class CapitalPoolWithRisk:

    def __init__(self, total_assets: float = 0.0, risk_config: RiskConfig = None):
        from capital_pool import Strategy, FundAllocation

        self._total_assets = total_assets
        self._available_funds = total_assets
        self._locked_funds = 0.0
        self._allocations: Dict[str, FundAllocation] = {}
        self._strategies: Dict[str, 'Strategy'] = {}
        self.risk_manager = RiskManager(risk_config)

    @property
    def total_assets(self) -> float:
        return self._total_assets

    @property
    def available_funds(self) -> float:
        return self._available_funds

    @property
    def locked_funds(self) -> float:
        return self._locked_funds

    @property
    def allocation_ratio(self) -> float:
        if self._total_assets == 0:
            return 0.0
        return self._locked_funds / self._total_assets

    def update_total_assets(self, new_total: float) -> float:
        diff = new_total - self._total_assets
        self._total_assets = new_total
        self._available_funds += diff
        return diff

    def allocate_funds(self, strategy: 'Strategy', amount: float) -> tuple[bool, str]:
        from capital_pool import Strategy, StrategyType, StrategyState, FundAllocation

        if not self.risk_manager.can_allocate(
            amount,
            self._total_assets,
            self._locked_funds
        ):
            safe_amount = self.risk_manager.get_safe_allocation(
                amount,
                self._total_assets,
                self._locked_funds
            )
            if safe_amount > 0:
                return False, f"Risk limit: recommended allocation {safe_amount:.2f} USDT"
            return False, "Risk limit: current risk level does not allow new allocation"

        if amount > self._available_funds:
            return False, "Insufficient funds"

        allocation = FundAllocation(
            strategy_id=strategy.id,
            strategy_type=strategy.strategy_type,
            allocated_amount=amount,
            occupied_amount=amount,
            reserved_amount=0.0,
            state=StrategyState.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        self._allocations[strategy.id] = allocation
        self._strategies[strategy.id] = strategy
        self._available_funds -= amount
        self._locked_funds += amount

        self.risk_manager.register_strategy(
            strategy_id=strategy.id,
            entry_price=strategy.initial_amount,
            entry_amount=amount
        )

        strategy.on_allocated(amount)
        return True, "Allocation successful"

    def release_funds(self, strategy_id: str) -> tuple[float, str]:
        if strategy_id not in self._allocations:
            return 0.0, "Strategy not found"

        if self.risk_manager.should_stop_strategy(strategy_id):
            reason = "Risk triggered: loss limit exceeded"
        else:
            reason = "Manual release"

        allocation = self._allocations[strategy_id]
        released = allocation.occupied_amount + allocation.reserved_amount

        self._available_funds += released
        self._locked_funds -= allocation.occupied_amount

        del self._allocations[strategy_id]

        if strategy_id in self._strategies:
            self._strategies[strategy_id].on_released()

        return released, reason

    def convert_strategy(
        self,
        old_strategy_id: str,
        new_strategy: 'Strategy',
        keep_ratio: float = 0.5
    ) -> tuple[bool, str]:
        from capital_pool import StrategyType, StrategyState

        if old_strategy_id not in self._allocations:
            return False, "Strategy not found"

        old_allocation = self._allocations[old_strategy_id]
        keep_amount = old_allocation.occupied_amount * keep_ratio
        release_amount = old_allocation.occupied_amount - keep_amount

        old_allocation.state = StrategyState.CONVERTED
        old_allocation.occupied_amount = keep_amount

        self._available_funds += release_amount
        self._locked_funds -= release_amount

        if new_strategy.strategy_type == StrategyType.DCA:
            success, msg = self.allocate_funds(new_strategy, keep_amount)
            if success:
                return True, f"Strategy converted, keep {keep_ratio:.0%} funds"
            return False, f"Strategy converted but failed to allocate: {msg}"

        return True, "Strategy converted"

    def daily_risk_check(self, current_prices: Dict[str, float]) -> Dict:
        allocations = {
            alloc.strategy_id: alloc.occupied_amount
            for alloc in self._allocations.values()
        }

        status = self.risk_manager.check_all_risks(
            self._total_assets,
            allocations,
            current_prices
        )

        strategies_to_stop = []
        for strategy_id in self._allocations:
            if self.risk_manager.should_stop_strategy(strategy_id):
                strategies_to_stop.append(strategy_id)

        return {
            "risk_status": status,
            "strategies_to_stop": strategies_to_stop,
            "report": self.risk_manager.get_risk_report()
        }

    def get_pool_status(self) -> Dict:
        from capital_pool import StrategyState

        return {
            "total_assets": self._total_assets,
            "available_funds": self._available_funds,
            "locked_funds": self._locked_funds,
            "allocation_ratio": self.allocation_ratio,
            "active_strategies": len([a for a in self._allocations.values() if a.state == StrategyState.ACTIVE]),
            "total_strategies": len(self._allocations),
            "risk_level": self.risk_manager.status.risk_level.value
        }