# IntelliFile Backend

A fully local RAG (Retrieval-Augmented Generation) system for intelligent document exploration using Llama 3.1 via Ollama.

## 🚀 Features

### Core RAG System

- **Local LLM**: Uses Llama 3.1 via Ollama (no cloud dependencies)
- **Multiple Document Formats**: Support for PDF, DOC, and DOCX files
- **Extensible Architecture**: Easy to add new document format processors
- **Vector Search**: ChromaDB for persistent vector storage
- **Embeddings**: sentence-transformers (MiniLM-L6-v2)
- **REST API**: FastAPI-based endpoints for upload and querying

### Metadata-Aware File Explorer (New!)

- **Automatic Metadata Extraction**: File system + document-specific metadata
- **AI-Generated Metadata**: Summaries, keywords, document classification
- **Metadata Storage**: Separate ChromaDB collection for document discovery
- **Advanced Search**: Filter by filename, type, author, date, keywords
- **Semantic Document Search**: Find documents by meaning, not just keywords
- **Query Classification**: Auto-route between metadata/content/hybrid queries
- **Hybrid RAG**: Combine metadata filtering with content retrieval

### Production Ready

- Comprehensive error handling, logging, and testing
- Modular architecture for easy extension
- Full API documentation with interactive Swagger UI

## 📋 Prerequisites

1. **Python 3.9+** installed
2. **Ollama** installed and running
3. **Llama 3.1 model** pulled in Ollama

## 🐳 Docker (Recommended)

The easiest way to run the backend is using Docker Compose from the root directory:

```bash
# From the project root directory
docker compose up -d

# Check backend logs
docker logs -f intellifile-backend

# Backend will be available at http://localhost:8000
```

See the [main README](../README.md) for complete Docker instructions.

## 🛠️ Development Installation

For local development with hot-reloading:

### Step 1: Install Ollama

Download and install Ollama from: https://ollama.ai

### Step 2: Pull Llama 3.1 Model

```bash
ollama pull llama3.1:latest
```

Verify it's running:

```bash
ollama list
```

### Step 3: Set Up Python Environment

```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:

- FastAPI & Uvicorn (web framework)
- Ollama Python client
- sentence-transformers (embeddings)
- ChromaDB (vector database)
- PyPDF (PDF processing)
- And more...

## 🏃 Running the Server

### Option 1: Direct Python

```bash
cd backend
# Activate virtual environment first
python -m app.main
```

### Option 2: Using Uvicorn (with hot-reload)

```bash
cd backend
# Activate virtual environment first
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The server will start on: **http://localhost:8000**

## 📡 API Endpoints

> **📖 For complete metadata system documentation, see [METADATA_SYSTEM.md](METADATA_SYSTEM.md)**

### Core Endpoints

#### 1. Health Check

```bash
GET http://localhost:8000/health
```

Returns system status and component health.

#### 2. Upload Document

```bash
POST http://localhost:8000/upload/document
Content-Type: multipart/form-data

file: <your_document_file>
```

**Supported formats**: PDF, DOC, DOCX

**Example using cURL:**

```cmd
# Upload PDF
curl -X POST "http://localhost:8000/upload/document" -F "file=@document.pdf"

# Upload DOCX
curl -X POST "http://localhost:8000/upload/document" -F "file=@report.docx"

# Upload DOC
curl -X POST "http://localhost:8000/upload/document" -F "file=@legacy.doc"
```

**Legacy endpoint** (backward compatible):

```cmd
curl -X POST "http://localhost:8000/upload/pdf" -F "file=@document.pdf"
```

**Response:**

```json
{
  "success": true,
  "message": "Document uploaded and processed successfully (.docx)",
  "file_id": "uuid-here",
  "filename": "report.docx",
  "chunks_created": 45,
  "timestamp": "2025-11-20T10:30:00"
}
```

**What happens during upload:**

1. Document is saved to disk
2. Text is extracted and chunked
3. **File system metadata is extracted** (size, timestamps, etc.)
4. **Document metadata is extracted** (PDF/DOCX properties)
5. **AI metadata is generated** (summary, keywords, classification)
6. Chunks are embedded and stored in vector database
7. **Metadata is embedded and stored in metadata collection**

#### 3. Query/Chat

```bash
POST http://localhost:8000/chat/query
Content-Type: application/json

{
  "question": "What is the main topic of the document?",
  "top_k": 5
}
```

**Example using cURL:**

```cmd
curl -X POST "http://localhost:8000/chat/query" ^
  -H "Content-Type: application/json" ^
  -d "{\"question\": \"What is the main topic?\"}"
```

**Response:**

```json
{
  "success": true,
  "question": "What is the main topic?",
  "answer": "Based on the provided context...",
  "retrieved_chunks": [
    {
      "chunk_id": "uuid",
      "document_id": "doc-uuid",
      "text": "Relevant text chunk...",
      "similarity_score": 0.89
    }
  ],
  "model_used": "llama3.1:latest",
  "processing_time": 2.34
}
```

**Query Classification:**

The system automatically classifies your query and routes it appropriately:

- **Metadata queries**: "Find all invoices from 2023" → Searches metadata collection
- **Content queries**: "What is the refund policy?" → Searches document content
- **Hybrid queries**: "What does the Q4 report say about revenue?" → Combines both

#### 4. Get Statistics

```bash
GET http://localhost:8000/chat/stats
```

Returns system statistics including document count, embeddings info, etc.

#### 5. Delete Document

```bash
DELETE http://localhost:8000/upload/document/{document_id}
```

**Example:**

```cmd
curl -X DELETE "http://localhost:8000/upload/document/uuid-here"
```

**What happens during deletion:**

- Document chunks removed from vector database
- **Document metadata removed from metadata collection**
- Physical file deleted from disk

### Metadata Explorer Endpoints (New!)

#### 6. Search Documents by Filters

```bash
POST http://localhost:8000/metadata/search
Content-Type: application/json

{
  "document_type": "report",
  "author": "John Doe",
  "date_from": "2023-01-01",
  "date_to": "2023-12-31",
  "keywords": ["revenue", "growth"],
  "limit": 20
}
```

Find documents by properties like type, author, date, keywords, file type, etc.

#### 7. Semantic Document Search

```bash
POST http://localhost:8000/metadata/semantic-search
Content-Type: application/json

{
  "query": "financial performance and revenue analysis",
  "limit": 10
}
```

Find documents by semantic similarity to your query (searches document summaries).

#### 8. List All Documents

```bash
GET http://localhost:8000/metadata/list?page=1&page_size=20
```

Paginated listing of all documents with metadata.

#### 9. Get Metadata Statistics

```bash
GET http://localhost:8000/metadata/stats
```

System-wide statistics: document counts, file types, document types, storage size, date ranges.

#### 10. Get Document Metadata

```bash
GET http://localhost:8000/metadata/document/{document_id}
```

Retrieve complete metadata for a specific document.

> **💡 Tip:** See [METADATA_SYSTEM.md](METADATA_SYSTEM.md) for detailed examples and use cases.

## 🧪 Testing

Run the test suite:

```cmd
cd backend
venv\Scripts\activate
pytest tests/ -v
```

Run specific test file:

```cmd
pytest tests/test_pdf.py -v
pytest tests/test_rag.py -v
```

## 📁 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   ├── config.py                  # Configuration management
│   ├── models.py                  # Pydantic models (core)
│   ├── models_metadata.py         # Pydantic models (metadata)
│   │
│   ├── document_processor.py      # Multi-format document processing
│   ├── embeddings.py              # Embedding generation
│   ├── vector_store.py            # ChromaDB vector storage (chunks)
│   ├── llm_client.py              # Ollama LLM client
│   ├── rag_pipeline.py            # RAG orchestration
│   │
│   ├── metadata_extractor.py     # File + PDF/DOCX metadata extraction
│   ├── ai_metadata_generator.py  # AI-powered summary/keywords/classification
│   ├── metadata_store.py         # ChromaDB metadata storage
│   ├── query_classifier.py       # Query type classification
│   │
│   └── routers/
│       ├── __init__.py
│       ├── upload.py              # Document upload (with metadata)
│       ├── chat.py                # Query endpoints (hybrid RAG)
│       └── metadata.py            # Metadata search endpoints
│
├── data/
│   ├── documents/                 # Uploaded documents (all formats)
│   └── chroma_db/                 # ChromaDB persistent storage
│       ├── document_chunks/       # Content collection
│       └── document_metadata/     # Metadata collection
│
├── tests/
│   ├── __init__.py
│   ├── test_pdf.py                # PDF processing tests
│   └── test_rag.py                # RAG pipeline tests
│
├── requirements.txt               # Python dependencies
├── README.md                      # This file
├── METADATA_SYSTEM.md             # Metadata system documentation
├── DOCUMENT_FORMATS.md            # Supported formats guide
└── .gitignore                     # Git ignore rules
```

## ⚙️ Configuration

Configuration is managed in `app/config.py`. Key settings:

```python
# LLM Settings
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.1:latest"

