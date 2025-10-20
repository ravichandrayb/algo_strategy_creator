from typing import List, Dict
import pandas as pd
from ...base_strategy import BaseStrategy
from ...signals import OptionSignal, Action, OptionType, CreditDebit


class ProtectivePutStrategy(BaseStrategy):
    """
    Protective Put Strategy
    
    Hedge strategy for existing stock positions. Buy put options to protect against downside.
    Used when holding stock but concerned about potential decline.
    
    Parameters:
        volatility_spike_threshold (float): HV percentile to trigger protection (default: 70)
        put_delta (float): Target delta for protective put (default: 0.30)
        max_drawdown_tolerance (float): Max acceptable drawdown % (default: 0.10)
        days_to_expiration (int): Days until option expiration (default: 60)
        max_cost (float): Maximum put cost as % of stock price (default: 0.03)
    
    Required DataFrame columns:
        - close: Closing prices
        - high: High prices (for volatility calculation)
        - low: Low prices (for volatility calculation)
    
    Optional DataFrame attributes:
        - ticker: Stock ticker symbol
    """
    
    def __init__(self, volatility_spike_threshold: float = 70, put_delta: float = 0.30,
                 max_drawdown_tolerance: float = 0.10, days_to_expiration: int = 60, max_cost: float = 0.03):
        params = {
            "volatility_spike_threshold": volatility_spike_threshold,
            "put_delta": put_delta,
            "max_drawdown_tolerance": max_drawdown_tolerance,
            "days_to_expiration": days_to_expiration,
            "max_cost": max_cost
        }
        super().__init__(
            name="Protective Put Strategy",
            params=params,
            is_option_trade=True
        )
    
    def _calculate_historical_volatility(self, prices: pd.Series, window: int = 20) -> pd.Series:
        returns = prices.pct_change()
        return returns.rolling(window=window).std() * (252 ** 0.5) * 100
    
    def _calculate_max_drawdown(self, prices: pd.Series, window: int = 20) -> pd.Series:
        rolling_max = prices.rolling(window=window, min_periods=1).max()
        drawdown = (prices - rolling_max) / rolling_max
        return drawdown
    
    def generate_signals(self, df: pd.DataFrame) -> List[OptionSignal]:
        signals = []
        
        required_cols = ['close', 'high', 'low']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain columns: {required_cols}")
        
        df_copy = df.copy()
        vol_spike_threshold = self.params["volatility_spike_threshold"]
        put_delta = self.params["put_delta"]
        max_drawdown_tolerance = self.params["max_drawdown_tolerance"]
        days_to_expiration = self.params["days_to_expiration"]
        max_cost = self.params["max_cost"]
        
        df_copy['hv'] = self._calculate_historical_volatility(df_copy['close'])
        df_copy['hv_percentile'] = df_copy['hv'].rolling(window=252).rank(pct=True) * 100
        df_copy['drawdown'] = self._calculate_max_drawdown(df_copy['close'])
        
        ticker = getattr(df, 'ticker', 'UNKNOWN')
        
        for idx, row in df_copy.iterrows():
            if pd.isna(row['hv_percentile']) or pd.isna(row['drawdown']):
                continue
                
            # Trigger protection when volatility spikes or drawdown is concerning
            if (row['hv_percentile'] > vol_spike_threshold or 
                row['drawdown'] < -max_drawdown_tolerance * 0.7):  # 70% of max tolerance
                
                current_price = row['close']
                
                # Calculate protective put strike
                put_strike = current_price * (1 - max_drawdown_tolerance)
                
                # Estimate put cost
                put_cost = current_price * max_cost
                
                # Only buy protection if cost is reasonable
                if put_cost <= current_price * max_cost:
                    from datetime import datetime, timedelta
                    expiration_date = (datetime.now() + timedelta(days=days_to_expiration)).strftime("%Y-%m-%d")
                    
                    signals.append(OptionSignal(
                        ticker=ticker,
                        strike=round(put_strike, 2),
                        option_type=OptionType.PUT,
                        price=put_cost,
                        action=Action.BUY,
                        expiration=expiration_date,
                        credit_debit=CreditDebit.DEBIT
                    ))
        
        return signals
    
    def get_param_descriptions(self) -> Dict[str, str]:
        return {
            "volatility_spike_threshold": "HV percentile threshold to trigger protection",
            "put_delta": "Target delta for protective put (0.20-0.40)",
            "max_drawdown_tolerance": "Maximum acceptable portfolio drawdown (0.05-0.15)",
            "days_to_expiration": "Days until expiration (60-90 for protection)",
            "max_cost": "Maximum put cost as percentage of stock price"
        }
    
    def get_required_columns(self) -> List[str]:
        return ["close", "high", "low"]