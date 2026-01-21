from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from urllib.parse import unquote

from app.schemas.documents import (
    DocumentUploadResponse,
    DocumentIndexResponse,
    DocumentInfo,
    IndexedDocumentInfo,
    IndexedDocumentDeleteResponse,
)
from pydantic import BaseModel
from app.core.deps import get_document_service
from app.services.document_service import DocumentService

router = APIRouter()


@router.get("/list", response_model=List[DocumentInfo])
async def list_documents(
    service: DocumentService = Depends(get_document_service),
) -> List[DocumentInfo]:
    """List uploaded documents stored in local storage."""
    try:
        return service.list_files()
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service),
) -> DocumentUploadResponse:
    """
    Upload a single document to local storage without indexing.
    """
    try:
        return await service.upload(file)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(exc)}",
        )


class IndexRequest(BaseModel):
    filename: str


@router.post("/index", response_model=DocumentIndexResponse)
async def index_document(
    payload: IndexRequest,
    service: DocumentService = Depends(get_document_service),
) -> DocumentIndexResponse:
    """Index an already-uploaded document by its filename."""
    try:
        return await service.index_by_filename(payload.filename)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=500,
            detail=f"Failed to index document: {str(exc)}",
        )


@router.get("/indexed", response_model=List[IndexedDocumentInfo])
async def list_indexed_documents(
    service: DocumentService = Depends(get_document_service),
) -> List[IndexedDocumentInfo]:
    """
    List documents that have been indexed into the vector store.
    """
    try:
        return service.list_indexed_documents()
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list indexed documents: {str(exc)}",
        )


@router.delete(
    "/indexed/{source}",
    response_model=IndexedDocumentDeleteResponse,
)
async def delete_indexed_document(
    source: str,
    service: DocumentService = Depends(get_document_service),
) -> IndexedDocumentDeleteResponse:
    """
    Delete all indexed chunks for a given document source from the vector store.
    """
    try:
        # URL decode the source parameter in case it's encoded
        decoded_source = unquote(source)
        return service.remove_indexed_document(decoded_source)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete indexed document: {str(exc)}",
        )


