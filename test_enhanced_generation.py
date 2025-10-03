"""
Test the enhanced database generation system
"""
import asyncio
import json
from database.llm_generator import LLMDatabaseGenerator, DatabaseGenerationParams, BusinessType, ComplexityLevel

async def test_enhanced_generation():
    """Test the enhanced database generation with more realistic data amounts"""
    
    print("🧪 Testing Enhanced Database Generation")
    print("=" * 50)
    
    # Create generator
    generator = LLMDatabaseGenerator()
    
    # Test parameters for a generic business
    params = DatabaseGenerationParams(
        business_type=BusinessType.RETAIL,
        complexity=ComplexityLevel.SIMPLE,
        company_description="Modern electronics store selling smartphones, laptops, headphones, and gaming accessories to tech enthusiasts",
        specific_requirements=[
            "Product catalog with categories",
            "Customer management", 
            "Order processing",
            "Inventory tracking"
        ],
        sample_data_size="small"  # Start with small to test
    )
    
    print(f"Testing with business: {params.company_description}")
    print(f"Complexity: {params.complexity.value}")
    print(f"Data size: {params.sample_data_size}")
    print()
    
    try:
        print("� Generating complete database...")
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
        else:
            print("❌ Schema generation failed")
            return
        
        # Check sample data
        sample_data = result.get('sample_data', {})
        if sample_data:
            print("✅ Sample data generated successfully!")
            
            total_records = 0
            for table_name, records in sample_data.items():
                record_count = len(records)
                total_records += record_count
                print(f"  - {table_name}: {record_count} records")
                
                # Show sample record
                if records and len(records) > 0:
                    sample_record = records[0]
                    fields = list(sample_record.keys())
                    print(f"    Sample fields: {', '.join(fields[:5])}{'...' if len(fields) > 5 else ''}")
            
            print(f"\n📈 Total records generated: {total_records}")
            
            # Verify the enhancement worked
            if total_records >= 100:  # Should be 20-30 per table * ~4 tables
                print("🎉 SUCCESS: Enhanced data generation is working!")
                print("   Generated significantly more data than before (15-25 total)")
            else:
                print("⚠️  WARNING: May not be generating enough data")
                
        else:
            print("❌ Sample data generation failed")
            
    except Exception as e:
        print(f"❌ Error during generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_enhanced_generation())