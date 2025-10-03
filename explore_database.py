"""
Script to explore the full database contents for all companies
"""
import sqlite3
import os
from pathlib import Path

def explore_database(db_path, db_name):
    """Explore a SQLite database and show all tables and data"""
    print(f"\n{'='*60}")
    print(f"EXPLORING: {db_name}")
    print(f"Path: {db_path}")
    print(f"{'='*60}")
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"📊 Found {len(tables)} tables:")
        for table in tables:
            table_name = table[0]
            print(f"  - {table_name}")
        
        # Explore each table
        for table in tables:
            table_name = table[0]
            print(f"\n🔍 TABLE: {table_name}")
            print("-" * 40)
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            print("Columns:", [col[1] for col in columns])
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"Row count: {count}")
            
            # Show first few rows
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
                rows = cursor.fetchall()
                print("Sample data:")
                for i, row in enumerate(rows):
                    print(f"  Row {i+1}: {row}")
            else:
                print("  (No data)")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error exploring database: {e}")

def main():
    """Main function to explore all databases"""
    base_path = Path(".")
    
    print("🔍 COMPREHENSIVE DATABASE EXPLORATION")
    print("=" * 80)
    
    # Look for all .db files
    db_files = []
    
    # Check main directory
    for file in base_path.glob("*.db"):
        db_files.append((str(file), file.name))
    
    # Check data directory
    data_path = base_path / "data"
    if data_path.exists():
        for file in data_path.glob("*.db"):
            db_files.append((str(file), f"data/{file.name}"))
    
    # Check database directory
    db_path = base_path / "database"
    if db_path.exists():
        for file in db_path.glob("*.db"):
            db_files.append((str(file), f"database/{file.name}"))
    
    # Check companies directory (where company-specific databases might be)
    companies_path = base_path / "companies"
    if companies_path.exists():
        for file in companies_path.rglob("*.db"):
            db_files.append((str(file), f"companies/{file.relative_to(companies_path)}"))
    
    # Check if there are generated company databases
    for company_dir in base_path.glob("*"):
        if company_dir.is_dir() and "aquarium" in company_dir.name.lower():
            for file in company_dir.glob("*.db"):
                db_files.append((str(file), f"{company_dir.name}/{file.name}"))
    
    print(f"Found {len(db_files)} database files:")
    for db_path, db_name in db_files:
        print(f"  - {db_name}")
    
    # Explore each database
    for db_path, db_name in db_files:
        explore_database(db_path, db_name)
    
    # Also check the main business_data.db
    main_db = "business_data.db"
    if os.path.exists(main_db):
        explore_database(main_db, "Main Business Database")
    
    print(f"\n{'='*80}")
    print("✅ Database exploration complete!")

if __name__ == "__main__":
    main()