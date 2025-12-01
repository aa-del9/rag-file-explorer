"""
Documents router for file explorer and intelligent search endpoints.
Provides advanced search, recommendations, similar documents, and summaries.
"""

import logging
from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional, List
from datetime import datetime

from app.models_metadata import (
    AdvancedSearchRequest,
    AdvancedSearchResponse,
    RecommendationRequest,
    RecommendationResponse,
    SimilarDocumentsResponse,
    DocumentSummaryResponse,
    DocumentSearchResult,
    DocumentMetadataResponse,
    SortField,
    SortOrder
)
from app.config import settings
from app.metadata_store import MetadataStore
from app.vector_store import VectorStore
from app.embeddings import get_embedding_model
from app.llm_client import LLMClient
from app.search_service import SearchService
from app.summary_cache import SummaryCache, SmartSummaryGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents", "explorer", "search"])

# Lazy-loaded components
_metadata_store = None
_vector_store = None
_embedding_model = None
_llm_client = None
_search_service = None
_summary_cache = None
_summary_generator = None


def get_components():
    """Lazy initialization of heavy components."""
    global _metadata_store, _vector_store, _embedding_model, _llm_client
    global _search_service, _summary_cache, _summary_generator
    
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
    
    if _metadata_store is None:
        _metadata_store = MetadataStore(
            persist_directory=settings.CHROMA_DIR
        )
    
    if _llm_client is None:
        _llm_client = LLMClient(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            timeout=settings.OLLAMA_TIMEOUT
        )
    
    if _search_service is None:
        _search_service = SearchService(
            embedding_model=_embedding_model,
            vector_store=_vector_store,
            metadata_store=_metadata_store
        )
    
    if _summary_cache is None:
        _summary_cache = SummaryCache(cache_dir=settings.DATA_DIR)
    
    if _summary_generator is None:
        _summary_generator = SmartSummaryGenerator(
            llm_client=_llm_client,
            cache=_summary_cache
        )
    
    return {
        'metadata_store': _metadata_store,
        'vector_store': _vector_store,
        'embedding_model': _embedding_model,
        'llm_client': _llm_client,
        'search_service': _search_service,
        'summary_cache': _summary_cache,
        'summary_generator': _summary_generator
    }


def _convert_to_metadata_response(doc: dict) -> DocumentMetadataResponse:
    """Convert internal document dict to metadata response."""
    metadata = doc.get('metadata', {})
    
    # Parse keywords
    keywords = metadata.get('ai_keywords', '')
    if isinstance(keywords, str):
        keywords = [k.strip() for k in keywords.split(',') if k.strip()]
    
    # Parse tags
    tags = metadata.get('tags', '')
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(',') if t.strip()]
    
    # Get preview
    preview = doc.get('summary', '')
    if len(preview) > 200:
        preview = preview[:200] + "..."
    
    return DocumentMetadataResponse(
        document_id=doc.get('document_id', ''),
        filename=metadata.get('filename', 'unknown'),
        file_path=metadata.get('file_path', ''),
        file_size_mb=float(metadata.get('file_size_mb', 0)),
        file_type=metadata.get('file_type', 'unknown'),
        page_count=metadata.get('page_count'),
        created_at=metadata.get('created_at', ''),
        modified_at=metadata.get('modified_at', ''),
        title=metadata.get('title'),
        author=metadata.get('author'),
        ai_summary=metadata.get('ai_summary'),
        ai_keywords=keywords if isinstance(keywords, list) else None,
        ai_document_type=metadata.get('ai_document_type'),
        similarity_score=doc.get('similarity_score'),
        preview_snippet=preview if preview else None,
        tags=tags if isinstance(tags, list) else None
    )


# ============================================================
# DOCUMENT EXPLORER ENDPOINTS
# ============================================================

