"""
API endpoints for company management
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse

from app.models.company import (
    CompanyCreateRequest,
    CompanyUpdateRequest,
    CompanyResponse,
    CompanyListResponse,
    CompanyStatsResponse,
    CompanySwitchRequest,
    CompanyDeleteResponse,
    CompanyContextResponse,
    CompanyDatabaseGenerationRequest
)
from app.services.company_manager import get_company_manager, CompanyProfile
from database.llm_generator import LLMDatabaseGenerator, DatabaseGenerationParams
from database.enhanced_llm_generator import EnhancedLLMGenerator
from database.migration_handler import DatabaseMigrationHandler
from utils.logging import get_logger
import sqlite3
import os
from pathlib import Path

router = APIRouter(prefix="/companies", tags=["companies"])
logger = get_logger(__name__)


def get_manager():
    """Dependency to get company manager"""
    return get_company_manager()


async def deploy_to_company_database(database_file: str, schema: Dict[str, Any], sample_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Deploy schema and data to a company-specific database"""
    try:
        logger.info(f"Deploying database to: {database_file}")
        logger.info(f"Schema structure: {type(schema)} with keys: {list(schema.keys()) if schema else 'None'}")
        
        # Ensure database file directory exists
        db_path = Path(database_file)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to the specific database
        conn = sqlite3.connect(database_file)
        cursor = conn.cursor()
        
        tables_created = 0
        records_inserted = 0
        
        # Deploy schema
        if 'tables' in schema:
            tables_list = schema['tables']
            logger.info(f"Found {len(tables_list) if isinstance(tables_list, list) else 'unknown'} tables to create")
            
            if isinstance(tables_list, list):
                # Handle list format from _parse_schema
                for table_obj in tables_list:
                    try:
                        # Create table using SQL from parsed schema
                        table_name = table_obj.get('name', '')
                        create_sql = table_obj.get('sql', '')
                        logger.info(f"Creating table '{table_name}' with SQL: {create_sql[:100]}...")
                        if create_sql and table_name:
                            cursor.execute(create_sql)
                            tables_created += 1
                            logger.info(f"Created table: {table_name}")
                    except Exception as e:
                        logger.error(f"Error creating table {table_name}: {str(e)}")
            else:
                # Handle dictionary format (legacy)
                for table_name, table_def in tables_list.items():
                    try:
                        # Create table
                        create_sql = table_def.get('create_sql', '')
                        if create_sql:
                            cursor.execute(create_sql)
                            tables_created += 1
                            logger.info(f"Created table: {table_name}")
                    except Exception as e:
                        logger.error(f"Error creating table {table_name}: {str(e)}")
        else:
            logger.warning("No 'tables' key found in schema")
        
        # Deploy sample data
        if sample_data:
            logger.info(f"Deploying sample data for {len(sample_data)} tables")
            for table_name, records in sample_data.items():
                if records and isinstance(records, list):
                    try:
                        logger.info(f"Inserting {len(records)} records into {table_name}")
                        # Get table columns
                        cursor.execute(f"PRAGMA table_info({table_name})")
                        columns = [col[1] for col in cursor.fetchall()]
                        
                        # Insert records
                        for record in records:
                            if isinstance(record, dict):
                                # Filter record to only include existing columns
                                filtered_record = {k: v for k, v in record.items() if k in columns}
                                if filtered_record:
                                    placeholders = ', '.join(['?' for _ in filtered_record])
                                    columns_str = ', '.join(filtered_record.keys())
                                    values = list(filtered_record.values())
                                    
                                    insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                                    cursor.execute(insert_sql, values)
                                    records_inserted += 1
                                    
                    except Exception as e:
                        logger.error(f"Error inserting data into {table_name}: {str(e)}")
        else:
            logger.info("No sample data to deploy")
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'tables_created': tables_created,
            'records_inserted': records_inserted,
            'message': f'Successfully deployed schema with {tables_created} tables and {records_inserted} records'
        }
        
    except Exception as e:
        logger.error(f"Error deploying to company database: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'tables_created': 0,
            'records_inserted': 0
        }


