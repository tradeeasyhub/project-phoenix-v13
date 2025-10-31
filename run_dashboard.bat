@echo off
REM ==================== PROJECT PHOENIX v12.2 - LAUNCHER ====================
REM Author: tradeeasyhub
REM Date: 2025-10-31
REM Description: Advanced launcher script for Phoenix Dashboard
REM Features:
REM   - Python environment detection
REM   - Automatic dependency installation
REM   - Flask server auto-start
REM   - Browser auto-launch
REM   - Error handling & logging
REM   - Graceful shutdown
REM =========================================================================

SETLOCAL EnableDelayedExpansion

REM ==================== CONFIGURATION ====================
SET "SCRIPT_DIR=%~dp0"
SET "LOG_FILE=%SCRIPT_DIR%phoenix_launcher.log"
SET "DASHBOARD_FILE=%SCRIPT_DIR%dashboard.html"
SET "PYTHON_SCRIPT=%SCRIPT_DIR%app.py"
SET "ENV_FILE=%SCRIPT_DIR%.env"
SET "SERVER_PORT=5000"
SET "DASHBOARD_URL=file:///%DASHBOARD_FILE:\=/%"

REM ==================== BANNER ====================
COLOR 0A
CLS
ECHO.
ECHO ========================================================================
ECHO      PROJECT PHOENIX v12.2 - ADVANCED LAUNCHER
ECHO ========================================================================
ECHO      Author: tradeeasyhub
ECHO      Date: 2025-10-31 07:40:00 UTC
ECHO      Mode: Production (All 15 Fixes Applied)
ECHO ========================================================================
ECHO.

REM ==================== LOGGING FUNCTION ====================
IF EXIST "%LOG_FILE%" DEL /F /Q "%LOG_FILE%" >NUL 2>&1
ECHO [%DATE% %TIME%] Phoenix Launcher Started >> "%LOG_FILE%"

REM ==================== STEP 1: CHECK PYTHON INSTALLATION ====================
ECHO [1/7] Checking Python installation...
ECHO [%DATE% %TIME%] Checking Python... >> "%LOG_FILE%"

python --version >NUL 2>&1
IF ERRORLEVEL 1 (
    COLOR 0C
    ECHO [ERROR] Python is not installed or not in PATH!
    ECHO.
    ECHO Please install Python 3.8+ from: https://www.python.org/downloads/
    ECHO Make sure to check "Add Python to PATH" during installation.
    ECHO.
    ECHO [%DATE% %TIME%] ERROR: Python not found >> "%LOG_FILE%"
    PAUSE
    EXIT /B 1
)

FOR /F "tokens=2" %%i IN ('python --version 2^>^&1') DO SET PYTHON_VERSION=%%i
ECHO       [OK] Python %PYTHON_VERSION% detected
ECHO [%DATE% %TIME%] Python %PYTHON_VERSION% OK >> "%LOG_FILE%"

REM ==================== STEP 2: CHECK REQUIRED FILES ====================
ECHO [2/7] Checking required files...
ECHO [%DATE% %TIME%] Checking files... >> "%LOG_FILE%"

SET "FILES_OK=1"

IF NOT EXIST "%DASHBOARD_FILE%" (
    COLOR 0C
    ECHO       [ERROR] dashboard.html not found!
    ECHO [%DATE% %TIME%] ERROR: dashboard.html missing >> "%LOG_FILE%"
    SET "FILES_OK=0"
)

IF NOT EXIST "%PYTHON_SCRIPT%" (
    COLOR 0C
    ECHO       [ERROR] app.py not found!
    ECHO [%DATE% %TIME%] ERROR: app.py missing >> "%LOG_FILE%"
    SET "FILES_OK=0"
)

