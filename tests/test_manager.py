import unittest
import pandas as pd
import os
from trading_signals import StrategyManager, SimpleMovingAverageStrategy, SimplePutCreditSpreadStrategy
from trading_signals.signals import StockSignal, OptionSignal


class TestStrategyManager(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = StrategyManager()
        
        # Load mock data
        mock_data_dir = os.path.join(os.path.dirname(__file__), '../mockData')
        self.test_data = pd.read_csv(os.path.join(mock_data_dir, 'trending_stock.csv'))
        self.test_data.ticker = 'TEST'
    
    def test_manager_initialization(self):
        """Test StrategyManager initialization"""
        self.assertIsInstance(self.manager, StrategyManager)
        self.assertIn('sma_crossover', self.manager.strategies)
        self.assertIn('put_credit_spread', self.manager.strategies)
    
    def test_list_strategies(self):
        """Test listing available strategies"""
        strategies = self.manager.list_strategies()
        
        self.assertIsInstance(strategies, list)
        self.assertEqual(len(strategies), 2)  # Default strategies
        
        # Check structure of strategy info
        for strategy in strategies:
            self.assertIn('name', strategy)
            self.assertIn('info', strategy)
            self.assertIn('name', strategy['info'])
            self.assertIn('params', strategy['info'])
            self.assertIn('is_option_trade', strategy['info'])
    
    def test_get_strategy(self):
        """Test getting specific strategies"""
        sma_strategy = self.manager.get_strategy('sma_crossover')
        self.assertIsInstance(sma_strategy, SimpleMovingAverageStrategy)
        
        option_strategy = self.manager.get_strategy('put_credit_spread')
        self.assertIsInstance(option_strategy, SimplePutCreditSpreadStrategy)
    
    def test_get_nonexistent_strategy(self):
        """Test getting a strategy that doesn't exist"""
        with self.assertRaises(ValueError) as context:
            self.manager.get_strategy('nonexistent_strategy')
        
        self.assertIn("Strategy 'nonexistent_strategy' not found", str(context.exception))
    
    def test_register_strategy(self):
        """Test registering a new strategy"""
        custom_strategy = SimpleMovingAverageStrategy(short_window=5, long_window=15)
        self.manager.register_strategy('custom_sma', custom_strategy)
        
        # Verify registration
        self.assertIn('custom_sma', self.manager.strategies)
        retrieved_strategy = self.manager.get_strategy('custom_sma')
        self.assertEqual(retrieved_strategy.params['short_window'], 5)
        self.assertEqual(retrieved_strategy.params['long_window'], 15)
    
    def test_generate_signals_stock(self):
        """Test generating stock signals"""
        signals = self.manager.generate_signals('sma_crossover', self.test_data)
        
        self.assertIsInstance(signals, list)
        
        # All signals should be StockSignal instances
        for signal in signals:
            self.assertIsInstance(signal, StockSignal)
            self.assertEqual(signal.ticker, 'TEST')
    
    def test_generate_signals_option(self):
        """Test generating option signals"""
        signals = self.manager.generate_signals('put_credit_spread', self.test_data)
        
        self.assertIsInstance(signals, list)
        
        # All signals should be OptionSignal instances
        for signal in signals:
            self.assertIsInstance(signal, OptionSignal)
            self.assertEqual(signal.ticker, 'TEST')
    
    def test_create_custom_strategy(self):
        """Test creating and registering custom strategy"""
        custom_strategy = self.manager.create_custom_strategy(
            'fast_sma',
            SimpleMovingAverageStrategy,
            short_window=3,
            long_window=7
        )
        
        # Verify strategy creation
        self.assertIsInstance(custom_strategy, SimpleMovingAverageStrategy)
        self.assertEqual(custom_strategy.params['short_window'], 3)
        self.assertEqual(custom_strategy.params['long_window'], 7)
        
        # Verify registration
        self.assertIn('fast_sma', self.manager.strategies)
        
        # Test signal generation with custom strategy
        signals = self.manager.generate_signals('fast_sma', self.test_data)
        self.assertIsInstance(signals, list)
    
    def test_strategy_info_consistency(self):
        """Test that strategy info is consistent across access methods"""
        # Get strategy info through manager
        strategies_list = self.manager.list_strategies()
        sma_info_from_list = next(s['info'] for s in strategies_list if s['name'] == 'sma_crossover')
        
        # Get strategy info directly
        sma_strategy = self.manager.get_strategy('sma_crossover')
        sma_info_direct = sma_strategy.get_strategy_info()
        
        # Should be identical
        self.assertEqual(sma_info_from_list, sma_info_direct)
    
    def test_multiple_strategy_instances(self):
        """Test that multiple instances of same strategy type work correctly"""
        self.manager.register_strategy('sma_short', SimpleMovingAverageStrategy(5, 10))
        self.manager.register_strategy('sma_long', SimpleMovingAverageStrategy(20, 50))
        
        short_signals = self.manager.generate_signals('sma_short', self.test_data)
        long_signals = self.manager.generate_signals('sma_long', self.test_data)
        
        # Different parameters should potentially generate different signals
        self.assertIsInstance(short_signals, list)
        self.assertIsInstance(long_signals, list)
        
        # Verify strategies have different parameters
        short_strategy = self.manager.get_strategy('sma_short')
        long_strategy = self.manager.get_strategy('sma_long')
        
        self.assertEqual(short_strategy.params['short_window'], 5)
        self.assertEqual(long_strategy.params['short_window'], 20)


if __name__ == '__main__':
    unittest.main()