from typing import List, Dict
import pandas as pd
from ...base_strategy import BaseStrategy
from ...signals import OptionSignal, Action, OptionType, CreditDebit


class ShortPutLadderStrategy(BaseStrategy):
    """
    Short Put Ladder Strategy
    
    Bearish strategy that sells multiple puts at different strikes.
    Profits when stock declines but provides some protection if it rises.
    
    Parameters:
        bearish_signal_threshold (float): RSI threshold for bearish signal (default: 65)
        ladder_strikes (int): Number of ladder strikes (default: 3)
        strike_spacing (float): Spacing between strikes as % of price (default: 0.025)
        base_delta (float): Delta for highest strike put (default: 0.30)
        days_to_expiration (int): Days until option expiration (default: 30)
        min_total_credit (float): Minimum total credit as % of price (default: 0.04)
    
    Required DataFrame columns:
        - close: Closing prices
        - high: High prices (for resistance analysis)
        - low: Low prices (for support analysis)
    
    Optional DataFrame attributes:
        - ticker: Stock ticker symbol
    """
    
    def __init__(self, bearish_signal_threshold: float = 65, ladder_strikes: int = 3,
                 strike_spacing: float = 0.025, base_delta: float = 0.30,
                 days_to_expiration: int = 30, min_total_credit: float = 0.04):
        params = {
            "bearish_signal_threshold": bearish_signal_threshold,
            "ladder_strikes": ladder_strikes,
            "strike_spacing": strike_spacing,
            "base_delta": base_delta,
            "days_to_expiration": days_to_expiration,
            "min_total_credit": min_total_credit
        }
        super().__init__(
            name="Short Put Ladder Strategy",
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
        
        required_cols = ['close', 'high', 'low']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain columns: {required_cols}")
        
        df_copy = df.copy()
        bearish_threshold = self.params["bearish_signal_threshold"]
        ladder_strikes = self.params["ladder_strikes"]
        strike_spacing = self.params["strike_spacing"]
        base_delta = self.params["base_delta"]
        days_to_expiration = self.params["days_to_expiration"]
        min_total_credit = self.params["min_total_credit"]
        
        df_copy['rsi'] = self._calculate_rsi(df_copy['close'])
        df_copy['resistance'] = df_copy['high'].rolling(window=20).max()
        df_copy['support'] = df_copy['low'].rolling(window=20).min()
        
        ticker = getattr(df, 'ticker', 'UNKNOWN')
        
        for idx, row in df_copy.iterrows():
            if pd.isna(row['rsi']) or pd.isna(row['resistance']) or pd.isna(row['support']):
                continue
                
            # Enter when bearish signal and price near resistance
            if (row['rsi'] > bearish_threshold and 
                row['close'] >= row['resistance'] * 0.95):
                
                current_price = row['close']
                spacing_points = current_price * strike_spacing
                
                # Calculate ladder strikes (descending)
                strikes = []
                base_strike = current_price * (1 - base_delta * 0.1)
                
                for i in range(ladder_strikes):
                    strike = base_strike - (i * spacing_points)
                    strikes.append(strike)
                
                # Estimate credits for each strike
                total_credit = 0
                ladder_signals = []
                
                from datetime import datetime, timedelta
                expiration_date = (datetime.now() + timedelta(days=days_to_expiration)).strftime("%Y-%m-%d")
                
                for i, strike in enumerate(strikes):
                    # Higher strikes get more premium
                    credit_factor = 0.025 - (i * 0.005)  # Decreasing credit
                    put_credit = current_price * max(credit_factor, 0.01)
                    total_credit += put_credit
                    
                    ladder_signals.append(OptionSignal(
                        ticker=ticker,
                        strike=round(strike, 2),
                        option_type=OptionType.PUT,
                        price=put_credit,
                        action=Action.SELL,
                        expiration=expiration_date,
                        credit_debit=CreditDebit.CREDIT
                    ))
                
                # Only enter if total credit is adequate
                if total_credit >= current_price * min_total_credit:
                    signals.extend(ladder_signals)
        
        return signals
    
    def get_param_descriptions(self) -> Dict[str, str]:
        return {
            "bearish_signal_threshold": "RSI threshold for bearish signal entry",
            "ladder_strikes": "Number of put strikes in the ladder (2-5)",
            "strike_spacing": "Spacing between strikes as % of stock price",
            "base_delta": "Target delta for the highest strike put",
            "days_to_expiration": "Days until expiration (20-45 optimal)",
            "min_total_credit": "Minimum total credit from all puts as % of price"
        }
    
    def get_required_columns(self) -> List[str]:
        return ["close", "high", "low"]