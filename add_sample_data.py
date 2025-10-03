#!/usr/bin/env python3
"""
Add minimal sample data to test the system
"""
import sqlite3
import os

db_path = "companies/3a0c7db4/3a0c7db4_database.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Add sample products
        cursor.execute("""
            INSERT OR REPLACE INTO products (id, name, description, price, stock_quantity, category_id) 
            VALUES (1, 'Premium Widget', 'High-quality widget for luxury applications', 299.99, 50, 1)
        """)
        cursor.execute("""
            INSERT OR REPLACE INTO products (id, name, description, price, stock_quantity, category_id) 
            VALUES (2, 'Luxury Gadget', 'Top-tier gadget for professional use', 599.99, 25, 1)
        """)
        
        # Add sample customers 
        cursor.execute("""
            INSERT OR REPLACE INTO customers (id, first_name, last_name, email, phone) 
            VALUES (1, 'John', 'Doe', 'john@example.com', '555-1234')
        """)
        cursor.execute("""
            INSERT OR REPLACE INTO customers (id, first_name, last_name, email, phone) 
            VALUES (2, 'Jane', 'Smith', 'jane@example.com', '555-5678')
        """)
        
        # Add sample orders
        cursor.execute("""
            INSERT OR REPLACE INTO orders (id, customer_id, order_date, total_amount, status) 
            VALUES (1, 1, '2024-01-15', 299.99, 'completed')
        """)
        cursor.execute("""
            INSERT OR REPLACE INTO orders (id, customer_id, order_date, total_amount, status) 
            VALUES (2, 2, '2024-01-20', 599.99, 'completed')
        """)
        
        # Add sample order items
        cursor.execute("""
            INSERT OR REPLACE INTO order_items (id, order_id, product_id, quantity, price) 
            VALUES (1, 1, 1, 1, 299.99)
        """)
        cursor.execute("""
            INSERT OR REPLACE INTO order_items (id, order_id, product_id, quantity, price) 
            VALUES (2, 2, 2, 1, 599.99)
        """)
        
        conn.commit()
        print("Successfully added sample data!")
        
        # Verify data
        cursor.execute("SELECT COUNT(*) FROM products")
        products_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM customers")
        customers_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM orders")
        orders_count = cursor.fetchone()[0]
        
        print(f"Database now has: {products_count} products, {customers_count} customers, {orders_count} orders")
        
    except Exception as e:
        print(f"Error adding data: {e}")
    finally:
        conn.close()
else:
    print(f"Database not found at {db_path}")