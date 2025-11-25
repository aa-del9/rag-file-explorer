"""
Upload router for PDF file handling.
Handles PDF upload and document ingestion into the RAG system.
"""

import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pathlib import Path
import uuid
import time
import aiofiles

from app.models import UploadResponse, ErrorResponse
from app.config import settings
from app.document_processor import DocumentProcessor
from app.embeddings import get_embedding_model
from app.vector_store import VectorStore
from app.llm_client import LLMClient
from app.metadata_extractor import MetadataExtractor
from app.ai_metadata_generator import AIMetadataGenerator
from app.metadata_store import MetadataStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])

# Initialize lightweight components
document_processor = DocumentProcessor(
    chunk_size=settings.CHUNK_SIZE,
    chunk_overlap=settings.CHUNK_OVERLAP
)
metadata_extractor = MetadataExtractor()

# Lazy-loaded components (initialized on first use)
_embedding_model = None
_vector_store = None
_llm_client = None
_ai_metadata_generator = None
_metadata_store = None


def get_components():
    """Lazy initialization of heavy components."""
    global _embedding_model, _vector_store, _llm_client, _ai_metadata_generator, _metadata_store
    
    if _embedding_model is None:
        _embedding_model = get_embedding_model(
            model_name=settings.EMBEDDING_MODEL,
            device=settings.EMBEDDING_DEVICE
        )
    
    if _vector_store is None:
        _vector_store = VectorStore(
            persist_directory=settings.CHROMA_DIR,
            collection_name=settings.CHROMA_COLLECTION_NAME
        )
    
    if _llm_client is None:
        _llm_client = LLMClient(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            timeout=settings.OLLAMA_TIMEOUT
        )
    
    if _ai_metadata_generator is None:
        _ai_metadata_generator = AIMetadataGenerator(llm_client=_llm_client)
    
    if _metadata_store is None:
        _metadata_store = MetadataStore(
            persist_directory=settings.CHROMA_DIR
        )
    
    return _embedding_model, _vector_store, _ai_metadata_generator, _metadata_store


