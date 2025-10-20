# Trading Signals - Parameter Reference

This document provides a comprehensive reference for all strategy parameters and usage patterns.

## Quick Parameter Lookup

### SMA Crossover Strategy (`sma_crossover`)
**Type:** Stock Strategy  
**Parameters:**
- `short_window` (int, default: 20): Period for short-term moving average (1-100)
- `long_window` (int, default: 50): Period for long-term moving average (2-200)

**Usage:**
```python
from trading_signals import StrategyManager, SimpleMovingAverageStrategy

# Default parameters
manager = StrategyManager()
signals = manager.generate_signals('sma_crossover', df)

# Custom parameters
custom_strategy = manager.create_custom_strategy(
    'fast_sma',
    SimpleMovingAverageStrategy,
    short_window=10,  # Faster signals
    long_window=30
)
```

### Put Credit Spread Strategy (`put_credit_spread`)
**Type:** Option Strategy  
**Parameters:**
- `rsi_oversold` (float, default: 30): RSI threshold for oversold condition (10-50)
- `strike_offset` (float, default: 0.05): Strike offset below current price (0.01-0.20)
- `days_to_expiration` (int, default: 30): Days until expiration (7-90)

**Usage:**
```python
from trading_signals import StrategyManager, SimplePutCreditSpreadStrategy

# Default parameters
manager = StrategyManager()
signals = manager.generate_signals('put_credit_spread', df)

# Custom parameters
custom_strategy = manager.create_custom_strategy(
    'conservative_puts',
    SimplePutCreditSpreadStrategy,
    rsi_oversold=25,      # More selective
    strike_offset=0.03,   # Closer to current price
    days_to_expiration=45 # Longer time to expiration
)
```

## Data Requirements

### Required DataFrame Format
```python
import pandas as pd

# Minimum required format
df = pd.DataFrame({
    'close': [100.0, 101.5, 102.3, 101.8, 103.2]  # Required column
})
df.ticker = 'AAPL'  # Required attribute

# Full format (recommended)
df = pd.DataFrame({
    'date': pd.date_range('2023-01-01', periods=5),
    'open': [99.5, 101.0, 102.0, 101.5, 103.0],
    'high': [100.5, 102.0, 103.0, 102.5, 104.0],
    'low': [99.0, 100.5, 101.5, 101.0, 102.5],
    'close': [100.0, 101.5, 102.3, 101.8, 103.2],
    'volume': [1000000, 1200000, 1100000, 900000, 1300000]
})
df.ticker = 'AAPL'
```

## Parameter Discovery Methods

### Method 1: Print All Strategy Help
```python
from trading_signals import StrategyManager

manager = StrategyManager()
manager.print_strategy_help()  # Shows all strategies with parameters
```

### Method 2: Get Specific Strategy Parameters
```python
manager = StrategyManager()
params = manager.get_strategy_parameters('sma_crossover')
print(params)
# Output:
# {
#     'strategy_name': 'sma_crossover',
#     'parameters': {'short_window': 20, 'long_window': 50},
#     'parameter_descriptions': {
#         'short_window': 'Period for short-term moving average...',
#         'long_window': 'Period for long-term moving average...'
#     },
#     'required_columns': ['close'],
#     'is_option_trade': False
# }
```

### Method 3: Package-Level Help
```python
import trading_signals
trading_signals.help()  # Comprehensive package help
```

### Method 4: Strategy Info Function
```python
from trading_signals import get_all_strategy_info

all_info = get_all_strategy_info()
for strategy_name, info in all_info.items():
    print(f"Strategy: {strategy_name}")
    print(f"Parameters: {info['parameters']}")
    print(f"Descriptions: {info['parameter_descriptions']}")
```

## Signal Output Reference

### Stock Signals (StockSignal)
```python
# Example signal output
signal = StockSignal(
    ticker="AAPL",           # str: Stock symbol
    price=150.75,            # float: Current price
    action=Action.BUY,       # Action.BUY or Action.SELL
    timestamp=datetime.now() # datetime: Signal time
)
```

### Option Signals (OptionSignal)
```python
# Example signal output
signal = OptionSignal(
    ticker="AAPL",                    # str: Underlying symbol
    strike=145.0,                     # float: Strike price
    option_type=OptionType.PUT,       # OptionType.CALL or OptionType.PUT
    price=3.50,                       # float: Option premium
    action=Action.SELL,               # Action.BUY or Action.SELL
    expiration="2023-12-15",          # str: Expiration date
    credit_debit=CreditDebit.CREDIT,  # CreditDebit.CREDIT or CreditDebit.DEBIT
    timestamp=datetime.now()          # datetime: Signal time
)
```

## Common Usage Patterns

### Pattern 1: Quick Signal Generation
```python
from trading_signals import StrategyManager
import pandas as pd

manager = StrategyManager()
df = pd.read_csv('your_data.csv')
df.ticker = 'AAPL'

# Generate stock signals
stock_signals = manager.generate_signals('sma_crossover', df)

# Generate option signals
option_signals = manager.generate_signals('put_credit_spread', df)
```

### Pattern 2: Custom Strategy Creation
```python
# Create multiple variants of the same strategy
manager.create_custom_strategy('sma_fast', SimpleMovingAverageStrategy, 
                               short_window=5, long_window=15)
manager.create_custom_strategy('sma_slow', SimpleMovingAverageStrategy, 
                               short_window=50, long_window=100)

# Use different variants
fast_signals = manager.generate_signals('sma_fast', df)
slow_signals = manager.generate_signals('sma_slow', df)
```

### Pattern 3: Strategy Comparison
```python
strategies = ['sma_crossover', 'sma_fast', 'sma_slow']
results = {}

for strategy_name in strategies:
    signals = manager.generate_signals(strategy_name, df)
    results[strategy_name] = {
        'signal_count': len(signals),
        'buy_signals': len([s for s in signals if s.action == Action.BUY]),
        'sell_signals': len([s for s in signals if s.action == Action.SELL])
    }
```

## Parameter Tuning Guidelines

### SMA Strategy Tuning
- **Faster signals**: Decrease both windows (e.g., 5, 15)
- **Slower signals**: Increase both windows (e.g., 50, 100)
- **More signals**: Decrease the gap between windows (e.g., 20, 25)
- **Fewer signals**: Increase the gap between windows (e.g., 10, 50)

### Option Strategy Tuning
- **More selective entries**: Lower `rsi_oversold` (e.g., 20)
- **More frequent entries**: Higher `rsi_oversold` (e.g., 40)
- **Conservative strikes**: Lower `strike_offset` (e.g., 0.02)
- **Aggressive strikes**: Higher `strike_offset` (e.g., 0.10)
- **More time value**: Higher `days_to_expiration` (e.g., 60)
- **Less time decay**: Lower `days_to_expiration` (e.g., 15)

## Error Handling

### Common Errors and Solutions
```python
# Error: Missing 'close' column
try:
    signals = manager.generate_signals('sma_crossover', df)
except ValueError as e:
    print(f"Data error: {e}")
    # Solution: Ensure df has 'close' column

# Error: Strategy not found
try:
    strategy = manager.get_strategy('nonexistent')
except ValueError as e:
    print(f"Strategy error: {e}")
    # Solution: Check available strategies with manager.list_strategies()

# Error: Invalid parameters
try:
    strategy = SimpleMovingAverageStrategy(short_window=50, long_window=20)  # Invalid: short > long
except Exception as e:
    print(f"Parameter error: {e}")
    # Solution: Ensure short_window < long_window
```