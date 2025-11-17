from typing import List, Dict
import pandas as pd
from ...base_strategy import BaseStrategy
from ...signals import OptionSignal, Action, OptionType, CreditDebit


class BigLizardStrategy(BaseStrategy):
    """
    Big Lizard Strategy
    
    Neutral to bearish strategy combining short call and short put spread.
    Sells call above current price and put spread below. Opposite of Jade Lizard.
    
    Parameters:
        iv_percentile_min (float): Minimum IV percentile for entry (default: 50)
        call_delta (float): Target delta for short call (default: 0.20)
        put_spread_width (float): Put spread width as % of price (default: 0.05)
        put_delta (float): Target delta for short put (default: 0.16)
        days_to_expiration (int): Days until option expiration (default: 45)
        min_credit (float): Minimum total credit as % of price (default: 0.03)
    
    Required DataFrame columns:
        - close: Closing prices
        - high: High prices (for volatility analysis)
        - low: Low prices (for volatility analysis)
    
    Optional DataFrame attributes:
        - ticker: Stock ticker symbol
    """
    
    def __init__(self, iv_percentile_min: float = 50, call_delta: float = 0.20,
                 put_spread_width: float = 0.05, put_delta: float = 0.16,
                 days_to_expiration: int = 45, min_credit: float = 0.03):
        params = {
            "iv_percentile_min": iv_percentile_min,
            "call_delta": call_delta,
            "put_spread_width": put_spread_width,
            "put_delta": put_delta,
            "days_to_expiration": days_to_expiration,
            "min_credit": min_credit
        }
        super().__init__(
            name="Big Lizard Strategy",
            params=params,
            is_option_trade=True
        )
    
    def _calculate_historical_volatility(self, prices: pd.Series, window: int = 20) -> pd.Series:
        returns = prices.pct_change()
        return returns.rolling(window=window).std() * (252 ** 0.5) * 100
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
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
        put_spread_width = self.params["put_spread_width"]
        put_delta = self.params["put_delta"]
        days_to_expiration = self.params["days_to_expiration"]
        min_credit = self.params["min_credit"]
        
        df_copy['hv'] = self._calculate_historical_volatility(df_copy['close'])
        df_copy['hv_percentile'] = df_copy['hv'].rolling(window=252).rank(pct=True) * 100
        df_copy['rsi'] = self._calculate_rsi(df_copy['close'])
        
        ticker = getattr(df, 'ticker', 'UNKNOWN')
        
        for idx, row in df_copy.iterrows():
            if pd.isna(row['hv_percentile']) or pd.isna(row['rsi']):
                continue
                
            # Enter when IV is elevated and market is neutral to bearish
            if (row['hv_percentile'] > iv_percentile_min and 
                35 < row['rsi'] < 70):  # Not oversold but can be overbought
                
                current_price = row['close']
                
                # Strike calculations
                call_strike = current_price * (1 + call_delta * 0.15)
                put_spread_points = current_price * put_spread_width
                short_put_strike = current_price * (1 - put_delta * 0.12)
                long_put_strike = short_put_strike - put_spread_points
                
                # Estimate credits/costs
                call_credit = current_price * 0.025
                short_put_credit = current_price * 0.02
                long_put_cost = current_price * 0.01
                
                total_credit = call_credit + short_put_credit - long_put_cost
                
                # Only enter if credit is adequate
                if total_credit >= current_price * min_credit:
                    from datetime import datetime, timedelta
                    expiration_date = (datetime.now() + timedelta(days=days_to_expiration)).strftime("%Y-%m-%d")
                    
                    signals.extend([
                        # Sell covered call
                        OptionSignal(
                            ticker=ticker,
                            strike=round(call_strike, 2),
                            option_type=OptionType.CALL,
                            price=call_credit,
                            action=Action.SELL,
                            expiration=expiration_date,
                            credit_debit=CreditDebit.CREDIT
                        ),
                        # Short put spread
                        OptionSignal(
                            ticker=ticker,
                            strike=round(short_put_strike, 2),
                            option_type=OptionType.PUT,
                            price=short_put_credit,
                            action=Action.SELL,
                            expiration=expiration_date,
                            credit_debit=CreditDebit.CREDIT
                        ),
                        OptionSignal(
                            ticker=ticker,
                            strike=round(long_put_strike, 2),
                            option_type=OptionType.PUT,
                            price=long_put_cost,
                            action=Action.BUY,
                            expiration=expiration_date,
                            credit_debit=CreditDebit.DEBIT
                        )
                    ])
        
        return signals
    
    def get_param_descriptions(self) -> Dict[str, str]:
        return {
            "iv_percentile_min": "Minimum IV percentile for entry (want elevated IV)",
            "call_delta": "Target delta for short call (0.15-0.25)",
            "put_spread_width": "Put spread width as percentage of stock price",
            "put_delta": "Target delta for short put (0.12-0.20)",
            "days_to_expiration": "Days until expiration (30-60 optimal)",
            "min_credit": "Minimum total credit as percentage of stock price"
        }
    
    def get_required_columns(self) -> List[str]:
        return ["close", "high", "low"]