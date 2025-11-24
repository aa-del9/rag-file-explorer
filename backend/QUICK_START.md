# Quick Start Guide - Metadata-Aware RAG File Explorer

## Getting Started in 5 Minutes

### 1. Start the Server

```cmd
cd c:\Projects\uni\rag-file-explorer\backend
venv\Scripts\activate
python -m app.main
```

Server runs at: **http://localhost:8000**

### 2. Verify Everything is Working

Open your browser and visit:

- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs

You should see all systems healthy (green status).

### 3. Upload Your First Document

```cmd
curl -X POST "http://localhost:8000/upload/document" -F "file=@your_document.pdf"
```

Or use the interactive docs at http://localhost:8000/docs

**What happens:**

- ✅ Document saved and text extracted
- ✅ Metadata extracted (file info + PDF properties)
- ✅ AI generates summary, keywords, and classification
- ✅ Content embedded and stored
- ✅ Metadata embedded and stored

### 4. Try Different Types of Queries

#### Content Query (searches document text)

```bash
curl -X POST "http://localhost:8000/chat/query" \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"What is the main topic discussed in the documents?\"}"
```

#### Metadata Query (searches document properties)

```bash
curl -X POST "http://localhost:8000/metadata/search" \
  -H "Content-Type: application/json" \
  -d "{\"document_type\": \"report\", \"limit\": 10}"
```

#### Hybrid Query (combines both)

```bash
curl -X POST "http://localhost:8000/chat/query" \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"What does the 2023 financial report say about revenue?\"}"
```

## Common Use Cases

### Use Case 1: Find Documents by Type

**Goal**: List all invoices in the system

```bash
curl -X POST "http://localhost:8000/metadata/search" \
  -H "Content-Type: application/json" \
  -d "{\"document_type\": \"invoice\"}"
```

### Use Case 2: Find Documents by Date Range

**Goal**: Get all reports from Q4 2023

```bash
curl -X POST "http://localhost:8000/metadata/search" \
  -H "Content-Type: application/json" \
  -d "{
    \"document_type\": \"report\",
    \"date_from\": \"2023-10-01\",
    \"date_to\": \"2023-12-31\"
  }"
```

### Use Case 3: Find Documents by Author

**Goal**: Get all documents authored by "John Doe"

```bash
curl -X POST "http://localhost:8000/metadata/search" \
  -H "Content-Type: application/json" \
  -d "{\"author\": \"John Doe\"}"
```

### Use Case 4: Semantic Document Search

**Goal**: Find documents related to "machine learning" without exact keyword match

```bash
curl -X POST "http://localhost:8000/metadata/semantic-search" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"artificial intelligence and neural networks\",
    \"limit\": 5
  }"
```

### Use Case 5: Get System Statistics

**Goal**: See what documents you have in the system

```bash
curl -X GET "http://localhost:8000/metadata/stats"
```

**Response:**

```json
{
  "total_documents": 25,
  "file_type_distribution": {
    "pdf": 15,
    "docx": 8,
    "doc": 2
  },
  "document_type_distribution": {
    "report": 10,
    "invoice": 7,
    "contract": 5,
    "other": 3
  },
  "total_size_mb": 125.5
}
```

### Use Case 6: Browse All Documents

**Goal**: List all documents with pagination

```bash
curl -X GET "http://localhost:8000/metadata/list?page=1&page_size=10"
```

## Testing with Python

### Upload Script

```python
import requests

# Upload a document
with open("my_report.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/upload/document",
        files={"file": f}
    )

result = response.json()
print(f"Uploaded: {result['filename']}")
print(f"Document ID: {result['file_id']}")
print(f"Chunks created: {result['chunks_created']}")
```

### Search Script

```python
import requests

# Search for invoices from 2023
response = requests.post(
    "http://localhost:8000/metadata/search",
    json={
        "document_type": "invoice",
        "date_from": "2023-01-01",
        "date_to": "2023-12-31"
    }
)

documents = response.json()["documents"]
print(f"Found {len(documents)} invoices from 2023:")
for doc in documents:
    print(f"  - {doc['filename']}: {doc['summary'][:100]}...")
```

### Query Script

```python
import requests

# Ask a question
response = requests.post(
    "http://localhost:8000/chat/query",
    json={
        "question": "What are the payment terms in the contracts?"
    }
)

result = response.json()
print(f"Answer: {result['answer']}")
print(f"\nSources ({len(result['retrieved_chunks'])} chunks):")
for i, chunk in enumerate(result['retrieved_chunks'], 1):
    print(f"  {i}. {chunk['metadata']['document_name']} (score: {chunk['similarity_score']})")
```

## Using the Interactive API Docs

1. Open http://localhost:8000/docs in your browser
2. You'll see all available endpoints
3. Click on any endpoint to expand it
4. Click "Try it out" button
5. Fill in the parameters
6. Click "Execute"
7. See the response below

**Recommended endpoints to try:**

- `POST /upload/document` - Upload your first file
- `GET /metadata/list` - See all uploaded documents
- `POST /metadata/search` - Filter documents
- `POST /chat/query` - Ask questions

## Troubleshooting

### "No documents have been uploaded yet"

**Problem:** Query returns this message

**Solution:** Upload at least one document first:

```bash
curl -X POST "http://localhost:8000/upload/document" -F "file=@document.pdf"
```

### "Cannot connect to Ollama"

**Problem:** Health check shows Ollama disconnected

**Solution:** Make sure Ollama is running:

```cmd
ollama serve
```

### "Model not found"

**Problem:** Llama 3.1 model not available

**Solution:** Pull the model:

```cmd
ollama pull llama3.1:latest
```

### Metadata extraction errors (non-critical)

**Problem:** Upload succeeds but logs show metadata errors

**Impact:** Content search works fine, metadata search may be limited

**Solution:**

- Check that Ollama is running (for AI metadata)
- Verify document has proper metadata (PDFs from scanners may not)
- File system metadata always works regardless

## Next Steps

1. ✅ Upload several documents of different types
2. ✅ Check `/metadata/stats` to see your collection
3. ✅ Try filtering by document type, author, or date
4. ✅ Try semantic search to find similar documents
5. ✅ Ask questions and see how hybrid queries work
6. 📖 Read [METADATA_SYSTEM.md](METADATA_SYSTEM.md) for advanced features
7. 📖 Read [DOCUMENT_FORMATS.md](DOCUMENT_FORMATS.md) to add new formats

## Tips for Best Results

### For Better Content Search

- Upload documents with clear, structured text
- Use specific questions
- Adjust `top_k` parameter to retrieve more/fewer chunks

### For Better Metadata Search

- Use PDFs with proper metadata (author, title, etc.)
- Let the AI generate metadata (wait 2-5 seconds per upload)
- Use specific filters to narrow down results

### For Hybrid Queries

- Include both "what" (content) and "where" (metadata) in your question
- Example: "What does the Q4 2023 report say about sales?"
  - "Q4 2023" → metadata filter
  - "say about sales" → content search

## Performance Expectations

- **Upload**: 3-10 seconds per document (includes AI generation)
- **Metadata search**: < 100ms
- **Content search**: 100-200ms
- **Query with LLM**: 2-5 seconds (depends on Ollama speed)
- **Hybrid query**: 2-5 seconds (LLM is the bottleneck)

Enjoy your metadata-aware RAG file explorer! 🚀
