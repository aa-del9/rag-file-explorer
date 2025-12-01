"""
Summary cache service module.
Provides caching for LLM-generated document summaries to avoid repeated calls.
"""

import logging
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class SummaryCache:
    """
    Persistent cache for document summaries.
    Stores summaries in a JSON file to avoid repeated LLM calls.
    """
    
    def __init__(self, cache_dir: Path):
        """
        Initialize summary cache.
        
        Args:
            cache_dir: Directory to store cache file
        """
        self.cache_dir = cache_dir
        self.cache_file = cache_dir / "summary_cache.json"
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        # Load existing cache
        self._load_cache()
        
        logger.info(f"SummaryCache initialized with {len(self._cache)} entries")
    
    def _load_cache(self):
        """Load cache from disk."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
                logger.info(f"Loaded {len(self._cache)} cached summaries")
        except Exception as e:
            logger.warning(f"Failed to load summary cache: {str(e)}")
            self._cache = {}
    
    def _save_cache(self):
        """Save cache to disk."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save summary cache: {str(e)}")
    
    def get(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached summary for a document.
        
        Args:
            document_id: Document identifier
            
        Returns:
            Cached summary data or None
        """
        return self._cache.get(document_id)
    
    def set(
        self,
        document_id: str,
        summary: str,
        key_topics: Optional[List[str]] = None,
        metadata_summary: Optional[Dict[str, Any]] = None
    ):
        """
        Cache a document summary.
        
        Args:
            document_id: Document identifier
            summary: Generated summary text
            key_topics: Optional list of key topics
            metadata_summary: Optional metadata summary dict
        """
        self._cache[document_id] = {
            'summary': summary,
            'key_topics': key_topics or [],
            'metadata_summary': metadata_summary or {},
            'generated_at': datetime.now().isoformat(),
            'cache_version': '1.0'
        }
        self._save_cache()
        logger.info(f"Cached summary for document: {document_id}")
    
    def invalidate(self, document_id: str) -> bool:
        """
        Invalidate cached summary for a document.
        
        Args:
            document_id: Document identifier
            
        Returns:
            True if entry was found and removed
        """
        if document_id in self._cache:
            del self._cache[document_id]
            self._save_cache()
            logger.info(f"Invalidated cache for document: {document_id}")
            return True
        return False
    
    def clear(self):
        """Clear all cached summaries."""
        self._cache = {}
        self._save_cache()
        logger.info("Summary cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'total_entries': len(self._cache),
            'cache_file': str(self.cache_file),
            'cache_size_kb': self.cache_file.stat().st_size / 1024 if self.cache_file.exists() else 0
        }


class SmartSummaryGenerator:
    """
    Generates intelligent summaries combining content and metadata.
    Uses LLM for summary generation with caching.
    """
    
    def __init__(self, llm_client, cache: SummaryCache):
        """
        Initialize summary generator.
        
        Args:
            llm_client: LLM client for generation
            cache: Summary cache instance
        """
        self.llm_client = llm_client
        self.cache = cache
        
        logger.info("SmartSummaryGenerator initialized")
    
    def generate_smart_summary(
        self,
        document_id: str,
        filename: str,
        content_preview: str,
        metadata: Dict[str, Any],
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a smart summary combining content and metadata.
        
        Args:
            document_id: Document identifier
            filename: Document filename
            content_preview: Preview of document content
            metadata: Document metadata
            force_regenerate: Force regeneration even if cached
            
        Returns:
            Summary result dict
        """
        # Check cache first
        if not force_regenerate:
            cached = self.cache.get(document_id)
            if cached:
                logger.info(f"Returning cached summary for: {document_id}")
                return {
                    'summary': cached['summary'],
                    'key_topics': cached['key_topics'],
                    'metadata_summary': cached['metadata_summary'],
                    'cached': True,
                    'generated_at': cached['generated_at']
                }
        
        # Build prompt for LLM
        prompt = self._build_summary_prompt(filename, content_preview, metadata)
        
        try:
            # Generate summary using LLM
            response = self.llm_client.generate(
                prompt=prompt,
                temperature=0.3,  # Lower temperature for factual summary
                max_tokens=500
            )
            
            # Parse response
            summary, key_topics = self._parse_summary_response(response)
            
            # Build metadata summary
            metadata_summary = self._build_metadata_summary(metadata)
            
            # Cache the result
            self.cache.set(
                document_id=document_id,
                summary=summary,
                key_topics=key_topics,
                metadata_summary=metadata_summary
            )
            
            return {
                'summary': summary,
                'key_topics': key_topics,
                'metadata_summary': metadata_summary,
                'cached': False,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate summary: {str(e)}")
            # Return basic summary on failure
            return {
                'summary': f"Document: {filename}. {metadata.get('ai_summary', 'Summary not available.')}",
                'key_topics': [],
                'metadata_summary': self._build_metadata_summary(metadata),
                'cached': False,
                'generated_at': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def _build_summary_prompt(
        self,
        filename: str,
        content_preview: str,
        metadata: Dict[str, Any]
    ) -> str:
        """Build the prompt for summary generation."""
        # Truncate content preview if too long
        if len(content_preview) > 3000:
            content_preview = content_preview[:3000] + "..."
        
        prompt = f"""Generate a comprehensive yet concise summary of this document.

Document Information:
- Filename: {filename}
- File Type: {metadata.get('file_type', 'unknown')}
- Page Count: {metadata.get('page_count', 'N/A')}
- Author: {metadata.get('author', 'Unknown')}
- Title: {metadata.get('title', 'Untitled')}
- Document Type: {metadata.get('ai_document_type', 'Unknown')}
- Existing Keywords: {metadata.get('ai_keywords', 'None')}

Content Preview:
{content_preview}

Please provide:
1. A clear, 2-3 sentence summary of what this document is about
2. 3-5 key topics or themes covered in the document

Format your response as:
SUMMARY: [Your summary here]
KEY_TOPICS: [topic1], [topic2], [topic3], ...
"""
        return prompt
    
    def _parse_summary_response(self, response: str) -> tuple:
        """Parse LLM response into summary and topics."""
        summary = response
        key_topics = []
        
        try:
            lines = response.strip().split('\n')
            for line in lines:
                if line.upper().startswith('SUMMARY:'):
                    summary = line[8:].strip()
                elif line.upper().startswith('KEY_TOPICS:') or line.upper().startswith('KEY TOPICS:'):
                    topics_str = line.split(':', 1)[1].strip()
                    key_topics = [t.strip().strip('[]') for t in topics_str.split(',')]
            
            # If no structured response, use whole response as summary
            if summary == response and 'SUMMARY:' not in response.upper():
                # Just use first 300 chars as summary
                summary = response[:300] + "..." if len(response) > 300 else response
                
        except Exception as e:
            logger.warning(f"Failed to parse summary response: {str(e)}")
        
        return summary, key_topics
    
    def _build_metadata_summary(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Build a structured metadata summary."""
        return {
            'file_info': {
                'type': metadata.get('file_type', 'unknown'),
                'size_mb': metadata.get('file_size_mb', 0),
                'page_count': metadata.get('page_count')
            },
            'dates': {
                'created': metadata.get('created_at', ''),
                'modified': metadata.get('modified_at', '')
            },
            'authorship': {
                'title': metadata.get('title'),
                'author': metadata.get('author')
            },
            'classification': {
                'document_type': metadata.get('ai_document_type'),
                'keywords': metadata.get('ai_keywords')
            }
        }
