import unittest
import pandas as pd
import os
from trading_signals.strategies import SimpleMovingAverageStrategy, SimplePutCreditSpreadStrategy
from trading_signals.signals import Action, OptionType, CreditDebit


class TestStrategies(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Load mock data for testing"""
        cls.mock_data_dir = os.path.join(os.path.dirname(__file__), '../mockData')
        
        # Load different types of data
        cls.trending_data = pd.read_csv(os.path.join(cls.mock_data_dir, 'trending_stock.csv'))
        cls.trending_data.ticker = 'AAPL'
        
        cls.sideways_data = pd.read_csv(os.path.join(cls.mock_data_dir, 'sideways_stock.csv'))
        cls.sideways_data.ticker = 'MSFT'
        
        cls.volatile_data = pd.read_csv(os.path.join(cls.mock_data_dir, 'volatile_stock.csv'))
        cls.volatile_data.ticker = 'TSLA'
        
        cls.small_data = pd.read_csv(os.path.join(cls.mock_data_dir, 'small_dataset.csv'))
        cls.small_data.ticker = 'GOOGL'
    
    def test_sma_strategy_initialization(self):
        """Test SMA strategy initialization with default parameters"""
        strategy = SimpleMovingAverageStrategy()
        
        self.assertEqual(strategy.name, "Simple Moving Average Crossover")
        self.assertFalse(strategy.is_option_trade)
        self.assertEqual(strategy.params["short_window"], 20)
        self.assertEqual(strategy.params["long_window"], 50)
    
    def test_sma_strategy_custom_parameters(self):
        """Test SMA strategy with custom parameters"""
        strategy = SimpleMovingAverageStrategy(short_window=10, long_window=30)
        
        self.assertEqual(strategy.params["short_window"], 10)
        self.assertEqual(strategy.params["long_window"], 30)
    
    def test_sma_strategy_trending_data(self):
        """Test SMA strategy on trending data"""
        strategy = SimpleMovingAverageStrategy(short_window=10, long_window=20)
        signals = strategy.generate_signals(self.trending_data)
        
        self.assertIsInstance(signals, list)
        
        # Should generate some signals on trending data
        self.assertGreater(len(signals), 0)
        
        # Check signal properties
        for signal in signals:
            self.assertEqual(signal.ticker, 'AAPL')
            self.assertIn(signal.action, [Action.BUY, Action.SELL])
            self.assertIsInstance(signal.price, float)
            self.assertGreater(signal.price, 0)
    
    def test_sma_strategy_sideways_data(self):
        """Test SMA strategy on sideways data"""
        strategy = SimpleMovingAverageStrategy(short_window=5, long_window=15)
        signals = strategy.generate_signals(self.sideways_data)
        
        # Sideways data might generate fewer signals
        self.assertIsInstance(signals, list)
        
        for signal in signals:
            self.assertEqual(signal.ticker, 'MSFT')
            self.assertIn(signal.action, [Action.BUY, Action.SELL])
    
    def test_sma_strategy_insufficient_data(self):
        """Test SMA strategy with insufficient data"""
        strategy = SimpleMovingAverageStrategy(short_window=10, long_window=20)
        
        # Create data with only 15 rows (less than long_window)
        small_df = self.trending_data.head(15).copy()
        small_df.ticker = 'TEST'
        
        signals = strategy.generate_signals(small_df)
        
        # Should return empty list or handle gracefully
        self.assertIsInstance(signals, list)
    
    def test_sma_strategy_missing_column(self):
        """Test SMA strategy with missing close column"""
        strategy = SimpleMovingAverageStrategy()
        
        df_no_close = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [101, 102, 103],
            'low': [99, 100, 101]
        })
        
        with self.assertRaises(ValueError):
            strategy.generate_signals(df_no_close)
    
    def test_put_credit_spread_initialization(self):
        """Test Put Credit Spread strategy initialization"""
        strategy = SimplePutCreditSpreadStrategy()
        
        self.assertEqual(strategy.name, "Simple Put Credit Spread")
        self.assertTrue(strategy.is_option_trade)
        self.assertEqual(strategy.params["rsi_oversold"], 30)
        self.assertEqual(strategy.params["strike_offset"], 0.05)
        self.assertEqual(strategy.params["days_to_expiration"], 30)
    
    def test_put_credit_spread_custom_parameters(self):
        """Test Put Credit Spread with custom parameters"""
        strategy = SimplePutCreditSpreadStrategy(
            rsi_oversold=25,
            strike_offset=0.03,
            days_to_expiration=45
        )
        
        self.assertEqual(strategy.params["rsi_oversold"], 25)
        self.assertEqual(strategy.params["strike_offset"], 0.03)
        self.assertEqual(strategy.params["days_to_expiration"], 45)
    
    def test_put_credit_spread_volatile_data(self):
        """Test Put Credit Spread on volatile data"""
        strategy = SimplePutCreditSpreadStrategy(rsi_oversold=35)
        signals = strategy.generate_signals(self.volatile_data)
        
        self.assertIsInstance(signals, list)
        
        # Volatile data should generate some oversold signals
        if len(signals) > 0:
            for signal in signals:
                self.assertEqual(signal.ticker, 'TSLA')
                self.assertEqual(signal.action, Action.SELL)
                self.assertEqual(signal.option_type, OptionType.PUT)
                self.assertEqual(signal.credit_debit, CreditDebit.CREDIT)
                self.assertIsInstance(signal.strike, float)
                self.assertGreater(signal.strike, 0)
                self.assertIsInstance(signal.expiration, str)
    
    def test_put_credit_spread_trending_data(self):
        """Test Put Credit Spread on trending data"""
        strategy = SimplePutCreditSpreadStrategy(rsi_oversold=20)
        signals = strategy.generate_signals(self.trending_data)
        
        # Trending up data might generate fewer oversold signals
        self.assertIsInstance(signals, list)
        
        for signal in signals:
            self.assertEqual(signal.ticker, 'AAPL')
            self.assertEqual(signal.option_type, OptionType.PUT)
    
    def test_strategy_info_methods(self):
        """Test get_strategy_info methods"""
        sma_strategy = SimpleMovingAverageStrategy(short_window=5, long_window=10)
        sma_info = sma_strategy.get_strategy_info()
        
        self.assertIn('name', sma_info)
        self.assertIn('params', sma_info)
        self.assertIn('is_option_trade', sma_info)
        self.assertEqual(sma_info['is_option_trade'], False)
        
        option_strategy = SimplePutCreditSpreadStrategy()
        option_info = option_strategy.get_strategy_info()
        
        self.assertEqual(option_info['is_option_trade'], True)
    
    def test_rsi_calculation(self):
        """Test RSI calculation in option strategy"""
        strategy = SimplePutCreditSpreadStrategy()
        
        # Create simple test data for RSI
        test_prices = pd.Series([100, 102, 101, 103, 102, 104, 103, 105, 104, 106])
        rsi = strategy._calculate_rsi(test_prices, window=5)
        
        # RSI should be a pandas Series
        self.assertIsInstance(rsi, pd.Series)
        
        # RSI values should be between 0 and 100 (where not NaN)
        valid_rsi = rsi.dropna()
        if len(valid_rsi) > 0:
            self.assertTrue(all(0 <= val <= 100 for val in valid_rsi))


if __name__ == '__main__':
    unittest.main()