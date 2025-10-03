"""
Test medium complexity database generation to verify enhanced record counts
"""
import asyncio
import json
from database.llm_generator import LLMDatabaseGenerator, DatabaseGenerationParams, BusinessType, ComplexityLevel

async def test_medium_generation():
    """Test medium complexity generation to check if we get 50-100 records per table"""
    
    print("🧪 Testing MEDIUM Complexity Database Generation")
    print("=" * 60)
    
    # Create generator
    generator = LLMDatabaseGenerator()
    
    # Test parameters for medium complexity
    params = DatabaseGenerationParams(
        business_type=BusinessType.CONSULTING,
        complexity=ComplexityLevel.MEDIUM,
        company_description="Digital marketing agency providing social media management, SEO, content creation, and advertising campaigns for small to medium businesses",
        specific_requirements=[
            "Track client projects and campaigns",
            "Manage team members and their skills",
            "Monitor campaign performance metrics",
            "Handle client billing and invoicing"
        ],
        sample_data_size="medium"  # Should trigger 50-100 records per table
    )
    
    print(f"Testing with business: {params.company_description}")
    print(f"Complexity: {params.complexity.value}")
    print(f"Data size: {params.sample_data_size}")
    print()
    
    try:
        print("🔄 Generating complete database...")
        result = await generator.generate_database(params)
        
        print("✅ Database generation completed!")
        
        # Check schema
        schema = result.get('schema', {})
        if schema and "tables" in schema:
            table_count = len(schema["tables"])
            print(f"📊 Generated schema with {table_count} tables")
            
            for table in schema["tables"]:
                column_count = len(table.get("columns", []))
                print(f"  - {table['name']}: {column_count} columns")
        
        # Check sample data
        sample_data = result.get('sample_data', {})
        if sample_data:
            print("✅ Sample data generated successfully!")
            
            total_records = 0
            for table_name, records in sample_data.items():
                record_count = len(records)
                total_records += record_count
                print(f"  - {table_name}: {record_count} records")
            
            print(f"\n🎯 MEDIUM complexity test results:")
            print(f"   ✅ Total records generated: {total_records}")
            print(f"   ✅ Tables created: {table_count}")
            
            # Analyze if we're getting the expected medium range (50-100 per table)
            table_with_most_records = max(sample_data.items(), key=lambda x: len(x[1]))
            max_records = len(table_with_most_records[1])
            
            print(f"   📈 Largest table: {table_with_most_records[0]} with {max_records} records")
            
            if max_records >= 50:
                print("   ✅ SUCCESS: Getting substantial data volumes for medium complexity!")
            elif max_records >= 25:
                print("   ⚠️  PARTIAL: Getting more data than before, but could be higher")
            else:
                print("   ❌ ISSUE: Still generating low record counts")
        
        return result
        
    except Exception as e:
        print(f"❌ Error during generation: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_medium_generation())