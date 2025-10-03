#!/usr/bin/env python3
import sqlite3

db_path = 'companies/47e1d8c4/47e1d8c4_database.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== HOME DEPOT DATABASE ANALYSIS ===\n")

# Check foreign key issues
print("1. FOREIGN KEY REFERENCE ISSUES:")
print("-" * 40)

# Products -> Categories
cursor.execute("SELECT DISTINCT category_id FROM Products ORDER BY category_id;")
product_categories = [row[0] for row in cursor.fetchall()]
cursor.execute("SELECT category_id FROM Categories ORDER BY category_id;")
valid_categories = [row[0] for row in cursor.fetchall()]

print(f"Product categories used: {product_categories}")
print(f"Valid categories available: {valid_categories[:10]}...")  # Show first 10
invalid_product_categories = [cat for cat in product_categories if cat not in valid_categories]
print(f"INVALID product category references: {invalid_product_categories}")

# Products -> Suppliers  
cursor.execute("SELECT DISTINCT supplier_id FROM Products ORDER BY supplier_id;")
product_suppliers = [row[0] for row in cursor.fetchall()]
cursor.execute("SELECT supplier_id FROM Suppliers ORDER BY supplier_id;")
valid_suppliers = [row[0] for row in cursor.fetchall()]

print(f"\nProduct suppliers used: {product_suppliers}")
print(f"Valid suppliers available: {valid_suppliers}")
invalid_product_suppliers = [sup for sup in product_suppliers if sup not in valid_suppliers]
print(f"INVALID product supplier references: {invalid_product_suppliers}")

# Orders -> Customers
cursor.execute("SELECT DISTINCT customer_id FROM Orders ORDER BY customer_id;")
order_customers = [row[0] for row in cursor.fetchall()]
cursor.execute("SELECT customer_id FROM Customers ORDER BY customer_id;")
valid_customers = [row[0] for row in cursor.fetchall()]

print(f"\nOrder customers used: {order_customers}")
print(f"Valid customers available: {valid_customers}")
invalid_order_customers = [cust for cust in order_customers if cust not in valid_customers]
print(f"INVALID order customer references: {invalid_order_customers}")

# Order_Items -> Products
cursor.execute("SELECT DISTINCT product_id FROM Order_Items ORDER BY product_id;")
orderitem_products = [row[0] for row in cursor.fetchall()]
cursor.execute("SELECT product_id FROM Products ORDER BY product_id;")
valid_products = [row[0] for row in cursor.fetchall()]

print(f"\nOrder item products used: {orderitem_products}")
print(f"Valid products available: {valid_products}")
invalid_orderitem_products = [prod for prod in orderitem_products if prod not in valid_products]
print(f"INVALID order item product references: {invalid_orderitem_products}")

# Order_Items -> Orders
cursor.execute("SELECT DISTINCT order_id FROM Order_Items ORDER BY order_id;")
orderitem_orders = [row[0] for row in cursor.fetchall()]
cursor.execute("SELECT order_id FROM Orders ORDER BY order_id;")
valid_orders = [row[0] for row in cursor.fetchall()]

print(f"\nOrder item orders used: {orderitem_orders}")
print(f"Valid orders available: {valid_orders}")
invalid_orderitem_orders = [ord for ord in orderitem_orders if ord not in valid_orders]
print(f"INVALID order item order references: {invalid_orderitem_orders}")

print("\n2. TABLE RECORD COUNTS:")
print("-" * 40)
tables = ['Categories', 'Suppliers', 'Products', 'Customers', 'Orders', 'Order_Items', 'Payments', 'Reviews', 'Inventory_Transactions']
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table};")
    count = cursor.fetchone()[0]
    print(f"{table}: {count} records")

print("\n3. FOREIGN KEY CONSTRAINT CHECK:")
print("-" * 40)
print("If this database had foreign key constraints enabled, these would cause errors:")
total_fk_violations = len(invalid_product_categories) + len(invalid_product_suppliers) + len(invalid_order_customers) + len(invalid_orderitem_products) + len(invalid_orderitem_orders)
print(f"Total foreign key violations: {total_fk_violations}")

conn.close()