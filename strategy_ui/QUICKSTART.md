# Strategy Manager UI - Quick Start Guide

## 🎯 Overview

The Strategy Manager UI provides a beautiful, modern interface to manage your 20+ option trading strategies. Deploy, monitor, and stop strategies with a single click!

## 🚀 Getting Started

### Step 1: Setup (One-time)
```bash
cd strategy_ui
./setup.sh
```

This will:
- Install Flask backend dependencies
- Install React frontend dependencies
- Set up virtual environments

### Step 2: Start the Application
```bash
./start.sh
```

Or start manually in two terminals:

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

### Step 3: Access the UI
Open your browser to: **http://localhost:3000**

## 📊 UI Components

### Main Dashboard
```
┌─────────────────────────────────────────────────────────────┐
│  Activity Icon    STRATEGY MANAGER        Total: 20  Active: 3 │
└─────────────────────────────────────────────────────────────┘
```

### Filter Bar
```
[ All ] [ Active ] [ Inactive ] [ 📈 Bullish ] [ 📉 Bearish ] [ ➡️ Neutral ]

Symbol: [ NIFTY ▼ ]
```

### Active Strategies (Green Cards)
```
┌────────────────────────────────────────────┐
│ 🟢 ACTIVE STRATEGIES                       │
├────────────────────────────────────────────┤
│ Iron Condor              [ ⬛ Stop ]       │
│ NIFTY                                      │
│ Deployed: Nov 16, 2025 10:30 AM  Medium   │
└────────────────────────────────────────────┘
```

### Strategy Cards
```
┌────────────────────────────────────────────┐
│ 📈 Bull Call Spread                        │
│ [Directional] [🛡️ Medium]                  │
│                                            │
│ Limited risk bullish strategy using calls  │
│                                            │
│ Bullish                      [ ▶️ Deploy ] │
└────────────────────────────────────────────┘
```

## 🎨 Visual Features

### Color Coding
- **Green Cards**: Active strategies
- **White Cards**: Inactive strategies
- **Green Risk Badge**: Low risk
- **Orange Risk Badge**: Medium risk
- **Red Risk Badge**: High risk
- **Dark Red Risk Badge**: Very High risk

### Icons
- 📈 = Bullish strategies
- 📉 = Bearish strategies
- ➡️ = Neutral strategies
- 🛡️ = Risk indicator
- ▶️ = Deploy button
- ⬛ = Stop button

## 🔄 Workflow

### Deploying a Strategy
1. **Select Symbol**: Choose NIFTY, BANKNIFTY, RELIANCE, TCS, or INFY
2. **Find Strategy**: Browse or filter to find your desired strategy
3. **Click Deploy**: Hit the green "Deploy" button
4. **Confirmation**: See success notification
5. **Monitor**: Strategy appears in "Active Strategies" section

### Managing Active Strategies
- Active strategies show at the top with green background
- Auto-refresh every 5 seconds
- Click "Stop" button to deactivate
- View deployment time and risk level

### Filtering Strategies
- **All**: Show all 20+ strategies
- **Active**: Show only running strategies
- **Inactive**: Show only stopped strategies
- **Bullish/Bearish/Neutral**: Filter by market outlook

## 📋 Available Strategies

### Income Strategies (14)
1. **Covered Call** - Generate income by selling calls
2. **Cash Secured Put** - Sell puts with cash reserved
3. **Iron Condor** - Low volatility with defined risk
4. **Iron Butterfly** - ATM strikes for income
5. **Bull Put Spread** - Credit spread for bullish outlook
6. **Bear Call Spread** - Credit spread for bearish outlook
7. **Calendar Spread** - Profit from time decay
8. **Diagonal Spread** - Combined calendar and vertical
9. **Butterfly Spread** - Limited risk/reward
10. **Jade Lizard** - High probability, no upside risk
11. **Big Lizard** - Enhanced jade lizard
12. **Short Strangle** - Range-bound movement
13. **Short Straddle** - Low volatility (high risk)
14. **Short Put Ladder** - Multiple put strikes

### Directional Strategies (2)
1. **Bull Call Spread** - Limited risk bullish
2. **Bear Put Spread** - Limited risk bearish

