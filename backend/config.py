import os
from typing import Optional, List


def get_env_list(key: str, default: str) -> List[str]:
    """Get a list of strings from a comma-separated environment variable."""
    return [item.strip() for item in os.getenv(key, default).split(",") if item.strip()]


class Settings:
    """Application settings and configuration"""

    # API Settings
    API_TITLE: str = os.getenv("API_TITLE", "Legal Document Analyzer API")
    API_VERSION: str = os.getenv("API_VERSION", "1.0.0")
    API_DESCRIPTION: str = os.getenv(
        "API_DESCRIPTION", "AI-powered legal document analysis and clause extraction"
    )

    # CORS Settings
    ALLOWED_ORIGINS: List[str] = get_env_list(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173",
    )

    # File Processing Settings
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    ALLOWED_EXTENSIONS: List[str] = get_env_list(
        "ALLOWED_EXTENSIONS", ".pdf,.png,.jpg,.jpeg,.tiff,.bmp"
    )
    TEMP_DIR: str = os.getenv("TEMP_DIR", "/tmp")

    # OCR Settings
    TESSERACT_CMD: Optional[str] = os.getenv("TESSERACT_CMD")
    OCR_LANGUAGE: str = os.getenv("OCR_LANGUAGE", "eng")

    # AI Analysis Settings
    MAX_CLAUSES_PER_DOCUMENT: int = int(os.getenv("MAX_CLAUSES_PER_DOCUMENT", "10"))
    MIN_CLAUSE_LENGTH: int = int(os.getenv("MIN_CLAUSE_LENGTH", "50"))
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))

    # Logging Settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # OpenAI Settings (for future AI integration)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    # Database Settings (for future use)
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")

    @classmethod
    def get_tesseract_cmd(cls) -> Optional[str]:
        """Get Tesseract command path"""
        if cls.TESSERACT_CMD:
            return cls.TESSERACT_CMD

        # Try common installation paths
        common_paths = [
            "/usr/bin/tesseract",
            "/usr/local/bin/tesseract",
            "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
            "C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe",
        ]

        for path in common_paths:
            if os.path.exists(path):
                return path

        return None


settings = Settings()
