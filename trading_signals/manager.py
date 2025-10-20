from typing import Dict, List, Union, Type
import pandas as pd
import sys
import os

# Handle both direct execution and package import
try:
    from .base_strategy import BaseStrategy
    from .signals import StockSignal, OptionSignal
    from .strategies import SimpleMovingAverageStrategy, SimplePutCreditSpreadStrategy
except ImportError:
    # Add parent directory to path for direct execution
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        from trading_signals.base_strategy import BaseStrategy
        from trading_signals.signals import StockSignal, OptionSignal
        from trading_signals.strategies import SimpleMovingAverageStrategy, SimplePutCreditSpreadStrategy
    except ImportError:
        from base_strategy import BaseStrategy
        from signals import StockSignal, OptionSignal
        from strategies import SimpleMovingAverageStrategy, SimplePutCreditSpreadStrategy


class StrategyManager:
    def __init__(self):
        self.strategies: Dict[str, BaseStrategy] = {}
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        self.register_strategy("sma_crossover", SimpleMovingAverageStrategy())
        self.register_strategy("put_credit_spread", SimplePutCreditSpreadStrategy())
    
    def register_strategy(self, name: str, strategy: BaseStrategy):
        self.strategies[name] = strategy
    
    def get_strategy(self, name: str) -> BaseStrategy:
        if name not in self.strategies:
            raise ValueError(f"Strategy '{name}' not found")
        return self.strategies[name]
    
    def list_strategies(self) -> List[Dict[str, any]]:
        """
        List all registered strategies with their detailed information.
        
        Returns:
            List of dicts containing strategy name and detailed info including parameters
        """
        return [
            {
                "name": name,
                "info": strategy.get_strategy_info()
            }
            for name, strategy in self.strategies.items()
        ]
    
    def get_strategy_parameters(self, strategy_name: str) -> Dict[str, any]:
        """
        Get parameter information for a specific strategy.
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            Dict containing parameter names, values, descriptions, and types
        """
        strategy = self.get_strategy(strategy_name)
        info = strategy.get_strategy_info()
        
        return {
            "strategy_name": strategy_name,
            "parameters": info["params"],
            "parameter_descriptions": info.get("param_descriptions", {}),
            "required_columns": info.get("required_columns", []),
            "is_option_trade": info["is_option_trade"]
        }
    
    def print_strategy_help(self, strategy_name: str = None):
        """
        Print detailed help information for strategies.
        
        Args:
            strategy_name: Optional specific strategy name. If None, prints all strategies.
        """
        if strategy_name:
            if strategy_name not in self.strategies:
                print(f"Strategy '{strategy_name}' not found.")
                return
            
            self._print_single_strategy_help(strategy_name)
        else:
            print("Available Trading Strategies:")
            print("=" * 50)
            for name in self.strategies.keys():
                self._print_single_strategy_help(name)
                print("-" * 50)
    
    def _print_single_strategy_help(self, strategy_name: str):
        """Print help for a single strategy"""
        strategy = self.strategies[strategy_name]
        info = strategy.get_strategy_info()
        
        print(f"\nStrategy: {strategy_name}")
        print(f"Name: {info['name']}")
        print(f"Type: {'Options' if info['is_option_trade'] else 'Stock'}")
        print(f"Required columns: {', '.join(info.get('required_columns', []))}")
        
        print("\nParameters:")
        params = info['params']
        descriptions = info.get('param_descriptions', {})
        
        for param_name, param_value in params.items():
            desc = descriptions.get(param_name, "No description available")
            print(f"  {param_name}: {param_value} ({type(param_value).__name__})")
            print(f"    {desc}")
        
        # Show docstring if available
        if hasattr(strategy.__class__, '__doc__') and strategy.__class__.__doc__:
            print(f"\nDescription:")
            print(f"  {strategy.__class__.__doc__.strip()}")
    
    def generate_signals(self, strategy_name: str, df: pd.DataFrame) -> List[Union[StockSignal, OptionSignal]]:
        strategy = self.get_strategy(strategy_name)
        return strategy.generate_signals(df)
    
    def create_custom_strategy(self, name: str, strategy_class: Type[BaseStrategy], **kwargs) -> BaseStrategy:
        strategy = strategy_class(**kwargs)
        self.register_strategy(name, strategy)
        return strategy