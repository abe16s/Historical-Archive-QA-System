from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Request
from fastapi.responses import Response
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
        decoded_source = unquote(source)
        return service.remove_indexed_document(decoded_source)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete indexed document: {str(exc)}",
        )


@router.get("/view/{source:path}")
async def view_document(
    source: str,
    request: Request,
    service: DocumentService = Depends(get_document_service),
):
    """
    Serve a document file for viewing/downloading.
    The source parameter should be the filename (e.g., "document.pdf").
    Supports page navigation via URL fragment (e.g., #page=5).
    """
    try:
        decoded_source = unquote(source)
        
        files = service.list_files()
        matching_file = None
        
        for file_info in files:
            if file_info.original_filename == decoded_source:
                matching_file = file_info
                break
        
        if not matching_file:
            raise HTTPException(status_code=404, detail=f"Document not found: {decoded_source}")
        
        file_bytes, content_type, metadata = service.get_file_bytes(matching_file.key)
        
        headers = {
            "Content-Disposition": f'inline; filename="{decoded_source}"',
        }
        
        media_type = content_type or "application/pdf"
        
        return Response(
            content=file_bytes,
            media_type=media_type,
            headers=headers
        )
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve document: {str(exc)}")

