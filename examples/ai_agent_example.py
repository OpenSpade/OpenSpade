#!/usr/bin/env python3
"""
AI Agent Example

This script demonstrates how to use the AI Agent to:
1. Download K-line data from Binance
2. Generate trading strategies
3. Backtest strategies
4. Optimize strategy parameters
"""

from openspade.ai.agent import AIAgent
import time


def main():
    # Initialize AI Agent
    agent = AIAgent(data_dir="data")
    
    # 1. Download K-line data
    print("Step 1: Downloading K-line data...")
    data_file = agent.download_klines(
        symbol="BTCUSDT",
        interval="1h",
        days=30  # Download 30 days of 1-hour data
    )
    
    if not data_file:
        print("Failed to download data, exiting...")
        return
    
    time.sleep(1)
    
    # 2. Generate strategies
    print("\nStep 2: Generating trading strategies...")
    
    # Generate trend following strategy
    trend_strategy = agent.generate_strategy(strategy_type="trend_following")
    trend_file = agent.save_strategy(trend_strategy, "trend_following_strategy")
    
    # Generate mean reversion strategy
    mean_strategy = agent.generate_strategy(strategy_type="mean_reversion")
    mean_file = agent.save_strategy(mean_strategy, "mean_reversion_strategy")
    
    # Generate momentum strategy
    momentum_strategy = agent.generate_strategy(strategy_type="momentum")
    momentum_file = agent.save_strategy(momentum_strategy, "momentum_strategy")
    
    time.sleep(1)
    
    # 3. Backtest strategies
    print("\nStep 3: Backtesting strategies...")
    
    # Backtest trend following strategy
    print("\nBacktesting trend following strategy...")
    trend_results = agent.backtest_strategy(trend_file, data_file)
    print(f"Trend following results: {trend_results}")
    
    # Backtest mean reversion strategy
    print("\nBacktesting mean reversion strategy...")
    mean_results = agent.backtest_strategy(mean_file, data_file)
    print(f"Mean reversion results: {mean_results}")
    
    # Backtest momentum strategy
    print("\nBacktesting momentum strategy...")
    momentum_results = agent.backtest_strategy(momentum_file, data_file)
    print(f"Momentum results: {momentum_results}")
    
    time.sleep(1)
    
    # 4. Optimize strategy
    print("\nStep 4: Optimizing strategy parameters...")
    
    # Define parameters to optimize
    params = {
        "ma_short": [5, 20],  # Short moving average period
        "ma_long": [20, 50]   # Long moving average period
    }
    
    # Optimize trend following strategy
    print("Optimizing trend following strategy...")
    optimization_results = agent.optimize_strategy(trend_file, data_file, params)
    print(f"Optimization results: {optimization_results}")
    
    print("\nAI Agent workflow completed successfully!")


if __name__ == "__main__":
    main()
