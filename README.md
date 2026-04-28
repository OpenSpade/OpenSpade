# OpenSpade - Binance Futures Trading System

A comprehensive cryptocurrency trading system for Binance futures markets, featuring capital pool management, automated trading strategies, and risk management.

## Features

- **Binance API Integration**: Connect to Binance spot and futures accounts to fetch balances, positions, and prices
- **Trading Strategies**: Support for Grid and DCA (Dollar Cost Averaging) strategies
- **Capital Pool Management**: Track and allocate funds across multiple trading strategies
- **Risk Management**: Built-in risk controls including position limits, drawdown protection, and leverage checks
- **Technical Analysis**: Calculate technical indicators (RSI, MACD, MA, Bollinger Bands) and generate trading signals
- **Data Persistence**: SQLite database for storing trading data, strategies, and risk records

## Project Structure

```
OpenSpade/
├── binance_connector.py       # Binance API connection module
├── capital_pool.py            # Capital pool and strategy management
├── risk_manager.py            # Risk control and monitoring
├── binance_futures_scraper.py # Market data scraping and analysis
├── database_extension.py      # Database persistence layer
├── requirements.txt           # Python dependencies
└── tests/
    └── test_capital_pool.py   # Unit tests
```

## Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Dependencies

- `six>=1.16.0`
- `requests` (for Binance API calls)
- `pandas` (for data manipulation)
- `numpy` (for numerical calculations)

## Quick Start

### 1. Initialize Database

```python
from openspade.db.database_extension import init_capital_pool_tables

init_capital_pool_tables()
```

### 2. Connect to Binance

```python
from openspade.gateway.binance_connector import BinanceConnector

connector = BinanceConnector(api_key='your_api_key', api_secret='your_api_secret')

# Get account balances
spot_balance = connector.get_spot_balance()
futures_balance = connector.get_futures_balance()
total_assets = connector.get_total_assets()

# Get portfolio summary
summary = connector.get_portfolio_summary()
```

### 3. Create Trading Strategies

```python
from capital_pool import CapitalPool, GridStrategy, DCAStrategy

pool = CapitalPool(total_assets=10000.0)

grid_strategy = GridStrategy(
    strategy_id="grid_1",
    symbol="BTCUSDT",
    initial_amount=1000.0,
    grid_num=10,
    grid_range=0.10
)

pool.allocate_funds(grid_strategy, 1000.0)
```

### 4. Risk Management

```python
from risk_manager import RiskManager, RiskConfig

config = RiskConfig(
    max_position_ratio=0.8,
    max_single_position_ratio=0.3,
    max_loss_per_strategy=0.15,
    max_drawdown=0.20
)

risk_manager = RiskManager(config)

# Check if allocation is safe
can_allocate = risk_manager.can_allocate(amount=1000.0, total_value=10000.0, current_allocated=5000.0)
safe_amount = risk_manager.get_safe_allocation(requested_amount=2000.0, total_value=10000.0, current_allocated=5000.0)
```

### 5. Scrape Market Data and Generate Signals

```python
from binance_futures_scraper import (
    init_database,
    get_binance_futures_pairs,
    analyze_trading_pair,
    analyze_multiple_pairs
)

init_database()

pairs = get_binance_futures_pairs()

# Analyze single pair
analysis = analyze_trading_pair("BTCUSDT")

# Analyze multiple pairs
results = analyze_multiple_pairs(pairs, max_pairs=20)
```

## API Reference

### BinanceConnector

| Method | Description |
|--------|-------------|
| `get_spot_balance()` | Get USDT balance in spot account |
| `get_futures_balance()` | Get USDT balance in futures account |
| `get_total_assets()` | Get total assets across all accounts |
| `get_positions()` | Get all futures positions |
| `get_position_info(symbol)` | Get specific position by symbol |
| `get_current_price(symbol)` | Get current price for a symbol |
| `get_portfolio_summary()` | Get comprehensive portfolio data |

### CapitalPool

| Method | Description |
|--------|-------------|
| `allocate_funds(strategy, amount)` | Allocate funds to a strategy |
| `release_funds(strategy_id)` | Release funds from a strategy |
| `convert_strategy(old_id, new_strategy)` | Convert strategy to a new type |
| `get_pool_status()` | Get current pool status |

### RiskManager

| Method | Description |
|--------|-------------|
| `check_all_risks(portfolio_value, allocations, prices)` | Perform comprehensive risk check |
| `register_strategy(strategy_id, entry_price, entry_amount)` | Register a strategy for monitoring |
| `can_allocate(amount, total_value, current_allocated)` | Check if allocation is within risk limits |
| `get_safe_allocation(requested, total, current)` | Calculate safe allocation amount |

## Strategy Types

### Grid Strategy

Divides price range into multiple levels and places buy/sell orders at each level. Suitable for sideways markets.

Parameters:
- `grid_num`: Number of grid levels
- `grid_range`: Price range percentage
- `reserved_ratio`: Reserved funds ratio

### DCA Strategy

Dollar-cost averaging strategy that buys at regular intervals. Triggered when grid strategy breaks out of range.

Parameters:
- `dca_interval`: Interval between DCA purchases (seconds)
- `dca_amount_ratio`: Ratio of current amount to invest per DCA

## Risk Levels

- **LOW**: Normal operation
- **MEDIUM**: Drawdown warning triggered
- **HIGH**: Position full or multiple warnings
- **CRITICAL**: Drawdown stop or critical risk detected

## Database Tables

- `trading_pairs`: Trading pair information
- `klines`: Historical K-line data
- `analysis_results`: Technical analysis results
- `capital_pool`: Capital pool status
- `strategies`: Strategy records
- `fund_allocations`: Fund allocation records
- `risk_records`: Risk tracking records
- `risk_alerts`: Risk alert history

## License

MIT License
