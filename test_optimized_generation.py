"""
Test script to verify optimized database generation performance
"""

import asyncio
import time
from database.llm_generator import LLMDatabaseGenerator, DatabaseGenerationParams, BusinessType, ComplexityLevel

async def test_optimized_generation():
    """Test the optimized generation performance"""
    
    print("Testing optimized database generation...")
    
    # Test parameters
    params = DatabaseGenerationParams(
        business_type=BusinessType.TECHNOLOGY,
        complexity=ComplexityLevel.MEDIUM,
        company_description="A software development company specializing in web applications and mobile apps",
        specific_requirements=["User authentication", "Payment processing", "Real-time notifications"],
        include_sample_data=True,
        sample_data_size="medium"
    )
    
    # Progress callback for testing
    async def progress_callback(message: str, progress: int):
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {progress:3d}% - {message}")
    
    # Create generator and time the operation
    generator = LLMDatabaseGenerator()
    start_time = time.time()
    
    try:
        result = await generator.generate_database(params, progress_callback)
        end_time = time.time()
        
        generation_time = end_time - start_time
        
        print(f"\n=== PERFORMANCE RESULTS ===")
        print(f"Generation Time: {generation_time:.2f} seconds")
        print(f"Schema Tables: {len(result['schema'].get('tables', []))}")
        print(f"Sample Data Tables: {len(result['sample_data']) if result['sample_data'] else 0}")
        print(f"Used Cache: {result['metadata'].get('used_cache', False)}")
        
        # Test cache performance with second generation
        print(f"\n=== TESTING CACHE PERFORMANCE ===")
        start_time = time.time()
        
        result2 = await generator.generate_database(params, progress_callback)
        end_time = time.time()
        
        cache_generation_time = end_time - start_time
        print(f"Cached Generation Time: {cache_generation_time:.2f} seconds")
        print(f"Speed Improvement: {((generation_time - cache_generation_time) / generation_time * 100):.1f}%")
        
        # Performance targets
        print(f"\n=== PERFORMANCE EVALUATION ===")
        target_time = 60  # 60 seconds target
        
        if generation_time <= target_time:
            print(f"✅ PASSED: Generation time ({generation_time:.2f}s) is under target ({target_time}s)")
        else:
            print(f"❌ FAILED: Generation time ({generation_time:.2f}s) exceeds target ({target_time}s)")
        
        if cache_generation_time <= 10:
            print(f"✅ PASSED: Cache performance ({cache_generation_time:.2f}s) is excellent")
        else:
            print(f"⚠️  WARNING: Cache performance ({cache_generation_time:.2f}s) could be better")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_optimized_generation())