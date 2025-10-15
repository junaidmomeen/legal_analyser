import re
import html
import os
import logging
from typing import Any, Dict, Optional
from pydantic import BaseModel, validator

logger = logging.getLogger(__name__)


class InputSanitizer:
    """Service for sanitizing and validating user inputs"""

    @staticmethod
    def sanitize_text(text: str, max_length: int = 1000) -> str:
        """Sanitize text input to prevent XSS and injection attacks"""
        if not isinstance(text, str):
            return ""

        # Limit length
        text = text[:max_length]

        # HTML encode to prevent XSS
        text = html.escape(text)

        # Remove potentially dangerous characters
        text = re.sub(r'[<>"\']', "", text)

        # Remove control characters
        text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)

        return text.strip()

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal"""
        if not isinstance(filename, str):
            return ""

        # Remove path components
        filename = os.path.basename(filename)

        # Remove dangerous characters
        dangerous_chars = r'[<>:"/\\|?*\x00-\x1f\x7f-\x9f]'
        filename = re.sub(dangerous_chars, "", filename)

        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[: 255 - len(ext)] + ext

        return filename

    @staticmethod
    def validate_uuid(uuid_string: str) -> bool:
        """Validate UUID format"""
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
            re.IGNORECASE,
        )
        return bool(uuid_pattern.match(uuid_string))

    @staticmethod
    def sanitize_json_input(data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize JSON input data"""
        if not isinstance(data, dict):
            return {}

        sanitized = {}
        for key, value in data.items():
            # Sanitize key
            clean_key = InputSanitizer.sanitize_text(str(key), 100)
            if not clean_key:
                continue

            # Sanitize value based on type
            if isinstance(value, str):
                clean_value = InputSanitizer.sanitize_text(value)
            elif isinstance(value, (int, float, bool)):
                clean_value = value
            elif isinstance(value, dict):
                clean_value = InputSanitizer.sanitize_json_input(value)
            elif isinstance(value, list):
                clean_value = [
                    InputSanitizer.sanitize_text(str(item))
                    if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                clean_value = InputSanitizer.sanitize_text(str(value))

            sanitized[clean_key] = clean_value

        return sanitized


class SanitizedRequest(BaseModel):
    """Base model for sanitized request data"""

    @validator("*", pre=True)
    def sanitize_string_fields(cls, v):
        if isinstance(v, str):
            return InputSanitizer.sanitize_text(v)
        return v


class AnalysisRequest(SanitizedRequest):
    """Sanitized analysis request"""

    file_id: str
    format: Optional[str] = "pdf"

    @validator("file_id")
    def validate_file_id(cls, v):
        if not InputSanitizer.validate_uuid(v):
            raise ValueError("Invalid file ID format")
        return v

    @validator("format")
    def validate_format(cls, v):
        if v and v.lower() not in ["pdf", "json"]:
            raise ValueError("Format must be pdf or json")
        return v.lower() if v else "pdf"


class ExportRequest(SanitizedRequest):
    """Sanitized export request"""

    file_id: str
    format: str

    @validator("file_id")
    def validate_file_id(cls, v):
        if not InputSanitizer.validate_uuid(v):
            raise ValueError("Invalid file ID format")
        return v

    @validator("format")
    def validate_format(cls, v):
        if v.lower() not in ["pdf", "json"]:
            raise ValueError("Format must be pdf or json")
        return v.lower()


def sanitize_request_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize request data to prevent injection attacks"""
    try:
        return InputSanitizer.sanitize_json_input(data)
    except Exception as e:
        logger.warning(f"Failed to sanitize request data: {e}")
        return {}


def validate_and_sanitize_filename(filename: str) -> str:
    """Validate and sanitize filename"""
    try:
        sanitized = InputSanitizer.sanitize_filename(filename)
        if not sanitized:
            raise ValueError("Invalid filename")
        return sanitized
    except Exception as e:
        logger.warning(f"Failed to validate filename '{filename}': {e}")
        raise ValueError("Invalid filename")
