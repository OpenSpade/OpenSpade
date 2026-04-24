from typing import Dict, List, Optional, Any
import os
import time
import json
import importlib.util
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from deap import base, creator, tools, algorithms

from binance_connector import BinanceConnector


class AIAgent:
    """AI Agent for automated trading strategy development"""
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize AI Agent
        
        Args:
            data_dir: Directory to store downloaded data
        """
        self.data_dir = data_dir
        self.connector = BinanceConnector()
        os.makedirs(data_dir, exist_ok=True)
        
    def download_klines(self, symbol: str, interval: str = "1m", days: int = 7) -> str:
        """
        Download K-line data from Binance
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            interval: Time interval (e.g., "1m", "1h", "1d")
            days: Number of days to download
            
        Returns:
            Path to the downloaded data file
        """
        print(f"Downloading {symbol} {interval} data for {days} days...")
        
        # Calculate total bars needed
        interval_map = {
            "1m": 1440,  # 1440 minutes per day
            "3m": 480,
            "5m": 288,
            "15m": 96,
            "30m": 48,
            "1h": 24,
            "2h": 12,
            "4h": 6,
            "6h": 4,
            "8h": 3,
            "12h": 2,
            "1d": 1
        }
        
        bars_per_day = interval_map.get(interval, 24)
        total_bars = bars_per_day * days
        
        # Download data in chunks to avoid API limits
        all_klines = []
        limit = 1000  # Binance API limit
        chunks = (total_bars + limit - 1) // limit
        
        for i in range(chunks):
            print(f"Downloading chunk {i+1}/{chunks}...")
            klines = self.connector.get_klines(symbol, interval, limit)
            if klines:
                all_klines.extend(klines)
                time.sleep(0.1)  # Respect rate limits
        
        # Save data to CSV
        df = pd.DataFrame(all_klines)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            filename = f"{symbol}_{interval}_{days}days_{datetime.now().strftime('%Y%m%d')}.csv"
            filepath = os.path.join(self.data_dir, filename)
            df.to_csv(filepath)
            print(f"Data saved to {filepath}")
            return filepath
        else:
            print("Failed to download data")
            return None
    
    def generate_strategy(self, strategy_type: str = "trend_following") -> str:
        """
        Generate trading strategy code
        
        Args:
            strategy_type: Type of strategy to generate
            
        Returns:
            Generated strategy code
        """
        strategies = {
            "trend_following": self._generate_trend_following_strategy,
            "mean_reversion": self._generate_mean_reversion_strategy,
            "momentum": self._generate_momentum_strategy
        }
        
        if strategy_type not in strategies:
            strategy_type = "trend_following"
        
        return strategies[strategy_type]()
    
    def _generate_trend_following_strategy(self) -> str:
        """Generate trend following strategy"""
        return """
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
"""
    
    def _generate_mean_reversion_strategy(self) -> str:
        """Generate mean reversion strategy"""
        return """
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
"""
    
    def _generate_momentum_strategy(self) -> str:
        """Generate momentum strategy"""
        return """
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
"""
    
    def save_strategy(self, code: str, filename: str) -> str:
        """
        Save generated strategy to file
        
        Args:
            code: Generated strategy code
            filename: Name of the file to save
            
        Returns:
            Path to the saved file
        """
        filepath = os.path.join("openspade", "strategy", f"{filename}.py")
        with open(filepath, 'w') as f:
            f.write(code)
        print(f"Strategy saved to {filepath}")
        return filepath
    
    def backtest_strategy(self, strategy_file: str, data_file: str) -> Dict[str, Any]:
        """
        Backtest a strategy using historical data
        
        Args:
            strategy_file: Path to strategy file
            data_file: Path to historical data file
            
        Returns:
            Backtest results
        """
        print(f"Backtesting strategy from {strategy_file} using data from {data_file}")
        
        # Load data
        df = pd.read_csv(data_file, index_col='timestamp', parse_dates=True)
        
        # Create a simple backtest engine
        class BacktestEngine:
            def __init__(self, data):
                self.data = data
                self.balance = 10000  # Initial balance
                self.position = 0
                self.trades = []
                self.current_price = 0
            
            def on_price_update(self, price):
                self.current_price = price
            
            def buy(self):
                if self.position == 0:
                    self.position = self.balance / self.current_price
                    self.balance = 0
                    self.trades.append({
                        'type': 'buy',
                        'price': self.current_price,
                        'timestamp': datetime.now()
                    })
            
            def sell(self):
                if self.position > 0:
                    self.balance = self.position * self.current_price
                    self.trades.append({
                        'type': 'sell',
                        'price': self.current_price,
                        'timestamp': datetime.now(),
                        'profit': self.balance - 10000  # Initial balance
                    })
                    self.position = 0
            
            def get_results(self):
                # Calculate final balance
                if self.position > 0:
                    final_balance = self.position * self.current_price
                else:
                    final_balance = self.balance
                
                # Calculate metrics
                total_return = (final_balance - 10000) / 10000 * 100
                num_trades = len(self.trades) // 2  # Each trade pair is buy + sell
                
                # Calculate win rate
                winning_trades = 0
                for i in range(1, len(self.trades), 2):
                    buy_price = self.trades[i-1]['price']
                    sell_price = self.trades[i]['price']
                    if sell_price > buy_price:
                        winning_trades += 1
                
                win_rate = (winning_trades / num_trades * 100) if num_trades > 0 else 0
                
                return {
                    'initial_balance': 10000,
                    'final_balance': final_balance,
                    'total_return': total_return,
                    'num_trades': num_trades,
                    'win_rate': win_rate,
                    'trades': self.trades
                }
        
        # Simulate price updates
        engine = BacktestEngine(df)
        
        # For simplicity, we'll simulate a basic strategy
        # In a real implementation, we would load and execute the actual strategy
        for i, row in enumerate(df.iterrows()):
            index, row_data = row
            engine.on_price_update(row_data['close'])
            
            # Simple moving average crossover strategy for demonstration
            if i > 20:
                ma5 = df['close'].iloc[i-5:i].mean()
                ma20 = df['close'].iloc[i-20:i].mean()
                
                if ma5 > ma20 and engine.position == 0:
                    engine.buy()
                elif ma5 < ma20 and engine.position > 0:
                    engine.sell()
        
        # Close any open position
        if engine.position > 0:
            engine.sell()
        
        results = engine.get_results()
        print(f"Backtest results: {results}")
        return results
    
    def optimize_strategy(self, strategy_file: str, data_file: str, params: Dict[str, List[float]]) -> Dict[str, Any]:
        """
        Optimize strategy parameters using genetic algorithm
        
        Args:
            strategy_file: Path to strategy file
            data_file: Path to historical data file
            params: Parameters to optimize with their ranges
            
        Returns:
            Optimized parameters and backtest results
        """
        print(f"Optimizing strategy from {strategy_file} using data from {data_file}")
        
        # Load data
        df = pd.read_csv(data_file, index_col='timestamp', parse_dates=True)
        
        # Define fitness function
        def evaluate(individual):
            # Map individual to parameters
            param_values = {}
            for i, (param, range_) in enumerate(params.items()):
                # Scale individual value to parameter range
                param_values[param] = range_[0] + (range_[1] - range_[0]) * individual[i]
            
            # Run backtest with these parameters
            engine = BacktestEngine(df)
            
            # Simple strategy with optimized parameters
            ma_short = int(param_values['ma_short'])
            ma_long = int(param_values['ma_long'])
            
            for i, row in enumerate(df.iterrows()):
                index, row_data = row
                engine.on_price_update(row_data['close'])
                
                if i > ma_long:
                    ma_short_val = df['close'].iloc[i-ma_short:i].mean()
                    ma_long_val = df['close'].iloc[i-ma_long:i].mean()
                    
                    if ma_short_val > ma_long_val and engine.position == 0:
                        engine.buy()
                    elif ma_short_val < ma_long_val and engine.position > 0:
                        engine.sell()
            
            if engine.position > 0:
                engine.sell()
            
            results = engine.get_results()
            return (results['total_return'],)
        
        # Create genetic algorithm components
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)
        
        toolbox = base.Toolbox()
        
        # Register genetic operators
        num_params = len(params)
        toolbox.register("attr_float", np.random.random)
        toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_float, n=num_params)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        
        toolbox.register("evaluate", evaluate)
        toolbox.register("mate", tools.cxBlend, alpha=0.5)
        toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=0.1, indpb=0.2)
        toolbox.register("select", tools.selTournament, tournsize=3)
        
        # Run genetic algorithm
        population = toolbox.population(n=50)
        hof = tools.HallOfFame(1)
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean)
        stats.register("std", np.std)
        stats.register("min", np.min)
        stats.register("max", np.max)
        
        algorithms.eaSimple(population, toolbox, cxpb=0.5, mutpb=0.2, ngen=10, stats=stats, halloffame=hof)
        
        # Get best individual
        best_individual = hof[0]
        best_params = {}
        for i, (param, range_) in enumerate(params.items()):
            best_params[param] = range_[0] + (range_[1] - range_[0]) * best_individual[i]
        
        # Run backtest with best parameters
        best_results = evaluate(best_individual)
        
        print(f"Optimized parameters: {best_params}")
        print(f"Best return: {best_results[0]:.2f}%")
        
        return {
            'best_params': best_params,
            'best_return': best_results[0],
            'optimization_history': str(stats)
        }


# BacktestEngine class for the optimize_strategy method
class BacktestEngine:
    def __init__(self, data):
        self.data = data
        self.balance = 10000  # Initial balance
        self.position = 0
        self.trades = []
        self.current_price = 0
    
    def on_price_update(self, price):
        self.current_price = price
    
    def buy(self):
        if self.position == 0:
            self.position = self.balance / self.current_price
            self.balance = 0
            self.trades.append({
                'type': 'buy',
                'price': self.current_price,
                'timestamp': datetime.now()
            })
    
    def sell(self):
        if self.position > 0:
            self.balance = self.position * self.current_price
            self.trades.append({
                'type': 'sell',
                'price': self.current_price,
                'timestamp': datetime.now(),
                'profit': self.balance - 10000  # Initial balance
            })
            self.position = 0
    
    def get_results(self):
        # Calculate final balance
        if self.position > 0:
            final_balance = self.position * self.current_price
        else:
            final_balance = self.balance
        
        # Calculate metrics
        total_return = (final_balance - 10000) / 10000 * 100
        num_trades = len(self.trades) // 2  # Each trade pair is buy + sell
        
        # Calculate win rate
        winning_trades = 0
        for i in range(1, len(self.trades), 2):
            buy_price = self.trades[i-1]['price']
            sell_price = self.trades[i]['price']
            if sell_price > buy_price:
                winning_trades += 1
        
        win_rate = (winning_trades / num_trades * 100) if num_trades > 0 else 0
        
        return {
            'initial_balance': 10000,
            'final_balance': final_balance,
            'total_return': total_return,
            'num_trades': num_trades,
            'win_rate': win_rate,
            'trades': self.trades
        }