### Volatility Strategies (2)
1. **Long Straddle** - Profit from large moves
2. **Long Strangle** - Lower cost than straddle

### Hedging Strategies (2)
1. **Protective Put** - Insurance for long positions
2. **Collar** - Protect downside, limit upside

## 🎯 Use Cases

### Example 1: Deploy Iron Condor on NIFTY
```
1. Select "NIFTY" from symbol dropdown
2. Find "Iron Condor" card (or filter by "Neutral")
3. Click "Deploy" button
4. See green notification: "Iron Condor deployed successfully!"
5. Strategy now shows in Active Strategies section
```

### Example 2: Stop All Active Strategies
```
1. Go to "Active Strategies" section at top
2. Click "Stop" button on each active strategy
3. Confirm with notifications
4. All strategies now inactive
```

### Example 3: Filter Bullish Strategies
```
1. Click "📈 Bullish" filter button
2. See only bullish strategies:
   - Covered Call
   - Cash Secured Put
   - Bull Call Spread
   - Bull Put Spread
   - Jade Lizard
   - Big Lizard
   - Short Put Ladder
   - Protective Put
```

## 🔧 API Usage (Advanced)

### Test Backend Directly
```bash
# Health check
curl http://localhost:5000/api/health

# Get all strategies
curl http://localhost:5000/api/strategies

# Deploy a strategy
curl -X POST http://localhost:5000/api/strategies/IronCondorStrategy/deploy \
  -H "Content-Type: application/json" \
  -d '{"symbol": "NIFTY", "parameters": {}}'

# Get active strategies
curl http://localhost:5000/api/strategies/active

# Stop a strategy
curl -X POST http://localhost:5000/api/strategies/IronCondorStrategy/stop
```

## 🐛 Troubleshooting

### Issue: Backend not starting
```bash
# Check Python version
python3 --version  # Should be 3.8+

# Activate virtual environment
cd strategy_ui/backend
source venv/bin/activate

# Check if port is in use
lsof -i :5000

# Kill existing process if needed
kill -9 <PID>
```

### Issue: Frontend not starting
```bash
# Check Node version
node --version  # Should be 14+

# Clear cache and reinstall
cd strategy_ui/frontend
rm -rf node_modules package-lock.json
npm install

# Check if port is in use
lsof -i :3000
```

### Issue: Strategies not loading
```bash
# Verify backend is running
curl http://localhost:5000/api/health

# Check browser console for errors (F12)

# Verify CORS is enabled in backend
# Check backend logs for errors
```

## 📱 Mobile Experience

The UI is fully responsive and works on:
- Desktop browsers (Chrome, Firefox, Safari, Edge)
- Tablets (iPad, Android tablets)
- Mobile phones (touch-optimized)

## 🎨 Customization

### Change Theme Colors
Edit `frontend/src/App.css`:
```css
/* Change gradient background */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Change active strategy color */
background: linear-gradient(135deg, #10b981 0%, #059669 100%);
```

### Add New Symbols
Edit `frontend/src/App.js`:
```javascript
<select value={selectedSymbol} onChange={(e) => setSelectedSymbol(e.target.value)}>
  <option value="NIFTY">NIFTY</option>
  <option value="BANKNIFTY">BANKNIFTY</option>
  <option value="YOUR_SYMBOL">YOUR_SYMBOL</option>
</select>
```

## 🚀 Next Steps

1. **Add Authentication**: Secure the API with user login
2. **Add Backtesting**: Show strategy performance history
3. **Add Parameters**: Allow custom parameters when deploying
4. **Add Notifications**: Email/SMS alerts for strategy events
5. **Add Charts**: Visualize strategy P&L
6. **Add Position Tracking**: Real-time position monitoring
7. **Add Order Management**: Place orders directly from UI

## 💡 Tips

- Use filters to quickly find strategies by category
- Monitor active strategies in real-time
- Test with different symbols to see flexibility
- Start with low-risk strategies first
- Deploy multiple strategies for diversification

## 📧 Support

For issues or questions:
- Check the troubleshooting section
- Review browser console (F12) for errors
- Check backend logs for API errors
- Open an issue on GitHub

---

**Enjoy managing your trading strategies! 🎉📈**
