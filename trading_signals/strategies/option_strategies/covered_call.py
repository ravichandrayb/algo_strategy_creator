from typing import List, Dict
import pandas as pd
from ...base_strategy import BaseStrategy
from ...signals import OptionSignal, Action, OptionType, CreditDebit


class CoveredCallStrategy(BaseStrategy):
    """
    Covered Call Strategy
    
    Sells call options against existing stock positions when price is above resistance.
    This is a conservative income-generating strategy.
    
    Parameters:
        resistance_lookback (int): Days to look back for resistance level (default: 20)
        call_delta (float): Target delta for call options (default: 0.30)
        days_to_expiration (int): Days until option expiration (default: 30)
        min_premium (float): Minimum premium percentage to collect (default: 0.02)
    
    Required DataFrame columns:
        - close: Closing prices
        - high: High prices (for resistance calculation)
    
    Optional DataFrame attributes:
        - ticker: Stock ticker symbol
    """
    
    def __init__(self, resistance_lookback: int = 20, call_delta: float = 0.30, 
                 days_to_expiration: int = 30, min_premium: float = 0.02):
        params = {
            "resistance_lookback": resistance_lookback,
            "call_delta": call_delta,
            "days_to_expiration": days_to_expiration,
            "min_premium": min_premium
        }
        super().__init__(
            name="Covered Call Strategy",
            params=params,
            is_option_trade=True
        )
    
    def generate_signals(self, df: pd.DataFrame) -> List[OptionSignal]:
        signals = []
        
        # Normalize column names to lowercase
        df = self.normalize_dataframe(df)
        
        if 'close' not in df.columns or 'high' not in df.columns:
            raise ValueError("DataFrame must contain 'close' and 'high' columns")
        
        df_copy = df.copy()
        resistance_lookback = self.params["resistance_lookback"]
        call_delta = self.params["call_delta"]
        days_to_expiration = self.params["days_to_expiration"]
        min_premium = self.params["min_premium"]
        
        # Calculate resistance levels
        df_copy['resistance'] = df_copy['high'].rolling(window=resistance_lookback).max()
        
        ticker = getattr(df, 'ticker', 'UNKNOWN')
        
        for idx, row in df_copy.iterrows():
            if pd.isna(row['resistance']):
                continue
                
            # Signal when price is near or above resistance
            if row['close'] >= row['resistance'] * 0.98:  # Within 2% of resistance
                current_price = row['close']
                
                # Estimate strike price based on delta (simplified)
                strike_price = current_price * (1 + call_delta * 0.1)
                
                # Estimate premium (simplified model)
                premium = current_price * min_premium
                
                from datetime import datetime, timedelta
                expiration_date = (datetime.now() + timedelta(days=days_to_expiration)).strftime("%Y-%m-%d")
                
                signals.append(OptionSignal(
                    ticker=ticker,
                    strike=round(strike_price, 2),
                    option_type=OptionType.CALL,
                    price=premium,
                    action=Action.SELL,
                    expiration=expiration_date,
                    credit_debit=CreditDebit.CREDIT
                ))
        
        return signals
    
    def get_param_descriptions(self) -> Dict[str, str]:
        return {
            "resistance_lookback": "Number of days to look back for resistance level calculation",
            "call_delta": "Target delta for call options (0.1-0.5, lower = more OTM)",
            "days_to_expiration": "Number of days until option expiration",
            "min_premium": "Minimum premium percentage to collect (0.01 = 1%)"
        }
    
    def get_required_columns(self) -> List[str]:
        return ["close", "high"]