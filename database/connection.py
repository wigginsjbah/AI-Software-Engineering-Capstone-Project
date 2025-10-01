"""
Database connection and management
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from typing import Optional

from config.settings import get_settings
from utils.logging import get_logger

Base = declarative_base()

class DatabaseManager:
    """
    Manages database connections and operations
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.engine: Optional[create_async_engine] = None
        self.session_factory: Optional[async_sessionmaker] = None
    
    async def initialize(self):
        """Initialize database connection"""
        try:
            # Convert SQLite URL to async if needed
            db_url = self.settings.DATABASE_URL
            if db_url.startswith("sqlite:///"):
                db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///")
            
            self.engine = create_async_engine(
                db_url,
                echo=self.settings.DEBUG,
                future=True
            )
            
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            self.logger.info("Database connection initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {str(e)}")
            raise
    
    async def get_session(self) -> AsyncSession:
        """Get database session"""
        if not self.session_factory:
            await self.initialize()
        return self.session_factory()
    
    async def execute_query(self, query: str, params: dict = None) -> list:
        """Execute a raw SQL query safely"""
        try:
            async with self.get_session() as session:
                result = await session.execute(text(query), params or {})
                return result.fetchall()
        except Exception as e:
            self.logger.error(f"Error executing query: {str(e)}")
            raise
    
    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()

# Global database manager instance
_db_manager: Optional[DatabaseManager] = None

def get_database() -> DatabaseManager:
    """Get database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager