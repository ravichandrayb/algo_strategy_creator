from typing import List, Dict
import pandas as pd
from ...base_strategy import BaseStrategy
from ...signals import OptionSignal, Action, OptionType, CreditDebit


class ShortStraddleStrategy(BaseStrategy):
    """
    Short Straddle Strategy
    
    Volatility strategy that profits from low price movement. Sell ATM call and ATM put.
    Collects premium but has unlimited risk. Profits when stock stays near ATM strike.
    
    Parameters:
        iv_percentile_min (float): Minimum IV percentile to enter (default: 60)
        range_bound_period (int): Period to check for range-bound behavior (default: 20)
        atm_tolerance (float): Tolerance for ATM selection (default: 0.02)
        days_to_expiration (int): Days until option expiration (default: 30)
        min_credit (float): Minimum credit as percentage of stock price (default: 0.06)
    
    Required DataFrame columns:
        - close: Closing prices
        - high: High prices (for range calculation)
        - low: Low prices (for range calculation)
    
    Optional DataFrame attributes:
        - ticker: Stock ticker symbol
    """
    
    def __init__(self, iv_percentile_min: float = 60, range_bound_period: int = 20,
                 atm_tolerance: float = 0.02, days_to_expiration: int = 30, min_credit: float = 0.06):
        params = {
            "iv_percentile_min": iv_percentile_min,
            "range_bound_period": range_bound_period,
            "atm_tolerance": atm_tolerance,
            "days_to_expiration": days_to_expiration,
            "min_credit": min_credit
        }
        super().__init__(
            name="Short Straddle Strategy",
            params=params,
            is_option_trade=True
        )
    
    def _calculate_historical_volatility(self, prices: pd.Series, window: int = 20) -> pd.Series:
        returns = prices.pct_change()
        return returns.rolling(window=window).std() * (252 ** 0.5) * 100
    
    def generate_signals(self, df: pd.DataFrame) -> List[OptionSignal]:
        signals = []
        
        required_cols = ['close', 'high', 'low']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain columns: {required_cols}")
        
        df_copy = df.copy()
        iv_percentile_min = self.params["iv_percentile_min"]
        range_bound_period = self.params["range_bound_period"]
        atm_tolerance = self.params["atm_tolerance"]
        days_to_expiration = self.params["days_to_expiration"]
        min_credit = self.params["min_credit"]
        
        df_copy['hv'] = self._calculate_historical_volatility(df_copy['close'])
        df_copy['hv_percentile'] = df_copy['hv'].rolling(window=252).rank(pct=True) * 100
        
        # Calculate range-bound indicator
        df_copy['range_high'] = df_copy['high'].rolling(window=range_bound_period).max()
        df_copy['range_low'] = df_copy['low'].rolling(window=range_bound_period).min()
        df_copy['range_width'] = (df_copy['range_high'] - df_copy['range_low']) / df_copy['close']
        
        ticker = getattr(df, 'ticker', 'UNKNOWN')
        
        for idx, row in df_copy.iterrows():
            if pd.isna(row['hv_percentile']) or pd.isna(row['range_width']):
                continue
                
            # Enter when volatility is high but stock is range-bound
            if (row['hv_percentile'] > iv_percentile_min and 
                row['range_width'] < 0.15 and  # Stock in tight range
                row['close'] > (row['range_low'] + row['range_width'] * row['close'] * 0.3) and
                row['close'] < (row['range_high'] - row['range_width'] * row['close'] * 0.3)):
                
                current_price = row['close']
                
                # ATM strike
                atm_strike = round(current_price * 2) / 2
                
                # Check if current price is close enough to ATM
                if abs(current_price - atm_strike) / current_price <= atm_tolerance:
                    # Estimate straddle credit
                    call_credit = current_price * min_credit * 0.5
                    put_credit = current_price * min_credit * 0.5
                    total_credit = call_credit + put_credit
                    
                    # Only enter if credit is adequate
                    if total_credit >= current_price * min_credit:
                        from datetime import datetime, timedelta
                        expiration_date = (datetime.now() + timedelta(days=days_to_expiration)).strftime("%Y-%m-%d")
                        
                        signals.extend([
                            # Sell ATM call
                            OptionSignal(
                                ticker=ticker,
                                strike=round(atm_strike, 2),
                                option_type=OptionType.CALL,
                                price=call_credit,
                                action=Action.SELL,
                                expiration=expiration_date,
                                credit_debit=CreditDebit.CREDIT
                            ),
                            # Sell ATM put
                            OptionSignal(
                                ticker=ticker,
                                strike=round(atm_strike, 2),
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
            "iv_percentile_min": "Minimum IV percentile to enter (want high volatility)",
            "range_bound_period": "Period to check for range-bound price behavior",
            "atm_tolerance": "Maximum deviation from ATM for trade entry",
            "days_to_expiration": "Days until expiration (shorter favors seller)",
            "min_credit": "Minimum straddle credit as percentage of stock price"
        }
    
    def get_required_columns(self) -> List[str]:
        return ["close", "high", "low"]