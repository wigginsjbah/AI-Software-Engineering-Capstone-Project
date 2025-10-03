"""
Robust schema analyzer for database generation
Handles different database types, column variations, and data type mappings
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass


class ColumnType(str, Enum):
    """Standard column types with robust mapping"""
    INTEGER = "integer"
    STRING = "string"
    DECIMAL = "decimal"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    TEXT = "text"
    JSON = "json"
    FOREIGN_KEY = "foreign_key"


@dataclass
class ColumnMapping:
    """Maps database column types to standard types"""
    standard_type: ColumnType
    sql_type: str
    constraints: List[str]
    is_primary_key: bool = False
    is_foreign_key: bool = False
    references: Optional[str] = None


class SchemaAnalyzer:
    """
    Analyzes and normalizes database schemas for robust handling
    """
    
    # Common column name patterns for different business concepts
    ID_PATTERNS = [
        r'^id$', r'^.*_id$', r'^.*Id$', r'^pk_.*', r'^primary_key$'
    ]
    
    NAME_PATTERNS = [
        r'^name$', r'^.*_name$', r'^title$', r'^label$', r'^description$'
    ]
    
    PRICE_PATTERNS = [
        r'^price$', r'^cost$', r'^amount$', r'^total$', r'^.*_price$', 
        r'^.*_cost$', r'^.*_amount$', r'^.*_total$', r'^value$'
    ]
    
    DATE_PATTERNS = [
        r'^.*_date$', r'^.*_time$', r'^created.*', r'^updated.*', 
        r'^modified.*', r'^timestamp$', r'^date_.*'
    ]
    
    BOOLEAN_PATTERNS = [
        r'^is_.*', r'^has_.*', r'^can_.*', r'^.*_flag$', r'^active$', 
        r'^enabled$', r'^visible$', r'^.*_status$'
    ]
    
    # SQL type mappings for different database systems
    TYPE_MAPPINGS = {
        # SQLite types
        'INTEGER': ColumnType.INTEGER,
        'TEXT': ColumnType.TEXT,
        'REAL': ColumnType.DECIMAL,
        'BLOB': ColumnType.TEXT,
        'NUMERIC': ColumnType.DECIMAL,
        
        # PostgreSQL types
        'SERIAL': ColumnType.INTEGER,
        'BIGSERIAL': ColumnType.INTEGER,
        'VARCHAR': ColumnType.STRING,
        'CHAR': ColumnType.STRING,
        'TIMESTAMP': ColumnType.DATETIME,
        'DATE': ColumnType.DATE,
        'BOOLEAN': ColumnType.BOOLEAN,
        'DECIMAL': ColumnType.DECIMAL,
        'MONEY': ColumnType.DECIMAL,
        'JSON': ColumnType.JSON,
        'JSONB': ColumnType.JSON,
        
        # MySQL types
        'INT': ColumnType.INTEGER,
        'BIGINT': ColumnType.INTEGER,
        'TINYINT': ColumnType.INTEGER,
        'SMALLINT': ColumnType.INTEGER,
        'MEDIUMINT': ColumnType.INTEGER,
        'FLOAT': ColumnType.DECIMAL,
        'DOUBLE': ColumnType.DECIMAL,
        'DATETIME': ColumnType.DATETIME,
        'TINYTEXT': ColumnType.STRING,
        'MEDIUMTEXT': ColumnType.TEXT,
        'LONGTEXT': ColumnType.TEXT,
        
        # Generic patterns
        'STRING': ColumnType.STRING,
        'NUMBER': ColumnType.DECIMAL,
        'CURRENCY': ColumnType.DECIMAL,
    }
    
    def __init__(self):
        self.logger = None
        try:
            from utils.logging import get_logger
            self.logger = get_logger(__name__)
        except ImportError:
            pass
    
    def _log(self, message: str, level: str = "info"):
        """Safe logging that works even if logger is not available"""
        if self.logger:
            getattr(self.logger, level)(message)
        else:
            print(f"[{level.upper()}] {message}")
    
    def analyze_table_schema(self, table_info: List[Tuple]) -> Dict[str, Any]:
        """
        Analyze table schema from PRAGMA table_info() results
        Returns normalized schema information
        """
        columns = []
        primary_keys = []
        foreign_keys = []
        
        for col_info in table_info:
            # SQLite PRAGMA table_info format: (cid, name, type, notnull, dflt_value, pk)
            col_id, col_name, col_type, not_null, default_value, is_pk = col_info
            
            # Parse the column
            column_mapping = self._parse_column(col_name, col_type, bool(is_pk), bool(not_null))
            
            columns.append({
                'name': col_name,
                'type': col_type,
                'standard_type': column_mapping.standard_type.value,
                'is_primary_key': column_mapping.is_primary_key,
                'is_foreign_key': column_mapping.is_foreign_key,
                'is_nullable': not bool(not_null),
                'default_value': default_value,
                'constraints': column_mapping.constraints,
                'references': column_mapping.references
            })
            
            if column_mapping.is_primary_key:
                primary_keys.append(col_name)
            
            if column_mapping.is_foreign_key:
                foreign_keys.append({
                    'column': col_name,
                    'references': column_mapping.references
                })
        
        return {
            'columns': columns,
            'primary_keys': primary_keys,
            'foreign_keys': foreign_keys,
            'column_count': len(columns)
        }
    
    def _parse_column(self, name: str, sql_type: str, is_pk: bool, not_null: bool) -> ColumnMapping:
        """
        Parse a single column and determine its standard type and properties
        """
        # Clean up the SQL type
        clean_type = self._normalize_sql_type(sql_type)
        
        # Determine standard type
        standard_type = self._map_sql_type_to_standard(clean_type, name)
        
        # Check for foreign key pattern
        is_foreign_key = self._is_foreign_key_column(name)
        references = None
        if is_foreign_key:
            references = self._guess_foreign_key_reference(name)
        
        # Build constraints
        constraints = []
        if not_null:
            constraints.append("NOT NULL")
        if is_pk:
            constraints.append("PRIMARY KEY")
        if is_foreign_key:
            constraints.append("FOREIGN KEY")
        
        return ColumnMapping(
            standard_type=standard_type,
            sql_type=sql_type,
            constraints=constraints,
            is_primary_key=is_pk,
            is_foreign_key=is_foreign_key,
            references=references
        )
    
    def _normalize_sql_type(self, sql_type: str) -> str:
        """
        Normalize SQL type strings to handle variations
        """
        if not sql_type:
            return "TEXT"
        
        # Remove size specifiers and convert to uppercase
        clean_type = re.sub(r'\(\d+(?:,\d+)?\)', '', sql_type).strip().upper()
        
        # Handle common variations
        if 'VARCHAR' in clean_type or 'CHAR' in clean_type:
            return 'VARCHAR'
        elif 'INT' in clean_type:
            return 'INTEGER'
        elif 'DECIMAL' in clean_type or 'NUMERIC' in clean_type:
            return 'DECIMAL'
        elif 'FLOAT' in clean_type or 'DOUBLE' in clean_type or 'REAL' in clean_type:
            return 'DECIMAL'
        elif 'DATE' in clean_type and 'TIME' in clean_type:
            return 'DATETIME'
        elif 'DATE' in clean_type:
            return 'DATE'
        elif 'TIME' in clean_type:
            return 'DATETIME'
        elif 'BOOL' in clean_type:
            return 'BOOLEAN'
        elif 'TEXT' in clean_type or 'CLOB' in clean_type:
            return 'TEXT'
        elif 'JSON' in clean_type:
            return 'JSON'
        
        return clean_type
    
    def _map_sql_type_to_standard(self, sql_type: str, column_name: str) -> ColumnType:
        """
        Map SQL type to standard ColumnType, considering column name patterns
        """
        # First check direct type mapping
        if sql_type in self.TYPE_MAPPINGS:
            mapped_type = self.TYPE_MAPPINGS[sql_type]
        else:
            # Default mapping based on common patterns
            if 'INT' in sql_type or 'SERIAL' in sql_type:
                mapped_type = ColumnType.INTEGER
            elif 'CHAR' in sql_type or 'VARCHAR' in sql_type:
                mapped_type = ColumnType.STRING
            elif 'TEXT' in sql_type or 'CLOB' in sql_type:
                mapped_type = ColumnType.TEXT
            elif 'DECIMAL' in sql_type or 'NUMERIC' in sql_type or 'FLOAT' in sql_type or 'REAL' in sql_type:
                mapped_type = ColumnType.DECIMAL
            elif 'DATE' in sql_type:
                mapped_type = ColumnType.DATETIME if 'TIME' in sql_type else ColumnType.DATE
            elif 'BOOL' in sql_type:
                mapped_type = ColumnType.BOOLEAN
            elif 'JSON' in sql_type:
                mapped_type = ColumnType.JSON
            else:
                mapped_type = ColumnType.STRING  # Default fallback
        
        # Refine based on column name patterns
        name_lower = column_name.lower()
        
        # Override for specific name patterns
        if self._matches_patterns(name_lower, self.PRICE_PATTERNS):
            return ColumnType.DECIMAL
        elif self._matches_patterns(name_lower, self.DATE_PATTERNS):
            return ColumnType.DATETIME
        elif self._matches_patterns(name_lower, self.BOOLEAN_PATTERNS):
            return ColumnType.BOOLEAN
        elif self._matches_patterns(name_lower, self.ID_PATTERNS):
            return ColumnType.INTEGER
        
        return mapped_type
    
    def _matches_patterns(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any of the given regex patterns"""
        return any(re.match(pattern, text, re.IGNORECASE) for pattern in patterns)
    
    def _is_foreign_key_column(self, column_name: str) -> bool:
        """Check if column name suggests it's a foreign key"""
        name_lower = column_name.lower()
        
        # Skip if it's likely a primary key
        if name_lower == 'id':
            return False
        
        # Check for foreign key patterns
        fk_patterns = [
            r'^.*_id$',     # ends with _id
            r'^.*Id$',      # ends with Id (camelCase)
            r'^fk_.*',      # starts with fk_
        ]
        
        return self._matches_patterns(name_lower, fk_patterns)
    
    def _guess_foreign_key_reference(self, column_name: str) -> Optional[str]:
        """
        Guess what table this foreign key references
        """
        name_lower = column_name.lower()
        
        # Remove common suffixes to get base table name
        if name_lower.endswith('_id'):
            base_name = name_lower[:-3]
        elif name_lower.endswith('id'):
            base_name = name_lower[:-2]
        else:
            return None
        
        # Common table name variations
        possible_tables = [
            base_name,           # users_id -> users
            base_name + 's',     # user_id -> users
            base_name[:-1],      # customers_id -> customer
        ]
        
        # Return the most likely table name
        return possible_tables[1] if not base_name.endswith('s') else possible_tables[0]
    
    def build_robust_query(self, table_schema: Dict[str, Any], query_type: str = "select") -> str:
        """
        Build a robust SQL query based on analyzed schema
        """
        columns = table_schema['columns']
        table_name = "table_name"  # This would be passed in real usage
        
        if query_type == "select":
            # Build SELECT query with proper column handling
            select_columns = []
            
            for col in columns:
                col_name = col['name']
                standard_type = col['standard_type']
                
                # Handle different data types appropriately
                if standard_type == ColumnType.DECIMAL.value:
                    select_columns.append(f"CAST({col_name} AS DECIMAL(10,2)) as {col_name}")
                elif standard_type == ColumnType.DATETIME.value:
                    select_columns.append(f"datetime({col_name}) as {col_name}")
                elif standard_type == ColumnType.DATE.value:
                    select_columns.append(f"date({col_name}) as {col_name}")
                else:
                    select_columns.append(col_name)
            
            return f"SELECT {', '.join(select_columns)} FROM {table_name}"
        
        return f"SELECT * FROM {table_name}"
    
    def get_data_generation_hints(self, table_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate hints for realistic data generation based on schema analysis
        """
        hints = {
            'realistic_ranges': {},
            'data_patterns': {},
            'relationships': [],
            'constraints': {}
        }
        
        for col in table_schema['columns']:
            col_name = col['name']
            standard_type = col['standard_type']
            
            # Set realistic ranges and patterns based on column type and name
            if standard_type == ColumnType.INTEGER.value:
                if self._matches_patterns(col_name.lower(), self.ID_PATTERNS):
                    hints['realistic_ranges'][col_name] = {'min': 1, 'max': 10000}
                else:
                    hints['realistic_ranges'][col_name] = {'min': 1, 'max': 1000}
            
            elif standard_type == ColumnType.DECIMAL.value:
                if self._matches_patterns(col_name.lower(), self.PRICE_PATTERNS):
                    hints['realistic_ranges'][col_name] = {'min': 1.00, 'max': 10000.00}
                    hints['data_patterns'][col_name] = 'currency'
                else:
                    hints['realistic_ranges'][col_name] = {'min': 0.0, 'max': 1000.0}
            
            elif standard_type == ColumnType.STRING.value:
                if self._matches_patterns(col_name.lower(), self.NAME_PATTERNS):
                    hints['data_patterns'][col_name] = 'name'
                else:
                    hints['data_patterns'][col_name] = 'text'
            
            elif standard_type == ColumnType.DATETIME.value:
                hints['data_patterns'][col_name] = 'recent_date'
            
            elif standard_type == ColumnType.BOOLEAN.value:
                hints['data_patterns'][col_name] = 'boolean'
            
            # Track foreign key relationships
            if col['is_foreign_key']:
                hints['relationships'].append({
                    'column': col_name,
                    'references': col['references'],
                    'type': 'foreign_key'
                })
        
        return hints