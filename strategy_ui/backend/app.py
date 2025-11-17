"""
Flask Backend API for Strategy Management UI
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import importlib
import inspect
import sys
import os
from datetime import datetime
import json
from pathlib import Path

# Add parent directory to path to import trading_signals
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from trading_signals.strategies.option_strategies import *
from trading_signals.strategies.user_strategies import *
from strategy_executor import executor

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Store active strategy instances
active_strategies = {}

# Start the strategy executor scheduler
executor.start()

# User strategies metadata
USER_STRATEGY_METADATA = {
    'Nifty15mProStrategy': {
        'name': 'Nifty 15m Pro',
        'description': 'Supertrend + ADX strategy for 15-minute NIFTY trading',
        'risk_level': 'Medium',
        'type': 'Trend Following',
        'category': 'User Strategy',
        'timeframe': '15m',
        'best_for': 'NIFTY'
    }
}

# Strategy metadata with proper names
STRATEGY_METADATA = {
    'CoveredCallStrategy': {
        'name': 'Covered Call',
        'description': 'Generate income by selling calls against stock holdings',
        'risk_level': 'Low',
        'type': 'Income',
        'category': 'Bullish'
    },
    'CashSecuredPutStrategy': {
        'name': 'Cash Secured Put',
        'description': 'Sell puts with cash reserved to buy the stock',
        'risk_level': 'Medium',
        'type': 'Income',
        'category': 'Bullish'
    },
    'IronCondorStrategy': {
        'name': 'Iron Condor',
        'description': 'Profit from low volatility with defined risk',
        'risk_level': 'Medium',
        'type': 'Income',
        'category': 'Neutral'
    },
    'IronButterflyStrategy': {
        'name': 'Iron Butterfly',
        'description': 'Similar to iron condor but with ATM strikes',
        'risk_level': 'Medium',
        'type': 'Income',
        'category': 'Neutral'
    },
    'BullCallSpreadStrategy': {
        'name': 'Bull Call Spread',
        'description': 'Limited risk bullish strategy using calls',
        'risk_level': 'Medium',
        'type': 'Directional',
        'category': 'Bullish'
    },
    'BearPutSpreadStrategy': {
        'name': 'Bear Put Spread',
        'description': 'Limited risk bearish strategy using puts',
        'risk_level': 'Medium',
        'type': 'Directional',
        'category': 'Bearish'
    },
    'BullPutSpreadStrategy': {
        'name': 'Bull Put Spread',
        'description': 'Credit spread for bullish outlook',
        'risk_level': 'Medium',
        'type': 'Income',
        'category': 'Bullish'
    },
    'BearCallSpreadStrategy': {
        'name': 'Bear Call Spread',
        'description': 'Credit spread for bearish outlook',
        'risk_level': 'Medium',
        'type': 'Income',
        'category': 'Bearish'
    },
    'LongStraddleStrategy': {
        'name': 'Long Straddle',
        'description': 'Profit from large price moves in either direction',
        'risk_level': 'High',
        'type': 'Volatility',
        'category': 'Neutral'
    },
    'ShortStraddleStrategy': {
        'name': 'Short Straddle',
        'description': 'Profit from low volatility, unlimited risk',
        'risk_level': 'Very High',
        'type': 'Income',
        'category': 'Neutral'
    },
    'LongStrangleStrategy': {
        'name': 'Long Strangle',
        'description': 'Lower cost than straddle, needs bigger move',
        'risk_level': 'High',
        'type': 'Volatility',
        'category': 'Neutral'
    },
    'ShortStrangleStrategy': {
        'name': 'Short Strangle',
        'description': 'Profit from range-bound movement',
        'risk_level': 'Very High',
        'type': 'Income',
        'category': 'Neutral'
    },
    'ProtectivePutStrategy': {
        'name': 'Protective Put',
        'description': 'Insurance for long stock positions',
        'risk_level': 'Low',
        'type': 'Hedging',
        'category': 'Bullish'
    },
    'CollarStrategy': {
        'name': 'Collar',
        'description': 'Protect downside while limiting upside',
        'risk_level': 'Low',
        'type': 'Hedging',
        'category': 'Neutral'
    },
    'CalendarSpreadStrategy': {
        'name': 'Calendar Spread',
        'description': 'Profit from time decay differences',
        'risk_level': 'Medium',
        'type': 'Income',
        'category': 'Neutral'
    },
    'DiagonalSpreadStrategy': {
        'name': 'Diagonal Spread',
        'description': 'Combine calendar and vertical spreads',
        'risk_level': 'Medium',
        'type': 'Income',
        'category': 'Neutral'
    },
    'ButterflySpreadStrategy': {
        'name': 'Butterfly Spread',
        'description': 'Limited risk/reward, profit from narrow range',
        'risk_level': 'Low',
        'type': 'Income',
        'category': 'Neutral'
    },
    'JadeLizardStrategy': {
        'name': 'Jade Lizard',
        'description': 'High probability credit strategy with no upside risk',
        'risk_level': 'Medium',
        'type': 'Income',
        'category': 'Bullish'
    },
    'BigLizardStrategy': {
        'name': 'Big Lizard',
        'description': 'Enhanced jade lizard with higher credit',
        'risk_level': 'Medium',
        'type': 'Income',
        'category': 'Bullish'
    },
    'ShortPutLadderStrategy': {
        'name': 'Short Put Ladder',
        'description': 'Multiple put strikes for income generation',
        'risk_level': 'High',
        'type': 'Income',
        'category': 'Bullish'
    }
}

@app.route('/api/strategies', methods=['GET'])
def get_strategies():
    """Get all available strategies with metadata"""
    strategies = []
    
    # Get all strategy classes from option_strategies module
    from trading_signals.strategies import option_strategies
    
    for name in option_strategies.__all__:
        strategy_class = getattr(option_strategies, name)
        metadata = STRATEGY_METADATA.get(name, {
            'name': name.replace('Strategy', '').replace('_', ' ').title(),
            'description': 'Option trading strategy',
            'risk_level': 'Medium',
            'type': 'General',
            'category': 'Neutral'
        })
        
        strategies.append({
            'id': name,
            'class_name': name,
            'name': metadata['name'],
            'description': metadata['description'],
            'risk_level': metadata['risk_level'],
            'type': metadata['type'],
            'category': metadata['category'],
            'status': 'active' if name in active_strategies else 'inactive',
            'strategy_type': 'option'
        })
    
    return jsonify({
        'success': True,
        'strategies': sorted(strategies, key=lambda x: x['name']),
        'count': len(strategies)
    })

@app.route('/api/user-strategies', methods=['GET'])
def get_user_strategies():
    """Get all user-defined strategies"""
    strategies = []
    
    # Get all strategy classes from user_strategies module
    from trading_signals.strategies import user_strategies
    
    for name in user_strategies.__all__:
        strategy_class = getattr(user_strategies, name)
        metadata = USER_STRATEGY_METADATA.get(name, {
            'name': name.replace('Strategy', '').replace('_', ' ').title(),
            'description': 'User-defined strategy',
            'risk_level': 'Medium',
            'type': 'Custom',
            'category': 'User Strategy',
            'timeframe': 'Any',
            'best_for': 'General'
        })
        
        strategies.append({
            'id': name,
            'class_name': name,
            'name': metadata['name'],
            'description': metadata['description'],
            'risk_level': metadata['risk_level'],
            'type': metadata['type'],
            'category': metadata['category'],
            'timeframe': metadata.get('timeframe', 'Any'),
            'best_for': metadata.get('best_for', 'General'),
            'status': 'active' if name in active_strategies else 'inactive',
            'strategy_type': 'user'
        })
    
    return jsonify({
        'success': True,
        'strategies': sorted(strategies, key=lambda x: x['name']),
        'count': len(strategies)
    })

@app.route('/api/strategies/<strategy_id>/deploy', methods=['POST'])
def deploy_strategy(strategy_id):
    """Deploy (activate) a strategy"""
    try:
        data = request.json or {}
        symbol = data.get('symbol', 'NIFTY50')  # Default to NIFTY50
        parameters = data.get('parameters', {})
        interval = data.get('interval', '15minute')  # Default to 15 minute
        
        # Try to import from option_strategies first, then user_strategies
        strategy_class = None
        strategy_name = strategy_id
        
        try:
            from trading_signals.strategies import option_strategies
            strategy_class = getattr(option_strategies, strategy_id)
            strategy_name = STRATEGY_METADATA.get(strategy_id, {}).get('name', strategy_id)
        except AttributeError:
            from trading_signals.strategies import user_strategies
            strategy_class = getattr(user_strategies, strategy_id)
            strategy_name = USER_STRATEGY_METADATA.get(strategy_id, {}).get('name', strategy_id)
        
        # Create strategy instance
        strategy_instance = strategy_class(**parameters) if parameters else strategy_class()
        
        # Deploy to executor for live execution
        success = executor.deploy_strategy(
            strategy_id=strategy_id,
            strategy_instance=strategy_instance,
            symbol=symbol,
            interval=interval,
            parameters=parameters
        )
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Strategy is already deployed'
            }), 400
        
        # Also store in active_strategies for backward compatibility
        active_strategies[strategy_id] = {
            'class_name': strategy_id,
            'instance': strategy_instance,
            'symbol': symbol,
            'deployed_at': datetime.now().isoformat(),
            'status': 'running',
            'parameters': parameters,
            'interval': interval
        }
        
        return jsonify({
            'success': True,
            'message': f'{strategy_name} deployed successfully and running live',
            'strategy': {
                'id': strategy_id,
                'name': strategy_name,
                'symbol': symbol,
                'interval': interval,
                'deployed_at': active_strategies[strategy_id]['deployed_at'],
                'status': 'running'
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/strategies/<strategy_id>/stop', methods=['POST'])
def stop_strategy(strategy_id):
    """Stop (deactivate) a strategy"""
    try:
        # Stop in executor
        executor_stopped = executor.stop_strategy(strategy_id)
        
        if strategy_id in active_strategies:
            stopped_strategy = active_strategies.pop(strategy_id)
            
            # Get strategy name from either metadata dict
            strategy_name = STRATEGY_METADATA.get(strategy_id, USER_STRATEGY_METADATA.get(strategy_id, {})).get('name', strategy_id)
            
            return jsonify({
                'success': True,
                'message': f'{strategy_name} stopped successfully',
                'strategy': {
                    'id': strategy_id,
                    'name': strategy_name,
                    'stopped_at': datetime.now().isoformat()
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Strategy not active'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/strategies/active', methods=['GET'])
def get_active_strategies():
    """Get all currently active strategies"""
    active = []
    for strategy_id, strategy_data in active_strategies.items():
        metadata = STRATEGY_METADATA.get(strategy_id, {})
        active.append({
            'id': strategy_id,
            'name': metadata.get('name', strategy_id),
            'symbol': strategy_data['symbol'],
            'deployed_at': strategy_data['deployed_at'],
            'status': strategy_data['status'],
            'parameters': strategy_data.get('parameters', {}),
            'category': metadata.get('category', 'Neutral'),
            'risk_level': metadata.get('risk_level', 'Medium')
        })
    
    return jsonify({
        'success': True,
        'active_strategies': active,
        'count': len(active)
    })

@app.route('/api/strategies/<strategy_id>/status', methods=['GET'])
def get_strategy_status(strategy_id):
    """Get detailed status of a specific strategy including live execution stats"""
    # Get executor info
    executor_info = executor.get_strategy_info(strategy_id)
    
    if strategy_id in active_strategies or executor_info:
        strategy_data = active_strategies.get(strategy_id, {})
        metadata = STRATEGY_METADATA.get(strategy_id, USER_STRATEGY_METADATA.get(strategy_id, {}))
        
        status_info = {
            'id': strategy_id,
            'name': metadata.get('name', strategy_id),
            'status': 'active' if strategy_id in active_strategies else 'inactive',
            'symbol': strategy_data.get('symbol'),
            'deployed_at': strategy_data.get('deployed_at'),
            'parameters': strategy_data.get('parameters', {}),
            'metadata': metadata
        }
        
        # Add executor stats if available
        if executor_info:
            status_info.update({
                'last_execution': executor_info.get('last_execution'),
                'execution_count': executor_info.get('execution_count', 0),
                'signal_count': executor_info.get('signal_count', 0),
                'order_count': executor_info.get('order_count', 0),
                'total_signals': executor_info.get('total_signals', 0),
                'total_orders': executor_info.get('total_orders', 0),
                'interval': executor_info.get('interval')
            })
        
        return jsonify({
            'success': True,
            'strategy': status_info
        })
    else:
        return jsonify({
            'success': True,
            'strategy': {
                'id': strategy_id,
                'status': 'inactive'
            }
        })

@app.route('/api/strategies/<strategy_id>/signals', methods=['GET'])
def get_strategy_signals(strategy_id):
    """Get signal history for a strategy"""
    limit = request.args.get('limit', 50, type=int)
    signals = executor.get_signal_history(strategy_id, limit=limit)
    
    return jsonify({
        'success': True,
        'strategy_id': strategy_id,
        'signals': signals,
        'count': len(signals)
    })

@app.route('/api/strategies/<strategy_id>/orders', methods=['GET'])
def get_strategy_orders(strategy_id):
    """Get order history for a strategy"""
    limit = request.args.get('limit', 50, type=int)
    orders = executor.get_order_history(strategy_id, limit=limit)
    
    return jsonify({
        'success': True,
        'strategy_id': strategy_id,
        'orders': orders,
        'count': len(orders)
    })

@app.route('/api/strategies/<strategy_id>/positions', methods=['GET'])
def get_strategy_positions(strategy_id):
    """Get open positions for a strategy"""
    positions = executor.get_open_positions(strategy_id)
    
    return jsonify({
        'success': True,
        'strategy_id': strategy_id,
        'positions': positions,
        'count': len(positions)
    })

@app.route('/api/strategies/<strategy_id>/logs', methods=['GET'])
def get_strategy_logs(strategy_id):
    """Get execution logs for a strategy"""
    limit = request.args.get('limit', 50, type=int)
    logs = executor.get_execution_logs(strategy_id, limit=limit)
    
    return jsonify({
        'success': True,
        'strategy_id': strategy_id,
        'logs': logs,
        'count': len(logs)
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_strategies_count': len(active_strategies)
    })

if __name__ == '__main__':
    # Use debug=False when running in background, or set use_reloader=False
    import sys
    debug_mode = sys.stdin.isatty()  # Only use debug if running interactively
    app.run(debug=debug_mode, port=5001, use_reloader=False)
