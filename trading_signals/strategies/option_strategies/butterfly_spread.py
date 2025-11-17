from typing import List, Dict
import pandas as pd
from ...base_strategy import BaseStrategy
from ...signals import OptionSignal, Action, OptionType, CreditDebit


class ButterflySpreadStrategy(BaseStrategy):
    """
    Butterfly Spread Strategy
    
    Neutral strategy that profits when stock stays near the middle strike.
    Long 2 options at middle strike, short 1 option above and 1 below.
    
    Parameters:
        wing_width (float): Distance from center to wings as % of price (default: 0.05)
        atm_tolerance (float): Tolerance for ATM center selection (default: 0.02)
        iv_percentile_min (float): Minimum IV percentile for entry (default: 40)
        days_to_expiration (int): Days until option expiration (default: 30)
        max_cost (float): Maximum debit as % of wing width (default: 0.70)
        range_bound_period (int): Period to check for range behavior (default: 20)
    
    Required DataFrame columns:
        - close: Closing prices
        - high: High prices (for range analysis)
        - low: Low prices (for range analysis)
    
    Optional DataFrame attributes:
        - ticker: Stock ticker symbol
    """
    
    def __init__(self, wing_width: float = 0.05, atm_tolerance: float = 0.02,
                 iv_percentile_min: float = 40, days_to_expiration: int = 30,
                 max_cost: float = 0.70, range_bound_period: int = 20):
        params = {
            "wing_width": wing_width,
            "atm_tolerance": atm_tolerance,
            "iv_percentile_min": iv_percentile_min,
            "days_to_expiration": days_to_expiration,
            "max_cost": max_cost,
            "range_bound_period": range_bound_period
        }
        super().__init__(
            name="Butterfly Spread Strategy",
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
        wing_width = self.params["wing_width"]
        atm_tolerance = self.params["atm_tolerance"]
        iv_percentile_min = self.params["iv_percentile_min"]
        days_to_expiration = self.params["days_to_expiration"]
        max_cost = self.params["max_cost"]
        range_period = self.params["range_bound_period"]
        
        df_copy['hv'] = self._calculate_historical_volatility(df_copy['close'])
        df_copy['hv_percentile'] = df_copy['hv'].rolling(window=252).rank(pct=True) * 100
        
        # Range analysis
        df_copy['range_high'] = df_copy['high'].rolling(window=range_period).max()
        df_copy['range_low'] = df_copy['low'].rolling(window=range_period).min()
        df_copy['range_center'] = (df_copy['range_high'] + df_copy['range_low']) / 2
        df_copy['price_to_center'] = abs(df_copy['close'] - df_copy['range_center']) / df_copy['close']
        
        ticker = getattr(df, 'ticker', 'UNKNOWN')
        
        for idx, row in df_copy.iterrows():
            if pd.isna(row['hv_percentile']) or pd.isna(row['price_to_center']):
                continue
                
            # Enter when IV is decent and price is near range center
            if (row['hv_percentile'] > iv_percentile_min and 
                row['price_to_center'] < atm_tolerance):
                
                current_price = row['close']
                wing_points = current_price * wing_width
                
                # Strike selection
                center_strike = round(current_price * 2) / 2  # ATM
                lower_wing = center_strike - wing_points
                upper_wing = center_strike + wing_points
                
                # Check ATM tolerance
                if abs(current_price - center_strike) / current_price <= atm_tolerance:
                    # Estimate costs (butterfly typically a debit)
                    wing_cost = wing_points * 0.3      # Cost of wings
                    center_credit = wing_points * 0.5  # Credit from center
                    net_debit = wing_cost - center_credit
                    
                    # Only enter if cost is reasonable
                    if net_debit <= wing_points * max_cost:
                        from datetime import datetime, timedelta
                        expiration_date = (datetime.now() + timedelta(days=days_to_expiration)).strftime("%Y-%m-%d")
                        
                        # Call butterfly (neutral to slightly bullish)
                        signals.extend([
                            # Buy lower wing call
                            OptionSignal(
                                ticker=ticker,
                                strike=round(lower_wing, 2),
                                option_type=OptionType.CALL,
                                price=wing_cost * 0.6,
                                action=Action.BUY,
                                expiration=expiration_date,
                                credit_debit=CreditDebit.DEBIT
                            ),
                            # Sell 2 center calls
                            OptionSignal(
                                ticker=ticker,
                                strike=round(center_strike, 2),
                                option_type=OptionType.CALL,
                                price=center_credit,
                                action=Action.SELL,
                                expiration=expiration_date,
                                credit_debit=CreditDebit.CREDIT
                            ),
                            # Buy upper wing call
                            OptionSignal(
                                ticker=ticker,
                                strike=round(upper_wing, 2),
                                option_type=OptionType.CALL,
                                price=wing_cost * 0.4,
                                action=Action.BUY,
                                expiration=expiration_date,
                                credit_debit=CreditDebit.DEBIT
                            )
                        ])
        
        return signals
    
    def get_param_descriptions(self) -> Dict[str, str]:
        return {
            "wing_width": "Distance from center to wing strikes as % of price",
            "atm_tolerance": "Maximum deviation from ATM for center strike",
            "iv_percentile_min": "Minimum IV percentile for entry",
            "days_to_expiration": "Days until expiration (30-45 optimal)",
            "max_cost": "Maximum debit as percentage of wing width",
            "range_bound_period": "Period to analyze for range-bound behavior"
        }
    
    def get_required_columns(self) -> List[str]:
        return ["close", "high", "low"]