#!/usr/bin/env python3
"""
Test script for database generation functionality
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.llm_generator import LLMDatabaseGenerator, DatabaseGenerationParams, BusinessType, ComplexityLevel


async def test_schema_generation():
    """Test just the schema generation part"""
    print("Testing schema generation...")
    
    try:
        generator = LLMDatabaseGenerator()
        
        # Simple test parameters
        params = DatabaseGenerationParams(
            business_type=BusinessType.TECHNOLOGY,
            complexity=ComplexityLevel.SIMPLE,
            industry_description="A software development company focused on web applications",
            specific_requirements=["Customer management", "Project tracking"],
            include_sample_data=False,  # Test schema only first
            sample_data_size="small"
        )
        
        print(f"Generating schema for {params.business_type} business...")
        
        # Test schema generation
        schema_result = await generator._generate_schema(params)
        print(f"Schema generation completed. Length: {len(schema_result)} chars")
        print(f"First 200 chars: {schema_result[:200]}...")
        
        # Test schema parsing
        parsed_schema = generator._parse_schema(schema_result)
        print(f"Schema parsed successfully. Found {len(parsed_schema.get('tables', []))} tables")
        
        for table in parsed_schema.get('tables', []):
            print(f"  - Table: {table.get('name')} ({len(table.get('columns', []))} columns)")
        
        return parsed_schema
        
    except Exception as e:
        print(f"Error in schema generation: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_full_generation():
    """Test full database generation including sample data"""
    print("\nTesting full database generation...")
    
    try:
        generator = LLMDatabaseGenerator()
        
        # Simple test parameters with sample data
        params = DatabaseGenerationParams(
            business_type=BusinessType.TECHNOLOGY,
            complexity=ComplexityLevel.SIMPLE,
            industry_description="A software development company focused on web applications",
            specific_requirements=["Customer management", "Project tracking"],
            include_sample_data=True,
            sample_data_size="small"
        )
        
        print(f"Generating full database for {params.business_type} business...")
        
        result = await generator.generate_database(params)
        
        if result:
            print("Database generation completed successfully!")
            print(f"Schema has {len(result.get('schema', {}).get('tables', []))} tables")
            
            sample_data = result.get('sample_data', {})
            if sample_data:
                print(f"Sample data generated for {len(sample_data)} tables")
                for table_name, records in sample_data.items():
                    print(f"  - {table_name}: {len(records) if records else 0} records")
            else:
                print("No sample data generated")
            
            return result
        else:
            print("Database generation returned empty result")
            return None
            
    except Exception as e:
        print(f"Error in full generation: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main test function"""
    print("=== Database Generation Test ===")
    
    # Test 1: Schema only
    schema_result = await test_schema_generation()
    
    if schema_result:
        print("\n✅ Schema generation test PASSED")
    else:
        print("\n❌ Schema generation test FAILED")
        return
    
    # Test 2: Full generation
    full_result = await test_full_generation()
    
    if full_result:
        print("\n✅ Full database generation test PASSED")
    else:
        print("\n❌ Full database generation test FAILED")


if __name__ == "__main__":
    asyncio.run(main())