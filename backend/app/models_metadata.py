"""
Pydantic models for metadata search and explorer endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class DocumentMetadataResponse(BaseModel):
    """Response model for document metadata."""
    document_id: str
    filename: str
    file_path: str
    file_size_mb: float
    file_type: str
    page_count: Optional[int] = None
    created_at: str
    modified_at: str
    title: Optional[str] = None
    author: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_keywords: Optional[List[str]] = None
    ai_document_type: Optional[str] = None
    similarity_score: Optional[float] = None


class MetadataSearchRequest(BaseModel):
    """Request model for metadata filtering."""
    filename_contains: Optional[str] = Field(None, description="Filter by filename pattern")
    file_type: Optional[str] = Field(None, description="Filter by file extension (.pdf, .docx)")
    document_type: Optional[str] = Field(None, description="Filter by AI-classified document type")
    author: Optional[str] = Field(None, description="Filter by author")
    keywords: Optional[List[str]] = Field(None, description="Filter by keywords")
    min_pages: Optional[int] = Field(None, description="Minimum page count")
    max_pages: Optional[int] = Field(None, description="Maximum page count")
    created_after: Optional[str] = Field(None, description="Created after date (ISO format)")
    created_before: Optional[str] = Field(None, description="Created before date (ISO format)")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results")


class SemanticSearchRequest(BaseModel):
    """Request model for semantic document search."""
    query: str = Field(..., min_length=1, description="Search query")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of results")
    file_type: Optional[str] = Field(None, description="Filter by file type")
    document_type: Optional[str] = Field(None, description="Filter by document type")


class MetadataSearchResponse(BaseModel):
    """Response model for metadata search."""
    success: bool
    total_results: int
    documents: List[DocumentMetadataResponse]
    query_params: Dict[str, Any]


class ExplorerListResponse(BaseModel):
    """Response model for document explorer list."""
    success: bool
    total_documents: int
    documents: List[DocumentMetadataResponse]
    page: int
    page_size: int


class MetadataStatsResponse(BaseModel):
    """Response model for metadata statistics."""
    success: bool
    total_documents: int
    file_type_distribution: Dict[str, int]
    document_type_distribution: Dict[str, int]
    total_size_mb: float
    collection_name: str
