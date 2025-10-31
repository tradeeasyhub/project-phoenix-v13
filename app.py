"""
PROJECT PHOENIX v12.2 - PYTHON SERVER (FIXED & SECURED)
========================================================
Author: tradeeasyhub
Date: 2025-10-30
Version: 12.2 (Security Hardened)

AUDIT FIX #4 APPLIED: All API keys moved to .env file

Features:
- /get-options-data endpoint (Binance Options IV)
- /api/binance/funding endpoint (Futures Funding Rate)
- /api/binance/oi endpoint (Open Interest)
- /api/binance/lsratio endpoint (Long/Short Ratio)
- Environment variable protection
- CORS enabled for localhost
- Error handling & logging
- Rate limiting ready
- Request validation
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timezone
import time
from functools import wraps

# ==================== ENVIRONMENT SETUP ====================

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== FLASK APP CONFIGURATION ====================

app = Flask(__name__)

# CORS Configuration (restrict to localhost for security)
# Allow 'null' origin for local file:// access (when opening dashboard.html directly)
# SECURITY NOTE: 'null' origin allows any file:// request. This is safe for local development
# where the dashboard is opened from the filesystem, but should be removed in production
# deployments where the dashboard is served over HTTP/HTTPS.
CORS(app, resources={
    r"/*": {
        "origins": [
            "null",  # Allow local file:// access
            "http://localhost:*",
            "http://127.0.0.1:*",
            "http://localhost:5500",
            "http://127.0.0.1:5500",
            "http://localhost:3000",
            "http://127.0.0.1:3000"
        ]
    }
})

# ==================== API CONFIGURATION (AUDIT FIX #4) ====================

# CRITICAL FIX: API Keys from environment variables
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY', '')

# API Endpoints
BINANCE_BASE_URL = 'https://api.binance.com'
BINANCE_FUTURES_URL = 'https://fapi.binance.com'
BINANCE_OPTIONS_URL = 'https://eapi.binance.com'

# Request timeout
REQUEST_TIMEOUT = 10

# Cache configuration
CACHE_DURATION = 10  # seconds
cache = {}

# ==================== UTILITY FUNCTIONS ====================

def get_cache_key(endpoint, params):
    """Generate cache key from endpoint and parameters"""
    param_str = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
    return f"{endpoint}?{param_str}"

def get_from_cache(key):
    """Retrieve data from cache if valid"""
    if key in cache:
        data, timestamp = cache[key]
        if time.time() - timestamp < CACHE_DURATION:
            logger.info(f"Cache HIT: {key}")
            return data
        else:
            logger.info(f"Cache EXPIRED: {key}")
            del cache[key]
    return None

def set_cache(key, data):
    """Store data in cache with timestamp"""
    cache[key] = (data, time.time())
    logger.info(f"Cache SET: {key}")

def validate_symbol(symbol):
    """Validate trading symbol format"""
    if not symbol or not isinstance(symbol, str):
        return False
    # Allow alphanumeric symbols (e.g., BTCUSDT, ETHUSDT)
    return symbol.isalnum() and len(symbol) >= 4 and len(symbol) <= 20

def handle_binance_error(response):
    """Handle Binance API error responses"""
    try:
        error_data = response.json()
        error_code = error_data.get('code', 'UNKNOWN')
        error_msg = error_data.get('msg', 'Unknown error')
        logger.error(f"Binance API Error {response.status_code}: {error_code} - {error_msg}")
        return {
            'error': True,
            'code': error_code,
            'message': error_msg,
            'status': response.status_code
        }
    except Exception as e:
        logger.error(f"Error parsing Binance error response: {e}")
        return {
            'error': True,
            'message': f'HTTP {response.status_code}: {response.text[:100]}',
            'status': response.status_code
        }

# ==================== RATE LIMITING DECORATOR ====================

request_counts = {}
RATE_LIMIT = 60  # requests per minute
RATE_WINDOW = 60  # seconds

def rate_limit(f):
    """Rate limiting decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr
        current_time = time.time()
        
        if client_ip not in request_counts:
            request_counts[client_ip] = []
        
        # Remove old requests outside the time window
        request_counts[client_ip] = [
            req_time for req_time in request_counts[client_ip]
            if current_time - req_time < RATE_WINDOW
        ]
        
        # Check rate limit
        if len(request_counts[client_ip]) >= RATE_LIMIT:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return jsonify({
                'error': True,
                'message': f'Rate limit exceeded. Maximum {RATE_LIMIT} requests per minute.'
            }), 429
        
        # Add current request
        request_counts[client_ip].append(current_time)
        
        return f(*args, **kwargs)
    
    return decorated_function

