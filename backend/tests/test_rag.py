"""
Tests for RAG pipeline functionality.
"""

import pytest
from pathlib import Path
import sys
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.embeddings import EmbeddingModel
from app.rag_pipeline import RAGPipeline
from app.models import RetrievedChunk


class TestEmbeddingModel:
    """Test suite for EmbeddingModel class."""
    
    @pytest.fixture
    def mock_sentence_transformer(self):
        """Mock SentenceTransformer to avoid loading actual model."""
        with patch('app.embeddings.SentenceTransformer') as mock:
            mock_instance = MagicMock()
            mock_instance.get_sentence_embedding_dimension.return_value = 384
            mock_instance.encode.return_value = [0.1] * 384
            mock.return_value = mock_instance
            yield mock
    
    def test_embed_text_single(self, mock_sentence_transformer):
        """Test embedding a single text."""
        # Reset singleton
        EmbeddingModel._instance = None
        EmbeddingModel._model = None
        
        model = EmbeddingModel(model_name="test-model", device="cpu")
        
        text = "This is a test sentence"
        embedding = model.embed_text(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384
    
    def test_embed_empty_text(self, mock_sentence_transformer):
        """Test embedding empty text."""
        # Reset singleton
        EmbeddingModel._instance = None
        EmbeddingModel._model = None
        
        model = EmbeddingModel(model_name="test-model", device="cpu")
        
        embedding = model.embed_text("")
        
        assert isinstance(embedding, list)
        assert len(embedding) == 384
    
    def test_embed_batch(self, mock_sentence_transformer):
        """Test batch embedding."""
        # Reset singleton
        EmbeddingModel._instance = None
        EmbeddingModel._model = None
        
        model = EmbeddingModel(model_name="test-model", device="cpu")
        
        # Mock batch encoding
        mock_sentence_transformer.return_value.encode.return_value = [[0.1] * 384] * 3
        
        texts = ["Text 1", "Text 2", "Text 3"]
        embeddings = model.embed_text_batch(texts)
        
        assert isinstance(embeddings, list)
        assert len(embeddings) == 3
    
    def test_singleton_pattern(self, mock_sentence_transformer):
        """Test that EmbeddingModel follows singleton pattern."""
        # Reset singleton
        EmbeddingModel._instance = None
        EmbeddingModel._model = None
        
        model1 = EmbeddingModel(model_name="test-model", device="cpu")
        model2 = EmbeddingModel(model_name="test-model", device="cpu")
        
        assert model1 is model2
    
    def test_get_embedding_dimension(self, mock_sentence_transformer):
        """Test getting embedding dimension."""
        # Reset singleton
        EmbeddingModel._instance = None
        EmbeddingModel._model = None
        
        model = EmbeddingModel(model_name="test-model", device="cpu")
        
        dim = model.get_embedding_dimension()
        assert dim == 384


class TestRAGPipeline:
    """Test suite for RAGPipeline class."""
    
    @pytest.fixture
    def mock_components(self):
        """Create mock components for RAG pipeline."""
        # Mock embedding model
        mock_embedding = Mock()
        mock_embedding.embed_text.return_value = [0.1] * 384
        
        # Mock vector store
        mock_vector_store = Mock()
        mock_vector_store.query.return_value = (
            ["Chunk 1 text", "Chunk 2 text"],
            [{"document_id": "doc1", "chunk_index": 0}, {"document_id": "doc1", "chunk_index": 1}],
            [0.1, 0.2],
            ["id1", "id2"]
        )
        
        # Mock LLM client
        mock_llm = Mock()
        mock_llm.generate.return_value = "This is a test answer"
        
        return mock_embedding, mock_vector_store, mock_llm
    
    def test_get_relevant_chunks(self, mock_components):
        """Test retrieving relevant chunks."""
        mock_embedding, mock_vector_store, mock_llm = mock_components
        
        pipeline = RAGPipeline(
            embedding_model=mock_embedding,
            vector_store=mock_vector_store,
            llm_client=mock_llm,
            top_k=5
        )
        
        chunks = pipeline.get_relevant_chunks("Test query", top_k=2)
        
        assert len(chunks) == 2
        assert all(isinstance(chunk, RetrievedChunk) for chunk in chunks)
        assert chunks[0].text == "Chunk 1 text"
        assert chunks[1].text == "Chunk 2 text"
    
    def test_build_prompt_with_chunks(self, mock_components):
        """Test prompt building with context chunks."""
        mock_embedding, mock_vector_store, mock_llm = mock_components
        
        pipeline = RAGPipeline(
            embedding_model=mock_embedding,
            vector_store=mock_vector_store,
            llm_client=mock_llm
        )
        
        chunks = [
            RetrievedChunk(
                chunk_id="1",
                document_id="doc1",
                text="Context text 1",
                similarity_score=0.9
            ),
            RetrievedChunk(
                chunk_id="2",
                document_id="doc1",
                text="Context text 2",
                similarity_score=0.8
            )
        ]
        
        prompt = pipeline.build_prompt(chunks, "What is the answer?")
        
        assert "Context text 1" in prompt
        assert "Context text 2" in prompt
        assert "What is the answer?" in prompt
        assert "Context" in prompt  # Should mention context
    
    def test_build_prompt_no_chunks(self, mock_components):
        """Test prompt building without context."""
        mock_embedding, mock_vector_store, mock_llm = mock_components
        
        pipeline = RAGPipeline(
            embedding_model=mock_embedding,
            vector_store=mock_vector_store,
            llm_client=mock_llm
        )
        
        prompt = pipeline.build_prompt([], "What is the answer?")
        
        assert "What is the answer?" in prompt
        assert "Context text" not in prompt
    
    def test_generate_answer(self, mock_components):
        """Test answer generation."""
        mock_embedding, mock_vector_store, mock_llm = mock_components
        
        pipeline = RAGPipeline(
            embedding_model=mock_embedding,
            vector_store=mock_vector_store,
            llm_client=mock_llm
        )
        
        answer = pipeline.generate_answer("Test prompt")
        
        assert answer == "This is a test answer"
        mock_llm.generate.assert_called_once()
    
    def test_full_query(self, mock_components):
        """Test complete RAG query pipeline."""
        mock_embedding, mock_vector_store, mock_llm = mock_components
        
        pipeline = RAGPipeline(
            embedding_model=mock_embedding,
            vector_store=mock_vector_store,
            llm_client=mock_llm,
            top_k=5
        )
        
        answer, chunks, processing_time = pipeline.query(
            question="What is the answer?",
            top_k=2
        )
        
        assert isinstance(answer, str)
        assert len(chunks) == 2
        assert isinstance(processing_time, float)
        assert processing_time >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
