#!/bin/bash

echo "Setting up Python requirements for Legal Analyzer Backend..."
echo

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "ERROR: Python is not installed or not in PATH"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

echo "Python found. Upgrading pip..."
python -m pip install --upgrade pip

echo
echo "Installing requirements..."
python -m pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo
    echo "ERROR: Failed to install requirements"
    echo "Please check the error messages above"
    exit 1
fi

echo
echo "SUCCESS: All requirements installed successfully!"
echo "You can now run the backend with: python main.py"
echo
