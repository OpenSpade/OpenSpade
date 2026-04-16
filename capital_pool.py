from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


class StrategyType(Enum):
    GRID = "grid"
    DCA = "dca"
    GRID_BROKEN = "grid_broken"


class StrategyState(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    CONVERTED = "converted"


@dataclass
class FundAllocation:
    strategy_id: str
    strategy_type: StrategyType
    allocated_amount: float
    occupied_amount: float
    reserved_amount: float
    state: StrategyState
    created_at: datetime
    updated_at: datetime


class CapitalPool:
    def __init__(self, total_assets: float = 0.0):
        self._total_assets = total_assets
        self._available_funds = total_assets
        self._locked_funds = 0.0
        self._allocations: Dict[str, FundAllocation] = {}
        self._strategies: Dict[str, 'Strategy'] = {}

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

    def allocate_funds(self, strategy: 'Strategy', amount: float) -> bool:
        if amount > self._available_funds:
            return False

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

        strategy.on_allocated(amount)
        return True

    def release_funds(self, strategy_id: str) -> float:
        if strategy_id not in self._allocations:
            return 0.0

        allocation = self._allocations[strategy_id]
        released = allocation.occupied_amount + allocation.reserved_amount

        self._available_funds += released
        self._locked_funds -= allocation.occupied_amount

        del self._allocations[strategy_id]

        if strategy_id in self._strategies:
            self._strategies[strategy_id].on_released()

        return released

    def convert_strategy(
        self,
        old_strategy_id: str,
        new_strategy: 'Strategy',
        keep_ratio: float = 0.5
    ) -> bool:
        if old_strategy_id not in self._allocations:
            return False

        old_allocation = self._allocations[old_strategy_id]
        keep_amount = old_allocation.occupied_amount * keep_ratio
        release_amount = old_allocation.occupied_amount - keep_amount

        old_allocation.state = StrategyState.CONVERTED
        old_allocation.occupied_amount = keep_amount

        self._available_funds += release_amount
        self._locked_funds -= release_amount

        if new_strategy.strategy_type == StrategyType.DCA:
            return self.allocate_funds(new_strategy, keep_amount)

        return True

    def get_strategy_allocation(self, strategy_id: str) -> Optional[FundAllocation]:
        return self._allocations.get(strategy_id)

    def get_all_allocations(self) -> List[FundAllocation]:
        return list(self._allocations.values())

    def get_pool_status(self) -> Dict:
        return {
            "total_assets": self._total_assets,
            "available_funds": self._available_funds,
            "locked_funds": self._locked_funds,
            "allocation_ratio": self.allocation_ratio,
            "active_strategies": len([a for a in self._allocations.values() if a.state == StrategyState.ACTIVE]),
            "total_strategies": len(self._allocations)
        }


class Strategy(ABC):
    def __init__(
        self,
        strategy_id: str,
        strategy_type: StrategyType,
        symbol: str,
        initial_amount: float
    ):
        self.id = strategy_id
        self.strategy_type = strategy_type
        self.symbol = symbol
        self.initial_amount = initial_amount
        self.current_amount = initial_amount
        self.state = StrategyState.ACTIVE

    @abstractmethod
    def calculate_occupied_amount(self) -> float:
        pass

    @abstractmethod
    def on_price_break(self, new_price: float) -> Optional['Strategy']:
        pass

    @abstractmethod
    def get_status(self) -> Dict:
        pass

    def on_allocated(self, amount: float) -> None:
        pass

    def on_released(self) -> None:
        self.state = StrategyState.STOPPED


class GridStrategy(Strategy):
    def __init__(
        self,
        strategy_id: str,
        symbol: str,
        initial_amount: float,
        grid_num: int = 10,
        grid_range: float = 0.10,
        reserved_ratio: float = 0.20
    ):
        super().__init__(strategy_id, StrategyType.GRID, symbol, initial_amount)

        self.grid_num = grid_num
        self.grid_range = grid_range
        self.reserved_ratio = reserved_ratio
        self.upper_price: float = 0.0
        self.lower_price: float = 0.0
        self.current_price: float = 0.0
        self.grid_count: int = 0
        self.profit_count: int = 0

    def set_price_range(self, current_price: float) -> None:
        self.current_price = current_price
        self.lower_price = current_price * (1 - self.grid_range / 2)
        self.upper_price = current_price * (1 + self.grid_range / 2)

    def calculate_occupied_amount(self) -> float:
        position_per_grid = self.current_amount / self.grid_num
        grid_occupied = position_per_grid * self.grid_num
        reserved = self.current_amount * self.reserved_ratio
        return grid_occupied + reserved

    def on_price_break(self, new_price: float) -> Optional['Strategy']:
        if new_price < self.lower_price or new_price > self.upper_price:
            dca_strategy = DCAStrategy(
                strategy_id=f"{self.id}_dca",
                symbol=self.symbol,
                initial_amount=self.current_amount,
                trigger_price=new_price,
                trigger_reason="grid_broken"
            )
            return dca_strategy
        return None

    def update_grid_status(self, current_price: float) -> None:
        self.current_price = current_price
        if current_price >= self.upper_price or current_price <= self.lower_price:
            self.grid_count += 1

    def execute_grid_trade(self, direction: str, price: float, amount: float) -> Dict:
        trade_result = {
            "strategy_id": self.id,
            "direction": direction,
            "price": price,
            "amount": amount,
            "timestamp": datetime.now()
        }

        if direction == "sell":
            self.profit_count += 1
            self.current_amount += amount * price * 0.001

        return trade_result

    def get_status(self) -> Dict:
        return {
            "strategy_id": self.id,
            "type": "grid",
            "symbol": self.symbol,
            "state": self.state.value,
            "initial_amount": self.initial_amount,
            "current_amount": self.current_amount,
            "occupied_amount": self.calculate_occupied_amount(),
            "grid_num": self.grid_num,
            "price_range": f"{self.lower_price:.4f} - {self.upper_price:.4f}",
            "current_price": self.current_price,
            "grid_count": self.grid_count,
            "profit_count": self.profit_count
        }


class DCAStrategy(Strategy):
    def __init__(
        self,
        strategy_id: str,
        symbol: str,
        initial_amount: float,
        trigger_price: float,
        trigger_reason: str = "manual",
        dca_interval: int = 86400,
        dca_amount_ratio: float = 0.10
    ):
        super().__init__(strategy_id, StrategyType.DCA, symbol, initial_amount)

        self.trigger_price = trigger_price
        self.trigger_reason = trigger_reason
        self.dca_interval = dca_interval
        self.dca_amount_ratio = dca_amount_ratio
        self.total_invested = 0.0
        self.average_cost = 0.0
        self.total_shares = 0.0
        self.last_dca_time: Optional[datetime] = None
        self.dca_count = 0

    def calculate_occupied_amount(self) -> float:
        future_dca_reserve = self.current_amount * self.dca_amount_ratio * 3
        return self.current_amount + future_dca_reserve

    def on_price_break(self, new_price: float) -> Optional['Strategy']:
        return None

    def execute_dca(self, current_price: float) -> Dict:
        dca_amount = self.current_amount * self.dca_amount_ratio

        if self.total_shares == 0:
            self.total_shares = dca_amount / current_price
            self.average_cost = current_price
        else:
            new_shares = dca_amount / current_price
            self.total_shares += new_shares
            self.total_invested += dca_amount
            self.average_cost = self.total_invested / self.total_shares

        self.last_dca_time = datetime.now()
        self.dca_count += 1

        return {
            "strategy_id": self.id,
            "dca_amount": dca_amount,
            "price": current_price,
            "shares": self.total_shares,
            "average_cost": self.average_cost,
            "timestamp": datetime.now()
        }

    def get_profit_loss(self, current_price: float) -> Dict:
        if self.total_shares == 0:
            return {"pnl": 0.0, "pnl_ratio": 0.0}

        current_value = self.total_shares * current_price
        pnl = current_value - self.total_invested
        pnl_ratio = pnl / self.total_invested if self.total_invested > 0 else 0.0

        return {
            "pnl": pnl,
            "pnl_ratio": pnl_ratio,
            "current_value": current_value,
            "total_invested": self.total_invested
        }

    def get_status(self) -> Dict:
        return {
            "strategy_id": self.id,
            "type": "dca",
            "symbol": self.symbol,
            "state": self.state.value,
            "initial_amount": self.initial_amount,
            "current_amount": self.current_amount,
            "occupied_amount": self.calculate_occupied_amount(),
            "trigger_price": self.trigger_price,
            "trigger_reason": self.trigger_reason,
            "total_invested": self.total_invested,
            "total_shares": self.total_shares,
            "average_cost": self.average_cost,
            "dca_count": self.dca_count,
            "last_dca_time": self.last_dca_time.isoformat() if self.last_dca_time else None
        }
