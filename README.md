# OpenSpade - Binance Futures Trading System

A comprehensive cryptocurrency trading system for Binance futures markets, featuring capital pool management, automated trading strategies, real-time risk control, AI-powered strategy optimization, and multi-channel notifications.

## Features

- **Binance API Integration**: Connect to Binance spot and futures accounts to fetch balances, positions, and prices
- **Trading Strategies**: Support for Grid, DCA (Dollar Cost Averaging), Trend Following, Mean Reversion, and Momentum strategies
- **Capital Pool Management**: Track and allocate funds across multiple trading strategies
- **Risk Management**: Multi-level risk controls (LOW/MEDIUM/HIGH/CRITICAL) including position limits, drawdown protection, and stop condition enforcement
- **Technical Analysis**: Calculate technical indicators (RSI, MACD, MA, Bollinger Bands) and generate trading signals
- **AI Agent**: Automated strategy development with genetic algorithm optimization (DEAP)
- **Asset Sync**: Automatic periodic synchronization of Binance account assets with local database
- **Notification System**: Multi-channel alerts via DingTalk, Telegram, Email, SMS, and Voice with priority-based routing
- **REST API**: Flask-based API server with scheduled task support for external integrations
- **CLI Interface**: Full-featured command-line tool for account management, strategy creation, risk configuration, and notifications
- **Data Persistence**: SQLite database for storing trading data, strategies, risk records, and asset history
- **Market Monitoring**: Binance delisting announcement crawling and volume breakout detection

## Project Structure

```
OpenSpade/
├── openspade/                          # Core package
│   ├── gateway/
│   │   └── binance_connector.py        # Binance API connection module
│   ├── db/
│   │   └── database_extension.py       # SQLite persistence layer
│   ├── cli/
│   │   └── cli.py                      # CLI interface (click-based)
│   ├── api/
│   │   └── app.py                      # Flask REST API server
│   ├── ai/
│   │   └── agent.py                    # AI agent for strategy optimization
│   ├── strategy/
│   │   ├── trend_following_strategy.py # Trend following strategy
│   │   ├── mean_reversion_strategy.py  # Mean reversion strategy
│   │   └── momentum_strategy.py        # Momentum strategy
│   ├── messsage/
│   │   └── notification.py             # Multi-channel notification system
│   ├── app/
│   │   ├── signal/                     # Signal generation module
│   │   └── crawl_binance_delisting.py  # Delisting announcement crawler
│   └── asset_sync.py                   # Asset synchronization service
├── capital_pool.py                     # Capital pool and strategy management
├── risk_manager.py                     # Risk control and monitoring
├── binance_futures_scraper.py          # Market data scraping and analysis
├── main.py                             # Application entry point
├── setup.py                            # Package configuration
├── requirements.txt                    # Python dependencies
├── frontend/                           # Vue.js frontend (Vite)
├── examples/
│   └── ai_agent_example.py            # AI agent usage example
└── tests/
    ├── test_capital_pool.py            # Capital pool unit tests
    ├── test_db.py                      # Database unit tests
    └── test_openspade_db.py            # OpenSpade DB integration tests
```

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd OpenSpade
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Install as a package (optional, enables `openspade` CLI command):

```bash
pip install -e .
```

## Dependencies

### Core

- `six>=1.16.0` - Python 2/3 compatibility
- `requests>=2.28.0` - Binance API HTTP client
- `click>=8.0.0` - CLI framework
- `twilio>=8.0.0` - SMS/Voice notifications

### Data Processing

- `numpy` - Numerical calculations
- `pandas` - Data analysis and indicator computation
- `simplejson` - JSON processing

### Web Framework

- `Flask` - REST API server
- `Flask-Cors` - Cross-origin request support
- `Flask-APScheduler` - Scheduled task management

### Database

- `peewee` - SQLite ORM
- `pymongo` - MongoDB support

### Visualization

- `matplotlib`, `seaborn`, `plotly` - Data visualization
- `PySide6`, `pyqtgraph`, `QDarkStyle` - Desktop GUI

### AI & Optimization

- `deap` - Genetic algorithm framework for strategy optimization

### Web Scraping

- `selenium`, `webdriver_manager` - Browser automation
- `beautifulsoup4` - HTML parsing

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
from tests.risk_manager import RiskManager, RiskConfig

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

### 6. Asset Synchronization

```python
from openspade.asset_sync import AssetSync

sync = AssetSync(api_key='your_api_key', api_secret='your_api_secret')

# One-time sync
result = sync.sync_assets()

# Start periodic sync (background thread)
sync.start()
```

## CLI Usage

The `openspade` CLI provides full system management:

```bash
# Show system info
openspade info

# Binance account commands
openspade binance balance --api-key <KEY> --api-secret <SECRET>
openspade binance positions --api-key <KEY> --api-secret <SECRET>

# Capital pool management
openspade capital init 10000
openspade capital grid grid_1 BTCUSDT 1000 --grid-num 10 --grid-range 0.10
openspade capital dca dca_1 ETHUSDT 500 --dca-interval 3600

# Risk management
openspade risk config --max-drawdown 0.20 --max-position-ratio 0.8
openspade risk check 1000 10000 5000

# Notifications
openspade notify send "Alert Title" "Alert Content" --priority high
```

## REST API

Start the API server:

```bash
python -m openspade.api.app
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/init` | Initialize Binance connector |
| GET | `/api/assets/spot` | Get spot account assets |
| GET | `/api/assets/futures` | Get futures account assets |
| GET | `/api/assets/all` | Get all account assets |
| GET | `/api/assets/total` | Get total asset value |
| GET | `/api/positions` | Get all futures positions |
| GET | `/api/positions/<symbol>` | Get specific position |
| GET | `/api/prices/<symbol>` | Get current price |
| GET | `/api/prices` | Get all prices |
| GET | `/api/portfolio/summary` | Get portfolio summary |

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

### Trend Following Strategy

Follows market trends using moving average crossovers and trend indicators.

### Mean Reversion Strategy

Identifies overbought/oversold conditions and trades on price reversion to the mean.

### Momentum Strategy

Captures price momentum using rate-of-change and momentum indicators.

## Risk Levels

| Level | Condition | Action |
|-------|-----------|--------|
| **LOW** | Normal operation | Continue trading |
| **MEDIUM** | Drawdown warning triggered | Alert notification |
| **HIGH** | Position full or multiple warnings | Restrict new allocations |
| **CRITICAL** | Drawdown stop or critical risk detected | Auto-liquidation triggered |

## Database Tables

- `trading_pairs`: Trading pair information
- `klines`: Historical K-line data
- `analysis_results`: Technical analysis results
- `capital_pool`: Capital pool status
- `strategies`: Strategy records
- `fund_allocations`: Fund allocation records
- `risk_records`: Risk tracking records
- `risk_alerts`: Risk alert history
- `assets`: Current asset snapshots
- `asset_history`: Historical asset records
- `asset_sync_log`: Synchronization audit log

## Running Tests

```bash
pytest tests/
```

## License

MIT License
