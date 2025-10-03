"""
Chat-related Pydantic models
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(..., description="User's message/query")
    session_id: str = Field(default="default", description="Chat session identifier")
    include_sources: bool = Field(default=True, description="Whether to include sources in response")
    language: str = Field(default="en", description="Language preference (en/es)")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    company_id: Optional[str] = Field(default=None, description="Specific company context to use")

class ChatSource(BaseModel):
    """Model for response sources"""
    type: str = Field(..., description="Source type (database, document, external)")
    name: str = Field(..., description="Source name")
    url: Optional[str] = Field(default=None, description="Source URL if applicable")
    confidence: float = Field(..., description="Confidence score for this source")

class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    message: str = Field(..., description="AI-generated response")
    sources: List[ChatSource] = Field(default=[], description="Sources used for the response")
    sql_query: Optional[str] = Field(default=None, description="SQL query executed (if any)")
    data_insights: Dict[str, Any] = Field(default={}, description="Additional data insights")
    session_id: str = Field(..., description="Chat session identifier")
    company_context: Optional[Dict[str, Any]] = Field(default=None, description="Company context used")
    confidence: Optional[float] = Field(default=None, description="Overall response confidence")
    response_type: Optional[str] = Field(default=None, description="Type of response generated")

class ChatHistory(BaseModel):
    """Model for chat history entries"""
    timestamp: datetime = Field(..., description="Message timestamp")
    query: str = Field(..., description="User's original query")
    response: str = Field(..., description="AI response")
    sources: List[ChatSource] = Field(default=[], description="Sources used")
    sql_query: Optional[str] = Field(default=None, description="SQL query executed")

class QuerySuggestion(BaseModel):
    """Model for query suggestions"""
    text: str = Field(..., description="Suggested query text")
    category: str = Field(..., description="Query category")
    description: str = Field(..., description="Description of what this query does")
    example_response: Optional[str] = Field(default=None, description="Example of expected response")