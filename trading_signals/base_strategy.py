from abc import ABC, abstractmethod
from typing import Dict, Any, List, Union
import pandas as pd
from .signals import StockSignal, OptionSignal


class BaseStrategy(ABC):
    def __init__(self, name: str, params: Dict[str, Any], is_option_trade: bool = False):
        self.name = name
        self.params = params
        self.is_option_trade = is_option_trade
    
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