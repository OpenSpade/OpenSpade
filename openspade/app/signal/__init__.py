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
        engine.bus.subscribe(SignalType.TIMER_TASK, self.on_timer_task)
    
    def on_price_alert(self, signal):
        print(f"收到信号: {signal.symbol} @ {signal.data['price']}")
    
    def on_timer_task(self, signal):
        print(f"定时任务执行: {signal.data['task_name']} - {signal.data}")

# 激活策略
engine.create_strategy("my_strategy")
```

### 2. 启动信号源
```python
from openspade.app.signal import BinanceFuturesSource, TimerSource, TimerTask

# 启动 Binance 期货信号源
binance_source = BinanceFuturesSource(
    symbols=["BTCUSDT", "ETHUSDT"],
    interval="1m",
    check_interval=10
)
engine.register_source("binance", binance_source)

# 启动定时任务信号源
timer_source = TimerSource(check_interval=1)

# 添加定时任务
def my_task_callback():
    return {"status": "completed", "result": "Task executed successfully"}

# 每5秒执行一次的任务
task1 = TimerTask(
    name="my_task",
    interval=5,
    callback=my_task_callback,
    symbol="ALL",
    data={"param1": "value1", "param2": "value2"}
)
timer_source.add_task(task1)

# 每10秒执行一次的任务
task2 = TimerTask(
    name="another_task",
    interval=10,
    symbol="BTCUSDT"
)
timer_source.add_task(task2)

engine.register_source("timer", timer_source)
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
- SignalType.TIMER_TASK - 定时任务信号

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

TimerTask:
- TimerTask(name, interval, callback=None, symbol="ALL", data=None) - 创建定时任务
- task.should_execute() -> bool - 判断是否应该执行任务
- task.execute(engine) - 执行任务并发送信号

TimerSource:
- TimerSource(check_interval=1) - 创建定时任务信号源
- source.add_task(task) - 添加定时任务
- source.remove_task(task_name) - 移除定时任务
- source.start(engine) - 启动信号源
- source.stop() - 停止信号源
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
    """信号类型枚举"""
    PRICE_ALERT = "price_alert"  # 价格突破信号
    TREND_CHANGE = "trend_change"  # 趋势变化信号
    VOLUME_SPIKE = "volume_spike"  # 成交量爆发信号
    CUSTOM = "custom"  # 自定义信号
    TIMER_TASK = "timer_task"  # 定时任务信号


@dataclass
class Signal:
    """信号数据类"""
    signal_type: SignalType  # 信号类型
    symbol: str  # 交易对
    timestamp: datetime  # 时间戳
    data: Dict[str, Any]  # 信号数据
    source: str = "unknown"  # 信号来源

    def __post_init__(self):
        """初始化后处理"""
        if isinstance(self.signal_type, str):
            self.signal_type = SignalType(self.signal_type)


class SignalSource(ABC):
    """信号源抽象基类"""
    
    @abstractmethod
    def start(self, engine: "EventEngine"):
        """启动信号源"""
        pass

    @abstractmethod
    def stop(self):
        """停止信号源"""
        pass


class BinanceFuturesSource(SignalSource):
    """Binance 期货信号源"""
    
    def __init__(self, symbols: List[str] = None, interval: str = "1m", check_interval: int = 5):
        """
        初始化 Binance 期货信号源
        
        Args:
            symbols: 交易对列表，默认 ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
            interval: K 线时间间隔，默认 "1m"
            check_interval: 检查间隔（秒），默认 5
        """
        self.symbols = symbols or ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        self.interval = interval
        self.check_interval = check_interval
        self.connector = BinanceConnector()
        self._running = False
        self._thread = None
        self._engine = None

    def start(self, engine: "EventEngine"):
        """启动信号源"""
        self._engine = engine
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """停止信号源"""
        self._running = False
        if self._thread:
            self._thread.join()

    def _run(self):
        """运行信号源"""
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
        """分析 K 线数据"""
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


class TimerTask:
    """定时任务类"""
    
    def __init__(self, name: str, interval: int, callback: Callable = None, symbol: str = "ALL", data: Dict[str, Any] = None):
        """
        初始化定时任务
        
        Args:
            name: 任务名称
            interval: 执行间隔（秒）
            callback: 回调函数，可选
            symbol: 交易对，默认 ALL
            data: 任务数据，可选
        """
        self.name = name
        self.interval = interval
        self.callback = callback
        self.symbol = symbol
        self.data = data or {}
        self.last_executed = time.time()

    def should_execute(self) -> bool:
        """判断是否应该执行任务"""
        return time.time() - self.last_executed >= self.interval

    def execute(self, engine: "EventEngine"):
        """执行任务"""
        self.last_executed = time.time()
        
        # 执行回调函数（如果有）
        if self.callback:
            try:
                result = self.callback()
                if result:
                    self.data['callback_result'] = result
            except Exception as e:
                print(f"Error executing task {self.name}: {e}")
                self.data['error'] = str(e)
        
        # 发送信号
        engine.emit_signal(
            SignalType.TIMER_TASK, self.symbol,
            {"task_name": self.name, "interval": self.interval, **self.data},
            "timer_source"
        )


