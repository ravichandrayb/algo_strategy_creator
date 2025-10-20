from typing import List, Dict
import pandas as pd
from ...base_strategy import BaseStrategy
from ...signals import OptionSignal, Action, OptionType, CreditDebit


class CollarStrategy(BaseStrategy):
    """
    Collar Strategy
    
    Protection strategy combining covered call and protective put. Sell call above current price,
    buy put below current price. Limits both upside and downside for existing stock positions.
    
    Parameters:
        volatility_threshold (float): HV percentile to trigger collar (default: 60)
        call_delta (float): Target delta for call option (default: 0.25)
        put_delta (float): Target delta for put option (default: 0.25)
        max_net_cost (float): Maximum net cost as % of stock price (default: 0.02)
        days_to_expiration (int): Days until option expiration (default: 60)
        target_protection (float): Target downside protection % (default: 0.10)
    
    Required DataFrame columns:
        - close: Closing prices
        - high: High prices (for volatility and resistance)
        - low: Low prices (for volatility and support)
    
    Optional DataFrame attributes:
        - ticker: Stock ticker symbol
    """
    
    def __init__(self, volatility_threshold: float = 60, call_delta: float = 0.25, put_delta: float = 0.25,
                 max_net_cost: float = 0.02, days_to_expiration: int = 60, target_protection: float = 0.10):
        params = {
            "volatility_threshold": volatility_threshold,
            "call_delta": call_delta,
            "put_delta": put_delta,
            "max_net_cost": max_net_cost,
            "days_to_expiration": days_to_expiration,
            "target_protection": target_protection
        }
        super().__init__(
            name="Collar Strategy",
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
        vol_threshold = self.params["volatility_threshold"]
        call_delta = self.params["call_delta"]
        put_delta = self.params["put_delta"]
        max_net_cost = self.params["max_net_cost"]
        days_to_expiration = self.params["days_to_expiration"]
        target_protection = self.params["target_protection"]
        
        df_copy['hv'] = self._calculate_historical_volatility(df_copy['close'])
        df_copy['hv_percentile'] = df_copy['hv'].rolling(window=252).rank(pct=True) * 100
        df_copy['resistance'] = df_copy['high'].rolling(window=20).max()
        df_copy['support'] = df_copy['low'].rolling(window=20).min()
        
        ticker = getattr(df, 'ticker', 'UNKNOWN')
        
        for idx, row in df_copy.iterrows():
            if pd.isna(row['hv_percentile']) or pd.isna(row['resistance']) or pd.isna(row['support']):
                continue
                
            # Enter collar when volatility is elevated (good time to sell premium)
            if row['hv_percentile'] > vol_threshold:
                current_price = row['close']
                
                # Calculate strikes
                call_strike = min(row['resistance'], current_price * (1 + call_delta * 0.15))
                put_strike = max(row['support'], current_price * (1 - target_protection))
                
                # Estimate option prices
                call_credit = current_price * 0.02  # OTM call credit
                put_cost = current_price * 0.025   # OTM put cost
                net_cost = put_cost - call_credit
                
                # Only enter if net cost is acceptable (preferably credit or low debit)
                if net_cost <= current_price * max_net_cost:
                    from datetime import datetime, timedelta
                    expiration_date = (datetime.now() + timedelta(days=days_to_expiration)).strftime("%Y-%m-%d")
                    
                    signals.extend([
                        # Sell call (covered call component)
                        OptionSignal(
                            ticker=ticker,
                            strike=round(call_strike, 2),
                            option_type=OptionType.CALL,
                            price=call_credit,
                            action=Action.SELL,
                            expiration=expiration_date,
                            credit_debit=CreditDebit.CREDIT
                        ),
                        # Buy put (protective put component)
                        OptionSignal(
                            ticker=ticker,
                            strike=round(put_strike, 2),
                            option_type=OptionType.PUT,
                            price=put_cost,
                            action=Action.BUY,
                            expiration=expiration_date,
                            credit_debit=CreditDebit.DEBIT
                        )
                    ])
        
        return signals
    
    def get_param_descriptions(self) -> Dict[str, str]:
        return {
            "volatility_threshold": "HV percentile threshold to enter collar",
            "call_delta": "Target delta for call option (0.15-0.35)",
            "put_delta": "Target delta for put option (0.15-0.35)",
            "max_net_cost": "Maximum net cost as % of stock price (prefer credit)",
            "days_to_expiration": "Days until expiration (45-90 optimal)",
            "target_protection": "Target downside protection percentage (0.05-0.15)"
        }
    
    def get_required_columns(self) -> List[str]:
        return ["close", "high", "low"]