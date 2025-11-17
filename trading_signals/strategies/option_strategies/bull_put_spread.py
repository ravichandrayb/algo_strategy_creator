from typing import List, Dict
import pandas as pd
from ...base_strategy import BaseStrategy
from ...signals import OptionSignal, Action, OptionType, CreditDebit


class BullPutSpreadStrategy(BaseStrategy):
    """
    Bull Put Spread Strategy
    
    Bullish credit spread using put options. Sell higher strike put, buy lower strike put.
    Collects credit upfront. Profits when stock stays above short put strike.
    
    Parameters:
        rsi_oversold (float): RSI threshold for oversold condition (default: 30)
        support_bounce_factor (float): Factor above support for entry (default: 1.02)
        spread_width (float): Width between strikes as % of price (default: 0.05)
        short_delta (float): Target delta for short put (default: 0.30)
        days_to_expiration (int): Days until option expiration (default: 30)
        min_credit (float): Minimum credit as % of spread width (default: 0.30)
    
    Required DataFrame columns:
        - close: Closing prices
        - low: Low prices (for support calculation)
    
    Optional DataFrame attributes:
        - ticker: Stock ticker symbol
    """
    
    def __init__(self, rsi_oversold: float = 30, support_bounce_factor: float = 1.02,
                 spread_width: float = 0.05, short_delta: float = 0.30,
                 days_to_expiration: int = 30, min_credit: float = 0.30):
        params = {
            "rsi_oversold": rsi_oversold,
            "support_bounce_factor": support_bounce_factor,
            "spread_width": spread_width,
            "short_delta": short_delta,
            "days_to_expiration": days_to_expiration,
            "min_credit": min_credit
        }
        super().__init__(
            name="Bull Put Spread Strategy",
            params=params,
            is_option_trade=True
        )
    
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
        
        required_cols = ['close', 'low']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain columns: {required_cols}")
        
        df_copy = df.copy()
        rsi_oversold = self.params["rsi_oversold"]
        support_bounce_factor = self.params["support_bounce_factor"]
        spread_width = self.params["spread_width"]
        short_delta = self.params["short_delta"]
        days_to_expiration = self.params["days_to_expiration"]
        min_credit = self.params["min_credit"]
        
        df_copy['rsi'] = self._calculate_rsi(df_copy['close'])
        df_copy['support'] = df_copy['low'].rolling(window=20).min()
        
        ticker = getattr(df, 'ticker', 'UNKNOWN')
        
        for idx, row in df_copy.iterrows():
            if pd.isna(row['rsi']) or pd.isna(row['support']):
                continue
                
            # Bullish signal: RSI recovering from oversold and price above support
            if (row['rsi'] > rsi_oversold and row['rsi'] < 50 and  # Recovery but not overbought
                row['close'] >= row['support'] * support_bounce_factor):
                
                current_price = row['close']
                spread_points = current_price * spread_width
                
                # Strike selection (put spread below current price)
                short_put_strike = current_price * (1 - short_delta * 0.1)
                long_put_strike = short_put_strike - spread_points
                
                # Estimate credit
                short_put_premium = spread_points * 0.6
                long_put_cost = spread_points * 0.3
                net_credit = short_put_premium - long_put_cost
                
                # Only enter if credit is adequate
                if net_credit >= spread_points * min_credit:
                    from datetime import datetime, timedelta
                    expiration_date = (datetime.now() + timedelta(days=days_to_expiration)).strftime("%Y-%m-%d")
                    
                    signals.extend([
                        # Sell higher strike put
                        OptionSignal(
                            ticker=ticker,
                            strike=round(short_put_strike, 2),
                            option_type=OptionType.PUT,
                            price=short_put_premium,
                            action=Action.SELL,
                            expiration=expiration_date,
                            credit_debit=CreditDebit.CREDIT
                        ),
                        # Buy lower strike put
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
            "rsi_oversold": "RSI threshold for oversold condition (20-40)",
            "support_bounce_factor": "Multiple of support level for bullish confirmation",
            "spread_width": "Width between put strikes as percentage of stock price",
            "short_delta": "Target delta for short put (0.15-0.35)",
            "days_to_expiration": "Days until expiration (20-45 optimal)",
            "min_credit": "Minimum credit as percentage of spread width (0.25-0.40)"
        }
    
    def get_required_columns(self) -> List[str]:
        return ["close", "low"]