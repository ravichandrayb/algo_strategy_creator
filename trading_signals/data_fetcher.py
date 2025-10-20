"""
Data Fetcher Utility for Kite Integration

This module provides functionality to fetch data using kite_utils package
and integrate it with the trading signals ranking system.
"""

from typing import Optional, Union
import pandas as pd
from datetime import datetime, timedelta
import warnings

try:
    from kite_utils import KiteDataFetcher, SimpleTokenManager
    KITE_AVAILABLE = True
except ImportError:
    KITE_AVAILABLE = False
    warnings.warn("kite_utils package not found. Data fetching from Kite will not be available.")


class DataFetcher:
    """
    Utility class to fetch market data using kite_utils package
    """
    
    def __init__(self, kite_data_fetcher=None, token_manager=None):
        """
        Initialize the data fetcher
        
        Args:
            kite_data_fetcher: Optional existing KiteDataFetcher instance
            token_manager: Optional existing SimpleTokenManager instance
        """
        if not KITE_AVAILABLE:
            raise ImportError("kite_utils package is required but not found. Please install it first.")
        
        if kite_data_fetcher:
            self.kite_fetcher = kite_data_fetcher
        else:
            # Try to create KiteDataFetcher with token manager
            try:
                if token_manager:
                    self.token_manager = token_manager
                else:
                    self.token_manager = SimpleTokenManager()
                
                if not self.token_manager.validate_token():
                    raise RuntimeError("Invalid or missing access token. Please run token generation first.")
                
                self.kite_fetcher = KiteDataFetcher()
            except Exception as e:
                raise RuntimeError(f"Failed to initialize KiteDataFetcher: {e}")
    
    def fetch_and_prepare_data(self, symbol: str, days: int = 365, 
                              interval: str = "day", from_date: Optional[str] = None, 
                              to_date: Optional[str] = None) -> pd.DataFrame:
        """
        Fetch historical data and prepare it for strategy analysis
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
            days: Number of days of historical data (default: 365)
            interval: Data interval ('day', 'minute', etc.) (default: 'day')
            from_date: Start date in 'YYYY-MM-DD' format (optional)
            to_date: End date in 'YYYY-MM-DD' format (optional)
            
        Returns:
            DataFrame prepared for strategy analysis with required columns and ticker attribute
        """
        # Calculate date range if not provided
        if not from_date or not to_date:
            if not to_date:
                to_date = datetime.now()
            else:
                # Convert string to datetime if needed
                if isinstance(to_date, str):
                    to_date = datetime.strptime(to_date, "%Y-%m-%d")
            
            if not from_date:
                from_date = datetime.now() - timedelta(days=days)
            else:
                # Convert string to datetime if needed
                if isinstance(from_date, str):
                    from_date = datetime.strptime(from_date, "%Y-%m-%d")
        
        # Fetch data using kite_utils
        df = self.kite_fetcher.fetch_historical_data(
            symbol=symbol,
            from_date=from_date,
            to_date=to_date,
            interval=interval
        )
        
        # Validate and prepare the DataFrame
        df = self._prepare_dataframe(df, symbol)
        
        return df
    
    def _prepare_dataframe(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Prepare DataFrame for strategy analysis
        
        Args:
            df: Raw DataFrame from kite_utils
            symbol: Stock symbol
            
        Returns:
            Prepared DataFrame with required columns and attributes
        """
        if df is None or df.empty:
            raise ValueError(f"No data retrieved for symbol: {symbol}")
        
        # Ensure required columns exist
        required_columns = ['close']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            # Try common column name variations
            column_mapping = {
                'Close': 'close',
                'CLOSE': 'close',
                'ltp': 'close',
                'LTP': 'close',
                'price': 'close',
                'High': 'high',
                'HIGH': 'high',
                'Low': 'low', 
                'LOW': 'low',
                'Open': 'open',
                'OPEN': 'open',
                'Volume': 'volume',
                'VOLUME': 'volume'
            }
            
            for old_name, new_name in column_mapping.items():
                if old_name in df.columns:
                    df = df.rename(columns={old_name: new_name})
        
        # Final check for required columns
        if 'close' not in df.columns:
            raise ValueError(f"Required 'close' column not found in data for {symbol}. "
                           f"Available columns: {list(df.columns)}")
        
        # Set ticker attribute (required by strategies)
        df.ticker = symbol
        
        # Ensure numeric data types
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Sort by date if date column exists
        date_columns = ['date', 'Date', 'timestamp', 'Timestamp', 'datetime']
        date_col = None
        for col in date_columns:
            if col in df.columns:
                date_col = col
                break
        
        if date_col:
            df = df.sort_values(date_col).reset_index(drop=True)
        
        # Remove any rows with NaN in close prices
        df = df.dropna(subset=['close'])
        
        if df.empty:
            raise ValueError(f"No valid price data found for symbol: {symbol}")
        
        return df
    
    def fetch_multiple_symbols(self, symbols: list, days: int = 365, 
                              interval: str = "day") -> dict:
        """
        Fetch data for multiple symbols
        
        Args:
            symbols: List of stock symbols
            days: Number of days of historical data
            interval: Data interval
            
        Returns:
            Dictionary with symbol as key and DataFrame as value
        """
        results = {}
        failed_symbols = []
        
        for symbol in symbols:
            try:
                df = self.fetch_and_prepare_data(symbol, days, interval)
                results[symbol] = df
                print(f"✓ Successfully fetched data for {symbol}: {len(df)} records")
            except Exception as e:
                failed_symbols.append(symbol)
                print(f"✗ Failed to fetch data for {symbol}: {e}")
        
        if failed_symbols:
            print(f"\nFailed symbols: {failed_symbols}")
        
        return results


def fetch_data_for_ranking(symbol: str, days: int = 365, 
                          kite_data_fetcher=None, token_manager=None) -> pd.DataFrame:
    """
    Convenience function to fetch data for strategy ranking
    
    Args:
        symbol: Stock symbol to fetch
        days: Number of days of historical data
        kite_data_fetcher: Optional existing KiteDataFetcher instance
        token_manager: Optional existing SimpleTokenManager instance
        
    Returns:
        DataFrame ready for strategy ranking
    """
    fetcher = DataFetcher(kite_data_fetcher, token_manager)
    return fetcher.fetch_and_prepare_data(symbol, days)


def rank_strategies_with_kite_data(symbol: str, days: int = 365, 
                                  top_n: int = 5, kite_data_fetcher=None, token_manager=None) -> list:
    """
    Fetch data from Kite and rank strategies in one step
    
    Args:
        symbol: Stock symbol to analyze
        days: Number of days of historical data
        top_n: Number of top strategies to return
        kite_data_fetcher: Optional existing KiteDataFetcher instance
        token_manager: Optional existing SimpleTokenManager instance
        
    Returns:
        List of tuples (strategy_name, score) for top strategies
    """
    from .strategy_ranker import rank_strategies_simple
    
    # Fetch data
    df = fetch_data_for_ranking(symbol, days, kite_data_fetcher, token_manager)
    
    # Rank strategies
    return rank_strategies_simple(df, top_n)


def analyze_symbol_with_kite(symbol: str, days: int = 365, 
                            kite_data_fetcher=None, token_manager=None, top_n: int = 10):
    """
    Complete analysis of a symbol using Kite data
    
    Args:
        symbol: Stock symbol to analyze
        days: Number of days of historical data
        kite_data_fetcher: Optional existing KiteDataFetcher instance
        token_manager: Optional existing SimpleTokenManager instance
        top_n: Number of strategies to show in report
    """
    from .strategy_ranker import StrategyRanker
    
    print(f"Fetching data for {symbol}...")
    df = fetch_data_for_ranking(symbol, days, kite_data_fetcher, token_manager)
    
    print(f"Data fetched: {len(df)} records")
    print(f"Date range: {df.index[0] if not df.empty else 'N/A'} to {df.index[-1] if not df.empty else 'N/A'}")
    print(f"Price range: ₹{df['close'].min():.2f} - ₹{df['close'].max():.2f}")
    
    # Analyze strategies
    ranker = StrategyRanker()
    ranker.print_ranking_report(df, top_n)
    
    return ranker.get_top_strategies(df, top_n)