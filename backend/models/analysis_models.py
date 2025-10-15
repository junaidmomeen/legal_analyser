from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class KeyClause(BaseModel):
    """Model for a key clause extracted from the document"""

    type: str = Field(
        ..., description="Type of clause (e.g., 'Payment Terms', 'Termination')"
    )
    content: str = Field(..., description="Full text content of the clause")
    importance: Literal["high", "medium", "low"] = Field(
        ..., description="Importance level of the clause"
    )
    classification: Literal[
        "Contractual",
        "Compliance",
        "Financial",
        "Termination",
        "Confidentiality",
        "Miscellaneous",
    ] = Field(..., description="Classification of the clause")
    risk_score: float = Field(
        default=0.0, ge=0.0, le=10.0, description="Risk score for the clause (1-10)"
    )
    page: Optional[int] = Field(None, description="Page number where clause was found")
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for clause extraction",
    )


class AnalysisResult(BaseModel):
    """Model for the complete document analysis result"""

    summary: str = Field(..., description="AI-generated summary of the document")
    key_clauses: List[KeyClause] = Field(
        default_factory=list, description="List of extracted key clauses"
    )
    document_type: str = Field(..., description="Detected type of legal document")
    total_pages: int = Field(
        default=1, ge=1, description="Total number of pages in the document"
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Overall confidence score"
    )
    processing_time: float = Field(
        default=0.0, description="Time taken to process the document in seconds"
    )
    word_count: int = Field(
        default=0, ge=0, description="Total word count in the document"
    )
    analyzed_at: datetime = Field(
        default_factory=datetime.now, description="Timestamp of analysis"
    )
    file_id: Optional[str] = Field(None, description="Unique ID for the uploaded file")


class DocumentProcessingResult(BaseModel):
    """Model for document processing result"""

    success: bool = Field(..., description="Whether processing was successful")
    extracted_text: str = Field(
        default="", description="Extracted text from the document"
    )
    total_pages: int = Field(default=1, description="Total number of pages processed")
    word_count: int = Field(default=0, description="Number of words extracted")
    processing_time: float = Field(default=0.0, description="Time taken for processing")
    error_message: Optional[str] = Field(
        None, description="Error message if validation failed"
    )


class FileValidationResult(BaseModel):
    """Model for file validation result"""

    is_valid: bool = Field(..., description="Whether the file is valid")
    file_type: str = Field(..., description="Detected file type")
    file_extension: str = Field(..., description="File extension")
    file_size: int = Field(..., description="File size in bytes")
    error_message: Optional[str] = Field(
        None, description="Error message if validation failed"
    )
