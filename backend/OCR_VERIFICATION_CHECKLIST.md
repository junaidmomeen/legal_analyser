# OCR Verification Checklist

Use this checklist to verify OCR is working correctly in your deployment.

## Pre-Deployment

- [ ] Dockerfile includes `tesseract-ocr` and `tesseract-ocr-eng`
- [ ] Dockerfile includes `libmagic1`
- [ ] `startup.sh` exists and is executable
- [ ] `.dockerignore` exists to reduce image size
- [ ] `requirements.txt` includes `pytesseract` and `python-magic`

## Docker Build

```bash
docker-compose build backend
```

Expected output:
- [ ] Build completes without errors
- [ ] See: `tesseract --version` output during build
- [ ] No warnings about missing dependencies

## Deployment

```bash
docker-compose up backend
```

Startup logs should show:
- [ ] `✓ Tesseract OCR: tesseract X.X.X`
- [ ] `✓ Available languages: eng`
- [ ] `✓ libmagic installed`
- [ ] `DocumentProcessor initialized with OCR support enabled`
- [ ] `All services initialized successfully | OCR Status: ENABLED`

## Health Check Verification

### Basic Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "tesseract_ocr": "enabled",
    "image_processing": "available"
  }
}
```

- [ ] `tesseract_ocr` is `"enabled"` (not `"disabled"`)
- [ ] `image_processing` is `"available"` (not `"unavailable"`)

### Deep Health Check

```bash
curl http://localhost:8000/health/deep
```

Expected response includes:
```json
{
  "checks": {
    "ocr_service": {
      "status": "healthy",
      "tesseract_available": true,
      "message": "OCR fully operational"
    }
  }
}
```

- [ ] `ocr_service.status` is `"healthy"` (not `"warning"` or `"error"`)
- [ ] `tesseract_available` is `true`
- [ ] Message says "OCR fully operational"

## Functional Testing

### Test Image Upload

1. Upload a test image with text (PNG, JPG, etc.)
   ```bash
   curl -X POST http://localhost:8000/analyze \
     -F "file=@test_image.png"
   ```

2. Verify response:
   - [ ] Status code is 200 (not 400 or 500)
   - [ ] Response includes extracted text
   - [ ] No errors about "OCR not available"
   - [ ] Processing notes may mention "OCR processed image"

### Test PDF Upload

1. Upload a test PDF
   ```bash
   curl -X POST http://localhost:8000/analyze \
     -F "file=@test_document.pdf"
   ```

2. Verify response:
   - [ ] Status code is 200
   - [ ] Text extracted successfully
   - [ ] If scanned PDF: processing notes mention OCR

## Production Verification

### Render/Fly.io/Railway

After deploying to production:

1. Check deployment logs:
   ```bash
   # Render: View logs in dashboard
   # Fly.io: fly logs
   # Railway: railway logs
   ```

   - [ ] See OCR initialization messages
   - [ ] No errors about missing Tesseract
   - [ ] See "OCR Status: ENABLED"

2. Test production health endpoint:
   ```bash
   curl https://your-app.com/health
   ```

   - [ ] OCR status is "enabled"

3. Test image upload in production:
   - [ ] Upload image through frontend
   - [ ] Verify text extraction works
   - [ ] Check for any OCR-related errors

## Troubleshooting

If any checks fail:

### OCR Status Shows "disabled"

1. Check Dockerfile includes all dependencies
2. Rebuild Docker image with `--no-cache`
3. Verify startup.sh is executable
4. Check deployment logs for Tesseract errors

### Image Uploads Fail

1. Check error message in response
2. Verify file size is under limit (50MB)
3. Check image format is supported
4. Review application logs for OCR errors

### "Tesseract not found" Error

1. Rebuild Docker image
2. Verify apt-get install succeeded
3. Check PATH includes /usr/bin
4. Run `docker exec -it container tesseract --version`

### Performance Issues

1. Check image size (resize large images)
2. Monitor CPU/memory usage
3. Adjust MAX_CONCURRENT_ANALYSES
4. Review OCR timeout settings

## Local Development Verification

If running locally (not Docker):

1. Run verification script:
   ```bash
   cd backend
   python verify_ocr.py
   ```

2. Expected output:
   - [ ] All checks pass
   - [ ] Tesseract detected
   - [ ] Python packages installed
   - [ ] libmagic working

3. If checks fail:
   - Ubuntu/Debian: `sudo apt-get install tesseract-ocr libmagic1`
   - macOS: `brew install tesseract libmagic`
   - Windows: Install from [tesseract-ocr](https://github.com/UB-Mannheim/tesseract/wiki)

## Sign-Off

Once all checks pass:

- [ ] OCR works in development
- [ ] OCR works in Docker
- [ ] OCR works in production
- [ ] Health checks report correct status
- [ ] Image uploads process successfully
- [ ] Logs show clear OCR status

**Date**: ___________
**Verified by**: ___________
**Environment**: [ ] Dev [ ] Staging [ ] Production
**Platform**: [ ] Docker [ ] Render [ ] Fly.io [ ] Railway [ ] Other: ___________
