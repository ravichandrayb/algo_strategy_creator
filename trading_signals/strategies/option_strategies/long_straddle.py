from typing import List, Dict
import pandas as pd
from ...base_strategy import BaseStrategy
from ...signals import OptionSignal, Action, OptionType, CreditDebit


class LongStraddleStrategy(BaseStrategy):
    """
    Long Straddle Strategy
    
    Volatility strategy that profits from large price movements in either direction.
    Buy ATM call and ATM put with same expiration. Profits when stock moves significantly.
    
    Parameters:
        iv_percentile_max (float): Maximum IV percentile to enter (default: 40)
        volatility_contraction_period (int): Period to check for low volatility (default: 20)
        atm_tolerance (float): Tolerance for ATM selection (default: 0.02)
        days_to_expiration (int): Days until option expiration (default: 30)
        max_cost (float): Maximum cost as percentage of stock price (default: 0.08)
    
    Required DataFrame columns:
        - close: Closing prices
        - high: High prices (for volatility calculation)
        - low: Low prices (for volatility calculation)
    
    Optional DataFrame attributes:
        - ticker: Stock ticker symbol
    """
    
    def __init__(self, iv_percentile_max: float = 40, volatility_contraction_period: int = 20,
                 atm_tolerance: float = 0.02, days_to_expiration: int = 30, max_cost: float = 0.08):
        params = {
            "iv_percentile_max": iv_percentile_max,
            "volatility_contraction_period": volatility_contraction_period,
            "atm_tolerance": atm_tolerance,
            "days_to_expiration": days_to_expiration,
            "max_cost": max_cost
        }
        super().__init__(
            name="Long Straddle Strategy",
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
        iv_percentile_max = self.params["iv_percentile_max"]
        vol_contraction_period = self.params["volatility_contraction_period"]
        atm_tolerance = self.params["atm_tolerance"]
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
                row['hv'] <= row['hv_avg']):  # Current vol below recent average
                
                current_price = row['close']
                
                # ATM strike (round to nearest option strike)
                atm_strike = round(current_price * 2) / 2  # $0.50 strike intervals
                
                # Check if current price is close enough to ATM
                if abs(current_price - atm_strike) / current_price <= atm_tolerance:
                    # Estimate straddle cost
                    call_cost = current_price * max_cost * 0.5
                    put_cost = current_price * max_cost * 0.5
                    total_cost = call_cost + put_cost
                    
                    # Only enter if cost is reasonable
                    if total_cost <= current_price * max_cost:
                        from datetime import datetime, timedelta
                        expiration_date = (datetime.now() + timedelta(days=days_to_expiration)).strftime("%Y-%m-%d")
                        
                        signals.extend([
                            # Buy ATM call
                            OptionSignal(
                                ticker=ticker,
                                strike=round(atm_strike, 2),
                                option_type=OptionType.CALL,
                                price=call_cost,
                                action=Action.BUY,
                                expiration=expiration_date,
                                credit_debit=CreditDebit.DEBIT
                            ),
                            # Buy ATM put
                            OptionSignal(
                                ticker=ticker,
                                strike=round(atm_strike, 2),
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
            "volatility_contraction_period": "Period to check for volatility contraction",
            "atm_tolerance": "Maximum deviation from ATM for trade entry",
            "days_to_expiration": "Days until expiration (30-60 for volatility plays)",
            "max_cost": "Maximum straddle cost as percentage of stock price"
        }
    
    def get_required_columns(self) -> List[str]:
        return ["close", "high", "low"]