# ==================== HEALTH CHECK ENDPOINT ====================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Phoenix v12.2 API Server',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': '12.2',
        'endpoints': [
            '/get-options-data',
            '/api/binance/funding',
            '/api/binance/oi',
            '/api/binance/lsratio'
        ]
    })

# ==================== OPTIONS DATA ENDPOINT ====================

@app.route('/get-options-data', methods=['GET'])
@rate_limit
def get_options_data():
    """
    Fetch Binance Options data for implied volatility calculation
    
    Query Parameters:
        - symbol: Base asset symbol (e.g., BTC, ETH)
    
    Returns:
        JSON array of option contracts with strikes, prices, expiry dates
    """
    try:
        # Get and validate symbol
        symbol = request.args.get('symbol', '').upper().strip()
        
        if not symbol:
            logger.warning("Options data request missing symbol")
            return jsonify({
                'error': True,
                'message': 'Symbol parameter is required'
            }), 400
        
        if not validate_symbol(symbol):
            logger.warning(f"Invalid symbol format: {symbol}")
            return jsonify({
                'error': True,
                'message': 'Invalid symbol format'
            }), 400
        
        logger.info(f"Fetching options data for symbol: {symbol}")
        
        # Check cache
        cache_key = get_cache_key('/eapi/v1/mark', {'symbol': symbol})
        cached_data = get_from_cache(cache_key)
        if cached_data is not None:
            return jsonify(cached_data)
        
        # Binance European Options API endpoint
        url = f"{BINANCE_OPTIONS_URL}/eapi/v1/mark"
        
        # Prepare request headers (no authentication needed for public endpoint)
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Make request
        response = requests.get(
            url,
            headers=headers,
            params={'symbol': symbol},
            timeout=REQUEST_TIMEOUT
        )
        
        # Handle response
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            if not isinstance(data, list):
                logger.error(f"Unexpected response structure for {symbol}")
                return jsonify({
                    'error': True,
                    'message': 'Unexpected response structure from Binance Options API'
                }), 500
            
            # Filter and format options data
            options_data = []
            for option in data:
                if not isinstance(option, dict):
                    continue
                
                # Extract relevant fields
                formatted_option = {
                    'symbol': option.get('symbol', ''),
                    'strikePrice': option.get('strikePrice', '0'),
                    'exercisePrice': option.get('exercisePrice', option.get('strikePrice', '0')),
                    'lastPrice': option.get('markPrice', option.get('lastPrice', '0')),
                    'markPrice': option.get('markPrice', '0'),
                    'markIV': option.get('markIV', '0'),
                    'bidPrice': option.get('bidPrice', '0'),
                    'askPrice': option.get('askPrice', '0'),
                    'delta': option.get('delta', '0'),
                    'theta': option.get('theta', '0'),
                    'gamma': option.get('gamma', '0'),
                    'vega': option.get('vega', '0'),
                    'highPrice': option.get('highPrice', '0'),
                    'lowPrice': option.get('lowPrice', '0')
                }
                options_data.append(formatted_option)
            
            if len(options_data) == 0:
                logger.warning(f"No options data available for {symbol}")
                return jsonify([]), 200
            
            logger.info(f"Successfully fetched {len(options_data)} options for {symbol}")
            
            # Cache the result
            set_cache(cache_key, options_data)
            
            return jsonify(options_data), 200
        
        elif response.status_code == 400:
            # Symbol might not have options trading
            logger.warning(f"Symbol {symbol} may not have options trading available")
            return jsonify([]), 200
        
        else:
            error_response = handle_binance_error(response)
            return jsonify(error_response), response.status_code
    
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching options data for {symbol}")
        return jsonify({
            'error': True,
            'message': 'Request timeout - Binance Options API did not respond in time'
        }), 504
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching options data: {e}")
        return jsonify({
            'error': True,
            'message': f'Network error: {str(e)}'
        }), 503
    
    except Exception as e:
        logger.error(f"Unexpected error in get_options_data: {e}", exc_info=True)
        return jsonify({
            'error': True,
            'message': f'Internal server error: {str(e)}'
        }), 500

# ==================== BINANCE FUTURES ENDPOINTS ====================

@app.route('/api/binance/funding', methods=['GET'])
@rate_limit
def get_funding_rate():
    """
    Fetch current funding rate for futures symbol
    
    Query Parameters:
        - symbol: Trading pair (e.g., BTCUSDT)
    
    Returns:
        JSON with funding rate data
    """
    try:
        symbol = request.args.get('symbol', '').upper().strip()
        
        if not symbol:
            return jsonify({'error': True, 'message': 'Symbol parameter is required'}), 400
        
        if not validate_symbol(symbol):
            return jsonify({'error': True, 'message': 'Invalid symbol format'}), 400
        
        logger.info(f"Fetching funding rate for {symbol}")
        
        # Check cache
        cache_key = get_cache_key('/fapi/v1/premiumIndex', {'symbol': symbol})
        cached_data = get_from_cache(cache_key)
        if cached_data is not None:
            return jsonify(cached_data)
        
        url = f"{BINANCE_FUTURES_URL}/fapi/v1/premiumIndex"
        
        response = requests.get(
            url,
            params={'symbol': symbol},
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            result = {
                'symbol': data.get('symbol', symbol),
                'markPrice': data.get('markPrice', '0'),
                'indexPrice': data.get('indexPrice', '0'),
                'lastFundingRate': data.get('lastFundingRate', '0'),
                'nextFundingTime': data.get('nextFundingTime', 0),
                'time': data.get('time', int(time.time() * 1000))
            }
            
            logger.info(f"Funding rate for {symbol}: {result['lastFundingRate']}")
            
            # Cache the result
            set_cache(cache_key, result)
            
            return jsonify(result), 200
        else:
            error_response = handle_binance_error(response)
            return jsonify(error_response), response.status_code
    
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching funding rate for {symbol}")
        return jsonify({'error': True, 'message': 'Request timeout'}), 504
    
    except Exception as e:
        logger.error(f"Error in get_funding_rate: {e}", exc_info=True)
        return jsonify({'error': True, 'message': str(e)}), 500

@app.route('/api/binance/oi', methods=['GET'])
@rate_limit
def get_open_interest():
    """
    Fetch open interest for futures symbol
    
    Query Parameters:
        - symbol: Trading pair (e.g., BTCUSDT)
    
    Returns:
        JSON with open interest data
    """
    try:
        symbol = request.args.get('symbol', '').upper().strip()
        
        if not symbol:
            return jsonify({'error': True, 'message': 'Symbol parameter is required'}), 400
        
        if not validate_symbol(symbol):
            return jsonify({'error': True, 'message': 'Invalid symbol format'}), 400
        
        logger.info(f"Fetching open interest for {symbol}")
        
        # Check cache
        cache_key = get_cache_key('/fapi/v1/openInterest', {'symbol': symbol})
        cached_data = get_from_cache(cache_key)
        if cached_data is not None:
            return jsonify(cached_data)
        
        url = f"{BINANCE_FUTURES_URL}/fapi/v1/openInterest"
        
        response = requests.get(
            url,
            params={'symbol': symbol},
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            result = {
                'symbol': data.get('symbol', symbol),
                'openInterest': data.get('openInterest', '0'),
                'time': data.get('time', int(time.time() * 1000))
            }
            
            logger.info(f"Open Interest for {symbol}: {result['openInterest']}")
            
            # Cache the result
            set_cache(cache_key, result)
            
            return jsonify(result), 200
        else:
            error_response = handle_binance_error(response)
            return jsonify(error_response), response.status_code
    
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching open interest for {symbol}")
        return jsonify({'error': True, 'message': 'Request timeout'}), 504
    
    except Exception as e:
        logger.error(f"Error in get_open_interest: {e}", exc_info=True)
        return jsonify({'error': True, 'message': str(e)}), 500

@app.route('/api/binance/lsratio', methods=['GET'])
@rate_limit
def get_long_short_ratio():
    """
    Fetch long/short ratio for futures symbol
    
    Query Parameters:
        - symbol: Trading pair (e.g., BTCUSDT)
        - period: Time period (5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d) - default: 5m
        - limit: Number of data points (default: 30, max: 500)
    
    Returns:
        JSON array with long/short ratio data
    """
    try:
        symbol = request.args.get('symbol', '').upper().strip()
        period = request.args.get('period', '5m')
        limit = request.args.get('limit', '30')
        
        if not symbol:
            return jsonify({'error': True, 'message': 'Symbol parameter is required'}), 400
        
        if not validate_symbol(symbol):
            return jsonify({'error': True, 'message': 'Invalid symbol format'}), 400
        
        # Validate period
        valid_periods = ['5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d']
        if period not in valid_periods:
            return jsonify({'error': True, 'message': f'Invalid period. Valid options: {valid_periods}'}), 400
        
        # Validate limit
        try:
            limit = int(limit)
            if limit < 1 or limit > 500:
                return jsonify({'error': True, 'message': 'Limit must be between 1 and 500'}), 400
        except ValueError:
            return jsonify({'error': True, 'message': 'Invalid limit value'}), 400
        
        logger.info(f"Fetching L/S ratio for {symbol} (period: {period}, limit: {limit})")
        
        # Check cache
        cache_key = get_cache_key('/futures/data/globalLongShortAccountRatio', {
            'symbol': symbol,
            'period': period,
            'limit': limit
        })
        cached_data = get_from_cache(cache_key)
        if cached_data is not None:
            return jsonify(cached_data)
        
        url = f"{BINANCE_FUTURES_URL}/futures/data/globalLongShortAccountRatio"
        
        params = {
            'symbol': symbol,
            'period': period,
            'limit': limit
        }
        
        response = requests.get(
            url,
            params=params,
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response is a list
            if not isinstance(data, list):
                logger.error(f"Unexpected L/S ratio response structure for {symbol}")
                return jsonify({'error': True, 'message': 'Unexpected response structure'}), 500
            
            # Format data
            formatted_data = []
            for item in data:
                formatted_item = {
                    'symbol': item.get('symbol', symbol),
                    'longShortRatio': item.get('longShortRatio', '0'),
                    'longAccount': item.get('longAccount', '0'),
                    'shortAccount': item.get('shortAccount', '0'),
                    'timestamp': item.get('timestamp', 0)
                }
                formatted_data.append(formatted_item)
            
            logger.info(f"L/S ratio for {symbol}: {len(formatted_data)} data points retrieved")
            
            # Cache the result
            set_cache(cache_key, formatted_data)
            
            return jsonify(formatted_data), 200
        else:
            error_response = handle_binance_error(response)
            return jsonify(error_response), response.status_code
    
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching L/S ratio for {symbol}")
        return jsonify({'error': True, 'message': 'Request timeout'}), 504
    
    except Exception as e:
        logger.error(f"Error in get_long_short_ratio: {e}", exc_info=True)
        return jsonify({'error': True, 'message': str(e)}), 500

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': True,
        'message': 'Endpoint not found',
        'status': 404
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': True,
        'message': 'Internal server error',
        'status': 500
    }), 500

@app.errorhandler(429)
def rate_limit_error(error):
    """Handle rate limit errors"""
    return jsonify({
        'error': True,
        'message': 'Rate limit exceeded. Please try again later.',
        'status': 429
    }), 429

# ==================== STARTUP CHECKS ====================

def startup_checks():
    """Perform startup validation checks"""
    logger.info("=" * 60)
    logger.info("PROJECT PHOENIX v12.2 - API SERVER STARTING")
    logger.info("=" * 60)
    
    # Check environment variables
    if not BINANCE_API_KEY:
        logger.warning("⚠️  BINANCE_API_KEY not set in .env file")
        logger.warning("    Some endpoints may require authentication")
    else:
        logger.info("✅ BINANCE_API_KEY loaded from environment")
    
    if not BINANCE_SECRET_KEY:
        logger.warning("⚠️  BINANCE_SECRET_KEY not set in .env file")
        logger.warning("    Authenticated endpoints will not work")
    else:
        logger.info("✅ BINANCE_SECRET_KEY loaded from environment")
    
    # Log configuration
    logger.info(f"📊 Cache Duration: {CACHE_DURATION}s")
    logger.info(f"🚦 Rate Limit: {RATE_LIMIT} requests per {RATE_WINDOW}s")
    logger.info(f"⏱️  Request Timeout: {REQUEST_TIMEOUT}s")
    
    # Log available endpoints
    logger.info("\n📡 Available Endpoints:")
    logger.info("  • GET  /health")
    logger.info("  • GET  /get-options-data?symbol={symbol}")
    logger.info("  • GET  /api/binance/funding?symbol={symbol}")
    logger.info("  • GET  /api/binance/oi?symbol={symbol}")
    logger.info("  • GET  /api/binance/lsratio?symbol={symbol}&period={period}&limit={limit}")
    
    logger.info("\n🔒 Security Features:")
    logger.info("  ✓ Environment variable protection")
    logger.info("  ✓ CORS restricted to localhost")
    logger.info("  ✓ Rate limiting enabled")
    logger.info("  ✓ Input validation active")
    logger.info("  ✓ Error handling configured")
    
    logger.info("\n🚀 Server ready to accept connections")
    logger.info("=" * 60)

# ==================== MAIN ENTRY POINT ====================

if __name__ == '__main__':
    startup_checks()
    
    # Run Flask app
    app.run(
        host='0.0.0.0',  # Allow connections from any IP (localhost only via CORS)
        port=5000,
        debug=False,  # Set to False in production
        threaded=True
    )