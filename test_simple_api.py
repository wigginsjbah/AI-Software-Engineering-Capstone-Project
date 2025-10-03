#!/usr/bin/env python3
"""
Test the new simple company creation API
"""

import requests
import json

def test_simple_company_api():
    base_url = "http://localhost:8000/api/v2"
    
    print("🧪 Testing Simple Company API")
    print("=" * 50)
    
    # Test 1: Get business types
    print("\n1. Testing business types endpoint...")
    try:
        response = requests.get(f"{base_url}/business-types")
        if response.status_code == 200:
            business_types = response.json()
            print("✅ Business types loaded:")
            for bt in business_types["business_types"]:
                print(f"   • {bt['name']} ({bt['type']})")
                print(f"     Tables: {', '.join(bt['tables'])}")
        else:
            print(f"❌ Error getting business types: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Create a retail company
    print("\n2. Testing company creation (retail)...")
    try:
        company_data = {
            "name": "Reliable Test Store",
            "business_type": "retail",
            "description": "A test retail store with guaranteed referential integrity"
        }
        
        response = requests.post(f"{base_url}/companies", json=company_data)
        if response.status_code == 200:
            company = response.json()
            print(f"✅ Company created successfully!")
            print(f"   ID: {company['id']}")
            print(f"   Name: {company['name']}")
            print(f"   Type: {company['business_type']}")
            print(f"   Database: {company['database_file']}")
            
            # Test the database integrity
            print("\n   Testing database integrity...")
            import sqlite3
            conn = sqlite3.connect(company['database_file'])
            cursor = conn.cursor()
            
            # Check referential integrity
            cursor.execute('SELECT COUNT(*) FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE c.id IS NULL')
            invalid_products = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM orders o LEFT JOIN customers c ON o.customer_id = c.id WHERE c.id IS NULL')
            invalid_orders = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM order_items oi LEFT JOIN orders o ON oi.order_id = o.id WHERE o.id IS NULL')
            invalid_order_items_orders = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM order_items oi LEFT JOIN products p ON oi.product_id = p.id WHERE p.id IS NULL')
            invalid_order_items_products = cursor.fetchone()[0]
            
            total_violations = invalid_products + invalid_orders + invalid_order_items_orders + invalid_order_items_products
            
            if total_violations == 0:
                print("   ✅ Perfect referential integrity - 0 violations!")
            else:
                print(f"   ❌ {total_violations} referential integrity violations")
            
            conn.close()
            
            return company['id']
        else:
            error_detail = response.json().get('detail', 'Unknown error')
            print(f"❌ Error creating company: {error_detail}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_healthcare_company():
    """Test healthcare company creation separately"""
    base_url = "http://localhost:8000/api/v2"
    
    # Test 3: Create a healthcare company
    print("\n3. Testing company creation (healthcare)...")
    try:
        company_data = {
            "name": "Reliable Medical Center",
            "business_type": "healthcare", 
            "description": "A test healthcare practice"
        }
        
        response = requests.post(f"{base_url}/companies", json=company_data)
        if response.status_code == 200:
            company = response.json()
            print(f"✅ Healthcare company created successfully!")
            print(f"   ID: {company['id']}")
            print(f"   Name: {company['name']}")
            print(f"   Database: {company['database_file']}")
            
            # Test healthcare database integrity
            print("\n   Testing healthcare database integrity...")
            import sqlite3
            conn = sqlite3.connect(company['database_file'])
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM doctors d LEFT JOIN specialties s ON d.specialty_id = s.id WHERE s.id IS NULL')
            invalid_doctors = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM appointments a LEFT JOIN patients p ON a.patient_id = p.id WHERE p.id IS NULL')
            invalid_appts_patients = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM appointments a LEFT JOIN doctors d ON a.doctor_id = d.id WHERE d.id IS NULL')
            invalid_appts_doctors = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM treatments t LEFT JOIN appointments a ON t.appointment_id = a.id WHERE a.id IS NULL')
            invalid_treatments = cursor.fetchone()[0]
            
            total_violations = invalid_doctors + invalid_appts_patients + invalid_appts_doctors + invalid_treatments
            
            if total_violations == 0:
                print("   ✅ Perfect healthcare referential integrity - 0 violations!")
            else:
                print(f"   ❌ {total_violations} referential integrity violations")
            
            conn.close()
            return company['id']
        else:
            error_detail = response.json().get('detail', 'Unknown error')
            print(f"❌ Error creating healthcare company: {error_detail}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    test_simple_company_api()
    test_healthcare_company()