"""
Vector store module using ChromaDB.
Manages persistent storage and retrieval of document embeddings.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings
import uuid

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Manages vector storage and similarity search using ChromaDB.
    Implements persistent storage for embeddings and metadata.
    """
    
    def __init__(self, persist_directory: Path, collection_name: str = "pdf_rag"):
        """
        Initialize ChromaDB client with persistent storage.
        
        Args:
            persist_directory: Path to store ChromaDB data
            collection_name: Name of the collection to use
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        try:
            logger.info(f"Initializing ChromaDB at {persist_directory}")
            
            # Create persistent ChromaDB client
            self.client = chromadb.PersistentClient(
                path=str(persist_directory),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "RAG PDF document embeddings"}
            )
            
            logger.info(f"ChromaDB initialized. Collection: {collection_name}")
            logger.info(f"Current collection size: {self.collection.count()} items")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}")
            raise Exception(f"Vector store initialization failed: {str(e)}")
    
    def upsert_chunks(
        self,
        chunks: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        chunk_ids: Optional[List[str]] = None
    ) -> int:
        """
        Insert or update document chunks with their embeddings.
        
        Args:
            chunks: List of text chunks
            embeddings: List of embedding vectors
            metadatas: List of metadata dictionaries
            chunk_ids: Optional list of custom IDs, otherwise generates UUIDs
            
        Returns:
            Number of chunks upserted
            
        Raises:
            ValueError: If input lists have mismatched lengths
        """
        if not (len(chunks) == len(embeddings) == len(metadatas)):
            raise ValueError(
                f"Mismatched lengths: chunks={len(chunks)}, "
                f"embeddings={len(embeddings)}, metadatas={len(metadatas)}"
            )
        
        if not chunks:
            logger.warning("No chunks to upsert")
            return 0
        
        try:
            # Generate IDs if not provided
            if chunk_ids is None:
                chunk_ids = [str(uuid.uuid4()) for _ in range(len(chunks))]
            
            logger.info(f"Upserting {len(chunks)} chunks to ChromaDB")
            
            # Ensure all metadata values are strings or numbers (ChromaDB requirement)
            processed_metadatas = []
            for metadata in metadatas:
                processed_metadata = {}
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float, bool)):
                        processed_metadata[key] = value
                    else:
                        processed_metadata[key] = str(value)
                processed_metadatas.append(processed_metadata)
            
            # Upsert to ChromaDB
            self.collection.upsert(
                ids=chunk_ids,
                documents=chunks,
                embeddings=embeddings,
                metadatas=processed_metadatas
            )
            
            logger.info(f"Successfully upserted {len(chunks)} chunks")
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Failed to upsert chunks: {str(e)}")
            raise Exception(f"Vector store upsert failed: {str(e)}")
    
    def query(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[str], List[Dict[str, Any]], List[float], List[str]]:
        """
        Query the vector store for similar chunks.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filter_metadata: Optional metadata filter
            
        Returns:
            Tuple of (documents, metadatas, distances, ids)
        """
        try:
            logger.info(f"Querying ChromaDB for top {top_k} results")
            
            # Build query parameters
            query_params = {
                "query_embeddings": [query_embedding],
                "n_results": min(top_k, self.collection.count()),  # Don't request more than available
            }
            
            if filter_metadata:
                query_params["where"] = filter_metadata
            
            # Query ChromaDB
            results = self.collection.query(**query_params)
            
            # Extract results
            documents = results["documents"][0] if results["documents"] else []
            metadatas = results["metadatas"][0] if results["metadatas"] else []
            distances = results["distances"][0] if results["distances"] else []
            ids = results["ids"][0] if results["ids"] else []
            
            logger.info(f"Query returned {len(documents)} results")
            
            return documents, metadatas, distances, ids
            
        except Exception as e:
            logger.error(f"Failed to query vector store: {str(e)}")
            raise Exception(f"Vector store query failed: {str(e)}")
    
    def delete_by_document_id(self, document_id: str) -> int:
        """
        Delete all chunks associated with a document.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            Number of chunks deleted
        """
        try:
            logger.info(f"Deleting chunks for document_id: {document_id}")
            
            # Query for all chunks with this document_id
            results = self.collection.get(
                where={"document_id": document_id}
            )
            
            if not results["ids"]:
                logger.info(f"No chunks found for document_id: {document_id}")
                return 0
            
            # Delete the chunks
            self.collection.delete(ids=results["ids"])
            
            deleted_count = len(results["ids"])
            logger.info(f"Deleted {deleted_count} chunks")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to delete chunks: {str(e)}")
            raise Exception(f"Vector store deletion failed: {str(e)}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store collection.
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            
            stats = {
                "collection_name": self.collection_name,
                "total_chunks": count,
                "persist_directory": str(self.persist_directory)
            }
            
            logger.info(f"Collection stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            return {"error": str(e)}
    
    def reset_collection(self) -> bool:
        """
        Delete all data from the collection (use with caution!).
        
        Returns:
            True if successful
        """
        try:
            logger.warning(f"Resetting collection: {self.collection_name}")
            
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "RAG PDF document embeddings"}
            )
            
            logger.info("Collection reset successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset collection: {str(e)}")
            return False
    
    def is_ready(self) -> bool:
        """
        Check if vector store is ready for operations.
        
        Returns:
            True if ready, False otherwise
        """
        try:
            self.collection.count()
            return True
        except Exception:
            return False
    
    def get_chunks_by_document(
        self,
        document_id: str,
        limit: int = 100
    ) -> Tuple[List[str], List[Dict[str, Any]], List[str]]:
        """
        Get all chunks for a specific document.
        
        Args:
            document_id: Document identifier
            limit: Maximum chunks to return
            
        Returns:
            Tuple of (documents, metadatas, ids)
        """
        try:
            results = self.collection.get(
                where={"document_id": document_id},
                limit=limit,
                include=["documents", "metadatas"]
            )
            
            return (
                results.get("documents", []),
                results.get("metadatas", []),
                results.get("ids", [])
            )
            
        except Exception as e:
            logger.error(f"Failed to get chunks by document: {str(e)}")
            return [], [], []
    
    def query_with_scores(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        include_embeddings: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Query the vector store and return structured results with scores.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filter_metadata: Optional metadata filter
            include_embeddings: Whether to include embeddings in results
            
        Returns:
            List of result dicts with text, metadata, score, and id
        """
        try:
            logger.info(f"Querying ChromaDB with scores for top {top_k} results")
            
            include = ["documents", "metadatas", "distances"]
            if include_embeddings:
                include.append("embeddings")
            
            query_params = {
                "query_embeddings": [query_embedding],
                "n_results": min(top_k, self.collection.count()),
                "include": include
            }
            
            if filter_metadata:
                query_params["where"] = filter_metadata
            
            results = self.collection.query(**query_params)
            
            structured_results = []
            for i in range(len(results["ids"][0])):
                similarity = 1.0 / (1.0 + results["distances"][0][i])
                
                result = {
                    "chunk_id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                    "similarity_score": round(similarity, 4)
                }
                
                if include_embeddings and results.get("embeddings"):
                    result["embedding"] = results["embeddings"][0][i]
                
                structured_results.append(result)
            
            logger.info(f"Query with scores returned {len(structured_results)} results")
            return structured_results
            
        except Exception as e:
            logger.error(f"Failed to query with scores: {str(e)}")
            return []
    
    def aggregate_document_scores(
        self,
        query_embedding: List[float],
        top_k_chunks: int = 50,
        top_k_docs: int = 10,
        aggregation_method: str = "max"  # "max", "mean", "top3_mean"
    ) -> List[Dict[str, Any]]:
        """
        Query chunks and aggregate scores by document.
        
        Args:
            query_embedding: Query embedding vector
            top_k_chunks: Number of chunks to retrieve
            top_k_docs: Number of documents to return
            aggregation_method: How to aggregate chunk scores per document
            
        Returns:
            List of documents with aggregated scores
        """
        try:
            # Get top chunks
            chunk_results = self.query_with_scores(
                query_embedding=query_embedding,
                top_k=top_k_chunks
            )
            
            # Aggregate by document
            doc_scores: Dict[str, Dict] = {}
            
            for chunk in chunk_results:
                doc_id = chunk["metadata"].get("document_id", "unknown")
                score = chunk["similarity_score"]
                
                if doc_id not in doc_scores:
                    doc_scores[doc_id] = {
                        "document_id": doc_id,
                        "scores": [],
                        "best_chunk": None,
                        "chunk_count": 0
                    }
                
                doc_scores[doc_id]["scores"].append(score)
                doc_scores[doc_id]["chunk_count"] += 1
                
                # Track best chunk
                if (doc_scores[doc_id]["best_chunk"] is None or 
                    score > doc_scores[doc_id]["best_chunk"]["similarity_score"]):
                    doc_scores[doc_id]["best_chunk"] = chunk
            
            # Calculate aggregated scores
            for doc_id, data in doc_scores.items():
                scores = data["scores"]
                if aggregation_method == "max":
                    data["aggregated_score"] = max(scores)
                elif aggregation_method == "mean":
                    data["aggregated_score"] = sum(scores) / len(scores)
                elif aggregation_method == "top3_mean":
                    top3 = sorted(scores, reverse=True)[:3]
                    data["aggregated_score"] = sum(top3) / len(top3)
                else:
                    data["aggregated_score"] = max(scores)
            
            # Sort by aggregated score and return top documents
            sorted_docs = sorted(
                doc_scores.values(),
                key=lambda x: x["aggregated_score"],
                reverse=True
            )[:top_k_docs]
            
            logger.info(f"Aggregated scores for {len(sorted_docs)} documents")
            return sorted_docs
            
        except Exception as e:
            logger.error(f"Failed to aggregate document scores: {str(e)}")
            return []
