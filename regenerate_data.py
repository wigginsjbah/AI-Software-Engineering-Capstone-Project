"""
Fix empty database by generating proper sample data
"""

import asyncio
import sqlite3
import os
from database.llm_generator import LLMDatabaseGenerator, DatabaseGenerationParams, BusinessType, ComplexityLevel

async def regenerate_sample_data():
    """Regenerate sample data for the existing database"""
    
    db_path = "companies/3a0c7db4/3a0c7db4_database.db"
    
    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return
    
    # Get the schema from existing database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = cursor.fetchall()
    
    print(f"Found {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Check if we have data (exclude metadata table)
    has_data = False
    for table in tables:
        if table[0] != '_company_metadata':
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  {table[0]}: {count} records")
            if count > 0:
                has_data = True
    
    conn.close()
    
    if has_data:
        print("Database already has data. Skipping regeneration.")
        return
    
    print("No data found. Generating sample data...")
    
    # Create generation parameters
    params = DatabaseGenerationParams(
        business_type=BusinessType.TECHNOLOGY,
        complexity=ComplexityLevel.MEDIUM,
        company_description="A software development company specializing in web applications and mobile apps",
        specific_requirements=["User authentication", "Payment processing"],
        include_sample_data=True,
        sample_data_size="medium"
    )
    
    # Generate sample data using optimized generator
    generator = LLMDatabaseGenerator()
    
    # Create a simplified schema from existing tables for data generation
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    schema = {"tables": []}
    for table in tables:
        table_name = table[0]
        if table_name != '_company_metadata':  # Skip metadata table
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            table_schema = {
                "name": table_name,
                "columns": [{"name": col[1], "type": col[2]} for col in columns]
            }
            schema["tables"].append(table_schema)
    
    conn.close()
    
    print(f"Generating data for {len(schema['tables'])} tables...")
    sample_data = await generator._generate_sample_data(schema, params)
    
    if sample_data:
        # Insert the data
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        records_inserted = 0
        for table_name, records in sample_data.items():
            if records:
                print(f"Inserting {len(records)} records into {table_name}")
                
                # Get column info
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns_info = cursor.fetchall()
                columns = [col[1] for col in columns_info]
                
                for record in records:
                    if isinstance(record, dict):
                        # Filter record to only include existing columns
                        filtered_record = {k: v for k, v in record.items() if k in columns}
                        if filtered_record:
                            placeholders = ', '.join(['?' for _ in filtered_record])
                            columns_str = ', '.join(filtered_record.keys())
                            values = list(filtered_record.values())
                            
                            try:
                                insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                                cursor.execute(insert_sql, values)
                                records_inserted += 1
                            except Exception as e:
                                print(f"Error inserting into {table_name}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"Successfully inserted {records_inserted} total records")
        
        # Create root copy
        try:
            import shutil
            root_db_path = "best_guy_database.db"
            shutil.copy2(db_path, root_db_path)
            print(f"Created root database copy at: {root_db_path}")
        except Exception as e:
            print(f"Error creating root copy: {e}")
            
    else:
        print("No sample data generated")

if __name__ == "__main__":
    asyncio.run(regenerate_sample_data())