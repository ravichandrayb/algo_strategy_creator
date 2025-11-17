from typing import List, Dict
import pandas as pd
from ...base_strategy import BaseStrategy
from ...signals import OptionSignal, Action, OptionType, CreditDebit


class BearCallSpreadStrategy(BaseStrategy):
    """
    Bear Call Spread Strategy
    
    Bearish credit spread using call options. Sell lower strike call, buy higher strike call.
    Collects credit upfront. Profits when stock stays below short call strike.
    
    Parameters:
        rsi_overbought (float): RSI threshold for overbought condition (default: 70)
        resistance_rejection_factor (float): Factor below resistance for entry (default: 0.98)
        spread_width (float): Width between strikes as % of price (default: 0.05)
        short_delta (float): Target delta for short call (default: 0.30)
        days_to_expiration (int): Days until option expiration (default: 30)
        min_credit (float): Minimum credit as % of spread width (default: 0.30)
    
    Required DataFrame columns:
        - close: Closing prices
        - high: High prices (for resistance calculation)
    
    Optional DataFrame attributes:
        - ticker: Stock ticker symbol
    """
    
    def __init__(self, rsi_overbought: float = 70, resistance_rejection_factor: float = 0.98,
                 spread_width: float = 0.05, short_delta: float = 0.30,
                 days_to_expiration: int = 30, min_credit: float = 0.30):
        params = {
            "rsi_overbought": rsi_overbought,
            "resistance_rejection_factor": resistance_rejection_factor,
            "spread_width": spread_width,
            "short_delta": short_delta,
            "days_to_expiration": days_to_expiration,
            "min_credit": min_credit
        }
        super().__init__(
            name="Bear Call Spread Strategy",
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
        
        required_cols = ['close', 'high']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain columns: {required_cols}")
        
        df_copy = df.copy()
        rsi_overbought = self.params["rsi_overbought"]
        resistance_rejection_factor = self.params["resistance_rejection_factor"]
        spread_width = self.params["spread_width"]
        short_delta = self.params["short_delta"]
        days_to_expiration = self.params["days_to_expiration"]
        min_credit = self.params["min_credit"]
        
        df_copy['rsi'] = self._calculate_rsi(df_copy['close'])
        df_copy['resistance'] = df_copy['high'].rolling(window=20).max()
        
        ticker = getattr(df, 'ticker', 'UNKNOWN')
        
        for idx, row in df_copy.iterrows():
            if pd.isna(row['rsi']) or pd.isna(row['resistance']):
                continue
                
            # Bearish signal: RSI overbought and price rejecting resistance
            if (row['rsi'] > rsi_overbought and 
                row['close'] <= row['resistance'] * resistance_rejection_factor):
                
                current_price = row['close']
                spread_points = current_price * spread_width
                
                # Strike selection (call spread above current price)
                short_call_strike = current_price * (1 + short_delta * 0.1)
                long_call_strike = short_call_strike + spread_points
                
                # Estimate credit
                short_call_premium = spread_points * 0.6
                long_call_cost = spread_points * 0.3
                net_credit = short_call_premium - long_call_cost
                
                # Only enter if credit is adequate
                if net_credit >= spread_points * min_credit:
                    from datetime import datetime, timedelta
                    expiration_date = (datetime.now() + timedelta(days=days_to_expiration)).strftime("%Y-%m-%d")
                    
                    signals.extend([
                        # Sell lower strike call
                        OptionSignal(
                            ticker=ticker,
                            strike=round(short_call_strike, 2),
                            option_type=OptionType.CALL,
                            price=short_call_premium,
                            action=Action.SELL,
                            expiration=expiration_date,
                            credit_debit=CreditDebit.CREDIT
                        ),
                        # Buy higher strike call
                        OptionSignal(
                            ticker=ticker,
                            strike=round(long_call_strike, 2),
                            option_type=OptionType.CALL,
                            price=long_call_cost,
                            action=Action.BUY,
                            expiration=expiration_date,
                            credit_debit=CreditDebit.DEBIT
                        )
                    ])
        
        return signals
    
    def get_param_descriptions(self) -> Dict[str, str]:
        return {
            "rsi_overbought": "RSI threshold for overbought condition (65-80)",
            "resistance_rejection_factor": "Multiple of resistance for bearish confirmation",
            "spread_width": "Width between call strikes as percentage of stock price",
            "short_delta": "Target delta for short call (0.15-0.35)",
            "days_to_expiration": "Days until expiration (20-45 optimal)",
            "min_credit": "Minimum credit as percentage of spread width (0.25-0.40)"
        }
    
    def get_required_columns(self) -> List[str]:
        return ["close", "high"]