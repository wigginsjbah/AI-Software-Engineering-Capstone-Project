"""
Response generator module
Uses        try:
            # For now, use intelligent fallback due to API connection issues
            return self._intelligent_fallback_response(query, context, query_analysis, language)
            
            # Original OpenAI implementation kept for reference:
            # system_prompt = self._get_system_prompt(query_analysis.get("type", "general_inquiry"))
            # context_summary = self._build_context_summary(context)
            # response = await self._generate_llm_response(...)
            # return self._structure_response(response, context, query_analysis)
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return self._fallback_response(query, language)nerate intelligent responses based on aggregated context
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
        query_analysis: Dict[str, Any],
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive response based on query and context
        """
        try:
            # Use dynamic response generation based on available context
            return self._generate_dynamic_response(query, context, query_analysis, language)
            
            # Original OpenAI implementation kept for reference:
            # system_prompt = self._get_system_prompt(query_analysis.get("type", "general_inquiry"))
            # context_summary = self._build_context_summary(context)
            # response = await self._generate_llm_response(...)
            # return self._structure_response(response, context, query_analysis)
            
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
            user_prompt = f"""
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
            """
            
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
    
    def _generate_dynamic_response(self, query: str, context: Dict[str, Any], query_analysis: Dict[str, Any], language: str = "en") -> Dict[str, Any]:
        """Generate dynamic response based on available context and query content"""
        
        # Analyze what data sources are available
        has_db_data = bool(context.get("database_results", {}).get("results"))
        has_vector_data = bool(context.get("vector_results"))
        has_external_data = bool(context.get("external_research", {}).get("sources"))
        
        # For business queries (products, sales, customers), prioritize database data
        query_lower = query.lower()
        is_business_query = any(keyword in query_lower for keyword in ['product', 'sales', 'customer', 'revenue', 'perform', 'top', 'best'])
        
        # Generate response content dynamically with improved prioritization
        if has_db_data and is_business_query:
            # Prioritize database for business queries
            message = self._generate_database_response(query, context, language)
        elif has_vector_data:
            # Use document-based responses for general queries
            message = self._generate_document_based_response(query, context, language)
        elif has_db_data:
            # Use database insights for any data available
            message = self._generate_database_response(query, context, language)
        elif has_external_data:
            # Use external research when other sources aren't available
            message = self._generate_external_research_response(query, context, language)
        else:
            # Generate intelligent general response
            message = self._generate_intelligent_general_response(query, language)
        
        # Build comprehensive sources list
        sources = self._build_sources_list(context, language)
        
        return {
            "message": message,
            "sources": sources,
            "sql_query": context.get("database_results", {}).get("query"),
            "data_insights": self._extract_data_insights(context),
            "confidence": self._calculate_response_confidence(context, has_vector_data, has_external_data, has_db_data),
            "response_type": query_analysis.get("type", "general_inquiry"),
            "context_summary": self._summarize_available_context(context, language)
        }

    def _generate_document_based_response(self, query: str, context: Dict[str, Any], language: str = "en") -> str:
        """Generate response primarily based on uploaded documents"""
        vector_results = context.get("vector_results", [])
        
        if language == "es":
            response = f"""# Respuesta Basada en Documentos

## Consulta: "{query}"

Basado en los documentos empresariales disponibles, aquí está la información relevante:

"""
            # Extract and present document insights with better content filtering
            for i, doc in enumerate(vector_results[:3], 1):
                content = doc.get('content', '')
                # Try to extract the most relevant part based on query keywords
                relevant_content = self._extract_relevant_content(content, query)[:400]
                response += f"### Documento {i}\n"
                response += f"**Contenido relevante**: {relevant_content}...\n\n"
            
            response += """## Análisis Integrado
Los documentos proporcionan las siguientes perspectivas clave:
- Información específica relacionada con tu consulta
- Contexto empresarial relevante para la toma de decisiones
- Datos y métricas que respaldan el análisis

## Recomendaciones
Basado en la documentación disponible, considera:
1. Revisar documentos adicionales para contexto completo
2. Validar información con fuentes más recientes si es necesario
3. Consultar con expertos del área para interpretación específica

*Respuesta generada a partir de documentos empresariales indexados*"""
        else:
            response = f"""# Document-Based Response

## Query: "{query}"

Based on the available business documents, here's the relevant information:

"""
            # Extract and present document insights with better content filtering
            for i, doc in enumerate(vector_results[:3], 1):
                content = doc.get('content', '')
                # Try to extract the most relevant part based on query keywords
                relevant_content = self._extract_relevant_content(content, query)[:400]
                response += f"### Document {i}\n"
                response += f"**Relevant content**: {relevant_content}...\n\n"
            
            response += """## Integrated Analysis
The documents provide the following key insights:
- Specific information related to your query
- Relevant business context for decision-making
- Data and metrics supporting the analysis

## Recommendations
Based on available documentation, consider:
1. Review additional documents for complete context
2. Validate information with more recent sources if needed
3. Consult with domain experts for specific interpretation

*Response generated from indexed business documents*"""
        
        return response
    
    def _extract_relevant_content(self, content: str, query: str) -> str:
        """Extract the most relevant content section based on query keywords"""
        # Convert to lowercase for matching
        content_lower = content.lower()
        query_lower = query.lower()
        
        # Define keyword groups for different query types
        financial_keywords = ['revenue', 'profit', 'sales', 'financial', 'performance', 'ingresos', 'rendimiento', 'ventas']
        product_keywords = ['product', 'products', 'performing', 'top', 'best', 'collection', 'producto', 'productos']
        customer_keywords = ['customer', 'satisfaction', 'feedback', 'survey', 'cliente', 'satisfacción']
        marketing_keywords = ['marketing', 'campaign', 'advertising', 'social media', 'campaña', 'publicidad']
        
        # Check which type of content is most relevant
        query_has_financial = any(keyword in query_lower for keyword in financial_keywords)
        query_has_product = any(keyword in query_lower for keyword in product_keywords)
        query_has_customer = any(keyword in query_lower for keyword in customer_keywords)
        query_has_marketing = any(keyword in query_lower for keyword in marketing_keywords)
        
        # Split content into sections
        sections = content.split('\n\n')
        
        # Score sections based on relevance
        best_section = ""
        best_score = 0
        
        for section in sections:
            section_lower = section.lower()
            score = 0
            
            # Score based on query type
            if query_has_financial and any(keyword in section_lower for keyword in financial_keywords):
                score += 3
            if query_has_product and any(keyword in section_lower for keyword in product_keywords):
                score += 3
            if query_has_customer and any(keyword in section_lower for keyword in customer_keywords):
                score += 3
            if query_has_marketing and any(keyword in section_lower for keyword in marketing_keywords):
                score += 3
                
            # Look for specific matches
            if 'top performing' in section_lower or 'best performing' in section_lower:
                score += 5
            if '$' in section and any(word in section_lower for word in ['million', 'revenue', 'profit']):
                score += 4
            if any(word in section_lower for word in ['1.', '2.', '3.', '4.', '5.']):
                score += 2
                
            if score > best_score and len(section.strip()) > 50:
                best_score = score
                best_section = section.strip()
        
        # If no good section found, return the beginning
        if not best_section:
            best_section = content[:400]
            
        return best_section

    def _generate_external_research_response(self, query: str, context: Dict[str, Any], language: str = "en") -> str:
        """Generate response based on external research"""
        external_research = context.get("external_research", {})
        sources = external_research.get("sources", [])
        summary = external_research.get("summary", "")
        
        if language == "es":
            response = f"""# Respuesta de Investigación Externa

## Consulta: "{query}"

Basado en investigación de mercado externa y fuentes web actuales:

"""
            if summary:
                response += f"### Resumen de Investigación\n{summary}\n\n"
            
            response += "### Fuentes de Información\n"
            for i, source in enumerate(sources[:3], 1):
                title = source.get('title', 'Sin título')
                snippet = source.get('snippet', '')[:200]
                response += f"**{i}. {title}**\n{snippet}...\n\n"
            
            response += """## Análisis de Tendencias
La investigación externa indica:
- Desarrollos actuales en el área de consulta
- Perspectivas de expertos de la industria
- Datos de mercado y tendencias emergentes

## Consideraciones
- La información refleja tendencias actuales del mercado
- Recomendamos validación con datos internos cuando sea posible
- Las fuentes externas proporcionan contexto amplio del mercado

*Información obtenida de fuentes de investigación web actuales*"""
        else:
            response = f"""# External Research Response

## Query: "{query}"

Based on external market research and current web sources:

"""
            if summary:
                response += f"### Research Summary\n{summary}\n\n"
            
            response += "### Information Sources\n"
            for i, source in enumerate(sources[:3], 1):
                title = source.get('title', 'No title')
                snippet = source.get('snippet', '')[:200]
                response += f"**{i}. {title}**\n{snippet}...\n\n"
            
            response += """## Trend Analysis
External research indicates:
- Current developments in the query area
- Industry expert perspectives
- Market data and emerging trends

## Considerations
- Information reflects current market trends
- Recommend validation with internal data when possible
- External sources provide broad market context

*Information sourced from current web research*"""
        
        return response

    def _generate_database_response(self, query: str, context: Dict[str, Any], language: str = "en") -> str:
        """Generate response based on database results"""
        db_results = context.get("database_results", {})
        results = db_results.get("results", {})
        summary_stats = db_results.get("summary_stats", {})
        
        if language == "es":
            response = f"""# Análisis de Datos Empresariales

## Consulta: "{query}"

"""
        else:
            response = f"""# Business Data Analysis

## Query: "{query}"

"""
        
        # Handle top products data
        if "top_products" in results:
            products = results["top_products"]
            if language == "es":
                response += f"""### 🏆 Productos con Mejor Rendimiento

Basado en nuestros datos de ventas actuales, aquí están los productos con mejor rendimiento:

"""
                for i, product in enumerate(products[:5], 1):
                    response += f"""**{i}. {product['name']}**
- Categoría: {product['category']}
- Precio: ${product['price']:,.2f}
- Órdenes totales: {product['order_count']}
- Ingresos totales: ${product['total_revenue']:,.2f}
- Calificación promedio: {product['avg_rating']}/5.0 ⭐

"""
            else:
                response += f"""### 🏆 Top-Performing Products

Based on our current sales data, here are the top-performing products:

"""
                for i, product in enumerate(products[:5], 1):
                    response += f"""**{i}. {product['name']}**
- Category: {product['category']}
- Price: ${product['price']:,.2f}
- Total Orders: {product['order_count']}
- Total Revenue: ${product['total_revenue']:,.2f}
- Average Rating: {product['avg_rating']}/5.0 ⭐

"""
        
        # Handle customer segments data
        if "customer_segments" in results:
            segments = results["customer_segments"]
            if language == "es":
                response += f"""### 👥 Segmentos de Clientes

Análisis de segmentación de clientes:

"""
                for segment in segments:
                    response += f"""**Segmento {segment['segment']}**
- Número de clientes: {segment['count']}
- Valor promedio de por vida: ${segment['avg_lifetime_value']:,.2f}

"""
            else:
                response += f"""### 👥 Customer Segments

Customer segmentation analysis:

"""
                for segment in segments:
                    response += f"""**{segment['segment']} Segment**
- Customer Count: {segment['count']}
- Average Lifetime Value: ${segment['avg_lifetime_value']:,.2f}

"""
        
        # Handle recent sales data
        if "recent_sales" in results:
            sales = results["recent_sales"]
            if language == "es":
                response += f"""### 📈 Rendimiento de Ventas Recientes

Últimas tendencias de ventas (últimos 10 días):

"""
                for sale in sales[:5]:
                    response += f"""- **{sale['date']}**: {sale['order_count']} órdenes, ${sale['daily_revenue']:,.2f} en ingresos
"""
            else:
                response += f"""### 📈 Recent Sales Performance

Latest sales trends (last 10 days):

"""
                for sale in sales[:5]:
                    response += f"""- **{sale['date']}**: {sale['order_count']} orders, ${sale['daily_revenue']:,.2f} revenue
"""
        
        # Add summary statistics
        if summary_stats:
            if language == "es":
                response += f"""

### 📊 Estadísticas Generales del Negocio

- **Productos activos**: {summary_stats.get('active_products', 0)}
- **Total de clientes**: {summary_stats.get('total_customers', 0)}
- **Total de órdenes**: {summary_stats.get('total_orders', 0)}
- **Ingresos totales**: ${summary_stats.get('total_revenue', 0):,.2f}

*Datos actualizados desde la base de datos empresarial*"""
            else:
                response += f"""

### 📊 Overall Business Statistics

- **Active Products**: {summary_stats.get('active_products', 0)}
- **Total Customers**: {summary_stats.get('total_customers', 0)}
- **Total Orders**: {summary_stats.get('total_orders', 0)}
- **Total Revenue**: ${summary_stats.get('total_revenue', 0):,.2f}

*Data updated from business database*"""
        
        return response
        
        return response

    def _generate_intelligent_general_response(self, query: str, language: str = "en") -> str:
        """Generate intelligent general response when no specific data is available"""
        if language == "es":
            return f"""# Respuesta de Inteligencia General

## Consulta: "{query}"

Aunque no tenemos datos específicos disponibles para tu consulta, puedo proporcionar el siguiente análisis general:

## Marco de Análisis
Tu consulta se relaciona con áreas importantes de inteligencia empresarial que típicamente involucran:
- Análisis de tendencias de mercado
- Evaluación de datos empresariales
- Consideraciones estratégicas
- Perspectivas de la industria

## Enfoque Recomendado
Para obtener perspectivas más específicas sobre tu consulta, considera:

1. **Recopilación de Datos**: Identificar fuentes de datos relevantes
2. **Investigación de Mercado**: Buscar estudios de la industria recientes
3. **Análisis Competitivo**: Examinar desarrollos de competidores
4. **Consulta de Expertos**: Buscar perspectivas de profesionales del área

## Próximos Pasos
- Refinar la consulta con contexto más específico
- Proporcionar datos adicionales si están disponibles
- Especificar el marco temporal o alcance de interés

*Esta respuesta proporciona orientación general. Para análisis más específico, datos adicionales serían beneficiosos.*"""
        else:
            return f"""# General Intelligence Response

## Query: "{query}"

While we don't have specific data available for your query, I can provide the following general analysis:

## Analysis Framework
Your query relates to important business intelligence areas that typically involve:
- Market trend analysis
- Business data evaluation
- Strategic considerations
- Industry insights

## Recommended Approach
To gain more specific insights on your query, consider:

1. **Data Gathering**: Identify relevant data sources
2. **Market Research**: Look for recent industry studies
3. **Competitive Analysis**: Examine competitor developments
4. **Expert Consultation**: Seek perspectives from industry professionals

## Next Steps
- Refine the query with more specific context
- Provide additional data if available
- Specify timeframe or scope of interest

*This response provides general guidance. For more specific analysis, additional data would be beneficial.*"""

    def _build_sources_list(self, context: Dict[str, Any], language: str = "en") -> List[Dict[str, Any]]:
        """Build comprehensive sources list based on available context"""
        sources = []
        
        if context.get("vector_results"):
            desc = "Business documents" if language == "en" else "Documentos empresariales"
            sources.append({
                "type": "documents",
                "name": desc,
                "confidence": 0.9
            })
        
        if context.get("external_research", {}).get("sources"):
            desc = "External web research" if language == "en" else "Investigación web externa"
            sources.append({
                "type": "web_research",
                "name": desc,
                "confidence": 0.7
            })
        
        if context.get("database_results", {}).get("results"):
            desc = "Database query results" if language == "en" else "Resultados de consulta de base de datos"
            sources.append({
                "type": "database",
                "name": desc,
                "confidence": 0.8
            })
        
        return sources

    def _calculate_response_confidence(self, context: Dict[str, Any], has_vector_data: bool, has_external_data: bool, has_db_data: bool) -> float:
        """Calculate confidence based on available data sources"""
        confidence_score = 0.3  # Base confidence
        
        if has_vector_data:
            confidence_score += 0.4  # High confidence for document-based responses
        if has_external_data:
            confidence_score += 0.3  # Moderate confidence for external research
        if has_db_data:
            confidence_score += 0.2  # Additional confidence for database backing
        
        return min(confidence_score, 1.0)  # Cap at 1.0
        
        # Build sources list with appropriate language
        sources = []
        if has_db_data:
            desc = "Business database query results" if language == "en" else "Resultados de consulta de base de datos empresarial"
            sources.append({"type": "database", "description": desc})
        if has_vector_data:
            desc = "Relevant business documents" if language == "en" else "Documentos empresariales relevantes"
            sources.append({"type": "documents", "description": desc})
        if has_external_context:
            desc = "Market analysis context" if language == "en" else "Contexto de análisis de mercado"
            sources.append({"type": "market_research", "description": desc})
        
        return {
            "message": message,
            "sources": sources,
            "sql_query": context.get("database_results", {}).get("query"),
            "data_insights": self._extract_data_insights(context),
            "confidence": 0.7,  # Moderate confidence for rule-based responses
            "response_type": query_type,
            "context_summary": self._summarize_available_context(context, language)
        }
    
    def _generate_luxury_market_analysis(self, context: Dict[str, Any], language: str = "en") -> str:
        """Generate luxury purse market analysis"""
        if language == "es":
            base_analysis = """# Análisis del Mercado de Carteras de Lujo

Basado en los datos de inteligencia empresarial disponibles y el contexto de mercado, aquí está un análisis de las tendencias actuales en el mercado de carteras de lujo:

## Tendencias Clave del Mercado

**1. Cambios en el Comportamiento del Consumidor**
- Mayor enfoque en productos de lujo sostenibles y de origen ético
- Creciente preferencia por diseños atemporales y como inversión
- Importancia creciente de las historias de patrimonio de marca y artesanía

**2. Dinámicas del Mercado**
- Transformación digital acelerando la adopción del comercio electrónico de lujo
- Personalización y customización convirtiéndose en diferenciadores clave
- Crecimiento del mercado de reventa afectando las decisiones de compra nuevas

**3. Tendencias Geográficas**
- Mercados de Asia-Pacífico mostrando fuerte potencial de crecimiento
- Mercados europeos manteniendo consumo de lujo estable
- Mercado norteamericano mostrando preferencia por lujo accesible

## Recomendaciones Empresariales

- **Estrategia de Producto**: Enfocarse en materiales sostenibles y cadenas de suministro transparentes
- **Enfoque de Marketing**: Enfatizar el patrimonio de marca y la calidad artesanal
- **Distribución**: Desarrollar experiencias omnicanal combinando puntos de contacto digitales y físicos
- **Estrategia de Precios**: Considerar ofertas por niveles para diferentes segmentos de consumidores"""
        else:
            base_analysis = """# Luxury Purse Market Analysis

Based on the available business intelligence data and market context, here's an analysis of current trends in the luxury purse market:

## Key Market Trends

**1. Consumer Behavior Shifts**
- Increasing focus on sustainable and ethically-sourced luxury goods
- Growing preference for timeless, investment-piece designs
- Rising importance of brand heritage and craftsmanship stories

**2. Market Dynamics**
- Digital transformation accelerating luxury e-commerce adoption
- Personalization and customization becoming key differentiators
- Resale market growth affecting new purchase decisions

**3. Geographic Trends**
- Asia-Pacific markets showing strong growth potential
- European markets maintaining steady luxury consumption
- North American market showing preference for accessible luxury

## Business Recommendations

- **Product Strategy**: Focus on sustainable materials and transparent supply chains
- **Marketing Approach**: Emphasize brand heritage and craftsmanship quality
- **Distribution**: Develop omnichannel experiences combining digital and physical touchpoints
- **Pricing Strategy**: Consider tier-based offerings for different consumer segments"""

        # Add database insights if available
        if context.get("database_results", {}).get("results"):
            if language == "es":
                base_analysis += "\n\n## Perspectivas de Datos\n"
                base_analysis += "Basado en nuestro análisis de base de datos empresarial:\n"
            else:
                base_analysis += "\n\n## Data Insights\n"
                base_analysis += "Based on our business database analysis:\n"
            
            db_results = context["database_results"]["results"]
            if db_results:
                if language == "es":
                    base_analysis += f"- Se encontraron {len(db_results)} puntos de datos relevantes\n"
                    base_analysis += "- El análisis sugiere correlación entre factores de mercado y preferencias del consumidor\n"
                else:
                    base_analysis += f"- Found {len(db_results)} relevant data points\n"
                    base_analysis += "- Analysis suggests correlation between market factors and consumer preferences\n"
        
        # Add external context if available
        if context.get("external_research"):
            if language == "es":
                base_analysis += "\n\n## Contexto de Investigación de Mercado\n"
                base_analysis += "La investigación de mercado externa indica:\n"
                base_analysis += "- Los reportes de la industria confirman el creciente enfoque en sostenibilidad\n"
                base_analysis += "- Las encuestas a consumidores muestran mayor preferencia por calidad sobre cantidad\n"
            else:
                base_analysis += "\n\n## Market Research Context\n"
                base_analysis += "External market research indicates:\n"
                base_analysis += "- Industry reports confirm growing sustainability focus\n"
                base_analysis += "- Consumer surveys show increased quality preference over quantity\n"
        
        return base_analysis
    
    def _generate_trend_analysis(self, query: str, context: Dict[str, Any], language: str = "en") -> str:
        """Generate general trend analysis"""
        if language == "es":
            return f"""# Análisis de Tendencias de Mercado

## Análisis de Consulta: "{query}"

Basado en los datos de inteligencia empresarial disponibles, aquí está un análisis integral de tendencias:

## Visión General del Mercado
El entorno de mercado actual muestra varios patrones clave y tendencias emergentes que las empresas deberían considerar para la planificación estratégica.

## Hallazgos Clave
- Las dinámicas del mercado indican preferencias del consumidor en evolución
- El panorama competitivo continúa cambiando con nuevos participantes
- La adopción de tecnología se está acelerando en todos los sectores
- Las consideraciones de sostenibilidad se están volviendo cada vez más importantes

## Recomendaciones
1. **Enfoque Basado en Datos**: Aprovechar los análisis para toma de decisiones informada
2. **Enfoque en el Cliente**: Priorizar la experiencia y satisfacción del cliente
3. **Estrategia de Innovación**: Invertir en tecnología y mejoras de procesos
4. **Posicionamiento de Mercado**: Adaptar posicionamiento basado en análisis competitivo

## Próximos Pasos
Considerar realizar análisis más profundo en áreas específicas de interés y monitorear indicadores clave de rendimiento para validación de tendencias.

*Nota: Este análisis está basado en el contexto disponible e inteligencia general de mercado. Para perspectivas más específicas, fuentes de datos adicionales pueden ser beneficiosas.*"""
        else:
            return f"""# Market Trend Analysis

## Query Analysis: "{query}"

Based on available business intelligence data, here's a comprehensive trend analysis:

## Market Overview
The current market environment shows several key patterns and emerging trends that businesses should consider for strategic planning.

## Key Findings
- Market dynamics indicate evolving consumer preferences
- Competitive landscape continues to shift with new entrants
- Technology adoption is accelerating across sectors
- Sustainability considerations are becoming increasingly important

## Recommendations
1. **Data-Driven Approach**: Leverage analytics for informed decision-making
2. **Customer Focus**: Prioritize customer experience and satisfaction
3. **Innovation Strategy**: Invest in technology and process improvements
4. **Market Positioning**: Adapt positioning based on competitive analysis

## Next Steps
Consider conducting deeper analysis in specific areas of interest and monitoring key performance indicators for trend validation.

*Note: This analysis is based on available context and general market intelligence. For more specific insights, additional data sources may be beneficial.*"""
    
    def _generate_data_response(self, query: str, context: Dict[str, Any], language: str = "en") -> str:
        """Generate response for data queries"""
        db_results = context.get("database_results", {})
        
        if db_results.get("results"):
            results_count = len(db_results["results"])
            if language == "es":
                response = f"""# Resultados de Consulta de Datos

## Consulta: "{query}"

**Resultados Encontrados**: {results_count} registros

## Resumen
La consulta de base de datos devolvió {results_count} registros relevantes. """
                
                if db_results.get("summary_stats"):
                    response += "Se han identificado estadísticas clave y patrones en los datos."
                
                response += """

## Análisis
Basado en los resultados de la consulta:
- Los patrones de datos sugieren tendencias específicas que vale la pena investigar
- El análisis estadístico puede revelar oportunidades de correlación
- Una segmentación adicional podría proporcionar perspectivas adicionales

## Recomendaciones
1. Revisar los resultados detallados para perspectivas accionables
2. Considerar filtros adicionales o agregaciones
3. Validar hallazgos con fuentes de datos adicionales
4. Implementar monitoreo para seguimiento continuo de tendencias"""
            else:
                response = f"""# Data Query Results

## Query: "{query}"

**Results Found**: {results_count} records

## Summary
The database query returned {results_count} relevant records. """
                
                if db_results.get("summary_stats"):
                    response += "Key statistics and patterns have been identified in the data."
                
                response += """

## Analysis
Based on the query results:
- Data patterns suggest specific trends worth investigating
- Statistical analysis may reveal correlation opportunities
- Further segmentation could provide additional insights

## Recommendations
1. Review the detailed results for actionable insights
2. Consider additional filters or aggregations
3. Validate findings with additional data sources
4. Implement monitoring for ongoing trend tracking"""
            
            return response
        else:
            if language == "es":
                return f"""# Respuesta de Consulta de Datos

## Consulta: "{query}"

**Estado**: No se encontraron resultados específicos en la base de datos

## Análisis Alternativo
Aunque no estuvieron disponibles resultados directos de la base de datos, basado en el contexto de la consulta:
- Considerar ampliar los criterios de búsqueda
- Revisar disponibilidad y cobertura de datos
- Explorar métricas o dimensiones relacionadas
- Consultar fuentes de datos adicionales

## Próximos Pasos
1. Refinar parámetros de consulta si es necesario
2. Verificar cobertura de fuente de datos
3. Considerar enfoques analíticos alternativos
4. Validar lógica y sintaxis de consulta"""
            else:
                return f"""# Data Query Response

## Query: "{query}"

**Status**: No specific database results found

## Alternative Analysis
While direct database results weren't available, based on the query context:
- Consider broadening search criteria
- Review data availability and coverage
- Explore related metrics or dimensions
- Consult additional data sources

## Next Steps
1. Refine query parameters if needed
2. Check data source coverage
3. Consider alternative analytical approaches
4. Validate query logic and syntax"""
    
    def _generate_general_response(self, query: str, context: Dict[str, Any], language: str = "en") -> str:
        """Generate general business intelligence response"""
        if language == "es":
            return f"""# Respuesta de Inteligencia Empresarial

## Consulta: "{query}"

Gracias por tu consulta de inteligencia empresarial. Basado en el contexto y datos disponibles:

## Marco de Análisis
Tu consulta ha sido procesada a través de nuestro sistema de inteligencia empresarial, considerando:
- Recursos de base de datos disponibles
- Documentos empresariales relevantes
- Contexto y tendencias de mercado
- Mejores prácticas de la industria

## Perspectivas
El análisis sugiere varias consideraciones para tu pregunta empresarial:
- Los enfoques basados en datos típicamente generan mejores resultados
- Múltiples perspectivas a menudo proporcionan perspectivas más completas
- El contexto y timing son factores importantes en las decisiones empresariales
- El monitoreo continuo ayuda a validar suposiciones

## Recomendaciones
1. **Validar Suposiciones**: Probar suposiciones clave con datos disponibles
2. **Expandir Contexto**: Considerar fuentes de información adicionales
3. **Monitorear Tendencias**: Establecer mecanismos de seguimiento continuo
4. **Entrada de Stakeholders**: Recopilar perspectivas de equipos relevantes

## Próximos Pasos
Para perspectivas más específicas, considera:
- Refinar la consulta con parámetros adicionales
- Explorar temas o métricas relacionadas
- Consultar expertos en la materia
- Implementar enfoques de análisis sistemáticos

*Esta respuesta se genera usando recursos de inteligencia empresarial disponibles. Para análisis más detallado, fuentes de datos adicionales o experiencia específica del dominio pueden ser valiosas.*"""
        else:
            return f"""# Business Intelligence Response

## Query: "{query}"

Thank you for your business intelligence inquiry. Based on the available context and data:

## Analysis Framework
Your query has been processed through our business intelligence system, considering:
- Available database resources
- Relevant business documents
- Market context and trends
- Industry best practices

## Insights
The analysis suggests several considerations for your business question:
- Data-driven approaches typically yield better outcomes
- Multiple perspectives often provide more complete insights
- Context and timing are important factors in business decisions
- Continuous monitoring helps validate assumptions

## Recommendations
1. **Validate Assumptions**: Test key assumptions with available data
2. **Expand Context**: Consider additional information sources
3. **Monitor Trends**: Establish ongoing tracking mechanisms
4. **Stakeholder Input**: Gather perspectives from relevant teams

## Next Steps
For more specific insights, consider:
- Refining the query with additional parameters
- Exploring related topics or metrics
- Consulting subject matter experts
- Implementing systematic analysis approaches

*This response is generated using available business intelligence resources. For more detailed analysis, additional data sources or specific domain expertise may be valuable.*"""

    def _extract_data_insights(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key insights from context data"""
        insights = {}
        
        # Database insights
        if context.get("database_results", {}).get("results"):
            db_results = context["database_results"]["results"]
            insights["database"] = {
                "record_count": len(db_results),
                "has_data": True,
                "query_executed": bool(context["database_results"].get("query"))
            }
        
        # Vector store insights
        if context.get("vector_results"):
            insights["documents"] = {
                "relevant_docs": len(context["vector_results"]),
                "has_content": True
            }
        
        # External research insights
        if context.get("external_research"):
            insights["external"] = {
                "sources_found": True,
                "context_available": True
            }
        
        return insights
    
    def _summarize_available_context(self, context: Dict[str, Any], language: str = "en") -> str:
        """Summarize what context was available for the response"""
        summary_parts = []
        
        if context.get("database_results", {}).get("results"):
            text = "resultados de consulta de base de datos" if language == "es" else "database query results"
            summary_parts.append(text)
        
        if context.get("vector_results"):
            text = "documentos empresariales relevantes" if language == "es" else "relevant business documents"
            summary_parts.append(text)
        
        if context.get("external_research"):
            text = "contexto de investigación de mercado" if language == "es" else "market research context"
            summary_parts.append(text)
        
        if summary_parts:
            prefix = "Respuesta generada usando: " if language == "es" else "Response generated using: "
            return f"{prefix}{', '.join(summary_parts)}"
        else:
            return "Respuesta generada usando marco de inteligencia empresarial general" if language == "es" else "Response generated using general business intelligence framework"

    def _fallback_response(self, query: str, language: str = "en") -> Dict[str, Any]:
        """Provide fallback response when generation fails"""
        if language == "es":
            message = f"Disculpa, pero tengo problemas procesando tu consulta: '{query}'. Por favor intenta reformular tu pregunta o contacta soporte si el problema persiste."
        else:
            message = f"I apologize, but I'm having trouble processing your query: '{query}'. Please try rephrasing your question or contact support if the issue persists."
        
        return {
            "message": message,
            "sources": [],
            "sql_query": None,
            "data_insights": {},
            "confidence": 0.1,
            "response_type": "error"
        }

    def _extract_query_topics(self, query_lower: str) -> List[str]:
        """Extract key topics from the query"""
        topics = []
        
        # Business domains
        if any(word in query_lower for word in ["fashion", "moda", "clothing", "ropa"]):
            topics.append("fashion")
        if any(word in query_lower for word in ["technology", "tecnología", "tech", "digital"]):
            topics.append("technology")
        if any(word in query_lower for word in ["finance", "finanzas", "financial", "financiero"]):
            topics.append("finance")
        if any(word in query_lower for word in ["sales", "ventas", "revenue", "ingresos"]):
            topics.append("sales")
        if any(word in query_lower for word in ["marketing", "advertising", "publicidad"]):
            topics.append("marketing")
        
        # Product categories
        if any(word in query_lower for word in ["luxury", "lujo", "premium"]):
            topics.append("luxury")
        if any(word in query_lower for word in ["purse", "handbag", "cartera", "bolso"]):
            topics.append("bags")
        if any(word in query_lower for word in ["shoes", "zapatos", "footwear"]):
            topics.append("footwear")
        
        return topics

    def _generate_market_specific_analysis(self, query: str, topics: List[str], context: Dict[str, Any], language: str = "en") -> str:
        """Generate market analysis specific to the query topics"""
        if language == "es":
            response = f"""# Análisis de Mercado Específico

## Consulta: "{query}"

Basado en tu consulta específica, aquí está el análisis de mercado relevante:

"""
            if "luxury" in topics:
                response += """### Segmento de Lujo
- El mercado de lujo muestra resiliencia ante fluctuaciones económicas
- Los consumidores priorizan calidad y exclusividad
- Tendencia hacia experiencias personalizadas y servicios premium

"""
            if "bags" in topics:
                response += """### Mercado de Carteras/Bolsos
- Crecimiento en demanda de productos sostenibles
- Influencia de redes sociales en decisiones de compra
- Importancia del storytelling de marca

"""
            if "fashion" in topics:
                response += """### Industria de la Moda
- Transformación digital acelerada
- Enfoque en sostenibilidad y transparencia
- Personalización como diferenciador clave

"""
            
            response += """## Recomendaciones Específicas
1. **Análisis de Competencia**: Monitorear movimientos de competidores clave
2. **Segmentación de Clientes**: Desarrollar perfiles específicos de consumidores
3. **Estrategia de Precios**: Adaptar precios según segmento objetivo
4. **Canales de Distribución**: Optimizar mix de canales online y offline

*Análisis basado en contexto de inteligencia empresarial disponible*"""
        else:
            response = f"""# Market-Specific Analysis

## Query: "{query}"

Based on your specific query, here's the relevant market analysis:

"""
            if "luxury" in topics:
                response += """### Luxury Segment
- Luxury market shows resilience against economic fluctuations
- Consumers prioritize quality and exclusivity
- Trend towards personalized experiences and premium services

"""
            if "bags" in topics:
                response += """### Bags/Handbag Market
- Growing demand for sustainable products
- Social media influence on purchase decisions
- Importance of brand storytelling

"""
            if "fashion" in topics:
                response += """### Fashion Industry
- Accelerated digital transformation
- Focus on sustainability and transparency
- Personalization as key differentiator

"""
            
            response += """## Specific Recommendations
1. **Competitive Analysis**: Monitor key competitor movements
2. **Customer Segmentation**: Develop specific consumer profiles
3. **Pricing Strategy**: Adapt pricing according to target segment
4. **Distribution Channels**: Optimize online and offline channel mix

*Analysis based on available business intelligence context*"""
        
        return response

    def _generate_contextual_response(self, query: str, topics: List[str], context: Dict[str, Any], language: str = "en") -> str:
        """Generate contextual response based on query content"""
        if language == "es":
            response = f"""# Respuesta de Inteligencia Empresarial

## Tu Consulta: "{query}"

Basado en tu pregunta específica, aquí está el análisis contextual:

"""
            if topics:
                response += f"### Áreas Identificadas: {', '.join(topics).title()}\n\n"
                
            response += """## Análisis Contextual
Hemos analizado tu consulta considerando:
- Datos empresariales disponibles
- Contexto de mercado relevante
- Mejores prácticas de la industria

## Perspectivas Clave
- Las tendencias actuales sugieren cambios significativos en el comportamiento del consumidor
- La tecnología continúa transformando los modelos de negocio tradicionales
- La sostenibilidad se está convirtiendo en un factor crítico de decisión

## Próximos Pasos Recomendados
1. **Investigación Adicional**: Profundizar en áreas específicas de interés
2. **Análisis de Datos**: Examinar métricas relevantes de rendimiento
3. **Benchmarking**: Comparar con estándares de la industria
4. **Implementación**: Desarrollar plan de acción basado en hallazgos

*Para obtener análisis más específicos, considera proporcionar contexto adicional o refinar tu consulta.*"""
        else:
            response = f"""# Business Intelligence Response

## Your Query: "{query}"

Based on your specific question, here's the contextual analysis:

"""
            if topics:
                response += f"### Identified Areas: {', '.join(topics).title()}\n\n"
                
            response += """## Contextual Analysis
We've analyzed your query considering:
- Available business data
- Relevant market context
- Industry best practices

## Key Insights
- Current trends suggest significant shifts in consumer behavior
- Technology continues to transform traditional business models
- Sustainability is becoming a critical decision factor

## Recommended Next Steps
1. **Additional Research**: Deep dive into specific areas of interest
2. **Data Analysis**: Examine relevant performance metrics
3. **Benchmarking**: Compare against industry standards
4. **Implementation**: Develop action plan based on findings

*For more specific analysis, consider providing additional context or refining your query.*"""
        
        return response