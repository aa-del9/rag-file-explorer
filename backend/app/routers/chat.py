"""
Chat router for RAG query handling.
Handles user questions and generates context-aware answers.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from app.models import ChatRequest, ChatResponse, ErrorResponse
from app.config import settings
from app.embeddings import get_embedding_model
from app.vector_store import VectorStore
from app.llm_client import LLMClient
from app.rag_pipeline import RAGPipeline
from app.metadata_store import MetadataStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Lazy-loaded components (initialized on first use)
_embedding_model = None
_vector_store = None
_llm_client = None
_metadata_store = None
_rag_pipeline = None


def get_components():
    """Lazy initialization of heavy components."""
    global _embedding_model, _vector_store, _llm_client, _metadata_store, _rag_pipeline
    
    if _embedding_model is None:
        _embedding_model = get_embedding_model(
            model_name=settings.EMBEDDING_MODEL,
            device=settings.EMBEDDING_DEVICE
        )
    
    if _vector_store is None:
        _vector_store = VectorStore(
            persist_directory=settings.CHROMA_DIR,
            collection_name=settings.CHROMA_COLLECTION_NAME
        )
    
    if _llm_client is None:
        _llm_client = LLMClient(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            timeout=settings.OLLAMA_TIMEOUT
        )
    
    if _metadata_store is None:
        _metadata_store = MetadataStore(
            persist_directory=settings.CHROMA_DIR
        )
    
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline(
            embedding_model=_embedding_model,
            vector_store=_vector_store,
            llm_client=_llm_client,
            metadata_store=_metadata_store,
            top_k=settings.TOP_K_RESULTS
        )
    
    return _vector_store, _rag_pipeline


@router.post("/query", response_model=ChatResponse, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def query(request: ChatRequest):
    """
    Process a user query using the RAG pipeline.
    
    Process:
    1. Validate question
    2. Retrieve relevant chunks from vector store
    3. Build context-aware prompt
    4. Generate answer using LLM
    5. Return answer with source chunks
    
    Args:
        request: ChatRequest with question and optional parameters
        
    Returns:
        ChatResponse with answer and retrieved context
    """
    # Get components (lazy initialization)
    vector_store, rag_pipeline = get_components()
    
    try:
        logger.info(f"Processing query: '{request.question[:50]}...'")
        
        # Check if vector store has any documents
        collection_stats = vector_store.get_collection_stats()
        if collection_stats.get("total_chunks", 0) == 0:
            logger.warning("No documents in vector store")
            return ChatResponse(
                success=True,
                question=request.question,
                answer="No documents have been uploaded yet. Please upload PDF documents first before asking questions.",
                retrieved_chunks=[],
                model_used=settings.OLLAMA_MODEL,
                processing_time=0.0
            )
        
        # Execute RAG pipeline
        try:
            answer, chunks, processing_time = rag_pipeline.query(
                question=request.question,
                top_k=request.top_k or settings.TOP_K_RESULTS,
                temperature=0.7
            )
        
        except Exception as e:
            logger.error(f"RAG pipeline failed: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process query: {str(e)}"
            )
        
        logger.info(
            f"Query completed in {processing_time:.2f}s, "
            f"retrieved {len(chunks)} chunks"
        )
        
        return ChatResponse(
            success=True,
            question=request.question,
            answer=answer,
            retrieved_chunks=chunks,
            model_used=settings.OLLAMA_MODEL,
            processing_time=round(processing_time, 2)
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error during query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/stats")
async def get_stats():
    """
    Get statistics about the RAG system.
    
    Returns:
        Dictionary with system statistics
    """
    # Get components (lazy initialization)
    vector_store, _ = get_components()
    embedding_model = _embedding_model  # Already initialized
    
    try:
        collection_stats = vector_store.get_collection_stats()
        
        return {
            "success": True,
            "vector_store": collection_stats,
            "embedding_model": {
                "name": settings.EMBEDDING_MODEL,
                "dimension": embedding_model.get_embedding_dimension(),
                "device": settings.EMBEDDING_DEVICE
            },
            "llm": {
                "model": settings.OLLAMA_MODEL,
                "base_url": settings.OLLAMA_BASE_URL
            },
            "config": {
                "chunk_size": settings.CHUNK_SIZE,
                "chunk_overlap": settings.CHUNK_OVERLAP,
                "top_k_results": settings.TOP_K_RESULTS
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to get stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve stats: {str(e)}"
        )
