"""
Metadata search and explorer router.
Provides endpoints for metadata-based search, filtering, and document exploration.
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pathlib import Path

from app.models_metadata import (
    MetadataSearchRequest,
    MetadataSearchResponse,
    SemanticSearchRequest,
    ExplorerListResponse,
    MetadataStatsResponse,
    DocumentMetadataResponse
)
from app.config import settings
from app.metadata_store import MetadataStore
from app.embeddings import get_embedding_model

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metadata", tags=["metadata", "explorer"])

# Lazy-loaded components (initialized on first use)
_metadata_store = None
_embedding_model = None


def get_components():
    """Lazy initialization of heavy components."""
    global _metadata_store, _embedding_model
    
    if _embedding_model is None:
        _embedding_model = get_embedding_model(
            model_name=settings.EMBEDDING_MODEL,
            device=settings.EMBEDDING_DEVICE
        )
    
    if _metadata_store is None:
        _metadata_store = MetadataStore(
            persist_directory=settings.CHROMA_DIR
        )
    
    return _metadata_store, _embedding_model


def _build_chromadb_filter(search_params: MetadataSearchRequest) -> Optional[dict]:
    """
    Build ChromaDB where clause from search parameters.
    
    Args:
        search_params: Search request parameters
        
    Returns:
        ChromaDB filter dict or None
    """
    conditions = []
    
    # File type filter
    if search_params.file_type:
        conditions.append({"file_type": {"$eq": search_params.file_type.lower()}})
    
    # Document type filter
    if search_params.document_type:
        conditions.append({"ai_document_type": {"$eq": search_params.document_type.lower()}})
    
    # Author filter
    if search_params.author:
        conditions.append({"author": {"$eq": search_params.author}})
    
    # Page count filters
    if search_params.min_pages is not None:
        conditions.append({"page_count": {"$gte": search_params.min_pages}})
    
    if search_params.max_pages is not None:
        conditions.append({"page_count": {"$lte": search_params.max_pages}})
    
    # Return combined filter or None
    if not conditions:
        return None
    
    if len(conditions) == 1:
        return conditions[0]
    
    return {"$and": conditions}


def _convert_to_response_model(doc: dict) -> DocumentMetadataResponse:
    """
    Convert internal document representation to response model.
    
    Args:
        doc: Document dictionary from metadata store
        
    Returns:
        DocumentMetadataResponse model
    """
    metadata = doc.get('metadata', {})
    
    # Parse keywords if stored as comma-separated string
    keywords = metadata.get('ai_keywords', '')
    if isinstance(keywords, str):
        keywords = [k.strip() for k in keywords.split(',') if k.strip()]
    elif not isinstance(keywords, list):
        keywords = []
    
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
        ai_keywords=keywords,
        ai_document_type=metadata.get('ai_document_type'),
        similarity_score=doc.get('similarity_score')
    )


@router.post("/search", response_model=MetadataSearchResponse)
async def search_documents_by_metadata(request: MetadataSearchRequest):
    """
    Search documents by metadata filters.
    
    Supports filtering by:
    - Filename pattern
    - File type (pdf, docx, doc)
    - Document type (invoice, report, etc.)
    - Author
    - Keywords
    - Page count range
    - Date range
    """
    # Get components (lazy initialization)
    metadata_store, _ = get_components()
    
    try:
        logger.info(f"Metadata search request: {request.dict()}")
        
        # Build ChromaDB filter
        filters = _build_chromadb_filter(request)
        
        # Search with filters
        results = metadata_store.search_by_filters(
            filters=filters if filters else {},
            limit=request.limit
        )
        
        # Additional client-side filtering for fields not supported by ChromaDB
        filtered_results = results
        
        # Filename contains filter
        if request.filename_contains:
            pattern = request.filename_contains.lower()
            filtered_results = [
                doc for doc in filtered_results
                if pattern in doc['metadata'].get('filename', '').lower()
            ]
        
        # Keywords filter (any keyword match)
        if request.keywords:
            search_keywords = [k.lower() for k in request.keywords]
            filtered_results = [
                doc for doc in filtered_results
                if any(
                    kw in doc['metadata'].get('ai_keywords', '').lower()
                    for kw in search_keywords
                )
            ]
        
        # Convert to response models
        document_responses = [_convert_to_response_model(doc) for doc in filtered_results]
        
        return MetadataSearchResponse(
            success=True,
            total_results=len(document_responses),
            documents=document_responses,
            query_params=request.dict()
        )
    
    except Exception as e:
        logger.error(f"Metadata search failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Metadata search failed: {str(e)}"
        )


@router.post("/semantic-search", response_model=MetadataSearchResponse)
async def semantic_search_documents(request: SemanticSearchRequest):
    """
    Semantic search across document summaries.
    
    Finds documents whose summaries are semantically similar to the query.
    Useful for finding documents by topic or content without exact keyword matches.
    """
    # Get components (lazy initialization)
    metadata_store, embedding_model = get_components()
    
    try:
        logger.info(f"Semantic search request: {request.query}")
        
        # Generate query embedding
        query_embedding = embedding_model.embed_text(request.query)
        
        # Build optional filters
        filters = None
        if request.file_type or request.document_type:
            filter_conditions = []
            if request.file_type:
                filter_conditions.append({"file_type": {"$eq": request.file_type.lower()}})
            if request.document_type:
                filter_conditions.append({"ai_document_type": {"$eq": request.document_type.lower()}})
            
            filters = filter_conditions[0] if len(filter_conditions) == 1 else {"$and": filter_conditions}
        
        # Perform semantic search
        results = metadata_store.semantic_search(
            query_embedding=query_embedding,
            top_k=request.top_k,
            filters=filters
        )
        
        # Convert to response models
        document_responses = [_convert_to_response_model(doc) for doc in results]
        
        return MetadataSearchResponse(
            success=True,
            total_results=len(document_responses),
            documents=document_responses,
            query_params={"query": request.query, "top_k": request.top_k}
        )
    
    except Exception as e:
        logger.error(f"Semantic search failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Semantic search failed: {str(e)}"
        )


@router.get("/list", response_model=ExplorerListResponse)
async def list_all_documents(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page")
):
    """
    List all documents with metadata for explorer UI.
    
    Supports pagination for large document collections.
    """
    # Get components (lazy initialization)
    metadata_store, _ = get_components()
    
    try:
        offset = (page - 1) * page_size
        
        logger.info(f"Listing documents: page={page}, page_size={page_size}")
        
        # Get documents with pagination
        results = metadata_store.list_all_documents(
            limit=page_size,
            offset=offset
        )
        
        # Get total count
        stats = metadata_store.get_statistics()
        total_count = stats.get('total_documents', 0)
        
        # Convert to response models
        document_responses = [_convert_to_response_model(doc) for doc in results]
        
        return ExplorerListResponse(
            success=True,
            total_documents=total_count,
            documents=document_responses,
            page=page,
            page_size=page_size
        )
    
    except Exception as e:
        logger.error(f"List documents failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get("/stats", response_model=MetadataStatsResponse)
async def get_metadata_statistics():
    """
    Get statistics about stored document metadata.
    
    Returns:
    - Total document count
    - File type distribution
    - Document type distribution
    - Total storage size
    """
    # Get components (lazy initialization)
    metadata_store, _ = get_components()
    
    try:
        stats = metadata_store.get_statistics()
        
        # Calculate total size
        all_docs = metadata_store.list_all_documents(limit=10000)
        total_size_mb = sum(
            float(doc['metadata'].get('file_size_mb', 0))
            for doc in all_docs
        )
        
        return MetadataStatsResponse(
            success=True,
            total_documents=stats.get('total_documents', 0),
            file_type_distribution=stats.get('file_type_distribution', {}),
            document_type_distribution=stats.get('document_type_distribution', {}),
            total_size_mb=round(total_size_mb, 2),
            collection_name=stats.get('collection_name', '')
        )
    
    except Exception as e:
        logger.error(f"Get statistics failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.get("/document/{document_id}", response_model=DocumentMetadataResponse)
async def get_document_metadata(document_id: str):
    """
    Get detailed metadata for a specific document.
    """
    # Get components (lazy initialization)
    metadata_store, _ = get_components()
    
    try:
        metadata_dict = metadata_store.get_document_metadata(document_id)
        
        if not metadata_dict:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {document_id}"
            )
        
        # Convert to response model
        doc = {
            'document_id': document_id,
            'metadata': metadata_dict
        }
        
        return _convert_to_response_model(doc)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document metadata failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get document metadata: {str(e)}"
        )
