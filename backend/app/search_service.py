"""
Search service module.
Provides advanced search functionality combining metadata and semantic search.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import time

from app.embeddings import EmbeddingModel
from app.vector_store import VectorStore
from app.metadata_store import MetadataStore
from app.models_metadata import (
    AdvancedSearchRequest,
    DocumentSearchResult,
    ChunkRelevance,
    SortField,
    SortOrder
)

logger = logging.getLogger(__name__)

# UUID pattern: 8-4-4-4-12 hex characters
UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}_', re.IGNORECASE)


def get_display_name(filename: str) -> str:
    """
    Extract the display name from a filename by removing the UUID prefix.
    
    Filenames are stored as: {uuid}_{original_filename}
    e.g., "a1b2c3d4-e5f6-7890-abcd-ef1234567890_report.pdf" -> "report.pdf"
    """
    if not filename:
        return filename
    
    match = UUID_PATTERN.match(filename)
    if match:
        return filename[match.end():]
    
    return filename


class SearchService:
    """
    Advanced search service combining metadata and semantic search.
    Supports filtering, ranking, and relevance scoring at both
    document and chunk levels.
    """
    
    def __init__(
        self,
        embedding_model: EmbeddingModel,
        vector_store: VectorStore,
        metadata_store: MetadataStore
    ):
        """
        Initialize search service with required components.
        
        Args:
            embedding_model: Model for generating embeddings
            vector_store: Vector store for chunk embeddings
            metadata_store: Metadata store for document-level data
        """
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.metadata_store = metadata_store
        
        logger.info("SearchService initialized")
    
    def advanced_search(
        self,
        request: AdvancedSearchRequest
    ) -> Tuple[List[DocumentSearchResult], str, float]:
        """
        Perform advanced search with combined metadata and semantic search.
        
        Args:
            request: Advanced search request with filters and options
            
        Returns:
            Tuple of (results, search_type, processing_time_ms)
        """
        start_time = time.time()
        
        # Determine search type
        has_semantic_query = request.query and request.query.strip()
        has_filters = self._has_filters(request)
        
        if has_semantic_query and has_filters:
            search_type = "hybrid"
        elif has_semantic_query:
            search_type = "semantic"
        else:
            search_type = "metadata"
        
        logger.info(f"Performing {search_type} search")
        
        try:
            if search_type == "semantic":
                results = self._semantic_search(request)
            elif search_type == "metadata":
                results = self._metadata_search(request)
            else:  # hybrid
                results = self._hybrid_search(request)
            
            # Apply sorting
            results = self._sort_results(results, request.sort_by, request.sort_order)
            
            # Limit results
            results = results[:request.top_k]
            
            processing_time = (time.time() - start_time) * 1000  # ms
            
            return results, search_type, processing_time
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise
    
    def _has_filters(self, request: AdvancedSearchRequest) -> bool:
        """Check if request has any metadata filters."""
        return any([
            request.filename_contains,
            request.file_types,
            request.document_types,
            request.authors,
            request.tags,
            request.keywords,
            request.min_pages is not None,
            request.max_pages is not None,
            request.min_size_mb is not None,
            request.max_size_mb is not None,
            request.created_after,
            request.created_before,
            request.modified_after,
            request.modified_before
        ])
    
    def _semantic_search(
        self,
        request: AdvancedSearchRequest
    ) -> List[DocumentSearchResult]:
        """Perform semantic-only search."""
        # Generate query embedding
        query_embedding = self.embedding_model.embed_text(request.query)
        
        if request.use_doc_level_ranking:
            # Document-level semantic search first
            doc_results = self.metadata_store.semantic_search(
                query_embedding=query_embedding,
                top_k=request.top_k * 2  # Get more for re-ranking
            )
            
            results = []
            for doc in doc_results:
                result = self._convert_to_search_result(doc)
                result.document_score = doc.get('similarity_score', 0.0)
                
                # Optionally get chunk scores
                if request.include_chunk_scores:
                    chunk_scores = self._get_chunk_scores(
                        doc['document_id'],
                        query_embedding
                    )
                    result.relevant_chunks = chunk_scores[:5]  # Top 5 chunks
                    result.chunk_score = chunk_scores[0].similarity_score if chunk_scores else 0.0
                    result.aggregated_score = (
                        result.document_score * 0.4 + result.chunk_score * 0.6
                    )
                else:
                    result.aggregated_score = result.document_score
                
                results.append(result)
        else:
            # Chunk-level search with aggregation
            results = self._chunk_aggregated_search(query_embedding, request)
        
        return results
    
    def _metadata_search(
        self,
        request: AdvancedSearchRequest
    ) -> List[DocumentSearchResult]:
        """Perform metadata-only search."""
        # Build ChromaDB filter
        filters = self._build_chromadb_filter(request)
        
        # Get documents matching filters
        if filters:
            doc_results = self.metadata_store.search_by_filters(
                filters=filters,
                limit=request.top_k * 2
            )
        else:
            doc_results = self.metadata_store.list_all_documents(
                limit=request.top_k * 2
            )
        
        # Apply additional client-side filters
        doc_results = self._apply_client_filters(doc_results, request)
        
        results = [self._convert_to_search_result(doc) for doc in doc_results]
        
        return results
    
    def _hybrid_search(
        self,
        request: AdvancedSearchRequest
    ) -> List[DocumentSearchResult]:
        """Perform hybrid search combining semantic and metadata."""
        # Generate query embedding
        query_embedding = self.embedding_model.embed_text(request.query)
        
        # Build filters
        filters = self._build_chromadb_filter(request)
        
        # Semantic search with filters
        doc_results = self.metadata_store.semantic_search(
            query_embedding=query_embedding,
            top_k=request.top_k * 3,  # Get more for filtering
            filters=filters
        )
        
        # Apply additional client-side filters
        doc_results = self._apply_client_filters(doc_results, request)
        
        results = []
        for doc in doc_results:
            result = self._convert_to_search_result(doc)
            result.document_score = doc.get('similarity_score', 0.0)
            
            if request.include_chunk_scores:
                chunk_scores = self._get_chunk_scores(
                    doc['document_id'],
                    query_embedding
                )
                result.relevant_chunks = chunk_scores[:5]
                result.chunk_score = chunk_scores[0].similarity_score if chunk_scores else 0.0
                result.aggregated_score = (
                    result.document_score * 0.4 + result.chunk_score * 0.6
                )
            else:
                result.aggregated_score = result.document_score
            
            results.append(result)
        
        return results
    
    def _chunk_aggregated_search(
        self,
        query_embedding: List[float],
        request: AdvancedSearchRequest
    ) -> List[DocumentSearchResult]:
        """
        Search chunks and aggregate scores per document.
        """
        # Search chunks
        documents, metadatas, distances, ids = self.vector_store.query(
            query_embedding=query_embedding,
            top_k=request.top_k * 10  # Get many chunks
        )
        
        # Aggregate by document
        doc_scores: Dict[str, Dict] = {}
        for i, (doc_text, metadata, distance, chunk_id) in enumerate(
            zip(documents, metadatas, distances, ids)
        ):
            doc_id = metadata.get('document_id', 'unknown')
            similarity = 1.0 / (1.0 + distance)
            
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {
                    'scores': [],
                    'chunks': [],
                    'best_score': 0.0
                }
            
            doc_scores[doc_id]['scores'].append(similarity)
            doc_scores[doc_id]['chunks'].append(
                ChunkRelevance(
                    chunk_id=chunk_id,
                    text=doc_text[:300] + "..." if len(doc_text) > 300 else doc_text,
                    similarity_score=round(similarity, 4),
                    chunk_index=metadata.get('chunk_index')
                )
            )
            
            if similarity > doc_scores[doc_id]['best_score']:
                doc_scores[doc_id]['best_score'] = similarity
        
        # Get document metadata and build results
        results = []
        for doc_id, scores_data in doc_scores.items():
            doc_metadata = self.metadata_store.get_document_metadata(doc_id)
            if not doc_metadata:
                continue
            
            # Calculate aggregated score (mean of top 3 chunk scores)
            top_scores = sorted(scores_data['scores'], reverse=True)[:3]
            aggregated_score = sum(top_scores) / len(top_scores) if top_scores else 0.0
            
            result = self._convert_metadata_to_search_result(doc_id, doc_metadata)
            result.chunk_score = scores_data['best_score']
            result.aggregated_score = aggregated_score
            
            if request.include_chunk_scores:
                result.relevant_chunks = sorted(
                    scores_data['chunks'],
                    key=lambda x: x.similarity_score,
                    reverse=True
                )[:5]
            
            results.append(result)
        
        return results
    
    def _get_chunk_scores(
        self,
        document_id: str,
        query_embedding: List[float]
    ) -> List[ChunkRelevance]:
        """Get chunk-level relevance scores for a document."""
        try:
            # Query chunks filtered by document
            documents, metadatas, distances, ids = self.vector_store.query(
                query_embedding=query_embedding,
                top_k=20,
                filter_metadata={"document_id": document_id}
            )
            
            chunks = []
            for doc_text, metadata, distance, chunk_id in zip(
                documents, metadatas, distances, ids
            ):
                similarity = 1.0 / (1.0 + distance)
                chunks.append(
                    ChunkRelevance(
                        chunk_id=chunk_id,
                        text=doc_text[:300] + "..." if len(doc_text) > 300 else doc_text,
                        similarity_score=round(similarity, 4),
                        chunk_index=metadata.get('chunk_index')
                    )
                )
            
            return sorted(chunks, key=lambda x: x.similarity_score, reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to get chunk scores: {str(e)}")
            return []
    
    def _build_chromadb_filter(
        self,
        request: AdvancedSearchRequest
    ) -> Optional[Dict]:
        """Build ChromaDB where clause from search parameters."""
        conditions = []
        
        # File type filter
        if request.file_types and len(request.file_types) == 1:
            conditions.append({"file_type": {"$eq": request.file_types[0].lower()}})
        elif request.file_types and len(request.file_types) > 1:
            conditions.append({
                "$or": [{"file_type": {"$eq": ft.lower()}} for ft in request.file_types]
            })
        
        # Document type filter
        if request.document_types and len(request.document_types) == 1:
            conditions.append({"ai_document_type": {"$eq": request.document_types[0].lower()}})
        
        # Page count filters
        if request.min_pages is not None:
            conditions.append({"page_count": {"$gte": request.min_pages}})
        if request.max_pages is not None:
            conditions.append({"page_count": {"$lte": request.max_pages}})
        
        if not conditions:
            return None
        
        if len(conditions) == 1:
            return conditions[0]
        
        return {"$and": conditions}
    
    def _apply_client_filters(
        self,
        documents: List[Dict],
        request: AdvancedSearchRequest
    ) -> List[Dict]:
        """Apply filters that can't be done in ChromaDB."""
        filtered = documents
        
        # Filename contains
        if request.filename_contains:
            pattern = request.filename_contains.lower()
            filtered = [
                d for d in filtered
                if pattern in d.get('metadata', {}).get('filename', '').lower()
            ]
        
        # Author filter
        if request.authors:
            authors_lower = [a.lower() for a in request.authors]
            filtered = [
                d for d in filtered
                if d.get('metadata', {}).get('author', '').lower() in authors_lower
            ]
        
        # Keywords filter
        if request.keywords:
            search_keywords = [k.lower() for k in request.keywords]
            filtered = [
                d for d in filtered
                if any(
                    kw in d.get('metadata', {}).get('ai_keywords', '').lower()
                    for kw in search_keywords
                )
            ]
        
        # Tags filter
        if request.tags:
            search_tags = [t.lower() for t in request.tags]
            filtered = [
                d for d in filtered
                if any(
                    tag in d.get('metadata', {}).get('tags', '').lower()
                    for tag in search_tags
                )
            ]
        
        # Size filters
        if request.min_size_mb is not None:
            filtered = [
                d for d in filtered
                if float(d.get('metadata', {}).get('file_size_mb', 0)) >= request.min_size_mb
            ]
        if request.max_size_mb is not None:
            filtered = [
                d for d in filtered
                if float(d.get('metadata', {}).get('file_size_mb', 0)) <= request.max_size_mb
            ]
        
        # Date filters
        if request.created_after:
            filtered = [
                d for d in filtered
                if d.get('metadata', {}).get('created_at', '') >= request.created_after
            ]
        if request.created_before:
            filtered = [
                d for d in filtered
                if d.get('metadata', {}).get('created_at', '') <= request.created_before
            ]
        if request.modified_after:
            filtered = [
                d for d in filtered
                if d.get('metadata', {}).get('modified_at', '') >= request.modified_after
            ]
        if request.modified_before:
            filtered = [
                d for d in filtered
                if d.get('metadata', {}).get('modified_at', '') <= request.modified_before
            ]
        
        return filtered
    
    def _convert_to_search_result(self, doc: Dict) -> DocumentSearchResult:
        """Convert internal document dict to search result."""
        metadata = doc.get('metadata', {})
        
        # Parse keywords
        keywords = metadata.get('ai_keywords', '')
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(',') if k.strip()]
        
        # Parse tags
        tags = metadata.get('tags', '')
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',') if t.strip()]
        
        # Get preview snippet
        preview = doc.get('summary', '')
        if len(preview) > 200:
            preview = preview[:200] + "..."
        
        # Get filename and display name
        filename = metadata.get('filename', 'unknown')
        display_name = get_display_name(filename)
        
        return DocumentSearchResult(
            document_id=doc.get('document_id', ''),
            filename=filename,
            display_name=display_name,
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
            tags=tags if isinstance(tags, list) else None,
            preview_snippet=preview if preview else None
        )
    
    def _convert_metadata_to_search_result(
        self,
        doc_id: str,
        metadata: Dict
    ) -> DocumentSearchResult:
        """Convert metadata dict to search result."""
        # Parse keywords
        keywords = metadata.get('ai_keywords', '')
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(',') if k.strip()]
        
        # Parse tags
        tags = metadata.get('tags', '')
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',') if t.strip()]
        
        # Get filename and display name
        filename = metadata.get('filename', 'unknown')
        display_name = get_display_name(filename)
        
        return DocumentSearchResult(
            document_id=doc_id,
            filename=filename,
            display_name=display_name,
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
            tags=tags if isinstance(tags, list) else None
        )
    
    def _sort_results(
        self,
        results: List[DocumentSearchResult],
        sort_by: Optional[SortField],
        sort_order: SortOrder
    ) -> List[DocumentSearchResult]:
        """Sort results by specified field."""
        if not sort_by:
            # Default: sort by aggregated score or document score
            return sorted(
                results,
                key=lambda x: x.aggregated_score or x.document_score or 0,
                reverse=True
            )
        
        reverse = sort_order == SortOrder.desc
        
        if sort_by == SortField.filename:
            return sorted(results, key=lambda x: x.filename.lower(), reverse=reverse)
        elif sort_by == SortField.created_at:
            return sorted(results, key=lambda x: x.created_at or '', reverse=reverse)
        elif sort_by == SortField.modified_at:
            return sorted(results, key=lambda x: x.modified_at or '', reverse=reverse)
        elif sort_by == SortField.file_size_mb:
            return sorted(results, key=lambda x: x.file_size_mb, reverse=reverse)
        elif sort_by == SortField.page_count:
            return sorted(results, key=lambda x: x.page_count or 0, reverse=reverse)
        elif sort_by == SortField.relevance:
            return sorted(
                results,
                key=lambda x: x.aggregated_score or x.document_score or 0,
                reverse=True  # Always descending for relevance
            )
        
        return results
    
    def find_similar_documents(
        self,
        document_id: str,
        limit: int = 10,
        exclude_ids: Optional[List[str]] = None
    ) -> Tuple[Dict, List[DocumentSearchResult]]:
        """
        Find documents similar to a given document.
        
        Args:
            document_id: Source document ID
            limit: Maximum number of similar documents
            exclude_ids: Additional IDs to exclude
            
        Returns:
            Tuple of (source_doc_info, similar_documents)
        """
        # Get source document
        source_metadata = self.metadata_store.get_document_metadata(document_id)
        if not source_metadata:
            raise ValueError(f"Document not found: {document_id}")
        
        source_info = {
            'document_id': document_id,
            'filename': source_metadata.get('filename', 'unknown')
        }
        
        # Get the source document's embedding
        # We'll use the summary embedding from the metadata store
        results = self.metadata_store.collection.get(
            ids=[document_id],
            include=["embeddings"]
        )
        
        embeddings = results.get('embeddings')
        if not results['ids'] or embeddings is None or len(embeddings) == 0:
            # Fall back to generating embedding from summary
            summary = source_metadata.get('ai_summary', source_metadata.get('filename', ''))
            doc_embedding = self.embedding_model.embed_text(summary)
        else:
            doc_embedding = embeddings[0]
        
        # Search for similar documents
        similar_docs = self.metadata_store.semantic_search(
            query_embedding=doc_embedding,
            top_k=limit + len(exclude_ids or []) + 1  # Extra for exclusions
        )
        
        # Build exclusion set
        exclude_set = {document_id}
        if exclude_ids:
            exclude_set.update(exclude_ids)
        
        # Convert and filter results
        similar_results = []
        for doc in similar_docs:
            if doc['document_id'] in exclude_set:
                continue
            
            result = self._convert_to_search_result(doc)
            result.document_score = doc.get('similarity_score', 0.0)
            result.aggregated_score = result.document_score
            similar_results.append(result)
            
            if len(similar_results) >= limit:
                break
        
        return source_info, similar_results
    
    def get_recommendations(
        self,
        query: str,
        top_k: int = 10,
        file_types: Optional[List[str]] = None,
        exclude_ids: Optional[List[str]] = None
    ) -> List[DocumentSearchResult]:
        """
        Get document recommendations based on a query.
        
        Args:
            query: Natural language query
            top_k: Number of recommendations
            file_types: Optional file type filter
            exclude_ids: Document IDs to exclude
            
        Returns:
            List of recommended documents
        """
        # Generate query embedding
        query_embedding = self.embedding_model.embed_text(query)
        
        # Build filters
        filters = None
        if file_types and len(file_types) == 1:
            filters = {"file_type": {"$eq": file_types[0].lower()}}
        elif file_types and len(file_types) > 1:
            filters = {
                "$or": [{"file_type": {"$eq": ft.lower()}} for ft in file_types]
            }
        
        # Search with summary embeddings
        doc_results = self.metadata_store.semantic_search(
            query_embedding=query_embedding,
            top_k=top_k + len(exclude_ids or []),  # Extra for exclusions
            filters=filters
        )
        
        # Filter and convert results
        exclude_set = set(exclude_ids or [])
        recommendations = []
        
        for doc in doc_results:
            if doc['document_id'] in exclude_set:
                continue
            
            result = self._convert_to_search_result(doc)
            result.document_score = doc.get('similarity_score', 0.0)
            result.aggregated_score = result.document_score
            recommendations.append(result)
            
            if len(recommendations) >= top_k:
                break
        
        return recommendations
