#!/usr/bin/env python3

import sqlite3
import sys

# Check if enhanced data generator can be imported
try:
    from scripts.enhanced_data_generator import EnhancedBusinessDataGenerator
    print("✅ Enhanced data generator imports successfully")
    
    # Test basic functionality
    generator = EnhancedBusinessDataGenerator(
        business_type="retail",
        company_name="Test Company", 
        company_description="A test company that sells jellybeans and candy"
    )
    print("✅ Generator created successfully")
    
except Exception as e:
    print(f"❌ Error importing or creating generator: {e}")
    sys.exit(1)