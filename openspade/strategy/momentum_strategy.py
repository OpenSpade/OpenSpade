
from openspade.app.signal import engine, StrategyRegistry, SignalType
import numpy as np

@StrategyRegistry.register("momentum")
class MomentumStrategy:
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
        if len(self.symbols[symbol]) > 10:
            self.symbols[symbol] = self.symbols[symbol][-10:]
        
        # Calculate momentum
        if len(self.symbols[symbol]) >= 10:
            # Calculate rate of change
            roc = (self.symbols[symbol][-1] - self.symbols[symbol][0]) / self.symbols[symbol][0] * 100
            
            # Generate signals
            if roc > 2 and not hasattr(self, f"{symbol}_position"):
                print(f"[{self.name}] BUY signal for {symbol} at {signal.data['price']}, Momentum: {roc:.2f}%")
                setattr(self, f"{symbol}_position", signal.data['price'])
            elif roc < -1 and hasattr(self, f"{symbol}_position"):
                entry_price = getattr(self, f"{symbol}_position")
                profit = (signal.data['price'] - entry_price) / entry_price * 100
                print(f"[{self.name}] SELL signal for {symbol} at {signal.data['price']}, Profit: {profit:.2f}%")
                delattr(self, f"{symbol}_position")
