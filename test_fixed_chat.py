import requests
import json

def test_chat_query():
    """Test the chat with a specific query about products"""
    
    print("Testing chat query about products...")
    
    chat_request = {
        "message": "What products do we sell?",
        "session_id": "test_session_fix",
        "include_sources": True,
        "company_id": "1bf9b50e"  # Armando's Aquarium
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/chat",
            json=chat_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Response length: {len(data.get('message', ''))}")
            print(f"Response preview: {data.get('message', '')[:200]}...")
            print(f"Sources: {len(data.get('sources', []))}")
            if data.get('sql_query'):
                print(f"SQL Query: {data['sql_query']}")
            else:
                print("No SQL query executed")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_chat_query()