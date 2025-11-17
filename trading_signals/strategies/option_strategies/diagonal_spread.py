from typing import List, Dict
import pandas as pd
from ...base_strategy import BaseStrategy
from ...signals import OptionSignal, Action, OptionType, CreditDebit


class DiagonalSpreadStrategy(BaseStrategy):
    """
    Diagonal Spread Strategy
    
    Combines calendar and vertical spread concepts. Sell short-term option at one strike,
    buy longer-term option at different strike. Directional bias with time decay benefit.
    
    Parameters:
        trend_strength_min (float): Minimum trend strength for directional bias (default: 0.6)
        strike_separation (float): Strike separation as % of price (default: 0.03)
        short_days_to_expiration (int): Days to front month expiration (default: 30)
        long_days_to_expiration (int): Days to back month expiration (default: 60)
        max_cost (float): Maximum debit as % of stock price (default: 0.05)
        volatility_skew_min (float): Minimum vol skew for entry (default: 1.05)
    
    Required DataFrame columns:
        - close: Closing prices
        - high: High prices (for trend analysis)
        - low: Low prices (for trend analysis)
    
    Optional DataFrame attributes:
        - ticker: Stock ticker symbol
    """
    
    def __init__(self, trend_strength_min: float = 0.6, strike_separation: float = 0.03,
                 short_days_to_expiration: int = 30, long_days_to_expiration: int = 60,
                 max_cost: float = 0.05, volatility_skew_min: float = 1.05):
        params = {
            "trend_strength_min": trend_strength_min,
            "strike_separation": strike_separation,
            "short_days_to_expiration": short_days_to_expiration,
            "long_days_to_expiration": long_days_to_expiration,
            "max_cost": max_cost,
            "volatility_skew_min": volatility_skew_min
        }
        super().__init__(
            name="Diagonal Spread Strategy",
            params=params,
            is_option_trade=True
        )
    
    def _calculate_trend_strength(self, prices: pd.Series, window: int = 20) -> pd.Series:
        """Calculate trend strength using linear regression slope"""
        def calc_slope(y):
            if len(y) < 2:
                return 0
            x = range(len(y))
            n = len(y)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_x2 = sum(x[i] ** 2 for i in range(n))
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
            return slope / y.iloc[-1]  # Normalize by current price
        
        return prices.rolling(window=window).apply(calc_slope, raw=False)
    
    def generate_signals(self, df: pd.DataFrame) -> List[OptionSignal]:
        signals = []
        
        # Normalize column names to lowercase
        df = self.normalize_dataframe(df)
        
        required_cols = ['close', 'high', 'low']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain columns: {required_cols}")
        
        df_copy = df.copy()
        trend_min = self.params["trend_strength_min"]
        strike_sep = self.params["strike_separation"]
        short_days = self.params["short_days_to_expiration"]
        long_days = self.params["long_days_to_expiration"]
        max_cost = self.params["max_cost"]
        vol_skew_min = self.params["volatility_skew_min"]
        
        df_copy['trend_strength'] = self._calculate_trend_strength(df_copy['close'])
        
        # Simulate volatility skew (OTM vs ATM vol)
        df_copy['vol_short'] = df_copy['close'].pct_change().rolling(10).std() * 100
        df_copy['vol_long'] = df_copy['close'].pct_change().rolling(30).std() * 100
        df_copy['vol_skew'] = df_copy['vol_short'] / df_copy['vol_long']
        
        ticker = getattr(df, 'ticker', 'UNKNOWN')
        
        for idx, row in df_copy.iterrows():
            if pd.isna(row['trend_strength']) or pd.isna(row['vol_skew']):
                continue
                
            # Enter when there's a clear trend and favorable vol skew
            if (abs(row['trend_strength']) > trend_min and 
                row['vol_skew'] > vol_skew_min):
                
                current_price = row['close']
                strike_points = current_price * strike_sep
                
                # Determine bullish or bearish bias
                is_bullish = row['trend_strength'] > 0
                
                if is_bullish:
                    # Bull diagonal: sell front month call OTM, buy back month call ATM
                    short_call_strike = current_price + strike_points
                    long_call_strike = current_price
                    
                    short_call_credit = current_price * 0.015
                    long_call_cost = current_price * 0.04
                    net_debit = long_call_cost - short_call_credit
                    
                    if net_debit <= current_price * max_cost:
                        from datetime import datetime, timedelta
                        
                        short_expiration = (datetime.now() + timedelta(days=short_days)).strftime("%Y-%m-%d")
                        long_expiration = (datetime.now() + timedelta(days=long_days)).strftime("%Y-%m-%d")
                        
                        signals.extend([
                            # Sell front month OTM call
                            OptionSignal(
                                ticker=ticker,
                                strike=round(short_call_strike, 2),
                                option_type=OptionType.CALL,
                                price=short_call_credit,
                                action=Action.SELL,
                                expiration=short_expiration,
                                credit_debit=CreditDebit.CREDIT
                            ),
                            # Buy back month ATM call
                            OptionSignal(
                                ticker=ticker,
                                strike=round(long_call_strike, 2),
                                option_type=OptionType.CALL,
                                price=long_call_cost,
                                action=Action.BUY,
                                expiration=long_expiration,
                                credit_debit=CreditDebit.DEBIT
                            )
                        ])
                        
                else:
                    # Bear diagonal: sell front month put OTM, buy back month put ATM
                    short_put_strike = current_price - strike_points
                    long_put_strike = current_price
                    
                    short_put_credit = current_price * 0.015
                    long_put_cost = current_price * 0.04
                    net_debit = long_put_cost - short_put_credit
                    
                    if net_debit <= current_price * max_cost:
                        from datetime import datetime, timedelta
                        
                        short_expiration = (datetime.now() + timedelta(days=short_days)).strftime("%Y-%m-%d")
                        long_expiration = (datetime.now() + timedelta(days=long_days)).strftime("%Y-%m-%d")
                        
                        signals.extend([
                            # Sell front month OTM put
                            OptionSignal(
                                ticker=ticker,
                                strike=round(short_put_strike, 2),
                                option_type=OptionType.PUT,
                                price=short_put_credit,
                                action=Action.SELL,
                                expiration=short_expiration,
                                credit_debit=CreditDebit.CREDIT
                            ),
                            # Buy back month ATM put
                            OptionSignal(
                                ticker=ticker,
                                strike=round(long_put_strike, 2),
                                option_type=OptionType.PUT,
                                price=long_put_cost,
                                action=Action.BUY,
                                expiration=long_expiration,
                                credit_debit=CreditDebit.DEBIT
                            )
                        ])
        
        return signals
    
    def get_param_descriptions(self) -> Dict[str, str]:
        return {
            "trend_strength_min": "Minimum trend strength for directional bias",
            "strike_separation": "Strike separation as percentage of stock price",
            "short_days_to_expiration": "Days to front month expiration",
            "long_days_to_expiration": "Days to back month expiration",
            "max_cost": "Maximum diagonal debit as % of stock price",
            "volatility_skew_min": "Minimum volatility skew for favorable entry"
        }
    
    def get_required_columns(self) -> List[str]:
        return ["close", "high", "low"]