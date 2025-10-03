"""
Enhanced data population system combining LLM intelligence with Faker for realistic data
"""

import json
import random
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from faker import Faker
from faker.providers import BaseProvider
import pandas as pd

from database.llm_generator import BusinessType, ComplexityLevel
from utils.logging import get_logger


class BusinessDataProvider(BaseProvider):
    """Custom Faker provider for business-specific data"""
    
    def business_email_domain(self):
        """Generate business email domains"""
        domains = [
            'company.com', 'corp.com', 'business.net', 'enterprise.org',
            'solutions.com', 'services.com', 'group.com', 'industries.com'
        ]
        return self.random_element(domains)
    
    def product_sku(self):
        """Generate realistic product SKUs"""
        prefix = self.random_element(['PRD', 'ITM', 'SKU', 'CAT'])
        number = self.random_int(1000, 9999)
        suffix = self.random_element(['A', 'B', 'C', 'X', 'Y', 'Z'])
        return f"{prefix}-{number}-{suffix}"
    
    def order_status(self):
        """Generate realistic order statuses"""
        statuses = [
            'pending', 'confirmed', 'processing', 'shipped', 
            'delivered', 'cancelled', 'refunded', 'returned'
        ]
        weights = [0.1, 0.15, 0.2, 0.25, 0.25, 0.03, 0.01, 0.01]
        return self.random_choices(statuses, weights)[0]
    
    def payment_status(self):
        """Generate realistic payment statuses"""
        statuses = ['pending', 'completed', 'failed', 'refunded', 'cancelled']
        weights = [0.05, 0.85, 0.05, 0.03, 0.02]
        return self.random_choices(statuses, weights)[0]


@dataclass
class DataGenerationConfig:
    """Configuration for data generation"""
    size_small: int = 10
    size_medium: int = 25
    size_large: int = 50
    use_faker: bool = True
    use_llm: bool = True
    ensure_referential_integrity: bool = True
    include_edge_cases: bool = True
    realistic_distributions: bool = True


