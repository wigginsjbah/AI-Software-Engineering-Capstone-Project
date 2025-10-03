"""
Main RAG Engine for Business Intelligence Chatbot
Integrates OpenAI, Tavily, and business database for intelligent responses
"""

import asyncio
from typing import Dict, List, Any, Optional
import json

from openai import AsyncOpenAI
from tavily import TavilyClient
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings

from app.core.query_processor import QueryProcessor
from app.core.context_builder import ContextBuilder
from app.core.response_generator import ResponseGenerator
from rag.vector_store import VectorStore
from database.connection import DatabaseManager
from agents.orchestrator import AgentOrchestrator
from config.settings import get_settings
from utils.logging import get_logger

class BusinessRAGEngine:
    """
    Main RAG engine that orchestrates the entire business intelligence workflow
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        
        # Initialize clients
        self.openai_client = AsyncOpenAI(api_key=self.settings.OPENAI_API_KEY)
        self.tavily_client = TavilyClient(api_key=self.settings.TAVILY_API_KEY)
        
        # Initialize components
        self.query_processor = QueryProcessor()
        self.context_builder = ContextBuilder()
        self.response_generator = ResponseGenerator()
        self.vector_store = VectorStore()
        self.db_manager = DatabaseManager()
        self.agent_orchestrator = AgentOrchestrator()
        
        # Chat history storage (in production, use Redis or database)
        self.chat_history = {}
        
        self.initialized = False
    
    async def initialize(self):
        """Initialize the RAG engine and all components"""
        try:
            self.logger.info("Initializing Business RAG Engine...")
            
            # Initialize database connection
            await self.db_manager.initialize()
            
            # Initialize vector store
            await self.vector_store.initialize()
            
            # Initialize agents
            await self.agent_orchestrator.initialize()
            
            # Load and index business data
            await self._index_business_data()
            
            self.initialized = True
            self.logger.info("Business RAG Engine initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize RAG engine: {str(e)}")
            raise
    
    async def process_query(
        self, 
        query: str, 
        session_id: str = "default",
        include_sources: bool = True,
        language: str = "en",
        company_id: str = None
    ) -> Dict[str, Any]:
        """
        Main query processing pipeline with company context support
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            self.logger.info(f"Processing query: {query} (Company: {company_id or 'default'})")
            
            # Step 1: Analyze query intent and type
            query_analysis = await self.query_processor.analyze_query(query)
            
            # Step 2: Determine if we need external research (Tavily)
            needs_external_data = query_analysis.get("needs_external_research", False)
            
            # Step 3: Build context from multiple sources with company awareness
            context = await self.context_builder.build_context(
                query=query,
                query_analysis=query_analysis,
                session_id=session_id,
                use_tavily=needs_external_data,
                company_id=company_id
            )
            
            # Step 4: Generate response using appropriate agent
            response = await self.response_generator.generate_response(
                query=query,
                context=context,
                query_analysis=query_analysis,
                language=language
            )
            
            # Step 5: Store conversation history
            await self._store_chat_history(session_id, query, response)
            
            # Step 6: Format final response with company context
            formatted_response = {
                "message": response["message"],
                "sources": response.get("sources", []) if include_sources else [],
                "sql_query": response.get("sql_query"),
                "data_insights": response.get("data_insights", {}),
                "query_type": query_analysis.get("type"),
                "confidence": response.get("confidence", 0.8),
                "company_context": context.get("company_context")
            }
            
            return formatted_response
            
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            return {
                "message": "I apologize, but I encountered an error processing your request. Please try again.",
                "sources": [],
                "sql_query": None,
                "data_insights": {},
                "error": str(e)
            }
    
    async def get_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve chat history for a session"""
        return self.chat_history.get(session_id, [])
    
    async def clear_chat_history(self, session_id: str):
        """Clear chat history for a session"""
        if session_id in self.chat_history:
            del self.chat_history[session_id]
    
    async def _index_business_data(self):
        """Index business data for vector search"""
        try:
            # TODO: Implement business data indexing
            # This should:
            # 1. Extract data from database
            # 2. Create embeddings
            # 3. Store in vector database
            self.logger.info("Indexing business data...")
            pass
            
        except Exception as e:
            self.logger.error(f"Error indexing business data: {str(e)}")
            raise
    
    async def _store_chat_history(self, session_id: str, query: str, response: Dict[str, Any]):
        """Store chat interaction in history"""
        if session_id not in self.chat_history:
            self.chat_history[session_id] = []
        
        self.chat_history[session_id].append({
            "timestamp": asyncio.get_event_loop().time(),
            "query": query,
            "response": response["message"],
            "sources": response.get("sources", []),
            "sql_query": response.get("sql_query")
        })
        
        # Keep only last 50 messages per session
        if len(self.chat_history[session_id]) > 50:
            self.chat_history[session_id] = self.chat_history[session_id][-50:]