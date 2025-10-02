"""
Document management system for uploading and processing business documents
"""

import os
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import aiofiles
from fastapi import UploadFile
import PyPDF2
import docx
from bs4 import BeautifulSoup

from utils.logging import get_logger
from rag.vector_store import VectorStore

class DocumentManager:
    """
    Manages document uploads, processing, and indexing for the RAG system
    """
    
    def __init__(self, upload_dir: str = "data/business_documents"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger(__name__)
        
        # Initialize vector store for document indexing
        self.vector_store = VectorStore()
        
        # Document metadata storage
        self.metadata_file = self.upload_dir / "document_metadata.json"
        
        # Supported file types
        self.supported_types = {
            '.txt': self._process_text_file,
            '.md': self._process_text_file,
            '.pdf': self._process_pdf_file,
            '.docx': self._process_docx_file,
            '.doc': self._process_docx_file,
            '.html': self._process_html_file,
            '.htm': self._process_html_file
        }
    
    async def upload_document(self, file: UploadFile, category: str = "general") -> Dict[str, Any]:
        """
        Upload and process a business document
        """
        try:
            # Initialize vector store if needed
            if not self.vector_store.initialized:
                await self.vector_store.initialize()
            
            # Validate file type
            file_extension = Path(file.filename).suffix.lower()
            if file_extension not in self.supported_types:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            # Generate unique filename
            file_hash = hashlib.md5(f"{file.filename}{datetime.now().isoformat()}".encode()).hexdigest()[:8]
            safe_filename = f"{file_hash}_{file.filename}"
            file_path = self.upload_dir / safe_filename
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # Process document content
            text_content = await self._extract_text_content(file_path, file_extension)
            
            # Split content into chunks for vector store
            chunks = self._split_text_into_chunks(text_content)
            
            # Create document metadata
            document_info = {
                "id": file_hash,
                "filename": file.filename,
                "safe_filename": safe_filename,
                "file_path": str(file_path),
                "file_size": len(content),
                "file_type": file_extension,
                "category": category,
                "upload_date": datetime.now().isoformat(),
                "content_preview": text_content[:500] + "..." if len(text_content) > 500 else text_content,
                "content_length": len(text_content),
                "status": "processed"
            }
            
            # Add to vector store
            await self._add_to_vector_store(chunks, document_info)
            
            # Save metadata
            await self._save_document_metadata(document_info)
            
            self.logger.info(f"Document uploaded successfully: {file.filename}")
            return document_info
            
        except Exception as e:
            self.logger.error(f"Error uploading document {file.filename}: {str(e)}")
            raise Exception(f"Failed to upload document: {str(e)}")
    
    async def _extract_text_content(self, file_path: Path, file_extension: str) -> str:
        """
        Extract text content from uploaded file based on its type
        """
        processor = self.supported_types.get(file_extension)
        if processor:
            return await processor(file_path)
        else:
            raise ValueError(f"No processor available for {file_extension}")
    
    async def _process_text_file(self, file_path: Path) -> str:
        """Process plain text and markdown files"""
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            return await f.read()
    
    async def _process_pdf_file(self, file_path: Path) -> str:
        """Process PDF files"""
        try:
            text_content = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text_content += page.extract_text() + "\n"
            return text_content
        except Exception as e:
            self.logger.error(f"Error processing PDF {file_path}: {str(e)}")
            return f"Error processing PDF: {str(e)}"
    
    async def _process_docx_file(self, file_path: Path) -> str:
        """Process Word documents"""
        try:
            doc = docx.Document(file_path)
            text_content = ""
            for paragraph in doc.paragraphs:
                text_content += paragraph.text + "\n"
            return text_content
        except Exception as e:
            self.logger.error(f"Error processing DOCX {file_path}: {str(e)}")
            return f"Error processing Word document: {str(e)}"
    
    async def _process_html_file(self, file_path: Path) -> str:
        """Process HTML files"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                html_content = await f.read()
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup.get_text()
        except Exception as e:
            self.logger.error(f"Error processing HTML {file_path}: {str(e)}")
            return f"Error processing HTML: {str(e)}"
    
    async def _save_document_metadata(self, document_info: Dict[str, Any]) -> None:
        """
        Save document metadata to a JSON file
        """
        metadata_file = self.upload_dir / "document_metadata.json"
        
        # Load existing metadata
        existing_metadata = []
        if metadata_file.exists():
            async with aiofiles.open(metadata_file, 'r') as f:
                import json
                try:
                    existing_metadata = json.loads(await f.read())
                except json.JSONDecodeError:
                    existing_metadata = []
        
        # Add new document metadata
        existing_metadata.append(document_info)
        
        # Save updated metadata
        async with aiofiles.open(metadata_file, 'w') as f:
            import json
            await f.write(json.dumps(existing_metadata, indent=2))
    
    async def get_all_documents(self) -> List[Dict[str, Any]]:
        """
        Get list of all uploaded documents with metadata
        """
        metadata_file = self.upload_dir / "document_metadata.json"
        
        if not metadata_file.exists():
            return []
        
        try:
            async with aiofiles.open(metadata_file, 'r') as f:
                import json
                return json.loads(await f.read())
        except Exception as e:
            self.logger.error(f"Error reading document metadata: {str(e)}")
            return []
    
    async def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document metadata by ID
        """
        documents = await self.get_all_documents()
        for doc in documents:
            if doc.get("id") == document_id:
                return doc
        return None
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and its metadata
        """
        try:
            documents = await self.get_all_documents()
            document_to_delete = None
            
            # Find document
            for doc in documents:
                if doc.get("id") == document_id:
                    document_to_delete = doc
                    break
            
            if not document_to_delete:
                return False
            
            # Delete file
            file_path = Path(document_to_delete["file_path"])
            if file_path.exists():
                file_path.unlink()
            
            # Remove from metadata
            documents = [doc for doc in documents if doc.get("id") != document_id]
            
            # Save updated metadata
            metadata_file = self.upload_dir / "document_metadata.json"
            async with aiofiles.open(metadata_file, 'w') as f:
                import json
                await f.write(json.dumps(documents, indent=2))
            
            self.logger.info(f"Document deleted successfully: {document_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting document {document_id}: {str(e)}")
            return False
    
    async def get_documents_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get documents filtered by category
        """
        documents = await self.get_all_documents()
        return [doc for doc in documents if doc.get("category") == category]
    
    async def search_documents(self, query: str) -> List[Dict[str, Any]]:
        """
        Search documents by filename or content preview
        """
        documents = await self.get_all_documents()
        query_lower = query.lower()
        
        results = []
        for doc in documents:
            if (query_lower in doc.get("filename", "").lower() or 
                query_lower in doc.get("content_preview", "").lower()):
                results.append(doc)
        
        return results
    
    def get_supported_file_types(self) -> List[str]:
        """
        Get list of supported file extensions
        """
        return list(self.supported_types.keys())
    
    async def get_document_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about uploaded documents
        """
        documents = await self.get_all_documents()
        
        total_documents = len(documents)
        total_size = sum(doc.get("file_size", 0) for doc in documents)
        
        # Count by category
        categories = {}
        file_types = {}
        
        for doc in documents:
            category = doc.get("category", "unknown")
            file_type = doc.get("file_type", "unknown")
            
            categories[category] = categories.get(category, 0) + 1
            file_types[file_type] = file_types.get(file_type, 0) + 1
        
        return {
            "total_documents": total_documents,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "categories": categories,
            "file_types": file_types,
            "supported_types": self.get_supported_file_types()
        }
    
    def _split_text_into_chunks(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks for vector store
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence or word boundaries
            if end < len(text):
                # Look for sentence ending
                for i in range(end, max(start + chunk_size // 2, 0), -1):
                    if text[i] in '.!?':
                        end = i + 1
                        break
                else:
                    # Look for word boundary
                    for i in range(end, max(start + chunk_size // 2, 0), -1):
                        if text[i] == ' ':
                            end = i
                            break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = max(start + chunk_size - overlap, end)
        
        return chunks
    
    async def _add_to_vector_store(self, chunks: List[str], document_info: Dict[str, Any]):
        """
        Add document chunks to vector store
        """
        try:
            metadatas = []
            chunk_ids = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document_info['id']}_chunk_{i}"
                metadata = {
                    "document_id": document_info["id"],
                    "filename": document_info["filename"],
                    "category": document_info["category"],
                    "file_type": document_info["file_type"],
                    "chunk_index": i,
                    "upload_date": document_info["upload_date"]
                }
                metadatas.append(metadata)
                chunk_ids.append(chunk_id)
            
            await self.vector_store.add_documents(
                documents=chunks,
                metadata=metadatas,
                ids=chunk_ids
            )
            
            self.logger.info(f"Added {len(chunks)} chunks to vector store for document {document_info['filename']}")
            
        except Exception as e:
            self.logger.error(f"Error adding document to vector store: {str(e)}")
            raise
    
    async def _save_document_metadata(self, document_info: Dict[str, Any]):
        """
        Save document metadata to JSON file
        """
        try:
            # Load existing metadata
            metadata_list = await self._load_document_metadata()
            
            # Add new document
            metadata_list.append(document_info)
            
            # Save updated metadata
            async with aiofiles.open(self.metadata_file, 'w') as f:
                await f.write(json.dumps(metadata_list, indent=2))
                
        except Exception as e:
            self.logger.error(f"Error saving document metadata: {str(e)}")
            raise
    
    async def _load_document_metadata(self) -> List[Dict[str, Any]]:
        """
        Load document metadata from JSON file
        """
        try:
            if self.metadata_file.exists():
                async with aiofiles.open(self.metadata_file, 'r') as f:
                    content = await f.read()
                    return json.loads(content)
            return []
        except Exception as e:
            self.logger.error(f"Error loading document metadata: {str(e)}")
            return []
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and remove it from the vector store
        """
        try:
            # Load current metadata
            metadata_list = await self._load_document_metadata()
            
            # Find the document to delete
            document_to_delete = None
            updated_metadata = []
            
            for doc in metadata_list:
                if doc['id'] == document_id:
                    document_to_delete = doc
                else:
                    updated_metadata.append(doc)
            
            if not document_to_delete:
                self.logger.warning(f"Document {document_id} not found for deletion")
                return False
            
            # Delete physical file
            try:
                file_path = Path(document_to_delete['file_path'])
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                self.logger.warning(f"Could not delete physical file: {str(e)}")
            
            # Remove from vector store (delete all chunks for this document)
            try:
                if not self.vector_store.initialized:
                    await self.vector_store.initialize()
                
                # We'll need to implement this in the vector store
                await self._remove_from_vector_store(document_id)
            except Exception as e:
                self.logger.warning(f"Could not remove from vector store: {str(e)}")
            
            # Update metadata file
            async with aiofiles.open(self.metadata_file, 'w') as f:
                await f.write(json.dumps(updated_metadata, indent=2))
            
            self.logger.info(f"Document {document_id} deleted successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting document {document_id}: {str(e)}")
            return False
    
    async def _remove_from_vector_store(self, document_id: str):
        """
        Remove document chunks from vector store
        """
        try:
            # For ChromaDB, we need to delete by document_id filter
            # This is a simplified approach - in a real implementation,
            # you'd want to query for all chunks with the document_id and delete them
            self.logger.info(f"Removing document {document_id} from vector store")
            # Note: ChromaDB delete by metadata filter requires specific implementation
            # For now, we'll just log this action
        except Exception as e:
            self.logger.error(f"Error removing document from vector store: {str(e)}")
            raise