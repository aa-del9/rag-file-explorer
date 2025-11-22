"""
PDF processing module.
Handles PDF text extraction and text chunking for RAG pipeline.
"""

import logging
from pathlib import Path
from typing import List, Tuple
from pypdf import PdfReader
import re

logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    Handles PDF document processing including text extraction and chunking.
    """
    
    def __init__(self, chunk_size: int = 400, chunk_overlap: int = 50):
        """
        Initialize PDF processor.
        
        Args:
            chunk_size: Target size for text chunks (in characters)
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        logger.info(f"PDFProcessor initialized with chunk_size={chunk_size}, overlap={chunk_overlap}")
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """
        Extract all text content from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as a single string
            
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            Exception: If PDF reading fails
        """
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        try:
            logger.info(f"Extracting text from PDF: {pdf_path.name}")
            reader = PdfReader(str(pdf_path))
            
            text_parts = []
            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
                    logger.debug(f"Extracted {len(page_text)} chars from page {page_num}")
            
            full_text = "\n\n".join(text_parts)
            logger.info(f"Successfully extracted {len(full_text)} characters from {len(reader.pages)} pages")
            
            # Clean up the text
            full_text = self._clean_text(full_text)
            
            return full_text
            
        except Exception as e:
            logger.error(f"Failed to extract text from PDF {pdf_path}: {str(e)}")
            raise Exception(f"PDF extraction failed: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text by removing excessive whitespace and special characters.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        
        # Replace multiple newlines with double newline
        text = re.sub(r'\n\n+', '\n\n', text)
        
        # Remove special characters that might cause issues
        text = text.replace('\x00', '')
        
        return text.strip()
    
    def chunk_text(self, text: str, metadata: dict = None) -> List[Tuple[str, dict]]:
        """
        Split text into overlapping chunks for embedding.
        
        Args:
            text: Full text to be chunked
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of tuples containing (chunk_text, chunk_metadata)
        """
        if not text or not text.strip():
            logger.warning("Attempted to chunk empty text")
            return []
        
        metadata = metadata or {}
        chunks = []
        
        # Split by sentences to avoid breaking mid-sentence
        sentences = self._split_into_sentences(text)
        
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # If adding this sentence exceeds chunk size and we have content, save chunk
            if current_length + sentence_length > self.chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunk_metadata = {
                    **metadata,
                    "chunk_length": len(chunk_text),
                    "chunk_index": len(chunks)
                }
                chunks.append((chunk_text, chunk_metadata))
                
                # Keep last few sentences for overlap
                overlap_text = " ".join(current_chunk)
                overlap_length = len(overlap_text)
                
                # Remove sentences from start until we're within overlap size
                while overlap_length > self.chunk_overlap and current_chunk:
                    removed = current_chunk.pop(0)
                    overlap_length -= len(removed) + 1  # +1 for space
                
                current_length = overlap_length
            
            current_chunk.append(sentence)
            current_length += sentence_length + 1  # +1 for space between sentences
        
        # Add the last chunk if there's remaining content
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunk_metadata = {
                **metadata,
                "chunk_length": len(chunk_text),
                "chunk_index": len(chunks)
            }
            chunks.append((chunk_text, chunk_metadata))
        
        logger.info(f"Created {len(chunks)} chunks from {len(text)} characters")
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using basic sentence boundary detection.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Simple sentence splitter - splits on .!? followed by space or newline
        sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])'
        sentences = re.split(sentence_pattern, text)
        
        # Filter out empty sentences and strip whitespace
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def process_pdf(self, pdf_path: Path, document_id: str) -> List[Tuple[str, dict]]:
        """
        Complete PDF processing pipeline: extract text and create chunks.
        
        Args:
            pdf_path: Path to PDF file
            document_id: Unique identifier for the document
            
        Returns:
            List of (chunk_text, metadata) tuples ready for embedding
        """
        logger.info(f"Processing PDF: {pdf_path.name} (ID: {document_id})")
        
        # Extract text
        text = self.extract_text_from_pdf(pdf_path)
        
        # Create metadata for all chunks
        base_metadata = {
            "document_id": document_id,
            "filename": pdf_path.name,
            "total_length": len(text)
        }
        
        # Chunk the text
        chunks = self.chunk_text(text, metadata=base_metadata)
        
        logger.info(f"PDF processing complete: {len(chunks)} chunks created")
        return chunks
