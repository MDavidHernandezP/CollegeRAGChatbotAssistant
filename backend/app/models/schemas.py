from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class DocumentMetadata(BaseModel):
    document_id: str
    filename: str
    upload_date: datetime
    page_number: Optional[int] = None
    chunk_index: int
    total_chunks: int


class DocumentUploadResponse(BaseModel):
    success: bool
    message: str
    document_id: str
    filename: str


class IngestRequest(BaseModel):
    document_id: str
    filename: str


class IngestResponse(BaseModel):
    success: bool
    message: str
    document_id: str
    chunks_processed: int
    embeddings_created: int


class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = Field(default=5, ge=1, le=20)


class RetrievedChunk(BaseModel):
    text: str
    score: float
    metadata: Dict[str, Any]


class QueryResponse(BaseModel):
    success: bool
    question: str
    answer: str
    retrieved_chunks: List[RetrievedChunk]
    processing_time: float


class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    upload_date: datetime
    chunk_count: int


class DocumentListResponse(BaseModel):
    success: bool
    documents: List[DocumentInfo]
    total_count: int


class DeleteDocumentResponse(BaseModel):
    success: bool
    message: str
    document_id: str
    deleted_chunks: int


class HealthResponse(BaseModel):
    status: str
    milvus_connected: bool
    collection_exists: bool
    total_documents: int