from typing import List, Dict
import pandas as pd
from ...base_strategy import BaseStrategy
from ...signals import OptionSignal, Action, OptionType, CreditDebit


class IronCondorStrategy(BaseStrategy):
    """
    Iron Condor Strategy
    
    Neutral strategy that profits from low volatility. Sells both a call spread (above) and put spread (below).
    Maximum profit when stock stays between short strikes at expiration.
    
    Parameters:
        iv_percentile_max (float): Max implied volatility percentile to enter (default: 50)
        wing_width (float): Width of spreads as percentage of stock price (default: 0.05)
        short_delta (float): Target delta for short options (default: 0.16)
        days_to_expiration (int): Days until option expiration (default: 45)
        min_credit (float): Minimum credit as percentage of wing width (default: 0.30)
    
    Required DataFrame columns:
        - close: Closing prices
        - high: High prices (for volatility estimation)
        - low: Low prices (for volatility estimation)
    
    Optional DataFrame attributes:
        - ticker: Stock ticker symbol
    """
    
    def __init__(self, iv_percentile_max: float = 50, wing_width: float = 0.05,
                 short_delta: float = 0.16, days_to_expiration: int = 45, min_credit: float = 0.30):
        params = {
            "iv_percentile_max": iv_percentile_max,
            "wing_width": wing_width,
            "short_delta": short_delta,
            "days_to_expiration": days_to_expiration,
            "min_credit": min_credit
        }
        super().__init__(
            name="Iron Condor Strategy",
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
        wing_width = self.params["wing_width"]
        short_delta = self.params["short_delta"]
        days_to_expiration = self.params["days_to_expiration"]
        min_credit = self.params["min_credit"]
        
        # Calculate historical volatility as proxy for IV
        df_copy['hv'] = self._calculate_historical_volatility(df_copy['close'])
        df_copy['hv_percentile'] = df_copy['hv'].rolling(window=252).rank(pct=True) * 100
        
        ticker = getattr(df, 'ticker', 'UNKNOWN')
        
        for idx, row in df_copy.iterrows():
            if pd.isna(row['hv_percentile']):
                continue
                
            # Enter when IV is not too high (want to sell when IV is elevated but not extreme)
            if row['hv_percentile'] < iv_percentile_max and row['hv_percentile'] > 20:
                current_price = row['close']
                
                # Calculate strike prices
                wing_points = current_price * wing_width
                short_call_strike = current_price * (1 + short_delta * 0.1)
                long_call_strike = short_call_strike + wing_points
                short_put_strike = current_price * (1 - short_delta * 0.1)
                long_put_strike = short_put_strike - wing_points
                
                # Estimate credit (simplified)
                credit = wing_points * min_credit
                
                from datetime import datetime, timedelta
                expiration_date = (datetime.now() + timedelta(days=days_to_expiration)).strftime("%Y-%m-%d")
                
                # Short call spread (sell call, buy higher call)
                signals.extend([
                    OptionSignal(
                        ticker=ticker,
                        strike=round(short_call_strike, 2),
                        option_type=OptionType.CALL,
                        price=credit * 0.6,  # Allocation of total credit
                        action=Action.SELL,
                        expiration=expiration_date,
                        credit_debit=CreditDebit.CREDIT
                    ),
                    OptionSignal(
                        ticker=ticker,
                        strike=round(long_call_strike, 2),
                        option_type=OptionType.CALL,
                        price=credit * 0.3,
                        action=Action.BUY,
                        expiration=expiration_date,
                        credit_debit=CreditDebit.DEBIT
                    )
                ])
                
                # Short put spread (sell put, buy lower put)
                signals.extend([
                    OptionSignal(
                        ticker=ticker,
                        strike=round(short_put_strike, 2),
                        option_type=OptionType.PUT,
                        price=credit * 0.6,
                        action=Action.SELL,
                        expiration=expiration_date,
                        credit_debit=CreditDebit.CREDIT
                    ),
                    OptionSignal(
                        ticker=ticker,
                        strike=round(long_put_strike, 2),
                        option_type=OptionType.PUT,
                        price=credit * 0.3,
                        action=Action.BUY,
                        expiration=expiration_date,
                        credit_debit=CreditDebit.DEBIT
                    )
                ])
        
        return signals
    
    def get_param_descriptions(self) -> Dict[str, str]:
        return {
            "iv_percentile_max": "Maximum IV percentile to enter trade (prefer lower IV)",
            "wing_width": "Width of spreads as percentage of stock price",
            "short_delta": "Target delta for short options (0.10-0.25)",
            "days_to_expiration": "Days until option expiration (30-60 optimal)",
            "min_credit": "Minimum credit as percentage of wing width"
        }
    
    def get_required_columns(self) -> List[str]:
        return ["close", "high", "low"]