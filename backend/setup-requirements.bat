@echo off
echo Setting up Python requirements for Legal Analyzer Backend...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo Python found. Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Installing requirements...
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERROR: Failed to install requirements
    echo Please check the error messages above
    pause
    exit /b 1
)

echo.
echo SUCCESS: All requirements installed successfully!
echo You can now run the backend with: python main.py
echo.
pause
