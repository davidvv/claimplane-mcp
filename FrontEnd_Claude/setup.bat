@echo off
REM EasyAirClaim Portal Setup Script for Windows

echo.
echo =============================
echo EasyAirClaim Portal Setup
echo =============================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Node.js is not installed
    echo Please download and install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)

echo Checking Node.js version...
node -v
echo.

REM Install dependencies
echo Installing dependencies...
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully
echo.

REM Create .env file if it doesn't exist
if not exist .env (
    echo Creating .env file...
    copy .env.example .env >nul
    echo .env file created
    echo.
    echo IMPORTANT: Edit .env and add your API credentials:
    echo    - VITE_API_BASE_URL
    echo    - VITE_API_KEY
    echo.
) else (
    echo .env file already exists
    echo.
)

echo Setup complete!
echo.
echo Next steps:
echo   1. Edit .env and add your API credentials
echo   2. Run: npm run dev
echo   3. Open: http://localhost:3000
echo.
echo Documentation:
echo   - QUICKSTART.md  - Quick start guide
echo   - README.md      - Full documentation
echo   - DEPLOYMENT.md  - Deployment guide
echo.
echo Happy coding!
echo.
pause
