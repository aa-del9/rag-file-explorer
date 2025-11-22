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
