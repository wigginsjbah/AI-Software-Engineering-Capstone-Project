"""
Chat API endpoints for the RAG chatbot
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import asyncio

from app.models.chat import ChatRequest, ChatResponse, ChatHistory
from app.core.rag_engine import BusinessRAGEngine
from utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Initialize RAG engine (will be dependency injected later)
rag_engine = BusinessRAGEngine()

@router.post("/chat", response_model=ChatResponse)
async def chat_with_business_data(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint that processes user queries and returns AI responses
    with business context and data insights.
    """
    try:
        logger.info(f"Processing chat request: {request.message}")
        
        # Process the query through the RAG engine
        response = await rag_engine.process_query(
            query=request.message,
            session_id=request.session_id,
            include_sources=request.include_sources
        )
        
        return ChatResponse(
            message=response["message"],
            sources=response.get("sources", []),
            sql_query=response.get("sql_query"),
            data_insights=response.get("data_insights", {}),
            session_id=request.session_id
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/history/{session_id}", response_model=List[ChatHistory])
async def get_chat_history(session_id: str) -> List[ChatHistory]:
    """
    Retrieve chat history for a specific session
    """
    try:
        history = await rag_engine.get_chat_history(session_id)
        return history
    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/chat/history/{session_id}")
async def clear_chat_history(session_id: str) -> Dict[str, str]:
    """
    Clear chat history for a specific session
    """
    try:
        await rag_engine.clear_chat_history(session_id)
        return {"message": "Chat history cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/suggest")
async def suggest_queries() -> Dict[str, List[str]]:
    """
    Provide suggested queries based on available business data
    """
    suggestions = {
        "popular_queries": [
            "What are our top-performing products this quarter?",
            "Show me customer sentiment analysis for our latest product",
            "Which regions have the highest sales growth?",
            "What are the common complaints in recent customer reviews?",
            "Generate a sales performance report for last month"
        ],
        "data_exploration": [
            "What customer segments do we have?",
            "Show me product categories and their performance",
            "What's our customer retention rate?",
            "Which products have the lowest ratings?"
        ]
    }
    return suggestions