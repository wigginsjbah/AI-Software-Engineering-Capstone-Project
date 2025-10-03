#!/usr/bin/env python3
"""
Test deployment functionality
"""

import asyncio
import sys
import os
import tempfile
import sqlite3

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.api.companies import deploy_to_company_database
from database.llm_generator import LLMDatabaseGenerator, DatabaseGenerationParams, BusinessType, ComplexityLevel


async def test_deployment():
    """Test database deployment"""
    print("Testing database deployment...")
    
    try:
        # Generate a simple database
        generator = LLMDatabaseGenerator()
        params = DatabaseGenerationParams(
            business_type=BusinessType.TECHNOLOGY,
            complexity=ComplexityLevel.SIMPLE,
            industry_description="Test company",
            specific_requirements=[],
            include_sample_data=True,
            sample_data_size="small"
        )
        
        print("Generating test database...")
        result = await generator.generate_database(params)
        
        if not result:
            print("❌ Failed to generate test database")
            return False
        
        # Create a temporary database file
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            temp_db_path = tmp_file.name
        
        print(f"Deploying to: {temp_db_path}")
        
        # Test deployment
        deployment_result = await deploy_to_company_database(
            temp_db_path,
            result['schema'],
            result.get('sample_data')
        )
        
        print(f"Deployment result: {deployment_result}")
        
        if deployment_result.get('success'):
            # Verify the database was created
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"Tables created: {[t[0] for t in tables]}")
            
            # Check sample data
            for table_tuple in tables:
                table_name = table_tuple[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  - {table_name}: {count} records")
            
            conn.close()
            
            # Clean up
            os.unlink(temp_db_path)
            
            print("✅ Deployment test PASSED")
            return True
        else:
            print("❌ Deployment failed")
            return False
            
    except Exception as e:
        print(f"❌ Error in deployment test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_deployment())
    if success:
        print("\n🎉 All deployment tests passed!")
    else:
        print("\n💥 Deployment tests failed!")