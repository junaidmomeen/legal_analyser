from fastapi import (
    FastAPI,
    File,
    UploadFile,
    HTTPException,
    BackgroundTasks,
    Request,
    status,
    Depends,
)
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
import uvicorn
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
import uuid
import asyncio
from pathlib import Path
import aiofiles
import aiofiles.os
import hashlib

from services.document_processor import DocumentProcessor
from services.ai_analyzer import AIAnalyzer
from services.report_generator import ReportGenerator
from utils.file_validator import FileValidator
from utils.error_handler import error_handler
from middleware.rate_limiter import limiter, analysis_limiter
from middleware.security_headers import SecurityHeadersMiddleware
from slowapi.errors import RateLimitExceeded
from utils.request_guards import enforce_content_length_limit
from services.tasks import celery_app
from services.retention_jobs import get_retention_manager
from observability import setup_prometheus
from routers import system as system_router
from utils.cache_manager import get_cache_manager

# Load environment variables
load_dotenv()


# Validate required environment variables
def validate_environment():
    """Validate that all required environment variables are set"""
    required_vars = ["OPENROUTER_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
        logging.critical(error_msg)
        raise SystemExit(error_msg)


validate_environment()

# API Version
API_VERSION = "1.1.0"


# Configure structured logging
# (setup_logging function remains the same as before)
def setup_logging():
    """Setup structured logging configuration"""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=log_level)
    logger = logging.getLogger(__name__)
    return logger


logger = setup_logging()

# Configuration
TEMP_STORAGE_PATH = os.getenv("TEMP_STORAGE_PATH", "temp_uploads")
MAX_CONCURRENT_ANALYSES = int(os.getenv("MAX_CONCURRENT_ANALYSES", "5"))

# Create directories
Path(TEMP_STORAGE_PATH).mkdir(exist_ok=True)
Path("logs").mkdir(exist_ok=True)
Path("exports").mkdir(exist_ok=True)

# Initialize FastAPI app
app = FastAPI(
    title="Legal Document Analyzer API",
    description="AI-powered legal document analysis and clause extraction with comprehensive reporting",
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter


# Middleware
class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response


app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
setup_prometheus(app)

# CORS configuration
allowed_origins_str = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000"
)
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["Content-Type", "X-Requested-With", "X-Request-ID"],
)

# Initialize services and cache
cache_manager = get_cache_manager()
try:
    document_processor = DocumentProcessor()
    ai_analyzer = AIAnalyzer()
    report_generator = ReportGenerator()
    file_validator = FileValidator()
except Exception as e:
    logger.error(f"Failed to initialize services: {e}", exc_info=True)
    raise

# Concurrency control
analysis_semaphore = asyncio.Semaphore(MAX_CONCURRENT_ANALYSES)

# Expose shared state for routers (health endpoints, etc.)
app.state.document_processor = document_processor
app.state.analysis_cache = {}
app.state.analysis_semaphore = analysis_semaphore


# Exception Handlers
# (Exception handlers remain the same)
@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return error_handler.handle_rate_limit_exceeded(request, exc)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return error_handler.handle_validation_error(request, exc)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return error_handler.handle_http_exception(request, exc)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return error_handler.handle_general_exception(request, exc)


# Startup/Shutdown Events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        retention_manager = get_retention_manager()
        retention_manager.cache_manager = cache_manager
        await retention_manager.start()
        logger.info("Retention jobs initialized and started")
        # Log registered routes for debugging
        try:
            routes = [getattr(r, "path", str(r)) for r in app.router.routes]
            logger.info(f"Registered routes: {routes}")
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Failed to initialize retention jobs: {e}", exc_info=True)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        retention_manager = get_retention_manager()
        await retention_manager.stop()
        logger.info("Retention jobs stopped during shutdown")
    except Exception as e:
        logger.error(f"Error stopping retention jobs during shutdown: {e}")


# Routers
app.include_router(system_router.router)


# Fallback basic health endpoint (ensures /health exists even if router not loaded)
@app.get("/health")
async def basic_health():
    return {"status": "healthy"}


# Fallback supported formats
@app.get("/supported-formats")
async def basic_supported_formats():
    return {"formats": ["PDF", "PNG", "JPG", "JPEG", "GIF", "BMP", "TIFF", "WEBP"]}