@router.post("/document", response_model=UploadResponse, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a document file (PDF, DOC, DOCX) for RAG.
    
    Process:
    1. Validate file type and size
    2. Save document to disk
    3. Extract text from document
    4. Chunk text
    5. Generate embeddings
    6. Store in vector database
    
    Args:
        file: Document file upload (PDF, DOC, or DOCX)
        
    Returns:
        UploadResponse with processing details
    """
    start_time = time.time()
    
    # Get components (lazy initialization)
    embedding_model, vector_store, ai_metadata_generator, metadata_store = get_components()
    
    try:
        # Validate file type
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in settings.ALLOWED_EXTENSIONS:
            logger.warning(f"Invalid file type attempted: {file.filename}")
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_extension} not supported. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Create safe filename
        safe_filename = f"{document_id}_{file.filename}"
        file_path = settings.DOCUMENTS_DIR / safe_filename
        
        logger.info(f"Processing upload: {file.filename} (ID: {document_id})")
        
        # Save file to disk
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                
                # Check file size
                if len(content) > settings.MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
                    )
                
                await f.write(content)
            
            logger.info(f"File saved: {file_path}")
        
        except Exception as e:
            logger.error(f"Failed to save file: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save file: {str(e)}"
            )
        
        # Process document: extract and chunk
        try:
            chunks = document_processor.process_document(file_path, document_id)
            
            if not chunks:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to extract text from document or document is empty"
                )
            
            logger.info(f"Created {len(chunks)} chunks from {file_extension} document")
        
        except Exception as e:
            logger.error(f"Failed to process document: {str(e)}")
            # Clean up saved file
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process document: {str(e)}"
            )
        
        # Generate embeddings
        try:
            chunk_texts = [chunk[0] for chunk in chunks]
            chunk_metadatas = [chunk[1] for chunk in chunks]
            
            embeddings = embedding_model.embed_text_batch(chunk_texts)
            
            logger.info(f"Generated {len(embeddings)} embeddings")
        
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {str(e)}")
            # Clean up saved file
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate embeddings: {str(e)}"
            )
        
        # Store chunks in vector database
        try:
            chunks_upserted = vector_store.upsert_chunks(
                chunks=chunk_texts,
                embeddings=embeddings,
                metadatas=chunk_metadatas
            )
            
            logger.info(f"Upserted {chunks_upserted} chunks to vector store")
        
        except Exception as e:
            logger.error(f"Failed to store in vector database: {str(e)}")
            # Clean up saved file
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to store in vector database: {str(e)}"
            )
        
        # Extract and store document metadata
        try:
            # Extract file system and document-specific metadata
            extracted_metadata = metadata_extractor.extract_all_metadata(file_path)
            logger.info(f"Extracted metadata: {extracted_metadata.get('title', file.filename)}")
            
            # Generate AI metadata (summary, keywords, document type)
            full_text = " ".join(chunk_texts)
            ai_metadata = ai_metadata_generator.generate_all_metadata(full_text, file.filename)
            logger.info(f"Generated AI metadata: type={ai_metadata.get('ai_document_type', 'unknown')}, keywords={len(ai_metadata.get('ai_keywords', []))}")
            
            # Merge all metadata
            combined_metadata = {**extracted_metadata, **ai_metadata}
            
            # Get the summary for embedding
            summary_text = ai_metadata.get("ai_summary", "")
            
            # Generate embedding for the summary
            summary_embedding = None
            if summary_text:
                try:
                    summary_embedding = embedding_model.embed_text(summary_text)
                except Exception as e:
                    logger.warning(f"Failed to generate summary embedding: {str(e)}")
            
            # Store in metadata store
            metadata_store.store_document_metadata(
                document_id=document_id,
                metadata=combined_metadata,
                summary_embedding=summary_embedding,
                summary_text=summary_text
            )
            
            logger.info(f"Stored metadata for document: {document_id}")
        
        except Exception as e:
            # Log error but don't fail the upload - content is already stored
            logger.error(f"Failed to extract/store metadata (non-critical): {str(e)}")
        
        processing_time = time.time() - start_time
        
        logger.info(
            f"Upload completed successfully in {processing_time:.2f}s: "
            f"{file.filename} -> {chunks_upserted} chunks"
        )
        
        return UploadResponse(
            success=True,
            message=f"Document uploaded and processed successfully ({file_extension})",
            file_id=document_id,
            filename=file.filename,
            chunks_created=chunks_upserted
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error during upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post("/pdf", response_model=UploadResponse, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def upload_pdf(file: UploadFile = File(...)):
    """
    Legacy endpoint for PDF upload (redirects to /document).
    Maintained for backward compatibility.
    """
    return await upload_document(file)


@router.delete("/document/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document and all associated chunks from the system.
    
    Args:
        document_id: UUID of the document to delete
        
    Returns:
        Success message with deletion details
    """
    # Get components (lazy initialization)
    _, vector_store, _, metadata_store = get_components()
    
    try:
        logger.info(f"Deleting document: {document_id}")
        
        # Delete from vector store
        deleted_count = vector_store.delete_by_document_id(document_id)
        
        # Delete from metadata store
        metadata_deleted = False
        try:
            metadata_store.delete_document(document_id)
            metadata_deleted = True
            logger.info(f"Deleted metadata for document: {document_id}")
        except Exception as e:
            logger.warning(f"Failed to delete metadata (non-critical): {str(e)}")
        
        # Find and delete document file
        document_files = list(settings.DOCUMENTS_DIR.glob(f"{document_id}_*"))
        files_deleted = 0
        
        for doc_file in document_files:
            try:
                doc_file.unlink()
                files_deleted += 1
                logger.info(f"Deleted file: {doc_file.name}")
            except Exception as e:
                logger.warning(f"Failed to delete file {doc_file}: {str(e)}")
        
        if deleted_count == 0 and files_deleted == 0 and not metadata_deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {document_id}"
            )
        
        return {
            "success": True,
            "message": "Document deleted successfully",
            "document_id": document_id,
            "chunks_deleted": deleted_count,
            "files_deleted": files_deleted
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Failed to delete document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )
