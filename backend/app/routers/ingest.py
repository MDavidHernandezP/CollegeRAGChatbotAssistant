from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from app.models.schemas import IngestRequest, IngestResponse
from app.services.rag_pipeline import RAGPipeline
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingest", tags=["Ingest"])

# Initialize RAG pipeline
rag_pipeline = RAGPipeline()

# Store ingestion status
ingestion_status = {}


def process_ingestion(document_id: str, filename: str):
    """
    Background task for document ingestion.
    """
    try:
        ingestion_status[document_id] = {"status": "processing", "progress": 0}
        
        result = rag_pipeline.ingest_document(document_id, filename)
        
        ingestion_status[document_id] = {
            "status": "completed",
            "progress": 100,
            "result": result
        }
    
    except Exception as e:
        logger.error(f"Background ingestion failed: {str(e)}")
        ingestion_status[document_id] = {
            "status": "failed",
            "progress": 0,
            "error": str(e)
        }


@router.post("/process", response_model=IngestResponse)
async def ingest_document(request: IngestRequest, background_tasks: BackgroundTasks):
    """
    Process and ingest a previously uploaded document.
    
    This endpoint:
    1. Extracts text from the PDF
    2. Chunks the text
    3. Generates embeddings
    4. Stores vectors in Milvus
    
    Can be run as background task for large documents.
    """
    try:
        logger.info(f"Starting ingestion for document: {request.document_id}")
        
        # For synchronous processing (recommended for moderate-sized documents)
        result = rag_pipeline.ingest_document(
            document_id=request.document_id,
            filename=request.filename
        )
        
        return IngestResponse(
            success=True,
            message="Document processed and indexed successfully",
            document_id=request.document_id,
            chunks_processed=result["chunks_created"],
            embeddings_created=result["embeddings_generated"]
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error ingesting document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error ingesting document: {str(e)}"
        )


@router.post("/process-async", response_model=dict)
async def ingest_document_async(request: IngestRequest, background_tasks: BackgroundTasks):
    """
    Process and ingest a document in the background.
    Use this for very large documents.
    """
    try:
        # Start background task
        background_tasks.add_task(
            process_ingestion,
            request.document_id,
            request.filename
        )
        
        ingestion_status[request.document_id] = {
            "status": "queued",
            "progress": 0
        }
        
        return {
            "success": True,
            "message": "Document queued for processing",
            "document_id": request.document_id,
            "status_endpoint": f"/ingest/status/{request.document_id}"
        }
    
    except Exception as e:
        logger.error(f"Error queueing document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error queueing document: {str(e)}"
        )


@router.get("/status/{document_id}")
async def get_ingestion_status(document_id: str):
    """
    Get the status of a background ingestion task.
    """
    if document_id not in ingestion_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No ingestion status found for document: {document_id}"
        )
    
    return {
        "success": True,
        "document_id": document_id,
        **ingestion_status[document_id]
    }


@router.post("/reindex/{document_id}")
async def reindex_document(document_id: str):
    """
    Reindex an existing document (useful if chunking strategy changes).
    """
    try:
        # First delete existing chunks
        delete_result = rag_pipeline.delete_document(document_id)
        
        if delete_result["deleted_chunks"] == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {document_id}"
            )
        
        # Get filename from file system
        file_path = rag_pipeline.pdf_service.get_file_path(document_id)
        if not file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document file not found: {document_id}"
            )
        
        filename = file_path.split('_', 1)[1]
        
        # Re-ingest
        result = rag_pipeline.ingest_document(document_id, filename)
        
        return {
            "success": True,
            "message": "Document reindexed successfully",
            "document_id": document_id,
            "old_chunks_deleted": delete_result["deleted_chunks"],
            "new_chunks_created": result["chunks_created"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reindexing document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reindexing document: {str(e)}"
        )