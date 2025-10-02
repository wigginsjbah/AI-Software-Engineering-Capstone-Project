"""
Context builder module
Aggregates context from database, vector store, and external sources (Tavily/DuckDuckGo)
"""

from typing import Dict, List, Any, Optional
import asyncio
from tavily import TavilyClient
from duckduckgo_search import DDGS

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
            suggested_tables = query_analysis.get("suggested_tables", [])
            entities = query_analysis.get("entities", [])
            time_period = query_analysis.get("time_period", "all_time")
            
            database_context = {
                "tables_queried": suggested_tables,
                "results": {},
                "summary_stats": {},
                "error": None
            }
            
            # Initialize database if needed
            if not self.db_manager.engine:
                await self.db_manager.initialize()
            
            # Query products for performance/sales related queries
            if any(keyword in query.lower() for keyword in ['product', 'perform', 'sales', 'top', 'best', 'revenue']):
                try:
                    # Get top-performing products with sales data
                    products_query = """
                        SELECT p.id, p.name, p.category, p.price, 
                               COUNT(o.id) as order_count,
                               SUM(o.total_amount) as total_revenue,
                               AVG(r.rating) as avg_rating
                        FROM products p
                        LEFT JOIN orders o ON p.id = o.product_id
                        LEFT JOIN reviews r ON p.id = r.product_id
                        WHERE p.status = 'active'
                        GROUP BY p.id, p.name, p.category, p.price
                        ORDER BY total_revenue DESC, order_count DESC
                        LIMIT 10
                    """
                    products_result = await self.db_manager.execute_query(products_query)
                    database_context["results"]["top_products"] = [
                        {
                            "id": row[0], "name": row[1], "category": row[2], 
                            "price": row[3], "order_count": row[4] or 0,
                            "total_revenue": row[5] or 0, "avg_rating": round(row[6] or 0, 2)
                        } for row in products_result
                    ]
                    database_context["tables_queried"].append("products")
                except Exception as e:
                    self.logger.error(f"Error querying products: {e}")
            
            # Query customers for customer-related queries
            if any(keyword in query.lower() for keyword in ['customer', 'segment', 'value', 'user']):
                try:
                    customers_query = """
                        SELECT segment, COUNT(*) as count, AVG(lifetime_value) as avg_value
                        FROM customers
                        GROUP BY segment
                        ORDER BY avg_value DESC
                    """
                    customers_result = await self.db_manager.execute_query(customers_query)
                    database_context["results"]["customer_segments"] = [
                        {"segment": row[0], "count": row[1], "avg_lifetime_value": round(row[2], 2)}
                        for row in customers_result
                    ]
                    database_context["tables_queried"].append("customers")
                except Exception as e:
                    self.logger.error(f"Error querying customers: {e}")
            
            # Query recent sales performance
            if any(keyword in query.lower() for keyword in ['sales', 'performance', 'revenue', 'trend']):
                try:
                    sales_query = """
                        SELECT DATE(order_date) as date, 
                               COUNT(*) as order_count,
                               SUM(total_amount) as daily_revenue
                        FROM orders
                        WHERE order_date >= date('now', '-30 days')
                        GROUP BY DATE(order_date)
                        ORDER BY date DESC
                        LIMIT 10
                    """
                    sales_result = await self.db_manager.execute_query(sales_query)
                    database_context["results"]["recent_sales"] = [
                        {"date": row[0], "order_count": row[1], "daily_revenue": round(row[2], 2)}
                        for row in sales_result
                    ]
                    database_context["tables_queried"].append("orders")
                except Exception as e:
                    self.logger.error(f"Error querying sales: {e}")
            
            # Add summary statistics
            try:
                summary_query = """
                    SELECT 
                        (SELECT COUNT(*) FROM products WHERE status = 'active') as active_products,
                        (SELECT COUNT(*) FROM customers) as total_customers,
                        (SELECT COUNT(*) FROM orders) as total_orders,
                        (SELECT SUM(total_amount) FROM orders) as total_revenue
                """
                summary_result = await self.db_manager.execute_query(summary_query)
                if summary_result:
                    row = summary_result[0]
                    database_context["summary_stats"] = {
                        "active_products": row[0],
                        "total_customers": row[1], 
                        "total_orders": row[2],
                        "total_revenue": round(row[3] or 0, 2)
                    }
            except Exception as e:
                self.logger.error(f"Error getting summary stats: {e}")
            
            return database_context
            
        except Exception as e:
            self.logger.error(f"Error getting database context: {str(e)}")
            return {"error": str(e), "results": {}}
    
    async def _get_vector_context(self, query: str, query_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get relevant context from vector store"""
        try:
            # Search for relevant business documents without complex filters for now
            search_results = await self.vector_store.similarity_search(
                query=query,
                k=5  # Top 5 most relevant results
            )
            
            return search_results
            
        except Exception as e:
            self.logger.error(f"Error getting vector context: {str(e)}")
            return []
    
    def _get_external_context(self, query: str, query_analysis: Dict[str, Any] = None) -> str:
        """Get external context from Tavily API with fallbacks"""
        # For now, skip external APIs due to SSL issues and provide intelligent fallback
        return self._get_intelligent_fallback_context(query)
        
        # Original code kept for reference when SSL issues are resolved:
        # try:
        #     client = TavilyClient(api_key=self.settings.TAVILY_API_KEY)
        #     response = client.search(query=query, max_results=5)
        #     # ... (original Tavily implementation)
        # except Exception as e:
        #     self.logger.error(f"Error getting external context via Tavily: {e}")
        #     return self._get_duckduckgo_context(query)
    
    def _get_intelligent_fallback_context(self, query: str) -> str:
        """Provide intelligent context without external APIs"""
        # Extract key terms and provide relevant business context
        query_lower = query.lower()
        
        # Market analysis contexts
        if any(term in query_lower for term in ['market', 'trend', 'industry']):
            if any(term in query_lower for term in ['luxury', 'premium', 'high-end']):
                return """**Luxury Market Analysis Context**

Key Factors for Luxury Market Trends:
• Consumer spending patterns and disposable income levels
• Brand positioning and exclusivity strategies
• Economic indicators affecting discretionary spending
• Digital transformation and e-commerce adoption
• Sustainability and ethical consumption trends
• Geographic market expansion and demographics
• Seasonal variations and cultural influences
• Competitive landscape and market consolidation

For luxury goods analysis, consider price elasticity, brand perception, and consumer psychology factors."""
            
            elif any(term in query_lower for term in ['technology', 'tech', 'software', 'digital']):
                return """**Technology Market Analysis Context**

Key Technology Market Factors:
• Innovation cycles and technological disruption
• Market adoption rates and user engagement metrics
• Regulatory environment and compliance requirements
• Investment patterns and venture capital trends
• Competitive dynamics and market consolidation
• Infrastructure development and scalability
• Security and privacy considerations
• Integration capabilities and ecosystem effects

Consider technology maturity, market penetration, and development lifecycle stages."""
            
            else:
                return """**General Market Analysis Context**

Standard Market Analysis Framework:
• Supply and demand dynamics
• Competitive landscape assessment
• Consumer behavior and preferences
• Economic and regulatory environment
• Market size, growth rate, and segmentation
• Distribution channels and value chain
• Risk factors and market barriers
• Future opportunities and challenges

Apply appropriate analytical models based on industry characteristics."""
        
        # Financial analysis contexts
        elif any(term in query_lower for term in ['revenue', 'profit', 'financial', 'sales']):
            return """**Financial Analysis Context**

Financial Performance Indicators:
• Revenue growth and profitability trends
• Market share and competitive positioning
• Cost structure and operational efficiency
• Cash flow and liquidity management
• Return on investment and asset utilization
• Debt levels and financial stability
• Seasonal patterns and cyclical variations
• Forward-looking guidance and projections

Focus on both historical trends and predictive indicators."""
        
        # Default business context
        else:
            return f"""**Business Intelligence Context**

Query Analysis: "{query}"

General Business Considerations:
• Market dynamics and competitive environment
• Customer segments and behavioral patterns
• Operational efficiency and performance metrics
• Strategic positioning and growth opportunities
• Risk assessment and mitigation strategies
• Data-driven decision making frameworks
• Industry best practices and benchmarking
• Technology enablers and innovation factors

Recommend focusing on quantitative metrics and qualitative insights for comprehensive analysis."""
    
    def _get_duckduckgo_context(self, query: str) -> str:
        """Get context from DuckDuckGo search as fallback"""
        try:
            # Try the newer ddgs package first
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS
            
            # Search for relevant information with SSL workaround
            import ssl
            import urllib3
            
            # Disable SSL warnings for this search
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
            
            if not results:
                return "No external context available from search"
            
            # Format results into context
            context_parts = []
            for result in results:
                title = result.get('title', 'No title')
                body = result.get('body', 'No description')
                url = result.get('href', '')
                
                context_parts.append(f"**{title}**\n{body}\nSource: {url}\n")
            
            return "\n".join(context_parts)
        
        except Exception as e:
            self.logger.error(f"Error getting DuckDuckGo context: {e}")
            # Fallback to basic market trends info
            return f"Market trends analysis for: {query}\n\nGeneral business context: This query relates to market trends and consumer behavior analysis. Consider factors like market demand, consumer preferences, economic conditions, and industry developments."
    
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