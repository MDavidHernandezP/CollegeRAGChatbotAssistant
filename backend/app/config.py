from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # API Settings
    API_TITLE: str = "RAG Q&A System API"
    API_VERSION: str = "1.0.0"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Milvus Settings
    MILVUS_HOST: str = "milvus-standalone"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "documents"
    MILVUS_DIMENSION: int = 384  # all-MiniLM-L6-v2 dimension
    
    # Embedding Settings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "cpu"
    
    # LLM Settings
    LLM_PROVIDER: str = "openai"  # "openai" or "local"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_MAX_TOKENS: int = 1000
    OPENAI_TEMPERATURE: float = 0.7
    
    # Chunking Settings
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    
    # RAG Settings
    TOP_K_RESULTS: int = 5
    SIMILARITY_THRESHOLD: float = 0.5
    
    # File Upload Settings
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: list = [".pdf"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()