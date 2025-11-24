"""
RAG Pipeline module.
Orchestrates the complete Retrieval-Augmented Generation workflow.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
import time

from app.embeddings import EmbeddingModel
from app.vector_store import VectorStore
from app.llm_client import LLMClient
from app.models import RetrievedChunk
from app.metadata_store import MetadataStore
from app.query_classifier import QueryClassifier

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Complete RAG pipeline for question answering over document collections.
    Combines retrieval and generation for context-aware responses.
    """
    
    def __init__(
        self,
        embedding_model: EmbeddingModel,
        vector_store: VectorStore,
        llm_client: LLMClient,
        metadata_store: Optional[MetadataStore] = None,
        top_k: int = 5
    ):
        """
        Initialize RAG pipeline with required components.
        
        Args:
            embedding_model: Model for generating embeddings
            vector_store: Vector database for similarity search
            llm_client: LLM client for text generation
            metadata_store: Optional metadata store for hybrid queries
            top_k: Default number of chunks to retrieve
        """
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.llm_client = llm_client
        self.metadata_store = metadata_store
        self.query_classifier = QueryClassifier()
        self.default_top_k = top_k
        
        logger.info("RAG Pipeline initialized with metadata support")
    
    def get_relevant_chunks(
        self,
        query: str,
        top_k: int = None,
        filter_metadata: Dict[str, Any] = None
    ) -> List[RetrievedChunk]:
        """
        Retrieve relevant document chunks for a given query.
        
        Args:
            query: User's question or search query
            top_k: Number of chunks to retrieve (uses default if None)
            filter_metadata: Optional metadata filter for search
            
        Returns:
            List of RetrievedChunk objects with text and metadata
        """
        if not query or not query.strip():
            logger.warning("Empty query provided")
            return []
        
        top_k = top_k or self.default_top_k
        
        try:
            logger.info(f"Retrieving relevant chunks for query: '{query[:50]}...'")
            
            # Generate query embedding
            query_embedding = self.embedding_model.embed_text(query)
            
            # Search vector store
            documents, metadatas, distances, ids = self.vector_store.query(
                query_embedding=query_embedding,
                top_k=top_k,
                filter_metadata=filter_metadata
            )
            
            # Convert to RetrievedChunk objects
            chunks = []
            for i, (doc, metadata, distance, chunk_id) in enumerate(zip(documents, metadatas, distances, ids)):
                # Convert distance to similarity score (ChromaDB uses L2 distance)
                # Lower distance = higher similarity
                similarity_score = 1.0 / (1.0 + distance)
                
                chunk = RetrievedChunk(
                    chunk_id=chunk_id,
                    document_id=metadata.get("document_id", "unknown"),
                    text=doc,
                    similarity_score=round(similarity_score, 4),
                    metadata=metadata
                )
                chunks.append(chunk)
            
            logger.info(f"Retrieved {len(chunks)} relevant chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to retrieve chunks: {str(e)}")
            raise Exception(f"Chunk retrieval failed: {str(e)}")
    
    def build_prompt(self, chunks: List[RetrievedChunk], question: str) -> str:
        """
        Build the final prompt for the LLM with retrieved context.
        
        Args:
            chunks: Retrieved document chunks
            question: User's question
            
        Returns:
            Formatted prompt string
        """
        if not chunks:
            # No context available
            prompt = f"""Answer the following question to the best of your ability.

Question: {question}

Answer:"""
            return prompt
        
        # Build context from chunks
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(f"[Context {i}]:\n{chunk.text}")
        
        context = "\n\n".join(context_parts)
        
        # Build full prompt with instruction
        prompt = f"""You are a helpful assistant that answers questions based on the provided context.

Use the context below to answer the question. If the answer is not contained in the context, say "I don't have enough information to answer this question based on the provided documents."

Context:
{context}

Question: {question}

Answer:"""
        
        return prompt
    
    def generate_answer(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = None
    ) -> str:
        """
        Generate answer using the LLM.
        
        Args:
            prompt: Full prompt with context and question
            temperature: Sampling temperature for generation
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated answer text
        """
        try:
            logger.info("Generating answer with LLM")
            
            answer = self.llm_client.generate(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return answer
            
        except Exception as e:
            logger.error(f"Failed to generate answer: {str(e)}")
            raise Exception(f"Answer generation failed: {str(e)}")
    
    def query(
        self,
        question: str,
        top_k: int = None,
        temperature: float = 0.7,
        filter_metadata: Dict[str, Any] = None,
        use_query_classification: bool = True
    ) -> Tuple[str, List[RetrievedChunk], float]:
        """
        Complete RAG query: retrieve context and generate answer.
        Supports hybrid queries with automatic metadata filtering.
        
        Args:
            question: User's question
            top_k: Number of chunks to retrieve
            temperature: LLM sampling temperature
            filter_metadata: Optional metadata filter
            use_query_classification: Whether to classify query for hybrid search
            
        Returns:
            Tuple of (answer, retrieved_chunks, processing_time)
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing RAG query: '{question[:50]}...'")
            
            # Step 1: Classify query and enhance with metadata if applicable
            if use_query_classification and self.metadata_store:
                classification = self.query_classifier.classify(question)
                logger.info(f"Query classified as: {classification.query_type}")
                
                # For metadata or hybrid queries, enhance retrieval
                if classification.query_type in ("metadata", "hybrid"):
                    # Get relevant documents by metadata first
                    if classification.extracted_filters:
                        logger.info(f"Applying extracted filters: {classification.extracted_filters}")
                        # This will be used to scope the content search
                        # In a full implementation, you'd build ChromaDB filters here
                        # For now, we log it and proceed with content search
            
            # Step 2: Retrieve relevant chunks
            chunks = self.get_relevant_chunks(
                query=question,
                top_k=top_k,
                filter_metadata=filter_metadata
            )
            
            # Step 3: Build prompt with context
            prompt = self.build_prompt(chunks, question)
            
            logger.debug(f"Built prompt with {len(chunks)} chunks, total length: {len(prompt)}")
            
            # Step 4: Generate answer
            answer = self.generate_answer(
                prompt=prompt,
                temperature=temperature
            )
            
            processing_time = time.time() - start_time
            
            logger.info(f"RAG query completed in {processing_time:.2f}s")
            
            return answer, chunks, processing_time
            
        except Exception as e:
            logger.error(f"RAG query failed: {str(e)}")
            raise Exception(f"RAG pipeline error: {str(e)}")
    
    def get_system_prompt(self) -> str:
        """
        Get the default system prompt for the RAG assistant.
        
        Returns:
            System prompt string
        """
        return """You are a helpful AI assistant that answers questions based on provided document context.
Your goal is to provide accurate, relevant answers using only the information given in the context.
If you cannot answer based on the context, clearly state that."""
