#!/usr/bin/env python3
"""
Comprehensive test of all business types
"""

import requests
import sqlite3

def test_all_business_types():
    base_url = "http://localhost:8000/api/v2"
    
    print("🧪 COMPREHENSIVE BUSINESS TYPE TEST")
    print("=" * 50)
    
    business_types = ["retail", "healthcare", "technology"]
    results = []
    
    for biz_type in business_types:
        print(f"\n📋 Testing {biz_type.upper()} business...")
        
        company_data = {
            'name': f'Test {biz_type.title()} Company',
            'business_type': biz_type,
            'description': f'Testing {biz_type} database generation'
        }
        
        try:
            response = requests.post(f"{base_url}/companies", json=company_data)
            
            if response.status_code == 200:
                company = response.json()
                print(f"✅ Company created: {company['name']} (ID: {company['id']})")
                
                # Test database integrity
                conn = sqlite3.connect(company['database_file'])
                cursor = conn.cursor()
                
                # Get all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != '_company_metadata'")
                tables = [row[0] for row in cursor.fetchall()]
                print(f"   Tables: {', '.join(tables)}")
                
                # Test basic referential integrity
                violations = 0
                
                if biz_type == "retail":
                    # Products -> Categories
                    cursor.execute('SELECT COUNT(*) FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE c.id IS NULL')
                    violations += cursor.fetchone()[0]
                    
                    # Orders -> Customers
                    cursor.execute('SELECT COUNT(*) FROM orders o LEFT JOIN customers c ON o.customer_id = c.id WHERE c.id IS NULL')
                    violations += cursor.fetchone()[0]
                
                elif biz_type == "healthcare":
                    # Doctors -> Specialties
                    cursor.execute('SELECT COUNT(*) FROM doctors d LEFT JOIN specialties s ON d.specialty_id = s.id WHERE s.id IS NULL')
                    violations += cursor.fetchone()[0]
                    
                    # Appointments -> Patients
                    cursor.execute('SELECT COUNT(*) FROM appointments a LEFT JOIN patients p ON a.patient_id = p.id WHERE p.id IS NULL')
                    violations += cursor.fetchone()[0]
                
                elif biz_type == "technology":
                    # Products -> Product Categories
                    cursor.execute('SELECT COUNT(*) FROM products p LEFT JOIN product_categories c ON p.category_id = c.id WHERE c.id IS NULL')
                    violations += cursor.fetchone()[0]
                    
                    # Subscriptions -> Users
                    cursor.execute('SELECT COUNT(*) FROM subscriptions s LEFT JOIN users u ON s.user_id = u.id WHERE u.id IS NULL')
                    violations += cursor.fetchone()[0]
                
                conn.close()
                
                if violations == 0:
                    print(f"   ✅ Perfect referential integrity!")
                    results.append((biz_type, True, company['id']))
                else:
                    print(f"   ❌ {violations} referential integrity violations")
                    results.append((biz_type, False, company['id']))
                    
            else:
                print(f"❌ Error creating {biz_type} company: {response.text}")
                results.append((biz_type, False, None))
                
        except Exception as e:
            print(f"❌ Exception testing {biz_type}: {e}")
            results.append((biz_type, False, None))
    
    print("\n" + "=" * 50)
    print("📊 FINAL RESULTS:")
    print("=" * 50)
    
    success_count = 0
    for biz_type, success, company_id in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{biz_type.upper():12} | {status:8} | {company_id or 'N/A'}")
        if success:
            success_count += 1
    
    print(f"\nSUCCESS RATE: {success_count}/{len(business_types)} ({success_count/len(business_types)*100:.0f}%)")
    
    if success_count == len(business_types):
        print("🎉 ALL BUSINESS TYPES WORKING PERFECTLY!")
        return True
    else:
        print("⚠️  Some business types failed")
        return False

if __name__ == "__main__":
    test_all_business_types()