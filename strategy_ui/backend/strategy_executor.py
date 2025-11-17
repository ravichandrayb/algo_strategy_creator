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
        
        # Position tracking - stores current open positions for each strategy
        self.open_positions: Dict[str, List[Dict]] = {}  # strategy_id -> list of open positions
        # Each position: {'symbol': str, 'quantity': int, 'side': 'BUY'/'SELL', 'order_id': str, 'timestamp': datetime}
        
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
        """Stop a running strategy and close all open positions"""
        with self.lock:
            if strategy_id not in self.running_strategies:
                logger.warning(f"Strategy {strategy_id} is not running")
                return False
            
            # Close all open positions for this strategy
            if strategy_id in self.open_positions and self.open_positions[strategy_id]:
                logger.info(f"Closing {len(self.open_positions[strategy_id])} open position(s) for {strategy_id}")
                positions_to_close = self.open_positions[strategy_id].copy()
                for position in positions_to_close:
                    self._close_position(strategy_id, position)
            
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
            
            # If no new signals, just log and return (no action needed)
            if not signals or len(signals) == 0:
                logger.info(f"No new signals generated for {strategy_id}. Positions remain unchanged.")
                exec_log['status'] = 'completed'
                exec_log['orders_placed'] = 0
                exec_log['positions_closed'] = 0
                exec_log['duration_seconds'] = (datetime.now() - execution_start).total_seconds()
                self.execution_logs[strategy_id].append(exec_log)
                
                # Update execution count
                with self.lock:
                    strategy_info['last_execution'] = execution_start.isoformat()
                    strategy_info['execution_count'] += 1
                return
            
            # 3. Check if we need to close existing positions (signal reversal)
            positions_closed = 0
            if signals and strategy_id in self.open_positions and self.open_positions[strategy_id]:
                # Get the new signal direction
                new_signal = signals[0]  # Primary signal (futures)
                new_direction = getattr(new_signal, 'action', None)
                
                if new_direction:
                    new_direction_str = new_direction.value if hasattr(new_direction, 'value') else str(new_direction)
                    
                    # Check if any existing position is opposite to new signal
                    existing_positions = self.open_positions[strategy_id].copy()
                    for position in existing_positions:
                        if position['side'] != new_direction_str:
                            logger.info(f"Signal reversed! Closing {position['side']} position on {position['symbol']}")
                            # Close the position
                            close_result = self._close_position(strategy_id, position)
                            if close_result:
                                positions_closed += 1
            
            exec_log['positions_closed'] = positions_closed
            
            # 4. Process and place orders for new signals
            orders_placed = 0
            if signals:
                for signal in signals:
                    signal_dict = self._signal_to_dict(signal)
                    signal_dict['strategy_id'] = strategy_id
                    signal_dict['timestamp'] = execution_start.isoformat()
                    
                    # Store signal
                    self.signal_history[strategy_id].append(signal_dict)
                    
                    # Place order
                    order_result = self._place_order(signal, symbol, strategy_id)
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
            option_type_value = signal.option_type.value if hasattr(signal.option_type, 'value') else str(signal.option_type) if hasattr(signal, 'option_type') else None
            signal_dict.update({
                'option_type': option_type_value,
                'strike': float(signal.strike) if hasattr(signal, 'strike') else None,
                'expiration': signal.expiration if hasattr(signal, 'expiration') else None,
                'quantity': int(signal.quantity) if hasattr(signal, 'quantity') else None
            })
        
        return signal_dict
    
    def _get_option_trading_symbol(self, symbol: str, strike: float, option_type: str, expiry=None) -> str:
        """
        Get the option trading symbol.
        
        Args:
            symbol: Base symbol (e.g., 'NIFTY50', 'BANKNIFTY')
            strike: Strike price
            option_type: 'CALL' or 'PUT'
            expiry: Optional expiry date, if None will find nearest weekly expiry
            
        Returns:
            Trading symbol for the option (e.g., 'NIFTY2511925950CE')
        """
        try:
            from datetime import datetime, timedelta
            
            # Symbol mapping
            symbol_map = {
                'NIFTY50': 'NIFTY',
                'NIFTY': 'NIFTY',
                'BANKNIFTY': 'BANKNIFTY',
                'FINNIFTY': 'FINNIFTY',
                'MIDCPNIFTY': 'MIDCPNIFTY'
            }
            
            base_symbol = symbol_map.get(symbol, symbol)
            
            # Get the nearest expiry if not provided
            if expiry is None and self.kite_client:
                try:
                    instruments = self.kite_client.instruments("NFO")
                    
                    # Filter for options of the base symbol with the given strike
                    option_suffix = 'CE' if option_type.upper() == 'CALL' else 'PE'
                    options = [
                        inst for inst in instruments
                        if inst['name'] == base_symbol
                        and inst['instrument_type'] == option_suffix
                        and inst['strike'] == strike
                        and inst['expiry'] >= datetime.now().date()
                    ]
                    
                    if options:
                        # Sort by expiry and get the nearest one
                        options.sort(key=lambda x: x['expiry'])
                        nearest_option = options[0]
                        logger.info(f"Found option: {nearest_option['tradingsymbol']} (Strike: {strike}, Expiry: {nearest_option['expiry']})")
                        return nearest_option['tradingsymbol']
                    else:
                        logger.warning(f"No option found for {base_symbol} {strike} {option_type}")
                        # Fallback to manual construction
                        return self._construct_option_symbol(base_symbol, strike, option_type)
                        
                except Exception as e:
                    logger.error(f"Error fetching option instruments: {str(e)}")
                    return self._construct_option_symbol(base_symbol, strike, option_type)
            else:
                return self._construct_option_symbol(base_symbol, strike, option_type, expiry)
                
        except Exception as e:
            logger.error(f"Error getting option trading symbol: {str(e)}")
            return f"{symbol}{int(strike)}{option_type[0]}E"
    
    def _construct_option_symbol(self, base_symbol: str, strike: float, option_type: str, expiry=None) -> str:
        """
        Manually construct option trading symbol.
        Format: NIFTY2511925950CE (NIFTY 19 Nov 2025, 25950 Strike, Call)
        """
        from datetime import datetime, timedelta
        
        if expiry is None:
            # Find next Thursday (weekly expiry for NIFTY)
            today = datetime.now().date()
            days_ahead = 3 - today.weekday()  # Thursday = 3
            if days_ahead <= 0:
                days_ahead += 7
            expiry = today + timedelta(days=days_ahead)
        
        # Format: YY + M + DD (e.g., 25N19 for Nov 19, 2025)
        year = expiry.strftime('%y')
        month = expiry.strftime('%b').upper()[0]  # N for Nov, O for Oct, D for Dec
        day = expiry.strftime('%d')
        
        option_suffix = 'CE' if option_type.upper() == 'CALL' else 'PE'
        strike_int = int(strike)
        
        symbol = f"{base_symbol}{year}{month}{day}{strike_int}{option_suffix}"
        logger.info(f"Constructed option symbol: {symbol}")
        return symbol
    
    def _get_lot_size(self, trading_symbol: str, exchange: str) -> int:
        """
        Get the lot size for a trading symbol.
        
        Args:
            trading_symbol: Trading symbol (e.g., 'NIFTY25NOVFUT')
            exchange: Exchange (e.g., 'NFO', 'NSE')
            
        Returns:
            Lot size for the instrument
        """
        try:
            # Common lot sizes for Indian indices
            lot_size_map = {
                'NIFTY': 75,
                'BANKNIFTY': 30,
                'FINNIFTY': 40,
                'MIDCPNIFTY': 75
            }
            
            # Extract base symbol from trading symbol
            # e.g., NIFTY25NOVFUT -> NIFTY
            for base_symbol, lot_size in lot_size_map.items():
                if trading_symbol.startswith(base_symbol):
                    logger.info(f"Lot size for {trading_symbol}: {lot_size}")
                    return lot_size
            
            # If using Kite API, try to get lot size from instruments
            if self.kite_client and exchange == self.kite_client.EXCHANGE_NFO:
                try:
                    instruments = self.kite_client.instruments(exchange)
                    for inst in instruments:
                        if inst['tradingsymbol'] == trading_symbol:
                            lot_size = inst['lot_size']
                            logger.info(f"Lot size for {trading_symbol} from API: {lot_size}")
                            return lot_size
                except Exception as e:
                    logger.warning(f"Could not fetch lot size from API: {str(e)}")
            
            # Default to 1 for stocks
            return 1
            
        except Exception as e:
            logger.error(f"Error getting lot size: {str(e)}")
            return 1
    
    def _get_trading_symbol(self, symbol: str) -> str:
        """
        Get the actual trading symbol for order placement.
        
        Maps commonly used symbols to their actual trading symbols:
        - NIFTY50 -> NIFTY 50 (spot index for data, but we'll use futures)
        - BANKNIFTY -> BANK NIFTY
        
        For futures trading, we need the current month contract.
        For now, we'll search for the correct symbol using Kite API.
        
        Args:
            symbol: Input symbol (e.g., 'NIFTY50', 'BANKNIFTY')
            
        Returns:
            Valid trading symbol for order placement
        """
        try:
            # Symbol mapping for common indices
            symbol_map = {
                'NIFTY50': 'NIFTY',
                'NIFTY': 'NIFTY',
                'BANKNIFTY': 'BANKNIFTY',
                'FINNIFTY': 'FINNIFTY',
                'MIDCPNIFTY': 'MIDCPNIFTY'
            }
            
            base_symbol = symbol_map.get(symbol, symbol)
            
            # For indices, we need to find the current month futures contract
            # Use Kite's instruments list to find the correct symbol
            if self.kite_client:
                try:
                    # Search for the nearest expiry futures contract
                    from datetime import datetime
                    
                    # Get instruments list (cached in kite_client if available)
                    instruments = self.kite_client.instruments("NFO")
                    
                    # Filter for futures contracts of the base symbol
                    # Format is typically: NIFTY25DECFUT, BANKNIFTY25DECFUT, etc.
                    futures = [
                        inst for inst in instruments
                        if inst['name'] == base_symbol 
                        and inst['instrument_type'] == 'FUT'
                        and inst['expiry'] >= datetime.now().date()
                    ]
                    
                    if futures:
                        # Sort by expiry and get the nearest one
                        futures.sort(key=lambda x: x['expiry'])
                        nearest_contract = futures[0]
                        logger.info(f"Mapped {symbol} -> {nearest_contract['tradingsymbol']} (Expiry: {nearest_contract['expiry']})")
                        return nearest_contract['tradingsymbol']
                    else:
                        logger.warning(f"No futures contract found for {base_symbol}, using base symbol")
                        return base_symbol
                        
                except Exception as e:
                    logger.error(f"Error fetching instruments: {str(e)}")
                    return base_symbol
            else:
                return base_symbol
                
        except Exception as e:
            logger.error(f"Error mapping trading symbol: {str(e)}")
            return symbol
    
    def _place_order(self, signal, symbol: str, strategy_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Place order based on signal
        
        Args:
            signal: Signal object
            symbol: Trading symbol
            strategy_id: Strategy ID for position tracking
        
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
            
            # Determine trading symbol and exchange
            if isinstance(signal, OptionSignal):
                # For options, construct the trading symbol using strike and option type
                strike = getattr(signal, 'strike', None)
                option_type = getattr(signal, 'option_type', None)
                expiration = getattr(signal, 'expiration', None)
                
                if strike is None or option_type is None:
                    logger.error(f"Option signal missing strike or option_type: {signal}")
                    return None
                
                # Get option type value (it's an enum)
                option_type_str = option_type.value if hasattr(option_type, 'value') else str(option_type)
                
                trading_symbol = self._get_option_trading_symbol(symbol, strike, option_type_str, expiration)
                exchange = self.kite_client.EXCHANGE_NFO
            else:
                # For stocks/indices, get the correct trading symbol
                trading_symbol = self._get_trading_symbol(symbol)
                # Determine exchange based on trading symbol
                # If it's a futures contract (ends with FUT), use NFO exchange
                if trading_symbol.endswith('FUT') or trading_symbol.endswith('CE') or trading_symbol.endswith('PE'):
                    exchange = self.kite_client.EXCHANGE_NFO
                else:
                    exchange = self.kite_client.EXCHANGE_NSE
            
            # Determine quantity (get lot size for futures/options)
            lot_size = self._get_lot_size(trading_symbol, exchange)
            # Get the number of lots from signal (default 1)
            num_lots = getattr(signal, 'quantity', 1)
            quantity = num_lots * lot_size
            
            # Place market order
            order_params = {
                'exchange': exchange,
                'tradingsymbol': trading_symbol,
                'transaction_type': transaction_type,
                'quantity': quantity,
                'order_type': self.kite_client.ORDER_TYPE_MARKET,
                'product': self.kite_client.PRODUCT_NRML,  # Normal (carry forward positions)
                'variety': self.kite_client.VARIETY_REGULAR
            }
            
            logger.info(f"Placing order: {order_params}")
            order_id = self.kite_client.place_order(**order_params)
            
            logger.info(f"Order placed successfully. Order ID: {order_id}")
            
            # Track this position if strategy_id is provided
            if strategy_id:
                position = {
                    'symbol': trading_symbol,
                    'quantity': quantity,
                    'side': signal_type.upper(),
                    'order_id': order_id,
                    'timestamp': datetime.now().isoformat(),
                    'exchange': exchange
                }
                
                if strategy_id not in self.open_positions:
                    self.open_positions[strategy_id] = []
                
                self.open_positions[strategy_id].append(position)
                logger.info(f"Tracked new position for {strategy_id}: {trading_symbol} {signal_type.upper()} {quantity}")
            
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
    
    def _close_position(self, strategy_id: str, position: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Close an existing position by placing opposite order
        
        Args:
            strategy_id: Strategy ID
            position: Position dict with symbol, quantity, side, etc.
            
        Returns:
            Dict with order details if successful, None otherwise
        """
        try:
            if not self.kite_client:
                logger.error("KiteConnect client not initialized. Cannot close position.")
                return None
            
            # Determine opposite transaction type
            if position['side'] == 'BUY':
                transaction_type = self.kite_client.TRANSACTION_TYPE_SELL
                action_str = "Closing LONG"
            else:
                transaction_type = self.kite_client.TRANSACTION_TYPE_BUY
                action_str = "Closing SHORT"
            
            # Place opposite order with same quantity
            order_params = {
                'exchange': position.get('exchange', self.kite_client.EXCHANGE_NFO),
                'tradingsymbol': position['symbol'],
                'transaction_type': transaction_type,
                'quantity': position['quantity'],
                'order_type': self.kite_client.ORDER_TYPE_MARKET,
                'product': self.kite_client.PRODUCT_NRML,  # Normal (same as opening order)
                'variety': self.kite_client.VARIETY_REGULAR
            }
            
            logger.info(f"{action_str} position: {order_params}")
            order_id = self.kite_client.place_order(**order_params)
            
            logger.info(f"Position closed successfully. Order ID: {order_id}")
            
            # Remove position from tracking
            if strategy_id in self.open_positions:
                self.open_positions[strategy_id] = [
                    p for p in self.open_positions[strategy_id]
                    if p['order_id'] != position['order_id']
                ]
            
            # Record the closing order
            close_order = {
                'order_id': order_id,
                'timestamp': datetime.now().isoformat(),
                'symbol': position['symbol'],
                'transaction_type': transaction_type,
                'quantity': position['quantity'],
                'order_type': 'MARKET',
                'status': 'placed',
                'action': 'CLOSE',
                'original_order_id': position['order_id'],
                'params': order_params
            }
            
            # Add to order history
            if strategy_id in self.order_history:
                self.order_history[strategy_id].append(close_order)
            
            return close_order
            
        except Exception as e:
            logger.error(f"Error closing position: {str(e)}", exc_info=True)
            return None
    
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
    
    def get_open_positions(self, strategy_id: str) -> List[Dict]:
        """Get current open positions for a strategy"""
        if strategy_id not in self.open_positions:
            return []
        return self.open_positions[strategy_id]
    
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
