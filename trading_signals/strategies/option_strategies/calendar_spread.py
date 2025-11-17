from typing import List, Dict
import pandas as pd
from ...base_strategy import BaseStrategy
from ...signals import OptionSignal, Action, OptionType, CreditDebit


class CalendarSpreadStrategy(BaseStrategy):
    """
    Calendar Spread Strategy
    
    Time decay strategy that sells short-term option and buys longer-term option at same strike.
    Profits from time decay when stock stays near the strike price.
    
    Parameters:
        iv_term_structure_min (float): Min front/back month IV ratio (default: 0.8)
        atm_tolerance (float): Tolerance for ATM selection (default: 0.03)
        short_days_to_expiration (int): Days to front month expiration (default: 30)
        long_days_to_expiration (int): Days to back month expiration (default: 60)
        max_cost (float): Maximum debit as % of stock price (default: 0.04)
        volatility_percentile_max (float): Max volatility percentile (default: 60)
    
    Required DataFrame columns:
        - close: Closing prices
        - high: High prices (for volatility calculation)
        - low: Low prices (for volatility calculation)
    
    Optional DataFrame attributes:
        - ticker: Stock ticker symbol
    """
    
    def __init__(self, iv_term_structure_min: float = 0.8, atm_tolerance: float = 0.03,
                 short_days_to_expiration: int = 30, long_days_to_expiration: int = 60,
                 max_cost: float = 0.04, volatility_percentile_max: float = 60):
        params = {
            "iv_term_structure_min": iv_term_structure_min,
            "atm_tolerance": atm_tolerance,
            "short_days_to_expiration": short_days_to_expiration,
            "long_days_to_expiration": long_days_to_expiration,
            "max_cost": max_cost,
            "volatility_percentile_max": volatility_percentile_max
        }
        super().__init__(
            name="Calendar Spread Strategy",
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
        iv_term_min = self.params["iv_term_structure_min"]
        atm_tolerance = self.params["atm_tolerance"]
        short_days = self.params["short_days_to_expiration"]
        long_days = self.params["long_days_to_expiration"]
        max_cost = self.params["max_cost"]
        vol_percentile_max = self.params["volatility_percentile_max"]
        
        df_copy['hv'] = self._calculate_historical_volatility(df_copy['close'])
        df_copy['hv_percentile'] = df_copy['hv'].rolling(window=252).rank(pct=True) * 100
        
        # Simulate term structure (short-term vs long-term volatility)
        df_copy['hv_short'] = self._calculate_historical_volatility(df_copy['close'], window=10)
        df_copy['hv_long'] = self._calculate_historical_volatility(df_copy['close'], window=30)
        df_copy['term_structure'] = df_copy['hv_short'] / df_copy['hv_long']
        
        ticker = getattr(df, 'ticker', 'UNKNOWN')
        
        for idx, row in df_copy.iterrows():
            if (pd.isna(row['hv_percentile']) or pd.isna(row['term_structure'])):
                continue
                
            # Enter when term structure is normal and volatility not too high
            if (row['term_structure'] > iv_term_min and 
                row['hv_percentile'] < vol_percentile_max):
                
                current_price = row['close']
                
                # ATM strike
                atm_strike = round(current_price * 2) / 2
                
                # Check if close enough to ATM
                if abs(current_price - atm_strike) / current_price <= atm_tolerance:
                    # Estimate costs
                    short_option_credit = current_price * 0.02  # Front month premium
                    long_option_cost = current_price * 0.035    # Back month premium
                    net_debit = long_option_cost - short_option_credit
                    
                    # Only enter if cost is reasonable
                    if net_debit <= current_price * max_cost:
                        from datetime import datetime, timedelta
                        
                        short_expiration = (datetime.now() + timedelta(days=short_days)).strftime("%Y-%m-%d")
                        long_expiration = (datetime.now() + timedelta(days=long_days)).strftime("%Y-%m-%d")
                        
                        # Use calls for neutral to slightly bullish outlook
                        signals.extend([
                            # Sell front month call
                            OptionSignal(
                                ticker=ticker,
                                strike=round(atm_strike, 2),
                                option_type=OptionType.CALL,
                                price=short_option_credit,
                                action=Action.SELL,
                                expiration=short_expiration,
                                credit_debit=CreditDebit.CREDIT
                            ),
                            # Buy back month call
                            OptionSignal(
                                ticker=ticker,
                                strike=round(atm_strike, 2),
                                option_type=OptionType.CALL,
                                price=long_option_cost,
                                action=Action.BUY,
                                expiration=long_expiration,
                                credit_debit=CreditDebit.DEBIT
                            )
                        ])
        
        return signals
    
    def get_param_descriptions(self) -> Dict[str, str]:
        return {
            "iv_term_structure_min": "Minimum front/back month IV ratio for entry",
            "atm_tolerance": "Maximum deviation from ATM for trade entry",
            "short_days_to_expiration": "Days to front month expiration",
            "long_days_to_expiration": "Days to back month expiration",
            "max_cost": "Maximum calendar debit as % of stock price",
            "volatility_percentile_max": "Maximum volatility percentile for entry"
        }
    
    def get_required_columns(self) -> List[str]:
        return ["close", "high", "low"]