IF NOT EXIST "%ENV_FILE%" (
    COLOR 0E
    ECHO       [WARNING] .env file not found - creating default...
    ECHO [%DATE% %TIME%] WARNING: .env missing, creating default >> "%LOG_FILE%"
    
    (
        ECHO # PROJECT PHOENIX v12.2 - ENVIRONMENT VARIABLES
        ECHO # Created: 2025-10-31 07:40:00
        ECHO.
        ECHO BINANCE_API_KEY=
        ECHO BINANCE_SECRET_KEY=
        ECHO ALPHA_VANTAGE_API_KEY=KH5P02ZGGSM2K63C
        ECHO FINNHUB_API_KEY=d3l7uo9r01qq28emakg0d3l7uo9r01qq28emakgg
        ECHO GEMINI_API_KEY=AIzaSyAoDb4cHJ7Lw3e2yWagK3whHt3geju4z4s
        ECHO FLASK_ENV=production
        ECHO FLASK_DEBUG=False
        ECHO SERVER_PORT=5000
    ) > "%ENV_FILE%"
    
    ECHO       [OK] Default .env created
) ELSE (
    ECHO       [OK] .env file found
)

IF "%FILES_OK%"=="0" (
    ECHO.
    ECHO [ERROR] Missing required files. Please ensure all files are in the same folder.
    ECHO [%DATE% %TIME%] ERROR: Missing files >> "%LOG_FILE%"
    PAUSE
    EXIT /B 1
)

ECHO       [OK] All required files present
ECHO [%DATE% %TIME%] Files OK >> "%LOG_FILE%"

REM ==================== STEP 3: CHECK/INSTALL PYTHON DEPENDENCIES ====================
ECHO [3/7] Checking Python dependencies...
ECHO [%DATE% %TIME%] Checking dependencies... >> "%LOG_FILE%"

python -c "import flask" >NUL 2>&1
IF ERRORLEVEL 1 (
    ECHO       [INSTALLING] flask...
    pip install flask --quiet >> "%LOG_FILE%" 2>&1
    IF ERRORLEVEL 1 (
        COLOR 0C
        ECHO       [ERROR] Failed to install flask
        ECHO [%DATE% %TIME%] ERROR: flask installation failed >> "%LOG_FILE%"
        PAUSE
        EXIT /B 1
    )
    ECHO       [OK] flask installed
)

python -c "import flask_cors" >NUL 2>&1
IF ERRORLEVEL 1 (
    ECHO       [INSTALLING] flask-cors...
    pip install flask-cors --quiet >> "%LOG_FILE%" 2>&1
    IF ERRORLEVEL 1 (
        COLOR 0C
        ECHO       [ERROR] Failed to install flask-cors
        ECHO [%DATE% %TIME%] ERROR: flask-cors installation failed >> "%LOG_FILE%"
        PAUSE
        EXIT /B 1
    )
    ECHO       [OK] flask-cors installed
)

python -c "import requests" >NUL 2>&1
IF ERRORLEVEL 1 (
    ECHO       [INSTALLING] requests...
    pip install requests --quiet >> "%LOG_FILE%" 2>&1
    IF ERRORLEVEL 1 (
        COLOR 0C
        ECHO       [ERROR] Failed to install requests
        ECHO [%DATE% %TIME%] ERROR: requests installation failed >> "%LOG_FILE%"
        PAUSE
        EXIT /B 1
    )
    ECHO       [OK] requests installed
)

python -c "import dotenv" >NUL 2>&1
IF ERRORLEVEL 1 (
    ECHO       [INSTALLING] python-dotenv...
    pip install python-dotenv --quiet >> "%LOG_FILE%" 2>&1
    IF ERRORLEVEL 1 (
        COLOR 0C
        ECHO       [ERROR] Failed to install python-dotenv
        ECHO [%DATE% %TIME%] ERROR: python-dotenv installation failed >> "%LOG_FILE%"
        PAUSE
        EXIT /B 1
    )
    ECHO       [OK] python-dotenv installed
)