class EnhancedDataPopulator:
    """
    Enhanced data population system that combines LLM intelligence with Faker
    """
    
    def __init__(self, config: DataGenerationConfig = None):
        self.config = config or DataGenerationConfig()
        self.logger = get_logger(__name__)
        self.fake = Faker()
        self.fake.add_provider(BusinessDataProvider)
        
        # Store generated data for referential integrity
        self.generated_data: Dict[str, List[Dict]] = {}
        self.primary_keys: Dict[str, List[Any]] = {}
    
    def generate_table_data(
        self, 
        table_info: Dict[str, Any], 
        business_type: BusinessType,
        record_count: int,
        related_tables: Dict[str, List[Dict]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate realistic data for a specific table
        """
        table_name = table_info['name']
        columns = table_info.get('columns', [])
        
        self.logger.info(f"Generating {record_count} records for {table_name}")
        
        records = []
        
        for i in range(record_count):
            record = {}
            
            for column in columns:
                col_name = column['name']
                col_type = column['type'].upper()
                
                # Generate value based on column name and type
                value = self._generate_column_value(
                    col_name, col_type, table_name, business_type, related_tables
                )
                
                record[col_name] = value
            
            # Post-process record for business logic
            record = self._apply_business_logic(record, table_name, business_type)
            records.append(record)
        
        # Store for referential integrity
        self.generated_data[table_name] = records
        
        # Extract primary keys
        pk_column = self._find_primary_key_column(columns)
        if pk_column:
            self.primary_keys[table_name] = [r[pk_column] for r in records]
        
        return records
    
    def _generate_column_value(
        self, 
        col_name: str, 
        col_type: str, 
        table_name: str,
        business_type: BusinessType,
        related_tables: Dict[str, List[Dict]] = None
    ) -> Any:
        """Generate value for a specific column"""
        
        col_name_lower = col_name.lower()
        
        # Handle foreign keys first
        if col_name_lower.endswith('_id') and col_name_lower != 'id':
            return self._generate_foreign_key(col_name, related_tables)
        
        # Handle primary keys
        if col_name_lower == 'id':
            return self._generate_primary_key()
        
        # Handle common column patterns
        if 'email' in col_name_lower:
            return self.fake.email()
        elif 'phone' in col_name_lower:
            return self.fake.phone_number()
        elif 'address' in col_name_lower:
            return self.fake.address()
        elif 'city' in col_name_lower:
            return self.fake.city()
        elif 'state' in col_name_lower:
            return self.fake.state()
        elif 'country' in col_name_lower:
            return self.fake.country()
        elif 'zip' in col_name_lower or 'postal' in col_name_lower:
            return self.fake.zipcode()
        elif 'name' in col_name_lower:
            return self._generate_name(col_name_lower, table_name, business_type)
        elif 'price' in col_name_lower or 'amount' in col_name_lower or 'cost' in col_name_lower:
            return self._generate_monetary_value(business_type)
        elif 'date' in col_name_lower or 'time' in col_name_lower:
            return self._generate_datetime(col_name_lower)
        elif 'status' in col_name_lower:
            return self._generate_status(table_name, business_type)
        elif 'description' in col_name_lower:
            return self.fake.text(max_nb_chars=200)
        elif 'url' in col_name_lower or 'website' in col_name_lower:
            return self.fake.url()
        elif 'sku' in col_name_lower or 'code' in col_name_lower:
            return self.fake.product_sku()
        
        # Handle by data type
        return self._generate_by_type(col_type, col_name_lower, business_type)
    
    def _generate_by_type(self, col_type: str, col_name: str, business_type: BusinessType) -> Any:
        """Generate value based on data type"""
        
        if 'VARCHAR' in col_type or 'TEXT' in col_type or 'CHAR' in col_type:
            return self.fake.word()
        elif 'INTEGER' in col_type or 'INT' in col_type:
            return self.fake.random_int(1, 1000)
        elif 'DECIMAL' in col_type or 'NUMERIC' in col_type or 'FLOAT' in col_type:
            return round(self.fake.random.uniform(1.0, 1000.0), 2)
        elif 'BOOLEAN' in col_type or 'BOOL' in col_type:
            return self.fake.boolean()
        elif 'TIMESTAMP' in col_type or 'DATETIME' in col_type:
            return self.fake.date_time_between(start_date='-2y', end_date='now')
        elif 'DATE' in col_type:
            return self.fake.date_between(start_date='-2y', end_date='now')
        else:
            return self.fake.word()
    
    def _generate_name(self, col_name: str, table_name: str, business_type: BusinessType) -> str:
        """Generate appropriate names based on context"""
        
        if 'first' in col_name:
            return self.fake.first_name()
        elif 'last' in col_name:
            return self.fake.last_name()
        elif 'company' in col_name or 'business' in col_name:
            return self.fake.company()
        elif 'product' in col_name:
            return self._generate_product_name(business_type)
        elif 'category' in col_name:
            return self._generate_category_name(business_type)
        else:
            return self.fake.name()
    
    def _generate_product_name(self, business_type: BusinessType) -> str:
        """Generate product names by business type"""
        
        if business_type == BusinessType.ECOMMERCE:
            products = [
                'Wireless Bluetooth Headphones', 'Smart Fitness Tracker', 'Organic Cotton T-Shirt',
                'Stainless Steel Water Bottle', 'Laptop Backpack', 'Portable Phone Charger'
            ]
        elif business_type == BusinessType.RETAIL:
            products = [
                'Premium Leather Wallet', 'Designer Sunglasses', 'Casual Running Shoes',
                'Winter Jacket', 'Coffee Mug Set', 'Kitchen Knife Set'
            ]
        else:
            products = [
                'Professional Service Package', 'Standard Plan', 'Premium Solution',
                'Basic Package', 'Enterprise Service', 'Custom Solution'
            ]
        
        return self.fake.random_element(products)
    
    def _generate_category_name(self, business_type: BusinessType) -> str:
        """Generate category names by business type"""
        
        if business_type == BusinessType.ECOMMERCE:
            categories = ['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books', 'Toys']
        elif business_type == BusinessType.RETAIL:
            categories = ['Apparel', 'Accessories', 'Footwear', 'Home Goods', 'Beauty', 'Health']
        else:
            categories = ['Services', 'Products', 'Solutions', 'Packages', 'Plans', 'Options']
        
        return self.fake.random_element(categories)
    
    def _generate_monetary_value(self, business_type: BusinessType) -> float:
        """Generate realistic monetary values"""
        
        if business_type == BusinessType.ECOMMERCE:
            return round(self.fake.random.uniform(9.99, 999.99), 2)
        elif business_type == BusinessType.FINANCE:
            return round(self.fake.random.uniform(100.0, 50000.0), 2)
        else:
            return round(self.fake.random.uniform(19.99, 499.99), 2)
    
    def _generate_datetime(self, col_name: str) -> datetime:
        """Generate datetime values with business logic"""
        
        if 'created' in col_name:
            return self.fake.date_time_between(start_date='-1y', end_date='now')
        elif 'updated' in col_name:
            return self.fake.date_time_between(start_date='-6m', end_date='now')
        elif 'birth' in col_name:
            return self.fake.date_time_between(start_date='-70y', end_date='-18y')
        else:
            return self.fake.date_time_between(start_date='-2y', end_date='now')
    
    def _generate_status(self, table_name: str, business_type: BusinessType) -> str:
        """Generate status values based on context"""
        
        if 'order' in table_name.lower():
            return self.fake.order_status()
        elif 'payment' in table_name.lower():
            return self.fake.payment_status()
        elif 'user' in table_name.lower() or 'customer' in table_name.lower():
            return self.fake.random_element(['active', 'inactive', 'pending', 'suspended'])
        else:
            return self.fake.random_element(['active', 'inactive', 'pending'])
    
    def _generate_foreign_key(self, col_name: str, related_tables: Dict[str, List[Dict]] = None) -> Optional[int]:
        """Generate foreign key values"""
        
        if not related_tables:
            return self.fake.random_int(1, 100)
        
        # Try to find related table
        table_name = col_name.replace('_id', '') + 's'  # Simple pluralization
        if table_name in related_tables and related_tables[table_name]:
            # Pick random ID from related table
            related_record = self.fake.random_element(related_tables[table_name])
            return related_record.get('id', self.fake.random_int(1, 100))
        
        return self.fake.random_int(1, 100)
    
    def _generate_primary_key(self) -> int:
        """Generate auto-incrementing primary key"""
        if not hasattr(self, '_pk_counter'):
            self._pk_counter = 0
        self._pk_counter += 1
        return self._pk_counter
    
    def _find_primary_key_column(self, columns: List[Dict]) -> Optional[str]:
        """Find the primary key column"""
        for col in columns:
            if col['name'].lower() == 'id':
                return col['name']
        return None
    
    def _apply_business_logic(
        self, 
        record: Dict[str, Any], 
        table_name: str, 
        business_type: BusinessType
    ) -> Dict[str, Any]:
        """Apply business-specific logic to records"""
        
        # Ensure created_at comes before updated_at
        if 'created_at' in record and 'updated_at' in record:
            if record['updated_at'] < record['created_at']:
                record['updated_at'] = record['created_at'] + timedelta(
                    days=self.fake.random_int(0, 30)
                )
        
        # Ensure realistic price relationships
        if 'price' in record and 'cost' in record:
            if record['cost'] >= record['price']:
                record['cost'] = round(record['price'] * 0.7, 2)
        
        return record
    
    def get_size_for_complexity(self, complexity: ComplexityLevel, table_name: str) -> int:
        """Get appropriate record count based on complexity and table type"""
        
        base_sizes = {
            ComplexityLevel.SIMPLE: {'core': 15, 'lookup': 5, 'transaction': 25},
            ComplexityLevel.MEDIUM: {'core': 25, 'lookup': 10, 'transaction': 50}, 
            ComplexityLevel.COMPLEX: {'core': 40, 'lookup': 15, 'transaction': 100},
            ComplexityLevel.ENTERPRISE: {'core': 75, 'lookup': 25, 'transaction': 200}
        }
        
        # Classify table type
        table_lower = table_name.lower()
        if any(word in table_lower for word in ['order', 'transaction', 'sale', 'payment']):
            table_type = 'transaction'
        elif any(word in table_lower for word in ['category', 'status', 'type', 'role']):
            table_type = 'lookup'
        else:
            table_type = 'core'
        
        return base_sizes.get(complexity, base_sizes[ComplexityLevel.MEDIUM])[table_type]


# Factory function
def create_enhanced_populator(config: DataGenerationConfig = None) -> EnhancedDataPopulator:
    """Create an enhanced data populator"""
    return EnhancedDataPopulator(config)