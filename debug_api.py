#!/usr/bin/env python3
"""
Debug the simple company API
"""

import requests
import json

def debug_api():
    print('🧪 Testing Simple Company API')
    print('=' * 50)

    # Test business types
    try:
        response = requests.get('http://localhost:8000/api/v2/business-types')
        print(f'Business types status: {response.status_code}')
        if response.status_code == 200:
            data = response.json()
            print('✅ Business types endpoint working')
            print(f'Available types: {[bt["type"] for bt in data["business_types"]]}')
        else:
            print(f'❌ Business types error: {response.text}')
    except Exception as e:
        print(f'❌ Business types error: {e}')

    # Test company creation
    try:
        company_data = {
            'name': 'Debug Test Company',
            'business_type': 'retail',
            'description': 'Testing the API'
        }
        
        print(f'\nCreating company: {company_data}')
        response = requests.post('http://localhost:8000/api/v2/companies', json=company_data)
        print(f'Company creation status: {response.status_code}')
        
        if response.status_code == 200:
            result = response.json()
            print(f'✅ Success! Company created:')
            print(f'   ID: {result["id"]}')
            print(f'   Name: {result["name"]}')
            print(f'   Database: {result["database_file"]}')
        else:
            print(f'❌ Error response: {response.text}')
            try:
                error_json = response.json()
                print(f'Error detail: {error_json}')
            except:
                pass
                
    except Exception as e:
        print(f'❌ Company creation error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_api()