# API Endpoints
@app.post("/analyze")
@analysis_limiter.limit("10/minute")
async def analyze_document(
    request: Request,
    file: UploadFile = File(...),
    _size_guard=Depends(enforce_content_length_limit),
):
    start_time = datetime.now()
    original_filename = file.filename or ""
    if not original_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Filename cannot be empty"
        )

    async with analysis_semaphore:
        file_id = str(uuid.uuid4())
        temp_file_path = None
        try:
            validation_result = await file_validator.validate_file(file)
            if not validation_result.is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=validation_result.error_message,
                )

            await file.seek(0)

            hasher = hashlib.sha256()
            chunk_size = 1024 * 1024
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)
            file_hash = hasher.hexdigest()
            await file.seek(0)

            existing_file_id = await cache_manager.get_file_id_by_hash(file_hash)
            if existing_file_id:
                cached_data = await cache_manager.get_analysis(existing_file_id)
                if cached_data:
                    logger.info(
                        f"Duplicate upload detected. Returning cached analysis for file_id: {existing_file_id}"
                    )
                    return cached_data["analysis"]  # Return the nested analysis data

            file_extension = validation_result.file_extension
            stored_filename = f"{file_id}.{file_extension}"
            temp_file_path = os.path.join(TEMP_STORAGE_PATH, stored_filename)

            async with aiofiles.open(temp_file_path, "wb") as buffer:
                while True:
                    chunk = await file.read(chunk_size)
                    if not chunk:
                        break
                    await buffer.write(chunk)

            processing_result = await document_processor.process_document(
                temp_file_path, validation_result.file_type
            )
            if not processing_result.success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=processing_result.error_message,
                )

            analysis_result = await ai_analyzer.analyze_document(
                processing_result.extracted_text,
                validation_result.file_type,
                original_filename,
            )
            processing_time = (datetime.now() - start_time).total_seconds()

            response_data = analysis_result.model_dump()
            response_data.update(
                {
                    "file_id": file_id,
                    "processing_time": processing_time,
                    "total_pages": processing_result.total_pages,
                    "word_count": processing_result.word_count,
                    "processing_notes": getattr(
                        processing_result, "processing_notes", []
                    ),
                }
            )

            cache_data = {
                "analysis": response_data,
                "file_path": temp_file_path,
                "original_filename": original_filename,
                "timestamp": datetime.now().isoformat(),
                "file_hash": file_hash,
            }
            await cache_manager.set_analysis(file_id, cache_data, file_hash)

            return response_data
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            if temp_file_path:
                try:
                    await aiofiles.os.remove(temp_file_path)
                except FileNotFoundError:
                    pass  # File already gone
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {e}",
            )


@app.get("/analysis/{file_id}")
async def get_analysis(file_id: str):
    data = await cache_manager.get_analysis(file_id)
    if not data:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return data["analysis"]


@app.get("/stats")
async def get_stats():
    return {
        "analysis_cache_size": await cache_manager.get_analysis_cache_size(),
        "export_tasks_size": await cache_manager.get_export_tasks_size(),
        "max_concurrent_analyses": MAX_CONCURRENT_ANALYSES,
        "active_analyses": MAX_CONCURRENT_ANALYSES - analysis_semaphore._value,
    }


@app.delete("/analyses")
async def clear_analyses(request: Request):
    all_analyses = await cache_manager.get_all_analysis_data()
    cleared_count = len(all_analyses)
    for data in all_analyses:
        try:
            file_path = data.get("file_path")
            if file_path and os.path.exists(file_path):
                await aiofiles.os.remove(file_path)
        except Exception as e:
            logger.error(f"Error cleaning up file: {e}")

    await cache_manager.clear_all_analyses()
    await cache_manager.clear_all_export_tasks()

    logger.info(f"All {cleared_count} analyses cleared.")
    return {"message": f"Successfully cleared {cleared_count} analysis records."}


@app.get("/documents/{file_id}")
async def get_document(file_id: str):
    try:
        uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file_id format"
        )

    cached_data = await cache_manager.get_analysis(file_id)
    if not cached_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or expired",
        )

    file_path_str = cached_data.get("file_path")
    if not file_path_str:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File path not found in cache"
        )

    # Path traversal safety check
    temp_storage_abs_path = Path(TEMP_STORAGE_PATH).resolve()
    resolved_path = Path(file_path_str).resolve()
    if temp_storage_abs_path not in resolved_path.parents:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden"
        )

    if not await aiofiles.os.path.exists(resolved_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original document file not found on disk",
        )

    return FileResponse(
        path=resolved_path,
        filename=cached_data.get("original_filename", "downloaded_file"),
    )


async def run_export(file_id: str, format: str, task_id: str):
    cached_data = await cache_manager.get_analysis(file_id)
    if not cached_data:
        logger.error(
            f"Export failed: Could not find analysis data for file_id {file_id}"
        )
        return

    analysis = cached_data["analysis"]
    original_filename = cached_data["original_filename"].rsplit(".", 1)[0]

    try:
        if format.lower() == "json":
            file_path = report_generator.export_as_json(analysis, original_filename)
        else:  # pdf
            file_path = report_generator.export_as_pdf(analysis, original_filename)

        await cache_manager.set_export_task(
            task_id, {"status": "completed", "file_path": file_path}
        )

    except Exception as e:
        await cache_manager.set_export_task(task_id, {"status": "failed"})
        logger.error(f"Export failed: {e}", exc_info=True)


@app.post("/export/{file_id}/{format}")
async def export_analysis(file_id: str, format: str, background_tasks: BackgroundTasks):
    if not await cache_manager.get_analysis(file_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found or expired",
        )

    if format.lower() not in ["json", "pdf"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported format. Use 'json' or 'pdf'",
        )

    task_id = str(uuid.uuid4())
    await cache_manager.set_export_task(
        task_id, {"status": "processing", "file_path": None}
    )

    if celery_app:
        celery_app.send_task(
            "backend.tasks.run_export_task", args=[file_id, format, task_id]
        )
    else:
        background_tasks.add_task(run_export, file_id, format, task_id)

    return {"task_id": task_id, "status": "processing"}


@app.get("/export/{task_id}")
async def get_export_status(task_id: str):
    task = await cache_manager.get_export_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Export task not found"
        )

    if task["status"] == "completed":
        return {"status": "ready"}
    elif task["status"] == "failed":
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Export Failed"},
        )
    else:
        return {"status": task["status"]}


@app.get("/export/{task_id}/download")
async def download_export(task_id: str):
    task = await cache_manager.get_export_task(task_id)
    if not task or task["status"] != "completed":
        raise HTTPException(status_code=404, detail="Export not ready or found")

    return FileResponse(
        path=task["file_path"],
        media_type="application/octet-stream",
        filename=os.path.basename(task["file_path"]),
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True
    )
