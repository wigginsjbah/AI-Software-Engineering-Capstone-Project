"""
Context builder module
Aggregates context from database, vector store, and external sources (Tavily/DuckDuckGo)
Supports company-specific context isolation for multi-tenant operations
Enhanced with robust schema detection and adaptive query building
"""

from typing import Dict, List, Any, Optional
import asyncio
from tavily import TavilyClient
from duckduckgo_search import DDGS

from database.connection import DatabaseManager
from database.schema_analyzer import SchemaAnalyzer, ColumnType
from rag.vector_store import VectorStore
from config.settings import get_settings
from utils.logging import get_logger
from app.services.company_manager import get_current_company_context, get_company_manager


class ContextBuilder:
    """
    Builds comprehensive context for RAG responses by aggregating data from:
    - Business database (SQL queries) - company-specific
    - Vector store (semantic search) - company-specific
    - External sources via Tavily (market/industry data)
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.tavily_client = TavilyClient(api_key=self.settings.TAVILY_API_KEY)
        self.db_manager = DatabaseManager()
        self.vector_store = VectorStore()
        self.company_manager = get_company_manager()
        self.schema_analyzer = SchemaAnalyzer()
        self.logger = get_logger(__name__)
    
    async def build_context(
        self,
        query: str,
        query_analysis: Dict[str, Any],
        session_id: str = "default",
        use_tavily: bool = False,
        company_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build comprehensive context from all available sources
        Uses company-specific data sources when company_id is provided
        """
        try:
            # Get company context
            if company_id:
                company_context = self.company_manager.get_company(company_id)
            else:
                company_context = get_current_company_context()
            
            context = {
                "database_results": {},
                "vector_results": [],
                "external_research": {},
                "chat_history": [],
                "metadata": {},
                "company_context": company_context
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
        """Get relevant data from business database - company-specific"""
        try:
            # Get company context for database targeting
            company_context = get_current_company_context()
            
            suggested_tables = query_analysis.get("suggested_tables", [])
            entities = query_analysis.get("entities", [])
            time_period = query_analysis.get("time_period", "all_time")
            
            database_context = {
                "tables_queried": suggested_tables,
                "results": {},
                "summary_stats": {},
                "error": None,
                "company_context": company_context
            }
            
            # Use company-specific database if available
            if company_context.get("database_file") and company_context.get("company_id"):
                # Create temporary database manager for company-specific DB
                from database.connection import DatabaseManager
                import os
                
                if os.path.exists(company_context["database_file"]):
                    company_db = DatabaseManager(
                        database_url=f"sqlite:///{company_context['database_file']}"
                    )
                    await company_db.initialize()
                    
                    # Use company database for queries
                    target_db = company_db
                    database_context["using_company_db"] = True
                    self.logger.info(f"Using company database: {company_context['company_name']}")
                else:
                    # Fall back to default database
                    if not self.db_manager.engine:
                        await self.db_manager.initialize()
                    target_db = self.db_manager
                    database_context["using_company_db"] = False
            else:
                # Use default database
                if not self.db_manager.engine:
                    await self.db_manager.initialize()
                target_db = self.db_manager
                database_context["using_company_db"] = False
            
            # Query products for performance/sales related queries
            if any(keyword in query.lower() for keyword in ['product', 'perform', 'sales', 'top', 'best', 'revenue']):
                try:
                    # Check if products table exists and get its schema
                    tables_query = "SELECT name FROM sqlite_master WHERE type='table' AND (name='products' OR name='Products')"
                    tables_result = await target_db.execute_query(tables_query)
                    
                    if tables_result:
                        table_name = tables_result[0][0]  # Use the actual table name (products or Products)
                        
                        # Get column information for the products table
                        pragma_query = f"PRAGMA table_info({table_name})"
                        columns_result = await target_db.execute_query(pragma_query)
                        column_names = [col[1] for col in columns_result]
                        
                        # Build dynamic query based on available columns
                        base_columns = []
                        if any(col in column_names for col in ['id', 'product_id']):
                            id_col = 'id' if 'id' in column_names else 'product_id'
                            base_columns.append(f"p.{id_col} as id")
                        
                        if any(col in column_names for col in ['name', 'product_name']):
                            name_col = 'name' if 'name' in column_names else 'product_name'
                            base_columns.append(f"p.{name_col} as name")
                        
                        if any(col in column_names for col in ['category', 'type', 'category_name', 'product_type']):
                            type_col = next((col for col in ['category', 'type', 'category_name', 'product_type'] if col in column_names), None)
                            if type_col:
                                base_columns.append(f"p.{type_col} as category")
                        
                        if 'price' in column_names:
                            base_columns.append("p.price")
                        
                        if base_columns:
                            # Check for related tables
                            order_items_exists = await target_db.execute_query(
                                "SELECT name FROM sqlite_master WHERE type='table' AND (name='order_items' OR name='Order_Items')"
                            )
                            reviews_exists = await target_db.execute_query(
                                "SELECT name FROM sqlite_master WHERE type='table' AND (name='reviews' OR name='Reviews')"
                            )
                            
                            select_clause = ", ".join(base_columns)
                            
                            # Add sales metrics if order_items table exists
                            if order_items_exists:
                                oi_table = order_items_exists[0][0]
                                select_clause += f", COUNT(oi.{id_col if id_col in ['id', 'product_id'] else 'id'}) as order_count"
                                select_clause += f", SUM(oi.price * oi.quantity) as total_revenue"
                                
                            # Add rating if reviews table exists
                            if reviews_exists:
                                r_table = reviews_exists[0][0]
                                select_clause += ", AVG(r.rating) as avg_rating"
                            
                            # Build the complete query
                            products_query = f"SELECT {select_clause} FROM {table_name} p"
                            
                            if order_items_exists:
                                oi_table = order_items_exists[0][0]
                                products_query += f" LEFT JOIN {oi_table} oi ON p.{id_col} = oi.product_id"
                            
                            if reviews_exists:
                                r_table = reviews_exists[0][0]
                                products_query += f" LEFT JOIN {r_table} r ON p.{id_col} = r.product_id"
                            
                            # Add grouping and ordering
                            group_by_cols = ", ".join([col.split(" as ")[0] for col in base_columns])
                            products_query += f" GROUP BY {group_by_cols}"
                            
                            if order_items_exists:
                                products_query += " ORDER BY total_revenue DESC, order_count DESC"
                            else:
                                products_query += f" ORDER BY p.{name_col if 'name' in column_names else 'product_name'}"
                            
                            products_query += " LIMIT 10"
                            
                            self.logger.info(f"Dynamic products query: {products_query}")
                            products_result = await target_db.execute_query(products_query)
                            
                            # Format results dynamically
                            if products_result:
                                formatted_results = []
                                for row in products_result:
                                    result_dict = {}
                                    col_idx = 0
                                    for col_def in base_columns:
                                        col_name = col_def.split(" as ")[-1] if " as " in col_def else col_def.split(".")[-1]
                                        result_dict[col_name] = row[col_idx]
                                        col_idx += 1
                                    
                                    if order_items_exists:
                                        result_dict["order_count"] = row[col_idx] or 0
                                        result_dict["total_revenue"] = row[col_idx + 1] or 0
                                        col_idx += 2
                                    
                                    if reviews_exists:
                                        result_dict["avg_rating"] = round(row[col_idx] or 0, 2) if col_idx < len(row) else 0
                                    
                                    formatted_results.append(result_dict)
                                
                                database_context["results"]["top_products"] = formatted_results
                                database_context["tables_queried"].append(table_name)
                    else:
                        # Get available tables for fallback
                        all_tables_query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '_%'"
                        available_tables = await target_db.execute_query(all_tables_query)
                        database_context["available_tables"] = [table[0] for table in available_tables]
                        
                except Exception as e:
                    self.logger.error(f"Error querying products: {e}")
                    database_context["error"] = str(e)
            
            # Query customers for customer-related queries
            if any(keyword in query.lower() for keyword in ['customer', 'segment', 'value', 'user']):
                try:
                    customers_query = """
                        SELECT segment, COUNT(*) as count, AVG(lifetime_value) as avg_value
                        FROM customers
                        GROUP BY segment
                        ORDER BY avg_value DESC
                    """
                    customers_result = await target_db.execute_query(customers_query)
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
                        SELECT DATE(created_at) as date, 
                               COUNT(*) as order_count,
                               SUM(total) as daily_revenue
                        FROM orders
                        WHERE created_at >= date('now', '-30 days')
                        GROUP BY DATE(created_at)
                        ORDER BY date DESC
                        LIMIT 10
                    """
                    sales_result = await target_db.execute_query(sales_query)
                    database_context["results"]["recent_sales"] = [
                        {"date": row[0], "order_count": row[1], "daily_revenue": round(row[2], 2)}
                        for row in sales_result
                    ]
                    database_context["tables_queried"].append("orders")
                except Exception as e:
                    self.logger.error(f"Error querying sales: {e}")
            
            # Add summary statistics
            try:
                # Get available tables first
                available_tables_query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '_%'"
                available_tables_result = await target_db.execute_query(available_tables_query)
                available_tables = [table[0].lower() for table in available_tables_result]
                
                summary_parts = []
                
                # Check for products table (case insensitive)
                products_table = None
                for table in available_tables_result:
                    if table[0].lower() in ['products', 'product']:
                        products_table = table[0]
                        break
                if products_table:
                    summary_parts.append(f"(SELECT COUNT(*) FROM {products_table}) as total_products")
                
                # Check for customers table
                customers_table = None  
                for table in available_tables_result:
                    if table[0].lower() in ['customers', 'customer']:
                        customers_table = table[0]
                        break
                if customers_table:
                    summary_parts.append(f"(SELECT COUNT(*) FROM {customers_table}) as total_customers")
                
                # Check for orders table and its total column
                orders_table = None
                for table in available_tables_result:
                    if table[0].lower() in ['orders', 'order']:
                        orders_table = table[0]
                        break
                
                if orders_table:
                    summary_parts.append(f"(SELECT COUNT(*) FROM {orders_table}) as total_orders")
                    
                    # Check what total/amount column exists in orders
                    orders_schema_query = f"PRAGMA table_info({orders_table})"
                    orders_columns_result = await target_db.execute_query(orders_schema_query)
                    orders_columns = [col[1].lower() for col in orders_columns_result]
                    
                    total_column = None
                    for possible_col in ['total', 'total_amount', 'amount', 'order_total', 'grand_total']:
                        if possible_col in orders_columns:
                            # Get the actual column name with proper case
                            for col in orders_columns_result:
                                if col[1].lower() == possible_col:
                                    total_column = col[1]
                                    break
                            break
                    
                    if total_column:
                        summary_parts.append(f"(SELECT SUM({total_column}) FROM {orders_table}) as total_revenue")
                
                if summary_parts:
                    summary_query = f"SELECT {', '.join(summary_parts)}"
                    self.logger.info(f"Dynamic summary query: {summary_query}")
                    summary_result = await target_db.execute_query(summary_query)
                    
                    if summary_result and summary_result[0]:
                        row = summary_result[0]
                        summary_stats = {}
                        
                        col_idx = 0
                        if products_table:
                            summary_stats["total_products"] = row[col_idx] or 0
                            col_idx += 1
                        if customers_table:
                            summary_stats["total_customers"] = row[col_idx] or 0
                            col_idx += 1
                        if orders_table:
                            summary_stats["total_orders"] = row[col_idx] or 0
                            col_idx += 1
                            if total_column:
                                summary_stats["total_revenue"] = round(row[col_idx] or 0, 2)
                        
                        database_context["summary_stats"] = summary_stats
                else:
                    database_context["summary_stats"] = {"note": "No standard tables found for summary statistics"}
                    
            except Exception as e:
                self.logger.error(f"Error getting summary stats: {e}")
                database_context["summary_stats"] = {"error": str(e)}
            
            return database_context
            
        except Exception as e:
            self.logger.error(f"Error getting database context: {str(e)}")
            return {"error": str(e), "results": {}}
    
    async def _get_vector_context(self, query: str, query_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get relevant context from vector store - company-specific"""
        try:
            # Get company context for vector store targeting
            company_context = get_current_company_context()
            
            # Use company-specific vector store if available
            if company_context.get("vector_store_path") and company_context.get("company_id"):
                import os
                
                if os.path.exists(company_context["vector_store_path"]):
                    # Create company-specific vector store instance
                    from rag.vector_store import VectorStore
                    company_vector_store = VectorStore(
                        persist_directory=company_context["vector_store_path"]
                    )
                    
                    # Initialize if needed
                    await company_vector_store.initialize()
                    
                    # Search company-specific documents
                    search_results = await company_vector_store.similarity_search(
                        query=query,
                        k=5  # Top 5 most relevant results
                    )
                    
                    # Add company context to results
                    for result in search_results:
                        result["company_context"] = {
                            "company_name": company_context.get("company_name"),
                            "business_type": company_context.get("business_type"),
                            "company_id": company_context.get("company_id")
                        }
                    
                    self.logger.info(f"Using company vector store: {company_context['company_name']}")
                    return search_results
            
            # Fall back to default vector store
            search_results = await self.vector_store.similarity_search(
                query=query,
                k=5  # Top 5 most relevant results
            )
            
            # Add default context marker
            for result in search_results:
                result["company_context"] = {
                    "company_name": "Default",
                    "business_type": "general",
                    "company_id": None
                }
            
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
    
    async def _get_robust_products_data(self, target_db) -> List[Dict[str, Any]]:
        """
        Get products data using robust schema analysis and adaptive queries
        """
        try:
            # Find products table with various naming conventions
            products_table = await self._find_table_by_patterns(target_db, ['products', 'product', 'items', 'catalog'])
            if not products_table:
                self.logger.warning("No products-like table found")
                return []
            
            # Analyze the table schema
            schema_info = await self._analyze_table_schema(target_db, products_table)
            if not schema_info:
                return []
            
            # Build adaptive query based on schema
            query = await self._build_adaptive_products_query(target_db, products_table, schema_info)
            if not query:
                return []
            
            self.logger.info(f"Executing robust products query: {query}")
            results = await target_db.execute_query(query)
            
            if results:
                return self._format_products_results(results, schema_info)
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error in robust products data retrieval: {e}")
            return []
    
    async def _find_table_by_patterns(self, target_db, patterns: List[str]) -> Optional[str]:
        """
        Find table that matches common naming patterns (case-insensitive)
        """
        try:
            # Get all table names
            tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
            tables_result = await target_db.execute_query(tables_query)
            
            if not tables_result:
                return None
            
            table_names = [row[0] for row in tables_result]
            
            # Look for exact matches first
            for pattern in patterns:
                for table_name in table_names:
                    if table_name.lower() == pattern.lower():
                        return table_name
            
            # Look for partial matches
            for pattern in patterns:
                for table_name in table_names:
                    if pattern.lower() in table_name.lower():
                        return table_name
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding table by patterns: {e}")
            return None
    
    async def _analyze_table_schema(self, target_db, table_name: str) -> Optional[Dict[str, Any]]:
        """
        Analyze table schema using the robust schema analyzer
        """
        try:
            pragma_query = f"PRAGMA table_info({table_name})"
            columns_result = await target_db.execute_query(pragma_query)
            
            if not columns_result:
                return None
            
            schema_info = self.schema_analyzer.analyze_table_schema(columns_result)
            schema_info['table_name'] = table_name
            
            return schema_info
            
        except Exception as e:
            self.logger.error(f"Error analyzing table schema for {table_name}: {e}")
            return None
    
    async def _build_adaptive_products_query(self, target_db, table_name: str, schema_info: Dict[str, Any]) -> Optional[str]:
        """
        Build adaptive products query based on available schema
        """
        try:
            columns = schema_info['columns']
            column_map = {col['name'].lower(): col['name'] for col in columns}
            
            # Find essential columns with flexible naming
            id_col = self._find_column_by_patterns(column_map, ['id', 'product_id', 'item_id', 'pk'])
            name_col = self._find_column_by_patterns(column_map, ['name', 'product_name', 'title', 'label'])
            price_col = self._find_column_by_patterns(column_map, ['price', 'cost', 'amount', 'value'])
            category_col = self._find_column_by_patterns(column_map, ['category', 'type', 'category_name', 'product_type', 'class'])
            
            if not id_col or not name_col:
                self.logger.warning(f"Essential columns not found in {table_name}")
                return None
            
            # Build base SELECT clause
            select_parts = [f"p.{id_col} as id", f"p.{name_col} as name"]
            
            if price_col:
                select_parts.append(f"p.{price_col} as price")
            if category_col:
                select_parts.append(f"p.{category_col} as category")
            
            # Look for related tables for sales metrics
            order_items_table = await self._find_table_by_patterns(target_db, ['order_items', 'orderitems', 'line_items', 'sales_items'])
            reviews_table = await self._find_table_by_patterns(target_db, ['reviews', 'ratings', 'feedback'])
            
            joins = []
            group_by_needed = False
            
            # Add sales metrics if order items table exists
            if order_items_table:
                oi_schema = await self._analyze_table_schema(target_db, order_items_table)
                if oi_schema:
                    oi_columns = {col['name'].lower(): col['name'] for col in oi_schema['columns']}
                    oi_product_id = self._find_column_by_patterns(oi_columns, ['product_id', 'item_id', 'id'])
                    oi_quantity = self._find_column_by_patterns(oi_columns, ['quantity', 'qty', 'amount'])
                    oi_price = self._find_column_by_patterns(oi_columns, ['price', 'unit_price', 'cost'])
                    
                    if oi_product_id:
                        joins.append(f"LEFT JOIN {order_items_table} oi ON p.{id_col} = oi.{oi_product_id}")
                        select_parts.append("COUNT(oi.*) as order_count")
                        
                        if oi_quantity and oi_price:
                            select_parts.append(f"SUM(oi.{oi_quantity} * oi.{oi_price}) as total_revenue")
                        elif oi_price:
                            select_parts.append(f"SUM(oi.{oi_price}) as total_revenue")
                        
                        group_by_needed = True
            
            # Add review metrics if reviews table exists
            if reviews_table:
                r_schema = await self._analyze_table_schema(target_db, reviews_table)
                if r_schema:
                    r_columns = {col['name'].lower(): col['name'] for col in r_schema['columns']}
                    r_product_id = self._find_column_by_patterns(r_columns, ['product_id', 'item_id', 'id'])
                    r_rating = self._find_column_by_patterns(r_columns, ['rating', 'score', 'stars'])
                    
                    if r_product_id and r_rating:
                        joins.append(f"LEFT JOIN {reviews_table} r ON p.{id_col} = r.{r_product_id}")
                        select_parts.append(f"AVG(r.{r_rating}) as avg_rating")
                        group_by_needed = True
            
            # Build the complete query
            query = f"SELECT {', '.join(select_parts)} FROM {table_name} p"
            
            if joins:
                query += " " + " ".join(joins)
            
            if group_by_needed:
                base_cols = [f"p.{id_col}", f"p.{name_col}"]
                if price_col:
                    base_cols.append(f"p.{price_col}")
                if category_col:
                    base_cols.append(f"p.{category_col}")
                query += f" GROUP BY {', '.join(base_cols)}"
                
                # Order by revenue if available, otherwise by name
                if order_items_table:
                    query += " ORDER BY total_revenue DESC, order_count DESC"
                else:
                    query += f" ORDER BY p.{name_col}"
            else:
                query += f" ORDER BY p.{name_col}"
            
            query += " LIMIT 20"
            
            return query
            
        except Exception as e:
            self.logger.error(f"Error building adaptive products query: {e}")
            return None
    
    def _find_column_by_patterns(self, column_map: Dict[str, str], patterns: List[str]) -> Optional[str]:
        """
        Find column by matching patterns (case-insensitive)
        """
        for pattern in patterns:
            if pattern.lower() in column_map:
                return column_map[pattern.lower()]
        
        # Look for partial matches
        for pattern in patterns:
            for col_lower, col_actual in column_map.items():
                if pattern.lower() in col_lower:
                    return col_actual
        
        return None
    
    def _format_products_results(self, results: List[tuple], schema_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Format products query results into standardized dictionaries
        """
        if not results:
            return []
        
        formatted_results = []
        
        # Assume first row defines the structure
        first_row = results[0]
        col_count = len(first_row)
        
        # Standard column mapping (adjust based on query structure)
        standard_cols = ['id', 'name', 'price', 'category', 'order_count', 'total_revenue', 'avg_rating']
        
        for row in results:
            result_dict = {}
            
            for i, value in enumerate(row):
                if i < len(standard_cols):
                    col_name = standard_cols[i]
                    
                    # Type-safe conversion
                    if col_name in ['order_count'] and value is not None:
                        result_dict[col_name] = int(value)
                    elif col_name in ['price', 'total_revenue', 'avg_rating'] and value is not None:
                        result_dict[col_name] = float(value)
                    else:
                        result_dict[col_name] = value
                else:
                    result_dict[f'col_{i}'] = value
            
            formatted_results.append(result_dict)
        
        return formatted_results
    
    def _default_context(self) -> Dict[str, Any]:
        """Return default context for error cases"""
        return {
            "database_results": {},
            "vector_results": [],
            "external_research": {},
            "chat_history": [],
            "metadata": {}
        }