"""
Parameter Discovery and Validation System

This module provides comprehensive parameter information for all strategies,
making it easy for users to understand what parameters are needed without
diving into source code.
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import inspect
from .manager import StrategyManager


@dataclass
class ParameterInfo:
    """Information about a strategy parameter"""
    name: str
    type: str
    default: Any
    required: bool
    description: str
    valid_range: Optional[str] = None
    examples: Optional[List[Any]] = None
    related_indicator: Optional[str] = None


@dataclass
class StrategyParameterGuide:
    """Complete parameter guide for a strategy"""
    strategy_name: str
    strategy_class_name: str
    description: str
    category: str  # 'stock', 'option_neutral', 'option_directional', etc.
    parameters: List[ParameterInfo]
    required_columns: List[str]
    example_usage: str
    market_conditions: str  # When to use this strategy


class ParameterDiscovery:
    """
    System for discovering and documenting strategy parameters
    """
    
    def __init__(self):
        self.manager = StrategyManager()
        self._parameter_database = self._build_parameter_database()
    
    def _build_parameter_database(self) -> Dict[str, StrategyParameterGuide]:
        """Build comprehensive parameter database for all strategies"""
        
        database = {}
        
        # Stock Strategies
        database['sma_crossover'] = StrategyParameterGuide(
            strategy_name='sma_crossover',
            strategy_class_name='SimpleMovingAverageStrategy',
            description='Moving Average Crossover strategy using two different period MAs',
            category='stock_trend',
            parameters=[
                ParameterInfo(
                    name='short_window',
                    type='int',
                    default=20,
                    required=False,
                    description='Period for short-term moving average',
                    valid_range='5-50 (typical), 1-100 (max)',
                    examples=[5, 10, 15, 20],
                    related_indicator='Simple Moving Average (SMA)'
                ),
                ParameterInfo(
                    name='long_window', 
                    type='int',
                    default=50,
                    required=False,
                    description='Period for long-term moving average',
                    valid_range='20-200 (typical), must be > short_window',
                    examples=[30, 50, 100, 200],
                    related_indicator='Simple Moving Average (SMA)'
                )
            ],
            required_columns=['close'],
            example_usage='SimpleMovingAverageStrategy(short_window=10, long_window=30)',
            market_conditions='Trending markets, avoid in sideways/choppy conditions'
        )
        
        # Option Strategies
        database['put_credit_spread'] = StrategyParameterGuide(
            strategy_name='put_credit_spread',
            strategy_class_name='SimplePutCreditSpreadStrategy', 
            description='Put Credit Spread using RSI oversold conditions',
            category='option_credit',
            parameters=[
                ParameterInfo(
                    name='rsi_oversold',
                    type='float',
                    default=30,
                    required=False,
                    description='RSI threshold below which stock is considered oversold',
                    valid_range='10-50 (typical), 0-100 (absolute)',
                    examples=[20, 25, 30, 35],
                    related_indicator='Relative Strength Index (RSI)'
                ),
                ParameterInfo(
                    name='strike_offset',
                    type='float', 
                    default=0.05,
                    required=False,
                    description='Percentage below current price to set put strike',
                    valid_range='0.01-0.20 (1%-20%)',
                    examples=[0.02, 0.03, 0.05, 0.10],
                    related_indicator='Strike Selection'
                ),
                ParameterInfo(
                    name='days_to_expiration',
                    type='int',
                    default=30,
                    required=False,
                    description='Number of days until option expiration',
                    valid_range='7-90 (typical), 1-365 (max)',
                    examples=[15, 30, 45, 60],
                    related_indicator='Time to Expiration'
                )
            ],
            required_columns=['close'],
            example_usage='SimplePutCreditSpreadStrategy(rsi_oversold=25, strike_offset=0.03, days_to_expiration=45)',
            market_conditions='Oversold conditions, expect bounce or consolidation'
        )
        
        return database
    
    def get_strategy_parameters(self, strategy_name: str) -> Optional[StrategyParameterGuide]:
        """Get complete parameter guide for a strategy"""
        return self._parameter_database.get(strategy_name)
    
    def list_all_parameters(self) -> Dict[str, StrategyParameterGuide]:
        """Get parameter guides for all strategies"""
        return self._parameter_database.copy()
    
    def get_parameters_by_indicator(self, indicator: str) -> List[ParameterInfo]:
        """Find all parameters that use a specific technical indicator"""
        results = []
        for guide in self._parameter_database.values():
            for param in guide.parameters:
                if param.related_indicator and indicator.lower() in param.related_indicator.lower():
                    results.append(param)
        return results
    
    def get_strategies_by_category(self, category: str) -> List[str]:
        """Get all strategies in a specific category"""
        return [name for name, guide in self._parameter_database.items() 
                if guide.category == category]
    
    def validate_parameters(self, strategy_name: str, **kwargs) -> Dict[str, Any]:
        """
        Validate parameters for a strategy and provide suggestions
        
        Returns:
            Dict with validation results, warnings, and suggestions
        """
        guide = self.get_strategy_parameters(strategy_name)
        if not guide:
            return {'error': f'Strategy {strategy_name} not found in parameter database'}
        
        result = {
            'valid': True,
            'warnings': [],
            'suggestions': [],
            'corrected_params': {},
            'missing_required': []
        }
        
        # Check each provided parameter
        param_names = {p.name for p in guide.parameters}
        
        for param_name, value in kwargs.items():
            if param_name not in param_names:
                result['warnings'].append(f"Unknown parameter '{param_name}' for {strategy_name}")
                continue
            
            param_info = next(p for p in guide.parameters if p.name == param_name)
            
            # Type checking
            expected_type = eval(param_info.type) if param_info.type in ['int', 'float', 'str', 'bool'] else str
            if not isinstance(value, expected_type):
                try:
                    corrected_value = expected_type(value)
                    result['corrected_params'][param_name] = corrected_value
                    result['suggestions'].append(f"Converting {param_name} from {type(value).__name__} to {param_info.type}")
                except (ValueError, TypeError):
                    result['valid'] = False
                    result['warnings'].append(f"Cannot convert {param_name}={value} to {param_info.type}")
            
            # Range validation (basic)
            if param_info.valid_range and isinstance(value, (int, float)):
                if 'typical' in param_info.valid_range:
                    range_part = param_info.valid_range.split('(typical)')[0].strip()
                    if '-' in range_part:
                        min_val, max_val = map(float, range_part.split('-'))
                        if not (min_val <= value <= max_val):
                            result['suggestions'].append(f"{param_name}={value} is outside typical range {range_part}")
        
        # Check for required parameters
        required_params = [p.name for p in guide.parameters if p.required]
        provided_params = set(kwargs.keys())
        missing = set(required_params) - provided_params
        if missing:
            result['missing_required'] = list(missing)
            result['valid'] = False
        
        return result
    
    def suggest_parameters_for_market(self, market_condition: str) -> List[str]:
        """Suggest strategies suitable for given market condition"""
        suggestions = []
        condition_lower = market_condition.lower()
        
        for name, guide in self._parameter_database.items():
            if condition_lower in guide.market_conditions.lower():
                suggestions.append(name)
        
        return suggestions
    
    def print_parameter_guide(self, strategy_name: str = None):
        """Print comprehensive parameter guide"""
        if strategy_name:
            guide = self.get_strategy_parameters(strategy_name)
            if guide:
                self._print_single_strategy_guide(guide)
            else:
                print(f"Strategy '{strategy_name}' not found in parameter database")
        else:
            print("=" * 80)
            print("COMPLETE PARAMETER GUIDE")
            print("=" * 80)
            
            categories = {}
            for name, guide in self._parameter_database.items():
                if guide.category not in categories:
                    categories[guide.category] = []
                categories[guide.category].append(guide)
            
            for category, guides in categories.items():
                print(f"\n📊 {category.upper()} STRATEGIES")
                print("-" * 50)
                for guide in guides:
                    self._print_single_strategy_guide(guide, brief=True)
                    print("-" * 30)
    
    def _print_single_strategy_guide(self, guide: StrategyParameterGuide, brief: bool = False):
        """Print guide for a single strategy"""
        print(f"\n🎯 {guide.strategy_name} ({guide.strategy_class_name})")
        print(f"Description: {guide.description}")
        print(f"Category: {guide.category}")
        print(f"Required columns: {', '.join(guide.required_columns)}")
        print(f"Market conditions: {guide.market_conditions}")
        
        if not brief:
            print(f"\nParameters:")
            for param in guide.parameters:
                required_text = "REQUIRED" if param.required else f"Optional (default: {param.default})"
                print(f"  📋 {param.name} ({param.type}) - {required_text}")
                print(f"     {param.description}")
                if param.valid_range:
                    print(f"     Valid range: {param.valid_range}")
                if param.examples:
                    print(f"     Examples: {param.examples}")
                if param.related_indicator:
                    print(f"     Indicator: {param.related_indicator}")
                print()
            
            print(f"Example usage:")
            print(f"  {guide.example_usage}")
        else:
            param_summary = [f"{p.name}({p.type})" for p in guide.parameters]
            print(f"Parameters: {', '.join(param_summary)}")
    
    def generate_parameter_cheatsheet(self) -> str:
        """Generate a quick reference cheatsheet"""
        cheatsheet = []
        cheatsheet.append("=" * 60)
        cheatsheet.append("TRADING SIGNALS PARAMETER CHEATSHEET")
        cheatsheet.append("=" * 60)
        
        for name, guide in self._parameter_database.items():
            cheatsheet.append(f"\n{name}:")
            for param in guide.parameters:
                default_text = f" (default: {param.default})" if not param.required else " (REQUIRED)"
                cheatsheet.append(f"  {param.name}: {param.type}{default_text}")
                if param.valid_range:
                    cheatsheet.append(f"    Range: {param.valid_range}")
        
        return "\n".join(cheatsheet)


# Convenience functions
def get_parameter_info(strategy_name: str) -> Optional[StrategyParameterGuide]:
    """Get parameter information for a strategy"""
    discovery = ParameterDiscovery()
    return discovery.get_strategy_parameters(strategy_name)


def validate_strategy_params(strategy_name: str, **kwargs) -> Dict[str, Any]:
    """Validate parameters for a strategy"""
    discovery = ParameterDiscovery()
    return discovery.validate_parameters(strategy_name, **kwargs)


def print_all_parameters():
    """Print parameter guide for all strategies"""
    discovery = ParameterDiscovery()
    discovery.print_parameter_guide()


def print_strategy_parameters(strategy_name: str):
    """Print parameter guide for a specific strategy"""
    discovery = ParameterDiscovery()
    discovery.print_parameter_guide(strategy_name)


def get_parameter_cheatsheet() -> str:
    """Get quick parameter reference"""
    discovery = ParameterDiscovery()
    return discovery.generate_parameter_cheatsheet()


def find_strategies_by_indicator(indicator: str) -> List[str]:
    """Find strategies that use a specific indicator (RSI, ADX, etc.)"""
    discovery = ParameterDiscovery()
    params = discovery.get_parameters_by_indicator(indicator)
    
    strategies = set()
    for name, guide in discovery.list_all_parameters().items():
        for param in guide.parameters:
            if param in params:
                strategies.add(name)
    
    return list(strategies)