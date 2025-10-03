#!/usr/bin/env python3
"""
Test technology company creation
"""

import requests
import json
import sqlite3

def test_tech_company():
    # Test company creation
    company_data = {
        'name': 'Final Test Company',
        'business_type': 'technology',
        'description': 'Testing the final system'
    }

    print('Creating technology company...')
    response = requests.post('http://localhost:8000/api/v2/companies', json=company_data)
    print(f'Status: {response.status_code}')

    if response.status_code == 200:
        result = response.json()
        print(f'✅ Success! Created: {result["name"]} (ID: {result["id"]})')
        print(f'Database: {result["database_file"]}')
        
        # Quick integrity check
        conn = sqlite3.connect(result['database_file'])
        cursor = conn.cursor()
        
        # Check users -> subscriptions relationship
        cursor.execute('SELECT COUNT(*) FROM subscriptions s LEFT JOIN users u ON s.user_id = u.id WHERE u.id IS NULL')
        invalid_subs = cursor.fetchone()[0]
        
        # Check products -> product_categories relationship
        cursor.execute('SELECT COUNT(*) FROM products p LEFT JOIN product_categories c ON p.category_id = c.id WHERE c.id IS NULL')
        invalid_products = cursor.fetchone()[0]
        
        total_violations = invalid_subs + invalid_products
        
        print(f'Technology DB integrity: {total_violations} violations (should be 0)')
        if total_violations == 0:
            print('✅ Perfect referential integrity!')
        
        conn.close()
        return True
    else:
        print(f'❌ Error: {response.text}')
        return False

if __name__ == "__main__":
    test_tech_company()