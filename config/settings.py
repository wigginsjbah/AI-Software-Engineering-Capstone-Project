"""
Configuration and settings management
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # API Keys
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")
    TAVILY_API_KEY: str = Field(..., description="Tavily API key")
    
    # Database
    DATABASE_URL: str = Field(default="sqlite:///./business_data.db", description="Database connection URL")
    
    # Vector Store
    VECTOR_STORE_TYPE: str = Field(default="chroma", description="Vector store type (chroma, faiss)")
    VECTOR_STORE_PATH: str = Field(default="./data/embeddings", description="Vector store path")
    
    # AI Model Settings
    OPENAI_MODEL: str = Field(default="gpt-4", description="OpenAI model to use")
    EMBEDDING_MODEL: str = Field(default="text-embedding-ada-002", description="Embedding model")
    MAX_TOKENS: int = Field(default=1500, description="Maximum tokens for responses")
    TEMPERATURE: float = Field(default=0.3, description="LLM temperature")
    
    # Application Settings
    DEBUG: bool = Field(default=False, description="Debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    MAX_CHAT_HISTORY: int = Field(default=50, description="Maximum chat history per session")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="Requests per minute")
    RATE_LIMIT_WINDOW: int = Field(default=60, description="Rate limit window in seconds")
    
    # External Research
    TAVILY_MAX_RESULTS: int = Field(default=5, description="Maximum Tavily search results")
    ENABLE_EXTERNAL_RESEARCH: bool = Field(default=True, description="Enable external research via Tavily")
    
    # Vector Search
    VECTOR_SEARCH_K: int = Field(default=5, description="Number of vector search results")
    SIMILARITY_THRESHOLD: float = Field(default=0.7, description="Similarity threshold for vector search")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """Get application settings (singleton)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings