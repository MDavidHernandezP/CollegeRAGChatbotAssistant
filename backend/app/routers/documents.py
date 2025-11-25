from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from app.models.schemas import (
    DocumentUploadResponse,
    DocumentListResponse,
    DeleteDocumentResponse,
    DocumentInfo
)
from app.services.pdf_service import PDFService
from app.services.rag_pipeline import RAGPipeline
from app.config import get_settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["Documents"])

# Initialize services
settings = get_settings()
pdf_service = PDFService(upload_dir=settings.UPLOAD_DIR)
rag_pipeline = RAGPipeline()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a PDF document.
    
    This endpoint only uploads and stores the file.
    Use /ingest endpoint to process and index the document.
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are allowed"
            )
        
        # Check file size
        content = await file.read()
        if len(content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes"
            )
        
        # Validate PDF
        if not content.startswith(b'%PDF-'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PDF file"
            )
        
        # Save file
        doc_info = pdf_service.save_uploaded_file(content, file.filename)
        
        logger.info(f"Document uploaded: {doc_info['document_id']}")
        
        return DocumentUploadResponse(
            success=True,
            message="Document uploaded successfully. Use /ingest endpoint to process it.",
            document_id=doc_info["document_id"],
            filename=doc_info["filename"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading document: {str(e)}"
        )


@router.get("/list", response_model=DocumentListResponse)
async def list_documents():
    """
    List all documents in the system with their metadata.
    """
    try:
        documents = rag_pipeline.get_all_documents()
        
        # Convert to DocumentInfo models
        document_infos = [
            DocumentInfo(
                document_id=doc["document_id"],
                filename=doc["filename"],
                upload_date=datetime.fromtimestamp(doc["upload_timestamp"]),
                chunk_count=doc["chunk_count"]
            )
            for doc in documents
        ]
        
        # Sort by upload date (newest first)
        document_infos.sort(key=lambda x: x.upload_date, reverse=True)
        
        return DocumentListResponse(
            success=True,
            documents=document_infos,
            total_count=len(document_infos)
        )
    
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing documents: {str(e)}"
        )


@router.delete("/{document_id}", response_model=DeleteDocumentResponse)
async def delete_document(document_id: str):
    """
    Delete a document and all its associated chunks from the system.
    """
    try:
        result = rag_pipeline.delete_document(document_id)
        
        if result["deleted_chunks"] == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}"
            )
        
        return DeleteDocumentResponse(
            success=True,
            message=f"Document deleted successfully. Removed {result['deleted_chunks']} chunks.",
            document_id=document_id,
            deleted_chunks=result["deleted_chunks"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting document: {str(e)}"
        )


@router.get("/{document_id}/info")
async def get_document_info(document_id: str):
    """
    Get detailed information about a specific document.
    """
    try:
        documents = rag_pipeline.get_all_documents()
        
        doc = next((d for d in documents if d["document_id"] == document_id), None)
        
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}"
            )
        
        return {
            "success": True,
            "document": {
                "document_id": doc["document_id"],
                "filename": doc["filename"],
                "upload_date": datetime.fromtimestamp(doc["upload_timestamp"]).isoformat(),
                "chunk_count": doc["chunk_count"]
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting document info: {str(e)}"
        )