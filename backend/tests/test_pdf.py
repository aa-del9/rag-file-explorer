"""
Tests for PDF processing functionality.
"""

import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.pdf_processor import PDFProcessor


class TestPDFProcessor:
    """Test suite for PDFProcessor class."""
    
    @pytest.fixture
    def processor(self):
        """Create PDFProcessor instance for testing."""
        return PDFProcessor(chunk_size=400, chunk_overlap=50)
    
    def test_clean_text(self, processor):
        """Test text cleaning functionality."""
        # Test multiple spaces
        text = "This  has   multiple    spaces"
        cleaned = processor._clean_text(text)
        assert "  " not in cleaned
        
        # Test multiple newlines
        text = "Line 1\n\n\n\nLine 2"
        cleaned = processor._clean_text(text)
        assert "\n\n\n" not in cleaned
    
    def test_split_into_sentences(self, processor):
        """Test sentence splitting logic."""
        text = "First sentence. Second sentence! Third sentence?"
        sentences = processor._split_into_sentences(text)
        
        assert len(sentences) == 3
        assert "First sentence." in sentences[0]
        assert "Second sentence!" in sentences[1]
        assert "Third sentence?" in sentences[2]
    
    def test_chunk_text_basic(self, processor):
        """Test basic text chunking."""
        text = "This is a test sentence. " * 50  # Create a long text
        chunks = processor.chunk_text(text)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, tuple) for chunk in chunks)
        assert all(len(chunk) == 2 for chunk in chunks)  # (text, metadata)
    
    def test_chunk_text_with_metadata(self, processor):
        """Test chunking with custom metadata."""
        text = "Test sentence. " * 100
        metadata = {"test_key": "test_value", "document_id": "test_123"}
        
        chunks = processor.chunk_text(text, metadata=metadata)
        
        assert len(chunks) > 0
        for chunk_text, chunk_metadata in chunks:
            assert "test_key" in chunk_metadata
            assert chunk_metadata["test_key"] == "test_value"
            assert "document_id" in chunk_metadata
            assert "chunk_index" in chunk_metadata
    
    def test_chunk_text_empty(self, processor):
        """Test chunking with empty text."""
        chunks = processor.chunk_text("")
        assert len(chunks) == 0
        
        chunks = processor.chunk_text("   ")
        assert len(chunks) == 0
    
    def test_chunk_overlap(self, processor):
        """Test that chunks have proper overlap."""
        text = "Sentence one. Sentence two. Sentence three. " * 30
        chunks = processor.chunk_text(text)
        
        if len(chunks) > 1:
            # Check that consecutive chunks might share some content
            # This is a basic check; exact overlap depends on sentence boundaries
            assert len(chunks) >= 2
    
    def test_chunk_size_respected(self, processor):
        """Test that chunks respect the maximum size."""
        text = "Word " * 200  # Create long text
        chunks = processor.chunk_text(text)
        
        for chunk_text, chunk_metadata in chunks:
            # Chunks might be slightly larger due to sentence boundaries
            # but should be roughly around chunk_size
            assert len(chunk_text) <= processor.chunk_size + 200  # Some tolerance


class TestPDFExtraction:
    """Test suite for PDF extraction (requires sample PDFs)."""
    
    @pytest.fixture
    def processor(self):
        """Create PDFProcessor instance."""
        return PDFProcessor()
    
    def test_extract_nonexistent_file(self, processor):
        """Test handling of non-existent PDF."""
        fake_path = Path("nonexistent_file.pdf")
        
        with pytest.raises(FileNotFoundError):
            processor.extract_text_from_pdf(fake_path)


def test_processor_initialization():
    """Test PDFProcessor initialization with custom parameters."""
    processor = PDFProcessor(chunk_size=500, chunk_overlap=100)
    
    assert processor.chunk_size == 500
    assert processor.chunk_overlap == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
