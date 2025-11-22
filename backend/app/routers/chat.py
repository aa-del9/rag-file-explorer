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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize components
embedding_model = get_embedding_model(
    model_name=settings.EMBEDDING_MODEL,
    device=settings.EMBEDDING_DEVICE
)
vector_store = VectorStore(
    persist_directory=settings.CHROMA_DIR,
    collection_name=settings.CHROMA_COLLECTION_NAME
)
llm_client = LLMClient(
    base_url=settings.OLLAMA_BASE_URL,
    model=settings.OLLAMA_MODEL,
    timeout=settings.OLLAMA_TIMEOUT
)
rag_pipeline = RAGPipeline(
    embedding_model=embedding_model,
    vector_store=vector_store,
    llm_client=llm_client,
    top_k=settings.TOP_K_RESULTS
)


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
