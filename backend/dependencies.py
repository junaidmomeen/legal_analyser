from functools import lru_cache
import logging

from services.document_processor import DocumentProcessor
from services.ai_analyzer import AIAnalyzer
from services.report_generator import ReportGenerator
from utils.file_validator import FileValidator

logger = logging.getLogger(__name__)


@lru_cache(maxsize=None)
def get_document_processor() -> DocumentProcessor:
    logger.info("Initializing DocumentProcessor")
    return DocumentProcessor()


@lru_cache(maxsize=None)
def get_ai_analyzer() -> AIAnalyzer:
    logger.info("Initializing AIAnalyzer")
    return AIAnalyzer()


@lru_cache(maxsize=None)
def get_report_generator() -> ReportGenerator:
    logger.info("Initializing ReportGenerator")
    return ReportGenerator()


@lru_cache(maxsize=None)
def get_file_validator() -> FileValidator:
    logger.info("Initializing FileValidator")
    return FileValidator()