# Embedding Settings
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DEVICE = "cpu"  # Use "cuda" for GPU

# RAG Settings
CHUNK_SIZE = 400
CHUNK_OVERLAP = 50
TOP_K_RESULTS = 5

# File Upload
MAX_FILE_SIZE = 50 MB
```

Create a `.env` file in the `backend` folder to override defaults:

```env
DEBUG=True
OLLAMA_MODEL=llama3.1:latest
EMBEDDING_DEVICE=cuda
TOP_K_RESULTS=10
```

## 🔧 Troubleshooting

### Ollama Connection Error

```
Error: Cannot connect to Ollama at http://localhost:11434
```

**Solution:** Make sure Ollama is running:

```cmd
ollama serve
```

### Model Not Found

```
Warning: Model llama3.1:latest not found
```

**Solution:** Pull the model:

```cmd
ollama pull llama3.1:latest
```

### CUDA Out of Memory

If using GPU and getting OOM errors:

1. Set `EMBEDDING_DEVICE=cpu` in config
2. Use a smaller model
3. Reduce `CHUNK_SIZE`

### Port Already in Use

```
Error: Address already in use
```

**Solution:** Change the port in `config.py` or kill the process using port 8000

## 📊 Performance Tips

1. **Use GPU**: Set `EMBEDDING_DEVICE=cuda` if you have NVIDIA GPU
2. **Adjust Chunk Size**: Smaller chunks = more precise but slower
3. **Tune top_k**: More chunks = better context but slower generation
4. **Batch Processing**: Upload multiple PDFs before querying

## 🔒 Security Notes

- This is a local development setup
- For production:
  - Add authentication (JWT tokens)
  - Implement rate limiting
  - Use HTTPS
  - Restrict CORS origins
  - Add input validation
  - Implement file scanning

## 📚 API Documentation

Once the server is running, visit:

- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 Extending with New File Formats

The system uses an extensible architecture for adding new document processors. Here's how to add support for a new format:

### Example: Adding TXT File Support

1. **Create a new extractor class** in `app/document_processor.py`:

```python
class TXTExtractor:
    """Extractor for plain text files."""

    def extract_text(self, file_path: Path) -> str:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
```

2. **Register the extractor**:

```python
# In app/document_processor.py or your initialization code
DocumentProcessor.register_extractor(".txt", TXTExtractor)
```

3. **Update allowed extensions** in `app/config.py`:

```python
ALLOWED_EXTENSIONS: set = {".pdf", ".doc", ".docx", ".txt"}
```

That's it! The system will now handle TXT files automatically.

### Adding Other Formats

- **Markdown (.md)**: Similar to TXT extractor
- **HTML (.html)**: Use BeautifulSoup for parsing
- **RTF (.rtf)**: Use `striprtf` library
- **ODT (.odt)**: Use `odfpy` library

The `DocumentExtractor` protocol ensures consistency across all extractors.

## 🤝 Contributing

1. Add new features in separate modules
2. Write tests for new functionality
3. Update this README
4. Follow PEP 8 style guidelines

## 📝 License

MIT License - Feel free to use for educational and commercial purposes.

## 🐛 Known Issues

1. Very large documents (>100MB) may take long to process
2. Scanned PDFs without OCR won't extract text
3. Complex document layouts may have formatting issues
4. Legacy .doc format has limited support (prefer .docx)

## 🎯 Future Enhancements

- [x] Add support for multiple file formats (PDF, DOC, DOCX)
- [x] Extensible architecture for new formats
- [x] Add document metadata search
- [x] AI-generated metadata (summary, keywords, classification)
- [x] Hybrid RAG with metadata filtering
- [x] Query classification for intelligent routing
- [ ] Add support for TXT, MD, HTML formats
- [ ] Implement conversation history
- [ ] Support for streaming responses
- [ ] Advanced metadata filtering (boolean operators)
- [ ] Named entity recognition in metadata
- [ ] Multi-language support
- [ ] GPU acceleration options
- [ ] Docker containerization
- [ ] Web frontend

## 📞 Support

For issues or questions:

1. Check the troubleshooting section
2. Review logs in `rag_backend.log`
3. Check Ollama logs: `ollama logs`

---

**Built with ❤️ using Python, FastAPI, and Ollama**
