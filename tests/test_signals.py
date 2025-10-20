import unittest
from datetime import datetime
from trading_signals.signals import StockSignal, OptionSignal, Action, OptionType, CreditDebit


class TestSignals(unittest.TestCase):
    
    def test_stock_signal_creation(self):
        """Test StockSignal creation and attributes"""
        signal = StockSignal(
            ticker="AAPL",
            price=150.50,
            action=Action.BUY
        )
        
        self.assertEqual(signal.ticker, "AAPL")
        self.assertEqual(signal.price, 150.50)
        self.assertEqual(signal.action, Action.BUY)
        self.assertIsInstance(signal.timestamp, datetime)
    
    def test_stock_signal_with_timestamp(self):
        """Test StockSignal with custom timestamp"""
        custom_time = datetime(2023, 6, 15, 10, 30, 0)
        signal = StockSignal(
            ticker="MSFT",
            price=280.75,
            action=Action.SELL,
            timestamp=custom_time
        )
        
        self.assertEqual(signal.timestamp, custom_time)
    
    def test_option_signal_creation(self):
        """Test OptionSignal creation and attributes"""
        signal = OptionSignal(
            ticker="TSLA",
            strike=200.0,
            option_type=OptionType.PUT,
            price=5.50,
            action=Action.SELL,
            expiration="2023-12-15",
            credit_debit=CreditDebit.CREDIT
        )
        
        self.assertEqual(signal.ticker, "TSLA")
        self.assertEqual(signal.strike, 200.0)
        self.assertEqual(signal.option_type, OptionType.PUT)
        self.assertEqual(signal.price, 5.50)
        self.assertEqual(signal.action, Action.SELL)
        self.assertEqual(signal.expiration, "2023-12-15")
        self.assertEqual(signal.credit_debit, CreditDebit.CREDIT)
        self.assertIsInstance(signal.timestamp, datetime)
    
    def test_action_enum(self):
        """Test Action enum values"""
        self.assertEqual(Action.BUY.value, "BUY")
        self.assertEqual(Action.SELL.value, "SELL")
    
    def test_option_type_enum(self):
        """Test OptionType enum values"""
        self.assertEqual(OptionType.CALL.value, "CALL")
        self.assertEqual(OptionType.PUT.value, "PUT")
    
    def test_credit_debit_enum(self):
        """Test CreditDebit enum values"""
        self.assertEqual(CreditDebit.CREDIT.value, "CREDIT")
        self.assertEqual(CreditDebit.DEBIT.value, "DEBIT")


if __name__ == '__main__':
    unittest.main()