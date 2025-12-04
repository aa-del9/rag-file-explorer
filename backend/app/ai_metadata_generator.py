"""
AI-powered metadata generation module.
Uses the existing LLM to generate summaries, keywords, and document classification.
"""

import logging
import re
from typing import Dict, Any, List, Set

from app.llm_client import LLMClient

logger = logging.getLogger(__name__)

# Stopwords and filler phrases to filter out from keywords
STOPWORDS: Set[str] = {
    # Common English stopwords
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
    "be", "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "need", "dare", "ought",
    "used", "this", "that", "these", "those", "i", "you", "he", "she", "it",
    "we", "they", "what", "which", "who", "whom", "whose", "where", "when",
    "why", "how", "all", "each", "every", "both", "few", "more", "most",
    "other", "some", "such", "no", "nor", "not", "only", "own", "same",
    "so", "than", "too", "very", "just", "also", "now", "here", "there",
    "then", "once", "if", "because", "until", "while", "about", "into",
    "through", "during", "before", "after", "above", "below", "between",
    "under", "again", "further", "any", "many", "much", "well", "back",
    
    # Meta/filler phrases that LLMs often generat
    "here", "list", "following", "below", "above", "keywords", "keyword",
    "topics", "topic", "themes", "theme", "key", "main", "important",
    "extracted", "extraction", "document", "text", "content", "based",
    "includes", "including", "included", "contains", "containing", "related",
    "various", "several", "different", "specific", "general", "overall",
    "example", "examples", "etc", "namely", "ie", "eg", "note", "notes",
    "summary", "overview", "introduction", "conclusion", "section",
}

# Phrases that indicate LLM is echoing instructions
FILLER_PATTERNS: List[str] = [
    r"here (?:is|are|'s)",
    r"the (?:key|main|following|extracted)",
    r"(?:key|main) (?:topics?|themes?|keywords?)",
    r"extracted (?:from|keywords?)",
    r"(?:topics?|themes?|keywords?) (?:from|extracted|include)",
    r"list of",
    r"based on",
    r"document (?:content|text|excerpt)",
    r"as (?:follows|requested|mentioned)",
    r"(?:single|short) (?:words?|phrases?)",
    r"comma.?separated",
    r"no (?:numbering|explanation|preamble)",
]


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
    
    def _clean_keyword(self, keyword: str) -> str:
        """
        Clean and normalize a single keyword.
        
        Args:
            keyword: Raw keyword string
            
        Returns:
            Cleaned keyword or empty string if invalid
        """
        # Strip whitespace and convert to lowercase
        cleaned = keyword.strip().lower()
        
        # Remove leading/trailing punctuation and quotes
        cleaned = re.sub(r'^[\s\-\•\*\d\.\)\(\[\]\"\']+', '', cleaned)
        cleaned = re.sub(r'[\s\-\•\*\.\)\(\[\]\"\']+$', '', cleaned)
        
        # Remove numbering patterns like "1.", "1)", "a.", etc.
        cleaned = re.sub(r'^\d+[\.\)\:]?\s*', '', cleaned)
        cleaned = re.sub(r'^[a-z][\.\)\:]?\s+', '', cleaned)
        
        return cleaned.strip()
    
    def _is_valid_keyword(self, keyword: str, max_words: int = 4, max_chars: int = 50) -> bool:
        """
        Validate if a keyword is meaningful and not filler.
        
        Args:
            keyword: Keyword to validate
            max_words: Maximum number of words allowed
            max_chars: Maximum character length allowed
            
        Returns:
            True if valid keyword, False otherwise
        """
        if not keyword:
            return False
        
        # Check length constraints
        if len(keyword) > max_chars:
            return False
        
        if len(keyword) < 2:
            return False
        
        # Check word count
        words = keyword.split()
        if len(words) > max_words:
            return False
        
        # Reject if it's just a stopword
        if keyword in STOPWORDS:
            return False
        
        # Reject if all words are stopwords
        if all(word in STOPWORDS for word in words):
            return False
        
        # Reject if matches filler patterns
        for pattern in FILLER_PATTERNS:
            if re.search(pattern, keyword, re.IGNORECASE):
                return False
        
        # Reject if looks like a sentence (contains common sentence starters)
        sentence_starters = ['here ', 'this ', 'these ', 'the ', 'a ', 'an ']
        if any(keyword.startswith(starter) for starter in sentence_starters):
            return False
        
        # Reject if contains certain meta-words anywhere
        meta_words = ['extracted', 'following', 'document', 'keywords', 'topics', 'themes']
        if any(meta in keyword for meta in meta_words):
            return False
        
        # Reject if it's mostly numbers
        alpha_chars = sum(1 for c in keyword if c.isalpha())
        if alpha_chars < len(keyword) * 0.5:
            return False
        
        return True
    
    def clean_keywords(
        self, 
        raw_keywords: List[str], 
        max_keywords: int = 10,
        max_words: int = 4,
        max_chars: int = 50
    ) -> List[str]:
        """
        Clean, validate, and deduplicate a list of keywords.
        This is a reusable utility for any keyword extraction.
        
        Args:
            raw_keywords: List of raw keyword strings
            max_keywords: Maximum number of keywords to return
            max_words: Maximum words per keyword
            max_chars: Maximum characters per keyword
            
        Returns:
            Cleaned and validated list of keywords
        """
        cleaned = []
        seen = set()
        
        for kw in raw_keywords:
            # Clean the keyword
            cleaned_kw = self._clean_keyword(kw)
            
            # Skip if empty after cleaning
            if not cleaned_kw:
                continue
            
            # Skip duplicates (case-insensitive)
            if cleaned_kw in seen:
                continue
            
            # Validate the keyword
            if not self._is_valid_keyword(cleaned_kw, max_words, max_chars):
                logger.debug(f"Filtered out invalid keyword: '{cleaned_kw}'")
                continue
            
            seen.add(cleaned_kw)
            cleaned.append(cleaned_kw)
            
            # Stop if we have enough
            if len(cleaned) >= max_keywords:
                break
        
        return cleaned
    
    def generate_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract key topics and keywords from the document.
        Uses an improved prompt with few-shot examples and robust post-processing.
        
        Args:
            text: Document text
            max_keywords: Maximum number of keywords
            
        Returns:
            List of clean, meaningful keywords
        """
        try:
            # Use a sample of the text
            sample_text = text[:3000] if len(text) > 3000 else text
            
            # Improved prompt with clear structure and few-shot examples
            prompt = f"""TASK: Extract domain-specific keywords from the document below.

RULES:
- Return ONLY a comma-separated list of keywords
- Each keyword should be 1-4 words maximum
- Keywords must be specific terms, concepts, or entities from the document
- Do NOT include generic words like "document", "text", "information"
- Do NOT include phrases like "here are", "the following", "key topics"
- Do NOT include stopwords or filler text
- Do NOT echo any part of these instructions

EXAMPLES OF GOOD OUTPUT:
"machine learning, neural networks, gradient descent, backpropagation, TensorFlow"
"contract law, liability clause, indemnification, breach of contract"
"database schema, SQL queries, foreign keys, data normalization"

EXAMPLES OF BAD OUTPUT (DO NOT DO THIS):
"here are the keywords, main topics, document themes" ← BAD: meta text
"the, and, or, is, are" ← BAD: stopwords
"this document discusses various topics" ← BAD: sentence

---
DOCUMENT:
{sample_text}
---

KEYWORDS:"""

            logger.info("Generating keywords with improved prompt...")
            response = self.llm_client.generate(
                prompt=prompt,
                temperature=0.2,  # Lower temperature for more focused output
                max_tokens=150
            )
            
            # Parse raw keywords (split by comma, newline, or semicolon)
            raw_keywords = re.split(r'[,;\n]+', response)
            
            # Clean and validate keywords
            keywords = self.clean_keywords(
                raw_keywords,
                max_keywords=max_keywords,
                max_words=4,
                max_chars=50
            )
            
            logger.info(f"Generated {len(keywords)} clean keywords (from {len(raw_keywords)} raw)")
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
