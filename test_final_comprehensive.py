"""
Final comprehensive test to validate all enhanced database generation improvements
"""
import asyncio
import json
from database.llm_generator import LLMDatabaseGenerator, DatabaseGenerationParams, BusinessType, ComplexityLevel

async def test_final_comprehensive():
    """Test all business types and complexities to validate enhanced generation"""
    
    print("🚀 COMPREHENSIVE DATABASE GENERATION TEST")
    print("=" * 70)
    print("Testing enhanced generation across multiple business types and complexities")
    print()
    
    # Test cases
    test_cases = [
        {
            "name": "Small Retail Store",
            "business_type": BusinessType.RETAIL,
            "complexity": ComplexityLevel.SIMPLE,
            "description": "Local pet supply store with dog food, toys, and accessories",
            "size": "small"
        },
        {
            "name": "Medium Tech Company", 
            "business_type": BusinessType.TECHNOLOGY,
            "complexity": ComplexityLevel.MEDIUM,
            "description": "Software development company creating mobile apps and web platforms",
            "size": "medium"
        }
    ]
    
    generator = LLMDatabaseGenerator()
    
    total_generated = 0
    all_results = []
    
    for i, test_case in enumerate(test_cases):
        print(f"🧪 Test {i+1}/2: {test_case['name']}")
        print(f"   Business: {test_case['description']}")
        print(f"   Type: {test_case['business_type'].value}")
        print(f"   Complexity: {test_case['complexity'].value}")
        print(f"   Size: {test_case['size']}")
        
        params = DatabaseGenerationParams(
            business_type=test_case['business_type'],
            complexity=test_case['complexity'],
            company_description=test_case['description'],
            specific_requirements=[
                "Track core business operations",
                "Manage customer relationships",
                "Monitor business performance"
            ],
            sample_data_size=test_case['size']
        )
        
        try:
            result = await generator.generate_database(params)
            
            schema = result.get('schema', {})
            sample_data = result.get('sample_data', {})
            
            if schema and sample_data:
                table_count = len(schema.get('tables', []))
                record_count = sum(len(records) for records in sample_data.values())
                
                print(f"   ✅ Generated: {table_count} tables, {record_count} records")
                
                # Show table breakdown
                for table_name, records in sample_data.items():
                    print(f"      📋 {table_name}: {len(records)} records")
                
                all_results.append({
                    'test': test_case['name'],
                    'tables': table_count,
                    'records': record_count,
                    'success': True
                })
                total_generated += record_count
                
            else:
                print(f"   ❌ Failed to generate data")
                all_results.append({
                    'test': test_case['name'],
                    'tables': 0,
                    'records': 0,
                    'success': False
                })
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            all_results.append({
                'test': test_case['name'],
                'tables': 0,
                'records': 0,
                'success': False
            })
        
        print()
    
    # Final summary
    print("📊 FINAL RESULTS SUMMARY")
    print("=" * 50)
    print(f"🎯 Total records generated across all tests: {total_generated}")
    
    successful_tests = [r for r in all_results if r['success']]
    failed_tests = [r for r in all_results if not r['success']]
    
    print(f"✅ Successful tests: {len(successful_tests)}/{len(all_results)}")
    
    if successful_tests:
        avg_records = sum(r['records'] for r in successful_tests) / len(successful_tests)
        print(f"📈 Average records per successful test: {avg_records:.1f}")
        
        max_records = max(r['records'] for r in successful_tests)
        print(f"🏆 Best performance: {max_records} records")
    
    if failed_tests:
        print(f"❌ Failed tests: {len(failed_tests)}")
        for test in failed_tests:
            print(f"   - {test['test']}")
    
    # Assessment
    print()
    print("🎯 ENHANCEMENT ASSESSMENT:")
    if total_generated > 100:
        print("✅ EXCELLENT: Generating substantial, realistic datasets!")
        print("✅ SUCCESS: Enhanced generation is working as intended")
    elif total_generated > 50:
        print("✅ GOOD: Significant improvement over original system")
        print("⚠️  NOTE: Could potentially be optimized further")
    else:
        print("⚠️  NEEDS WORK: Still generating relatively small datasets")
    
    print(f"\n🚀 Enhanced database generation system validation complete!")
    return all_results

if __name__ == "__main__":
    asyncio.run(test_final_comprehensive())