"""
Query Classifier for RAG File Explorer.
Classifies user queries as metadata-oriented, content-oriented, or hybrid.
"""

import logging
import re
from typing import Dict, List, Literal
from dataclasses import dataclass

logger = logging.getLogger(__name__)

QueryType = Literal["metadata", "content", "hybrid"]


@dataclass
class QueryClassification:
    """Result of query classification."""
    query_type: QueryType
    confidence: float
    metadata_indicators: List[str]
    content_indicators: List[str]
    extracted_filters: Dict


class QueryClassifier:
    """
    Classifies queries to route between metadata search, content search, or hybrid.
    
    Metadata queries focus on document properties:
    - "Find all invoices from 2023"
    - "Show me reports by John Doe"
    - "List all PDF files larger than 10 pages"
    
    Content queries focus on document text:
    - "What is the refund policy?"
    - "Explain machine learning algorithms"
    - "How do I reset my password?"
    
    Hybrid queries combine both:
    - "What does the 2023 Q4 report say about revenue?"
    - "Find contract terms in documents by Legal team"
    """
    
    # Metadata indicators (document properties, file attributes)
    METADATA_KEYWORDS = {
        # File properties
        "file", "files", "document", "documents", "pdf", "docx", "doc",
        
        # Document types
        "invoice", "invoices", "contract", "contracts", "report", "reports",
        "presentation", "presentations", "spreadsheet", "spreadsheets",
        "resume", "resumes", "letter", "letters", "memo", "memos",
        "manual", "manuals", "guide", "guides", "policy", "policies",
        
        # Authors and attribution
        "by", "from", "author", "authored", "created by", "written by",
        
        # Time references for metadata
        "dated", "created", "modified", "uploaded", "in", "during",
        
        # File attributes
        "page", "pages", "size", "larger", "smaller", "contains",
        
        # Listing/filtering verbs
        "list", "show", "find", "filter", "search for", "get all",
        "display", "retrieve", "fetch",
        
        # Metadata-specific queries
        "how many", "total", "count", "statistics", "stats"
    }
    
    # Content indicators (document text, semantic meaning)
    CONTENT_KEYWORDS = {
        # Question words (seeking information)
        "what", "how", "why", "when", "where", "which", "who",
        
        # Information retrieval verbs
        "explain", "describe", "tell me", "define", "summarize",
        "clarify", "elaborate", "detail",
        
        # Content references
        "says", "mentions", "discusses", "covers", "about",
        "regarding", "concerning", "related to",
        
        # Understanding/meaning
        "mean", "meaning", "understand", "interpretation"
    }
    
    # Temporal patterns for metadata filtering
    TEMPORAL_PATTERNS = [
        r'\b(20\d{2})\b',  # Year (2000-2099)
        r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b',
        r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b',
        r'\b(q[1-4]|quarter [1-4])\b',
        r'\b(last|this|next)\s+(year|month|week|quarter)\b',
    ]
    
    # Author/person patterns
    AUTHOR_PATTERNS = [
        r'\bby\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # by John Doe
        r'\bfrom\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # from Jane Smith
        r'\bauthor[ed]*\s+by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
    ]
    
    # File type patterns
    FILE_TYPE_PATTERNS = [
        r'\b(pdf|docx|doc)\s+files?\b',
        r'\b\.(pdf|docx|doc)\b',
    ]
    
    def __init__(self):
        """Initialize the query classifier."""
        # Precompile regex patterns
        self.temporal_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.TEMPORAL_PATTERNS]
        self.author_regex = [re.compile(pattern) for pattern in self.AUTHOR_PATTERNS]
        self.file_type_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.FILE_TYPE_PATTERNS]
    
    def classify(self, query: str) -> QueryClassification:
        """
        Classify a query as metadata, content, or hybrid.
        
        Args:
            query: User query string
            
        Returns:
            QueryClassification with type, confidence, and indicators
        """
        query_lower = query.lower()
        
        # Find indicators
        metadata_indicators = self._find_metadata_indicators(query_lower)
        content_indicators = self._find_content_indicators(query_lower)
        
        # Extract potential filters
        extracted_filters = self._extract_filters(query)
        
        # Calculate scores
        metadata_score = len(metadata_indicators) + (len(extracted_filters) * 2)
        content_score = len(content_indicators)
        
        # Determine query type
        if metadata_score == 0 and content_score == 0:
            # No clear indicators - default to content search
            query_type = "content"
            confidence = 0.3
        elif metadata_score > 0 and content_score == 0:
            # Pure metadata query
            query_type = "metadata"
            confidence = min(0.9, 0.5 + (metadata_score * 0.1))
        elif content_score > 0 and metadata_score == 0:
            # Pure content query
            query_type = "content"
            confidence = min(0.9, 0.5 + (content_score * 0.1))
        else:
            # Hybrid query
            query_type = "hybrid"
            confidence = min(0.9, 0.6 + ((metadata_score + content_score) * 0.05))
        
        logger.info(
            f"Query classified as {query_type} "
            f"(confidence: {confidence:.2f}, "
            f"metadata_score: {metadata_score}, "
            f"content_score: {content_score})"
        )
        
        return QueryClassification(
            query_type=query_type,
            confidence=confidence,
            metadata_indicators=metadata_indicators,
            content_indicators=content_indicators,
            extracted_filters=extracted_filters
        )
    
    def _find_metadata_indicators(self, query_lower: str) -> List[str]:
        """Find metadata keywords in query."""
        indicators = []
        for keyword in self.METADATA_KEYWORDS:
            if keyword in query_lower:
                indicators.append(keyword)
        return indicators
    
    def _find_content_indicators(self, query_lower: str) -> List[str]:
        """Find content keywords in query."""
        indicators = []
        for keyword in self.CONTENT_KEYWORDS:
            if keyword in query_lower:
                indicators.append(keyword)
        return indicators
    
    def _extract_filters(self, query: str) -> Dict:
        """
        Extract potential metadata filters from query.
        
        Returns:
            Dictionary with possible filter values:
            - years: List of year values
            - authors: List of author names
            - file_types: List of file extensions
            - months: List of month names
        """
        filters = {
            "years": [],
            "authors": [],
            "file_types": [],
            "months": [],
            "quarters": []
        }
        
        # Extract years
        for regex in self.temporal_regex:
            matches = regex.findall(query)
            if regex.pattern == r'\b(20\d{2})\b':
                filters["years"].extend(matches)
            elif "january|february" in regex.pattern.lower() or "jan|feb" in regex.pattern.lower():
                filters["months"].extend(matches)
            elif "q[1-4]" in regex.pattern.lower():
                filters["quarters"].extend(matches)
        
        # Extract authors
        for regex in self.author_regex:
            matches = regex.findall(query)
            filters["authors"].extend(matches)
        
        # Extract file types
        for regex in self.file_type_regex:
            matches = regex.findall(query)
            filters["file_types"].extend([m.lower().replace(".", "") for m in matches])
        
        # Remove duplicates
        for key in filters:
            filters[key] = list(set(filters[key]))
        
        return filters
    
    def is_metadata_query(self, query: str) -> bool:
        """
        Quick check if query is primarily metadata-focused.
        
        Args:
            query: User query string
            
        Returns:
            True if query is metadata-focused
        """
        classification = self.classify(query)
        return classification.query_type in ("metadata", "hybrid")
    
    def is_content_query(self, query: str) -> bool:
        """
        Quick check if query is primarily content-focused.
        
        Args:
            query: User query string
            
        Returns:
            True if query is content-focused
        """
        classification = self.classify(query)
        return classification.query_type in ("content", "hybrid")


# Example usage
if __name__ == "__main__":
    classifier = QueryClassifier()
    
    test_queries = [
        "Find all invoices from 2023",
        "What is the company's refund policy?",
        "Show me reports by John Doe about machine learning",
        "List all PDF files larger than 10 pages",
        "Explain the concept of neural networks",
        "What does the Q4 2023 financial report say about revenue growth?"
    ]
    
    for query in test_queries:
        result = classifier.classify(query)
        print(f"\nQuery: {query}")
        print(f"Type: {result.query_type} (confidence: {result.confidence:.2f})")
        print(f"Metadata indicators: {result.metadata_indicators}")
        print(f"Content indicators: {result.content_indicators}")
        print(f"Extracted filters: {result.extracted_filters}")
