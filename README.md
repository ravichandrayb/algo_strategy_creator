# Trading Signals Package

A comprehensive Python package for real-time trading signal generation and strategy analysis with Zerodha Kite API integration.

## Installation

### Option 1: Install with kite_utils (Recommended)
```bash
# Install with automatic kite_utils integration
pip install -e .
```

### Option 2: Manual Installation
```bash
# Install dependencies first
pip install pandas numpy
pip install git+https://github.com/ravichandrayb/kite-trading-utils.git

# Then install the package
pip install -e .
```

### Option 3: Without kite_utils (Limited functionality)
```bash
# Install only core dependencies (no live data fetching)
pip install pandas numpy
pip install -e . --no-deps
```

## Quick Start

### With Live Data (kite_utils integration)
```python
from trading_signals import analyze_symbol_with_kite

# Complete analysis with live data
strategies = analyze_symbol_with_kite('RELIANCE', days=180, top_n=8)
```

### With Your Own Data
```python
import pandas as pd
from trading_signals import StrategyManager, rank_strategies_simple

# Load your stock data (example format)
df = pd.DataFrame({
    'close': [100, 101, 102, 103, 104, 105, 104, 103, 102, 101]
})
df.ticker = 'AAPL'  # Set ticker attribute

# Quick ranking
top_strategies = rank_strategies_simple(df, top_n=5)
print(top_strategies)

# Or detailed analysis
manager = StrategyManager()
signals = manager.generate_signals('sma_crossover', df)
```

## Features

- **🔴 Live Data Integration**: Seamless integration with kite_utils for real-time market data
- **📊 Strategy Ranking**: Intelligent ranking system that matches strategies to market conditions
- **🎯 22+ Option Strategies**: Comprehensive collection of popular option trading strategies
- **📈 Market Analysis**: Automatic volatility, trend, and momentum analysis
- **🚀 Signal Types**: Supports both stock and option signals
- **🛠️ Easy Integration**: Drop-in solution for existing trading systems
- **Built-in Strategies**: 
  - **Stock**: SMA Crossover, and more
  - **Options**: Iron Condor, Covered Call, Straddles, Spreads, and 18+ more
- **Signal Output**:
  - Stock signals: ticker, price, action (BUY/SELL), timestamp
  - Option signals: ticker, strike, option_type, price, action, expiration, credit/debit, timestamp

## Creating Custom Strategies

```python
from trading_signals import BaseStrategy, StockSignal, Action

class MyCustomStrategy(BaseStrategy):
    def __init__(self, threshold: float = 0.02):
        super().__init__(
            name="My Custom Strategy",
            params={"threshold": threshold},
            is_option_trade=False
        )
    
    def generate_signals(self, df):
        signals = []
        # Your strategy logic here
        return signals

# Register and use
manager.register_strategy("my_strategy", MyCustomStrategy())
```

## Requirements

- pandas >= 1.3.0
- numpy >= 1.21.0
- kite_utils (automatically installed from GitHub)

## Live Data Integration

This package integrates with [kite_utils](https://github.com/ravichandrayb/kite-trading-utils) for live market data:

### Setup (One-time)
```python
# 1. Generate access token (fully automated)
from kite_utils import generate_access_token_automated
generate_access_token_automated()

# 2. Start using live data
from trading_signals import analyze_symbol_with_kite
analyze_symbol_with_kite('RELIANCE', days=252)
```

### Available Symbols
```python
from kite_utils import get_symbols
symbols = get_symbols()
print(symbols)  # ['NIFTY50', 'BANKNIFTY', 'RELIANCE', 'TCS', 'INFY', ...]
```