@router.get("", response_model=dict)
async def list_documents(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    sort_by: Optional[str] = Query(default=None, description="Sort field: filename, created_at, modified_at, file_size_mb, page_count"),
    sort_order: str = Query(default="desc", description="Sort order: asc or desc"),
    file_type: Optional[str] = Query(default=None, description="Filter by file type"),
    filename_contains: Optional[str] = Query(default=None, description="Filter by filename pattern")
):
    """
    List all documents with metadata for explorer view.
    
    Supports pagination, sorting, and basic filtering.
    Returns full list of files with metadata and preview snippets.
    
    **Example Response:**
    ```json
    {
        "success": true,
        "total_documents": 42,
        "page": 1,
        "page_size": 20,
        "total_pages": 3,
        "documents": [
            {
                "document_id": "abc-123",
                "filename": "report.pdf",
                "file_size_mb": 2.5,
                "file_type": ".pdf",
                "page_count": 15,
                "preview_snippet": "This document covers...",
                ...
            }
        ]
    }
    ```
    """
    components = get_components()
    metadata_store = components['metadata_store']
    
    try:
        offset = (page - 1) * page_size
        
        logger.info(f"Listing documents: page={page}, size={page_size}, sort={sort_by}")
        
        # Get all documents (we'll filter and sort in memory for flexibility)
        all_docs = metadata_store.list_all_documents(limit=10000)
        
        # Apply filters
        filtered_docs = all_docs
        
        if file_type:
            filtered_docs = [
                d for d in filtered_docs
                if d.get('metadata', {}).get('file_type', '').lower() == file_type.lower()
            ]
        
        if filename_contains:
            pattern = filename_contains.lower()
            filtered_docs = [
                d for d in filtered_docs
                if pattern in d.get('metadata', {}).get('filename', '').lower()
            ]
        
        # Sort
        if sort_by:
            reverse = sort_order.lower() == 'desc'
            if sort_by == 'filename':
                filtered_docs.sort(
                    key=lambda x: x.get('metadata', {}).get('filename', '').lower(),
                    reverse=reverse
                )
            elif sort_by == 'created_at':
                filtered_docs.sort(
                    key=lambda x: x.get('metadata', {}).get('created_at', ''),
                    reverse=reverse
                )
            elif sort_by == 'modified_at':
                filtered_docs.sort(
                    key=lambda x: x.get('metadata', {}).get('modified_at', ''),
                    reverse=reverse
                )
            elif sort_by == 'file_size_mb':
                filtered_docs.sort(
                    key=lambda x: float(x.get('metadata', {}).get('file_size_mb', 0)),
                    reverse=reverse
                )
            elif sort_by == 'page_count':
                filtered_docs.sort(
                    key=lambda x: x.get('metadata', {}).get('page_count') or 0,
                    reverse=reverse
                )
        
        # Paginate
        total_count = len(filtered_docs)
        total_pages = (total_count + page_size - 1) // page_size
        paginated_docs = filtered_docs[offset:offset + page_size]
        
        # Convert to response models
        documents = [_convert_to_metadata_response(doc) for doc in paginated_docs]
        
        return {
            "success": True,
            "total_documents": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "documents": documents
        }
    
    except Exception as e:
        logger.error(f"List documents failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.get("/{document_id}", response_model=DocumentMetadataResponse)
async def get_document(document_id: str = Path(..., description="Document ID")):
    """
    Get detailed metadata for a specific document.
    
    **Example Response:**
    ```json
    {
        "document_id": "abc-123",
        "filename": "quarterly_report.pdf",
        "file_path": "/data/documents/abc-123_quarterly_report.pdf",
        "file_size_mb": 2.5,
        "file_type": ".pdf",
        "page_count": 15,
        "created_at": "2024-01-15T10:30:00",
        "modified_at": "2024-01-15T10:30:00",
        "title": "Q4 2023 Quarterly Report",
        "author": "Finance Team",
        "ai_summary": "This document presents the financial results...",
        "ai_keywords": ["finance", "quarterly", "report"],
        "ai_document_type": "financial_report"
    }
    ```
    """
    components = get_components()
    metadata_store = components['metadata_store']
    
    try:
        metadata_dict = metadata_store.get_document_metadata(document_id)
        
        if not metadata_dict:
            raise HTTPException(status_code=404, detail=f"Document not found: {document_id}")
        
        doc = {
            'document_id': document_id,
            'metadata': metadata_dict
        }
        
        return _convert_to_metadata_response(doc)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


# ============================================================
# ADVANCED SEARCH ENDPOINTS
# ============================================================

@router.post("/search", response_model=AdvancedSearchResponse)
async def advanced_search(request: AdvancedSearchRequest):
    """
    Advanced document search combining metadata and semantic search.
    
    Supports:
    - Semantic search with natural language queries
    - Metadata filtering (file type, author, date range, etc.)
    - Hybrid search combining both
    - Document-level and chunk-level relevance scoring
    - Sorting and pagination
    
    **Example Request:**
    ```json
    {
        "query": "machine learning algorithms",
        "file_types": [".pdf", ".docx"],
        "created_after": "2024-01-01",
        "include_chunk_scores": true,
        "top_k": 10
    }
    ```
    
    **Example Response:**
    ```json
    {
        "success": true,
        "total_results": 5,
        "search_type": "hybrid",
        "documents": [
            {
                "document_id": "abc-123",
                "filename": "ml_guide.pdf",
                "document_score": 0.85,
                "chunk_score": 0.92,
                "aggregated_score": 0.89,
                "relevant_chunks": [...]
            }
        ]
    }
    ```
    """
    components = get_components()
    search_service = components['search_service']
    
    try:
        logger.info(f"Advanced search: query='{request.query}', filters present={request.file_types is not None}")
        
        results, search_type, processing_time = search_service.advanced_search(request)
        
        return AdvancedSearchResponse(
            success=True,
            total_results=len(results),
            documents=results,
            query_params=request.model_dump(exclude_none=True),
            search_type=search_type,
            processing_time_ms=round(processing_time, 2)
        )
    
    except Exception as e:
        logger.error(f"Advanced search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/search", response_model=AdvancedSearchResponse)
async def search_documents_get(
    query: Optional[str] = Query(default=None, description="Semantic search query"),
    filename_contains: Optional[str] = Query(default=None, description="Filter by filename pattern"),
    file_types: Optional[str] = Query(default=None, description="Comma-separated file types (.pdf,.docx)"),
    document_types: Optional[str] = Query(default=None, description="Comma-separated document types"),
    authors: Optional[str] = Query(default=None, description="Comma-separated authors"),
    tags: Optional[str] = Query(default=None, description="Comma-separated tags"),
    min_pages: Optional[int] = Query(default=None, ge=1, description="Minimum page count"),
    max_pages: Optional[int] = Query(default=None, description="Maximum page count"),
    min_size_mb: Optional[float] = Query(default=None, ge=0, description="Minimum file size in MB"),
    max_size_mb: Optional[float] = Query(default=None, description="Maximum file size in MB"),
    created_after: Optional[str] = Query(default=None, description="Created after (ISO date)"),
    created_before: Optional[str] = Query(default=None, description="Created before (ISO date)"),
    include_chunk_scores: bool = Query(default=False, description="Include chunk-level relevance"),
    top_k: int = Query(default=20, ge=1, le=100, description="Number of results"),
    sort_by: Optional[str] = Query(default=None, description="Sort field"),
    sort_order: str = Query(default="desc", description="Sort order: asc or desc")
):
    """
    Search documents with filters via GET request.
    
    Accepts filters as query parameters for easy URL-based searching.
    
    **Example:**
    ```
    GET /documents/search?query=machine+learning&file_types=.pdf,.docx&top_k=10
    ```
    """
    # Parse comma-separated values
    file_types_list = [ft.strip() for ft in file_types.split(',')] if file_types else None
    doc_types_list = [dt.strip() for dt in document_types.split(',')] if document_types else None
    authors_list = [a.strip() for a in authors.split(',')] if authors else None
    tags_list = [t.strip() for t in tags.split(',')] if tags else None
    
    # Convert sort_by string to enum if provided
    sort_field = None
    if sort_by:
        try:
            sort_field = SortField(sort_by)
        except ValueError:
            pass
    
    # Build request
    request = AdvancedSearchRequest(
        query=query,
        filename_contains=filename_contains,
        file_types=file_types_list,
        document_types=doc_types_list,
        authors=authors_list,
        tags=tags_list,
        min_pages=min_pages,
        max_pages=max_pages,
        min_size_mb=min_size_mb,
        max_size_mb=max_size_mb,
        created_after=created_after,
        created_before=created_before,
        include_chunk_scores=include_chunk_scores,
        top_k=top_k,
        sort_by=sort_field,
        sort_order=SortOrder(sort_order.lower()) if sort_order else SortOrder.desc
    )
    
    return await advanced_search(request)


# ============================================================
# RECOMMENDATION ENDPOINTS
# ============================================================

@router.get("/recommend", response_model=RecommendationResponse)
async def get_recommendations(
    query: str = Query(..., min_length=1, description="Query for recommendations"),
    top_k: int = Query(default=10, ge=1, le=50, description="Number of recommendations"),
    file_types: Optional[str] = Query(default=None, description="Comma-separated file types")
):
    """
    Get semantic file recommendations based on a query.
    
    Returns the most relevant documents based on semantic similarity
    of their summaries to the query.
    
    **Example:**
    ```
    GET /documents/recommend?query=financial+analysis&top_k=5
    ```
    
    **Example Response:**
    ```json
    {
        "success": true,
        "query": "financial analysis",
        "total_results": 5,
        "recommendations": [
            {
                "document_id": "abc-123",
                "filename": "q4_report.pdf",
                "document_score": 0.89,
                "ai_summary": "Financial analysis of Q4 performance..."
            }
        ]
    }
    ```
    """
    components = get_components()
    search_service = components['search_service']
    
    try:
        logger.info(f"Getting recommendations for: '{query}'")
        
        file_types_list = [ft.strip() for ft in file_types.split(',')] if file_types else None
        
        recommendations = search_service.get_recommendations(
            query=query,
            top_k=top_k,
            file_types=file_types_list
        )
        
        return RecommendationResponse(
            success=True,
            query=query,
            total_results=len(recommendations),
            recommendations=recommendations
        )
    
    except Exception as e:
        logger.error(f"Get recommendations failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@router.post("/recommend", response_model=RecommendationResponse)
async def get_recommendations_post(request: RecommendationRequest):
    """
    Get semantic file recommendations based on a query (POST version).
    
    **Example Request:**
    ```json
    {
        "query": "machine learning tutorials",
        "top_k": 10,
        "file_types": [".pdf"],
        "exclude_document_ids": ["doc-to-exclude"]
    }
    ```
    """
    components = get_components()
    search_service = components['search_service']
    
    try:
        logger.info(f"Getting recommendations for: '{request.query}'")
        
        recommendations = search_service.get_recommendations(
            query=request.query,
            top_k=request.top_k,
            file_types=request.file_types,
            exclude_ids=request.exclude_document_ids
        )
        
        return RecommendationResponse(
            success=True,
            query=request.query,
            total_results=len(recommendations),
            recommendations=recommendations
        )
    
    except Exception as e:
        logger.error(f"Get recommendations failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


# ============================================================
# SIMILAR DOCUMENTS ENDPOINT
# ============================================================

@router.get("/{document_id}/similar", response_model=SimilarDocumentsResponse)
async def find_similar_documents(
    document_id: str = Path(..., description="Source document ID"),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum similar documents")
):
    """
    Find documents similar to a given document.
    
    Uses document-level embeddings to find conceptually similar documents.
    The source document is excluded from results.
    
    **Example:**
    ```
    GET /documents/abc-123/similar?limit=10
    ```
    
    **Example Response:**
    ```json
    {
        "success": true,
        "source_document_id": "abc-123",
        "source_document_filename": "ml_guide.pdf",
        "total_results": 5,
        "similar_documents": [
            {
                "document_id": "def-456",
                "filename": "deep_learning.pdf",
                "document_score": 0.87,
                "ai_summary": "Guide to deep learning..."
            }
        ]
    }
    ```
    """
    components = get_components()
    search_service = components['search_service']
    
    try:
        logger.info(f"Finding similar documents for: {document_id}")
        
        source_info, similar_docs = search_service.find_similar_documents(
            document_id=document_id,
            limit=limit
        )
        
        return SimilarDocumentsResponse(
            success=True,
            source_document_id=source_info['document_id'],
            source_document_filename=source_info['filename'],
            total_results=len(similar_docs),
            similar_documents=similar_docs
        )
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Find similar documents failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to find similar documents: {str(e)}")


# ============================================================
# SMART SUMMARY ENDPOINT
# ============================================================

@router.get("/{document_id}/summary", response_model=DocumentSummaryResponse)
async def get_document_summary(
    document_id: str = Path(..., description="Document ID"),
    force_regenerate: bool = Query(default=False, description="Force regeneration even if cached")
):
    """
    Get an intelligent summary of a document.
    
    Combines extracted content and metadata to generate a comprehensive
    summary using LLM. Results are cached to avoid repeated LLM calls.
    
    **Example:**
    ```
    GET /documents/abc-123/summary
    ```
    
    **Example Response:**
    ```json
    {
        "success": true,
        "document_id": "abc-123",
        "filename": "quarterly_report.pdf",
        "summary": "This document presents the Q4 2023 financial results...",
        "key_topics": ["financial results", "revenue growth", "market analysis"],
        "metadata_summary": {
            "file_info": {"type": ".pdf", "size_mb": 2.5, "page_count": 15},
            "dates": {"created": "2024-01-15", "modified": "2024-01-15"},
            "authorship": {"title": "Q4 Report", "author": "Finance Team"},
            "classification": {"document_type": "financial_report"}
        },
        "cached": true,
        "generated_at": "2024-01-20T14:30:00"
    }
    ```
    """
    components = get_components()
    metadata_store = components['metadata_store']
    vector_store = components['vector_store']
    summary_generator = components['summary_generator']
    
    try:
        logger.info(f"Getting summary for document: {document_id}")
        
        # Get document metadata
        metadata = metadata_store.get_document_metadata(document_id)
        if not metadata:
            raise HTTPException(status_code=404, detail=f"Document not found: {document_id}")
        
        filename = metadata.get('filename', 'unknown')
        
        # Get content preview from chunks
        try:
            documents, _, _, _ = vector_store.query(
                query_embedding=[0.0] * 384,  # Dummy embedding, we filter by doc ID
                top_k=5,
                filter_metadata={"document_id": document_id}
            )
            content_preview = " ".join(documents[:3]) if documents else ""
        except Exception:
            content_preview = metadata.get('ai_summary', '')
        
        # Generate summary
        result = summary_generator.generate_smart_summary(
            document_id=document_id,
            filename=filename,
            content_preview=content_preview,
            metadata=metadata,
            force_regenerate=force_regenerate
        )
        
        return DocumentSummaryResponse(
            success=True,
            document_id=document_id,
            filename=filename,
            summary=result['summary'],
            key_topics=result.get('key_topics'),
            metadata_summary=result.get('metadata_summary', {}),
            cached=result.get('cached', False),
            generated_at=result.get('generated_at', datetime.now().isoformat())
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document summary failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


# ============================================================
# ADDITIONAL UTILITY ENDPOINTS
# ============================================================

@router.get("/stats/overview")
async def get_documents_overview():
    """
    Get overview statistics for the document collection.
    
    **Example Response:**
    ```json
    {
        "success": true,
        "total_documents": 42,
        "total_chunks": 1234,
        "file_types": {".pdf": 30, ".docx": 12},
        "document_types": {"report": 15, "manual": 10, "other": 17},
        "total_size_mb": 156.8,
        "cache_stats": {"total_entries": 20}
    }
    ```
    """
    components = get_components()
    metadata_store = components['metadata_store']
    vector_store = components['vector_store']
    summary_cache = components['summary_cache']
    
    try:
        # Get metadata stats
        meta_stats = metadata_store.get_statistics()
        
        # Get vector store stats
        vector_stats = vector_store.get_collection_stats()
        
        # Get all docs for size calculation
        all_docs = metadata_store.list_all_documents(limit=10000)
        total_size = sum(
            float(d.get('metadata', {}).get('file_size_mb', 0))
            for d in all_docs
        )
        
        # Get cache stats
        cache_stats = summary_cache.get_stats()
        
        return {
            "success": True,
            "total_documents": meta_stats.get('total_documents', 0),
            "total_chunks": vector_stats.get('total_chunks', 0),
            "file_types": meta_stats.get('file_type_distribution', {}),
            "document_types": meta_stats.get('document_type_distribution', {}),
            "total_size_mb": round(total_size, 2),
            "cache_stats": cache_stats
        }
    
    except Exception as e:
        logger.error(f"Get overview failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get overview: {str(e)}")


@router.delete("/{document_id}/summary/cache")
async def clear_document_summary_cache(document_id: str = Path(..., description="Document ID")):
    """
    Clear the cached summary for a specific document.
    
    Useful when document content has been updated and you want
    to regenerate the summary.
    """
    components = get_components()
    summary_cache = components['summary_cache']
    
    try:
        invalidated = summary_cache.invalidate(document_id)
        
        return {
            "success": True,
            "message": "Cache cleared" if invalidated else "No cache entry found",
            "document_id": document_id
        }
    
    except Exception as e:
        logger.error(f"Clear cache failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")
