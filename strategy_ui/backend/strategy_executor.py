"""
Strategy Executor - Handles live strategy execution with real order placement
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import logging
from pathlib import Path
import sys
import json
from threading import Lock

# Add parent directory to path to import trading_signals
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from kite_utils import KiteDataFetcher
from kiteconnect import KiteConnect
from trading_signals.base_strategy import BaseStrategy
from trading_signals.signals import StockSignal, OptionSignal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('strategy_executor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class StrategyExecutor:
    """
    Manages live execution of trading strategies
    - Fetches live data using KiteDataFetcher
    - Generates signals using strategy logic
    - Places real orders using KiteConnect
    - Tracks signals, orders, and P&L
    """
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.running_strategies: Dict[str, Dict[str, Any]] = {}
        self.data_fetcher = None
        self.kite_client = None
        self.lock = Lock()
        
        # History tracking
        self.signal_history: Dict[str, List[Dict]] = {}  # strategy_id -> list of signals
        self.order_history: Dict[str, List[Dict]] = {}   # strategy_id -> list of orders
        self.execution_logs: Dict[str, List[Dict]] = {}  # strategy_id -> list of execution logs
        
        # Initialize Kite clients
        self._initialize_kite_clients()
        
    def _initialize_kite_clients(self):
        """Initialize KiteDataFetcher and KiteConnect clients"""
        try:
            self.data_fetcher = KiteDataFetcher()
            logger.info("KiteDataFetcher initialized successfully")
            
            # Initialize KiteConnect for order placement
            # Get credentials from environment
            import os
            from dotenv import load_dotenv
            load_dotenv()
            
            api_key = os.getenv('KITE_API_KEY') or os.getenv('API_KEY')
            access_token = os.getenv('KITE_ACCESS_TOKEN') or os.getenv('ACCESS_TOKEN')
            
            if api_key and access_token:
                self.kite_client = KiteConnect(api_key=api_key)
                self.kite_client.set_access_token(access_token)
                logger.info("KiteConnect client initialized successfully for order placement")
            else:
                logger.warning("API key or access token not found in environment. Order placement will fail.")
                
        except Exception as e:
            logger.error(f"Failed to initialize Kite clients: {str(e)}")
    
    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Strategy executor scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Strategy executor scheduler stopped")
    
    def deploy_strategy(
        self,
        strategy_id: str,
        strategy_instance: BaseStrategy,
        symbol: str,
        interval: str = '15minute',
        parameters: Dict[str, Any] = None
    ):
        """
        Deploy a strategy for live execution
        
        Args:
            strategy_id: Unique identifier for the strategy
            strategy_instance: Instance of the strategy class
            symbol: Trading symbol (e.g., 'NIFTY50', 'BANKNIFTY')
            interval: Data interval ('15minute', '5minute', '30minute', 'day')
            parameters: Strategy parameters
        """
        with self.lock:
            if strategy_id in self.running_strategies:
                logger.warning(f"Strategy {strategy_id} is already deployed")
                return False
            
            # Parse interval to get execution frequency
            interval_minutes = self._parse_interval(interval)
            
            # Store strategy info
            self.running_strategies[strategy_id] = {
                'instance': strategy_instance,
                'symbol': symbol,
                'interval': interval,
                'interval_minutes': interval_minutes,
                'parameters': parameters or {},
                'deployed_at': datetime.now().isoformat(),
                'status': 'running',
                'last_execution': None,
                'execution_count': 0,
                'signal_count': 0,
                'order_count': 0
            }
            
            # Initialize history lists
            self.signal_history[strategy_id] = []
            self.order_history[strategy_id] = []
            self.execution_logs[strategy_id] = []
            
            # Schedule the strategy execution
            job_id = f"strategy_{strategy_id}"
            self.scheduler.add_job(
                func=self._execute_strategy,
                trigger=IntervalTrigger(minutes=interval_minutes),
                args=[strategy_id],
                id=job_id,
                name=f"Execute {strategy_instance.name}",
                replace_existing=True,
                next_run_time=datetime.now()  # Run immediately on deployment
            )
            
            logger.info(f"Strategy {strategy_id} deployed successfully. Will run every {interval_minutes} minutes.")
            return True
    
    def stop_strategy(self, strategy_id: str):
        """Stop a running strategy"""
        with self.lock:
            if strategy_id not in self.running_strategies:
                logger.warning(f"Strategy {strategy_id} is not running")
                return False
            
            # Remove scheduled job
            job_id = f"strategy_{strategy_id}"
            try:
                self.scheduler.remove_job(job_id)
            except Exception as e:
                logger.error(f"Error removing job {job_id}: {str(e)}")
            
            # Remove from running strategies
            strategy_info = self.running_strategies.pop(strategy_id)
            logger.info(f"Strategy {strategy_id} stopped successfully")
            return True
    
    def _parse_interval(self, interval: str) -> int:
        """Parse interval string to minutes"""
        interval_map = {
            'minute': 1,
            '3minute': 3,
            '5minute': 5,
            '10minute': 10,
            '15minute': 15,
            '30minute': 30,
            '60minute': 60,
            'day': 1440  # Run once per day
        }
        return interval_map.get(interval, 15)  # Default to 15 minutes
    
    def _execute_strategy(self, strategy_id: str):
        """
        Execute a single strategy iteration
        1. Fetch latest data
        2. Generate signals
        3. Place orders for signals
        4. Update tracking
        """
        try:
            strategy_info = self.running_strategies.get(strategy_id)
            if not strategy_info:
                logger.warning(f"Strategy {strategy_id} not found in running strategies")
                return
            
            execution_start = datetime.now()
            logger.info(f"Executing strategy {strategy_id} at {execution_start}")
            
            # Log execution start
            exec_log = {
                'timestamp': execution_start.isoformat(),
                'status': 'started',
                'strategy_id': strategy_id
            }
            
            # 1. Fetch data
            symbol = strategy_info['symbol']
            interval = strategy_info['interval']
            
            logger.info(f"Fetching data for {symbol} with interval {interval}")
            df = self._fetch_data(symbol, interval)
            
            if df is None or df.empty:
                logger.error(f"No data fetched for {symbol}")
                exec_log['status'] = 'failed'
                exec_log['error'] = 'No data fetched'
                self.execution_logs[strategy_id].append(exec_log)
                return
            
            exec_log['data_points'] = len(df)
            logger.info(f"Fetched {len(df)} data points for {symbol}")
            
            # 2. Generate signals
            strategy_instance = strategy_info['instance']
            
            # Enable live trading mode to only get the latest signal
            strategy_instance.live_trading_mode = True
            
            signals = strategy_instance.generate_signals(df)
            
            # Apply live trading filter if strategy returns all historical signals
            if signals and len(signals) > 1:
                signals = strategy_instance.filter_signals_for_live_trading(signals)
                logger.info(f"Filtered to {len(signals)} most recent signal(s) for live trading")
            
            exec_log['signals_generated'] = len(signals) if signals else 0
            logger.info(f"Generated {len(signals) if signals else 0} signals")
            
            # 3. Process and place orders for signals
            orders_placed = 0
            if signals:
                for signal in signals:
                    signal_dict = self._signal_to_dict(signal)
                    signal_dict['strategy_id'] = strategy_id
                    signal_dict['timestamp'] = execution_start.isoformat()
                    
                    # Store signal
                    self.signal_history[strategy_id].append(signal_dict)
                    
                    # Place order
                    order_result = self._place_order(signal, symbol)
                    if order_result:
                        order_result['strategy_id'] = strategy_id
                        order_result['signal'] = signal_dict
                        self.order_history[strategy_id].append(order_result)
                        orders_placed += 1
            
            exec_log['orders_placed'] = orders_placed
            
            # 4. Update strategy info
            with self.lock:
                strategy_info['last_execution'] = execution_start.isoformat()
                strategy_info['execution_count'] += 1
                strategy_info['signal_count'] += len(signals) if signals else 0
                strategy_info['order_count'] += orders_placed
            
            # Log execution completion
            exec_log['status'] = 'completed'
            exec_log['duration_seconds'] = (datetime.now() - execution_start).total_seconds()
            self.execution_logs[strategy_id].append(exec_log)
            
            logger.info(f"Strategy {strategy_id} execution completed. Signals: {len(signals) if signals else 0}, Orders: {orders_placed}")
            
        except Exception as e:
            logger.error(f"Error executing strategy {strategy_id}: {str(e)}", exc_info=True)
            exec_log = {
                'timestamp': datetime.now().isoformat(),
                'status': 'error',
                'strategy_id': strategy_id,
                'error': str(e)
            }
            self.execution_logs[strategy_id].append(exec_log)
    
    def _fetch_data(self, symbol: str, interval: str, days: int = 30) -> Optional[pd.DataFrame]:
        """Fetch historical data for the symbol"""
        try:
            if not self.data_fetcher:
                logger.error("KiteDataFetcher not initialized")
                return None
            
            df = self.data_fetcher.fetch_historical_data(
                symbol=symbol,
                days=days,
                interval=interval
            )
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return None
    
    def _signal_to_dict(self, signal) -> Dict[str, Any]:
        """Convert signal object to dictionary"""
        # Handle both signal_type (old) and action (new) attributes
        signal_type = None
        if hasattr(signal, 'action'):
            signal_type = signal.action.value if hasattr(signal.action, 'value') else str(signal.action)
        elif hasattr(signal, 'signal_type'):
            signal_type = signal.signal_type.value if hasattr(signal.signal_type, 'value') else str(signal.signal_type)
        
        signal_dict = {
            'type': signal_type,
            'ticker': signal.ticker if hasattr(signal, 'ticker') else None,
            'timestamp': signal.timestamp.isoformat() if hasattr(signal.timestamp, 'isoformat') else str(signal.timestamp),
            'price': float(signal.price) if hasattr(signal, 'price') else None,
            'stop_loss': float(signal.stop_loss) if hasattr(signal, 'stop_loss') else None,
            'target': float(signal.target) if hasattr(signal, 'target') else None,
            'reason': signal.reason if hasattr(signal, 'reason') else None
        }
        
        # Add option-specific fields if it's an OptionSignal
        if isinstance(signal, OptionSignal):
            signal_dict.update({
                'option_type': signal.option_type if hasattr(signal, 'option_type') else None,
                'strike': float(signal.strike) if hasattr(signal, 'strike') else None,
                'expiry': signal.expiry.isoformat() if hasattr(signal, 'expiry') and signal.expiry else None,
                'quantity': int(signal.quantity) if hasattr(signal, 'quantity') else None
            })
        
        return signal_dict
    
    def _place_order(self, signal, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Place order based on signal
        
        Returns:
            Dict with order details if successful, None otherwise
        """
        try:
            if not self.kite_client:
                logger.error("KiteConnect client not initialized. Cannot place order.")
                return None
            
            # Determine order parameters based on signal - handle both action and signal_type
            if hasattr(signal, 'action'):
                signal_type = signal.action.value if hasattr(signal.action, 'value') else str(signal.action)
            elif hasattr(signal, 'signal_type'):
                signal_type = signal.signal_type.value if hasattr(signal.signal_type, 'value') else str(signal.signal_type)
            else:
                logger.warning("Signal has no action or signal_type attribute")
                return None
            
            if signal_type.upper() == 'BUY':
                transaction_type = self.kite_client.TRANSACTION_TYPE_BUY
            elif signal_type.upper() == 'SELL':
                transaction_type = self.kite_client.TRANSACTION_TYPE_SELL
            else:
                logger.warning(f"Unknown signal type: {signal_type}")
                return None
            
            # Determine quantity (default to 1 lot for options, can be customized)
            quantity = getattr(signal, 'quantity', 1)
            
            # Determine trading symbol
            if isinstance(signal, OptionSignal):
                # For options, construct the trading symbol
                # Format: SYMBOL[EXPIRY][STRIKE][CE/PE]
                # This is a simplified version, actual format depends on exchange
                trading_symbol = f"{symbol}"  # Simplified for now
            else:
                trading_symbol = symbol
            
            # Place market order
            order_params = {
                'exchange': self.kite_client.EXCHANGE_NSE,
                'tradingsymbol': trading_symbol,
                'transaction_type': transaction_type,
                'quantity': quantity,
                'order_type': self.kite_client.ORDER_TYPE_MARKET,
                'product': self.kite_client.PRODUCT_MIS,  # Intraday
                'variety': self.kite_client.VARIETY_REGULAR
            }
            
            logger.info(f"Placing order: {order_params}")
            order_id = self.kite_client.place_order(**order_params)
            
            logger.info(f"Order placed successfully. Order ID: {order_id}")
            
            return {
                'order_id': order_id,
                'timestamp': datetime.now().isoformat(),
                'symbol': trading_symbol,
                'transaction_type': transaction_type,
                'quantity': quantity,
                'order_type': 'MARKET',
                'status': 'placed',
                'params': order_params
            }
            
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}", exc_info=True)
            return {
                'timestamp': datetime.now().isoformat(),
                'status': 'failed',
                'error': str(e)
            }
    
    def get_strategy_info(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed info about a running strategy"""
        if strategy_id not in self.running_strategies:
            return None
        
        info = self.running_strategies[strategy_id].copy()
        # Remove instance object for JSON serialization
        info.pop('instance', None)
        
        # Add history counts
        info['total_signals'] = len(self.signal_history.get(strategy_id, []))
        info['total_orders'] = len(self.order_history.get(strategy_id, []))
        info['total_executions'] = len(self.execution_logs.get(strategy_id, []))
        
        return info
    
    def get_signal_history(self, strategy_id: str, limit: int = 50) -> List[Dict]:
        """Get recent signal history for a strategy"""
        if strategy_id not in self.signal_history:
            return []
        return self.signal_history[strategy_id][-limit:]
    
    def get_order_history(self, strategy_id: str, limit: int = 50) -> List[Dict]:
        """Get recent order history for a strategy"""
        if strategy_id not in self.order_history:
            return []
        return self.order_history[strategy_id][-limit:]
    
    def get_execution_logs(self, strategy_id: str, limit: int = 50) -> List[Dict]:
        """Get recent execution logs for a strategy"""
        if strategy_id not in self.execution_logs:
            return []
        return self.execution_logs[strategy_id][-limit:]
    
    def get_all_running_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Get info about all running strategies"""
        result = {}
        for strategy_id in self.running_strategies.keys():
            result[strategy_id] = self.get_strategy_info(strategy_id)
        return result


# Global executor instance
executor = StrategyExecutor()
