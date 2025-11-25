from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Generate embeddings using sentence-transformers.
    Supports multiple models and batch processing.
    """
    
    def __init__(self):
        settings = get_settings()
        self.model_name = settings.EMBEDDING_MODEL
        self.device = settings.EMBEDDING_DEVICE
        self.dimension = settings.MILVUS_DIMENSION
        
        logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name, device=self.device)
        logger.info(f"Model loaded successfully on {self.device}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def generate_embeddings_batch(
        self, 
        texts: List[str], 
        batch_size: int = 32,
        show_progress: bool = False
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.
        More efficient for large document processing.
        """
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )
        return embeddings.tolist()
    
    def get_dimension(self) -> int:
        """Return the dimension of embeddings."""
        return self.dimension
    
    def compute_similarity(
        self, 
        embedding1: Union[List[float], np.ndarray], 
        embedding2: Union[List[float], np.ndarray]
    ) -> float:
        """Compute cosine similarity between two embeddings."""
        if isinstance(embedding1, list):
            embedding1 = np.array(embedding1)
        if isinstance(embedding2, list):
            embedding2 = np.array(embedding2)
        
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        similarity = dot_product / (norm1 * norm2)
        return float(similarity)