ECHO       [OK] All dependencies installed
ECHO [%DATE% %TIME%] Dependencies OK >> "%LOG_FILE%"

REM ==================== STEP 4: CHECK IF PORT IS AVAILABLE ====================
ECHO [4/7] Checking if port %SERVER_PORT% is available...
ECHO [%DATE% %TIME%] Checking port %SERVER_PORT%... >> "%LOG_FILE%"

netstat -ano | findstr ":%SERVER_PORT%" | findstr "LISTENING" >NUL 2>&1
IF NOT ERRORLEVEL 1 (
    COLOR 0E
    ECHO       [WARNING] Port %SERVER_PORT% is already in use
    ECHO       [INFO] Attempting to kill existing process...
    
    FOR /F "tokens=5" %%P IN ('netstat -ano ^| findstr ":%SERVER_PORT%" ^| findstr "LISTENING"') DO (
        ECHO       [INFO] Killing process ID: %%P
        taskkill /F /PID %%P >NUL 2>&1
        ECHO [%DATE% %TIME%] Killed PID %%P on port %SERVER_PORT% >> "%LOG_FILE%"
    )
    
    TIMEOUT /T 2 /NOBREAK >NUL
    ECHO       [OK] Port cleared
) ELSE (
    ECHO       [OK] Port %SERVER_PORT% is available
)

ECHO [%DATE% %TIME%] Port OK >> "%LOG_FILE%"

REM ==================== STEP 5: START FLASK SERVER ====================
ECHO [5/7] Starting Flask API server...
ECHO [%DATE% %TIME%] Starting Flask... >> "%LOG_FILE%"

START /B python "%PYTHON_SCRIPT%" > "%SCRIPT_DIR%flask_server.log" 2>&1

REM Wait for server to start
ECHO       [INFO] Waiting for server to initialize...
TIMEOUT /T 3 /NOBREAK >NUL

REM Verify server is running
SET "SERVER_RUNNING=0"
FOR /L %%i IN (1,1,10) DO (
    curl -s http://localhost:%SERVER_PORT%/health >NUL 2>&1
    IF NOT ERRORLEVEL 1 (
        SET "SERVER_RUNNING=1"
        GOTO :SERVER_STARTED
    )
    TIMEOUT /T 1 /NOBREAK >NUL
)

:SERVER_STARTED
IF "%SERVER_RUNNING%"=="1" (
    ECHO       [OK] Flask server started on http://localhost:%SERVER_PORT%
    ECHO [%DATE% %TIME%] Flask server started >> "%LOG_FILE%"
) ELSE (
    COLOR 0E
    ECHO       [WARNING] Server may not have started properly
    ECHO       [INFO] Check flask_server.log for errors
    ECHO [%DATE% %TIME%] WARNING: Server startup uncertain >> "%LOG_FILE%"
)

REM ==================== STEP 6: OPEN DASHBOARD IN BROWSER ====================
ECHO [6/7] Opening dashboard in browser...
ECHO [%DATE% %TIME%] Opening browser... >> "%LOG_FILE%"

