
from openspade.app.signal import engine, StrategyRegistry, SignalType
import numpy as np

@StrategyRegistry.register("trend_following")
class TrendFollowingStrategy:
    def __init__(self, name, engine):
        self.name = name
        self._engine = engine
        self.symbols = {}
        engine.bus.subscribe(SignalType.PRICE_ALERT, self.on_price_alert)
    
    def on_price_alert(self, signal):
        symbol = signal.symbol
        if symbol not in self.symbols:
            self.symbols[symbol] = []
        
        # Add current price to history
        self.symbols[symbol].append(signal.data['price'])
        if len(self.symbols[symbol]) > 20:
            self.symbols[symbol] = self.symbols[symbol][-20:]
        
        # Calculate moving averages
        if len(self.symbols[symbol]) >= 20:
            ma5 = np.mean(self.symbols[symbol][-5:])
            ma20 = np.mean(self.symbols[symbol])
            
            # Generate signals
            if ma5 > ma20 and not hasattr(self, f"{symbol}_position"):
                print(f"[{self.name}] BUY signal for {symbol} at {signal.data['price']}")
                setattr(self, f"{symbol}_position", signal.data['price'])
            elif ma5 < ma20 and hasattr(self, f"{symbol}_position"):
                entry_price = getattr(self, f"{symbol}_position")
                profit = (signal.data['price'] - entry_price) / entry_price * 100
                print(f"[{self.name}] SELL signal for {symbol} at {signal.data['price']}, Profit: {profit:.2f}%")
                delattr(self, f"{symbol}_position")
