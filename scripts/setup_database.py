"""
Database setup and data generation script
"""

import asyncio
import random
from datetime import datetime, timedelta
from decimal import Decimal
from faker import Faker
import sqlite3
import os

from config.settings import get_settings

fake = Faker()

async def create_database_schema():
    """Create the database schema"""
    settings = get_settings()
    
    # Extract database path from URL
    db_path = settings.DATABASE_URL.replace("sqlite:///", "").replace("sqlite+aiosqlite:///", "")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.executescript("""
        -- Products table
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            description TEXT,
            launch_date DATE,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Customers table
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            registration_date DATE NOT NULL,
            segment TEXT NOT NULL,
            lifetime_value DECIMAL(10,2) DEFAULT 0.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Orders table
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            order_date DATE NOT NULL,
            quantity INTEGER NOT NULL,
            total_amount DECIMAL(10,2) NOT NULL,
            status TEXT DEFAULT 'completed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        );
        
        -- Reviews table
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            review_text TEXT,
            review_date DATE NOT NULL,
            sentiment TEXT,
            helpful_votes INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id),
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        );
        
        -- Sales performance table
        CREATE TABLE IF NOT EXISTS sales_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            month DATE NOT NULL,
            units_sold INTEGER NOT NULL,
            revenue DECIMAL(10,2) NOT NULL,
            region TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id)
        );
        
        -- Create indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
        CREATE INDEX IF NOT EXISTS idx_orders_product_id ON orders(product_id);
        CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);
        CREATE INDEX IF NOT EXISTS idx_reviews_product_id ON reviews(product_id);
        CREATE INDEX IF NOT EXISTS idx_reviews_customer_id ON reviews(customer_id);
        CREATE INDEX IF NOT EXISTS idx_sales_performance_product_id ON sales_performance(product_id);
        CREATE INDEX IF NOT EXISTS idx_sales_performance_month ON sales_performance(month);
    """)
    
    conn.commit()
    conn.close()
    print("Database schema created successfully!")

