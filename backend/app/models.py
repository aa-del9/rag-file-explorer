"""
Pydantic models for request/response validation.
Defines data structures used across the API.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class UploadResponse(BaseModel):
    """Response model for PDF upload endpoint."""
    success: bool
    message: str
    file_id: str
    filename: str
    chunks_created: int
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatRequest(BaseModel):
    """Request model for chat/query endpoint."""
    question: str = Field(..., min_length=1, max_length=1000, description="User's question")
    top_k: Optional[int] = Field(default=5, ge=1, le=20, description="Number of relevant chunks to retrieve")
    
    @validator('question')
    def question_not_empty(cls, v):
        """Ensure question is not just whitespace."""
        if not v.strip():
            raise ValueError('Question cannot be empty or just whitespace')
        return v.strip()


class RetrievedChunk(BaseModel):
    """Model for a retrieved chunk from vector store."""
    chunk_id: str
    document_id: str
    text: str
    similarity_score: float
    metadata: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Response model for chat/query endpoint."""
    success: bool
    question: str
    answer: str
    retrieved_chunks: List[RetrievedChunk]
    model_used: str
    timestamp: datetime = Field(default_factory=datetime.now)
    processing_time: Optional[float] = None  # in seconds


class ErrorResponse(BaseModel):
    """Standard error response model."""
    success: bool = False
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    app_name: str
    version: str
    ollama_connected: bool
    embedding_model_loaded: bool
    vector_store_ready: bool
