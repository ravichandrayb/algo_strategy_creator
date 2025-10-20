from typing import List, Dict
import pandas as pd
from ...base_strategy import BaseStrategy
from ...signals import OptionSignal, Action, OptionType, CreditDebit


class LongStrangleStrategy(BaseStrategy):
    """
    Long Strangle Strategy
    
    Volatility strategy similar to straddle but with OTM options. Buy OTM call and OTM put.
    Lower cost than straddle but requires larger move to profit.
    
    Parameters:
        iv_percentile_max (float): Maximum IV percentile to enter (default: 40)
        call_delta (float): Target delta for call option (default: 0.25)
        put_delta (float): Target delta for put option (default: 0.25)
        volatility_contraction_period (int): Period to check for low volatility (default: 20)
        days_to_expiration (int): Days until option expiration (default: 30)
        max_cost (float): Maximum cost as percentage of stock price (default: 0.06)
    
    Required DataFrame columns:
        - close: Closing prices
        - high: High prices (for volatility calculation)
        - low: Low prices (for volatility calculation)
    
    Optional DataFrame attributes:
        - ticker: Stock ticker symbol
    """
    
    def __init__(self, iv_percentile_max: float = 40, call_delta: float = 0.25, put_delta: float = 0.25,
                 volatility_contraction_period: int = 20, days_to_expiration: int = 30, max_cost: float = 0.06):
        params = {
            "iv_percentile_max": iv_percentile_max,
            "call_delta": call_delta,
            "put_delta": put_delta,
            "volatility_contraction_period": volatility_contraction_period,
            "days_to_expiration": days_to_expiration,
            "max_cost": max_cost
        }
        super().__init__(
            name="Long Strangle Strategy",
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
        iv_percentile_max = self.params["iv_percentile_max"]
        call_delta = self.params["call_delta"]
        put_delta = self.params["put_delta"]
        vol_contraction_period = self.params["volatility_contraction_period"]
        days_to_expiration = self.params["days_to_expiration"]
        max_cost = self.params["max_cost"]
        
        df_copy['hv'] = self._calculate_historical_volatility(df_copy['close'])
        df_copy['hv_percentile'] = df_copy['hv'].rolling(window=252).rank(pct=True) * 100
        df_copy['hv_avg'] = df_copy['hv'].rolling(window=vol_contraction_period).mean()
        
        ticker = getattr(df, 'ticker', 'UNKNOWN')
        
        for idx, row in df_copy.iterrows():
            if pd.isna(row['hv_percentile']) or pd.isna(row['hv_avg']):
                continue
                
            # Enter when volatility is low (expecting expansion)
            if (row['hv_percentile'] < iv_percentile_max and 
                row['hv'] <= row['hv_avg']):
                
                current_price = row['close']
                
                # Calculate OTM strikes
                call_strike = current_price * (1 + call_delta * 0.15)  # OTM call
                put_strike = current_price * (1 - put_delta * 0.15)    # OTM put
                
                # Estimate costs (OTM options cheaper than ATM)
                call_cost = current_price * max_cost * 0.4
                put_cost = current_price * max_cost * 0.4
                total_cost = call_cost + put_cost
                
                # Only enter if cost is reasonable
                if total_cost <= current_price * max_cost:
                    from datetime import datetime, timedelta
                    expiration_date = (datetime.now() + timedelta(days=days_to_expiration)).strftime("%Y-%m-%d")
                    
                    signals.extend([
                        # Buy OTM call
                        OptionSignal(
                            ticker=ticker,
                            strike=round(call_strike, 2),
                            option_type=OptionType.CALL,
                            price=call_cost,
                            action=Action.BUY,
                            expiration=expiration_date,
                            credit_debit=CreditDebit.DEBIT
                        ),
                        # Buy OTM put
                        OptionSignal(
                            ticker=ticker,
                            strike=round(put_strike, 2),
                            option_type=OptionType.PUT,
                            price=put_cost,
                            action=Action.BUY,
                            expiration=expiration_date,
                            credit_debit=CreditDebit.DEBIT
                        )
                    ])
        
        return signals
    
    def get_param_descriptions(self) -> Dict[str, str]:
        return {
            "iv_percentile_max": "Maximum IV percentile to enter (want low volatility)",
            "call_delta": "Target delta for call option (0.15-0.35)",
            "put_delta": "Target delta for put option (0.15-0.35)",
            "volatility_contraction_period": "Period to check for volatility contraction",
            "days_to_expiration": "Days until expiration (30-60 for volatility)",
            "max_cost": "Maximum strangle cost as percentage of stock price"
        }
    
    def get_required_columns(self) -> List[str]:
        return ["close", "high", "low"]