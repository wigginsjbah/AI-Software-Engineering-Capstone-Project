"""
Generate More Sample Data for Armando's Aquarium
This will add more products, customers, and orders to make the database more realistic
"""
import sqlite3
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()

def add_sample_data_to_aquarium():
    """Add more realistic data to Armando's Aquarium database"""
    
    # Find the company database
    import os
    from pathlib import Path
    
    companies_path = Path("companies")
    if not companies_path.exists():
        print("❌ Companies directory not found")
        return
    
    # Find Armando's Aquarium database
    db_path = None
    for company_dir in companies_path.iterdir():
        if company_dir.is_dir():
            for db_file in company_dir.glob("*.db"):
                try:
                    conn = sqlite3.connect(str(db_file))
                    cursor = conn.cursor()
                    cursor.execute("SELECT value FROM _company_metadata WHERE key = 'company_name'")
                    result = cursor.fetchone()
                    if result and "Armando" in result[0]:
                        db_path = str(db_file)
                        print(f"✅ Found Armando's Aquarium database: {db_path}")
                        break
                    conn.close()
                except:
                    continue
        if db_path:
            break
    
    if not db_path:
        print("❌ Could not find Armando's Aquarium database")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🐠 Adding more products...")
    
    # Add more aquarium products
    aquarium_products = [
        ("Angelfish", "Beautiful freshwater angelfish", 24.99, "Freshwater"),
        ("Clownfish", "Vibrant orange clownfish", 19.99, "Saltwater"),
        ("Neon Tetra", "School of colorful neon tetras", 3.99, "Freshwater"),
        ("Java Fern", "Low-maintenance aquatic plant", 12.99, "Freshwater"),
        ("Live Rock", "Natural saltwater aquarium rock", 34.99, "Saltwater"),
        ("Coral Fragment", "Living coral for reef tanks", 45.99, "Saltwater"),
        ("Aquarium Filter", "High-quality filtration system", 89.99, "Equipment"),
        ("LED Aquarium Light", "Full spectrum LED lighting", 129.99, "Equipment"),
        ("Aquarium Heater", "Adjustable temperature control", 39.99, "Equipment"),
        ("Fish Food Flakes", "Premium nutrition for tropical fish", 8.99, "Food"),
        ("Algae Scraper", "Tool for cleaning aquarium glass", 15.99, "Equipment"),
        ("Water Test Kit", "Complete water quality testing", 25.99, "Equipment"),
        ("Bubble Stone", "Aquarium air stone for aeration", 6.99, "Equipment"),
        ("Driftwood", "Natural aquarium decoration", 22.99, "Decoration"),
        ("Gravel Substrate", "Colored aquarium gravel", 18.99, "Substrate")
    ]
    
    for product in aquarium_products:
        cursor.execute("""
            INSERT INTO products (name, description, price, type, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (*product, datetime.now().isoformat(), datetime.now().isoformat()))
    
    print("👥 Adding more customers...")
    
    # Add more customers
    for i in range(20):
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = f"{first_name.lower()}.{last_name.lower()}@{fake.domain_name()}"
        phone = fake.phone_number()[:12]  # Limit phone number length
        loyalty_points = random.randint(0, 500)
        
        cursor.execute("""
            INSERT INTO customers (first_name, last_name, email, phone_number, loyalty_points, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (first_name, last_name, email, phone, loyalty_points, 
              datetime.now().isoformat(), datetime.now().isoformat()))
        
        # Add address for each customer
        customer_id = cursor.lastrowid
        cursor.execute("""
            INSERT INTO addresses (customer_id, street, city, state, zip_code, country, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (customer_id, fake.street_address(), fake.city(), fake.state_abbr(), 
              fake.zipcode(), "USA", datetime.now().isoformat(), datetime.now().isoformat()))
    
    print("📦 Adding more orders...")
    
    # Get all customer and product IDs
    cursor.execute("SELECT id FROM customers")
    customer_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT id, price FROM products")
    products = cursor.fetchall()
    
    # Add more orders
    for i in range(50):
        customer_id = random.choice(customer_ids)
        order_date = fake.date_between(start_date='-6M', end_date='today')
        status = random.choice(['Processing', 'Shipped', 'Delivered', 'Completed'])
        
        # Create order
        cursor.execute("""
            INSERT INTO orders (customer_id, total, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (customer_id, 0, status, order_date.isoformat(), order_date.isoformat()))
        
        order_id = cursor.lastrowid
        
        # Add 1-3 items per order
        num_items = random.randint(1, 3)
        order_total = 0
        
        for _ in range(num_items):
            product_id, product_price = random.choice(products)
            quantity = random.randint(1, 3)
            item_total = product_price * quantity
            order_total += item_total
            
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, price, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (order_id, product_id, quantity, product_price, 
                  order_date.isoformat(), order_date.isoformat()))
        
        # Update order total
        cursor.execute("UPDATE orders SET total = ? WHERE id = ?", (order_total, order_id))
    
    print("⭐ Adding more reviews...")
    
    # Add more reviews
    cursor.execute("SELECT id FROM products")
    product_ids = [row[0] for row in cursor.fetchall()]
    
    review_comments = [
        "Excellent quality, very happy with purchase!",
        "Great product, arrived quickly",
        "Beautiful addition to my aquarium",
        "Good value for money",
        "Fish are healthy and vibrant",
        "Easy to install and use",
        "Perfect for my tank setup",
        "Highly recommend this product",
        "Decent quality, does the job",
        "Amazing customer service",
        "Fish arrived in perfect condition",
        "Great for beginners",
        "Professional quality equipment",
        "My fish love this!",
        "Exactly as described",
        "Fast shipping, well packaged",
        "Good instructions included",
        "Sturdy and well-made",
        "Fair price for quality",
        "Will buy again"
    ]
    
    for i in range(40):
        product_id = random.choice(product_ids)
        customer_id = random.choice(customer_ids)
        rating = random.choices([1, 2, 3, 4, 5], weights=[5, 10, 15, 35, 35])[0]  # Skew towards positive
        comment = random.choice(review_comments)
        review_date = fake.date_between(start_date='-6M', end_date='today')
        
        cursor.execute("""
            INSERT INTO reviews (product_id, customer_id, rating, comment, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (product_id, customer_id, rating, comment, 
              review_date.isoformat(), review_date.isoformat()))
    
    print("📊 Adding inventory data...")
    
    # Add inventory for all products
    cursor.execute("SELECT id FROM products")
    all_product_ids = [row[0] for row in cursor.fetchall()]
    
    locations = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'Storage-1', 'Storage-2', 'Display-1', 'Display-2']
    
    for product_id in all_product_ids:
        quantity = random.randint(5, 100)
        location = random.choice(locations)
        
        cursor.execute("""
            INSERT OR REPLACE INTO inventory (product_id, quantity, location, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (product_id, quantity, location, 
              datetime.now().isoformat(), datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    print("✅ Sample data generation complete!")
    print("\n📊 Summary:")
    print(f"  - Added {len(aquarium_products)} more products")
    print(f"  - Added 20 more customers with addresses")
    print(f"  - Added 50 more orders with multiple items")
    print(f"  - Added 40 more reviews")
    print(f"  - Updated inventory for all products")
    print(f"\n🎯 Armando's Aquarium now has much more realistic data!")

if __name__ == "__main__":
    add_sample_data_to_aquarium()