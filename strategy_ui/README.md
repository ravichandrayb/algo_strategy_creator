# Strategy Manager UI

A modern React-based web interface for managing and deploying trading strategies.

## 🌟 Features

- **Strategy Dashboard**: View all 20+ option strategies with detailed information
- **One-Click Deployment**: Deploy strategies instantly with a single click
- **Real-Time Management**: Start, stop, and monitor strategies in real-time
- **Smart Filtering**: Filter by status, category (Bullish/Bearish/Neutral), and more
- **Multi-Symbol Support**: Deploy strategies on NIFTY, BANKNIFTY, RELIANCE, TCS, INFY
- **Risk Assessment**: Visual risk indicators for each strategy
- **Live Status**: Auto-refreshing active strategies dashboard
- **Beautiful UI**: Modern gradient design with smooth animations

## 📋 Strategies Included

### Income Strategies
- Covered Call
- Cash Secured Put
- Iron Condor
- Iron Butterfly
- Bull Put Spread
- Bear Call Spread
- Calendar Spread
- Diagonal Spread
- Butterfly Spread
- Jade Lizard
- Big Lizard
- Short Strangle
- Short Straddle
- Short Put Ladder

### Directional Strategies
- Bull Call Spread
- Bear Put Spread

### Volatility Strategies
- Long Straddle
- Long Strangle

### Hedging Strategies
- Protective Put
- Collar

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 14+
- npm or yarn

### Installation

1. **Run the setup script:**
```bash
cd strategy_ui
chmod +x setup.sh
./setup.sh
```

2. **Start the application:**
```bash
chmod +x start.sh
./start.sh
```

Or start services manually:

**Terminal 1 - Backend:**
```bash
cd strategy_ui/backend
source venv/bin/activate
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd strategy_ui/frontend
npm start
```

3. **Access the UI:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000

## 📱 Using the UI

### Dashboard Overview
- **Total Strategies**: Shows count of all available strategies
- **Active Count**: Number of currently running strategies
- **Filter Buttons**: Quick filters for All, Active, Inactive, Bullish, Bearish, Neutral
- **Symbol Selector**: Choose symbol for deployment (NIFTY, BANKNIFTY, etc.)

### Strategy Cards
Each card displays:
- **Strategy Name**: Proper formatted name (e.g., "Iron Condor" instead of "IronCondorStrategy")
- **Category Icon**: Visual indicator (📈 Bullish, 📉 Bearish, ➡️ Neutral)
- **Description**: What the strategy does
- **Type Badge**: Strategy type (Income, Directional, Volatility, Hedging)
- **Risk Badge**: Risk level with color coding
  - Green: Low risk
  - Orange: Medium risk
  - Red: High risk
  - Dark Red: Very High risk
- **Deploy/Stop Button**: One-click action buttons

### Deploying a Strategy
1. Select your desired symbol from the dropdown
2. Find the strategy you want to deploy
3. Click the **Deploy** button
4. Strategy appears in the "Active Strategies" section
5. Notification confirms successful deployment

### Stopping a Strategy
1. Locate the active strategy (green card or in Active section)
2. Click the **Stop** button
3. Strategy is removed from active list
4. Notification confirms successful stop

### Active Strategies Section
- Shows all currently running strategies
- Displays symbol and deployment time
- Quick stop button for each
- Auto-refreshes every 5 seconds

## 🔧 API Endpoints

### GET `/api/strategies`
Get all available strategies with metadata
```json
{
  "success": true,
  "strategies": [...],
  "count": 20
}
```

### POST `/api/strategies/<strategy_id>/deploy`
Deploy a strategy
```json
{
  "symbol": "NIFTY",
  "parameters": {}
}
```

### POST `/api/strategies/<strategy_id>/stop`
Stop a running strategy

### GET `/api/strategies/active`
Get all active strategies
```json
{
  "success": true,
  "active_strategies": [...],
  "count": 3
}
```

### GET `/api/strategies/<strategy_id>/status`
Get detailed status of a specific strategy

### GET `/api/health`
Health check endpoint

## 🎨 UI Features

### Responsive Design
- Works on desktop, tablet, and mobile
- Adaptive grid layout
- Touch-friendly buttons

### Visual Feedback
- Success/error notifications
- Smooth animations
- Color-coded risk levels
- Loading states

### Real-Time Updates
- Active strategies auto-refresh every 5 seconds
- Instant UI updates on deploy/stop
- Live status indicators

## 📁 Project Structure

```
strategy_ui/
├── backend/
│   ├── app.py              # Flask API server
│   ├── requirements.txt    # Python dependencies
│   └── venv/              # Virtual environment
├── frontend/
│   ├── public/
│   │   └── index.html     # HTML template
│   ├── src/
│   │   ├── App.js         # Main React component
│   │   ├── App.css        # Styles
│   │   ├── index.js       # React entry point
│   │   └── index.css      # Global styles
│   ├── package.json       # Node dependencies
│   └── node_modules/      # Node packages
├── setup.sh               # Setup script
├── start.sh               # Start script
└── README.md             # This file
```

## 🔐 Security Notes

- Backend runs on localhost only by default
- No authentication required for local development
- Add authentication for production deployment
- CORS enabled for local React development

## 🐛 Troubleshooting

### Backend won't start
- Check Python version: `python3 --version`
- Verify virtual environment: `source backend/venv/bin/activate`
- Check port 5000 is free: `lsof -i :5000`

### Frontend won't start
- Check Node version: `node --version`
- Delete node_modules and reinstall: `rm -rf node_modules && npm install`
- Check port 3000 is free: `lsof -i :3000`

### Strategies not loading
- Verify backend is running: `curl http://localhost:5000/api/health`
- Check console for errors
- Ensure trading_signals package is installed

## 🚀 Production Deployment

For production:
1. Build the React app: `cd frontend && npm run build`
2. Serve with a production server (nginx, Apache)
3. Add authentication and HTTPS
4. Configure CORS properly
5. Use environment variables for configuration
6. Add logging and monitoring

## 📝 License

Part of the Algo Strategy Signals project

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## 📧 Support

For issues or questions, please open an issue on the repository.

---

**Happy Trading! 📈📉**
