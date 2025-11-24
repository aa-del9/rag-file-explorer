"""
Metadata storage module using ChromaDB.
Manages document-level metadata in a separate collection with semantic search capabilities.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import chromadb
from chromadb.config import Settings
from datetime import datetime

logger = logging.getLogger(__name__)


class MetadataStore:
    """
    Manages document metadata storage and retrieval using ChromaDB.
    Stores file-level metadata with semantic search capabilities.
    """
    
    def __init__(self, persist_directory: Path, collection_name: str = "document_metadata"):
        """
        Initialize metadata store with ChromaDB.
        
        Args:
            persist_directory: Path to ChromaDB storage
            collection_name: Name of metadata collection
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        try:
            logger.info(f"Initializing MetadataStore at {persist_directory}")
            
            # Create persistent ChromaDB client
            self.client = chromadb.PersistentClient(
                path=str(persist_directory),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create metadata collection
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "Document-level metadata with semantic search"}
            )
            
            logger.info(f"MetadataStore initialized. Documents: {self.collection.count()}")
            
        except Exception as e:
            logger.error(f"Failed to initialize MetadataStore: {str(e)}")
            raise Exception(f"Metadata store initialization failed: {str(e)}")
    
    def store_document_metadata(
        self,
        document_id: str,
        metadata: Dict[str, Any],
        summary_embedding: Optional[List[float]] = None,
        summary_text: Optional[str] = None
    ) -> bool:
        """
        Store metadata for a single document.
        
        Args:
            document_id: Unique document identifier
            metadata: Document metadata dictionary
            summary_embedding: Optional embedding of document summary
            summary_text: Optional summary text for storage
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Storing metadata for document: {document_id}")
            logger.info(f"Metadata keys: {list(metadata.keys())}")
            logger.info(f"Summary text length: {len(summary_text) if summary_text else 0}")
            logger.info(f"Has embedding: {summary_embedding is not None}")
            
            # Prepare metadata for ChromaDB (ensure all values are strings/numbers)
            clean_metadata = {}
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    clean_metadata[key] = value
                elif isinstance(value, list):
                    clean_metadata[key] = ", ".join(str(v) for v in value)
                elif value is not None:
                    clean_metadata[key] = str(value)
            
            # Add storage timestamp
            clean_metadata['stored_at'] = datetime.now().isoformat()
            
            # Use summary text as document content, or filename as fallback
            document_text = summary_text or clean_metadata.get('filename', document_id)
            
            # Store in ChromaDB
            if summary_embedding:
                self.collection.upsert(
                    ids=[document_id],
                    documents=[document_text],
                    embeddings=[summary_embedding],
                    metadatas=[clean_metadata]
                )
                logger.info(f"Stored with provided embedding")
            else:
                self.collection.upsert(
                    ids=[document_id],
                    documents=[document_text],
                    metadatas=[clean_metadata]
                )
                logger.info(f"Stored without embedding (ChromaDB will generate)")
            
            # Verify storage
            count = self.collection.count()
            logger.info(f"Successfully stored metadata for: {document_id}. Collection now has {count} documents")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store metadata: {str(e)}")
            return False
    
    def get_document_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve metadata for a specific document.
        
        Args:
            document_id: Document identifier
            
        Returns:
            Metadata dictionary or None if not found
        """
        try:
            results = self.collection.get(
                ids=[document_id],
                include=["metadatas", "documents"]
            )
            
            if results['ids']:
                metadata = results['metadatas'][0]
                metadata['document_text'] = results['documents'][0]
                return metadata
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve metadata: {str(e)}")
            return None
    
    def search_by_filters(
        self,
        filters: Dict[str, Any],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search documents by metadata filters.
        
        Args:
            filters: Dictionary of filter conditions (ChromaDB where clause)
            limit: Maximum number of results
            
        Returns:
            List of matching document metadata
        """
        try:
            logger.info(f"Searching with filters: {filters}")
            
            results = self.collection.get(
                where=filters,
                limit=limit,
                include=["metadatas", "documents"]
            )
            print("results: ",results)
            logger.info(f"Filter search returned {len(results['ids'])} results")
            documents = []
            for i, doc_id in enumerate(results['ids']):
                doc_data = {
                    'document_id': doc_id,
                    'metadata': results['metadatas'][i],
                    'summary': results['documents'][i]
                }
                documents.append(doc_data)
            
            logger.info(f"Found {len(documents)} documents matching filters")
            return documents
            
        except Exception as e:
            logger.error(f"Filter search failed: {str(e)}")
            return []
    
    def semantic_search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search across document summaries.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of relevant documents with scores
        """
        try:
            logger.info(f"Performing semantic search (top_k={top_k})")
            
            query_params = {
                "query_embeddings": [query_embedding],
                "n_results": min(top_k, self.collection.count())
            }
            
            if filters:
                query_params["where"] = filters
            
            results = self.collection.query(**query_params)
            
            documents = []
            for i, doc_id in enumerate(results['ids'][0]):
                doc_data = {
                    'document_id': doc_id,
                    'metadata': results['metadatas'][0][i],
                    'summary': results['documents'][0][i],
                    'similarity_score': 1.0 / (1.0 + results['distances'][0][i])  # Convert distance to similarity
                }
                documents.append(doc_data)
            
            logger.info(f"Semantic search returned {len(documents)} documents")
            return documents
            
        except Exception as e:
            logger.error(f"Semantic search failed: {str(e)}")
            return []
    
    def list_all_documents(
        self,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List all documents with metadata.
        
        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            
        Returns:
            List of document metadata
        """
        try:
            total_count = self.collection.count()
            logger.info(f"list_all_documents called: limit={limit}, offset={offset}, total_in_collection={total_count}")
            
            # Get all documents
            results = self.collection.get(
                limit=limit,
                offset=offset,
                include=["metadatas", "documents"]
            )
            
            logger.info(f"ChromaDB returned {len(results['ids'])} document IDs")
            
            documents = []
            for i, doc_id in enumerate(results['ids']):
                doc_data = {
                    'document_id': doc_id,
                    'metadata': results['metadatas'][i],
                    'summary': results['documents'][i]
                }
                documents.append(doc_data)
            
            logger.info(f"Listed {len(documents)} documents (total in collection: {total_count})")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to list documents: {str(e)}")
            return []
    
    def delete_document_metadata(self, document_id: str) -> bool:
        """
        Delete metadata for a document.
        
        Args:
            document_id: Document identifier
            
        Returns:
            True if successful
        """
        try:
            self.collection.delete(ids=[document_id])
            logger.info(f"Deleted metadata for: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete metadata: {str(e)}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored metadata.
        
        Returns:
            Statistics dictionary
        """
        try:
            count = self.collection.count()
            
            # Get all documents to calculate stats
            all_docs = self.list_all_documents(limit=1000)
            
            # Calculate file type distribution
            file_types = {}
            doc_types = {}
            
            for doc in all_docs:
                metadata = doc['metadata']
                
                # File type
                file_type = metadata.get('file_type', 'unknown')
                file_types[file_type] = file_types.get(file_type, 0) + 1
                
                # AI document type
                doc_type = metadata.get('ai_document_type', 'unknown')
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            stats = {
                "total_documents": count,
                "file_type_distribution": file_types,
                "document_type_distribution": doc_types,
                "collection_name": self.collection_name
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {str(e)}")
            return {"error": str(e)}
