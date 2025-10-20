from typing import List, Dict
import pandas as pd
import sys
import os

try:
    from ..base_strategy import BaseStrategy
    from ..signals import StockSignal, Action
except ImportError:
    # Add parent directory to path for direct execution
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    try:
        from trading_signals.base_strategy import BaseStrategy
        from trading_signals.signals import StockSignal, Action
    except ImportError:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from base_strategy import BaseStrategy
        from signals import StockSignal, Action


class SimpleMovingAverageStrategy(BaseStrategy):
    """
    Simple Moving Average Crossover Strategy
    
    Generates BUY signals when short MA crosses above long MA
    Generates SELL signals when short MA crosses below long MA
    
    Parameters:
        short_window (int): Period for short moving average (default: 20)
        long_window (int): Period for long moving average (default: 50)
    
    Required DataFrame columns:
        - close: Closing prices
    
    Optional DataFrame attributes:
        - ticker: Stock ticker symbol (will use 'UNKNOWN' if not set)
    """
    
    def __init__(self, short_window: int = 20, long_window: int = 50):
        params = {
            "short_window": short_window,
            "long_window": long_window
        }
        super().__init__(
            name="Simple Moving Average Crossover",
            params=params,
            is_option_trade=False
        )
    
    def generate_signals(self, df: pd.DataFrame) -> List[StockSignal]:
        signals = []
        
        if 'close' not in df.columns:
            raise ValueError("DataFrame must contain 'close' column")
        
        short_window = self.params["short_window"]
        long_window = self.params["long_window"]
        
        df_copy = df.copy()
        df_copy['short_ma'] = df_copy['close'].rolling(window=short_window).mean()
        df_copy['long_ma'] = df_copy['close'].rolling(window=long_window).mean()
        
        df_copy['signal'] = 0
        df_copy.loc[df_copy['short_ma'] > df_copy['long_ma'], 'signal'] = 1
        df_copy.loc[df_copy['short_ma'] <= df_copy['long_ma'], 'signal'] = -1
        
        df_copy['position'] = df_copy['signal'].diff()
        
        ticker = getattr(df, 'ticker', 'UNKNOWN')
        
        for idx, row in df_copy.iterrows():
            if row['position'] == 2:
                signals.append(StockSignal(
                    ticker=ticker,
                    price=row['close'],
                    action=Action.BUY
                ))
            elif row['position'] == -2:
                signals.append(StockSignal(
                    ticker=ticker,
                    price=row['close'],
                    action=Action.SELL
                ))
        
        return signals
    
    def get_param_descriptions(self) -> Dict[str, str]:
        return {
            "short_window": "Period for short-term moving average (smaller number = more sensitive)",
            "long_window": "Period for long-term moving average (larger number = less sensitive)"
        }
    
    def get_required_columns(self) -> List[str]:
        return ["close"]