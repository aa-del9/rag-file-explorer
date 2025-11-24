"""
AI-powered metadata generation module.
Uses the existing LLM to generate summaries, keywords, and document classification.
"""

import logging
from typing import Dict, Any, List
import json

from app.llm_client import LLMClient

logger = logging.getLogger(__name__)


class AIMetadataGenerator:
    """
    Generates AI-powered metadata for documents using LLM.
    Provides summaries, keywords, and document type classification.
    """
    
    # Document type categories
    DOCUMENT_TYPES = [
        "invoice",
        "receipt",
        "contract",
        "agreement",
        "research_paper",
        "academic_paper",
        "report",
        "presentation",
        "memo",
        "letter",
        "email",
        "notes",
        "manual",
        "guide",
        "tutorial",
        "article",
        "blog_post",
        "whitepaper",
        "specification",
        "proposal",
        "resume",
        "cv",
        "form",
        "application",
        "other"
    ]
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize AI metadata generator.
        
        Args:
            llm_client: LLM client instance for generation
        """
        self.llm_client = llm_client
        logger.info("AIMetadataGenerator initialized")
    
    def generate_summary(self, text: str, max_length: int = 200) -> str:
        """
        Generate a concise summary of the document.
        
        Args:
            text: Document text
            max_length: Maximum summary length in words
            
        Returns:
            Generated summary
        """
        try:
            # Truncate text if too long (use first ~3000 chars for context)
            sample_text = text[:3000] if len(text) > 3000 else text
            
            prompt = f"""Analyze this document excerpt and provide a concise summary in {max_length} words or less.
Focus on the main topic, purpose, and key points.

Document excerpt:
{sample_text}

Provide only the summary, no preamble."""

            logger.info("Generating document summary...")
            summary = self.llm_client.generate(
                prompt=prompt,
                temperature=0.3,  # Lower temperature for more focused output
                max_tokens=300
            )
            
            # Clean up the summary
            summary = summary.strip()
            
            logger.info(f"Generated summary: {len(summary)} characters")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate summary: {str(e)}")
            return "Summary generation failed"
    
    def generate_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract key topics and keywords from the document.
        
        Args:
            text: Document text
            max_keywords: Maximum number of keywords
            
        Returns:
            List of keywords
        """
        try:
            # Use a sample of the text
            sample_text = text[:3000] if len(text) > 3000 else text
            
            prompt = f"""Extract up to {max_keywords} key topics, themes, or keywords from this document.
Return them as a comma-separated list of single words or short phrases.

Document excerpt:
{sample_text}

Keywords (comma-separated only, no numbering or explanation)"""

            logger.info("Generating keywords...")
            response = self.llm_client.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=150
            )
            
            # Parse keywords
            keywords = [
                kw.strip().lower() 
                for kw in response.split(',') 
                if kw.strip()
            ][:max_keywords]
            
            logger.info(f"Generated {len(keywords)} keywords")
            return keywords
            
        except Exception as e:
            logger.error(f"Failed to generate keywords: {str(e)}")
            return []
    
    def classify_document_type(self, text: str, filename: str = "") -> str:
        """
        Classify the document type.
        
        Args:
            text: Document text
            filename: Optional filename for additional context
            
        Returns:
            Document type classification
        """
        try:
            sample_text = text[:2000] if len(text) > 2000 else text
            
            # Build category list for prompt
            categories = ", ".join(self.DOCUMENT_TYPES)
            
            prompt = f"""Classify this document into ONE of these categories: {categories}

Filename: {filename}

Document excerpt:
{sample_text}

Return ONLY the category name, nothing else."""

            logger.info("Classifying document type...")
            doc_type = self.llm_client.generate(
                prompt=prompt,
                temperature=0.1,  # Very low temperature for consistent classification
                max_tokens=20
            )
            
            # Clean and validate the response
            doc_type = doc_type.strip().lower().replace(" ", "_")
            
            # Validate against known types
            if doc_type not in self.DOCUMENT_TYPES:
                # Try to find closest match
                for known_type in self.DOCUMENT_TYPES:
                    if known_type in doc_type or doc_type in known_type:
                        doc_type = known_type
                        break
                else:
                    doc_type = "other"
            
            logger.info(f"Document classified as: {doc_type}")
            return doc_type
            
        except Exception as e:
            logger.error(f"Failed to classify document: {str(e)}")
            return "other"
    
    def generate_all_metadata(
        self, 
        text: str, 
        filename: str = "",
        include_summary: bool = True,
        include_keywords: bool = True,
        include_classification: bool = True
    ) -> Dict[str, Any]:
        """
        Generate all AI metadata for a document.
        
        Args:
            text: Document text
            filename: Optional filename
            include_summary: Whether to generate summary
            include_keywords: Whether to generate keywords
            include_classification: Whether to classify document type
            
        Returns:
            Dictionary with AI-generated metadata
        """
        logger.info(f"Generating AI metadata for document: {filename}")
        
        metadata = {}
        
        if include_summary:
            metadata['ai_summary'] = self.generate_summary(text)
        
        if include_keywords:
            metadata['ai_keywords'] = self.generate_keywords(text)
        
        if include_classification:
            metadata['ai_document_type'] = self.classify_document_type(text, filename)
        
        logger.info("AI metadata generation complete")
        return metadata
    
    def generate_metadata_batch(
        self, 
        documents: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Generate metadata for multiple documents efficiently.
        
        Args:
            documents: List of dicts with 'text' and optional 'filename' keys
            
        Returns:
            List of metadata dictionaries
        """
        results = []
        
        for i, doc in enumerate(documents, 1):
            logger.info(f"Processing document {i}/{len(documents)}")
            
            metadata = self.generate_all_metadata(
                text=doc.get('text', ''),
                filename=doc.get('filename', '')
            )
            
            results.append(metadata)
        
        return results
