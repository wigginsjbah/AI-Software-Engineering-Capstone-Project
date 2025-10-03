import sqlite3
import os

db_path = "companies/1bf9b50e/1bf9b50e_database.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Tables found: {len(tables)}")
    
    for table in tables:
        table_name = table[0]
        print(f"\nTable: {table_name}")
        
        # Get column info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print(f"Columns: {[col[1] for col in columns]}")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        print(f"Row count: {row_count}")
        
        # Show first few rows
        if row_count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            rows = cursor.fetchall()
            for i, row in enumerate(rows):
                print(f"Row {i+1}: {row}")
    
    conn.close()
else:
    print(f"Database not found: {db_path}")