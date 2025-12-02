"""
Pydantic models for metadata search and explorer endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class SortOrder(str, Enum):
    """Sort order enumeration."""
    asc = "asc"
    desc = "desc"


class SortField(str, Enum):
    """Sortable fields enumeration."""
    filename = "filename"
    created_at = "created_at"
    modified_at = "modified_at"
    file_size_mb = "file_size_mb"
    page_count = "page_count"
    relevance = "relevance"


class ChunkRelevance(BaseModel):
    """Model for chunk-level relevance scoring."""
    chunk_id: str
    text: str
    similarity_score: float
    chunk_index: Optional[int] = None


class DocumentMetadataResponse(BaseModel):
    """Response model for document metadata."""
    document_id: str
    filename: str
    display_name: str  # Filename without UUID prefix
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
    preview_snippet: Optional[str] = None
    tags: Optional[List[str]] = None


class DocumentSearchResult(BaseModel):
    """Enhanced search result with both document and chunk scores."""
    document_id: str
    filename: str
    display_name: str  # Filename without UUID prefix
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
    tags: Optional[List[str]] = None
    preview_snippet: Optional[str] = None
    # Relevance scores
    document_score: Optional[float] = None  # Document-level similarity
    chunk_score: Optional[float] = None  # Best chunk similarity
    aggregated_score: Optional[float] = None  # Combined score
    relevant_chunks: Optional[List[ChunkRelevance]] = None  # Top relevant chunks


class AdvancedSearchRequest(BaseModel):
    """Request model for advanced combined search."""
    query: Optional[str] = Field(None, description="Semantic search query")
    filename_contains: Optional[str] = Field(None, description="Filter by filename pattern")
    file_types: Optional[List[str]] = Field(None, description="Filter by file extensions (.pdf, .docx)")
    document_types: Optional[List[str]] = Field(None, description="Filter by AI-classified document types")
    authors: Optional[List[str]] = Field(None, description="Filter by authors")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    keywords: Optional[List[str]] = Field(None, description="Filter by AI keywords")
    min_pages: Optional[int] = Field(None, ge=1, description="Minimum page count")
    max_pages: Optional[int] = Field(None, description="Maximum page count")
    min_size_mb: Optional[float] = Field(None, ge=0, description="Minimum file size in MB")
    max_size_mb: Optional[float] = Field(None, description="Maximum file size in MB")
    created_after: Optional[str] = Field(None, description="Created after date (ISO format)")
    created_before: Optional[str] = Field(None, description="Created before date (ISO format)")
    modified_after: Optional[str] = Field(None, description="Modified after date (ISO format)")
    modified_before: Optional[str] = Field(None, description="Modified before date (ISO format)")
    include_chunk_scores: bool = Field(default=False, description="Include chunk-level relevance")
    use_doc_level_ranking: bool = Field(default=True, description="Use document-level ranking first")
    top_k: int = Field(default=20, ge=1, le=100, description="Number of results")
    sort_by: Optional[SortField] = Field(default=None, description="Sort field")
    sort_order: SortOrder = Field(default=SortOrder.desc, description="Sort order")


class AdvancedSearchResponse(BaseModel):
    """Response model for advanced search."""
    success: bool
    total_results: int
    documents: List[DocumentSearchResult]
    query_params: Dict[str, Any]
    search_type: str  # "semantic", "metadata", "hybrid"
    processing_time_ms: Optional[float] = None


class RecommendationRequest(BaseModel):
    """Request model for semantic recommendations."""
    query: str = Field(..., min_length=1, description="Query for recommendations")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of recommendations")
    file_types: Optional[List[str]] = Field(None, description="Filter by file types")
    exclude_document_ids: Optional[List[str]] = Field(None, description="Document IDs to exclude")


class RecommendationResponse(BaseModel):
    """Response model for recommendations."""
    success: bool
    query: str
    total_results: int
    recommendations: List[DocumentSearchResult]


class SimilarDocumentsResponse(BaseModel):
    """Response model for similar documents."""
    success: bool
    source_document_id: str
    source_document_filename: str
    total_results: int
    similar_documents: List[DocumentSearchResult]


class DocumentSummaryResponse(BaseModel):
    """Response model for smart document summary."""
    success: bool
    document_id: str
    filename: str
    summary: str
    key_topics: Optional[List[str]] = None
    metadata_summary: Dict[str, Any]
    cached: bool = False
    generated_at: str


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
