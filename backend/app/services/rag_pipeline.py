from typing import List, Dict, Any
from app.services.pdf_service import PDFService
from app.services.vector_service import VectorService
from app.utils.chunker import TextChunker
from app.utils.embeddings import EmbeddingGenerator
from app.utils.llm_client import LLMClient
from app.config import get_settings
import logging
import time

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Complete RAG pipeline implementation.
    Handles document processing, embedding generation, and query execution.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.pdf_service = PDFService(upload_dir=self.settings.UPLOAD_DIR)
        self.vector_service = VectorService()
        self.chunker = TextChunker(
            chunk_size=self.settings.CHUNK_SIZE,
            chunk_overlap=self.settings.CHUNK_OVERLAP
        )
        self.embedding_generator = EmbeddingGenerator()
        self.llm_client = LLMClient()
        logger.info("RAG Pipeline initialized successfully")
    
    def ingest_document(
        self,
        document_id: str,
        filename: str
    ) -> Dict[str, Any]:
        """
        Complete document ingestion pipeline.
        
        Steps:
        1. Get file path
        2. Extract text from PDF
        3. Chunk text
        4. Generate embeddings
        5. Store in vector database
        """
        start_time = time.time()
        
        try:
            # Step 1: Get file path
            file_path = self.pdf_service.get_file_path(document_id)
            if not file_path:
                raise ValueError(f"File not found for document_id: {document_id}")
            
            logger.info(f"Starting ingestion for document: {document_id}")
            
            # Step 2: Extract text from PDF
            pages_data = self.pdf_service.extract_text(file_path)
            
            if not pages_data:
                raise ValueError("No text extracted from PDF")
            
            logger.info(f"Extracted {len(pages_data)} pages")
            
            # Step 3: Chunk text
            all_chunks = []
            all_page_numbers = []
            
            for page_data in pages_data:
                page_text = page_data["text"]
                page_number = page_data["page_number"]
                
                # Chunk the page text
                chunks_with_indices = self.chunker.chunk_text(page_text)
                
                for chunk_text, chunk_idx in chunks_with_indices:
                    all_chunks.append(chunk_text)
                    all_page_numbers.append(page_number)
            
            if not all_chunks:
                raise ValueError("No chunks created from document")
            
            logger.info(f"Created {len(all_chunks)} chunks")
            
            # Step 4: Generate embeddings
            logger.info("Generating embeddings...")
            embeddings = self.embedding_generator.generate_embeddings_batch(
                all_chunks,
                batch_size=32,
                show_progress=True
            )
            
            logger.info(f"Generated {len(embeddings)} embeddings")
            
            # Step 5: Store in vector database
            chunks_inserted = self.vector_service.insert_documents(
                document_id=document_id,
                filename=filename,
                chunks=all_chunks,
                embeddings=embeddings,
                page_numbers=all_page_numbers
            )
            
            processing_time = time.time() - start_time
            
            result = {
                "success": True,
                "document_id": document_id,
                "filename": filename,
                "pages_processed": len(pages_data),
                "chunks_created": len(all_chunks),
                "embeddings_generated": len(embeddings),
                "chunks_inserted": chunks_inserted,
                "processing_time": processing_time
            }
            
            logger.info(f"Document ingestion completed in {processing_time:.2f}s")
            return result
        
        except Exception as e:
            logger.error(f"Error in document ingestion: {str(e)}")
            raise
    
    def query(
        self,
        question: str,
        top_k: int = None
    ) -> Dict[str, Any]:
        """
        Execute RAG query pipeline.
        
        Steps:
        1. Generate query embedding
        2. Search vector database
        3. Retrieve top-K chunks
        4. Build context
        5. Generate answer with LLM
        """
        start_time = time.time()
        
        if top_k is None:
            top_k = self.settings.TOP_K_RESULTS
        
        try:
            logger.info(f"Processing query: {question}")
            
            # Step 1: Generate query embedding
            query_embedding = self.embedding_generator.generate_embedding(question)
            
            # Step 2: Search vector database
            search_results = self.vector_service.search(
                query_embedding=query_embedding,
                top_k=top_k
            )
            
            if not search_results:
                return {
                    "success": True,
                    "question": question,
                    "answer": "No se encontraron documentos relevantes para responder tu pregunta.",
                    "retrieved_chunks": [],
                    "processing_time": time.time() - start_time
                }
            
            logger.info(f"Retrieved {len(search_results)} chunks")
            
            # Step 3: Filter by similarity threshold
            filtered_results = [
                result for result in search_results
                if result["score"] >= self.settings.SIMILARITY_THRESHOLD
            ]
            
            if not filtered_results:
                return {
                    "success": True,
                    "question": question,
                    "answer": "Los documentos encontrados no son suficientemente relevantes para responder tu pregunta.",
                    "retrieved_chunks": [],
                    "processing_time": time.time() - start_time
                }
            
            # Step 4: Prepare context for LLM
            context_chunks = [
                {
                    "text": result["text"],
                    "score": result["score"],
                    "metadata": {
                        "filename": result["filename"],
                        "page_number": result["page_number"],
                        "chunk_index": result["chunk_index"]
                    }
                }
                for result in filtered_results
            ]
            
            # Step 5: Generate answer
            logger.info("Generating answer with LLM...")
            answer = self.llm_client.generate_answer(
                question=question,
                context_chunks=context_chunks
            )
            
            processing_time = time.time() - start_time
            
            result = {
                "success": True,
                "question": question,
                "answer": answer,
                "retrieved_chunks": context_chunks,
                "processing_time": processing_time
            }
            
            logger.info(f"Query completed in {processing_time:.2f}s")
            return result
        
        except Exception as e:
            logger.error(f"Error in query pipeline: {str(e)}")
            raise
    
    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """
        Delete document from both filesystem and vector database.
        """
        try:
            # Delete from vector database
            deleted_chunks = self.vector_service.delete_by_document_id(document_id)
            
            # Delete file
            file_deleted = self.pdf_service.delete_file(document_id)
            
            return {
                "success": True,
                "document_id": document_id,
                "deleted_chunks": deleted_chunks,
                "file_deleted": file_deleted
            }
        
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """
        Get list of all documents in the system.
        """
        return self.vector_service.get_all_documents()
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check health of all components.
        """
        milvus_healthy = self.vector_service.health_check()
        stats = self.vector_service.get_collection_stats()
        
        return {
            "status": "healthy" if milvus_healthy else "unhealthy",
            "milvus_connected": milvus_healthy,
            "total_chunks": stats.get("total_chunks", 0),
            "collection_name": stats.get("collection_name", ""),
            "embedding_dimension": self.embedding_generator.get_dimension()
        }