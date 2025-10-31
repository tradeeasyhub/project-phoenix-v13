# Project Phoenix v12.2 - Trading Dashboard

## Overview
Project Phoenix is an institutional-grade cryptocurrency trading dashboard with advanced technical indicators and real-time data streaming from Binance.

## Features
- Real-time WebSocket connections for live market data
- 15+ technical indicators including ADX, RSI, VWAP, Ichimoku, and more
- Options data analysis with implied volatility
- Futures market data (Open Interest, Funding Rate, Long/Short Ratio)
- Smart Money Concepts (SMC) integration
- Multi-timeframe analysis
- All 15 security and performance audit fixes applied

## Quick Start

### Prerequisites
- Python 3.8 or higher
- Modern web browser (Chrome, Firefox, or Edge)

### Installation & Running

#### Windows
Simply double-click `run_dashboard.bat` - it will:
1. Check Python installation
2. Install required dependencies automatically
3. Start the Flask API server
4. Open the dashboard in your default browser

#### Linux/Mac
```bash
# Install dependencies
pip install flask flask-cors requests python-dotenv

# Start the server
python3 app.py

# Open dashboard.html in your browser
```

## CORS Configuration

The Flask server is configured to accept requests from:
- Local file:// protocol (when opening dashboard.html directly)
- http://localhost:* 
- http://127.0.0.1:*

This allows the dashboard to work when opened directly from the filesystem without needing a separate web server.

## API Endpoints

All endpoints are available at `http://localhost:5000`

### Health Check
```
GET /health
```
Returns server status and available endpoints.

### Options Data
```
GET /get-options-data?symbol={symbol}
```
Example: `/get-options-data?symbol=BTC`

### Funding Rate
```
GET /api/binance/funding?symbol={symbol}
```
Example: `/api/binance/funding?symbol=BTCUSDT`

### Open Interest
```
GET /api/binance/oi?symbol={symbol}
```
Example: `/api/binance/oi?symbol=BTCUSDT`

### Long/Short Ratio
```
GET /api/binance/lsratio?symbol={symbol}&period={period}&limit={limit}
```
Example: `/api/binance/lsratio?symbol=BTCUSDT&period=5m&limit=30`

Valid periods: 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d

## Configuration

### Environment Variables
Create a `.env` file in the project root (optional):

```env
# Binance API Credentials (optional - only needed for authenticated endpoints)
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SERVER_PORT=5000
```

**Note:** The `.env` file is automatically created with empty values if it doesn't exist. Public endpoints work without API keys.

## Security Features

✅ Environment variable protection (API keys not hardcoded)  
✅ CORS restricted to localhost and null origin (file:// access)  
✅ Rate limiting enabled (60 requests per minute per IP)  
✅ Input validation for all parameters  
✅ Error handling and logging  
✅ Request timeout protection  

## Troubleshooting

### CORS Errors
If you see CORS errors in the browser console:
1. Make sure the Flask server is running on port 5000
2. Check that you're accessing the dashboard from file:// or localhost
3. Verify the server logs show "Server ready to accept connections"

### Server Not Starting
1. Verify Python 3.8+ is installed: `python --version`
2. Install dependencies manually: `pip install flask flask-cors requests python-dotenv`
3. Check if port 5000 is available: `netstat -an | grep 5000` (Linux/Mac) or `netstat -an | findstr 5000` (Windows)

### API Errors
- Check server logs in `flask_server.log`
- Verify internet connectivity for Binance API access
- Some endpoints may require valid API keys in `.env`

## Development

### File Structure
```
project-phoenix-v13/
├── app.py                  # Flask API server
├── dashboard.html          # Main dashboard UI
├── script.js              # Client-side JavaScript
├── style.css              # Dashboard styles
├── run_dashboard.bat      # Windows launcher script
├── .env                   # Environment variables (git-ignored)
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

### Logging
- Server logs: `flask_server.log`
- Launcher logs: `phoenix_launcher.log` (Windows)

## Version History

### v12.2 (Current)
- All 15 audit fixes applied
- CORS support for file:// access
- Enhanced security features
- Improved error handling
- Rate limiting implemented
- Environment variable protection

## License
© 2025 tradeeasyhub. All rights reserved.

## Support
For issues, please check the troubleshooting section or review the server logs.
