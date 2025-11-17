from typing import List, Dict
import pandas as pd
from ...base_strategy import BaseStrategy
from ...signals import OptionSignal, Action, OptionType, CreditDebit


class ShortStrangleStrategy(BaseStrategy):
    """
    Short Strangle Strategy
    
    Volatility strategy that sells OTM call and OTM put. Collects premium and profits
    when stock stays between the strikes. Lower credit but safer than short straddle.
    
    Parameters:
        iv_percentile_min (float): Minimum IV percentile to enter (default: 50)
        call_delta (float): Target delta for call option (default: 0.20)
        put_delta (float): Target delta for put option (default: 0.20)
        range_bound_period (int): Period to check for range-bound behavior (default: 20)
        days_to_expiration (int): Days until option expiration (default: 45)
        min_credit (float): Minimum credit as percentage of stock price (default: 0.04)
    
    Required DataFrame columns:
        - close: Closing prices
        - high: High prices (for range calculation)
        - low: Low prices (for range calculation)
    
    Optional DataFrame attributes:
        - ticker: Stock ticker symbol
    """
    
    def __init__(self, iv_percentile_min: float = 50, call_delta: float = 0.20, put_delta: float = 0.20,
                 range_bound_period: int = 20, days_to_expiration: int = 45, min_credit: float = 0.04):
        params = {
            "iv_percentile_min": iv_percentile_min,
            "call_delta": call_delta,
            "put_delta": put_delta,
            "range_bound_period": range_bound_period,
            "days_to_expiration": days_to_expiration,
            "min_credit": min_credit
        }
        super().__init__(
            name="Short Strangle Strategy",
            params=params,
            is_option_trade=True
        )
    
    def _calculate_historical_volatility(self, prices: pd.Series, window: int = 20) -> pd.Series:
        returns = prices.pct_change()
        return returns.rolling(window=window).std() * (252 ** 0.5) * 100
    
    def generate_signals(self, df: pd.DataFrame) -> List[OptionSignal]:
        signals = []
        
        # Normalize column names to lowercase
        df = self.normalize_dataframe(df)
        
        required_cols = ['close', 'high', 'low']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain columns: {required_cols}")
        
        df_copy = df.copy()
        iv_percentile_min = self.params["iv_percentile_min"]
        call_delta = self.params["call_delta"]
        put_delta = self.params["put_delta"]
        range_bound_period = self.params["range_bound_period"]
        days_to_expiration = self.params["days_to_expiration"]
        min_credit = self.params["min_credit"]
        
        df_copy['hv'] = self._calculate_historical_volatility(df_copy['close'])
        df_copy['hv_percentile'] = df_copy['hv'].rolling(window=252).rank(pct=True) * 100
        
        # Range-bound indicators
        df_copy['range_high'] = df_copy['high'].rolling(window=range_bound_period).max()
        df_copy['range_low'] = df_copy['low'].rolling(window=range_bound_period).min()
        df_copy['range_width'] = (df_copy['range_high'] - df_copy['range_low']) / df_copy['close']
        df_copy['price_position'] = (df_copy['close'] - df_copy['range_low']) / (df_copy['range_high'] - df_copy['range_low'])
        
        ticker = getattr(df, 'ticker', 'UNKNOWN')
        
        for idx, row in df_copy.iterrows():
            if pd.isna(row['hv_percentile']) or pd.isna(row['range_width']):
                continue
                
            # Enter when IV is elevated and stock is range-bound and centered
            if (row['hv_percentile'] > iv_percentile_min and 
                row['range_width'] < 0.20 and  # Reasonable range
                0.3 < row['price_position'] < 0.7):  # Price in middle of range
                
                current_price = row['close']
                
                # Calculate OTM strikes
                call_strike = current_price * (1 + call_delta * 0.15)
                put_strike = current_price * (1 - put_delta * 0.15)
                
                # Estimate credits
                call_credit = current_price * min_credit * 0.5
                put_credit = current_price * min_credit * 0.5
                total_credit = call_credit + put_credit
                
                # Only enter if credit is adequate
                if total_credit >= current_price * min_credit:
                    from datetime import datetime, timedelta
                    expiration_date = (datetime.now() + timedelta(days=days_to_expiration)).strftime("%Y-%m-%d")
                    
                    signals.extend([
                        # Sell OTM call
                        OptionSignal(
                            ticker=ticker,
                            strike=round(call_strike, 2),
                            option_type=OptionType.CALL,
                            price=call_credit,
                            action=Action.SELL,
                            expiration=expiration_date,
                            credit_debit=CreditDebit.CREDIT
                        ),
                        # Sell OTM put
                        OptionSignal(
                            ticker=ticker,
                            strike=round(put_strike, 2),
                            option_type=OptionType.PUT,
                            price=put_credit,
                            action=Action.SELL,
                            expiration=expiration_date,
                            credit_debit=CreditDebit.CREDIT
                        )
                    ])
        
        return signals
    
    def get_param_descriptions(self) -> Dict[str, str]:
        return {
            "iv_percentile_min": "Minimum IV percentile to enter (want elevated IV)",
            "call_delta": "Target delta for call option (0.15-0.30)",
            "put_delta": "Target delta for put option (0.15-0.30)",
            "range_bound_period": "Period to check for range-bound behavior",
            "days_to_expiration": "Days until expiration (30-60 optimal)",
            "min_credit": "Minimum strangle credit as percentage of stock price"
        }
    
    def get_required_columns(self) -> List[str]:
        return ["close", "high", "low"]