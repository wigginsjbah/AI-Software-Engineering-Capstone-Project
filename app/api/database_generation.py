"""
API endpoints for LLM-powered database generation
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, validator
import asyncio

from database.llm_generator import (
    LLMDatabaseGenerator, 
    DatabaseGenerationParams, 
    BusinessType, 
    ComplexityLevel
)
from database.migration_handler import DatabaseMigrationHandler
from database.data_populator import EnhancedDataPopulator, DataGenerationConfig
from utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


class DatabaseGenerationRequest(BaseModel):
    """Request model for database generation"""
    business_type: BusinessType
    complexity: ComplexityLevel
    company_description: str = Field(..., min_length=10, max_length=500)
    specific_requirements: List[str] = Field(default_factory=list, max_items=10)
    include_sample_data: bool = True
    sample_data_size: str = Field(default="medium", pattern="^(small|medium|large)$")
    additional_context: str = Field(default="", max_length=1000)
    
    @validator('specific_requirements')
    def validate_requirements(cls, v):
        if v:
            for req in v:
                if len(req.strip()) < 5:
                    raise ValueError('Each requirement must be at least 5 characters')
        return v


class SchemaPreviewRequest(BaseModel):
    """Request model for schema preview (no deployment)"""
    business_type: BusinessType
    complexity: ComplexityLevel
    company_description: str = Field(..., min_length=10, max_length=500)
    specific_requirements: List[str] = Field(default_factory=list, max_items=10)
    additional_context: str = Field(default="", max_length=1000)


class DeploymentRequest(BaseModel):
    """Request model for deploying a generated schema"""
    schema: Dict[str, Any]
    sample_data: Optional[Dict[str, List[Dict]]] = None
    backup_existing: bool = True
    validate_first: bool = True


class GenerationResponse(BaseModel):
    """Response model for database generation"""
    success: bool
    schema: Optional[Dict[str, Any]] = None
    sample_data: Optional[Dict[str, List[Dict]]] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    generation_time_seconds: Optional[float] = None


class DeploymentResponse(BaseModel):
    """Response model for deployment"""
    success: bool
    deployment_id: Optional[str] = None
    backup_info: Optional[Dict[str, Any]] = None
    tables_created: Optional[int] = None
    records_inserted: Optional[int] = None
    message: Optional[str] = None
    error: Optional[str] = None


# Store for async generation tasks
generation_tasks: Dict[str, Dict[str, Any]] = {}


@router.post("/generate/preview", response_model=GenerationResponse)
async def preview_database_schema(request: SchemaPreviewRequest):
    """
    Generate a database schema preview without deployment with improved reliability
    """
    try:
        import time
        start_time = time.time()
        
        logger.info(f"Generating schema preview for {request.business_type} business")
        
        # Validate request parameters
        if not request.company_description or len(request.company_description.strip()) < 10:
            raise HTTPException(
                status_code=400, 
                detail="Company description must be at least 10 characters long"
            )
        
        # Create generation parameters
        params = DatabaseGenerationParams(
            business_type=request.business_type,
            complexity=request.complexity,
            company_description=request.company_description,
            specific_requirements=request.specific_requirements,
            include_sample_data=False,  # Preview only, no sample data
            additional_context=request.additional_context
        )
        
        # Generate schema with retry mechanism
        generator = LLMDatabaseGenerator()
        max_retries = 2  # Fewer retries for preview since it's faster
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Schema preview attempt {attempt + 1}/{max_retries}")
                result = await generator.generate_database(params)
                
                # Validate the result
                if not result or 'schema' not in result:
                    raise ValueError("Generated result is missing schema data")
                
                if not result['schema'] or 'tables' not in result['schema']:
                    raise ValueError("Generated schema is invalid or missing tables")
                
                if len(result['schema']['tables']) == 0:
                    raise ValueError("Generated schema contains no tables")
                
                generation_time = time.time() - start_time
                logger.info(f"Schema preview generated successfully in {generation_time:.2f}s")
                
                return GenerationResponse(
                    success=True,
                    schema=result['schema'],
                    metadata=result['metadata'],
                    generation_time_seconds=round(generation_time, 2)
                )
                
            except Exception as e:
                last_error = e
                logger.warning(f"Preview attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    # Wait before retry
                    import asyncio
                    await asyncio.sleep(1)  # Shorter wait for preview
                    continue
                else:
                    break
        
        # All retries failed
        error_msg = f"Failed to generate schema preview after {max_retries} attempts. Last error: {str(last_error)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in schema preview: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"Schema preview failed: {str(e)}"
        )


@router.post("/generate/full", response_model=GenerationResponse)
async def generate_full_database(request: DatabaseGenerationRequest):
    """
    Generate a complete database with schema and sample data with improved reliability
    """
    try:
        import time
        start_time = time.time()
        
        logger.info(f"Generating full database for {request.business_type} business")
        
        # Validate request parameters
        if not request.company_description or len(request.company_description.strip()) < 10:
            raise HTTPException(
                status_code=400, 
                detail="Company description must be at least 10 characters long"
            )
        
        # Create generation parameters
        params = DatabaseGenerationParams(
            business_type=request.business_type,
            complexity=request.complexity,
            company_description=request.company_description,
            specific_requirements=request.specific_requirements,
            include_sample_data=request.include_sample_data,
            sample_data_size=request.sample_data_size,
            additional_context=request.additional_context
        )
        
        # Generate database with retry mechanism
        generator = LLMDatabaseGenerator()
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Database generation attempt {attempt + 1}/{max_retries}")
                result = await generator.generate_database(params)
                
                # Validate the result
                if not result or 'schema' not in result:
                    raise ValueError("Generated result is missing schema data")
                
                if not result['schema'] or 'tables' not in result['schema']:
                    raise ValueError("Generated schema is invalid or missing tables")
                
                if len(result['schema']['tables']) == 0:
                    raise ValueError("Generated schema contains no tables")
                
                generation_time = time.time() - start_time
                logger.info(f"Database generated successfully in {generation_time:.2f}s")
                
                return GenerationResponse(
                    success=True,
                    schema=result['schema'],
                    sample_data=result['sample_data'],
                    metadata=result['metadata'],
                    generation_time_seconds=round(generation_time, 2)
                )
                
            except Exception as e:
                last_error = e
                logger.warning(f"Generation attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    # Wait before retry
                    import asyncio
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    break
        
        # All retries failed
        error_msg = f"Failed to generate database after {max_retries} attempts. Last error: {str(last_error)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in database generation: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"Database generation failed: {str(e)}"
        )


@router.post("/generate/async")
async def generate_database_async(request: DatabaseGenerationRequest, background_tasks: BackgroundTasks):
    """
    Start asynchronous database generation for large/complex schemas
    """
    try:
        import uuid
        task_id = str(uuid.uuid4())
        
        # Store task info
        generation_tasks[task_id] = {
            'status': 'started',
            'progress': 0,
            'start_time': asyncio.get_event_loop().time(),
            'request': request.dict()
        }
        
        # Start background task
        background_tasks.add_task(
            _generate_database_background,
            task_id,
            request
        )
        
        return {
            'task_id': task_id,
            'status': 'started',
            'message': 'Database generation started in background'
        }
        
    except Exception as e:
        logger.error(f"Error starting async generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/generate/status/{task_id}")
async def get_generation_status(task_id: str):
    """
    Get status of async database generation
    """
    if task_id not in generation_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_info = generation_tasks[task_id]
    
    return {
        'task_id': task_id,
        'status': task_info['status'],
        'progress': task_info.get('progress', 0),
        'elapsed_time': round(asyncio.get_event_loop().time() - task_info['start_time'], 2),
        'result': task_info.get('result'),
        'error': task_info.get('error')
    }


@router.post("/deploy", response_model=DeploymentResponse)
async def deploy_database_schema(request: DeploymentRequest):
    """
    Deploy a generated database schema to the active database
    """
    try:
        logger.info("Starting database schema deployment")
        
        # Create migration handler
        migration_handler = DatabaseMigrationHandler()
        
        # Deploy schema
        result = await migration_handler.deploy_new_schema(
            schema=request.schema,
            sample_data=request.sample_data,
            backup_existing=request.backup_existing,
            validate_first=request.validate_first
        )
        
        if result['success']:
            return DeploymentResponse(
                success=True,
                deployment_id=result['deployment_id'],
                backup_info=result.get('backup_info'),
                tables_created=result.get('tables_created'),
                records_inserted=result.get('records_inserted'),
                message=result['message']
            )
        else:
            return DeploymentResponse(
                success=False,
                error=result.get('error', 'Deployment failed')
            )
            
    except Exception as e:
        logger.error(f"Error deploying schema: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backups")
async def list_database_backups():
    """
    List available database backups
    """
    try:
        migration_handler = DatabaseMigrationHandler()
        backups = await migration_handler.list_backups()
        
        return {
            'backups': backups,
            'count': len(backups)
        }
        
    except Exception as e:
        logger.error(f"Error listing backups: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/business-types")
async def get_business_types():
    """
    Get available business types for database generation
    """
    return {
        'business_types': [
            {
                'value': bt.value,
                'label': bt.value.replace('_', ' ').title(),
                'description': _get_business_type_description(bt)
            }
            for bt in BusinessType
        ]
    }


@router.get("/complexity-levels")
async def get_complexity_levels():
    """
    Get available complexity levels
    """
    return {
        'complexity_levels': [
            {
                'value': cl.value,
                'label': cl.value.title(),
                'description': _get_complexity_description(cl),
                'estimated_tables': _get_estimated_tables(cl)
            }
            for cl in ComplexityLevel
        ]
    }


@router.post("/validate-schema")
async def validate_schema(schema: Dict[str, Any]):
    """
    Validate a generated schema without deploying
    """
    try:
        migration_handler = DatabaseMigrationHandler()
        validation_result = await migration_handler._validate_schema(schema)
        
        return {
            'valid': validation_result['valid'],
            'errors': validation_result.get('errors', []),
            'warnings': validation_result.get('warnings', [])
        }
        
    except Exception as e:
        logger.error(f"Error validating schema: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _generate_database_background(task_id: str, request: DatabaseGenerationRequest):
    """Background task for database generation"""
    
    try:
        # Update progress
        generation_tasks[task_id]['status'] = 'generating_schema'
        generation_tasks[task_id]['progress'] = 25
        
        # Create generation parameters
        params = DatabaseGenerationParams(
            business_type=request.business_type,
            complexity=request.complexity,
            company_description=request.company_description,
            specific_requirements=request.specific_requirements,
            include_sample_data=request.include_sample_data,
            sample_data_size=request.sample_data_size,
            additional_context=request.additional_context
        )
        
        # Generate database
        generator = LLMDatabaseGenerator()
        
        generation_tasks[task_id]['status'] = 'generating_data'
        generation_tasks[task_id]['progress'] = 75
        
        result = await generator.generate_database(params)
        
        # Complete
        generation_tasks[task_id]['status'] = 'completed'
        generation_tasks[task_id]['progress'] = 100
        generation_tasks[task_id]['result'] = result
        
    except Exception as e:
        generation_tasks[task_id]['status'] = 'failed'
        generation_tasks[task_id]['error'] = str(e)
        logger.error(f"Background generation failed for task {task_id}: {str(e)}")


def _get_business_type_description(business_type: BusinessType) -> str:
    """Get description for business type"""
    descriptions = {
        BusinessType.ECOMMERCE: "Online retail with products, customers, orders, and payments",
        BusinessType.HEALTHCARE: "Medical practice with patients, appointments, and treatments",
        BusinessType.FINANCE: "Financial services with accounts, transactions, and investments",
        BusinessType.EDUCATION: "Educational institution with students, courses, and grades",
        BusinessType.MANUFACTURING: "Production company with inventory, orders, and supply chain",
        BusinessType.RETAIL: "Physical retail store with POS, inventory, and customers",
        BusinessType.TECHNOLOGY: "Tech company with projects, users, and services",
        BusinessType.HOSPITALITY: "Hotel or restaurant with bookings, guests, and services",
        BusinessType.LOGISTICS: "Shipping and logistics with routes, vehicles, and deliveries",
        BusinessType.CONSULTING: "Professional services with clients, projects, and billing",
        BusinessType.CUSTOM: "Custom business model with specific requirements"
    }
    return descriptions.get(business_type, "Custom business model")


def _get_complexity_description(complexity: ComplexityLevel) -> str:
    """Get description for complexity level"""
    descriptions = {
        ComplexityLevel.SIMPLE: "Basic business operations with core entities",
        ComplexityLevel.MEDIUM: "Standard business with moderate complexity",
        ComplexityLevel.COMPLEX: "Advanced business with comprehensive features",
        ComplexityLevel.ENTERPRISE: "Large-scale enterprise with full functionality"
    }
    return descriptions.get(complexity, "Unknown complexity")


def _get_estimated_tables(complexity: ComplexityLevel) -> str:
    """Get estimated table count for complexity"""
    estimates = {
        ComplexityLevel.SIMPLE: "3-5 tables",
        ComplexityLevel.MEDIUM: "6-12 tables",
        ComplexityLevel.COMPLEX: "13-25 tables",
        ComplexityLevel.ENTERPRISE: "25+ tables"
    }
    return estimates.get(complexity, "Unknown")