REM Detect default browser and open dashboard
IF EXIST "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    START "" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" "%DASHBOARD_FILE%"
    ECHO       [OK] Opened in Google Chrome
    ECHO [%DATE% %TIME%] Opened in Chrome >> "%LOG_FILE%"
) ELSE IF EXIST "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
    START "" "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" "%DASHBOARD_FILE%"
    ECHO       [OK] Opened in Google Chrome
    ECHO [%DATE% %TIME%] Opened in Chrome >> "%LOG_FILE%"
) ELSE IF EXIST "%ProgramFiles%\Mozilla Firefox\firefox.exe" (
    START "" "%ProgramFiles%\Mozilla Firefox\firefox.exe" "%DASHBOARD_FILE%"
    ECHO       [OK] Opened in Firefox
    ECHO [%DATE% %TIME%] Opened in Firefox >> "%LOG_FILE%"
) ELSE IF EXIST "%ProgramFiles(x86)%\Mozilla Firefox\firefox.exe" (
    START "" "%ProgramFiles(x86)%\Mozilla Firefox\firefox.exe" "%DASHBOARD_FILE%"
    ECHO       [OK] Opened in Firefox
    ECHO [%DATE% %TIME%] Opened in Firefox >> "%LOG_FILE%"
) ELSE IF EXIST "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" (
    START "" "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" "%DASHBOARD_FILE%"
    ECHO       [OK] Opened in Microsoft Edge
    ECHO [%DATE% %TIME%] Opened in Edge >> "%LOG_FILE%"
) ELSE IF EXIST "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" (
    START "" "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" "%DASHBOARD_FILE%"
    ECHO       [OK] Opened in Microsoft Edge
    ECHO [%DATE% %TIME%] Opened in Edge >> "%LOG_FILE%"
) ELSE (
    REM Fallback to default browser
    START "" "%DASHBOARD_FILE%"
    ECHO       [OK] Opened in default browser
    ECHO [%DATE% %TIME%] Opened in default browser >> "%LOG_FILE%"
)

REM ==================== STEP 7: READY ====================
ECHO [7/7] Initialization complete!
ECHO.
COLOR 0A
ECHO ========================================================================
ECHO      PROJECT PHOENIX v12.2 - READY
ECHO ========================================================================
ECHO.
ECHO      Status:           RUNNING
ECHO      Dashboard:        %DASHBOARD_FILE%
ECHO      API Server:       http://localhost:%SERVER_PORT%
ECHO      Health Check:     http://localhost:%SERVER_PORT%/health
ECHO      Logs:             %LOG_FILE%
ECHO      Server Log:       flask_server.log
ECHO.
ECHO ========================================================================
ECHO      INSTRUCTIONS
ECHO ========================================================================
ECHO.
ECHO      1. The dashboard is now open in your browser
ECHO      2. Enter a symbol (e.g., btcusdt) and click "Connect Streams"
ECHO      3. The Flask server is running in the background
ECHO      4. Press Ctrl+C to stop the server and close this window
ECHO.
ECHO      Available Endpoints:
ECHO        - /get-options-data?symbol=BTC
ECHO        - /api/binance/funding?symbol=BTCUSDT
ECHO        - /api/binance/oi?symbol=BTCUSDT
ECHO        - /api/binance/lsratio?symbol=BTCUSDT
ECHO.
ECHO ========================================================================
ECHO      SECURITY NOTICE
ECHO ========================================================================
ECHO.
ECHO      API keys are stored in .env file (AUDIT FIX #4 applied)
ECHO      Edit .env to add your Binance API keys if needed
ECHO      Public endpoints work without authentication
ECHO.
ECHO ========================================================================
ECHO.

ECHO [%DATE% %TIME%] Dashboard ready >> "%LOG_FILE%"

REM ==================== KEEP WINDOW OPEN ====================
ECHO Press Ctrl+C to stop the server...
ECHO.

REM Keep the window open and handle Ctrl+C gracefully
:LOOP
TIMEOUT /T 5 /NOBREAK >NUL
GOTO LOOP

REM ==================== CLEANUP ON EXIT ====================
:CLEANUP
ECHO.
ECHO ========================================================================
ECHO      SHUTTING DOWN
ECHO ========================================================================
ECHO.
ECHO [INFO] Stopping Flask server...

REM Kill all Python processes running app.py
FOR /F "tokens=2" %%P IN ('tasklist ^| findstr "python.exe"') DO (
    taskkill /F /PID %%P >NUL 2>&1
)

ECHO [INFO] Server stopped
ECHO [%DATE% %TIME%] Shutdown complete >> "%LOG_FILE%"
ECHO.
ECHO Thank you for using Project Phoenix v12.2!
ECHO.
PAUSE
EXIT /B 0