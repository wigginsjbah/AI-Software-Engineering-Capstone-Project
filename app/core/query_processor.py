"""
Query processing and analysis module
Determines query intent, type, and routing strategy
"""

import re
from typing import Dict, List, Any
from openai import AsyncOpenAI

from config.settings import get_settings
from utils.logging import get_logger

class QueryProcessor:
    """
    Analyzes user queries to determine intent and processing strategy
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.openai_client = AsyncOpenAI(api_key=self.settings.OPENAI_API_KEY)
        self.logger = get_logger(__name__)
        
        # Query patterns for classification
        self.sql_patterns = [
            r'\b(show|select|find|get|list|count|sum|average|group by)\b',
            r'\b(products?|customers?|orders?|reviews?|sales)\b',
            r'\b(top|best|worst|highest|lowest)\b',
            r'\b(last|previous|this|current)\s+(month|quarter|year|week)\b'
        ]
        
        self.analysis_patterns = [
            r'\b(analyze|analysis|trend|pattern|insight|correlation)\b',
            r'\b(why|how|what.*cause|explain|reason)\b',
            r'\b(predict|forecast|projection|future)\b'
        ]
        
        self.external_patterns = [
            r'\b(market|industry|competitor|benchmark|news|recent)\b',
            r'\b(external|outside|industry standard|market trend)\b'
        ]
    
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze query to determine type, intent, and processing strategy
        """
        try:
            query_lower = query.lower()
            
            # Basic pattern matching
            needs_sql = any(re.search(pattern, query_lower) for pattern in self.sql_patterns)
            needs_analysis = any(re.search(pattern, query_lower) for pattern in self.analysis_patterns)
            needs_external = any(re.search(pattern, query_lower) for pattern in self.external_patterns)
            
            # Use LLM for more sophisticated analysis
            llm_analysis = await self._llm_analyze_query(query)
            
            analysis = {
                "type": self._determine_query_type(query_lower, llm_analysis),
                "intent": llm_analysis.get("intent", "information_request"),
                "entities": self._extract_entities(query),
                "needs_sql": needs_sql or llm_analysis.get("needs_database", False),
                "needs_analysis": needs_analysis or llm_analysis.get("needs_analysis", False),
                "needs_external_research": needs_external or llm_analysis.get("needs_external", False),
                "complexity": llm_analysis.get("complexity", "medium"),
                "suggested_tables": llm_analysis.get("suggested_tables", []),
                "time_period": self._extract_time_period(query),
                "metrics": self._extract_metrics(query)
            }
            
            self.logger.info(f"Query analysis: {analysis}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing query: {str(e)}")
            return self._default_analysis()
    
    async def _llm_analyze_query(self, query: str) -> Dict[str, Any]:
        """Use LLM to analyze query intent and requirements"""
        try:
            system_prompt = \"\"\"You are a business intelligence query analyzer. Analyze the user's query and return a JSON response with:
            - intent: The main intent (data_retrieval, analysis, reporting, comparison, etc.)
            - needs_database: Boolean - does this need database queries?
            - needs_analysis: Boolean - does this need analytical processing?
            - needs_external: Boolean - does this need external market/industry data?
            - complexity: low/medium/high
            - suggested_tables: Array of likely database tables needed
            - key_entities: Important business entities mentioned
            
            Example business tables: products, customers, orders, reviews, sales_performance
            \"\"\"
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this query: {query}"}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            import json
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            self.logger.error(f"Error in LLM query analysis: {str(e)}")
            return {}
    
    def _determine_query_type(self, query_lower: str, llm_analysis: Dict) -> str:
        """Determine the primary query type"""
        if "report" in query_lower or llm_analysis.get("intent") == "reporting":
            return "report_generation"
        elif any(word in query_lower for word in ["compare", "vs", "versus", "difference"]):
            return "comparison"
        elif any(word in query_lower for word in ["trend", "pattern", "over time"]):
            return "trend_analysis"
        elif llm_analysis.get("needs_database", False):
            return "data_query"
        elif llm_analysis.get("needs_analysis", False):
            return "data_analysis"
        else:
            return "general_inquiry"
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract business entities from query"""
        entities = []
        
        # Business entity patterns
        entity_patterns = {
            "products": r"\b(product|item|sku)\w*\b",
            "customers": r"\b(customer|client|user)\w*\b",
            "orders": r"\b(order|purchase|transaction)\w*\b",
            "sales": r"\b(sale|revenue|income)\w*\b",
            "reviews": r"\b(review|rating|feedback)\w*\b"
        }
        
        for entity_type, pattern in entity_patterns.items():
            if re.search(pattern, query.lower()):
                entities.append(entity_type)
        
        return entities
    
    def _extract_time_period(self, query: str) -> str:
        """Extract time period from query"""
        time_patterns = {
            "today": r"\btoday\b",
            "yesterday": r"\byesterday\b",
            "this_week": r"\bthis week\b",
            "last_week": r"\blast week\b",
            "this_month": r"\bthis month\b",
            "last_month": r"\blast month\b",
            "this_quarter": r"\bthis quarter\b",
            "last_quarter": r"\blast quarter\b",
            "this_year": r"\bthis year\b",
            "last_year": r"\blast year\b"
        }
        
        for period, pattern in time_patterns.items():
            if re.search(pattern, query.lower()):
                return period
        
        return "all_time"
    
    def _extract_metrics(self, query: str) -> List[str]:
        """Extract metrics mentioned in query"""
        metrics = []
        
        metric_patterns = {
            "revenue": r"\b(revenue|sales|income)\b",
            "count": r"\b(count|number|total)\b",
            "average": r"\b(average|avg|mean)\b",
            "rating": r"\b(rating|score|stars)\b",
            "growth": r"\b(growth|increase|decrease)\b"
        }
        
        for metric, pattern in metric_patterns.items():
            if re.search(pattern, query.lower()):
                metrics.append(metric)
        
        return metrics
    
    def _default_analysis(self) -> Dict[str, Any]:
        """Return default analysis for error cases"""
        return {
            "type": "general_inquiry",
            "intent": "information_request",
            "entities": [],
            "needs_sql": False,
            "needs_analysis": False,
            "needs_external_research": False,
            "complexity": "medium",
            "suggested_tables": [],
            "time_period": "all_time",
            "metrics": []
        }