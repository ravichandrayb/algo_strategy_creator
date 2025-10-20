from typing import List, Dict
import pandas as pd
from ...base_strategy import BaseStrategy
from ...signals import OptionSignal, Action, OptionType, CreditDebit


class BearPutSpreadStrategy(BaseStrategy):
    """
    Bear Put Spread Strategy
    
    Bearish strategy using put options. Buy higher strike put, sell lower strike put.
    Limited profit and limited risk. Profits when stock falls moderately.
    
    Parameters:
        bearish_signal_threshold (float): RSI threshold for bearish signal (default: 60)
        resistance_rejection_factor (float): Factor below resistance for entry (default: 0.98)
        spread_width (float): Width between strikes as % of price (default: 0.05)
        short_delta (float): Target delta for short put (default: 0.30)
        days_to_expiration (int): Days until option expiration (default: 30)
        max_cost (float): Maximum debit as % of spread width (default: 0.60)
    
    Required DataFrame columns:
        - close: Closing prices
        - high: High prices (for resistance calculation)
    
    Optional DataFrame attributes:
        - ticker: Stock ticker symbol
    """
    
    def __init__(self, bearish_signal_threshold: float = 60, resistance_rejection_factor: float = 0.98,
                 spread_width: float = 0.05, short_delta: float = 0.30,
                 days_to_expiration: int = 30, max_cost: float = 0.60):
        params = {
            "bearish_signal_threshold": bearish_signal_threshold,
            "resistance_rejection_factor": resistance_rejection_factor,
            "spread_width": spread_width,
            "short_delta": short_delta,
            "days_to_expiration": days_to_expiration,
            "max_cost": max_cost
        }
        super().__init__(
            name="Bear Put Spread Strategy",
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
        
        required_cols = ['close', 'high']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain columns: {required_cols}")
        
        df_copy = df.copy()
        bearish_threshold = self.params["bearish_signal_threshold"]
        resistance_rejection_factor = self.params["resistance_rejection_factor"]
        spread_width = self.params["spread_width"]
        short_delta = self.params["short_delta"]
        days_to_expiration = self.params["days_to_expiration"]
        max_cost = self.params["max_cost"]
        
        df_copy['rsi'] = self._calculate_rsi(df_copy['close'])
        df_copy['resistance'] = df_copy['high'].rolling(window=20).max()
        
        ticker = getattr(df, 'ticker', 'UNKNOWN')
        
        for idx, row in df_copy.iterrows():
            if pd.isna(row['rsi']) or pd.isna(row['resistance']):
                continue
                
            # Bearish signal: RSI overbought and price rejecting resistance
            if (row['rsi'] > bearish_threshold and 
                row['close'] <= row['resistance'] * resistance_rejection_factor):
                
                current_price = row['close']
                spread_points = current_price * spread_width
                
                # Strike selection
                long_put_strike = current_price  # ATM or slightly ITM
                short_put_strike = long_put_strike - spread_points
                
                # Estimate costs
                long_put_cost = spread_points * 0.7  # ITM put costs more
                short_put_credit = spread_points * 0.3  # OTM put worth less
                net_debit = long_put_cost - short_put_credit
                
                # Only enter if cost is reasonable
                if net_debit <= spread_points * max_cost:
                    from datetime import datetime, timedelta
                    expiration_date = (datetime.now() + timedelta(days=days_to_expiration)).strftime("%Y-%m-%d")
                    
                    signals.extend([
                        # Buy higher strike put
                        OptionSignal(
                            ticker=ticker,
                            strike=round(long_put_strike, 2),
                            option_type=OptionType.PUT,
                            price=long_put_cost,
                            action=Action.BUY,
                            expiration=expiration_date,
                            credit_debit=CreditDebit.DEBIT
                        ),
                        # Sell lower strike put
                        OptionSignal(
                            ticker=ticker,
                            strike=round(short_put_strike, 2),
                            option_type=OptionType.PUT,
                            price=short_put_credit,
                            action=Action.SELL,
                            expiration=expiration_date,
                            credit_debit=CreditDebit.CREDIT
                        )
                    ])
        
        return signals
    
    def get_param_descriptions(self) -> Dict[str, str]:
        return {
            "bearish_signal_threshold": "RSI level above which to consider bearish (60-80)",
            "resistance_rejection_factor": "Multiple of resistance level for entry confirmation",
            "spread_width": "Width between put strikes as percentage of stock price",
            "short_delta": "Target delta for short put (determines OTM distance)",
            "days_to_expiration": "Days until expiration (30-45 optimal for spreads)",
            "max_cost": "Maximum debit as percentage of spread width (0.5-0.7)"
        }
    
    def get_required_columns(self) -> List[str]:
        return ["close", "high"]