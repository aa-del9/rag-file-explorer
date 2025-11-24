"""
Reset script to clear all data and start fresh.
Deletes ChromaDB collections and uploaded documents.
"""

import shutil
from pathlib import Path
import sys

def reset_database():
    """Reset all data: ChromaDB and uploaded documents."""
    
    backend_dir = Path(__file__).parent
    
    # Paths to delete
    chroma_dir = backend_dir / "data" / "chroma_db"
    documents_dir = backend_dir / "data" / "documents"
    pdfs_dir = backend_dir / "data" / "pdfs"  # Legacy directory
    log_file = backend_dir / "rag_backend.log"
    
    print("=" * 60)
    print("RAG File Explorer - Database Reset")
    print("=" * 60)
    print()
    print("This will delete:")
    print(f"  • ChromaDB database: {chroma_dir}")
    print(f"  • Uploaded documents: {documents_dir}")
    if pdfs_dir.exists():
        print(f"  • Legacy PDFs: {pdfs_dir}")
    if log_file.exists():
        print(f"  • Log file: {log_file}")
    print()
    
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() not in ['yes', 'y']:
        print("\nReset cancelled.")
        return
    
    print("\nResetting...")
    deleted_count = 0
    
    # Delete ChromaDB
    if chroma_dir.exists():
        try:
            shutil.rmtree(chroma_dir)
            print(f"✓ Deleted ChromaDB: {chroma_dir}")
            deleted_count += 1
        except Exception as e:
            print(f"✗ Failed to delete ChromaDB: {str(e)}")
            print(f"  → Make sure the server is stopped (no Python processes using the DB)")
    
    # Delete documents
    if documents_dir.exists():
        try:
            shutil.rmtree(documents_dir)
            print(f"✓ Deleted documents: {documents_dir}")
            deleted_count += 1
        except Exception as e:
            print(f"✗ Failed to delete documents: {str(e)}")
    
    # Delete legacy PDFs directory
    if pdfs_dir.exists():
        try:
            shutil.rmtree(pdfs_dir)
            print(f"✓ Deleted legacy PDFs: {pdfs_dir}")
            deleted_count += 1
        except Exception as e:
            print(f"✗ Failed to delete PDFs: {str(e)}")
    
    # Delete log file
    if log_file.exists():
        try:
            log_file.unlink()
            print(f"✓ Deleted log file: {log_file}")
            deleted_count += 1
        except Exception as e:
            print(f"✗ Failed to delete log: {str(e)}")
    
    # Recreate empty directories
    documents_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created empty documents directory")
    
    print()
    print("=" * 60)
    if deleted_count > 0:
        print("✅ Reset complete! All data has been cleared.")
    else:
        print("⚠️  Reset incomplete. Some files may still be locked.")
        print("   Make sure to stop the server first.")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Start the server: python -m app.main")
    print("  2. Upload documents: POST http://localhost:8000/upload/document")
    print("  3. Check API docs: http://localhost:8000/docs")
    print()


if __name__ == "__main__":
    try:
        reset_database()
    except KeyboardInterrupt:
        print("\n\nReset cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        sys.exit(1)
