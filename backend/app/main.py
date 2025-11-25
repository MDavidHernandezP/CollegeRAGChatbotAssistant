from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routers import documents, ingest, query
from app.config import get_settings
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="RAG-based Q&A system with PDF document processing and Milvus vector database"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router)
app.include_router(ingest.router)
app.include_router(query.router)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting RAG Q&A System API...")
    logger.info(f"Milvus host: {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
    logger.info(f"Embedding model: {settings.EMBEDDING_MODEL}")
    logger.info(f"LLM provider: {settings.LLM_PROVIDER}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down RAG Q&A System API...")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "RAG Q&A System API",
        "version": settings.API_VERSION,
        "endpoints": {
            "docs": "/docs",
            "upload": "/documents/upload",
            "ingest": "/ingest/process",
            "query": "/query/ask",
            "list": "/documents/list",
            "health": "/query/health"
        }
    }


@app.get("/health")
async def health():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "service": "RAG Q&A System"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )