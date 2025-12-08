# IntelliFile

<div align="center">

**Intelligent Document Explorer with Local AI**

A fully local RAG (Retrieval-Augmented Generation) system for intelligent document exploration using Llama 3.1 via Ollama.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Next.js](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com/)
[![Ollama](https://img.shields.io/badge/Ollama-Llama_3.1-purple)](https://ollama.ai/)

</div>

---

## ✨ Features

- **🔒 100% Local & Private** - All processing happens on your machine, no cloud dependencies
- **📄 Multi-Format Support** - PDF, DOC, and DOCX files
- **🔍 Semantic Search** - Find documents by meaning, not just keywords
- **🤖 AI-Powered Insights** - Automatic summaries, keywords, and document classification
- **📊 Smart Metadata** - Extract and search file properties, authors, dates
- **💬 Chat with Documents** - Ask questions and get AI-powered answers
- **🎨 Modern UI** - Beautiful dark mode interface with Next.js 15

## 🚀 Quick Start

### Option 1: Docker (Recommended)

The fastest way to get IntelliFile running with all dependencies.

**Prerequisites:**
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

**Steps:**

```bash
# 1. Clone the repository
git clone https://github.com/aa-del9/rag-file-explorer.git
cd rag-file-explorer

# 2. (Optional) Create environment file for customization
cp .env.example .env

# 3. Start all services
docker compose up -d

# 4. Wait for model download (~4GB, first run only)
docker logs -f intellifile-ollama-pull
```

**Services will be available at:**
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **ChromaDB**: http://localhost:8100
- **Ollama**: http://localhost:11434

**Check service health:**
```bash
docker ps
docker logs intellifile-backend
```

**Stop services:**
```bash
docker compose down

# To also remove volumes (⚠️ deletes all data):
docker compose down -v
```

---

### Option 2: Development Setup

For local development with hot-reloading.

**Prerequisites:**
- [Python 3.9+](https://www.python.org/downloads/)
- [Node.js 18.17+](https://nodejs.org/)
- [pnpm](https://pnpm.io/) (recommended) or npm
- [Ollama](https://ollama.ai/) installed

#### Step 1: Set up Ollama

```bash
# Install Ollama (see https://ollama.ai for your OS)
# Then pull the Llama 3.1 model
ollama pull llama3.1:latest

# Verify it's running
ollama list
```

#### Step 2: Set up Backend

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python -m app.main
```

Backend will be available at: http://localhost:8000

#### Step 3: Set up Frontend

```bash
# In a new terminal, navigate to frontend
cd frontend

# Install dependencies
pnpm install

# Create environment file
cp .env.example .env.local

# Start development server
pnpm dev
```

Frontend will be available at: http://localhost:3000

---

## 📖 Usage

### Upload Documents

1. Navigate to http://localhost:3000/upload
2. Drag and drop files or click to browse
3. Wait for processing (text extraction, embedding, AI analysis)

### Explore Documents

1. Navigate to http://localhost:3000/explorer
2. Browse documents with filtering and sorting
3. Click a document to view AI-generated summary and similar documents

### Search Documents

1. Use the search bar in the navbar
2. Enter semantic queries like "documents about machine learning"
3. Results are ranked by relevance

### Chat with Documents

Use the API to ask questions:

```bash
curl -X POST "http://localhost:8000/chat/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the main topics in my documents?"}'
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js 15)                    │
│                    http://localhost:3000                         │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                           │
│                    http://localhost:8000                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Upload    │  │    Chat     │  │  Documents  │              │
│  │   Router    │  │   Router    │  │   Router    │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│         │                │                │                      │
│         ▼                ▼                ▼                      │
│  ┌─────────────────────────────────────────────────┐            │
│  │              RAG Pipeline                        │            │
│  │  • Document Processing  • Embeddings             │            │
│  │  • Metadata Extraction  • Query Classification   │            │
│  └─────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
        │                                       │
        ▼                                       ▼
┌───────────────────┐                ┌───────────────────┐
│     ChromaDB      │                │      Ollama       │
│  Vector Database  │                │   Llama 3.1 LLM   │
│ localhost:8100    │                │ localhost:11434   │
└───────────────────┘                └───────────────────┘
```

---

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_MODEL` | `llama3.1:latest` | LLM model to use |
| `OLLAMA_TIMEOUT` | `120` | Request timeout in seconds |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence transformer model |
| `EMBEDDING_DEVICE` | `cpu` | `cpu` or `cuda` for GPU |
| `CHUNK_SIZE` | `400` | Text chunk size in characters |
| `CHUNK_OVERLAP` | `50` | Overlap between chunks |
| `TOP_K_RESULTS` | `5` | Number of results to retrieve |
| `MAX_FILE_SIZE` | `52428800` | Max upload size (50MB) |

### GPU Support (NVIDIA)

Uncomment the GPU section in `docker-compose.yml`:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```

---

## 📁 Project Structure

```
rag-file-explorer/
├── docker-compose.yml      # Docker orchestration
├── .env.example           # Environment template
├── backend/               # FastAPI backend
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py       # Application entry
│   │   ├── config.py     # Configuration
│   │   ├── rag_pipeline.py
│   │   ├── embeddings.py
│   │   ├── vector_store.py
│   │   └── routers/      # API endpoints
│   └── data/             # Documents & database
└── frontend/             # Next.js frontend
    ├── package.json
    ├── app/              # Pages
    ├── components/       # React components
    └── lib/              # Utilities & API
```

---

## 🔧 Troubleshooting

### Docker Issues

**Services not starting:**
```bash
# Check logs
docker compose logs

# Rebuild containers
docker compose build --no-cache
docker compose up -d
```

**Model not downloading:**
```bash
# Check ollama-pull logs
docker logs intellifile-ollama-pull

# Manually pull in running container
docker exec -it intellifile-ollama ollama pull llama3.1:latest
```

### Development Issues

**Backend won't start:**
- Ensure Ollama is running: `ollama list`
- Check Python version: `python --version` (3.9+ required)
- Verify virtual environment is activated

**Frontend can't connect to backend:**
- Ensure backend is running on port 8000
- Check `NEXT_PUBLIC_API_URL` in `.env.local`

---

## 📚 Documentation

- [Backend README](backend/README.md) - Detailed API documentation
- [Frontend README](frontend/README.md) - Frontend development guide
- [Metadata System](backend/METADATA_SYSTEM.md) - Metadata extraction details

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
