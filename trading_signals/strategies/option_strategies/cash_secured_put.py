from typing import List, Dict
import pandas as pd
from ...base_strategy import BaseStrategy
from ...signals import OptionSignal, Action, OptionType, CreditDebit


class CashSecuredPutStrategy(BaseStrategy):
    """
    Cash Secured Put Strategy
    
    Sells put options when stock is oversold, securing cash to buy shares if assigned.
    Strategy for acquiring stocks at desired prices while collecting premium.
    
    Parameters:
        rsi_oversold (float): RSI threshold for oversold condition (default: 30)
        support_lookback (int): Days to look back for support level (default: 20)
        put_delta (float): Target delta for put options (default: 0.30)
        days_to_expiration (int): Days until option expiration (default: 30)
        min_premium (float): Minimum premium percentage to collect (default: 0.02)
    
    Required DataFrame columns:
        - close: Closing prices
        - low: Low prices (for support calculation)
    
    Optional DataFrame attributes:
        - ticker: Stock ticker symbol
    """
    
    def __init__(self, rsi_oversold: float = 30, support_lookback: int = 20,
                 put_delta: float = 0.30, days_to_expiration: int = 30, min_premium: float = 0.02):
        params = {
            "rsi_oversold": rsi_oversold,
            "support_lookback": support_lookback,
            "put_delta": put_delta,
            "days_to_expiration": days_to_expiration,
            "min_premium": min_premium
        }
        super().__init__(
            name="Cash Secured Put Strategy",
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
        
        if 'close' not in df.columns or 'low' not in df.columns:
            raise ValueError("DataFrame must contain 'close' and 'low' columns")
        
        df_copy = df.copy()
        rsi_oversold = self.params["rsi_oversold"]
        support_lookback = self.params["support_lookback"]
        put_delta = self.params["put_delta"]
        days_to_expiration = self.params["days_to_expiration"]
        min_premium = self.params["min_premium"]
        
        df_copy['rsi'] = self._calculate_rsi(df_copy['close'])
        df_copy['support'] = df_copy['low'].rolling(window=support_lookback).min()
        
        ticker = getattr(df, 'ticker', 'UNKNOWN')
        
        for idx, row in df_copy.iterrows():
            if pd.isna(row['rsi']) or pd.isna(row['support']):
                continue
                
            # Signal when RSI is oversold and price is near support
            if row['rsi'] < rsi_oversold and row['close'] <= row['support'] * 1.05:
                current_price = row['close']
                
                # Strike price based on support and delta
                strike_price = max(row['support'], current_price * (1 - put_delta * 0.1))
                
                # Estimate premium
                premium = current_price * min_premium
                
                from datetime import datetime, timedelta
                expiration_date = (datetime.now() + timedelta(days=days_to_expiration)).strftime("%Y-%m-%d")
                
                signals.append(OptionSignal(
                    ticker=ticker,
                    strike=round(strike_price, 2),
                    option_type=OptionType.PUT,
                    price=premium,
                    action=Action.SELL,
                    expiration=expiration_date,
                    credit_debit=CreditDebit.CREDIT
                ))
        
        return signals
    
    def get_param_descriptions(self) -> Dict[str, str]:
        return {
            "rsi_oversold": "RSI threshold below which stock is considered oversold",
            "support_lookback": "Number of days to look back for support level calculation",
            "put_delta": "Target delta for put options (0.1-0.5, lower = more OTM)",
            "days_to_expiration": "Number of days until option expiration",
            "min_premium": "Minimum premium percentage to collect (0.01 = 1%)"
        }
    
    def get_required_columns(self) -> List[str]:
        return ["close", "low"]