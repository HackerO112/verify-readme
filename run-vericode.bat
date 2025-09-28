@echo off
setlocal enabledelayedexpansion

REM VeriCode - Live Documentation Verifier
REM Easy Setup Script for Non-Coders (Windows)
REM This script will set up and run the VeriCode application automatically

title VeriCode Setup

REM Color codes for Windows
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM Function to print colored output
:print_status
echo %BLUE%[INFO]%NC% %~1
goto :eof

:print_success
echo %GREEN%[SUCCESS]%NC% %~1
goto :eof

:print_warning
echo %YELLOW%[WARNING]%NC% %~1
goto :eof

:print_error
echo %RED%[ERROR]%NC% %~1
goto :eof

REM Function to check if command exists
:command_exists
where %1 >nul 2>&1
exit /b 0

REM Main script
cls
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║                    🚀 VeriCode Setup 🚀                      ║
echo ║                Live Documentation Verifier                   ║
echo ║                                                              ║
echo ║          Easy Setup Script for Non-Coders                   ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

call :print_status "System Information:"
echo   Operating System: Windows
if exist "node.exe" (
    for /f "tokens=*" %%a in ('node -v') do set NODE_VERSION=%%a
    echo   Node.js Version: !NODE_VERSION!
) else (
    echo   Node.js: Not installed
)
if exist "npm.cmd" (
    for /f "tokens=*" %%a in ('npm -v') do set NPM_VERSION=%%a
    echo   NPM Version: !NPM_VERSION!
) else (
    echo   NPM: Not installed
)
echo.

call :print_status "Starting VeriCode setup process..."
echo.

REM Check if Node.js is installed
call :print_status "Checking Node.js installation..."
if not exist "node.exe" (
    call :print_error "Node.js is not installed."
    echo.
    echo Please download and install Node.js from:
    echo https://nodejs.org/
    echo.
    echo After installation, please run this script again.
    pause
    exit /b 1
)
call :print_success "Node.js is installed"
echo.

REM Check if package.json exists
if not exist "package.json" (
    call :print_error "package.json not found. Please make sure you're in the correct directory."
    pause
    exit /b 1
)

REM Install dependencies
call :print_status "Installing project dependencies..."
npm install
if %errorlevel% neq 0 (
    call :print_error "Failed to install dependencies"
    pause
    exit /b 1
)
call :print_success "Dependencies installed successfully"
echo.

REM Setup database
call :print_status "Setting up database..."
if not exist "prisma\schema.prisma" (
    call :print_error "Prisma schema not found. Please make sure you're in the correct directory."
    pause
    exit /b 1
)

REM Generate Prisma client
npx prisma generate
if %errorlevel% neq 0 (
    call :print_error "Failed to generate Prisma client"
    pause
    exit /b 1
)

REM Push database schema
npm run db:push
if %errorlevel% neq 0 (
    call :print_error "Failed to setup database"
    pause
    exit /b 1
)
call :print_success "Database setup completed successfully"
echo.

REM Start application
call :print_status "Starting VeriCode application..."
echo.
call :print_success "VeriCode is starting up..."
call :print_status "Please wait a moment for the development server to initialize..."
call :print_status "Once ready, you can access VeriCode at: http://localhost:3000"
call :print_status "To stop the application, press Ctrl+C"
echo.

REM Start the development server
npm run dev
pause