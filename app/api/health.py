"""
Health check endpoints
"""

from fastapi import APIRouter
from datetime import datetime
from typing import Dict, Any

router = APIRouter()

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Business RAG Chatbot",
        "version": "1.0.0"
    }

@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check including service dependencies
    """
    # TODO: Add actual health checks for:
    # - Database connection
    # - OpenAI API
    # - Tavily API
    # - Vector store
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": {"status": "healthy", "response_time_ms": 0},
            "openai_api": {"status": "healthy", "response_time_ms": 0},
            "tavily_api": {"status": "healthy", "response_time_ms": 0},
            "vector_store": {"status": "healthy", "response_time_ms": 0}
        },
        "system": {
            "memory_usage": "N/A",
            "cpu_usage": "N/A",
            "disk_usage": "N/A"
        }
    }