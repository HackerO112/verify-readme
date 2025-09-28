@echo off
echo Starting VeriCode...
echo.
echo Please wait while the application loads...
echo.
echo Once ready, open your browser and go to: http://localhost:3000
echo.
echo To stop VeriCode, close this window.
echo.

REM Check if we're in the right directory
if not exist "package.json" (
    echo Error: Please run this script from the VeriCode folder
    echo.
    pause
    exit /b 1
)

REM Start the application
npm run dev

pause