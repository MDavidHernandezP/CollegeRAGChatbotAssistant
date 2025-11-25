from fastapi import APIRouter, HTTPException, status
from app.models.schemas import QueryRequest, QueryResponse, RetrievedChunk
from app.services.rag_pipeline import RAGPipeline
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/query", tags=["Query"])

# Initialize services
settings = get_settings()
rag_pipeline = RAGPipeline()


@router.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    """
    Ask a question and get an answer based on indexed documents.
    
    This is the main RAG endpoint that:
    1. Generates query embedding
    2. Searches for relevant chunks in Milvus
    3. Retrieves top-K most similar chunks
    4. Builds context from retrieved chunks
    5. Sends context + question to LLM
    6. Returns generated answer with sources
    """
    try:
        if not request.question.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question cannot be empty"
            )
        
        logger.info(f"Processing question: {request.question[:100]}...")
        
        # Execute RAG pipeline
        result = rag_pipeline.query(
            question=request.question,
            top_k=request.top_k
        )
        
        # Format retrieved chunks
        retrieved_chunks = [
            RetrievedChunk(
                text=chunk["text"],
                score=chunk["score"],
                metadata=chunk["metadata"]
            )
            for chunk in result["retrieved_chunks"]
        ]
        
        return QueryResponse(
            success=True,
            question=request.question,
            answer=result["answer"],
            retrieved_chunks=retrieved_chunks,
            processing_time=result["processing_time"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )


@router.post("/search")
async def semantic_search(request: QueryRequest):
    """
    Perform semantic search without LLM generation.
    Returns only the most relevant chunks.
    """
    try:
        if not request.question.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query cannot be empty"
            )
        
        # Generate query embedding
        query_embedding = rag_pipeline.embedding_generator.generate_embedding(
            request.question
        )
        
        # Search vector database
        search_results = rag_pipeline.vector_service.search(
            query_embedding=query_embedding,
            top_k=request.top_k
        )
        
        # Filter by threshold
        filtered_results = [
            result for result in search_results
            if result["score"] >= settings.SIMILARITY_THRESHOLD
        ]
        
        return {
            "success": True,
            "query": request.question,
            "results": filtered_results,
            "total_results": len(filtered_results)
        }
    
    except Exception as e:
        logger.error(f"Error in semantic search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in semantic search: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Check health status of the RAG system.
    """
    try:
        health_info = rag_pipeline.health_check()
        
        return {
            "success": True,
            **health_info
        }
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )