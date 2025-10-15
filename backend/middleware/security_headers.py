from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import os


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        security_headers = {
            # Prevent clickjacking
            "X-Frame-Options": "DENY",
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            # XSS protection
            "X-XSS-Protection": "1; mode=block",
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            # Content Security Policy
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            ),
            # Permissions Policy (formerly Feature Policy)
            "Permissions-Policy": (
                "camera=(), "
                "microphone=(), "
                "geolocation=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "accelerometer=()"
            ),
            # Strict Transport Security (only in production with HTTPS)
            **self._get_hsts_header(),
            # Remove server information
            "Server": "Legal-Analyzer",
        }

        # Add headers to response
        for header, value in security_headers.items():
            if value:  # Only add non-empty values
                response.headers[header] = value

        return response

    def _get_hsts_header(self) -> dict:
        """Get HSTS header only in production with HTTPS"""
        if (
            os.getenv("APP_ENV") == "production"
            and os.getenv("FORCE_HTTPS", "false").lower() == "true"
        ):
            max_age = int(os.getenv("HSTS_MAX_AGE", "31536000"))  # 1 year default
            include_subdomains = (
                os.getenv("HSTS_INCLUDE_SUBDOMAINS", "true").lower() == "true"
            )

            hsts_value = f"max-age={max_age}"
            if include_subdomains:
                hsts_value += "; includeSubDomains"

            return {"Strict-Transport-Security": hsts_value}

        return {}
