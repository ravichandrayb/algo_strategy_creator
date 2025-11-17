import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Play, Square, Activity, Shield, RefreshCw } from 'lucide-react';
import './App.css';

const API_BASE_URL = 'http://localhost:5001/api';

function App() {
  const [strategies, setStrategies] = useState([]);
  const [userStrategies, setUserStrategies] = useState([]);
  const [activeStrategies, setActiveStrategies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [selectedSymbol, setSelectedSymbol] = useState('NIFTY');
  const [notification, setNotification] = useState(null);
  const [activeTab, setActiveTab] = useState('option'); // 'option' or 'user'

  useEffect(() => {
    fetchStrategies();
    fetchUserStrategies();
    fetchActiveStrategies();
    // Poll active strategies every 5 seconds
    const interval = setInterval(fetchActiveStrategies, 5000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchStrategies = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/strategies`);
      setStrategies(response.data.strategies);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching strategies:', error);
      showNotification('Failed to load strategies', 'error');
      setLoading(false);
    }
  };

  const fetchUserStrategies = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/user-strategies`);
      setUserStrategies(response.data.strategies);
    } catch (error) {
      console.error('Error fetching strategies:', error);
      showNotification('Failed to load strategies', 'error');
      setLoading(false);
    }
  };

  const fetchActiveStrategies = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/strategies/active`);
      setActiveStrategies(response.data.active_strategies);
    } catch (error) {
      console.error('Error fetching active strategies:', error);
    }
  };

  const deployStrategy = async (strategyId, strategyName) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/strategies/${strategyId}/deploy`, {
        symbol: selectedSymbol,
        parameters: {}
      });
      
      if (response.data.success) {
        showNotification(`${strategyName} deployed successfully!`, 'success');
        fetchStrategies();
        fetchUserStrategies();
        fetchActiveStrategies();
      }
    } catch (error) {
      console.error('Error deploying strategy:', error);
      showNotification(`Failed to deploy ${strategyName}`, 'error');
    }
  };

  const stopStrategy = async (strategyId, strategyName) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/strategies/${strategyId}/stop`);
      
      if (response.data.success) {
        showNotification(`${strategyName} stopped successfully!`, 'success');
        fetchStrategies();
        fetchUserStrategies();
        fetchActiveStrategies();
      }
    } catch (error) {
      console.error('Error stopping strategy:', error);
      showNotification(`Failed to stop ${strategyName}`, 'error');
    }
  };

  const showNotification = (message, type) => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  const getRiskColor = (riskLevel) => {
    const colors = {
      'Low': '#10b981',
      'Medium': '#f59e0b',
      'High': '#ef4444',
      'Very High': '#dc2626'
    };
    return colors[riskLevel] || '#6b7280';
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'Bullish': return '📈';
      case 'Bearish': return '📉';
      case 'Neutral': return '➡️';
      case 'User Strategy': return '⚡';
      default: return '📊';
    }
  };

  // Get current strategy list based on active tab
  const currentStrategies = activeTab === 'option' ? strategies : userStrategies;

  const filteredStrategies = currentStrategies.filter(strategy => {
    if (filter === 'all') return true;
    if (filter === 'active') return strategy.status === 'active';
    if (filter === 'inactive') return strategy.status === 'inactive';
    return strategy.category === filter;
  });

  if (loading) {
    return (
      <div className="loading-container">
        <RefreshCw className="spin" size={48} />
        <p>Loading strategies...</p>
      </div>
    );
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="header-title">
            <Activity size={32} />
            <h1>Strategy Manager</h1>
          </div>
          <div className="header-stats">
            <div className="stat-card">
              <span className="stat-label">Total Strategies</span>
              <span className="stat-value">{strategies.length + userStrategies.length}</span>
            </div>
            <div className="stat-card active">
              <span className="stat-label">Active</span>
              <span className="stat-value">{activeStrategies.length}</span>
            </div>
          </div>
        </div>
      </header>

      {/* Notification */}
      {notification && (
        <div className={`notification ${notification.type}`}>
          {notification.message}
        </div>
      )}

      {/* Tab Switcher */}
      <div className="tab-switcher">
        <button 
          className={activeTab === 'option' ? 'active' : ''} 
          onClick={() => setActiveTab('option')}
        >
          📊 Option Strategies ({strategies.length})
        </button>
        <button 
          className={activeTab === 'user' ? 'active' : ''} 
          onClick={() => setActiveTab('user')}
        >
          ⚡ User Strategies ({userStrategies.length})
        </button>
      </div>

      {/* Controls */}
      <div className="controls">
        <div className="filter-group">
          <button 
            className={filter === 'all' ? 'active' : ''} 
            onClick={() => setFilter('all')}
          >
            All
          </button>
          <button 
            className={filter === 'active' ? 'active' : ''} 
            onClick={() => setFilter('active')}
          >
            Active
          </button>
          <button 
            className={filter === 'inactive' ? 'active' : ''} 
            onClick={() => setFilter('inactive')}
          >
            Inactive
          </button>
          <button 
            className={filter === 'Bullish' ? 'active' : ''} 
            onClick={() => setFilter('Bullish')}
          >
            📈 Bullish
          </button>
          <button 
            className={filter === 'Bearish' ? 'active' : ''} 
            onClick={() => setFilter('Bearish')}
          >
            📉 Bearish
          </button>
          <button 
            className={filter === 'Neutral' ? 'active' : ''} 
            onClick={() => setFilter('Neutral')}
          >
            ➡️ Neutral
          </button>
        </div>

        <div className="symbol-selector">
          <label>Symbol:</label>
          <select value={selectedSymbol} onChange={(e) => setSelectedSymbol(e.target.value)}>
            <option value="NIFTY">NIFTY</option>
            <option value="BANKNIFTY">BANKNIFTY</option>
            <option value="RELIANCE">RELIANCE</option>
            <option value="TCS">TCS</option>
            <option value="INFY">INFY</option>
          </select>
        </div>
      </div>

      {/* Active Strategies Section */}
      {activeStrategies.length > 0 && (
        <div className="active-strategies-section">
          <h2>🟢 Active Strategies</h2>
          <div className="active-strategies-grid">
            {activeStrategies.map((strategy) => (
              <div key={strategy.id} className="active-strategy-card">
                <div className="active-strategy-header">
                  <div>
                    <h3>{strategy.name}</h3>
                    <span className="symbol-badge">{strategy.symbol}</span>
                  </div>
                  <button 
                    className="stop-btn"
                    onClick={() => stopStrategy(strategy.id, strategy.name)}
                  >
                    <Square size={16} />
                    Stop
                  </button>
                </div>
                <div className="active-strategy-info">
                  <span>Deployed: {new Date(strategy.deployed_at).toLocaleString()}</span>
                  <span className="risk-badge" style={{ backgroundColor: getRiskColor(strategy.risk_level) }}>
                    {strategy.risk_level}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Strategies Grid */}
      <div className="strategies-section">
        <h2>Available Strategies ({filteredStrategies.length})</h2>
        <div className="strategies-grid">
          {filteredStrategies.map((strategy) => (
            <div 
              key={strategy.id} 
              className={`strategy-card ${strategy.status === 'active' ? 'active' : ''}`}
            >
              <div className="strategy-header">
                <div className="strategy-title">
                  <span className="category-icon">{getCategoryIcon(strategy.category)}</span>
                  <h3>{strategy.name}</h3>
                </div>
                <div className="strategy-badges">
                  <span className="type-badge">{strategy.type}</span>
                  <span 
                    className="risk-badge" 
                    style={{ backgroundColor: getRiskColor(strategy.risk_level) }}
                  >
                    <Shield size={12} />
                    {strategy.risk_level}
                  </span>
                </div>
              </div>

              <p className="strategy-description">{strategy.description}</p>

              {/* Additional info for user strategies */}
              {strategy.strategy_type === 'user' && (
                <div className="user-strategy-info">
                  {strategy.timeframe && (
                    <span className="info-badge">⏱️ {strategy.timeframe}</span>
                  )}
                  {strategy.best_for && (
                    <span className="info-badge">🎯 Best for: {strategy.best_for}</span>
                  )}
                </div>
              )}

              <div className="strategy-footer">
                <div className="strategy-meta">
                  <span className="category-tag">{strategy.category}</span>
                  {strategy.status === 'active' && (
                    <span className="status-badge active">● Running</span>
                  )}
                </div>
                
                {strategy.status === 'active' ? (
                  <button 
                    className="action-btn stop"
                    onClick={() => stopStrategy(strategy.id, strategy.name)}
                  >
                    <Square size={16} />
                    Stop
                  </button>
                ) : (
                  <button 
                    className="action-btn deploy"
                    onClick={() => deployStrategy(strategy.id, strategy.name)}
                  >
                    <Play size={16} />
                    Deploy
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <footer className="footer">
        <p>© 2025 Algo Strategy Signals - Trading Strategy Manager</p>
      </footer>
    </div>
  );
}

export default App;
