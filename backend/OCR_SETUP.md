# OCR Setup Guide

This document explains how OCR (Optical Character Recognition) is configured in the Legal Document Analyzer and how to troubleshoot issues.

## Overview

The application uses **Tesseract OCR** for extracting text from images and scanned PDFs. OCR is automatically installed in Docker environments and provides fallback handling when unavailable.

## Docker Environment (Render, Fly.io, etc.)

OCR dependencies are **automatically installed** in the Docker image:

- `tesseract-ocr` - OCR engine
- `tesseract-ocr-eng` - English language data
- `libmagic1` - File type detection
- All required system libraries (libgl1, libglib2.0-0, etc.)

### Verification

The application logs OCR status on startup:

```
✓ Tesseract OCR: tesseract 4.1.1
✓ Available languages: eng
Starting application...
```

Check the `/health` endpoint:

```json
{
  "status": "healthy",
  "services": {
    "tesseract_ocr": "enabled",
    "image_processing": "available"
  }
}
```

## Local Development

### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-eng libmagic1
```

### macOS

```bash
brew install tesseract libmagic
```

### Windows

1. Download Tesseract installer from [tesseract-ocr](https://github.com/UB-Mannheim/tesseract/wiki)
2. Install to `C:\Program Files\Tesseract-OCR\`
3. The application will auto-detect the installation

### Verify Installation

Run the verification script:

```bash
cd backend
python verify_ocr.py
```

Expected output:

```
============================================================
OCR & File Type Detection Verification
============================================================

System Dependencies:
✓ Tesseract OCR installed: tesseract 4.1.1
✓ Tesseract languages available: eng

Python Packages:
✓ Python package 'pytesseract' installed
✓ Python package 'python-magic' installed
✓ Python package 'PIL' installed
✓ Python package 'PyMuPDF' installed

File Type Detection:
✓ libmagic (python-magic) working

============================================================
✓ All checks passed! OCR is ready to use.
============================================================
```

## Fallback Behavior

When Tesseract is not available:

1. **PDF Processing**: Extracts native text, skips OCR on scanned pages
2. **Image Processing**: Returns error message with installation instructions
3. **Health Check**: Reports OCR status as "disabled"
4. **Logs**: Clear warnings about missing OCR capabilities

The application continues to function normally for text-based PDFs.

## Troubleshooting

### Issue: "OCR not available" in Docker

**Solution**: Rebuild the Docker image to ensure dependencies are installed:

```bash
docker-compose build --no-cache backend
docker-compose up backend
```

### Issue: "Tesseract not found" locally

**Solution**: Install Tesseract using the commands above, then restart the application.

### Issue: Images fail to process

**Check**:
1. Verify OCR status: `curl http://localhost:8000/health`
2. Check logs for Tesseract errors
3. Run `python verify_ocr.py` to diagnose

### Issue: Poor OCR accuracy

**Improvements**:
- Use higher resolution images (300+ DPI)
- Ensure good contrast between text and background
- Avoid skewed or rotated text
- Use clear, non-decorative fonts

## Architecture

### OCR Detection

The `DocumentProcessor` automatically detects Tesseract on startup:

1. Checks common installation paths
2. Tests Tesseract version command
3. Sets `tesseract_available` flag
4. Logs status for debugging

### Image Enhancement

Before OCR, images are preprocessed:

- Convert to grayscale
- Resize if too small (min 1000px)
- Denoise with median filter
- Enhance contrast and sharpness
- Apply adaptive thresholding

### Error Handling

OCR failures are handled gracefully:

- PDFs: Falls back to native text extraction
- Images: Returns clear error message
- Logs: Detailed warnings for debugging
- API: Includes processing notes in response

## Performance

### OCR Processing Time

- Small image (< 1MB): 1-3 seconds
- Large image (5-10MB): 3-8 seconds
- PDF with OCR (10 pages): 10-30 seconds

### Optimization

OCR runs asynchronously and includes:
- Rate limiting to prevent overload
- Concurrent request limiting (default: 5)
- Automatic cleanup of temp files
- Memory-efficient streaming

## Monitoring

### Startup Logs

```
[INFO] ✓ Tesseract OCR successfully initialized at /usr/bin/tesseract, version: 4.1.1
[INFO] DocumentProcessor initialized with OCR support enabled
[INFO] All services initialized successfully | OCR Status: ENABLED
```

### Health Endpoints

- `/health` - Basic OCR status
- `/health/deep` - Detailed OCR service check

### Processing Logs

```json
{
  "level": "INFO",
  "message": "Processing image with OCR: document.png",
  "file_id": "abc123",
  "processing_time": 2.45
}
```

## Additional Languages

To support more languages, install additional Tesseract language packs:

### Docker

Add to Dockerfile:

```dockerfile
RUN apt-get install -y \
    tesseract-ocr-fra \
    tesseract-ocr-spa \
    tesseract-ocr-deu
```

### Local

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr-fra tesseract-ocr-spa

# macOS
brew reinstall tesseract --with-all-languages
```

## Security

- OCR runs with non-root user permissions
- File size limits prevent memory exhaustion
- Input sanitization prevents injection attacks
- Temp files are automatically cleaned up
- No external OCR APIs used (all processing is local)
