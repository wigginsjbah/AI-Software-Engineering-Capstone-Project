"""
Response generator module
Uses OpenAI to generate intelligent responses based on aggregated context
"""

from typing import Dict, List, Any
from openai import AsyncOpenAI
import json

from config.settings import get_settings
from config.prompts import get_system_prompts
from utils.logging import get_logger

class ResponseGenerator:
    """
    Generates intelligent responses using OpenAI based on context from multiple sources
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.openai_client = AsyncOpenAI(api_key=self.settings.OPENAI_API_KEY)
        self.prompts = get_system_prompts()
        self.logger = get_logger(__name__)
    
    async def generate_response(
        self,
        query: str,
        context: Dict[str, Any],
        query_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive response based on query and context
        """
        try:
            # Select appropriate prompt based on query type
            system_prompt = self._get_system_prompt(query_analysis.get("type", "general_inquiry"))
            
            # Build context summary for the LLM
            context_summary = self._build_context_summary(context)
            
            # Generate the response
            response = await self._generate_llm_response(
                system_prompt=system_prompt,
                query=query,
                context_summary=context_summary,
                query_analysis=query_analysis
            )
            
            # Post-process and structure the response
            structured_response = self._structure_response(response, context, query_analysis)
            
            return structured_response
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return self._fallback_response(query)
    
    def _get_system_prompt(self, query_type: str) -> str:
        """Get appropriate system prompt based on query type"""
        prompt_map = {
            "data_query": self.prompts["data_analyst"],
            "trend_analysis": self.prompts["trend_analyst"],
            "comparison": self.prompts["comparison_analyst"],
            "report_generation": self.prompts["report_generator"],
            "data_analysis": self.prompts["business_analyst"],
            "general_inquiry": self.prompts["general_assistant"]
        }
        
        return prompt_map.get(query_type, self.prompts["general_assistant"])
    
    def _build_context_summary(self, context: Dict[str, Any]) -> str:
        """Build a comprehensive context summary for the LLM"""
        summary_parts = []
        
        # Database results summary
        if context.get("database_results") and context["database_results"].get("results"):
            summary_parts.append("DATABASE CONTEXT:")
            db_results = context["database_results"]
            if db_results.get("summary_stats"):
                summary_parts.append(f"Summary Statistics: {json.dumps(db_results['summary_stats'], indent=2)}")
            if db_results.get("results"):
                summary_parts.append(f"Query Results: {json.dumps(db_results['results'], indent=2)[:1000]}...")
        
        # Vector store results summary
        if context.get("vector_results"):
            summary_parts.append("\\nRELEVANT DOCUMENTS:")
            for i, result in enumerate(context["vector_results"][:3]):  # Top 3 results
                summary_parts.append(f"{i+1}. {result.get('content', '')[:200]}...")
        
        # External research summary
        if context.get("external_research") and context["external_research"].get("sources"):
            summary_parts.append("\\nEXTERNAL MARKET CONTEXT:")
            ext_research = context["external_research"]
            if ext_research.get("summary"):
                summary_parts.append(f"Market Summary: {ext_research['summary']}")
            
            for source in ext_research.get("sources", [])[:2]:  # Top 2 sources
                summary_parts.append(f"- {source.get('title', '')}: {source.get('content', '')[:150]}...")
        
        # Chat history summary
        if context.get("chat_history"):
            summary_parts.append("\\nCONVERSATION HISTORY:")
            for msg in context["chat_history"][-3:]:  # Last 3 messages
                summary_parts.append(f"User: {msg.get('query', '')}")
                summary_parts.append(f"Assistant: {msg.get('response', '')[:100]}...")
        
        # Metadata summary
        if context.get("metadata"):
            metadata = context["metadata"]
            summary_parts.append("\\nQUERY METADATA:")
            summary_parts.append(f"Entities: {metadata.get('entities', [])}")
            summary_parts.append(f"Time Period: {metadata.get('time_period', 'N/A')}")
            summary_parts.append(f"Metrics: {metadata.get('metrics', [])}")
        
        return "\\n".join(summary_parts)
    
    async def _generate_llm_response(
        self,
        system_prompt: str,
        query: str,
        context_summary: str,
        query_analysis: Dict[str, Any]
    ) -> str:
        """Generate response using OpenAI"""
        try:
            user_prompt = f\"\"\"
            User Query: {query}
            
            Available Context:
            {context_summary}
            
            Query Analysis:
            - Type: {query_analysis.get('type', 'N/A')}
            - Intent: {query_analysis.get('intent', 'N/A')}
            - Entities: {query_analysis.get('entities', [])}
            - Complexity: {query_analysis.get('complexity', 'medium')}
            
            Please provide a comprehensive, data-driven response that:
            1. Directly answers the user's question
            2. Uses specific data from the context when available
            3. Provides actionable insights when appropriate
            4. Mentions data sources and confidence levels
            5. Suggests follow-up questions if relevant
            \"\"\"
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Error generating LLM response: {str(e)}")
            raise
    
    def _structure_response(
        self,
        llm_response: str,
        context: Dict[str, Any],
        query_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Structure the LLM response with additional metadata"""
        
        # Extract sources from context
        sources = []
        
        # Add database sources
        if context.get("database_results") and context["database_results"].get("tables_queried"):
            sources.extend([
                {
                    "type": "database",
                    "name": f"Business Database - {table}",
                    "confidence": 0.9
                }
                for table in context["database_results"]["tables_queried"]
            ])
        
        # Add vector store sources
        for result in context.get("vector_results", []):
            sources.append({
                "type": "document",
                "name": result.get("source", "Business Document"),
                "confidence": result.get("score", 0.8)
            })
        
        # Add external sources
        for source in context.get("external_research", {}).get("sources", []):
            sources.append({
                "type": "external",
                "name": source.get("title", "External Source"),
                "url": source.get("url", ""),
                "confidence": 0.7
            })
        
        # Extract SQL query if available
        sql_query = context.get("database_results", {}).get("sql_query")
        
        # Calculate data insights
        data_insights = self._calculate_data_insights(context, query_analysis)
        
        return {
            "message": llm_response,
            "sources": sources,
            "sql_query": sql_query,
            "data_insights": data_insights,
            "confidence": self._calculate_confidence(context, query_analysis),
            "response_type": query_analysis.get("type", "general_inquiry")
        }
    
    def _calculate_data_insights(self, context: Dict[str, Any], query_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate additional data insights"""
        insights = {}
        
        # Add database insights
        if context.get("database_results", {}).get("summary_stats"):
            insights["summary_statistics"] = context["database_results"]["summary_stats"]
        
        # Add trend insights if applicable
        if query_analysis.get("type") == "trend_analysis":
            insights["trend_direction"] = "upward"  # Placeholder
            insights["trend_confidence"] = 0.8
        
        # Add external market insights
        if context.get("external_research", {}).get("summary"):
            insights["market_context"] = context["external_research"]["summary"][:200]
        
        return insights
    
    def _calculate_confidence(self, context: Dict[str, Any], query_analysis: Dict[str, Any]) -> float:
        """Calculate overall confidence score for the response"""
        confidence_factors = []
        
        # Database availability
        if context.get("database_results", {}).get("results"):
            confidence_factors.append(0.9)
        
        # Vector results availability
        if context.get("vector_results"):
            confidence_factors.append(0.8)
        
        # External validation
        if context.get("external_research", {}).get("sources"):
            confidence_factors.append(0.7)
        
        # Query complexity
        complexity = query_analysis.get("complexity", "medium")
        complexity_score = {"low": 0.9, "medium": 0.8, "high": 0.7}.get(complexity, 0.8)
        confidence_factors.append(complexity_score)
        
        return sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5
    
    def _fallback_response(self, query: str) -> Dict[str, Any]:
        """Provide fallback response when generation fails"""
        return {
            "message": f"I apologize, but I'm having trouble processing your query: '{query}'. Please try rephrasing your question or contact support if the issue persists.",
            "sources": [],
            "sql_query": None,
            "data_insights": {},
            "confidence": 0.1,
            "response_type": "error"
        }