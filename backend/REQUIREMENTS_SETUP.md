# Backend Requirements Setup Guide

## Issue Fixed

The pip installation issue has been permanently resolved by:

1. **Removed `pip>=25.2` from requirements.txt** - This was causing installation conflicts
2. **Updated pip separately** - Pip should be upgraded independently, not through requirements.txt
3. **Created setup scripts** - Automated setup scripts for both Windows and Linux/Mac

## How to Install Requirements

### Option 1: Use the Setup Scripts (Recommended)

**Windows:**
```bash
cd backend
setup-requirements.bat
```

**Linux/Mac:**
```bash
cd backend
./setup-requirements.sh
```

### Option 2: Manual Installation

**Step 1: Upgrade pip**
```bash
python -m pip install --upgrade pip
```

**Step 2: Install requirements**
```bash
python -m pip install -r requirements.txt
```

## Why This Fixes the Issue

1. **Pip conflicts**: Having `pip>=25.2` in requirements.txt can cause installation conflicts because pip is trying to modify itself while running
2. **Proper separation**: Pip should be upgraded independently before installing other packages
3. **Clean installation**: This ensures all packages are installed with the latest pip version

## Best Practices

1. **Never include pip in requirements.txt** - Upgrade pip separately
2. **Use virtual environments** - Always work in a virtual environment for Python projects
3. **Pin versions** - Use specific version numbers in requirements.txt for reproducible builds
4. **Regular updates** - Periodically update pip and packages

## Troubleshooting

If you encounter similar issues in the future:

1. **Clear pip cache**: `python -m pip cache purge`
2. **Use --no-cache-dir**: `python -m pip install --no-cache-dir -r requirements.txt`
3. **Check Python version**: Ensure you're using Python 3.8 or higher
4. **Virtual environment**: Make sure you're in the correct virtual environment

## Verification

After installation, verify everything works:
```bash
python -c "import fastapi, uvicorn; print('Backend dependencies installed successfully!')"
```
