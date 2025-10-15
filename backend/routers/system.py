from fastapi import APIRouter, Request, status, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
import shutil
import os

from services.document_processor import DocumentProcessor
from services.retention_jobs import get_retention_manager
from utils.circuit_breaker import circuit_manager


router = APIRouter()


@router.get("/health")
async def health_check(request: Request):
    try:
        app = request.app
        document_processor: DocumentProcessor = getattr(
            app.state, "document_processor", None
        )
        ocr_available = (
            getattr(document_processor, "tesseract_available", False)
            if document_processor
            else False
        )
        services_status = {
            "document_processor": "healthy",
            "ai_analyzer": "healthy",
            "report_generator": "healthy",
            "tesseract_ocr": "enabled" if ocr_available else "disabled",
            "image_processing": "available" if ocr_available else "unavailable",
        }
        try:
            temp_path = os.getenv("TEMP_STORAGE_PATH", "temp_uploads")
            disk_usage = shutil.disk_usage(temp_path)
            free_space_gb = disk_usage.free / (1024**3)
            services_status["disk_space_gb"] = round(free_space_gb, 2)
        except Exception:
            services_status["disk_space_gb"] = "unknown"

        app_state_cache = getattr(app.state, "analysis_cache", {})
        app_state_sem = getattr(app.state, "analysis_semaphore", None)
        max_concurrent = int(os.getenv("MAX_CONCURRENT_ANALYSES", "5"))

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": os.getenv("API_VERSION", "1.1.0"),
            "cache_size": len(app_state_cache),
            "active_analyses": (
                max_concurrent - getattr(app_state_sem, "_value", max_concurrent)
            )
            if app_state_sem
            else 0,
            "services": services_status,
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "Service Unavailable",
                "message": f"Health check failed: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "request_id": getattr(request.state, "request_id", None),
            },
        )


