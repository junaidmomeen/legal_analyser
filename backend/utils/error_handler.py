import logging
import traceback
from typing import Any, Dict, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import os

logger = logging.getLogger(__name__)


class SecureErrorHandler:
    """Secure error handling to prevent information leakage"""

    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode or os.getenv("APP_ENV") == "development"

    def handle_validation_error(
        self, request: Request, exc: ValidationError
    ) -> JSONResponse:
        """Handle validation errors securely"""
        request_id = getattr(request.state, "request_id", None)

        logger.warning(
            f"Validation error for {request.url}: {len(exc.errors())} errors",
            extra={"request_id": request_id, "error_type": "validation_error"},
        )

        # Don't expose detailed validation errors in production
        if self.debug_mode:
            error_details = [
                {
                    "field": error.get("loc", ["unknown"])[-1],
                    "message": error.get("msg", "Invalid value"),
                    "type": error.get("type", "validation_error"),
                }
                for error in exc.errors()
            ]
        else:
            error_details = [{"message": "Invalid request data"}]

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation Error",
                "message": "Invalid request data provided",
                "details": error_details,
                "request_id": request_id,
            },
        )

    def handle_http_exception(
        self, request: Request, exc: HTTPException
    ) -> JSONResponse:
        """Handle HTTP exceptions securely"""
        request_id = getattr(request.state, "request_id", None)

        # Log the actual error details
        logger.error(
            f"HTTP exception for {request.url}: {exc.detail}",
            extra={
                "error_type": "http_exception",
                "status_code": exc.status_code,
                "request_id": request_id,
            },
        )

        # Don't expose internal error details
        if exc.status_code >= 500:
            message = "Internal server error occurred"
            details = {
                "message": "An unexpected error occurred. Please try again later."
            }
        else:
            message = exc.detail
            details = {"message": message}

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "Request Failed",
                "message": message,
                "details": details,
                "request_id": request_id,
            },
        )

    def handle_general_exception(
        self, request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle general exceptions securely"""
        request_id = getattr(request.state, "request_id", None)

        # Log the full exception with traceback
        logger.error(
            f"Unhandled exception for {request.url}",
            exc_info=True,
            extra={
                "error_type": "unhandled_exception",
                "request_id": request_id,
                "exception_type": type(exc).__name__,
            },
        )

        # Never expose internal error details to clients
        if self.debug_mode:
            # In development, provide more details
            error_details = {
                "exception_type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(),
            }
        else:
            # In production, generic error message
            error_details = {
                "message": "An unexpected error occurred. Please try again later."
            }

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred. Please try again later.",
                "details": error_details,
                "request_id": request_id,
            },
        )

    def handle_rate_limit_exceeded(
        self, request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle rate limit exceeded errors"""
        request_id = getattr(request.state, "request_id", None)

        logger.warning(
            f"Rate limit exceeded for {request.client.host}",
            extra={
                "error_type": "rate_limit_exceeded",
                "client_ip": request.client.host,
                "request_id": request_id,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate Limit Exceeded",
                "message": "Too many requests. Please try again later.",
                "details": {
                    "retry_after": 60,  # seconds
                    "message": "Rate limit exceeded. Please wait before making another request.",
                },
                "request_id": request_id,
            },
            headers={"Retry-After": "60"},
        )

    def handle_file_upload_error(
        self, request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle file upload specific errors"""
        request_id = getattr(request.state, "request_id", None)

        logger.warning(
            f"File upload error for {request.url}",
            extra={
                "error_type": "file_upload_error",
                "request_id": request_id,
                "exception_type": type(exc).__name__,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "File Upload Error",
                "message": "Failed to process uploaded file. Please check file format and size.",
                "details": {
                    "message": "Invalid file provided. Please ensure file is in supported format and within size limits."
                },
                "request_id": request_id,
            },
        )

    def handle_ai_service_error(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle AI service specific errors"""
        request_id = getattr(request.state, "request_id", None)

        logger.error(
            f"AI service error for {request.url}",
            extra={
                "error_type": "ai_service_error",
                "request_id": request_id,
                "exception_type": type(exc).__name__,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "Analysis Service Unavailable",
                "message": "Document analysis service is temporarily unavailable.",
                "details": {
                    "message": "Please try again later. If the problem persists, contact support."
                },
                "request_id": request_id,
            },
        )


# Global error handler instance
error_handler = SecureErrorHandler()


def create_error_response(
    request: Request,
    error_type: str,
    message: str,
    status_code: int = 500,
    details: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """Create a standardized error response"""
    request_id = getattr(request.state, "request_id", None)

    logger.warning(
        f"Custom error response: {message}",
        extra={
            "error_type": error_type,
            "request_id": request_id,
            "status_code": status_code,
        },
    )

    return JSONResponse(
        status_code=status_code,
        content={
            "error": error_type.replace("_", " ").title(),
            "message": message,
            "details": details or {"message": message},
            "request_id": request_id,
        },
    )
