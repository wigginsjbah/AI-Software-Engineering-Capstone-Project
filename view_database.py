#!/usr/bin/env python3
"""
Database Viewer for Business Intelligence RAG Chatbot
Quick tool to explore your business_data.db
"""

import sqlite3
import pandas as pd
from typing import List, Dict

def connect_db(db_path: str = "business_data.db"):
    """Connect to the SQLite database"""
    return sqlite3.connect(db_path)

def show_tables(conn):
    """Show all tables in the database"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("📊 Tables in business_data.db:")
    for table in tables:
        print(f"  - {table[0]}")
    return [table[0] for table in tables]

def show_table_info(conn, table_name: str):
    """Show column information for a table"""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    print(f"\n🏗️  Table '{table_name}' structure:")
    for col in columns:
        col_name, col_type = col[1], col[2]
        print(f"  - {col_name}: {col_type}")

def preview_table(conn, table_name: str, limit: int = 5):
    """Show sample data from a table"""
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT {limit}", conn)
        print(f"\n📋 Sample data from '{table_name}' (showing {limit} rows):")
        print(df.to_string(index=False))
        
        # Show total count
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total = cursor.fetchone()[0]
        print(f"   Total rows in {table_name}: {total}")
        
    except Exception as e:
        print(f"Error reading {table_name}: {e}")

def show_business_summary(conn):
    """Show business intelligence summary"""
    print("\n💼 Business Intelligence Summary:")
    
    # Products by category
    try:
        df = pd.read_sql_query("""
            SELECT category, COUNT(*) as count, 
                   AVG(price) as avg_price,
                   SUM(stock_quantity) as total_stock
            FROM products 
            GROUP BY category
        """, conn)
        print("\n📦 Products by Category:")
        print(df.to_string(index=False))
    except Exception as e:
        print(f"Error getting product summary: {e}")
    
    # Recent orders
    try:
        df = pd.read_sql_query("""
            SELECT order_date, COUNT(*) as order_count, 
                   SUM(total_amount) as daily_revenue
            FROM orders 
            GROUP BY order_date 
            ORDER BY order_date DESC 
            LIMIT 5
        """, conn)
        print("\n📈 Recent Daily Sales:")
        print(df.to_string(index=False))
    except Exception as e:
        print(f"Error getting sales summary: {e}")

def explore_database():
    """Main function to explore the database"""
    print("🔍 Business Database Explorer")
    print("=" * 50)
    
    try:
        conn = connect_db()
        
        # Show all tables
        tables = show_tables(conn)
        
        # Show structure and preview for each table
        for table in tables:
            show_table_info(conn, table)
            preview_table(conn, table, 3)
            print("-" * 50)
        
        # Show business summary
        show_business_summary(conn)
        
        conn.close()
        print("\n✅ Database exploration complete!")
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    explore_database()