async def generate_sample_data():
    """Generate sample business data"""
    settings = get_settings()
    db_path = settings.DATABASE_URL.replace("sqlite:///", "").replace("sqlite+aiosqlite:///", "")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Categories and sample products
    categories = ["Electronics", "Clothing", "Books", "Home & Garden", "Sports", "Beauty", "Automotive"]
    
    products_data = [
        ("Wireless Headphones", "Electronics", 99.99, "High-quality wireless headphones with noise cancellation"),
        ("Smartphone", "Electronics", 699.99, "Latest model smartphone with advanced features"),
        ("Laptop", "Electronics", 1299.99, "Powerful laptop for work and gaming"),
        ("T-Shirt", "Clothing", 19.99, "Comfortable cotton t-shirt"),
        ("Jeans", "Clothing", 59.99, "Premium denim jeans"),
        ("Running Shoes", "Sports", 129.99, "Lightweight running shoes for athletes"),
        ("Coffee Maker", "Home & Garden", 89.99, "Automatic coffee maker with timer"),
        ("Programming Book", "Books", 45.99, "Comprehensive guide to Python programming"),
        ("Moisturizer", "Beauty", 29.99, "Anti-aging moisturizer with SPF"),
        ("Car Phone Mount", "Automotive", 24.99, "Adjustable phone mount for vehicles")
    ]
    
    # Insert products
    print("Generating products...")
    for i, (name, category, price, description) in enumerate(products_data):
        launch_date = fake.date_between(start_date="-2y", end_date="today")
        cursor.execute("""
            INSERT INTO products (name, category, price, description, launch_date, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, category, price, description, launch_date, "active"))
    
    # Add more random products
    for _ in range(40):
        category = random.choice(categories)
        name = f"{fake.word().title()} {category[:-1]}"
        price = round(random.uniform(10, 500), 2)
        description = fake.text(max_nb_chars=100)
        launch_date = fake.date_between(start_date="-2y", end_date="today")
        
        cursor.execute("""
            INSERT INTO products (name, category, price, description, launch_date, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, category, price, description, launch_date, "active"))
    
    # Generate customers
    print("Generating customers...")
    segments = ["Premium", "Standard", "Basic", "Enterprise"]
    
    for _ in range(200):
        name = fake.name()
        email = fake.email()
        registration_date = fake.date_between(start_date="-2y", end_date="today")
        segment = random.choice(segments)
        lifetime_value = round(random.uniform(50, 5000), 2)
        
        cursor.execute("""
            INSERT INTO customers (name, email, registration_date, segment, lifetime_value)
            VALUES (?, ?, ?, ?, ?)
        """, (name, email, registration_date, segment, lifetime_value))
    
    # Generate orders
    print("Generating orders...")
    customer_ids = [row[0] for row in cursor.execute("SELECT id FROM customers").fetchall()]
    product_ids = [row[0] for row in cursor.execute("SELECT id FROM products").fetchall()]
    
    for _ in range(1000):
        customer_id = random.choice(customer_ids)
        product_id = random.choice(product_ids)
        order_date = fake.date_between(start_date="-1y", end_date="today")
        quantity = random.randint(1, 5)
        
        # Get product price
        product_price = cursor.execute("SELECT price FROM products WHERE id = ?", (product_id,)).fetchone()[0]
        total_amount = float(product_price) * quantity
        
        status = random.choices(["completed", "pending", "cancelled"], weights=[0.8, 0.15, 0.05])[0]
        
        cursor.execute("""
            INSERT INTO orders (customer_id, product_id, order_date, quantity, total_amount, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (customer_id, product_id, order_date, quantity, total_amount, status))
    
    # Generate reviews
    print("Generating reviews...")
    sentiments = ["positive", "neutral", "negative"]
    
    for _ in range(500):
        product_id = random.choice(product_ids)
        customer_id = random.choice(customer_ids)
        rating = random.choices([1, 2, 3, 4, 5], weights=[0.05, 0.1, 0.2, 0.35, 0.3])[0]
        review_text = fake.text(max_nb_chars=200)
        review_date = fake.date_between(start_date="-1y", end_date="today")
        sentiment = random.choices(sentiments, weights=[0.6, 0.25, 0.15])[0]
        helpful_votes = random.randint(0, 20)
        
        try:
            cursor.execute("""
                INSERT INTO reviews (product_id, customer_id, rating, review_text, review_date, sentiment, helpful_votes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (product_id, customer_id, rating, review_text, review_date, sentiment, helpful_votes))
        except sqlite3.IntegrityError:
            # Skip duplicate customer-product reviews
            continue
    
    # Generate sales performance data
    print("Generating sales performance data...")
    regions = ["North America", "Europe", "Asia", "South America", "Australia"]
    
    for product_id in product_ids[:20]:  # For first 20 products
        for month_offset in range(12):  # Last 12 months
            month = (datetime.now() - timedelta(days=30 * month_offset)).replace(day=1).date()
            region = random.choice(regions)
            units_sold = random.randint(10, 500)
            
            # Get product price for revenue calculation
            product_price = cursor.execute("SELECT price FROM products WHERE id = ?", (product_id,)).fetchone()[0]
            revenue = float(product_price) * units_sold
            
            cursor.execute("""
                INSERT INTO sales_performance (product_id, month, units_sold, revenue, region)
                VALUES (?, ?, ?, ?, ?)
            """, (product_id, month, units_sold, revenue, region))
    
    conn.commit()
    conn.close()
    print("Sample data generated successfully!")

async def main():
    """Main setup function"""
    print("Setting up business database...")
    await create_database_schema()
    await generate_sample_data()
    print("Database setup complete!")
    
    # Print some stats
    settings = get_settings()
    db_path = settings.DATABASE_URL.replace("sqlite:///", "").replace("sqlite+aiosqlite:///", "")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    stats = {}
    for table in ["products", "customers", "orders", "reviews", "sales_performance"]:
        count = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        stats[table] = count
    
    conn.close()
    
    print("\\nDatabase Statistics:")
    for table, count in stats.items():
        print(f"  {table}: {count} records")

if __name__ == "__main__":
    asyncio.run(main())