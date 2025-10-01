"""
Simple database setup script for the Business Intelligence RAG Chatbot
Creates SQLite database with sample business data
"""

import sqlite3
import random
from datetime import datetime, timedelta
import os

def create_database():
    """Create SQLite database with business tables and sample data"""
    
    # Create database file
    db_path = "business_data.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Creating database tables...")
    
    # Create tables
    cursor.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            launch_date DATE,
            status TEXT DEFAULT 'active'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            registration_date DATE NOT NULL,
            segment TEXT NOT NULL,
            lifetime_value REAL DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            product_id INTEGER,
            order_date DATE NOT NULL,
            quantity INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'completed',
            FOREIGN KEY (customer_id) REFERENCES customers (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE reviews (
            id INTEGER PRIMARY KEY,
            product_id INTEGER,
            customer_id INTEGER,
            rating INTEGER CHECK (rating >= 1 AND rating <= 5),
            review_text TEXT,
            review_date DATE NOT NULL,
            sentiment TEXT,
            FOREIGN KEY (product_id) REFERENCES products (id),
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE sales_performance (
            id INTEGER PRIMARY KEY,
            product_id INTEGER,
            month DATE,
            units_sold INTEGER,
            revenue REAL,
            region TEXT,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    print("Inserting sample data...")
    
    # Sample products
    products = [
        ("iPhone 15", "Electronics", 999.99, "Latest Apple smartphone", "2023-09-01"),
        ("Samsung Galaxy S24", "Electronics", 899.99, "Android flagship phone", "2023-10-15"),
        ("MacBook Pro", "Electronics", 1999.99, "High-performance laptop", "2023-08-01"),
        ("Nike Air Max", "Footwear", 129.99, "Comfortable running shoes", "2023-07-15"),
        ("Adidas Ultraboost", "Footwear", 179.99, "Premium running shoes", "2023-06-01"),
        ("Levi's Jeans", "Clothing", 59.99, "Classic denim jeans", "2023-05-01"),
        ("North Face Jacket", "Clothing", 299.99, "Weather-resistant jacket", "2023-04-15"),
        ("Sony Headphones", "Electronics", 349.99, "Noise-canceling headphones", "2023-09-15"),
        ("Apple Watch", "Electronics", 399.99, "Smartwatch with health features", "2023-08-15"),
        ("Nike T-Shirt", "Clothing", 29.99, "Cotton athletic shirt", "2023-06-15"),
    ]
    
    for i, (name, category, price, desc, launch) in enumerate(products, 1):
        cursor.execute('''
            INSERT INTO products (id, name, category, price, description, launch_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (i, name, category, price, desc, launch))
    
    # Sample customers
    customers = [
        ("John Smith", "john.smith@email.com", "2023-01-15", "Premium"),
        ("Sarah Johnson", "sarah.j@email.com", "2023-02-20", "Standard"),
        ("Mike Wilson", "mike.w@email.com", "2023-03-10", "Premium"),
        ("Emma Davis", "emma.d@email.com", "2023-01-25", "Standard"),
        ("David Brown", "david.b@email.com", "2023-04-05", "Basic"),
        ("Lisa Miller", "lisa.m@email.com", "2023-02-15", "Premium"),
        ("Tom Anderson", "tom.a@email.com", "2023-05-20", "Standard"),
        ("Amy Taylor", "amy.t@email.com", "2023-03-30", "Basic"),
        ("Chris Lee", "chris.l@email.com", "2023-06-10", "Premium"),
        ("Kate Moore", "kate.m@email.com", "2023-04-25", "Standard"),
    ]
    
    for i, (name, email, reg_date, segment) in enumerate(customers, 1):
        lifetime_value = random.uniform(100, 2000) if segment == "Premium" else random.uniform(50, 500)
        cursor.execute('''
            INSERT INTO customers (id, name, email, registration_date, segment, lifetime_value)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (i, name, email, reg_date, segment, round(lifetime_value, 2)))
    
    # Sample orders
    print("Generating sample orders...")
    for order_id in range(1, 51):  # 50 orders
        customer_id = random.randint(1, 10)
        product_id = random.randint(1, 10)
        order_date = datetime(2023, random.randint(6, 12), random.randint(1, 28)).strftime("%Y-%m-%d")
        quantity = random.randint(1, 3)
        
        # Get product price
        cursor.execute("SELECT price FROM products WHERE id = ?", (product_id,))
        price = cursor.fetchone()[0]
        total_amount = price * quantity
        
        cursor.execute('''
            INSERT INTO orders (id, customer_id, product_id, order_date, quantity, total_amount)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (order_id, customer_id, product_id, order_date, quantity, round(total_amount, 2)))
    
    # Sample reviews
    print("Generating sample reviews...")
    review_texts = [
        "Great product, highly recommended!",
        "Good quality but a bit expensive.",
        "Average product, nothing special.",
        "Excellent quality and fast shipping.",
        "Not as expected, disappointed.",
        "Perfect! Will buy again.",
        "Good value for money.",
        "Poor quality, wouldn't recommend.",
        "Amazing product, exceeded expectations!",
        "Decent product but could be better.",
    ]
    
    for review_id in range(1, 31):  # 30 reviews
        product_id = random.randint(1, 10)
        customer_id = random.randint(1, 10)
        rating = random.randint(1, 5)
        review_text = random.choice(review_texts)
        review_date = datetime(2023, random.randint(6, 12), random.randint(1, 28)).strftime("%Y-%m-%d")
        sentiment = "positive" if rating >= 4 else "negative" if rating <= 2 else "neutral"
        
        cursor.execute('''
            INSERT INTO reviews (id, product_id, customer_id, rating, review_text, review_date, sentiment)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (review_id, product_id, customer_id, rating, review_text, review_date, sentiment))
    
    # Sample sales performance
    print("Generating sales performance data...")
    regions = ["North", "South", "East", "West", "Central"]
    
    for perf_id in range(1, 61):  # 60 performance records
        product_id = random.randint(1, 10)
        month = datetime(2023, random.randint(6, 12), 1).strftime("%Y-%m-%d")
        units_sold = random.randint(10, 100)
        
        # Get product price
        cursor.execute("SELECT price FROM products WHERE id = ?", (product_id,))
        price = cursor.fetchone()[0]
        revenue = price * units_sold
        region = random.choice(regions)
        
        cursor.execute('''
            INSERT INTO sales_performance (id, product_id, month, units_sold, revenue, region)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (perf_id, product_id, month, units_sold, round(revenue, 2), region))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Database created successfully: {db_path}")
    print(f"📊 Sample data includes:")
    print(f"   - 10 products across Electronics, Clothing, and Footwear")
    print(f"   - 10 customers with different segments")
    print(f"   - 50 orders from June-December 2023")
    print(f"   - 30 customer reviews with sentiment analysis")
    print(f"   - 60 sales performance records by region")

if __name__ == "__main__":
    create_database()