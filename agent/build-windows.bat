@echo off
REM Compliance Monitor Agent - Windows Build Script
REM This script builds and packages the agent for distribution

echo ================================================
echo Compliance Monitor Agent - Windows Build
echo ================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "main.py" (
    echo Error: main.py not found
    echo Please run this script from the agent directory
    pause
    exit /b 1
)

echo Step 1: Installing dependencies...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install runtime dependencies
    pause
    exit /b 1
)

python -m pip install -r requirements-build.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install build dependencies
    pause
    exit /b 1
)

echo.
echo Step 2: Building executable...
python build.py
if %errorlevel% neq 0 (
    echo Error: Build failed
    pause
    exit /b 1
)

echo.
echo Step 3: Creating distribution packages...
python deploy.py
if %errorlevel% neq 0 (
    echo Error: Deployment failed
    pause
    exit /b 1
)

echo.
echo ================================================
echo Build Complete!
echo ================================================
echo.
echo Created packages:
dir /b *.zip 2>nul
echo.
echo Files in release directory:
dir /b release\* 2>nul
echo.
echo Next steps:
echo 1. Test the executable: release\compliance-monitor-agent.exe
echo 2. Configure .env file with your server details
echo 3. Run installer: release\install.ps1 (as Administrator)
echo.
echo For distribution:
echo - compliance-monitor-agent-v1.0.0-windows.zip (Complete package)
echo - dist\compliance-monitor-agent-windows-amd64.zip (Portable version)
echo.
pause
