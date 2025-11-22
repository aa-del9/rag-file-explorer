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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])

# Initialize components
document_processor = DocumentProcessor(
    chunk_size=settings.CHUNK_SIZE,
    chunk_overlap=settings.CHUNK_OVERLAP
)
embedding_model = get_embedding_model(
    model_name=settings.EMBEDDING_MODEL,
    device=settings.EMBEDDING_DEVICE
)
vector_store = VectorStore(
    persist_directory=settings.CHROMA_DIR,
    collection_name=settings.CHROMA_COLLECTION_NAME
)


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
        
        # Store in vector database
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
    try:
        logger.info(f"Deleting document: {document_id}")
        
        # Delete from vector store
        deleted_count = vector_store.delete_by_document_id(document_id)
        
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
        
        if deleted_count == 0 and files_deleted == 0:
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
