import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def generate_trending_stock_data(symbol="AAPL", days=252, start_price=150.0):
    """Generate trending upward stock data"""
    np.random.seed(42)
    dates = pd.date_range(start='2023-01-01', periods=days, freq='D')
    
    # Generate trending prices with some volatility
    trend = np.linspace(0, 0.3, days)  # 30% growth over period
    volatility = np.random.normal(0, 0.02, days)  # 2% daily volatility
    
    prices = start_price * np.exp(np.cumsum(trend/days + volatility))
    
    # Generate OHLC data
    high_factor = 1 + np.abs(np.random.normal(0, 0.01, days))
    low_factor = 1 - np.abs(np.random.normal(0, 0.01, days))
    
    df = pd.DataFrame({
        'date': dates,
        'open': prices * np.random.uniform(0.99, 1.01, days),
        'high': prices * high_factor,
        'low': prices * low_factor,
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, days)
    })
    
    df.ticker = symbol
    return df

def generate_sideways_stock_data(symbol="MSFT", days=252, base_price=280.0):
    """Generate sideways/ranging stock data"""
    np.random.seed(123)
    dates = pd.date_range(start='2023-01-01', periods=days, freq='D')
    
    # Generate sideways movement with noise
    noise = np.random.normal(0, 0.015, days)  # 1.5% daily volatility
    prices = base_price * (1 + np.cumsum(noise))
    
    # Add some mean reversion
    mean_price = np.mean(prices)
    prices = prices + 0.1 * (mean_price - prices)
    
    high_factor = 1 + np.abs(np.random.normal(0, 0.008, days))
    low_factor = 1 - np.abs(np.random.normal(0, 0.008, days))
    
    df = pd.DataFrame({
        'date': dates,
        'open': prices * np.random.uniform(0.995, 1.005, days),
        'high': prices * high_factor,
        'low': prices * low_factor,
        'close': prices,
        'volume': np.random.randint(2000000, 8000000, days)
    })
    
    df.ticker = symbol
    return df

def generate_volatile_stock_data(symbol="TSLA", days=252, start_price=200.0):
    """Generate highly volatile stock data with RSI signals"""
    np.random.seed(456)
    dates = pd.date_range(start='2023-01-01', periods=days, freq='D')
    
    # Generate high volatility data
    volatility = np.random.normal(0, 0.04, days)  # 4% daily volatility
    trend_changes = np.random.choice([-1, 1], days, p=[0.3, 0.7]) * 0.001
    
    price_changes = volatility + trend_changes
    prices = start_price * np.exp(np.cumsum(price_changes))
    
    high_factor = 1 + np.abs(np.random.normal(0, 0.02, days))
    low_factor = 1 - np.abs(np.random.normal(0, 0.02, days))
    
    df = pd.DataFrame({
        'date': dates,
        'open': prices * np.random.uniform(0.98, 1.02, days),
        'high': prices * high_factor,
        'low': prices * low_factor,
        'close': prices,
        'volume': np.random.randint(5000000, 20000000, days)
    })
    
    df.ticker = symbol
    return df

def generate_crypto_data(symbol="BTC", days=365, start_price=30000.0):
    """Generate crypto-like data with high volatility"""
    np.random.seed(789)
    dates = pd.date_range(start='2023-01-01', periods=days, freq='D')
    
    # Crypto-like volatility patterns
    volatility = np.random.normal(0, 0.06, days)  # 6% daily volatility
    momentum = np.random.choice([-1, 0, 1], days, p=[0.2, 0.6, 0.2]) * 0.002
    
    price_changes = volatility + momentum
    prices = start_price * np.exp(np.cumsum(price_changes))
    
    high_factor = 1 + np.abs(np.random.normal(0, 0.03, days))
    low_factor = 1 - np.abs(np.random.normal(0, 0.03, days))
    
    df = pd.DataFrame({
        'date': dates,
        'open': prices * np.random.uniform(0.95, 1.05, days),
        'high': prices * high_factor,
        'low': prices * low_factor,
        'close': prices,
        'volume': np.random.randint(100000, 1000000, days)
    })
    
    df.ticker = symbol
    return df

def main():
    """Generate all mock data files"""
    output_dir = "/Users/ravi/Documents/personal/Algo Startegy Signals/mockData"
    
    # Generate different types of market data
    datasets = [
        ("trending_stock.csv", generate_trending_stock_data("AAPL", 252, 150.0)),
        ("sideways_stock.csv", generate_sideways_stock_data("MSFT", 252, 280.0)),
        ("volatile_stock.csv", generate_volatile_stock_data("TSLA", 252, 200.0)),
        ("crypto_data.csv", generate_crypto_data("BTC", 365, 30000.0)),
        ("small_dataset.csv", generate_trending_stock_data("GOOGL", 50, 2500.0)),
        ("large_dataset.csv", generate_volatile_stock_data("SPY", 500, 400.0))
    ]
    
    for filename, df in datasets:
        filepath = os.path.join(output_dir, filename)
        df.to_csv(filepath, index=False)
        print(f"Generated {filename}: {len(df)} rows, ticker: {df.ticker}")
    
    print(f"\nAll mock data files saved to: {output_dir}")

if __name__ == "__main__":
    main()