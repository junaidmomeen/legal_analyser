import os

try:
    import magic  # type: ignore

    _MAGIC_AVAILABLE = True
except Exception:
    magic = None  # type: ignore
    _MAGIC_AVAILABLE = False
from fastapi import UploadFile
from typing import Set
import logging

from models.analysis_models import FileValidationResult
from config import settings

logger = logging.getLogger(__name__)


class FileValidator:
    """Service for validating uploaded files"""

    def __init__(self):
        self.max_file_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        # Additional early limits
        self.max_pdf_pages = (
            int(os.getenv("MAX_PDF_PAGES", "100")) if hasattr(os, "getenv") else 100
        )
        self.max_image_dimension = (
            int(os.getenv("MAX_IMAGE_DIMENSION", "5000"))
            if hasattr(os, "getenv")
            else 5000
        )
        self.allowed_extensions: Set[str] = set(settings.ALLOWED_EXTENSIONS)
        self.allowed_mime_types: Set[str] = {
            "application/pdf",
            "image/png",
            "image/jpeg",
            "image/tiff",
            "image/bmp",
            "application/octet-stream",
            "text/plain",
        }

    async def validate_file(self, file: UploadFile) -> FileValidationResult:
        """
        Validate an uploaded file with enhanced security checks

        Args:
            file: The uploaded file to validate

        Returns:
            FileValidationResult: Validation result with details
        """
        try:
            # Check filename exists and is safe
            if not file.filename:
                return FileValidationResult(
                    is_valid=False,
                    file_type="unknown",
                    file_extension="",
                    file_size=0,
                    error_message="No filename provided",
                )

            # Sanitize filename to prevent path traversal
            filename = self._sanitize_filename(file.filename)
            if not filename:
                return FileValidationResult(
                    is_valid=False,
                    file_type="unknown",
                    file_extension="",
                    file_size=0,
                    error_message="Invalid filename",
                )

            file_extension = os.path.splitext(filename)[1].lower()

            if not file_extension:
                return FileValidationResult(
                    is_valid=False,
                    file_type="unknown",
                    file_extension="",
                    file_size=0,
                    error_message=f"File has no extension. Supported extensions are: {', '.join(self.allowed_extensions)}",
                )

            if file_extension not in self.allowed_extensions:
                return FileValidationResult(
                    is_valid=False,
                    file_type="unknown",
                    file_extension=file_extension,
                    file_size=0,
                    error_message=f"File extension '{file_extension}' not allowed. Supported: {', '.join(self.allowed_extensions)}",
                )

            content = await file.read()
            file_size = len(content)

            await file.seek(0)

            if file_size > self.max_file_size:
                return FileValidationResult(
                    is_valid=False,
                    file_type="unknown",
                    file_extension=file_extension,
                    file_size=file_size,
                    error_message=f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds maximum allowed size ({self.max_file_size / 1024 / 1024}MB)",
                )

            if file_size == 0:
                return FileValidationResult(
                    is_valid=False,
                    file_type="unknown",
                    file_extension=file_extension,
                    file_size=file_size,
                    error_message="File is empty",
                )

            if _MAGIC_AVAILABLE:
                mime_type = magic.from_buffer(content, mime=True)
            else:
                mime_type = self._detect_mime_without_libmagic(content, file_extension)
            if mime_type not in self.allowed_mime_types:
                return FileValidationResult(
                    is_valid=False,
                    file_type="unknown",
                    file_extension=file_extension,
                    file_size=file_size,
                    error_message=f"Invalid file type: {mime_type}. Supported types are: {', '.join(self.allowed_mime_types)}",
                )

            # Check if the extension matches the MIME type
            if file_extension == ".pdf" and mime_type not in [
                "application/pdf",
                "application/octet-stream",
                "text/plain",
            ]:
                return FileValidationResult(
                    is_valid=False,
                    file_type="unknown",
                    file_extension=file_extension,
                    file_size=file_size,
                    error_message=f"File extension '{file_extension}' does not match MIME type '{mime_type}'",
                )

            if file_extension in {".jpg", ".jpeg"} and mime_type not in [
                "image/jpeg",
                "application/octet-stream",
            ]:
                return FileValidationResult(
                    is_valid=False,
                    file_type="unknown",
                    file_extension=file_extension,
                    file_size=file_size,
                    error_message=f"File extension '{file_extension}' does not match MIME type '{mime_type}'",
                )

            if file_extension == ".png" and mime_type not in [
                "image/png",
                "application/octet-stream",
            ]:
                return FileValidationResult(
                    is_valid=False,
                    file_type="unknown",
                    file_extension=file_extension,
                    file_size=file_size,
                    error_message=f"File extension '{file_extension}' does not match MIME type '{mime_type}'",
                )

            file_type = "pdf" if "pdf" in file_extension else "image"

            # Validate file content matches expected type
            if not self._validate_file_content(content, file_type):
                return FileValidationResult(
                    is_valid=False,
                    file_type=file_type,
                    file_extension=file_extension,
                    file_size=file_size,
                    error_message=f"File content does not match expected {file_type} format",
                )

            # Early structural checks (best-effort without expensive parsing)
            if file_type == "pdf":
                # Quick page count heuristic: count 'Page' markers or XRef sections is unreliable; rely on downstream
                # Here we only block zero-length or absurdly large declared size already handled above
                pass
            else:
                # For images, attempt a cheap dimension check using PIL if available
                try:
                    from PIL import Image
                    import io as _io

                    with Image.open(_io.BytesIO(content)) as img:
                        w, h = img.size
                        if w > self.max_image_dimension or h > self.max_image_dimension:
                            return FileValidationResult(
                                is_valid=False,
                                file_type=file_type,
                                file_extension=file_extension,
                                file_size=file_size,
                                error_message=f"Image dimensions too large: {w}x{h}px. Max is {self.max_image_dimension}px",
                            )
                except Exception:
                    # If PIL fails, let downstream processing handle
                    pass

            return FileValidationResult(
                is_valid=True,
                file_type=file_type,
                file_extension=file_extension.lstrip("."),
                file_size=file_size,
            )

        except Exception as e:
            logger.error(f"Error validating file: {str(e)}")
            return FileValidationResult(
                is_valid=False,
                file_type="unknown",
                file_extension="",
                file_size=0,
                error_message=f"Validation error: {str(e)}",
            )

    def get_max_file_size_mb(self) -> float:
        return self.max_file_size / 1024 / 1024

    def get_allowed_extensions(self) -> Set[str]:
        return self.allowed_extensions.copy()

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal attacks"""
        import re

        # Remove any path components
        filename = os.path.basename(filename)

        # Remove null bytes and control characters
        filename = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", filename)

        # Remove dangerous characters
        dangerous_chars = r'[<>:"/\\|?*\x00-\x1f\x7f-\x9f]'
        filename = re.sub(dangerous_chars, "", filename)

        # Limit filename length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[: 255 - len(ext)] + ext

        # Ensure filename is not empty or just dots
        if not filename or filename in [".", ".."]:
            return ""

        return filename

    def _validate_file_content(self, content: bytes, expected_type: str) -> bool:
        """Validate file content matches expected type"""
        if expected_type == "pdf":
            # Check PDF magic bytes
            return content.startswith(b"%PDF-")
        elif expected_type == "image":
            # Check image magic bytes
            image_signatures = [
                b"\x89PNG\r\n\x1a\n",  # PNG
                b"\xff\xd8\xff",  # JPEG
                b"GIF87a",  # GIF87a
                b"GIF89a",  # GIF89a
                b"BM",  # BMP
                b"II*\x00",  # TIFF little endian
                b"MM\x00*",  # TIFF big endian
                b"RIFF",  # WebP
            ]
            # Special case for JPEG files which might have different signatures
            if content.startswith(b"\xff\xd8"):
                return True
            return any(content.startswith(sig) for sig in image_signatures)

        return False

    def _detect_mime_without_libmagic(self, content: bytes, file_extension: str) -> str:
        """Best-effort MIME detection using signatures and extension when libmagic is unavailable.
        This is intended for Windows/local dev environments lacking libmagic.
        """
        # Signature-based detection first
        if content.startswith(b"%PDF-"):
            return "application/pdf"
        signatures = {
            b"\x89PNG\r\n\x1a\n": "image/png",
            b"\xff\xd8\xff": "image/jpeg",
            b"GIF87a": "image/gif",
            b"GIF89a": "image/gif",
            b"BM": "image/bmp",
            b"II*\x00": "image/tiff",
            b"MM\x00*": "image/tiff",
        }
        for sig, mime in signatures.items():
            if content.startswith(sig):
                return mime
        # Fallback by extension (lower confidence)
        ext_map = {
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".bmp": "image/bmp",
            ".tif": "image/tiff",
            ".tiff": "image/tiff",
        }
        # Return the mapped MIME type or default to a safe value based on extension
        mime_type = ext_map.get(file_extension.lower(), "application/octet-stream")
        # For JPG/JPEG files, ensure we always return the correct MIME type
        if file_extension.lower() in [".jpg", ".jpeg"]:
            return "image/jpeg"
        return mime_type

    def get_supported_formats(self) -> dict:
        supported_formats_dict = {
            "pdf": {
                "extensions": [],
                "mime_types": [],
                "max_size_mb": self.get_max_file_size_mb(),
            },
            "images": {
                "extensions": [],
                "mime_types": [],
                "max_size_mb": self.get_max_file_size_mb(),
            },
        }

        for ext in self.allowed_extensions:
            if ext == ".pdf":
                supported_formats_dict["pdf"]["extensions"].append(ext)
            else:
                supported_formats_dict["images"]["extensions"].append(ext)

        for mime in self.allowed_mime_types:
            if "pdf" in mime:
                supported_formats_dict["pdf"]["mime_types"].append(mime)
            elif "image" in mime:
                supported_formats_dict["images"]["mime_types"].append(mime)

        return supported_formats_dict
