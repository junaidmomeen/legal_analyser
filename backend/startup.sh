#!/bin/sh
set -e

echo "================================"
echo "Legal Document Analyzer - Startup"
echo "================================"
echo ""

# Verify OCR installation
echo "Checking OCR dependencies..."
if command -v tesseract >/dev/null 2>&1; then
    TESSERACT_VERSION=$(tesseract --version 2>&1 | head -n1)
    echo "✓ Tesseract OCR: $TESSERACT_VERSION"
else
    echo "⚠ WARNING: Tesseract OCR not found - image processing will be disabled"
fi

# Check libmagic
if command -v ldconfig >/dev/null 2>&1; then
    if ldconfig -p | grep -q libmagic; then
        echo "✓ libmagic installed"
    else
        echo "⚠ WARNING: libmagic not found - file type detection may fall back to alternative methods"
    fi
else
    echo "⚠ WARNING: ldconfig not found - skipping libmagic check"
fi

echo ""
echo "Starting application..."
echo "================================"
echo ""

# Create required directories
mkdir -p /app/logs /app/exports /app/temp_uploads

# Start the application with dynamic port
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 4