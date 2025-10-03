#!/usr/bin/env python3

import asyncio
import aiohttp
import json

async def test_finance_company_creation():
    """Test creating a finance company to verify the fix"""
    
    url = "http://127.0.0.1:8007/api/companies/create-enhanced"
    
    data = {
        "company_name": "Chariott Financial",
        "company_description": "A comprehensive financial services company offering banking, loans, investments, and insurance products",
        "business_type": "finance",
        "complexity": "simple",
        "requirements": "banking services, customer accounts, transaction processing",
        "additional_context": "Focus on retail banking and investment services"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print("🔄 Testing finance company creation...")
            async with session.post(url, data=data) as response:
                result = await response.json()
                
                if response.status == 200:
                    print("✅ Finance company creation SUCCESSFUL!")
                    print(f"📊 Company: {result.get('company_name')}")
                    print(f"📊 Data Stats: {result.get('data_stats')}")
                    print(f"📊 Company ID: {result.get('company_id')}")
                else:
                    print(f"❌ Finance company creation FAILED!")
                    print(f"Status: {response.status}")
                    print(f"Error: {result}")
                    
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_finance_company_creation())