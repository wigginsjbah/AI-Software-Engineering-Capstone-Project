"""
Quick test to check if our enhanced prompts are working
"""
import asyncio
import json
from database.llm_generator import LLMDatabaseGenerator, DatabaseGenerationParams, BusinessType, ComplexityLevel

async def test_prompt_generation():
    """Test that the actual prompt includes the enhanced record counts"""
    
    print("🔍 Testing Enhanced Prompt Generation")
    print("=" * 50)
    
    # Create generator
    generator = LLMDatabaseGenerator()
    
    # Test parameters for medium data
    params = DatabaseGenerationParams(
        business_type=BusinessType.RETAIL,
        complexity=ComplexityLevel.SIMPLE,
        company_description="Pet supply store selling dog food, cat toys, fish tanks, and bird accessories",
        specific_requirements=["Track pet product inventory", "Manage customer pet profiles"],
        sample_data_size="medium"  # Should trigger 50-100 records per table
    )
    
    # Create a simple mock schema to test the prompt generation
    mock_schema = {
        "tables": [
            {
                "name": "products",
                "columns": [
                    {"name": "id", "type": "INTEGER"},
                    {"name": "name", "type": "TEXT"},
                    {"name": "price", "type": "DECIMAL"}
                ]
            },
            {
                "name": "customers", 
                "columns": [
                    {"name": "id", "type": "INTEGER"},
                    {"name": "name", "type": "TEXT"},
                    {"name": "email", "type": "TEXT"}
                ]
            }
        ]
    }
    
    print(f"Testing with business: {params.company_description}")
    print(f"Data size: {params.sample_data_size}")
    print()
    
    # Test the prompt generation method directly
    prompt = generator._get_data_generation_prompt(mock_schema["tables"][0], params)
    
    print("📝 Generated prompt snippet:")
    print("-" * 40)
    # Look for the record count in the prompt
    lines = prompt.split('\n')
    for line in lines:
        if 'records' in line.lower() or '50-100' in line or 'generate' in line.lower():
            print(f"  {line.strip()}")
    print("-" * 40)
    
    # Check if the prompt contains the expected record count
    if "50-100" in prompt:
        print("✅ SUCCESS: Prompt correctly includes 50-100 record requirement!")
    elif "20-30" in prompt:
        print("⚠️  PARTIAL: Prompt includes 20-30 (small) instead of 50-100 (medium)")
    else:
        print("❌ ISSUE: Prompt doesn't contain expected record counts")
    
    # Also test a real generation with simple setup
    print("\n🔄 Testing actual generation...")
    try:
        result = await generator.generate_database(params)
        
        sample_data = result.get('sample_data', {})
        if sample_data:
            total_records = sum(len(records) for records in sample_data.values())
            print(f"📊 Generated {total_records} total records")
            
            for table_name, records in sample_data.items():
                print(f"   - {table_name}: {len(records)} records")
            
            max_records = max(len(records) for records in sample_data.values())
            if max_records >= 40:
                print("✅ SUCCESS: Generating substantial record counts!")
            elif max_records >= 20:
                print("⚠️  PARTIAL: Better than before, but still room for improvement")
            else:
                print("❌ ISSUE: Still generating low record counts")
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_prompt_generation())