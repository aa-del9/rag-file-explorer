"""
Embeddings module.
Handles text embedding generation using sentence-transformers.
"""

import logging
from typing import List, Union
from sentence_transformers import SentenceTransformer
import torch

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """
    Manages text embedding generation using sentence-transformers.
    Implements singleton pattern to load model only once.
    """
    
    _instance = None
    _model = None
    
    def __new__(cls, model_name: str = "all-MiniLM-L6-v2", device: str = "cpu"):
        """
        Singleton pattern to ensure only one model instance exists.
        
        Args:
            model_name: Name of the sentence-transformer model
            device: Device to run model on ("cpu" or "cuda")
        """
        if cls._instance is None:
            cls._instance = super(EmbeddingModel, cls).__new__(cls)
            cls._instance._initialize(model_name, device)
        return cls._instance
    
    def _initialize(self, model_name: str, device: str):
        """
        Initialize the embedding model.
        
        Args:
            model_name: Name of the sentence-transformer model
            device: Device to run model on
        """
        self.model_name = model_name
        self.device = device
        
        try:
            logger.info(f"Loading embedding model: {model_name} on device: {device}")
            
            # Check if CUDA is available if requested
            if device == "cuda" and not torch.cuda.is_available():
                logger.warning("CUDA requested but not available, falling back to CPU")
                self.device = "cpu"
            
            # Load the model
            self._model = SentenceTransformer(model_name, device=self.device)
            
            # Get embedding dimension
            self.embedding_dim = self._model.get_sentence_embedding_dimension()
            
            logger.info(f"Embedding model loaded successfully. Dimension: {self.embedding_dim}")
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            raise Exception(f"Embedding model initialization failed: {str(e)}")
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text string.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            logger.warning("Attempted to embed empty text")
            return [0.0] * self.embedding_dim
        
        try:
            # Generate embedding
            embedding = self._model.encode(
                text,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise Exception(f"Embedding generation failed: {str(e)}")
    
    def embed_text_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently in batches.
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process at once
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            logger.warning("Attempted to embed empty text list")
            return []
        
        # Filter out empty strings
        valid_texts = [text if text.strip() else " " for text in texts]
        
        try:
            logger.info(f"Generating embeddings for {len(valid_texts)} texts")
            
            # Generate embeddings in batch
            embeddings = self._model.encode(
                valid_texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=len(valid_texts) > 100  # Show progress for large batches
            )
            
            logger.info(f"Successfully generated {len(embeddings)} embeddings")
            
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {str(e)}")
            raise Exception(f"Batch embedding generation failed: {str(e)}")
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embedding vectors.
        
        Returns:
            Embedding dimension
        """
        return self.embedding_dim
    
    def is_loaded(self) -> bool:
        """
        Check if the model is loaded and ready.
        
        Returns:
            True if model is loaded, False otherwise
        """
        return self._model is not None


# Module-level function for easy access
def get_embedding_model(model_name: str = "all-MiniLM-L6-v2", device: str = "cpu") -> EmbeddingModel:
    """
    Get or create the embedding model instance.
    
    Args:
        model_name: Name of the sentence-transformer model
        device: Device to run model on
        
    Returns:
        EmbeddingModel instance
    """
    return EmbeddingModel(model_name, device)
