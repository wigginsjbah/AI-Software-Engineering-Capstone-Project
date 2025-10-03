import requests
import json
import asyncio
from app.core.context_builder import ContextBuilder
from app.services.company_manager import get_company_manager

async def test_chat_with_database():
    """Test the complete chat workflow with database connectivity"""
    
    print("=== Testing Chat with Database Connectivity ===\n")
    
    # Test 1: Check company context
    print("1. Testing Company Context...")
    try:
        response = requests.get("http://localhost:8000/api/companies/current")
        if response.status_code == 200:
            company_data = response.json()
            print(f"✅ Current company: {company_data.get('company_name', 'None')}")
            print(f"   Company ID: {company_data.get('company_id', 'None')}")
            print(f"   Database file: {company_data.get('database_file', 'None')}")
            company_id = company_data.get('company_id')
        else:
            print(f"❌ Error getting company: {response.text}")
            return
    except Exception as e:
        print(f"❌ Exception getting company: {e}")
        return
    
    # Test 2: Check database exists and has data
    print("\n2. Testing Database Content...")
    if company_id:
        try:
            response = requests.get(f"http://localhost:8000/api/companies/{company_id}/stats")
            if response.status_code == 200:
                stats = response.json()
                print(f"✅ Database exists: {stats.get('database_exists', False)}")
                print(f"   Tables: {stats.get('table_count', 0)}")
                print(f"   Records: {stats.get('record_count', 0)}")
                print(f"   Size: {stats.get('database_size_mb', 0)} MB")
            else:
                print(f"❌ Error getting stats: {response.text}")
        except Exception as e:
            print(f"❌ Exception getting stats: {e}")
    
    # Test 3: Test chat with database query
    print("\n3. Testing Chat with Database Query...")
    test_queries = [
        "What products do we sell?",
        "How many customers do we have?",
        "Show me our inventory levels"
    ]
    
    for query in test_queries:
        print(f"\n   Testing query: '{query}'")
        try:
            chat_request = {
                "message": query,
                "session_id": "test_session",
                "include_sources": True,
                "company_id": company_id
            }
            
            response = requests.post(
                "http://localhost:8000/api/v1/chat",
                json=chat_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                chat_data = response.json()
                print(f"   ✅ Response received: {len(chat_data.get('message', ''))} chars")
                print(f"   Sources: {len(chat_data.get('sources', []))}")
                if chat_data.get('sql_query'):
                    print(f"   SQL executed: {chat_data['sql_query'][:100]}...")
                else:
                    print("   No SQL query generated")
            else:
                print(f"   ❌ Chat error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Chat exception: {e}")
    
    # Test 4: Direct database context test
    print("\n4. Testing Direct Database Context...")
    try:
        # Get company manager and test context builder
        manager = get_company_manager()
        current_company = manager.get_current_company()
        
        if current_company:
            print(f"✅ Company manager working: {current_company.name}")
            print(f"   Database file: {current_company.database_file}")
            
            # Test context builder
            context_builder = ContextBuilder()
            test_query_analysis = {
                "needs_sql": True,
                "suggested_tables": ["products", "customers"],
                "entities": ["products", "customers"]
            }
            
            context = await context_builder._get_database_context(
                "What products do we sell?", 
                test_query_analysis
            )
            
            print(f"✅ Context builder result:")
            print(f"   Using company DB: {context.get('using_company_db', False)}")
            print(f"   Tables queried: {context.get('tables_queried', [])}")
            print(f"   Results: {len(str(context.get('results', {})))} chars")
            
        else:
            print("❌ No current company found")
            
    except Exception as e:
        print(f"❌ Direct test exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chat_with_database())