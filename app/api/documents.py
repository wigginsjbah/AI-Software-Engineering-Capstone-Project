"""
Document management API endpoints
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from typing import List, Optional
import json

from app.services.document_manager import DocumentManager
from utils.logging import get_logger

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])
logger = get_logger(__name__)

# Initialize document manager
doc_manager = DocumentManager()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    category: str = Query("general", description="Document category")
):
    """
    Upload a business document for RAG processing
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected")
        
        # Check file type
        supported_types = doc_manager.get_supported_file_types()
        file_extension = "." + file.filename.split(".")[-1].lower()
        
        if file_extension not in supported_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Supported types: {', '.join(supported_types)}"
            )
        
        # Upload and process document
        document_info = await doc_manager.upload_document(file, category)
        
        return {
            "success": True,
            "message": "Document uploaded successfully",
            "document": document_info
        }
        
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def get_all_documents():
    """
    Get list of all uploaded documents
    """
    try:
        documents = await doc_manager.get_all_documents()
        return {
            "success": True,
            "documents": documents,
            "total": len(documents)
        }
    except Exception as e:
        logger.error(f"Error retrieving documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics")
async def get_document_statistics():
    """
    Get statistics about uploaded documents
    """
    try:
        stats = await doc_manager.get_document_statistics()
        return {
            "success": True,
            "statistics": stats
        }
    except Exception as e:
        logger.error(f"Error getting document statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_documents(q: str = Query(..., description="Search query")):
    """
    Search documents by filename or content
    """
    try:
        results = await doc_manager.search_documents(q)
        return {
            "success": True,
            "query": q,
            "results": results,
            "total": len(results)
        }
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/category/{category}")
async def get_documents_by_category(category: str):
    """
    Get documents filtered by category
    """
    try:
        documents = await doc_manager.get_documents_by_category(category)
        return {
            "success": True,
            "category": category,
            "documents": documents,
            "total": len(documents)
        }
    except Exception as e:
        logger.error(f"Error getting documents by category: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{document_id}")
async def get_document(document_id: str):
    """
    Get specific document by ID
    """
    try:
        document = await doc_manager.get_document_by_id(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "success": True,
            "document": document
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document
    """
    try:
        success = await doc_manager.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "success": True,
            "message": "Document deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/supported-types")
async def get_supported_file_types():
    """
    Get list of supported file types for upload
    """
    return {
        "success": True,
        "supported_types": doc_manager.get_supported_file_types(),
        "descriptions": {
            ".txt": "Plain text files",
            ".md": "Markdown files",
            ".pdf": "PDF documents",
            ".docx": "Microsoft Word documents",
            ".doc": "Microsoft Word documents (legacy)",
            ".html": "HTML files",
            ".htm": "HTML files"
        }
    }