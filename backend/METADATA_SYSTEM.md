# Metadata-Aware File Explorer System

## Overview

The RAG File Explorer has been extended with a comprehensive metadata layer that enables intelligent document discovery and hybrid search capabilities. The system now supports:

1. **Document-level metadata extraction** - File properties, PDF/DOCX metadata
2. **AI-generated metadata** - Summaries, keywords, document classification
3. **Metadata storage** - Separate ChromaDB collection with semantic search
4. **Metadata search API** - Filter-based and semantic document discovery
5. **Query classification** - Automatic routing between metadata/content/hybrid queries
6. **Hybrid RAG** - Combined metadata filtering and content retrieval

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    Upload    │  │     Chat     │  │   Metadata   │      │
│  │    Router    │  │    Router    │  │    Router    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │               │
├─────────┼──────────────────┼──────────────────┼──────────────┤
│         │                  │                  │               │
│  ┌──────▼───────┐   ┌─────▼──────┐   ┌──────▼───────┐      │
│  │  Document    │   │    RAG     │   │   Metadata   │      │
│  │  Processor   │   │  Pipeline  │   │    Store     │      │
│  └──────┬───────┘   └─────┬──────┘   └──────┬───────┘      │
│         │                  │                  │               │
│  ┌──────▼───────┐   ┌─────▼──────┐   ┌──────▼───────┐      │
│  │  Metadata    │   │   Query    │   │ AI Metadata  │      │
│  │  Extractor   │   │ Classifier │   │  Generator   │      │
│  └──────────────┘   └────────────┘   └──────────────┘      │
│                                                               │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐    │
│  │   Vector     │   │   Metadata   │   │  Embedding   │    │
│  │    Store     │   │    Store     │   │    Model     │    │
│  │  (ChromaDB)  │   │  (ChromaDB)  │   │  (MiniLM)    │    │
│  └──────────────┘   └──────────────┘   └──────────────┘    │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### Data Flow

#### Document Upload with Metadata

```
1. User uploads document (PDF/DOC/DOCX)
2. DocumentProcessor extracts text and chunks
3. MetadataExtractor extracts file system + document metadata
4. AIMetadataGenerator creates summary, keywords, classification
5. Embeddings generated for chunks and summary
6. Chunks stored in vector_store
7. Metadata stored in metadata_store
```

#### Query Processing

```
1. User submits query
2. QueryClassifier analyzes query type
3a. Metadata query → metadata_store search
3b. Content query → vector_store search
3c. Hybrid query → both stores with combination
4. RAGPipeline retrieves context
5. LLM generates answer
6. Response returned with sources
```

## Metadata Extraction

### File System Metadata

Extracted for all document types:

- `filename` - Original filename
- `file_path` - Absolute path to stored file
- `file_size_bytes` - File size in bytes
- `file_type` - Extension (.pdf, .docx, .doc)
- `created_at` - File creation timestamp
- `modified_at` - Last modification timestamp
- `uploaded_at` - Upload timestamp

### PDF-Specific Metadata

Extracted from PDF XMP metadata and info dictionary:

- `page_count` - Number of pages
- `title` - Document title
- `author` - Author name
- `subject` - Document subject
- `keywords` - Document keywords
- `creator` - Application that created the PDF
- `producer` - PDF producer software

### DOCX-Specific Metadata

Extracted from DOCX core properties:

- `title` - Document title
- `author` - Author name
- `subject` - Document subject
- `keywords` - Document keywords
- `created` - Creation date
- `modified` - Last modification date
- `last_modified_by` - Last editor

### AI-Generated Metadata

Generated using Llama 3.1 LLM:

- `summary` - 2-3 sentence document summary
- `keywords` - 5-10 relevant keywords
- `document_type` - Classification into 24 categories:
  - invoice, contract, report, presentation, spreadsheet
  - resume, letter, memo, manual, guide, policy
  - academic_paper, research_paper, thesis, article
  - meeting_notes, technical_documentation, user_guide
  - marketing_material, financial_statement, legal_document
  - general, other

## API Endpoints

### Metadata Search Endpoints

#### POST /metadata/search

Filter-based document search with flexible criteria.

**Request Body:**

```json
{
  "filename": "quarterly_report",
  "file_type": "pdf",
  "document_type": "report",
  "author": "John Doe",
  "keywords": ["revenue", "growth"],
  "page_count_min": 10,
  "page_count_max": 50,
  "date_from": "2023-01-01",
  "date_to": "2023-12-31",
  "limit": 20
}
```

**Response:**

