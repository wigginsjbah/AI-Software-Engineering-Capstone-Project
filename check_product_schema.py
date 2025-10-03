#!/usr/bin/env python3
"""
Check product table schema
"""
import sqlite3
import os

db_path = "companies/3a0c7db4/3a0c7db4_database.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check products table schema
    cursor.execute("PRAGMA table_info(products)")
    columns = cursor.fetchall()
    print("Products table schema:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Check orders table schema
    cursor.execute("PRAGMA table_info(orders)")
    columns = cursor.fetchall()
    print("\nOrders table schema:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Check order_items table schema
    cursor.execute("PRAGMA table_info(order_items)")
    columns = cursor.fetchall()
    print("\nOrder_items table schema:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    conn.close()
else:
    print(f"Database not found at {db_path}")