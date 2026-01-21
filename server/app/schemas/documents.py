from datetime import datetime
from typing import Optional

from pydantic import BaseModel, model_validator


class DocumentUploadResponse(BaseModel):
    """Response returned when a single document is uploaded (no indexing yet)."""

    message: str
    filename: Optional[str]
    chunks_count: Optional[int] = None
    file_path: Optional[str]


class DocumentIndexRequest(BaseModel):
    """Request body for indexing an already uploaded document.
    
    Must provide either file_path OR filename, but not both.
    """

    file_path: Optional[str] = None
    filename: Optional[str] = None

    @model_validator(mode='after')
    def validate_one_provided(self):
        if self.file_path and self.filename:
            raise ValueError("Cannot provide both file_path and filename. Provide only one.")
        if not self.file_path and not self.filename:
            raise ValueError("Must provide either file_path or filename.")
        return self


class DocumentIndexResponse(BaseModel):
    """Response returned when an existing document has been indexed."""

    message: str
    filename: Optional[str]
    chunks_count: int
    file_path: str


class DocumentInfo(BaseModel):
    """Information about a stored document in local storage."""

    key: str
    size: Optional[int]
    last_modified: Optional[datetime]
    original_filename: Optional[str] = None
    signed_url: Optional[str] = None


class IndexedDocumentInfo(BaseModel):
    """Aggregated information about an indexed document in the vector store."""

    source: str
    chunks_count: int
    last_indexed_at: Optional[datetime] = None


class IndexedDocumentDeleteResponse(BaseModel):
    """Response returned when indexed chunks for a document are removed."""

    source: str
    deleted_chunks: int

