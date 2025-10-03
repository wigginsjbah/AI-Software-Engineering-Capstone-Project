"""
Enhanced LLM Generator with Robust Batch Processing
===================================================

Integrates the robust batch generation pipeline with the existing
LLM database generator to ensure all tables are populated correctly.
"""

from typing import Dict, List, Any, Optional
from database.llm_generator import LLMDatabaseGenerator, DatabaseGenerationParams
from database.robust_batch_generator import RobustBatchGenerator
from utils.logging import get_logger


class EnhancedLLMGenerator(LLMDatabaseGenerator):
    """
    Enhanced version of LLMDatabaseGenerator with robust batch processing
    for reliable table population
    """
    
    def __init__(self):
        super().__init__()
        self.robust_generator = RobustBatchGenerator()
        self.logger = get_logger(__name__)
    
    async def generate_database_robust(self, params: DatabaseGenerationParams, progress_callback=None) -> Dict[str, Any]:
        """
        Generate complete database with robust batch processing
        
        This method ensures all tables are populated with the correct number of records
        by using a multi-stage pipeline approach instead of single-batch generation.
        """
        try:
            cache_key = self._get_cache_key(params)
            self.logger.info(f"Starting ROBUST database generation for {params.business_type} business (complexity: {params.complexity})")
            
            if progress_callback:
                await progress_callback("Initializing robust generation...", 5)
            
            # Step 1: Generate schema (same as before)
            if cache_key in self._schema_cache:
                self.logger.info("Using cached schema for similar business profile")
                cached_schema = self._schema_cache[cache_key]
                schema_result = cached_schema['schema_sql']
                parsed_schema = cached_schema['parsed_schema']
                table_count = len(parsed_schema.get("tables", []))
                self.logger.info(f"Retrieved cached schema with {table_count} tables")
                if progress_callback:
                    await progress_callback("Retrieved cached schema", 15)
            else:
                self.logger.info("Generating database schema...")
                if progress_callback:
                    await progress_callback("Generating database schema...", 10)
                
                schema_result = await self._generate_schema(params)
                parsed_schema = self._parse_schema(schema_result)
                table_count = len(parsed_schema.get("tables", []))
                self.logger.info(f"Generated schema with {table_count} tables")
                
                # Cache the schema
                self._schema_cache[cache_key] = {
                    'schema_sql': schema_result,
                    'parsed_schema': parsed_schema
                }
                
                if progress_callback:
                    await progress_callback("Schema generation complete", 15)
            
            # Step 2: Generate sample data using ROBUST batch processing
            sample_data = None
            if params.include_sample_data:
                self.logger.info("Starting ROBUST sample data generation...")
                if progress_callback:
                    await progress_callback("Starting robust data generation...", 20)
                
                # Determine target records based on sample_data_size
                target_records = self._get_target_records_count(params.sample_data_size)
                
                # Create business context string
                business_context = f"{params.company_description} ({params.business_type.value} business)"
                
                # Use robust batch generator
                sample_data = await self.robust_generator.generate_all_tables(
                    schema=parsed_schema,
                    schema_sql=schema_result,
                    business_context=business_context,
                    target_records_per_table=target_records,
                    progress_callback=self._create_progress_adapter(progress_callback, 20, 90)
                )
                
                # Log generation results
                populated_tables = [table for table, data in sample_data.items() if data]
                total_tables = len(parsed_schema.get("tables", []))
                self.logger.info(f"ROBUST generation completed: {len(populated_tables)}/{total_tables} tables populated")
                
                # Log detailed results
                for table_name, data in sample_data.items():
                    if data:
                        self.logger.info(f"✓ {table_name}: {len(data)} records")
                    else:
                        self.logger.warning(f"✗ {table_name}: No data generated")
                
                if progress_callback:
                    await progress_callback("Robust data generation complete", 90)
            else:
                self.logger.info("Skipping sample data generation (not requested)")
            
            if progress_callback:
                await progress_callback("Database generation completed!", 100)
            
            self.logger.info("ROBUST database generation completed successfully!")
            
            return {
                "schema": parsed_schema,
                "sample_data": sample_data,
                "metadata": {
                    "business_type": params.business_type,
                    "complexity": params.complexity,
                    "tables_count": len(parsed_schema.get("tables", [])),
                    "populated_tables_count": len([t for t, d in (sample_data or {}).items() if d]),
                    "generation_timestamp": self._get_timestamp(),
                    "used_cache": cache_key in self._schema_cache,
                    "generation_method": "robust_batch"
                }
            }
            
        except Exception as e:
            if progress_callback:
                await progress_callback(f"Error: {str(e)}", -1)
            self.logger.error(f"Error in robust database generation: {str(e)}")
            raise
    
    def _get_target_records_count(self, sample_data_size: str) -> int:
        """Get target record count based on sample data size setting"""
        size_mapping = {
            "small": 30,      # Reasonable for testing
            "medium": 50,     # Good balance
            "large": 75       # More comprehensive
        }
        return size_mapping.get(sample_data_size, 50)
    
    def _create_progress_adapter(self, original_callback, start_pct: float, end_pct: float):
        """Create a progress callback adapter that maps progress to a specific range"""
        if not original_callback:
            return None
            
        async def adapted_callback(message: str, progress: float):
            # Map progress from 0-100 to start_pct-end_pct range
            if progress >= 0:
                mapped_progress = start_pct + (progress / 100.0) * (end_pct - start_pct)
                await original_callback(message, mapped_progress)
            else:
                await original_callback(message, progress)  # Pass through error states
                
        return adapted_callback
    
    async def generate_database_with_fallback(self, params: DatabaseGenerationParams, progress_callback=None) -> Dict[str, Any]:
        """
        Generate database with fallback to original method if robust fails
        
        This provides backward compatibility while preferring the robust approach.
        """
        try:
            # Try robust generation first
            self.logger.info("Attempting robust database generation...")
            return await self.generate_database_robust(params, progress_callback)
            
        except Exception as e:
            self.logger.warning(f"Robust generation failed ({str(e)}), falling back to original method")
            
            if progress_callback:
                await progress_callback("Falling back to original generation method...", 10)
            
            # Fallback to original method
            return await super().generate_database(params, progress_callback)
    
    async def compare_generation_methods(self, params: DatabaseGenerationParams) -> Dict[str, Any]:
        """
        Compare robust vs original generation methods for analysis
        
        This is useful for testing and validation purposes.
        """
        results = {}
        
        try:
            # Test original method
            self.logger.info("Testing original generation method...")
            original_result = await super().generate_database(params)
            
            original_sample_data = original_result.get("sample_data", {})
            original_populated = len([t for t, d in original_sample_data.items() if d])
            original_total = len(original_result.get("schema", {}).get("tables", []))
            
            results["original"] = {
                "success": True,
                "populated_tables": original_populated,
                "total_tables": original_total,
                "success_rate": original_populated / original_total if original_total > 0 else 0,
                "error": None
            }
            
        except Exception as e:
            results["original"] = {
                "success": False,
                "populated_tables": 0,
                "total_tables": 0,
                "success_rate": 0,
                "error": str(e)
            }
        
        try:
            # Test robust method
            self.logger.info("Testing robust generation method...")
            robust_result = await self.generate_database_robust(params)
            
            robust_sample_data = robust_result.get("sample_data", {})
            robust_populated = len([t for t, d in robust_sample_data.items() if d])
            robust_total = len(robust_result.get("schema", {}).get("tables", []))
            
            results["robust"] = {
                "success": True,
                "populated_tables": robust_populated,
                "total_tables": robust_total,
                "success_rate": robust_populated / robust_total if robust_total > 0 else 0,
                "error": None
            }
            
        except Exception as e:
            results["robust"] = {
                "success": False,
                "populated_tables": 0,
                "total_tables": 0,
                "success_rate": 0,
                "error": str(e)
            }
        
        # Calculate improvement
        original_rate = results["original"]["success_rate"]
        robust_rate = results["robust"]["success_rate"]
        
        results["comparison"] = {
            "improvement": robust_rate - original_rate,
            "improvement_percentage": ((robust_rate - original_rate) / original_rate * 100) if original_rate > 0 else 0,
            "robust_better": robust_rate > original_rate
        }
        
        return results