```json
{
  "success": true,
  "total_results": 5,
  "documents": [
    {
      "document_id": "uuid-here",
      "filename": "Q4_2023_Report.pdf",
      "file_type": "pdf",
      "document_type": "report",
      "summary": "Financial performance report...",
      "keywords": ["revenue", "growth", "Q4"],
      "metadata": {
        "author": "John Doe",
        "page_count": 25,
        "created_at": "2023-12-15T10:30:00",
        ...
      }
    }
  ]
}
```

#### POST /metadata/semantic-search

Semantic similarity search across document summaries.

**Request Body:**

```json
{
  "query": "documents about machine learning and neural networks",
  "limit": 10
}
```

**Response:**

```json
{
  "success": true,
  "total_results": 3,
  "documents": [
    {
      "document_id": "uuid-here",
      "filename": "Deep_Learning_Guide.pdf",
      "similarity_score": 0.89,
      "summary": "Comprehensive guide to neural networks...",
      ...
    }
  ]
}
```

#### GET /metadata/list

Paginated listing of all documents.

**Query Parameters:**

- `page` (default: 1) - Page number
- `page_size` (default: 20) - Items per page

**Response:**

```json
{
  "success": true,
  "total_documents": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8,
  "documents": [...]
}
```

#### GET /metadata/stats

System-wide metadata statistics.

**Response:**

```json
{
  "success": true,
  "total_documents": 150,
  "file_type_distribution": {
    "pdf": 100,
    "docx": 40,
    "doc": 10
  },
  "document_type_distribution": {
    "report": 45,
    "contract": 30,
    "invoice": 25,
    ...
  },
  "total_size_mb": 1250.5,
  "date_range": {
    "earliest": "2022-01-15T09:00:00",
    "latest": "2024-01-20T16:30:00"
  }
}
```

#### GET /metadata/document/{id}

Retrieve full metadata for a specific document.

**Response:**

```json
{
  "success": true,
  "document": {
    "document_id": "uuid-here",
    "filename": "Contract_2023.pdf",
    "file_type": "pdf",
    "document_type": "contract",
    "summary": "Service agreement between...",
    "keywords": ["contract", "service", "terms"],
    "metadata": {
      "author": "Legal Department",
      "page_count": 15,
      "title": "Service Agreement 2023",
      "file_size_bytes": 524288,
      "created_at": "2023-03-10T14:20:00",
      ...
    }
  }
}
```

## Query Classification

The `QueryClassifier` automatically detects query intent and routes appropriately.

### Metadata Query Examples

Queries focusing on document properties:

- "Find all invoices from 2023"
- "Show me reports by John Doe"
- "List PDF files larger than 10 pages"
- "Get contracts created in Q4"
- "How many documents do we have?"

**Detection Indicators:**

- File type references (pdf, docx, file)
- Document type names (invoice, report, contract)
- Author/attribution keywords (by, from, authored by)
- Time references (2023, Q4, last year)
- Listing verbs (list, show, find, get all)
- Counting queries (how many, total, count)

### Content Query Examples

Queries seeking information from document text:

- "What is the refund policy?"
- "Explain machine learning algorithms"
- "How do I reset my password?"
- "What are the benefits of cloud computing?"

**Detection Indicators:**

- Question words (what, how, why, when, where)
- Information verbs (explain, describe, tell me, define)
- Content references (says, mentions, discusses)
- Understanding keywords (mean, meaning)

### Hybrid Query Examples

Queries combining metadata filtering and content search:

- "What does the 2023 Q4 report say about revenue?"
- "Find contract terms in documents by Legal team"
- "Explain the methodology in John's research papers"
- "What security measures are mentioned in policy documents?"

**Detection:** Presence of both metadata and content indicators.

## Usage Examples

### Upload and Automatic Metadata Extraction

```python
import requests

# Upload a document - metadata is automatically extracted and stored
with open("Financial_Report_2023.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/upload/document",
        files={"file": f}
    )

print(response.json())
# {
#   "success": true,
#   "file_id": "abc-123",
#   "filename": "Financial_Report_2023.pdf",
#   "chunks_created": 45
# }
```

### Search by Metadata Filters

```python
# Find all financial reports from 2023
response = requests.post(
    "http://localhost:8000/metadata/search",
    json={
        "document_type": "report",
        "keywords": ["financial"],
        "date_from": "2023-01-01",
        "date_to": "2023-12-31"
    }
)

documents = response.json()["documents"]
for doc in documents:
    print(f"{doc['filename']}: {doc['summary']}")
```

### Semantic Document Search

```python
# Find documents similar to a concept
response = requests.post(
    "http://localhost:8000/metadata/semantic-search",
    json={
        "query": "quarterly financial performance analysis",
        "limit": 5
    }
)

for doc in response.json()["documents"]:
    print(f"{doc['filename']} (score: {doc['similarity_score']})")
    print(f"  {doc['summary']}")
```

