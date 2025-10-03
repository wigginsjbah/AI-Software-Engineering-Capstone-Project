#!/usr/bin/env python3
"""
Analyze Brinton Vision database to check table population
"""
import sqlite3
import os

db_path = "companies/ff7ed0d7/ff7ed0d7_database.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=== BRINTON VISION DATABASE ANALYSIS ===")
    print(f"Database file: {db_path}")
    print()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print(f"Total tables found: {len(tables)}")
    print("Tables:")
    for table in tables:
        table_name = table[0]
        print(f"  - {table_name}")
    print()
    
    # Check record counts for each table
    print("=== TABLE POPULATION ANALYSIS ===")
    total_records = 0
    populated_tables = 0
    empty_tables = 0
    
    for table in tables:
        table_name = table[0]
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            total_records += count
            
            if count > 0:
                populated_tables += 1
                print(f"✓ {table_name}: {count} records")
            else:
                empty_tables += 1
                print(f"✗ {table_name}: 0 records (EMPTY)")
                
        except Exception as e:
            print(f"ERROR {table_name}: {e}")
    
    print()
    print("=== SUMMARY ===")
    print(f"Total tables: {len(tables)}")
    print(f"Populated tables: {populated_tables}")
    print(f"Empty tables: {empty_tables}")
    print(f"Total records across all tables: {total_records}")
    print(f"Population rate: {populated_tables/len(tables)*100:.1f}%")
    
    # Show schema for a few key tables
    print()
    print("=== SAMPLE TABLE SCHEMAS ===")
    sample_tables = [table[0] for table in tables[:3]]  # First 3 tables
    
    for table_name in sample_tables:
        print(f"\n{table_name} schema:")
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        for col in columns:
            col_id, name, col_type, not_null, default, pk = col
            pk_str = " (PK)" if pk else ""
            null_str = " NOT NULL" if not_null else ""
            print(f"  {name}: {col_type}{null_str}{pk_str}")
    
    conn.close()
else:
    print(f"Database file not found: {db_path}")