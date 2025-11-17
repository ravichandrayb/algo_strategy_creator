from abc import ABC, abstractmethod
from typing import Dict, Any, List, Union
import pandas as pd
from .signals import StockSignal, OptionSignal


class BaseStrategy(ABC):
    def __init__(self, name: str, params: Dict[str, Any], is_option_trade: bool = False):
        self.name = name
        self.params = params
        self.is_option_trade = is_option_trade
        # Flag to control whether to return all signals or only the latest
        # For live trading, this should be True. For backtesting, False.
        self.live_trading_mode = True  # Default to live trading mode
    
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> List[Union[StockSignal, OptionSignal]]:
        """
        Generate trading signals based on the input DataFrame.
        
        Args:
            df (pd.DataFrame): Stock/asset price data with required columns
            
        Returns:
            List[Union[StockSignal, OptionSignal]]: List of generated signals
        """
        pass
    
    def normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize DataFrame column names to lowercase.
        
        KiteDataFetcher returns columns as 'Open', 'High', 'Low', 'Close', 'Volume'
        but most strategies expect lowercase 'open', 'high', 'low', 'close', 'volume'.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with lowercase column names
        """
        df_copy = df.copy()
        df_copy.columns = df_copy.columns.str.lower()
        return df_copy
    
    def filter_signals_for_live_trading(self, signals: List[Union[StockSignal, OptionSignal]]) -> List[Union[StockSignal, OptionSignal]]:
        """
        Filter signals to only return the most recent one for live trading.
        
        For live trading, we only want to act on the latest signal.
        For backtesting, we want all historical signals.
        
        Args:
            signals: List of all generated signals
            
        Returns:
            List containing only the most recent signal (if any)
        """
        if not self.live_trading_mode or not signals:
            return signals
        
        # Find the signal with the most recent timestamp
        latest_signal = max(signals, key=lambda s: s.timestamp if hasattr(s, 'timestamp') else 0)
        return [latest_signal]
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get comprehensive strategy information including parameters and their descriptions.
        
        Returns:
            Dict containing strategy name, parameters, descriptions, and trade type
        """
        return {
            "name": self.name,
            "params": self.params,
            "is_option_trade": self.is_option_trade,
            "param_descriptions": self.get_param_descriptions(),
            "required_columns": self.get_required_columns()
        }
    
    def get_param_descriptions(self) -> Dict[str, str]:
        """
        Get descriptions of all strategy parameters.
        Should be overridden by subclasses.
        
        Returns:
            Dict mapping parameter names to their descriptions
        """
        return {}
    
    def get_required_columns(self) -> List[str]:
        """
        Get list of required DataFrame columns for this strategy.
        Should be overridden by subclasses.
        
        Returns:
            List of required column names
        """
        return ["close"]