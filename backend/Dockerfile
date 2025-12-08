# IntelliFile Backend Dockerfile
# Multi-stage build for optimized image size

FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Production stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    # Application defaults (can be overridden)
    APP_NAME="IntelliFile" \
    APP_VERSION="1.0.0" \
    DEBUG="False" \
    HOST="0.0.0.0" \
    PORT="8000" \
    OLLAMA_BASE_URL="http://ollama:11434" \
    OLLAMA_MODEL="llama3.1:latest" \
    OLLAMA_TIMEOUT="120" \
    EMBEDDING_MODEL="all-MiniLM-L6-v2" \
    EMBEDDING_DEVICE="cpu"

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Required for document processing
    libmagic1 \
    # Health check utility
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Set working directory
WORKDIR /app

# Create data directories
RUN mkdir -p /app/data/documents /app/data/chroma_db && \
    chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
