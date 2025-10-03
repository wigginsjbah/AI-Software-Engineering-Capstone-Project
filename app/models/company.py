"""
Pydantic models for company management
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

from database.llm_generator import BusinessType, ComplexityLevel


class CompanyCreateRequest(BaseModel):
    """Request model for creating a new company"""
    name: str = Field(..., min_length=1, max_length=100, description="Company name")
    business_type: BusinessType = Field(..., description="Type of business")
    complexity: ComplexityLevel = Field(..., description="Complexity level")
    company_description: str = Field(
        ..., 
        min_length=10, 
        max_length=500, 
        description="Detailed company description"
    )
    additional_metadata: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Additional company metadata"
    )


class CompanyUpdateRequest(BaseModel):
    """Request model for updating company information"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    company_description: Optional[str] = Field(None, min_length=10, max_length=500)
    additional_metadata: Optional[Dict[str, Any]] = None


class CompanyResponse(BaseModel):
    """Response model for company information"""
    id: str
    name: str
    business_type: str
    complexity: str
    company_description: str
    database_file: str
    vector_store_path: str
    created_at: str
    updated_at: str
    is_active: bool
    metadata: Dict[str, Any]


class CompanyListResponse(BaseModel):
    """Response model for company list"""
    companies: List[CompanyResponse]
    total: int
    current_company_id: Optional[str] = None


class CompanyStatsResponse(BaseModel):
    """Response model for company statistics"""
    profile: CompanyResponse
    database_exists: bool
    database_size_mb: float
    table_count: int
    record_count: int
    vector_store_exists: bool


class CompanySwitchRequest(BaseModel):
    """Request model for switching active company"""
    company_id: str = Field(..., description="ID of company to switch to")


class CompanyDeleteResponse(BaseModel):
    """Response model for company deletion"""
    success: bool
    message: str
    deleted_company_id: str


class CompanyContextResponse(BaseModel):
    """Response model for current company context"""
    company_id: Optional[str]
    company_name: str
    business_type: str
    complexity: str
    company_description: str
    database_file: str
    vector_store_path: str


class CompanyDatabaseGenerationRequest(BaseModel):
    """Request model for company-specific database generation"""
    business_requirements: str = Field(
        default="", 
        description="Additional business requirements for database generation"
    )
    include_sample_data: bool = Field(
        default=True,
        description="Whether to include sample data in the generated database"
    )