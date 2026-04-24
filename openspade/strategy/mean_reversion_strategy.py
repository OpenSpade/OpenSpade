
from openspade.app.signal import engine, StrategyRegistry, SignalType
import numpy as np

@StrategyRegistry.register("mean_reversion")
class MeanReversionStrategy:
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
        if len(self.symbols[symbol]) > 30:
            self.symbols[symbol] = self.symbols[symbol][-30:]
        
        # Calculate mean and standard deviation
        if len(self.symbols[symbol]) >= 30:
            mean_price = np.mean(self.symbols[symbol])
            std_price = np.std(self.symbols[symbol])
            current_price = signal.data['price']
            
            # Generate signals
            z_score = (current_price - mean_price) / std_price
            
            if z_score < -1.5 and not hasattr(self, f"{symbol}_position"):
                print(f"[{self.name}] BUY signal for {symbol} at {signal.data['price']}, Z-score: {z_score:.2f}")
                setattr(self, f"{symbol}_position", signal.data['price'])
            elif z_score > 1.5 and hasattr(self, f"{symbol}_position"):
                entry_price = getattr(self, f"{symbol}_position")
                profit = (signal.data['price'] - entry_price) / entry_price * 100
                print(f"[{self.name}] SELL signal for {symbol} at {signal.data['price']}, Profit: {profit:.2f}%")
                delattr(self, f"{symbol}_position")