class TimerSource(SignalSource):
    """定时任务信号源"""
    
    def __init__(self, check_interval: int = 1):
        """
        初始化定时任务信号源
        
        Args:
            check_interval: 检查间隔（秒），默认 1
        """
        self.check_interval = check_interval
        self._tasks: List[TimerTask] = []
        self._running = False
        self._thread = None
        self._engine = None

    def add_task(self, task: TimerTask):
        """添加定时任务"""
        self._tasks.append(task)

    def remove_task(self, task_name: str):
        """移除定时任务"""
        self._tasks = [t for t in self._tasks if t.name != task_name]

    def start(self, engine: "EventEngine"):
        """启动信号源"""
        self._engine = engine
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """停止信号源"""
        self._running = False
        if self._thread:
            self._thread.join()

    def _run(self):
        """运行信号源"""
        while self._running:
            for task in self._tasks:
                if task.should_execute():
                    task.execute(self._engine)
            time.sleep(self.check_interval)


class EventBus:
    """事件总线"""
    
    def __init__(self):
        """初始化事件总线"""
        self._subscribers: Dict[SignalType, List[Callable]] = {}
        self._global_subscribers: List[Callable] = []
        self._lock = threading.Lock()

    def subscribe(self, signal_type: SignalType, handler: Callable[[Signal], None]):
        """订阅特定类型的信号"""
        with self._lock:
            if signal_type not in self._subscribers:
                self._subscribers[signal_type] = []
            self._subscribers[signal_type].append(handler)

    def subscribe_global(self, handler: Callable[[Signal], None]):
        """订阅所有信号"""
        with self._lock:
            self._global_subscribers.append(handler)

    def unsubscribe(self, signal_type: SignalType, handler: Callable[[Signal], None]):
        """取消订阅"""
        with self._lock:
            if signal_type in self._subscribers:
                try:
                    self._subscribers[signal_type].remove(handler)
                except ValueError:
                    pass

    def emit(self, signal: Signal):
        """发送信号"""
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
    """策略基类"""
    
    def __init__(self, name: str, engine: "EventEngine"):
        """
        初始化策略
        
        Args:
            name: 策略名称
            engine: 事件引擎实例
        """
        self.name = name
        self._engine = engine
        self._enabled = True

    def on(self, signal_type: SignalType):
        """装饰器，订阅信号"""
        def decorator(func: Callable[[Signal], None]):
            self._engine.bus.subscribe(signal_type, func)
            return func
        return decorator

    def enable(self):
        """启用策略"""
        self._enabled = True

    def disable(self):
        """禁用策略"""
        self._enabled = False


class StrategyRegistry:
    """策略注册表"""
    
    _strategies: Dict[str, type] = {}

    @classmethod
    def register(cls, name: str = None):
        """
        装饰器，注册策略类
        
        Args:
            name: 策略名称，默认使用类名
        """
        def decorator(strategy_cls: type):
            cls._strategies[name or strategy_cls.__name__] = strategy_cls
            return strategy_cls
        return decorator

    @classmethod
    def create(cls, name: str, engine: "EventEngine") -> Optional[Strategy]:
        """
        创建策略实例
        
        Args:
            name: 策略名称
            engine: 事件引擎实例
            
        Returns:
            策略实例，如果不存在则返回 None
        """
        if name not in cls._strategies:
            return None
        return cls._strategies[name](name, engine)

    @classmethod
    def list_strategies(cls):
        """列出所有已注册的策略"""
        return list(cls._strategies.keys())


class EventEngine:
    """事件引擎（单例）"""
    
    _instance = None

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初始化事件引擎"""
        if self._initialized:
            return
        self._bus = EventBus()
        self._strategies: Dict[str, Strategy] = {}
        self._sources: Dict[str, SignalSource] = {}
        self._initialized = True

    @property
    def bus(self) -> EventBus:
        """获取事件总线"""
        return self._bus

    @property
    def strategies(self) -> Dict[str, Strategy]:
        """获取所有策略"""
        return self._strategies

    def register_strategy(self, name: str, strategy: Strategy):
        """注册策略"""
        self._strategies[name] = strategy

    def get_strategy(self, name: str) -> Optional[Strategy]:
        """获取策略"""
        return self._strategies.get(name)

    def create_strategy(self, name: str) -> Optional[Strategy]:
        """
        创建并激活策略
        
        Args:
            name: 策略名称
            
        Returns:
            策略实例，如果不存在则返回 None
        """
        strategy = StrategyRegistry.create(name, self)
        if strategy:
            self._strategies[name] = strategy
        return strategy

    def register_source(self, name: str, source: SignalSource):
        """注册信号源"""
        self._sources[name] = source

    def start_sources(self):
        """启动所有信号源"""
        for source in self._sources.values():
            source.start(self)

    def stop_sources(self):
        """停止所有信号源"""
        for source in self._sources.values():
            source.stop()

    def emit_signal(self, signal_type: SignalType, symbol: str, data: Dict[str, Any], source: str = "unknown") -> Signal:
        """
        发送信号
        
        Args:
            signal_type: 信号类型
            symbol: 交易对
            data: 信号数据
            source: 信号来源
            
        Returns:
            发送的信号对象
        """
        signal = Signal(
            signal_type=signal_type,
            symbol=symbol,
            timestamp=datetime.now(),
            data=data,
            source=source
        )
        self._bus.emit(signal)
        return signal


engine = EventEngine()  # 全局事件引擎实例