"""
Configuration module for the IntelliFile backend.
Manages environment variables and application settings.
"""

from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Uses Pydantic for validation and type safety.
    """
    
    # Application Settings
    APP_NAME: str = "IntelliFile"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    DOCUMENTS_DIR: Path = DATA_DIR / "documents"  # Changed from PDF_DIR to support all formats
    CHROMA_DIR: Path = DATA_DIR / "chroma_db"
    
    # LLM Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:latest"
    OLLAMA_TIMEOUT: int = 120  # seconds
    
    # Embedding Settings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "cpu"  # Use "cuda" if GPU is available
    
    # Vector Store Settings
    CHROMA_COLLECTION_NAME: str = "pdf_rag"
    
    # RAG Settings
    CHUNK_SIZE: int = 400  # tokens/characters
    CHUNK_OVERLAP: int = 50  # overlap between chunks
    TOP_K_RESULTS: int = 5  # number of relevant chunks to retrieve
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50 MB
    ALLOWED_EXTENSIONS: set = {".pdf", ".doc", ".docx"}
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create necessary directories on initialization
        self.DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
        self.CHROMA_DIR.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
