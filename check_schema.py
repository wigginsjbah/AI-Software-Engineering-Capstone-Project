import sqlite3
import os

def check_database_schema():
    db_path = "companies/3a0c7db4/3a0c7db4_database.db"
    
    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("Available tables:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Check Products table schema
    if any('Products' in table[0] for table in tables):
        cursor.execute("PRAGMA table_info(Products)")
        columns = cursor.fetchall()
        
        print("\nProducts table columns:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
    
    # Check Orders table schema  
    if any('Orders' in table[0] for table in tables):
        cursor.execute("PRAGMA table_info(Orders)")
        columns = cursor.fetchall()
        
        print("\nOrders table columns:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
    
    # Sample some data
    try:
        cursor.execute("SELECT * FROM Products LIMIT 3")
        products = cursor.fetchall()
        print(f"\nSample Products data: {len(products)} rows")
        for product in products:
            print(f"  {product}")
    except Exception as e:
        print(f"Error querying Products: {e}")
    
    conn.close()

if __name__ == "__main__":
    check_database_schema()