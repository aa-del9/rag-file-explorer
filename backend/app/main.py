"""
Main FastAPI application entry point.
Initializes the IntelliFile backend server.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys

from app.config import settings
from app.models import HealthResponse
from app.routers import upload, chat, metadata
from app.routers import documents
from app.embeddings import get_embedding_model
from app.vector_store import VectorStore
from app.llm_client import LLMClient

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('rag_backend.log')
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("=" * 60)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("=" * 60)
    
    try:
        # Initialize embedding model
        logger.info("Initializing embedding model...")
        embedding_model = get_embedding_model(
            model_name=settings.EMBEDDING_MODEL,
            device=settings.EMBEDDING_DEVICE
        )
        logger.info(f"[OK] Embedding model loaded: {settings.EMBEDDING_MODEL}")
        
        # Initialize vector store
        logger.info("Initializing vector store...")
        vector_store = VectorStore(
            persist_directory=settings.CHROMA_DIR,
            collection_name=settings.CHROMA_COLLECTION_NAME
        )
        logger.info(f"[OK] Vector store ready: {vector_store.get_collection_stats()['total_chunks']} chunks")
        
        # Initialize LLM client
        logger.info("Connecting to Ollama...")
        llm_client = LLMClient(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            timeout=settings.OLLAMA_TIMEOUT
        )
        logger.info(f"[OK] Ollama connected: {settings.OLLAMA_MODEL}")
        
        logger.info("=" * 60)
        logger.info("All systems ready!")
        logger.info(f"Server starting on {settings.HOST}:{settings.PORT}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        logger.error("Please check your configuration and dependencies")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    logger.info("Goodbye!")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Local LLM RAG system for PDF document querying",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


# Include routers
app.include_router(upload.router)
app.include_router(chat.router)
app.include_router(metadata.router)
app.include_router(documents.router)


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "supported_formats": list(settings.ALLOWED_EXTENSIONS),
        "endpoints": {
            "health": "/health",
            "upload_document": "/upload/document",
            "upload_pdf": "/upload/pdf (legacy)",
            "delete_document": "/upload/document/{id}",
            "query": "/chat/query",
            "stats": "/chat/stats",
            "metadata_search": "/metadata/search",
            "metadata_semantic_search": "/metadata/semantic-search",
            "metadata_list": "/metadata/list",
            "metadata_stats": "/metadata/stats",
            "metadata_document": "/metadata/document/{id}",
            "documents_list": "/documents",
            "documents_search": "/documents/search",
            "documents_recommend": "/documents/recommend",
            "documents_similar": "/documents/{id}/similar",
            "documents_summary": "/documents/{id}/summary",
            "documents_overview": "/documents/stats/overview",
            "docs": "/docs"
        }
    }


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify all components are operational.
    """
    try:
        # Check embedding model
        embedding_model = get_embedding_model(
            model_name=settings.EMBEDDING_MODEL,
            device=settings.EMBEDDING_DEVICE
        )
        embedding_loaded = embedding_model.is_loaded()
        
        # Check vector store
        vector_store = VectorStore(
            persist_directory=settings.CHROMA_DIR,
            collection_name=settings.CHROMA_COLLECTION_NAME
        )
        vector_store_ready = vector_store.is_ready()
        
        # Check Ollama
        llm_client = LLMClient(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            timeout=settings.OLLAMA_TIMEOUT
        )
        ollama_connected = llm_client.is_available()
        
        # Determine overall status
        all_healthy = embedding_loaded and vector_store_ready and ollama_connected
        status = "healthy" if all_healthy else "degraded"
        
        return HealthResponse(
            status=status,
            app_name=settings.APP_NAME,
            version=settings.APP_VERSION,
            ollama_connected=ollama_connected,
            embedding_model_loaded=embedding_loaded,
            vector_store_ready=vector_store_ready
        )
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            app_name=settings.APP_NAME,
            version=settings.APP_VERSION,
            ollama_connected=False,
            embedding_model_loaded=False,
            vector_store_ready=False
        )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )
