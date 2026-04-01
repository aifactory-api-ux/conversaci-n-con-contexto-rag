from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from shared.database import get_db
from shared.exceptions import (
    NotFoundException,
    ValidationException,
    DocumentProcessingException
)
from shared.constants import (
    DocumentStatus,
    SUPPORTED_CONTENT_TYPES,
    MAX_FILE_SIZE_BYTES,
    ERROR_INVALID_FILE_TYPE,
    ERROR_FILE_TOO_LARGE
)

from .service import DocumentService
from .models import DocumentUploadResponse, DocumentStatusResponse

router = APIRouter(prefix="/api/documents", tags=["documents"])


def get_document_service(db: AsyncSession = Depends(get_db)) -> DocumentService:
    """Dependency injection for DocumentService."""
    return DocumentService(db)


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_202_ACCEPTED
)
async def upload_document(
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(get_document_service)
) -> DocumentUploadResponse:
    """
    Upload a document for processing.
    
    Supported file types: PDF, DOCX, TXT
    Max file size: 50MB
    """
    # Validate file type
    if file.content_type not in SUPPORTED_CONTENT_TYPES:
        raise ValidationException(
            message=ERROR_INVALID_FILE_TYPE,
            details={
                "supported_types": SUPPORTED_CONTENT_TYPES,
                "received_type": file.content_type
            }
        )
    
    # Validate file size
    try:
        # Read file content to check size
        content = await file.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise ValidationException(
                message=ERROR_FILE_TOO_LARGE,
                details={
                    "max_size_mb": MAX_FILE_SIZE_BYTES // (1024 * 1024),
                    "actual_size_bytes": len(content)
                }
            )
        
        # Reset file pointer
        await file.seek(0)
        
        # Process upload
        document = await document_service.upload_document(
            filename=file.filename,
            content_type=file.content_type,
            file_content=content,
            user_id="current_user_id"  # TODO: Get from auth token
        )
        
        return DocumentUploadResponse(
            id=str(document.id),
            status=document.status,
            message="Document uploaded successfully"
        )
        
    except Exception as e:
        if isinstance(e, ValidationException):
            raise
        raise DocumentProcessingException(
            message=f"Failed to upload document: {str(e)}",
            details={"filename": file.filename}
        )


@router.get("/", response_model=List[DocumentUploadResponse])
async def list_documents(
    document_service: DocumentService = Depends(get_document_service)
) -> List[DocumentUploadResponse]:
    """
    List all documents for the current user.
    """
    try:
        user_id = "current_user_id"  # TODO: Get from auth token
        documents = await document_service.list_documents(user_id)
        
        return [
            DocumentUploadResponse(
                id=str(doc.id),
                status=doc.status,
                message=f"Document {doc.filename}",
                chunks_count=doc.chunks_count
            )
            for doc in documents
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service)
) -> DocumentStatusResponse:
    """
    Get the processing status of a specific document.
    """
    try:
        document = await document_service.get_document(document_id)
        
        # Verify ownership (TODO: Implement proper auth)
        if document.user_id != "current_user_id":
            raise NotFoundException("document", document_id)
        
        return DocumentStatusResponse(
            id=str(document.id),
            status=document.status,
            chunks_count=document.chunks_count,
            error_message=document.error_message
        )
    except NotFoundException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document status: {str(e)}"
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service)
) -> JSONResponse:
    """
    Delete a document and all its chunks.
    """
    try:
        # First get document to verify ownership
        document = await document_service.get_document(document_id)
        
        # Verify ownership (TODO: Implement proper auth)
        if document.user_id != "current_user_id":
            raise NotFoundException("document", document_id)
        
        await document_service.delete_document(document_id)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Document deleted successfully"}
        )
    except NotFoundException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/health")
async def health_check() -> dict:
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "service": "document-service",
        "version": "1.0.0"
    }