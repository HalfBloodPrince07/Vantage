@echo off
echo ========================================
echo LocalLens React Frontend Setup
echo ========================================
echo.

echo Step 1/3: Installing Node.js dependencies...
call npm install

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: npm install failed!
    echo Please make sure Node.js is installed.
    pause
    exit /b 1
)

echo.
echo Step 2/3: Checking backend connection...
curl -s http://localhost:8000/health >nul 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo WARNING: Backend not running on port 8000
    echo Please start the backend with:
    echo   uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
    echo.
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start the development server:
echo   npm run dev
echo.
echo Then open: http://localhost:3000
echo.
pause
