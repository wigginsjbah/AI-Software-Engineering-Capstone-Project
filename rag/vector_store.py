"""
Vector store implementation for RAG system
"""

import asyncio
from typing import List, Dict, Any, Optional
import numpy as np
from openai import AsyncOpenAI

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

from config.settings import get_settings
from utils.logging import get_logger

class VectorStore:
    """
    Vector store for semantic search and retrieval
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.openai_client = AsyncOpenAI(api_key=self.settings.OPENAI_API_KEY)
        self.collection = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize vector store"""
        try:
            if self.settings.VECTOR_STORE_TYPE == "chroma" and CHROMA_AVAILABLE:
                await self._init_chroma()
            else:
                await self._init_simple_store()
            
            self.initialized = True
            self.logger.info("Vector store initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize vector store: {str(e)}")
            # Fall back to simple in-memory store
            await self._init_simple_store()
            self.initialized = True
    
    async def _init_chroma(self):
        """Initialize ChromaDB"""
        self.client = chromadb.PersistentClient(
            path=self.settings.VECTOR_STORE_PATH,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        self.collection = self.client.get_or_create_collection(
            name="business_data",
            metadata={"description": "Business intelligence documents and data"}
        )
    
    async def _init_simple_store(self):
        """Initialize simple in-memory vector store"""
        self.documents = []
        self.embeddings = []
        self.metadata = []
        self.logger.info("Using simple in-memory vector store")
    
    async def add_documents(
        self,
        documents: List[str],
        metadata: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ):
        """Add documents to vector store"""
        try:
            # Generate embeddings
            embeddings = await self._generate_embeddings(documents)
            
            if self.collection:  # ChromaDB
                self.collection.add(
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadata,
                    ids=ids or [f"doc_{i}" for i in range(len(documents))]
                )
            else:  # Simple store
                self.documents.extend(documents)
                self.embeddings.extend(embeddings)
                self.metadata.extend(metadata)
            
            self.logger.info(f"Added {len(documents)} documents to vector store")
            
        except Exception as e:
            self.logger.error(f"Error adding documents: {str(e)}")
            raise
    
    async def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Perform similarity search"""
        try:
            if not self.initialized:
                await self.initialize()
            
            # Generate query embedding
            query_embedding = await self._generate_embeddings([query])
            
            if self.collection:  # ChromaDB
                results = self.collection.query(
                    query_embeddings=query_embedding,
                    n_results=k,
                    where=filter_metadata
                )
                
                return [
                    {
                        "content": doc,
                        "metadata": meta,
                        "score": 1 - dist  # Convert distance to similarity
                    }
                    for doc, meta, dist in zip(
                        results["documents"][0],
                        results["metadatas"][0],
                        results["distances"][0]
                    )
                ]
            else:  # Simple store
                if not self.embeddings:
                    return []
                
                # Calculate similarities
                query_emb = np.array(query_embedding[0])
                similarities = []
                
                for i, doc_emb in enumerate(self.embeddings):
                    similarity = np.dot(query_emb, np.array(doc_emb)) / (
                        np.linalg.norm(query_emb) * np.linalg.norm(doc_emb)
                    )
                    similarities.append((similarity, i))
                
                # Sort by similarity and return top k
                similarities.sort(reverse=True)
                
                results = []
                for sim, idx in similarities[:k]:
                    if sim >= self.settings.SIMILARITY_THRESHOLD:
                        results.append({
                            "content": self.documents[idx],
                            "metadata": self.metadata[idx],
                            "score": sim
                        })
                
                return results
            
        except Exception as e:
            self.logger.error(f"Error in similarity search: {str(e)}")
            return []
    
    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI"""
        try:
            response = await self.openai_client.embeddings.create(
                model=self.settings.EMBEDDING_MODEL,
                input=texts
            )
            
            return [embedding.embedding for embedding in response.data]
            
        except Exception as e:
            self.logger.error(f"Error generating embeddings: {str(e)}")
            # Return dummy embeddings as fallback
            return [[0.0] * 1536 for _ in texts]  # 1536 is ada-002 dimension
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        try:
            if self.collection:
                count = self.collection.count()
                return {"document_count": count, "type": "chroma"}
            else:
                return {"document_count": len(self.documents), "type": "simple"}
        except Exception as e:
            self.logger.error(f"Error getting collection stats: {str(e)}")
            return {"document_count": 0, "type": "unknown"}