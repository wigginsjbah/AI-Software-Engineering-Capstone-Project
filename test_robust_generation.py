"""
Test Robust Batch Generation System
====================================

Validates the new batch processing pipeline against healthcare domain
to ensure all tables are populated correctly.
"""

import asyncio
import json
from database.enhanced_llm_generator import EnhancedLLMGenerator
from database.llm_generator import DatabaseGenerationParams, BusinessType, ComplexityLevel
from utils.logging import get_logger


async def test_robust_batch_generation():
    """Test the robust batch generation system with healthcare domain"""
    
    logger = get_logger(__name__)
    logger.info("Starting robust batch generation test...")
    
    # Create enhanced generator
    generator = EnhancedLLMGenerator()
    
    # Create test parameters (similar to Brinton Vision)
    params = DatabaseGenerationParams(
        business_type=BusinessType.HEALTHCARE,
        complexity=ComplexityLevel.COMPLEX,
        company_description="Brinton Vision is a comprehensive eye care center providing advanced ophthalmology services, specialized treatments, and patient care management",
        specific_requirements=[
            "Patient management system",
            "Doctor scheduling and appointments", 
            "Medical records and treatment history",
            "Insurance and billing integration",
            "Prescription and medication tracking"
        ],
        include_sample_data=True,
        sample_data_size="medium",
        additional_context="Focus on ophthalmology, eye care, vision treatments, and medical practice management"
    )
    
    print("=" * 80)
    print("ROBUST BATCH GENERATION TEST")
    print("=" * 80)
    print(f"Business Type: {params.business_type}")
    print(f"Complexity: {params.complexity}")
    print(f"Company: {params.company_description}")
    print(f"Sample Data Size: {params.sample_data_size}")
    print()
    
    # Progress callback for monitoring
    async def progress_callback(message: str, progress: float):
        if progress >= 0:
            print(f"[{progress:5.1f}%] {message}")
        else:
            print(f"[ERROR] {message}")
    
    try:
        # Test robust generation
        print("Testing ROBUST batch generation method...")
        print("-" * 50)
        
        result = await generator.generate_database_robust(params, progress_callback)
        
        # Analyze results
        schema = result.get("schema", {})
        sample_data = result.get("sample_data", {})
        metadata = result.get("metadata", {})
        
        total_tables = len(schema.get("tables", []))
        populated_tables = len([table for table, data in sample_data.items() if data and len(data) > 0])
        
        print()
        print("ROBUST GENERATION RESULTS:")
        print("=" * 40)
        print(f"Total Tables: {total_tables}")
        print(f"Populated Tables: {populated_tables}")
        print(f"Success Rate: {(populated_tables/total_tables*100):.1f}%")
        print()
        
        # Detailed table analysis
        print("TABLE POPULATION DETAILS:")
        print("-" * 40)
        for table in schema.get("tables", []):
            table_name = table["name"]
            if table_name in sample_data and sample_data[table_name]:
                record_count = len(sample_data[table_name])
                print(f"✓ {table_name:<25} {record_count:>3} records")
            else:
                print(f"✗ {table_name:<25} {0:>3} records")
        
        print()
        print(f"Generation Method: {metadata.get('generation_method', 'unknown')}")
        print(f"Used Cache: {metadata.get('used_cache', False)}")
        
        return result
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        print(f"ERROR: {str(e)}")
        return None


async def compare_generation_methods():
    """Compare robust vs original generation methods"""
    
    logger = get_logger(__name__)
    logger.info("Starting generation method comparison...")
    
    generator = EnhancedLLMGenerator()
    
    # Use simpler parameters for comparison
    params = DatabaseGenerationParams(
        business_type=BusinessType.HEALTHCARE,
        complexity=ComplexityLevel.MEDIUM,  # Smaller for faster comparison
        company_description="Medical clinic providing general healthcare services",
        specific_requirements=[
            "Patient records",
            "Appointments",
            "Medical history"
        ],
        include_sample_data=True,
        sample_data_size="small"
    )
    
    print()
    print("=" * 80)
    print("GENERATION METHOD COMPARISON")
    print("=" * 80)
    
    try:
        results = await generator.compare_generation_methods(params)
        
        print()
        print("COMPARISON RESULTS:")
        print("=" * 40)
        
        original = results.get("original", {})
        robust = results.get("robust", {})
        comparison = results.get("comparison", {})
        
        print(f"Original Method:")
        print(f"  Success: {original.get('success', False)}")
        print(f"  Populated: {original.get('populated_tables', 0)}/{original.get('total_tables', 0)}")
        print(f"  Success Rate: {original.get('success_rate', 0)*100:.1f}%")
        if original.get("error"):
            print(f"  Error: {original['error']}")
        
        print()
        print(f"Robust Method:")
        print(f"  Success: {robust.get('success', False)}")
        print(f"  Populated: {robust.get('populated_tables', 0)}/{robust.get('total_tables', 0)}")
        print(f"  Success Rate: {robust.get('success_rate', 0)*100:.1f}%")
        if robust.get("error"):
            print(f"  Error: {robust['error']}")
        
        print()
        print(f"Improvement:")
        print(f"  Rate Improvement: {comparison.get('improvement', 0)*100:.1f} percentage points")
        print(f"  Improvement %: {comparison.get('improvement_percentage', 0):.1f}%")
        print(f"  Robust Better: {comparison.get('robust_better', False)}")
        
        return results
        
    except Exception as e:
        logger.error(f"Comparison failed: {str(e)}")
        print(f"ERROR: {str(e)}")
        return None


async def main():
    """Main test function"""
    
    print("ROBUST BATCH GENERATION VALIDATION")
    print("=" * 80)
    print("Testing the new batch processing pipeline to ensure")
    print("all tables are populated with correct record counts.")
    print()
    
    # Test 1: Robust generation
    await test_robust_batch_generation()
    
    # Test 2: Method comparison
    await compare_generation_methods()
    
    print()
    print("=" * 80)
    print("TEST COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())