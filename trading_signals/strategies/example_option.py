from typing import List, Dict
import pandas as pd
import sys
import os

try:
    from ..base_strategy import BaseStrategy
    from ..signals import OptionSignal, Action, OptionType, CreditDebit
except ImportError:
    # Add parent directory to path for direct execution
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    try:
        from trading_signals.base_strategy import BaseStrategy
        from trading_signals.signals import OptionSignal, Action, OptionType, CreditDebit
    except ImportError:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from base_strategy import BaseStrategy
        from signals import OptionSignal, Action, OptionType, CreditDebit


class SimplePutCreditSpreadStrategy(BaseStrategy):
    """
    Simple Put Credit Spread Strategy
    
    Generates SELL PUT signals when RSI indicates oversold conditions.
    This is a credit strategy (collect premium upfront).
    
    Parameters:
        rsi_oversold (float): RSI threshold for oversold condition (default: 30)
        strike_offset (float): Strike price offset below current price (default: 0.05 = 5%)
        days_to_expiration (int): Days until option expiration (default: 30)
    
    Required DataFrame columns:
        - close: Closing prices
    
    Optional DataFrame attributes:
        - ticker: Stock ticker symbol (will use 'UNKNOWN' if not set)
    """
    
    def __init__(self, rsi_oversold: float = 30, strike_offset: float = 0.05, days_to_expiration: int = 30):
        params = {
            "rsi_oversold": rsi_oversold,
            "strike_offset": strike_offset,
            "days_to_expiration": days_to_expiration
        }
        super().__init__(
            name="Simple Put Credit Spread",
            params=params,
            is_option_trade=True
        )
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def generate_signals(self, df: pd.DataFrame) -> List[OptionSignal]:
        signals = []
        
        if 'close' not in df.columns:
            raise ValueError("DataFrame must contain 'close' column")
        
        df_copy = df.copy()
        df_copy['rsi'] = self._calculate_rsi(df_copy['close'])
        
        rsi_oversold = self.params["rsi_oversold"]
        strike_offset = self.params["strike_offset"]
        days_to_expiration = self.params["days_to_expiration"]
        
        ticker = getattr(df, 'ticker', 'UNKNOWN')
        
        for idx, row in df_copy.iterrows():
            if row['rsi'] < rsi_oversold:
                current_price = row['close']
                strike_price = current_price * (1 - strike_offset)
                
                from datetime import datetime, timedelta
                expiration_date = (datetime.now() + timedelta(days=days_to_expiration)).strftime("%Y-%m-%d")
                
                signals.append(OptionSignal(
                    ticker=ticker,
                    strike=round(strike_price, 2),
                    option_type=OptionType.PUT,
                    price=current_price * 0.02,
                    action=Action.SELL,
                    expiration=expiration_date,
                    credit_debit=CreditDebit.CREDIT
                ))
        
        return signals
    
    def get_param_descriptions(self) -> Dict[str, str]:
        return {
            "rsi_oversold": "RSI threshold below which stock is considered oversold (0-100, typical: 20-30)",
            "strike_offset": "Percentage below current price to set put strike (0.01 = 1%, 0.05 = 5%)",
            "days_to_expiration": "Number of days until option expiration (typical: 30-60 days)"
        }
    
    def get_required_columns(self) -> List[str]:
        return ["close"]