@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    request: CompanyCreateRequest,
    manager = Depends(get_manager)
) -> CompanyResponse:
    """Create a new company profile"""
    try:
        # Create company profile
        profile = manager.create_company(
            name=request.name,
            business_type=request.business_type,
            complexity=request.complexity,
            company_description=request.company_description,
            additional_metadata=request.additional_metadata
        )
        
        # Initialize database
        if not manager.initialize_company_database(profile.id):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initialize company database"
            )
        
        logger.info(f"Created company: {profile.name} ({profile.id})")
        
        return CompanyResponse(
            id=profile.id,
            name=profile.name,
            business_type=profile.business_type,
            complexity=profile.complexity,
            company_description=profile.company_description,
            database_file=profile.database_file,
            vector_store_path=profile.vector_store_path,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
            is_active=profile.is_active,
            metadata=profile.metadata
        )
        
    except Exception as e:
        logger.error(f"Error creating company: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create company: {str(e)}"
        )


@router.get("/", response_model=CompanyListResponse)
async def list_companies(manager = Depends(get_manager)) -> CompanyListResponse:
    """List all company profiles"""
    try:
        companies = manager.list_companies()
        current_company = manager.get_current_company()
        
        company_responses = [
            CompanyResponse(
                id=company.id,
                name=company.name,
                business_type=company.business_type,
                complexity=company.complexity,
                company_description=company.company_description,
                database_file=company.database_file,
                vector_store_path=company.vector_store_path,
                created_at=company.created_at,
                updated_at=company.updated_at,
                is_active=company.is_active,
                metadata=company.metadata
            )
            for company in companies
        ]
        
        return CompanyListResponse(
            companies=company_responses,
            total=len(company_responses),
            current_company_id=current_company.id if current_company else None
        )
        
    except Exception as e:
        logger.error(f"Error listing companies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list companies: {str(e)}"
        )


@router.get("/current", response_model=CompanyContextResponse)
async def get_current_company_context(manager = Depends(get_manager)) -> CompanyContextResponse:
    """Get current company context"""
    try:
        from app.services.company_manager import get_current_company_context
        context = get_current_company_context()
        
        return CompanyContextResponse(**context)
        
    except Exception as e:
        logger.error(f"Error getting current company context: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get current company context: {str(e)}"
        )


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: str,
    manager = Depends(get_manager)
) -> CompanyResponse:
    """Get specific company by ID"""
    try:
        company = manager.get_company(company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company with ID {company_id} not found"
            )
        
        return CompanyResponse(
            id=company.id,
            name=company.name,
            business_type=company.business_type,
            complexity=company.complexity,
            company_description=company.company_description,
            database_file=company.database_file,
            vector_store_path=company.vector_store_path,
            created_at=company.created_at,
            updated_at=company.updated_at,
            is_active=company.is_active,
            metadata=company.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get company: {str(e)}"
        )


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str,
    request: CompanyUpdateRequest,
    manager = Depends(get_manager)
) -> CompanyResponse:
    """Update company information"""
    try:
        # Check if company exists
        company = manager.get_company(company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company with ID {company_id} not found"
            )
        
        # Prepare updates
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.company_description is not None:
            updates["company_description"] = request.company_description
        if request.additional_metadata is not None:
            updates["metadata"] = request.additional_metadata
        
        # Update company
        if not manager.update_company(company_id, updates):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update company"
            )
        
        # Get updated company
        updated_company = manager.get_company(company_id)
        
        return CompanyResponse(
            id=updated_company.id,
            name=updated_company.name,
            business_type=updated_company.business_type,
            complexity=updated_company.complexity,
            company_description=updated_company.company_description,
            database_file=updated_company.database_file,
            vector_store_path=updated_company.vector_store_path,
            created_at=updated_company.created_at,
            updated_at=updated_company.updated_at,
            is_active=updated_company.is_active,
            metadata=updated_company.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating company: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update company: {str(e)}"
        )


@router.post("/switch", response_model=CompanyContextResponse)
async def switch_company(
    request: CompanySwitchRequest,
    manager = Depends(get_manager)
) -> CompanyContextResponse:
    """Switch to different company context"""
    try:
        if not manager.set_current_company(request.company_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company with ID {request.company_id} not found"
            )
        
        # Get updated context
        from app.services.company_manager import get_current_company_context
        context = get_current_company_context()
        
        logger.info(f"Switched to company: {context['company_name']} ({request.company_id})")
        
        return CompanyContextResponse(**context)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching company: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to switch company: {str(e)}"
        )


