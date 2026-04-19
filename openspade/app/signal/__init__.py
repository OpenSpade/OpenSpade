"""
OpenSpade Signal Module - 事件引擎与信号处理

## 快速开始

### 1. 创建策略
```python
from openspade.app.signal import engine, StrategyRegistry, SignalType

@StrategyRegistry.register("my_strategy")
class MyStrategy:
    def __init__(self, name, engine):
        self.name = name
        engine.bus.subscribe(SignalType.PRICE_ALERT, self.on_price_alert)
    
    def on_price_alert(self, signal):
        print(f"收到信号: {signal.symbol} @ {signal.data['price']}")

# 激活策略
engine.create_strategy("my_strategy")
```

### 2. 启动信号源
```python
from openspade.app.signal import BinanceFuturesSource

source = BinanceFuturesSource(
    symbols=["BTCUSDT", "ETHUSDT"],
    interval="1m",
    check_interval=10
)
engine.register_source("binance", source)
engine.start_sources()
```

### 3. 手动发送信号
```python
engine.emit_signal(SignalType.PRICE_ALERT, "BTCUSDT", {"price": 50000}, "manual")
```

## 信号类型
- SignalType.PRICE_ALERT - 价格突破信号
- SignalType.TREND_CHANGE - 趋势变化信号
- SignalType.VOLUME_SPIKE - 成交量爆发信号
- SignalType.CUSTOM - 自定义信号

## API 概览

EventEngine (单例):
- engine.create_strategy(name) -> Strategy
- engine.register_source(name, source)
- engine.start_sources() / stop_sources()
- engine.emit_signal(type, symbol, data, source)
- engine.bus.subscribe(type, handler)
- engine.bus.subscribe_global(handler)

StrategyRegistry:
- StrategyRegistry.register(name) - 装饰器注册策略类
- StrategyRegistry.list_strategies() - 列出已注册策略
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from abc import ABC, abstractmethod
import threading
import time
from binance_connector import BinanceConnector


class SignalType(Enum):
    PRICE_ALERT = "price_alert"
    TREND_CHANGE = "trend_change"
    VOLUME_SPIKE = "volume_spike"
    CUSTOM = "custom"


@dataclass
class Signal:
    signal_type: SignalType
    symbol: str
    timestamp: datetime
    data: Dict[str, Any]
    source: str = "unknown"

    def __post_init__(self):
        if isinstance(self.signal_type, str):
            self.signal_type = SignalType(self.signal_type)


class SignalSource(ABC):
    @abstractmethod
    def start(self, engine: "EventEngine"):
        pass

    @abstractmethod
    def stop(self):
        pass


class BinanceFuturesSource(SignalSource):
    def __init__(self, symbols: List[str] = None, interval: str = "1m", check_interval: int = 5):
        self.symbols = symbols or ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        self.interval = interval
        self.check_interval = check_interval
        self.connector = BinanceConnector()
        self._running = False
        self._thread = None
        self._engine = None

    def start(self, engine: "EventEngine"):
        self._engine = engine
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()

    def _run(self):
        while self._running:
            for symbol in self.symbols:
                try:
                    klines = self.connector.get_klines(symbol, self.interval, 5)
                    if klines:
                        self._analyze_klines(symbol, klines)
                except Exception as e:
                    print(f"Error analyzing {symbol}: {e}")
            time.sleep(self.check_interval)

    def _analyze_klines(self, symbol: str, klines: List[Dict]):
        if len(klines) < 2:
            return

        current_close = klines[-1]['close']
        previous_close = klines[-2]['close']
        price_change = (current_close - previous_close) / previous_close * 100

        if abs(price_change) > 1.0:
            self._engine.emit_signal(
                SignalType.PRICE_ALERT, symbol,
                {"price": current_close, "previous_price": previous_close,
                 "price_change": price_change, "volume": klines[-1]['volume']},
                "binance_futures"
            )

        if len(klines) > 3:
            current_volume = klines[-1]['volume']
            avg_volume = sum(k['volume'] for k in klines[-4:-1]) / 3
            if current_volume > avg_volume * 2:
                self._engine.emit_signal(
                    SignalType.VOLUME_SPIKE, symbol,
                    {"price": current_close, "volume": current_volume,
                     "avg_volume": avg_volume, "volume_ratio": current_volume / avg_volume},
                    "binance_futures"
                )


class EventBus:
    def __init__(self):
        self._subscribers: Dict[SignalType, List[Callable]] = {}
        self._global_subscribers: List[Callable] = []
        self._lock = threading.Lock()

    def subscribe(self, signal_type: SignalType, handler: Callable[[Signal], None]):
        with self._lock:
            if signal_type not in self._subscribers:
                self._subscribers[signal_type] = []
            self._subscribers[signal_type].append(handler)

    def subscribe_global(self, handler: Callable[[Signal], None]):
        with self._lock:
            self._global_subscribers.append(handler)

    def unsubscribe(self, signal_type: SignalType, handler: Callable[[Signal], None]):
        with self._lock:
            if signal_type in self._subscribers:
                try:
                    self._subscribers[signal_type].remove(handler)
                except ValueError:
                    pass

    def emit(self, signal: Signal):
        with self._lock:
            handlers = list(self._subscribers.get(signal.signal_type, []))
            global_handlers = list(self._global_subscribers)

        for handler in handlers:
            try:
                handler(signal)
            except Exception as e:
                print(f"Handler error: {e}")

        for handler in global_handlers:
            try:
                handler(signal)
            except Exception as e:
                print(f"Global handler error: {e}")


class Strategy:
    def __init__(self, name: str, engine: "EventEngine"):
        self.name = name
        self._engine = engine
        self._enabled = True

    def on(self, signal_type: SignalType):
        def decorator(func: Callable[[Signal], None]):
            self._engine.bus.subscribe(signal_type, func)
            return func
        return decorator

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False


class StrategyRegistry:
    _strategies: Dict[str, type] = {}

    @classmethod
    def register(cls, name: str = None):
        def decorator(strategy_cls: type):
            cls._strategies[name or strategy_cls.__name__] = strategy_cls
            return strategy_cls
        return decorator

    @classmethod
    def create(cls, name: str, engine: "EventEngine") -> Optional[Strategy]:
        if name not in cls._strategies:
            return None
        return cls._strategies[name](name, engine)

    @classmethod
    def list_strategies(cls):
        return list(cls._strategies.keys())


class EventEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._bus = EventBus()
        self._strategies: Dict[str, Strategy] = {}
        self._sources: Dict[str, SignalSource] = {}
        self._initialized = True

    @property
    def bus(self) -> EventBus:
        return self._bus

    @property
    def strategies(self) -> Dict[str, Strategy]:
        return self._strategies

    def register_strategy(self, name: str, strategy: Strategy):
        self._strategies[name] = strategy

    def get_strategy(self, name: str) -> Optional[Strategy]:
        return self._strategies.get(name)

    def create_strategy(self, name: str) -> Optional[Strategy]:
        strategy = StrategyRegistry.create(name, self)
        if strategy:
            self._strategies[name] = strategy
        return strategy

    def register_source(self, name: str, source: SignalSource):
        self._sources[name] = source

    def start_sources(self):
        for source in self._sources.values():
            source.start(self)

    def stop_sources(self):
        for source in self._sources.values():
            source.stop()

    def emit_signal(self, signal_type: SignalType, symbol: str, data: Dict[str, Any], source: str = "unknown"):
        signal = Signal(
            signal_type=signal_type,
            symbol=symbol,
            timestamp=datetime.now(),
            data=data,
            source=source
        )
        self._bus.emit(signal)
        return signal


engine = EventEngine()