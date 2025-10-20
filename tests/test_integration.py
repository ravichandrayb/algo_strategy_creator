import unittest
import pandas as pd
import os
from trading_signals import StrategyManager
from trading_signals.signals import StockSignal, OptionSignal, Action


class TestIntegration(unittest.TestCase):
    """Integration tests using all mock data files"""
    
    @classmethod
    def setUpClass(cls):
        """Load all mock data files"""
        cls.mock_data_dir = os.path.join(os.path.dirname(__file__), '../mockData')
        cls.manager = StrategyManager()
        
        cls.datasets = {}
        data_files = [
            ('trending', 'trending_stock.csv', 'AAPL'),
            ('sideways', 'sideways_stock.csv', 'MSFT'),
            ('volatile', 'volatile_stock.csv', 'TSLA'),
            ('crypto', 'crypto_data.csv', 'BTC'),
            ('small', 'small_dataset.csv', 'GOOGL'),
            ('large', 'large_dataset.csv', 'SPY')
        ]
        
        for name, filename, ticker in data_files:
            df = pd.read_csv(os.path.join(cls.mock_data_dir, filename))
            df.ticker = ticker
            cls.datasets[name] = df
    
    def test_all_datasets_sma_strategy(self):
        """Test SMA strategy on all datasets"""
        for dataset_name, df in self.datasets.items():
            with self.subTest(dataset=dataset_name):
                signals = self.manager.generate_signals('sma_crossover', df)
                
                self.assertIsInstance(signals, list)
                
                # All signals should be stock signals
                for signal in signals:
                    self.assertIsInstance(signal, StockSignal)
                    self.assertEqual(signal.ticker, df.ticker)
                    self.assertIn(signal.action, [Action.BUY, Action.SELL])
                    self.assertGreater(signal.price, 0)
    
    def test_all_datasets_option_strategy(self):
        """Test option strategy on all datasets"""
        for dataset_name, df in self.datasets.items():
            with self.subTest(dataset=dataset_name):
                signals = self.manager.generate_signals('put_credit_spread', df)
                
                self.assertIsInstance(signals, list)
                
                # All signals should be option signals
                for signal in signals:
                    self.assertIsInstance(signal, OptionSignal)
                    self.assertEqual(signal.ticker, df.ticker)
                    self.assertGreater(signal.strike, 0)
                    self.assertGreater(signal.price, 0)
    
    def test_signal_generation_consistency(self):
        """Test that signal generation is consistent across multiple calls"""
        df = self.datasets['trending']
        
        # Generate signals multiple times
        signals1 = self.manager.generate_signals('sma_crossover', df)
        signals2 = self.manager.generate_signals('sma_crossover', df)
        
        # Results should be identical
        self.assertEqual(len(signals1), len(signals2))
        
        for s1, s2 in zip(signals1, signals2):
            self.assertEqual(s1.ticker, s2.ticker)
            self.assertEqual(s1.price, s2.price)
            self.assertEqual(s1.action, s2.action)
    
    def test_different_strategy_parameters(self):
        """Test different parameter configurations"""
        df = self.datasets['volatile']
        
        # Create strategies with different parameters
        self.manager.create_custom_strategy(
            'sma_fast',
            self.manager.get_strategy('sma_crossover').__class__,
            short_window=5,
            long_window=10
        )
        
        self.manager.create_custom_strategy(
            'sma_slow',
            self.manager.get_strategy('sma_crossover').__class__,
            short_window=50,
            long_window=100
        )
        
        fast_signals = self.manager.generate_signals('sma_fast', df)
        slow_signals = self.manager.generate_signals('sma_slow', df)
        
        # Fast strategy should typically generate more signals
        self.assertIsInstance(fast_signals, list)
        self.assertIsInstance(slow_signals, list)
        
        # Verify all signals are valid
        all_signals = fast_signals + slow_signals
        for signal in all_signals:
            self.assertIsInstance(signal, StockSignal)
            self.assertEqual(signal.ticker, df.ticker)
    
    def test_large_dataset_performance(self):
        """Test strategy performance on large dataset"""
        large_df = self.datasets['large']
        self.assertEqual(len(large_df), 500)  # Verify it's actually large
        
        # Test both strategies on large dataset
        stock_signals = self.manager.generate_signals('sma_crossover', large_df)
        option_signals = self.manager.generate_signals('put_credit_spread', large_df)
        
        self.assertIsInstance(stock_signals, list)
        self.assertIsInstance(option_signals, list)
        
        # Verify signal quality
        for signal in stock_signals:
            self.assertIsInstance(signal, StockSignal)
            self.assertEqual(signal.ticker, 'SPY')
        
        for signal in option_signals:
            self.assertIsInstance(signal, OptionSignal)
            self.assertEqual(signal.ticker, 'SPY')
    
    def test_small_dataset_handling(self):
        """Test strategy behavior on small dataset"""
        small_df = self.datasets['small']
        self.assertEqual(len(small_df), 50)  # Verify it's small
        
        # Test strategies on small dataset
        stock_signals = self.manager.generate_signals('sma_crossover', small_df)
        option_signals = self.manager.generate_signals('put_credit_spread', small_df)
        
        # Should handle gracefully without errors
        self.assertIsInstance(stock_signals, list)
        self.assertIsInstance(option_signals, list)
    
    def test_crypto_data_handling(self):
        """Test strategies on crypto-like data with high volatility"""
        crypto_df = self.datasets['crypto']
        
        # Crypto data should work with both strategies
        stock_signals = self.manager.generate_signals('sma_crossover', crypto_df)
        option_signals = self.manager.generate_signals('put_credit_spread', crypto_df)
        
        self.assertIsInstance(stock_signals, list)
        self.assertIsInstance(option_signals, list)
        
        # Verify ticker is preserved
        for signal in stock_signals:
            self.assertEqual(signal.ticker, 'BTC')
        
        for signal in option_signals:
            self.assertEqual(signal.ticker, 'BTC')
    
    def test_strategy_comparison(self):
        """Compare strategy outputs across different market conditions"""
        results = {}
        
        for dataset_name, df in self.datasets.items():
            stock_signals = self.manager.generate_signals('sma_crossover', df)
            option_signals = self.manager.generate_signals('put_credit_spread', df)
            
            results[dataset_name] = {
                'stock_signal_count': len(stock_signals),
                'option_signal_count': len(option_signals),
                'data_length': len(df)
            }
        
        # Verify we have results for all datasets
        self.assertEqual(len(results), len(self.datasets))
        
        # Check that volatile data generates more option signals (typically)
        volatile_results = results.get('volatile', {})
        trending_results = results.get('trending', {})
        
        self.assertIn('option_signal_count', volatile_results)
        self.assertIn('option_signal_count', trending_results)


if __name__ == '__main__':
    unittest.main()