### Content Query with Automatic Classification

```python
# Query will be automatically classified and routed
response = requests.post(
    "http://localhost:8000/chat/query",
    json={
        "question": "What were the main findings in the 2023 Q4 financial report?"
    }
)

print(response.json()["answer"])
# Hybrid query: Metadata filtered to Q4 2023 reports, then content search
```

### Get Document Statistics

```python
# Get system-wide metadata statistics
response = requests.get("http://localhost:8000/metadata/stats")

stats = response.json()
print(f"Total documents: {stats['total_documents']}")
print(f"File types: {stats['file_type_distribution']}")
print(f"Document types: {stats['document_type_distribution']}")
print(f"Total storage: {stats['total_size_mb']} MB")
```

## ChromaDB Collections

The system uses two separate ChromaDB collections:

### 1. document_chunks (Content)

- **Purpose:** Stores text chunks for semantic content search
- **Embeddings:** Text chunks embedded with MiniLM
- **Metadata per chunk:**
  - `document_id` - Parent document UUID
  - `chunk_id` - Unique chunk identifier
  - `chunk_index` - Position in document
  - `document_name` - Original filename

### 2. document_metadata (Metadata)

- **Purpose:** Stores document-level metadata and summaries
- **Embeddings:** Document summaries embedded with MiniLM
- **Metadata per document:**
  - All extracted file system metadata
  - All document-specific metadata (PDF/DOCX)
  - All AI-generated metadata (summary, keywords, type)
  - Full searchable by filters and semantic similarity

## Configuration

No additional configuration required. The metadata system uses existing settings:

```python
# config.py
DOCUMENTS_DIR = Path("./data/documents")
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}
CHROMA_DIR = Path("./data/chroma_db")  # Both collections stored here
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
OLLAMA_MODEL = "llama3.1:latest"
```

## Performance Considerations

### Metadata Extraction Time

- **File metadata:** < 1ms per document
- **PDF metadata:** 10-50ms depending on file size
- **DOCX metadata:** 5-20ms depending on file size
- **AI generation:** 2-5 seconds per document (LLM call)

### Storage Requirements

- **Metadata collection:** ~5-10KB per document
- **Content collection:** 1-2KB per chunk (depends on chunk size)
- **Typical document:** 20-50 chunks = 20-100KB total

### Query Performance

- **Metadata filter search:** 10-50ms (ChromaDB query)
- **Semantic metadata search:** 50-100ms (embedding + query)
- **Content search:** 100-200ms (embedding + chunk retrieval)
- **Hybrid query:** 150-300ms (both searches + combination)

## Extension Points

### Adding Custom Metadata Extractors

```python
# app/metadata_extractor.py
def extract_custom_metadata(self, file_path: Path) -> Dict[str, Any]:
    """Add custom metadata extraction logic."""
    metadata = {}
    # Your custom extraction logic
    return metadata
```

### Adding Document Types

```python
# app/ai_metadata_generator.py
DOCUMENT_TYPES = [
    "invoice", "contract", "report",
    "your_custom_type",  # Add here
    ...
]
```

### Custom Query Classification Rules

```python
# app/query_classifier.py
METADATA_KEYWORDS.add("your_keyword")
CONTENT_KEYWORDS.add("your_keyword")
```

## Troubleshooting

### Metadata not being extracted

- Check that Ollama is running for AI metadata generation
- Verify file permissions on uploaded documents
- Check logs for extraction errors (non-critical, won't fail upload)

### Query classification incorrect

- Add more specific keywords to METADATA_KEYWORDS or CONTENT_KEYWORDS
- Adjust confidence thresholds in QueryClassifier
- Force query type by using specific metadata endpoints

### Slow metadata generation

- AI metadata generation is the slowest step (2-5s per document)
- Runs asynchronously during upload - won't block response
- Consider caching or pre-generating for large batches

## Future Enhancements

Possible extensions to the metadata system:

1. **Advanced Filtering**

   - Date range operators (before, after, between)
   - Numeric range filters (size, page count)
   - Boolean combinations (AND, OR, NOT)

2. **Metadata Enrichment**

   - Named entity recognition (people, organizations, locations)
   - Topic modeling
   - Language detection
   - Sentiment analysis

3. **Hybrid Search Refinement**

   - Weighted combination of metadata and content scores
   - Dynamic query expansion based on metadata
   - Filter suggestion based on initial results

4. **Metadata Management**

   - Manual metadata editing
   - Batch metadata updates
   - Metadata versioning
   - Metadata validation rules

5. **Analytics**
   - Document access tracking
   - Popular search terms
   - Metadata quality metrics
   - Storage analytics
