@echo off
REM Vantage Run Script for Windows
REM This script starts all required services for Vantage

setlocal enabledelayedexpansion

echo ==============================================
echo    Vantage - AI Document Search System
echo ==============================================
echo.

REM Check Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

REM Check Node
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js not found. Please install Node.js 16+
    pause
    exit /b 1
)

echo [CHECK] Python: OK
echo [CHECK] Node.js: OK

REM Check Ollama
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Ollama not running
    echo Please start Ollama in a separate terminal:
    echo    ollama serve
    echo.
    pause
)

REM Check OpenSearch
curl -s http://localhost:9200 >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] OpenSearch not running on localhost:9200
    echo Please start OpenSearch in a separate terminal:
    echo    cd C:\opensearch
    echo    .\bin\opensearch.bat
    echo.
    pause
    echo.
    pause
)

REM Check Redis
curl -s http://localhost:6379 >nul 2>&1
REM Redis doesn't respond to HTTP, so we just check if the port is open using netstat or similar if possible, 
REM but curl might fail with a specific error if port is open but not HTTP. 
REM Simpler approach for batch script without external tools is hard.
REM Let's try a simple netstat check.
netstat -an | find "6379" >nul
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Redis not running on port 6379
    echo Session memory will be in-memory only ^(non-persistent^)
    echo To enable persistence, start Redis:
    echo    redis-server
    echo.
    REM We don't pause here, just warn
)

REM Create logs directory
if not exist logs mkdir logs

echo.
echo [INFO] Starting LocalLens services...
echo ==============================================
echo.

REM Start backend
echo [START] Backend API (port 8000)...
start "LocalLens Backend" /MIN cmd /c "python -m backend.api > logs\backend.log 2>&1"
timeout /t 3 /nobreak >nul

REM Check backend
curl -s http://localhost:8000/health >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Backend failed to start
    echo Check logs\backend.log for details
    pause
    exit /b 1
)
echo [OK] Backend running

REM Start frontend
echo [START] Frontend (port 5173)...
cd frontend
start "LocalLens Frontend" /MIN cmd /c "npm run dev > ..\logs\frontend.log 2>&1"
cd ..
timeout /t 3 /nobreak >nul

echo.
echo ==============================================
echo    LocalLens is ready!
echo ==============================================
echo.
echo   Frontend:   http://localhost:5173
echo   Backend:    http://localhost:8000
echo   OpenSearch: http://localhost:9200
echo.
echo   Logs:
echo     Backend:  logs\backend.log
echo     Frontend: logs\frontend.log
echo.
echo [INFO] Check the started windows for live logs
echo [INFO] Close those windows to stop services
echo.
pause