@router.get("/{company_id}/stats", response_model=CompanyStatsResponse)
async def get_company_stats(
    company_id: str,
    manager = Depends(get_manager)
) -> CompanyStatsResponse:
    """Get company statistics and metadata"""
    try:
        stats = manager.get_company_stats(company_id)
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company with ID {company_id} not found"
            )
        
        profile_data = stats["profile"]
        return CompanyStatsResponse(
            profile=CompanyResponse(**profile_data),
            database_exists=stats["database_exists"],
            database_size_mb=stats["database_size_mb"],
            table_count=stats["table_count"],
            record_count=stats["record_count"],
            vector_store_exists=stats["vector_store_exists"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get company stats: {str(e)}"
        )


@router.delete("/{company_id}", response_model=CompanyDeleteResponse)
async def delete_company(
    company_id: str,
    manager = Depends(get_manager)
) -> CompanyDeleteResponse:
    """Delete company and all associated data"""
    try:
        # Get company info before deletion
        company = manager.get_company(company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company with ID {company_id} not found"
            )
        
        company_name = company.name
        
        # Delete company
        if not manager.delete_company(company_id):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete company"
            )
        
        logger.info(f"Deleted company: {company_name} ({company_id})")
        
        return CompanyDeleteResponse(
            success=True,
            message=f"Company '{company_name}' has been successfully deleted",
            deleted_company_id=company_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting company: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete company: {str(e)}"
        )


# Database generation endpoints for specific companies
@router.post("/{company_id}/generate-database")
async def generate_company_database(
    company_id: str,
    request: CompanyDatabaseGenerationRequest,
    manager = Depends(get_manager)
):
    """Generate database schema and data for specific company"""
    try:
        # Get company
        company = manager.get_company(company_id)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company with ID {company_id} not found"
            )
        
        # Generate database using company context with ROBUST batch processing
        from database.llm_generator import BusinessType, ComplexityLevel, DatabaseGenerationParams
        generator = EnhancedLLMGenerator()  # Use enhanced generator with robust batch processing
        
        # Progress tracking
        progress_messages = []
        
        async def progress_callback(message: str, progress: float):
            progress_messages.append({"message": message, "progress": progress})
            logger.info(f"[{progress:5.1f}%] {message}")
        
        # Create generation parameters
        generation_params = DatabaseGenerationParams(
            business_type=BusinessType(company.business_type),
            complexity=ComplexityLevel(company.complexity),
            company_description=company.company_description,
            specific_requirements=[request.business_requirements] if request.business_requirements else [],
            include_sample_data=request.include_sample_data,
            sample_data_size="medium",
            additional_context=""
        )
        
        logger.info(f"Starting ROBUST database generation for {company.name} ({company.business_type})")
        result = await generator.generate_database_robust(generation_params, progress_callback)
        
        if not result or 'schema' not in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database generation failed: Invalid result format"
            )
        
        # Deploy to company database
        deployment_result = await deploy_to_company_database(
            company.database_file,
            result['schema'],
            result.get('sample_data')
        )
        
        if not deployment_result.get('success', False):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database deployment failed: {deployment_result.get('error', 'Unknown error')}"
            )
        
        # Create a copy in the project root for easy visualization
        try:
            import shutil
            import os
            
            source_db = company.database_file
            root_db_name = f"{company.name.replace(' ', '_').lower()}_database.db"
            root_db_path = os.path.join(os.getcwd(), root_db_name)
            
            if os.path.exists(source_db):
                shutil.copy2(source_db, root_db_path)
                logger.info(f"Created root database copy at: {root_db_path}")
                deployment_result['root_database_path'] = root_db_path
            else:
                logger.warning(f"Source database not found at: {source_db}")
                
        except Exception as e:
            logger.error(f"Error creating root database copy: {str(e)}")
            # Don't fail the whole operation for this
        
        return {
            "success": True,
            "message": f"Database successfully generated and deployed for {company.name}",
            "company_id": company_id,
            "company_name": company.name,
            "tables_created": deployment_result.get('tables_created', 0),
            "records_inserted": deployment_result.get('records_inserted', 0),
            "deployment_details": deployment_result.get('message', ''),
            "generation_method": result.get('metadata', {}).get('generation_method', 'robust_batch'),
            "populated_tables": result.get('metadata', {}).get('populated_tables_count', 0),
            "total_tables": result.get('metadata', {}).get('tables_count', 0),
            "progress_log": progress_messages[-5:] if progress_messages else []  # Last 5 progress updates
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating company database: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate database: {str(e)}"
        )
