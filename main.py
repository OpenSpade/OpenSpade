from openspade.api.app import app
from openspade.app.signal import engine, StrategyRegistry, SignalType, BinanceFuturesSource


@StrategyRegistry.register("demo")
class DemoStrategy:
    def __init__(self, name, engine):
        self.name = name
        self._engine = engine
        engine.bus.subscribe(SignalType.PRICE_ALERT, self.on_price_alert)
        engine.bus.subscribe(SignalType.VOLUME_SPIKE, self.on_volume_spike)

    def on_price_alert(self, signal):
        print(f"[{self.name}] 收到价格警报: {signal.symbol} - 价格: {signal.data.get('price')} - 涨幅: {signal.data.get('price_change'):.2f}%")

    def on_volume_spike(self, signal):
        print(f"[{self.name}] 收到成交量爆发: {signal.symbol} - 成交量: {signal.data.get('volume')} - 倍数: {signal.data.get('volume_ratio'):.2f}x")


def main():
    engine.create_strategy("demo")
    
    # 注册 Binance 期货信号源
    source = BinanceFuturesSource(
        symbols=["BTCUSDT", "ETHUSDT", "BNBUSDT"],
        interval="1m",
        check_interval=10
    )
    engine.register_source("binance_futures", source)
    engine.start_sources()
    
    engine.bus.subscribe_global(lambda s: print(f"[Global] {s.signal_type.value}: {s.symbol}"))
    print(f"已注册策略: {StrategyRegistry.list_strategies()}")
    print(f"已激活策略: {list(engine.strategies.keys())}")
    app.run(debug=False, host='0.0.0.0', port=5000)


if __name__ == "__main__":
    main()