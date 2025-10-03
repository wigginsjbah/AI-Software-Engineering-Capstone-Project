#!/usr/bin/env python3
"""
Debug technology products table
"""

import sqlite3
from database.simple_reliable_generator import SimpleReliableGenerator

def debug_tech_products():
    # Create a test database with technology schema
    generator = SimpleReliableGenerator()
    conn = sqlite3.connect('debug_tech.db')
    cursor = conn.cursor()

    # Create just the products table
    tech_schema = generator.schemas['technology']['tables']['products']['schema']
    print('Creating products table with schema:')
    print(tech_schema)

    cursor.execute(tech_schema)

    # Check columns
    cursor.execute('PRAGMA table_info(products)')
    columns = cursor.fetchall()
    print('\nColumns in products table:')
    for col in columns:
        print(f'  {col[1]} ({col[2]})')

    column_names = [col[1] for col in columns]
    print(f'\nColumn names: {column_names}')
    print(f'Has price_monthly: {"price_monthly" in column_names}')
    print(f'Has price: {"price" in column_names}')

    conn.close()

if __name__ == "__main__":
    debug_tech_products()