"""
Context builder module
Aggregates context from database, vector store, and external sources (Tavily)
"""

from typing import Dict, List, Any, Optional
import asyncio
from tavily import TavilyClient

from database.connection import DatabaseManager
from rag.vector_store import VectorStore
from config.settings import get_settings
from utils.logging import get_logger

class ContextBuilder:
    """
    Builds comprehensive context for RAG responses by aggregating data from:
    - Business database (SQL queries)
    - Vector store (semantic search)
    - External sources via Tavily (market/industry data)
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.tavily_client = TavilyClient(api_key=self.settings.TAVILY_API_KEY)
        self.db_manager = DatabaseManager()
        self.vector_store = VectorStore()
        self.logger = get_logger(__name__)
    
    async def build_context(
        self,
        query: str,
        query_analysis: Dict[str, Any],
        session_id: str = "default",
        use_tavily: bool = False
    ) -> Dict[str, Any]:
        """
        Build comprehensive context from all available sources
        """
        try:
            context = {
                "database_results": {},
                "vector_results": [],
                "external_research": {},
                "chat_history": [],
                "metadata": {}
            }
            
            # Build context tasks concurrently
            tasks = []
            
            # Database context
            if query_analysis.get("needs_sql", False):
                tasks.append(self._get_database_context(query, query_analysis))
            
            # Vector store context
            tasks.append(self._get_vector_context(query, query_analysis))
            
            # External research context
            if use_tavily and query_analysis.get("needs_external_research", False):
                tasks.append(self._get_external_context(query, query_analysis))
            
            # Chat history context
            tasks.append(self._get_chat_context(session_id))
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Aggregate results
            if len(results) > 0 and not isinstance(results[0], Exception):
                context["database_results"] = results[0] if query_analysis.get("needs_sql") else {}
            
            vector_idx = 1 if query_analysis.get("needs_sql") else 0
            if len(results) > vector_idx and not isinstance(results[vector_idx], Exception):
                context["vector_results"] = results[vector_idx]
            
            # Handle external and chat context based on what was requested
            external_idx = len([t for t in [query_analysis.get("needs_sql"), True] if t])  # Vector is always included
            if use_tavily and len(results) > external_idx and not isinstance(results[external_idx], Exception):
                context["external_research"] = results[external_idx]
            
            chat_idx = len([t for t in [query_analysis.get("needs_sql"), True, use_tavily] if t])
            if len(results) > chat_idx and not isinstance(results[chat_idx], Exception):
                context["chat_history"] = results[chat_idx]
            
            # Add metadata
            context["metadata"] = {
                "query_type": query_analysis.get("type"),
                "entities": query_analysis.get("entities", []),
                "time_period": query_analysis.get("time_period"),
                "metrics": query_analysis.get("metrics", [])
            }
            
            self.logger.info(f"Built context with {len(context)} components")
            return context
            
        except Exception as e:
            self.logger.error(f"Error building context: {str(e)}")
            return self._default_context()
    
    async def _get_database_context(self, query: str, query_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get relevant data from business database"""
        try:
            # TODO: Implement intelligent SQL query generation
            # This should use the query analysis to generate appropriate SQL queries
            
            suggested_tables = query_analysis.get("suggested_tables", [])
            entities = query_analysis.get("entities", [])
            time_period = query_analysis.get("time_period", "all_time")
            
            database_context = {
                "tables_queried": suggested_tables,
                "results": {},
                "summary_stats": {},
                "error": None
            }
            
            # Placeholder for actual database queries
            # In implementation, this would generate and execute SQL based on query_analysis
            
            return database_context
            
        except Exception as e:
            self.logger.error(f"Error getting database context: {str(e)}")
            return {"error": str(e), "results": {}}
    
    async def _get_vector_context(self, query: str, query_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get relevant context from vector store"""
        try:
            # TODO: Implement vector similarity search
            # This should search for relevant business documents, reports, or indexed data
            
            search_results = await self.vector_store.similarity_search(
                query=query,
                k=5,  # Top 5 most relevant results
                filter_metadata={"entities": query_analysis.get("entities", [])}
            )
            
            return search_results
            
        except Exception as e:
            self.logger.error(f"Error getting vector context: {str(e)}")
            return []
    
    async def _get_external_context(self, query: str, query_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get external market/industry context using Tavily"""
        try:
            # Enhance query with business context for better Tavily results
            enhanced_query = self._enhance_query_for_tavily(query, query_analysis)
            
            # Search for external context
            search_results = self.tavily_client.search(
                query=enhanced_query,
                search_depth="advanced",
                max_results=5,
                include_domains=["business", "finance", "industry", "market"]
            )
            
            external_context = {
                "sources": search_results.get("results", []),
                "summary": search_results.get("answer", ""),
                "query_used": enhanced_query,
                "relevance_score": self._calculate_relevance_score(search_results, query_analysis)
            }
            
            return external_context
            
        except Exception as e:
            self.logger.error(f"Error getting external context via Tavily: {str(e)}")
            return {"error": str(e), "sources": []}
    
    async def _get_chat_context(self, session_id: str) -> List[Dict[str, Any]]:
        """Get relevant chat history for context"""
        try:
            # TODO: Implement chat history retrieval
            # This would get recent chat history to maintain conversation context
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting chat context: {str(e)}")
            return []
    
    def _enhance_query_for_tavily(self, query: str, query_analysis: Dict[str, Any]) -> str:
        """Enhance query with business context for better external search results"""
        entities = query_analysis.get("entities", [])
        query_type = query_analysis.get("type", "")
        
        # Add business context terms
        business_terms = []
        if "products" in entities:
            business_terms.append("product management")
        if "customers" in entities:
            business_terms.append("customer experience")
        if query_type == "trend_analysis":
            business_terms.append("market trends")
        
        enhanced_query = query
        if business_terms:
            enhanced_query += f" {' '.join(business_terms)} industry analysis"
        
        return enhanced_query
    
    def _calculate_relevance_score(self, search_results: Dict[str, Any], query_analysis: Dict[str, Any]) -> float:
        """Calculate relevance score for external search results"""
        # TODO: Implement relevance scoring algorithm
        return 0.8  # Placeholder
    
    def _default_context(self) -> Dict[str, Any]:
        """Return default context for error cases"""
        return {
            "database_results": {},
            "vector_results": [],
            "external_research": {},
            "chat_history": [],
            "metadata": {}
        }