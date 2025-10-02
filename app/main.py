"""
Main FastAPI application entry point
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from app.api import chat, data, health, documents
from app.core.rag_engine import BusinessRAGEngine
from config.settings import get_settings

# Initialize settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Business Intelligence RAG Chatbot",
    description="AI-powered chatbot for business data analysis and insights",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Include API routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(data.router, prefix="/api/v1", tags=["data"])
app.include_router(documents.router)

# Initialize RAG engine
rag_engine = BusinessRAGEngine()

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    await rag_engine.initialize()
    print("Business RAG Chatbot initialized successfully!")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main chat interface"""
    with open("frontend/templates/index.html", "r") as f:
        return HTMLResponse(content=f.read())

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )