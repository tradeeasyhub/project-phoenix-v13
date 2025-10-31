#!/usr/bin/env python3
"""
Test script to verify CORS configuration for Project Phoenix v12.2
Tests that the server allows 'null' origin for local file:// access
"""

import requests
import time
import subprocess
import sys
import signal
import os

# Configuration
SERVER_PORT = 5000
SERVER_BASE_URL = f"http://localhost:{SERVER_PORT}"
SHUTDOWN_TIMEOUT = 5  # seconds

def start_server():
    """Start the Flask server in the background"""
    print("Starting Flask server...")
    server_process = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    # Wait for server to be ready with health check polling
    max_retries = 20
    retry_delay = 0.5
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{SERVER_BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                print(f"Server ready after {(attempt + 1) * retry_delay:.1f}s")
                return server_process
        except requests.exceptions.RequestException:
            pass
        time.sleep(retry_delay)
    
    raise RuntimeError("Server failed to start within expected time")

def test_cors_null_origin():
    """Test CORS with null origin (file:// access)"""
    print("\n=== Testing CORS with 'null' origin ===")
    try:
        response = requests.get(
            f"{SERVER_BASE_URL}/health",
            headers={"Origin": "null"}
        )
        
        # Check status code
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Health endpoint returns 200 OK")
        
        # Check CORS header
        cors_header = response.headers.get("Access-Control-Allow-Origin")
        assert cors_header == "null", f"Expected 'null', got '{cors_header}'"
        print("✓ CORS header 'Access-Control-Allow-Origin: null' is present")
        
        # Check response data
        data = response.json()
        assert data.get("status") == "healthy", "Server not healthy"
        print("✓ Server reports healthy status")
        
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

def test_cors_localhost_origin():
    """Test CORS with localhost origin"""
    print("\n=== Testing CORS with 'localhost' origin ===")
    try:
        response = requests.get(
            f"{SERVER_BASE_URL}/health",
            headers={"Origin": "http://localhost:5500"}
        )
        
        # Check status code
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Health endpoint returns 200 OK")
        
        # Check CORS header
        cors_header = response.headers.get("Access-Control-Allow-Origin")
        assert cors_header == "http://localhost:5500", f"Expected 'http://localhost:5500', got '{cors_header}'"
        print("✓ CORS header reflects localhost origin correctly")
        
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

def test_endpoints():
    """Test that all endpoints are accessible"""
    print("\n=== Testing API Endpoints ===")
    endpoints = [
        "/health",
        "/get-options-data?symbol=BTCUSDT",
        "/api/binance/funding?symbol=BTCUSDT",
        "/api/binance/oi?symbol=BTCUSDT",
        "/api/binance/lsratio?symbol=BTCUSDT&period=5m&limit=1"
    ]
    
    all_passed = True
    for endpoint in endpoints:
        try:
            response = requests.get(
                f"{SERVER_BASE_URL}{endpoint}",
                headers={"Origin": "null"},
                timeout=5
            )
            
            # Check CORS header is present
            cors_header = response.headers.get("Access-Control-Allow-Origin")
            if cors_header == "null":
                print(f"✓ {endpoint} - CORS enabled")
            else:
                print(f"✗ {endpoint} - CORS header missing or incorrect")
                all_passed = False
        except Exception as e:
            print(f"✗ {endpoint} - Error: {e}")
            all_passed = False
    
    return all_passed

def main():
    """Main test runner"""
    print("=" * 60)
    print("Project Phoenix v12.2 - CORS Configuration Test")
    print("=" * 60)
    
    server_process = None
    try:
        # Start server
        server_process = start_server()
        
        # Run tests
        test1 = test_cors_null_origin()
        test2 = test_cors_localhost_origin()
        test3 = test_endpoints()
        
        # Summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        
        all_passed = test1 and test2 and test3
        
        if all_passed:
            print("✅ All tests passed!")
            print("\nThe CORS fix is working correctly.")
            print("Dashboard can now be opened from file:// protocol without CORS errors.")
            return 0
        else:
            print("❌ Some tests failed!")
            print("\nPlease review the errors above.")
            return 1
            
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Test execution failed: {e}")
        return 1
    finally:
        # Stop server
        if server_process:
            print("\n\nStopping Flask server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=SHUTDOWN_TIMEOUT)
                print("Server stopped gracefully")
            except subprocess.TimeoutExpired:
                print("Server termination timed out, force killing...")
                server_process.kill()
                server_process.wait()
                print("Server force stopped")

if __name__ == "__main__":
    sys.exit(main())
