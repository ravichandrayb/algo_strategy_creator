from typing import List, Dict
import pandas as pd
from ...base_strategy import BaseStrategy
from ...signals import OptionSignal, Action, OptionType, CreditDebit


class IronButterflyStrategy(BaseStrategy):
    """
    Iron Butterfly Strategy
    
    Neutral strategy with short straddle at ATM and long strangle for protection.
    Profits when stock stays very close to ATM strike at expiration.
    
    Parameters:
        atm_tolerance (float): Tolerance for ATM selection (default: 0.02)
        wing_width (float): Distance from ATM to long strikes (default: 0.05)
        iv_percentile_min (float): Minimum IV percentile to enter (default: 30)
        days_to_expiration (int): Days until option expiration (default: 30)
        min_credit (float): Minimum credit as percentage of wing width (default: 0.40)
    
    Required DataFrame columns:
        - close: Closing prices
        - high: High prices (for volatility calculation)
        - low: Low prices (for volatility calculation)
    
    Optional DataFrame attributes:
        - ticker: Stock ticker symbol
    """
    
    def __init__(self, atm_tolerance: float = 0.02, wing_width: float = 0.05,
                 iv_percentile_min: float = 30, days_to_expiration: int = 30, min_credit: float = 0.40):
        params = {
            "atm_tolerance": atm_tolerance,
            "wing_width": wing_width,
            "iv_percentile_min": iv_percentile_min,
            "days_to_expiration": days_to_expiration,
            "min_credit": min_credit
        }
        super().__init__(
            name="Iron Butterfly Strategy",
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
        atm_tolerance = self.params["atm_tolerance"]
        wing_width = self.params["wing_width"]
        iv_percentile_min = self.params["iv_percentile_min"]
        days_to_expiration = self.params["days_to_expiration"]
        min_credit = self.params["min_credit"]
        
        df_copy['hv'] = self._calculate_historical_volatility(df_copy['close'])
        df_copy['hv_percentile'] = df_copy['hv'].rolling(window=252).rank(pct=True) * 100
        
        ticker = getattr(df, 'ticker', 'UNKNOWN')
        
        for idx, row in df_copy.iterrows():
            if pd.isna(row['hv_percentile']):
                continue
                
            # Enter when IV is elevated
            if row['hv_percentile'] > iv_percentile_min:
                current_price = row['close']
                
                # ATM strike (round to nearest option strike)
                atm_strike = round(current_price * 2) / 2  # Assuming $0.50 strike intervals
                
                # Check if current price is close enough to ATM
                if abs(current_price - atm_strike) / current_price <= atm_tolerance:
                    # Wing strikes
                    wing_points = current_price * wing_width
                    upper_wing = atm_strike + wing_points
                    lower_wing = atm_strike - wing_points
                    
                    # Estimate credit
                    credit = wing_points * min_credit
                    
                    from datetime import datetime, timedelta
                    expiration_date = (datetime.now() + timedelta(days=days_to_expiration)).strftime("%Y-%m-%d")
                    
                    # Iron Butterfly components:
                    # 1. Sell ATM Call and Put (short straddle)
                    # 2. Buy OTM Call and Put (long strangle protection)
                    
                    signals.extend([
                        # Short ATM straddle
                        OptionSignal(
                            ticker=ticker,
                            strike=round(atm_strike, 2),
                            option_type=OptionType.CALL,
                            price=credit * 0.5,
                            action=Action.SELL,
                            expiration=expiration_date,
                            credit_debit=CreditDebit.CREDIT
                        ),
                        OptionSignal(
                            ticker=ticker,
                            strike=round(atm_strike, 2),
                            option_type=OptionType.PUT,
                            price=credit * 0.5,
                            action=Action.SELL,
                            expiration=expiration_date,
                            credit_debit=CreditDebit.CREDIT
                        ),
                        # Long protection wings
                        OptionSignal(
                            ticker=ticker,
                            strike=round(upper_wing, 2),
                            option_type=OptionType.CALL,
                            price=credit * 0.25,
                            action=Action.BUY,
                            expiration=expiration_date,
                            credit_debit=CreditDebit.DEBIT
                        ),
                        OptionSignal(
                            ticker=ticker,
                            strike=round(lower_wing, 2),
                            option_type=OptionType.PUT,
                            price=credit * 0.25,
                            action=Action.BUY,
                            expiration=expiration_date,
                            credit_debit=CreditDebit.DEBIT
                        )
                    ])
        
        return signals
    
    def get_param_descriptions(self) -> Dict[str, str]:
        return {
            "atm_tolerance": "Maximum deviation from ATM for trade entry (0.01 = 1%)",
            "wing_width": "Distance from ATM to protective wings as % of price",
            "iv_percentile_min": "Minimum IV percentile to enter (want elevated IV)",
            "days_to_expiration": "Days until expiration (shorter favors time decay)",
            "min_credit": "Minimum credit as percentage of wing width"
        }
    
    def get_required_columns(self) -> List[str]:
        return ["close", "high", "low"]