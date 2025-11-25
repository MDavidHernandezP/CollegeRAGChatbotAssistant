from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility
)
from typing import List, Dict, Any, Optional
from app.config import get_settings
import logging
import time

logger = logging.getLogger(__name__)


class VectorService:
    """
    Service for managing Milvus vector database operations.
    Handles connection, collection management, and CRUD operations.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.collection_name = self.settings.MILVUS_COLLECTION
        self.dimension = self.settings.MILVUS_DIMENSION
        self.collection: Optional[Collection] = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Milvus."""
        try:
            connections.connect(
                alias="default",
                host=self.settings.MILVUS_HOST,
                port=self.settings.MILVUS_PORT,
                timeout=30
            )
            logger.info(f"Connected to Milvus at {self.settings.MILVUS_HOST}:{self.settings.MILVUS_PORT}")
            self._init_collection()
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {str(e)}")
            raise
    
    def _init_collection(self):
        """Initialize or load collection."""
        if utility.has_collection(self.collection_name):
            logger.info(f"Collection '{self.collection_name}' exists, loading...")
            self.collection = Collection(self.collection_name)
            self.collection.load()
        else:
            logger.info(f"Creating new collection '{self.collection_name}'...")
            self._create_collection()
    
    def _create_collection(self):
        """Create a new collection with schema."""
        # Define fields
        fields = [
            FieldSchema(
                name="id",
                dtype=DataType.INT64,
                is_primary=True,
                auto_id=True,
                description="Primary ID"
            ),
            FieldSchema(
                name="document_id",
                dtype=DataType.VARCHAR,
                max_length=256,
                description="Document identifier"
            ),
            FieldSchema(
                name="filename",
                dtype=DataType.VARCHAR,
                max_length=512,
                description="Original filename"
            ),
            FieldSchema(
                name="chunk_index",
                dtype=DataType.INT64,
                description="Chunk index in document"
            ),
            FieldSchema(
                name="chunk_text",
                dtype=DataType.VARCHAR,
                max_length=65535,
                description="Text content of chunk"
            ),
            FieldSchema(
                name="embedding",
                dtype=DataType.FLOAT_VECTOR,
                dim=self.dimension,
                description="Embedding vector"
            ),
            FieldSchema(
                name="upload_timestamp",
                dtype=DataType.INT64,
                description="Upload timestamp"
            ),
            FieldSchema(
                name="page_number",
                dtype=DataType.INT64,
                description="Page number in PDF"
            )
        ]
        
        # Create schema
        schema = CollectionSchema(
            fields=fields,
            description="Document chunks with embeddings"
        )
        
        # Create collection
        self.collection = Collection(
            name=self.collection_name,
            schema=schema
        )
        
        # Create index for vector field
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        
        self.collection.create_index(
            field_name="embedding",
            index_params=index_params
        )
        
        # Load collection into memory
        self.collection.load()
        
        logger.info(f"Collection '{self.collection_name}' created and loaded successfully")
    
    def insert_documents(
        self,
        document_id: str,
        filename: str,
        chunks: List[str],
        embeddings: List[List[float]],
        page_numbers: Optional[List[int]] = None
    ) -> int:
        """
        Insert document chunks with embeddings into Milvus.
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")
        
        timestamp = int(time.time())
        
        if page_numbers is None:
            page_numbers = [0] * len(chunks)
        
        # Prepare data
        data = [
            [document_id] * len(chunks),  # document_id
            [filename] * len(chunks),      # filename
            list(range(len(chunks))),      # chunk_index
            chunks,                         # chunk_text
            embeddings,                     # embedding
            [timestamp] * len(chunks),     # upload_timestamp
            page_numbers                    # page_number
        ]
        
        try:
            result = self.collection.insert(data)
            self.collection.flush()
            logger.info(f"Inserted {len(chunks)} chunks for document {document_id}")
            return len(chunks)
        except Exception as e:
            logger.error(f"Error inserting documents: {str(e)}")
            raise
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_expr: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search.
        """
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }
        
        try:
            results = self.collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=filter_expr,
                output_fields=[
                    "document_id",
                    "filename",
                    "chunk_index",
                    "chunk_text",
                    "page_number",
                    "upload_timestamp"
                ]
            )
            
            # Format results
            formatted_results = []
            for hits in results:
                for hit in hits:
                    formatted_results.append({
                        "id": hit.id,
                        "score": float(hit.score),
                        "document_id": hit.entity.get("document_id"),
                        "filename": hit.entity.get("filename"),
                        "chunk_index": hit.entity.get("chunk_index"),
                        "text": hit.entity.get("chunk_text"),
                        "page_number": hit.entity.get("page_number"),
                        "upload_timestamp": hit.entity.get("upload_timestamp")
                    })
            
            return formatted_results
        
        except Exception as e:
            logger.error(f"Error searching vectors: {str(e)}")
            raise
    
    def delete_by_document_id(self, document_id: str) -> int:
        """
        Delete all chunks belonging to a document.
        """
        try:
            expr = f'document_id == "{document_id}"'
            
            # Query to get IDs
            results = self.collection.query(
                expr=expr,
                output_fields=["id"]
            )
            
            if not results:
                logger.warning(f"No chunks found for document_id: {document_id}")
                return 0
            
            ids_to_delete = [str(result["id"]) for result in results]
            
            # Delete by IDs
            delete_expr = f'id in [{",".join(ids_to_delete)}]'
            self.collection.delete(delete_expr)
            self.collection.flush()
            
            logger.info(f"Deleted {len(ids_to_delete)} chunks for document {document_id}")
            return len(ids_to_delete)
        
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """
        Get list of all unique documents in the collection.
        """
        try:
            # Query all unique document_ids
            results = self.collection.query(
                expr="document_id != ''",
                output_fields=["document_id", "filename", "upload_timestamp"],
                limit=10000
            )
            
            # Group by document_id
            documents_map = {}
            for result in results:
                doc_id = result["document_id"]
                if doc_id not in documents_map:
                    documents_map[doc_id] = {
                        "document_id": doc_id,
                        "filename": result["filename"],
                        "upload_timestamp": result["upload_timestamp"],
                        "chunk_count": 0
                    }
                documents_map[doc_id]["chunk_count"] += 1
            
            return list(documents_map.values())
        
        except Exception as e:
            logger.error(f"Error getting documents: {str(e)}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection."""
        try:
            stats = self.collection.num_entities
            return {
                "total_chunks": stats,
                "collection_name": self.collection_name,
                "dimension": self.dimension
            }
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            raise
    
    def health_check(self) -> bool:
        """Check if Milvus connection is healthy."""
        try:
            return utility.has_collection(self.collection_name)
        except:
            return False