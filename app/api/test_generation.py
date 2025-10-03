"""
Simple database generation test endpoint with progress tracking
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import uuid

from database.enhanced_llm_generator import EnhancedLLMGenerator
from database.llm_generator import DatabaseGenerationParams, BusinessType, ComplexityLevel
from utils.logging import get_logger

router = APIRouter(prefix="/api/test-generation", tags=["Database Testing"])
logger = get_logger(__name__)

# In-memory progress tracking for simple demo
progress_store: Dict[str, Dict[str, Any]] = {}


class TestGenerationRequest(BaseModel):
    business_type: str = "healthcare"
    complexity: str = "medium" 
    company_description: str = "Brinton Vision - comprehensive eye care center providing advanced ophthalmology services"
    sample_data_size: str = "medium"
    include_sample_data: bool = True


class ProgressResponse(BaseModel):
    generation_id: str
    status: str
    progress: float
    current_stage: str
    message: str
    completed: bool
    result: Optional[Dict[str, Any]] = None


@router.post("/start", response_model=Dict[str, str])
async def start_database_generation(request: TestGenerationRequest):
    """Start database generation with progress tracking"""
    try:
        generation_id = str(uuid.uuid4())
        
        # Initialize progress tracking
        progress_store[generation_id] = {
            "status": "started",
            "progress": 0.0,
            "current_stage": "initializing",
            "message": "Starting database generation...",
            "completed": False,
            "result": None,
            "error": None
        }
        
        # Start background generation
        asyncio.create_task(run_generation(generation_id, request))
        
        logger.info(f"Started database generation with ID: {generation_id}")
        
        return {
            "generation_id": generation_id,
            "status": "started",
            "message": "Database generation started. Use /progress/{generation_id} to track progress."
        }
        
    except Exception as e:
        logger.error(f"Error starting generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start generation: {str(e)}"
        )


@router.get("/progress/{generation_id}", response_model=ProgressResponse)
async def get_generation_progress(generation_id: str):
    """Get current progress of database generation"""
    try:
        if generation_id not in progress_store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Generation ID {generation_id} not found"
            )
        
        progress_data = progress_store[generation_id]
        
        return ProgressResponse(
            generation_id=generation_id,
            status=progress_data["status"],
            progress=progress_data["progress"],
            current_stage=progress_data["current_stage"],
            message=progress_data["message"],
            completed=progress_data["completed"],
            result=progress_data["result"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting progress: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get progress: {str(e)}"
        )


async def run_generation(generation_id: str, request: TestGenerationRequest):
    """Run database generation in background with progress updates"""
    try:
        # Update progress tracking function
        async def progress_callback(message: str, progress: float):
            if generation_id in progress_store:
                progress_store[generation_id].update({
                    "progress": max(0, min(100, progress)),  # Clamp between 0-100
                    "message": message,
                    "current_stage": _extract_stage_from_message(message)
                })
                logger.info(f"[{generation_id}] [{progress:5.1f}%] {message}")
        
        # Create enhanced generator
        generator = EnhancedLLMGenerator()
        
        # Set up generation parameters
        params = DatabaseGenerationParams(
            business_type=BusinessType(request.business_type),
            complexity=ComplexityLevel(request.complexity),
            company_description=request.company_description,
            specific_requirements=["Medical records", "Patient management", "Appointment scheduling"],
            include_sample_data=request.include_sample_data,
            sample_data_size=request.sample_data_size,
            additional_context="Focus on healthcare data and medical practice management"
        )
        
        # Update status
        progress_store[generation_id].update({
            "status": "generating",
            "message": "Initializing robust batch generation...",
            "current_stage": "setup"
        })
        
        # Run generation
        result = await generator.generate_database_robust(params, progress_callback)
        
        # Extract summary information
        metadata = result.get("metadata", {})
        sample_data = result.get("sample_data", {})
        
        populated_tables = len([table for table, data in sample_data.items() if data and len(data) > 0])
        total_tables = metadata.get("tables_count", 0)
        success_rate = (populated_tables / total_tables * 100) if total_tables > 0 else 0
        
        summary = {
            "total_tables": total_tables,
            "populated_tables": populated_tables,
            "success_rate": f"{success_rate:.1f}%",
            "generation_method": metadata.get("generation_method", "robust_batch"),
            "table_details": [
                {
                    "table_name": table_name,
                    "record_count": len(data) if data else 0,
                    "populated": bool(data and len(data) > 0)
                }
                for table_name, data in sample_data.items()
            ]
        }
        
        # Mark as completed
        progress_store[generation_id].update({
            "status": "completed",
            "progress": 100.0,
            "message": f"Generation completed! {populated_tables}/{total_tables} tables populated ({success_rate:.1f}% success rate)",
            "current_stage": "completed",
            "completed": True,
            "result": summary
        })
        
        logger.info(f"Generation {generation_id} completed successfully: {populated_tables}/{total_tables} tables populated")
        
    except Exception as e:
        logger.error(f"Generation {generation_id} failed: {str(e)}")
        
        # Mark as failed
        if generation_id in progress_store:
            progress_store[generation_id].update({
                "status": "failed",
                "message": f"Generation failed: {str(e)}",
                "current_stage": "error",
                "completed": True,
                "error": str(e)
            })


def _extract_stage_from_message(message: str) -> str:
    """Extract stage information from progress message"""
    message_lower = message.lower()
    
    if "schema" in message_lower:
        return "schema_generation"
    elif "analyzing" in message_lower or "planning" in message_lower:
        return "analysis"
    elif "mapping" in message_lower or "dependencies" in message_lower:
        return "dependency_mapping" 
    elif "generating" in message_lower and "data" in message_lower:
        return "data_generation"
    elif "validating" in message_lower:
        return "validation"
    elif "retrying" in message_lower:
        return "retry"
    elif "completed" in message_lower:
        return "completed"
    else:
        return "processing"


@router.get("/list-active")
async def list_active_generations():
    """List all active generation processes"""
    try:
        active_generations = [
            {
                "generation_id": gen_id,
                "status": data["status"],
                "progress": data["progress"],
                "message": data["message"],
                "completed": data["completed"]
            }
            for gen_id, data in progress_store.items()
        ]
        
        return {
            "active_generations": active_generations,
            "total_count": len(active_generations)
        }
        
    except Exception as e:
        logger.error(f"Error listing generations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list generations: {str(e)}"
        )


@router.delete("/cleanup")
async def cleanup_completed_generations():
    """Clean up completed generation processes"""
    try:
        completed_ids = [
            gen_id for gen_id, data in progress_store.items()
            if data.get("completed", False)
        ]
        
        for gen_id in completed_ids:
            del progress_store[gen_id]
        
        return {
            "cleaned_up": len(completed_ids),
            "remaining": len(progress_store)
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup: {str(e)}"
        )