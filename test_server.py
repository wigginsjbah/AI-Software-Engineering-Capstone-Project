"""
Simple server test to bypass main.py startup issue
"""
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from app.api import chat, data, health, documents, database_generation, companies, admin, test_generation
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
app.include_router(database_generation.router, prefix="/api/v1/database", tags=["database-generation"])
app.include_router(companies.router, prefix="/api", tags=["companies"])
app.include_router(admin.router)
app.include_router(test_generation.router)

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main chat interface"""
    with open("frontend/templates/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/companies", response_class=HTMLResponse)
async def companies():
    """Serve the unified company and database management interface"""
    with open("frontend/templates/unified_company_manager.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/database-generator", response_class=HTMLResponse)
async def database_generator():
    """Redirect to unified company manager (legacy endpoint for compatibility)"""
    with open("frontend/templates/unified_company_manager.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")