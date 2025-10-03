#!/usr/bin/env python3
"""
Test script to validate database generation robustness with different schema types
"""

import asyncio
import sqlite3
import os
import tempfile
from database.schema_analyzer import SchemaAnalyzer, ColumnType
from database.llm_generator import LLMDatabaseGenerator, DatabaseGenerationParams, BusinessType, ComplexityLevel


class SchemaRobustnessTest:
    """Test database generation robustness with various schema configurations"""
    
    def __init__(self):
        self.analyzer = SchemaAnalyzer()
        self.generator = LLMDatabaseGenerator()
        self.test_results = []
    
    def create_test_schemas(self):
        """Create various test database schemas with different characteristics"""
        
        test_schemas = [
            # Test 1: Standard e-commerce schema
            {
                "name": "standard_ecommerce",
                "sql": """
                CREATE TABLE products (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    price DECIMAL(10,2),
                    category_id INTEGER,
                    stock_quantity INTEGER
                );
                
                CREATE TABLE customers (
                    customer_id INTEGER PRIMARY KEY,
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    email VARCHAR(255),
                    created_date DATE
                );
                
                CREATE TABLE orders (
                    order_id INTEGER PRIMARY KEY,
                    customer_id INTEGER,
                    total_amount DECIMAL(10,2),
                    order_date DATE
                );
                """
            },
            
            # Test 2: Mixed case schema
            {
                "name": "mixed_case_schema", 
                "sql": """
                CREATE TABLE Products (
                    ProductID INTEGER PRIMARY KEY,
                    ProductName TEXT NOT NULL,
                    UnitPrice REAL,
                    CategoryID INTEGER
                );
                
                CREATE TABLE Categories (
                    CategoryID INTEGER PRIMARY KEY,
                    CategoryName TEXT,
                    Description TEXT
                );
                """
            },
            
            # Test 3: Alternative naming conventions
            {
                "name": "alternative_naming",
                "sql": """
                CREATE TABLE item_catalog (
                    item_id SERIAL PRIMARY KEY,
                    item_title VARCHAR(200),
                    cost_amount NUMERIC(12,4),
                    is_active BOOLEAN,
                    created_timestamp DATETIME
                );
                
                CREATE TABLE client_base (
                    client_pk INTEGER PRIMARY KEY,
                    client_full_name TEXT,
                    contact_email VARCHAR(150),
                    registration_date DATE
                );
                """
            },
            
            # Test 4: Minimal schema
            {
                "name": "minimal_schema",
                "sql": """
                CREATE TABLE items (
                    id INT,
                    name TEXT
                );
                """
            },
            
            # Test 5: Complex schema with various data types
            {
                "name": "complex_data_types",
                "sql": """
                CREATE TABLE inventory (
                    inventory_id INTEGER PRIMARY KEY,
                    sku VARCHAR(50),
                    product_name TEXT,
                    unit_price DECIMAL(15,4),
                    wholesale_cost MONEY,
                    in_stock BOOLEAN,
                    weight_kg FLOAT,
                    dimensions_json JSON,
                    created_at TIMESTAMP,
                    updated_date DATE,
                    notes LONGTEXT
                );
                """
            }
        ]
        
        return test_schemas
    
    def test_schema_analysis(self, schema_info):
        """Test schema analysis capabilities"""
        print(f"\n=== Testing Schema: {schema_info['name']} ===")
        
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        try:
            # Create database with test schema
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Execute schema creation
            for statement in schema_info['sql'].split(';'):
                statement = statement.strip()
                if statement:
                    cursor.execute(statement)
            
            conn.commit()
            
            # Get table information
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            results = {
                'schema_name': schema_info['name'],
                'tables_found': len(tables),
                'table_analyses': []
            }
            
            # Analyze each table
            for (table_name,) in tables:
                cursor.execute(f"PRAGMA table_info({table_name})")
                table_info = cursor.fetchall()
                
                # Test schema analysis
                analysis = self.analyzer.analyze_table_schema(table_info)
                
                # Test data generation hints
                hints = self.analyzer.get_data_generation_hints(analysis)
                
                table_result = {
                    'table_name': table_name,
                    'column_count': analysis['column_count'],
                    'primary_keys': analysis['primary_keys'],
                    'foreign_keys': len(analysis['foreign_keys']),
                    'data_patterns': len(hints['data_patterns']),
                    'realistic_ranges': len(hints['realistic_ranges']),
                    'columns_analyzed': []
                }
                
                # Test column analysis
                for col in analysis['columns']:
                    col_result = {
                        'name': col['name'],
                        'sql_type': col['type'],
                        'standard_type': col['standard_type'],
                        'is_pk': col['is_primary_key'],
                        'is_fk': col['is_foreign_key']
                    }
                    table_result['columns_analyzed'].append(col_result)
                
                table_result['analysis_success'] = True
                results['table_analyses'].append(table_result)
                
                print(f"  Table: {table_name}")
                print(f"    Columns: {analysis['column_count']}")
                print(f"    Primary Keys: {analysis['primary_keys']}")
                print(f"    Foreign Keys: {len(analysis['foreign_keys'])}")
                print(f"    Data Patterns: {list(hints['data_patterns'].keys())}")
            
            conn.close()
            results['test_success'] = True
            
        except Exception as e:
            print(f"  ERROR: {e}")
            results = {
                'schema_name': schema_info['name'],
                'test_success': False,
                'error': str(e)
            }
        
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)
        
        return results
    
    async def test_data_generation_robustness(self):
        """Test data generation with various business types and complexities"""
        
        test_params = [
            {
                'business_type': BusinessType.ECOMMERCE,
                'complexity': ComplexityLevel.SIMPLE,
                'description': 'Online electronics retailer'
            },
            {
                'business_type': BusinessType.HEALTHCARE,
                'complexity': ComplexityLevel.MEDIUM,
                'description': 'Medical clinic management system'
            },
            {
                'business_type': BusinessType.FINANCE,
                'complexity': ComplexityLevel.COMPLEX,
                'description': 'Investment portfolio management'
            }
        ]
        
        print(f"\n=== Testing Data Generation Robustness ===")
        
        for params in test_params:
            try:
                print(f"\nTesting: {params['business_type'].value} - {params['complexity'].value}")
                
                db_params = DatabaseGenerationParams(
                    business_type=params['business_type'],
                    complexity=params['complexity'],
                    company_description=params['description'],
                    specific_requirements=[],
                    include_sample_data=True,
                    sample_data_size="small"
                )
                
                # Test schema generation (this may take time with actual API calls)
                result = await self.generator.generate_database(db_params)
                
                if result and 'schema' in result:
                    schema = result['schema']
                    tables = schema.get('tables', [])
                    print(f"  Generated {len(tables)} tables")
                    
                    # Test robustness of generated schema
                    for table in tables:
                        columns = table.get('columns', [])
                        print(f"    Table {table['name']}: {len(columns)} columns")
                else:
                    print(f"  FAILED: No schema generated")
                    
            except Exception as e:
                print(f"  ERROR in data generation: {e}")
    
    def run_all_tests(self):
        """Run all robustness tests"""
        print("Database Generation Robustness Test Suite")
        print("=" * 50)
        
        # Test 1: Schema Analysis
        test_schemas = self.create_test_schemas()
        
        for schema_info in test_schemas:
            result = self.test_schema_analysis(schema_info)
            self.test_results.append(result)
        
        # Test 2: Data Generation (async)
        # Note: This would require actual API keys and can be expensive
        # asyncio.run(self.test_data_generation_robustness())
        
        # Summary
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print test results summary"""
        print(f"\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.get('test_success', False))
        
        print(f"Total schema tests: {total_tests}")
        print(f"Successful tests: {successful_tests}")
        print(f"Success rate: {successful_tests/total_tests*100:.1f}%")
        
        # Detailed results
        for result in self.test_results:
            if result.get('test_success'):
                print(f"\n✓ {result['schema_name']}: {result['tables_found']} tables analyzed")
                for table in result['table_analyses']:
                    print(f"  - {table['table_name']}: {table['column_count']} columns, {len(table['columns_analyzed'])} analyzed")
            else:
                print(f"\n✗ {result['schema_name']}: FAILED - {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    # Run the test suite
    test_suite = SchemaRobustnessTest()
    test_suite.run_all_tests()