@router.get("/health/deep")
async def deep_health_check(request: Request):
    """Deep health check with detailed service status"""

    health_checks = {
        "timestamp": datetime.now().isoformat(),
        "version": os.getenv("API_VERSION", "1.1.0"),
        "environment": os.getenv("APP_ENV", "development"),
        "checks": {},
    }

    overall_status = "healthy"

    try:
        # Check disk space
        temp_path = os.getenv("TEMP_STORAGE_PATH", "temp_uploads")
        disk_usage = shutil.disk_usage(temp_path)
        free_space_gb = disk_usage.free / (1024**3)
        free_space_percent = (disk_usage.free / disk_usage.total) * 100

        health_checks["checks"]["disk_space"] = {
            "status": "healthy"
            if free_space_percent > 10
            else "warning"
            if free_space_percent > 5
            else "critical",
            "free_space_gb": round(free_space_gb, 2),
            "free_space_percent": round(free_space_percent, 2),
        }

        if free_space_percent <= 5:
            overall_status = "critical"
        elif free_space_percent <= 10 and overall_status == "healthy":
            overall_status = "warning"

    except Exception as e:
        health_checks["checks"]["disk_space"] = {"status": "error", "error": str(e)}
        overall_status = "critical"

    try:
        # Check memory usage (if psutil available)
        try:
            import psutil

            memory = psutil.virtual_memory()
            health_checks["checks"]["memory"] = {
                "status": "healthy"
                if memory.percent < 80
                else "warning"
                if memory.percent < 90
                else "critical",
                "usage_percent": memory.percent,
                "available_gb": round(memory.available / (1024**3), 2),
            }

            if memory.percent >= 90:
                overall_status = "critical"
            elif memory.percent >= 80 and overall_status == "healthy":
                overall_status = "warning"
        except ImportError:
            health_checks["checks"]["memory"] = {
                "status": "unknown",
                "message": "psutil not available",
            }
    except Exception as e:
        health_checks["checks"]["memory"] = {"status": "error", "error": str(e)}

    try:
        # Check analysis cache
        app = request.app
        app_state_cache = getattr(app.state, "analysis_cache", {})
        app_state_sem = getattr(app.state, "analysis_semaphore", None)
        max_concurrent = int(os.getenv("MAX_CONCURRENT_ANALYSES", "5"))

        active_analyses = (
            (max_concurrent - getattr(app_state_sem, "_value", max_concurrent))
            if app_state_sem
            else 0
        )

        health_checks["checks"]["analysis_service"] = {
            "status": "healthy",
            "cache_size": len(app_state_cache),
            "active_analyses": active_analyses,
            "max_concurrent": max_concurrent,
        }

    except Exception as e:
        health_checks["checks"]["analysis_service"] = {
            "status": "error",
            "error": str(e),
        }
        overall_status = "critical"

    try:
        # Check OCR availability
        app = request.app
        document_processor = getattr(app.state, "document_processor", None)
        ocr_available = (
            getattr(document_processor, "tesseract_available", False)
            if document_processor
            else False
        )

        health_checks["checks"]["ocr_service"] = {
            "status": "healthy" if ocr_available else "warning",
            "tesseract_available": ocr_available,
            "image_processing": "enabled" if ocr_available else "disabled",
            "message": "OCR fully operational"
            if ocr_available
            else "OCR unavailable - images cannot be processed",
        }

        if not ocr_available and overall_status == "healthy":
            overall_status = "warning"

    except Exception as e:
        health_checks["checks"]["ocr_service"] = {"status": "error", "error": str(e)}

    try:
        # Check AI service availability
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        circuit_breakers = circuit_manager.get_all_states()

        health_checks["checks"]["ai_service"] = {
            "status": "healthy" if openrouter_key else "warning",
            "api_key_configured": bool(openrouter_key),
            "circuit_breakers": circuit_breakers,
        }

        # Check if any circuit breakers are open
        open_circuits = [
            name for name, state in circuit_breakers.items() if state["state"] == "open"
        ]
        if open_circuits:
            health_checks["checks"]["ai_service"]["status"] = "critical"
            overall_status = "critical"
        elif not openrouter_key:
            overall_status = (
                "warning" if overall_status == "healthy" else overall_status
            )

    except Exception as e:
        health_checks["checks"]["ai_service"] = {"status": "error", "error": str(e)}
        overall_status = "critical"

    # Set overall status
    health_checks["status"] = overall_status

    # Return appropriate status code
    status_code = 200 if overall_status == "healthy" else 503

    return JSONResponse(status_code=status_code, content=health_checks)


@router.get("/")
async def root(request: Request):
    return {
        "name": "Legal Document Analyzer API",
        "version": os.getenv("API_VERSION", "1.1.0"),
        "description": "AI-powered legal document analysis with comprehensive reporting",
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "analyze": "/analyze",
            "export": "/export/{file_id}/{format}",
            "supported_formats": "/supported-formats",
            "docs": "/docs",
        },
    }


@router.get("/supported-formats")
async def get_supported_formats():
    return {"formats": ["PDF", "PNG", "JPG", "JPEG", "GIF", "BMP", "TIFF", "WEBP"]}


@router.get("/retention/status")
async def get_retention_status():
    """Get current retention jobs status"""
    try:
        retention_manager = get_retention_manager()
        return retention_manager.get_status()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get retention status: {str(e)}",
        )


@router.post("/retention/cleanup")
async def force_cleanup(
    cleanup_type: str = "all",
):
    """Force immediate cleanup of specified type"""
    retention_manager = get_retention_manager()

    valid_types = ["all", "analysis", "temp", "export", "log"]
    if cleanup_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid cleanup type. Must be one of: {', '.join(valid_types)}",
        )

    try:
        await retention_manager.force_cleanup(cleanup_type)

        return {
            "message": f"Cleanup completed for type: {cleanup_type}",
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleanup failed: {str(e)}",
        )
