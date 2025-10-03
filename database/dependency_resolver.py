"""
Enhanced Table Dependency Resolver
==================================

Analyzes SQL schema to detect foreign key relationships and determine
optimal table generation order for maintaining referential integrity.
"""

import re
import sqlparse
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass

from utils.logging import get_logger


@dataclass
class ForeignKeyRelation:
    """Represents a foreign key relationship between tables"""
    source_table: str
    source_column: str
    target_table: str
    target_column: str


class TableDependencyResolver:
    """
    Analyzes database schema to determine table generation order
    based on foreign key dependencies
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
    def resolve_dependencies(self, schema_sql: str, tables: List[Dict]) -> Tuple[List[str], Dict[str, List[str]]]:
        """
        Analyze schema and return generation order and dependency mapping
        
        Returns:
            - generation_order: List of table names in order they should be generated
            - dependency_map: Dict mapping table_name -> list of tables it depends on
        """
        try:
            # Extract foreign key relationships from SQL
            foreign_keys = self._extract_foreign_keys(schema_sql)
            
            # Build dependency graph
            dependency_graph = self._build_dependency_graph(tables, foreign_keys)
            
            # Perform topological sort
            generation_order = self._topological_sort(dependency_graph)
            
            self.logger.info(f"Resolved dependencies for {len(tables)} tables")
            self.logger.info(f"Generation order: {generation_order}")
            
            return generation_order, dependency_graph
            
        except Exception as e:
            self.logger.error(f"Error resolving dependencies: {str(e)}")
            # Fallback: return tables in original order
            table_names = [table["name"] for table in tables]
            return table_names, {table: [] for table in table_names}
    
    def _extract_foreign_keys(self, schema_sql: str) -> List[ForeignKeyRelation]:
        """Extract foreign key relationships from SQL schema"""
        foreign_keys = []
        
        try:
            # Parse SQL statements
            statements = sqlparse.split(schema_sql)
            
            for statement in statements:
                if not statement.strip():
                    continue
                    
                # Parse the statement
                parsed = sqlparse.parse(statement)[0]
                
                # Extract table name
                table_name = self._extract_table_name(parsed)
                if not table_name:
                    continue
                
                # Find foreign key constraints
                fks = self._find_foreign_keys_in_statement(parsed, table_name)
                foreign_keys.extend(fks)
                
        except Exception as e:
            self.logger.warning(f"Error parsing SQL for foreign keys: {str(e)}")
            # Fallback to regex-based extraction
            foreign_keys = self._extract_foreign_keys_regex(schema_sql)
        
        self.logger.info(f"Found {len(foreign_keys)} foreign key relationships")
        return foreign_keys
    
    def _extract_table_name(self, parsed_statement) -> Optional[str]:
        """Extract table name from CREATE TABLE statement"""
        tokens = list(parsed_statement.flatten())
        
        create_found = False
        table_found = False
        
        for token in tokens:
            if token.ttype is sqlparse.tokens.Keyword and token.value.upper() == 'CREATE':
                create_found = True
            elif create_found and token.ttype is sqlparse.tokens.Keyword and token.value.upper() == 'TABLE':
                table_found = True
            elif table_found and token.ttype is None and token.value.strip():
                # This should be the table name
                return token.value.strip().strip('`\"[]')
                
        return None
    
    def _find_foreign_keys_in_statement(self, parsed_statement, table_name: str) -> List[ForeignKeyRelation]:
        """Find foreign key constraints in a parsed SQL statement"""
        foreign_keys = []
        tokens = list(parsed_statement.flatten())
        
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            # Look for FOREIGN KEY or REFERENCES keywords
            if token.ttype is sqlparse.tokens.Keyword:
                if token.value.upper() == 'FOREIGN':
                    # Try to parse FOREIGN KEY constraint
                    fk = self._parse_foreign_key_constraint(tokens, i, table_name)
                    if fk:
                        foreign_keys.append(fk)
                elif token.value.upper() == 'REFERENCES':
                    # Try to parse inline REFERENCES
                    fk = self._parse_references_constraint(tokens, i, table_name)
                    if fk:
                        foreign_keys.append(fk)
            
            i += 1
        
        return foreign_keys
    
    def _parse_foreign_key_constraint(self, tokens: List, start_idx: int, table_name: str) -> Optional[ForeignKeyRelation]:
        """Parse FOREIGN KEY (...) REFERENCES table(...) constraint"""
        try:
            # Look for pattern: FOREIGN KEY (column) REFERENCES table(column)
            i = start_idx
            
            # Skip to opening parenthesis after FOREIGN KEY
            while i < len(tokens) and tokens[i].value != '(':
                i += 1
            
            if i >= len(tokens):
                return None
                
            # Get source column
            i += 1
            source_column = None
            while i < len(tokens) and tokens[i].value != ')':
                if tokens[i].ttype is None and tokens[i].value.strip():
                    source_column = tokens[i].value.strip().strip('`\"[]')
                    break
                i += 1
            
            if not source_column:
                return None
            
            # Look for REFERENCES keyword
            while i < len(tokens) and tokens[i].value.upper() != 'REFERENCES':
                i += 1
                
            if i >= len(tokens):
                return None
                
            # Get target table
            i += 1
            target_table = None
            while i < len(tokens):
                if tokens[i].ttype is None and tokens[i].value.strip() and tokens[i].value != '(':
                    target_table = tokens[i].value.strip().strip('`\"[]')
                    break
                i += 1
            
            if not target_table:
                return None
            
            # Get target column (assume 'id' if not specified)
            target_column = 'id'
            
            # Look for target column in parentheses
            while i < len(tokens) and tokens[i].value != '(':
                i += 1
            
            if i < len(tokens):
                i += 1
                while i < len(tokens) and tokens[i].value != ')':
                    if tokens[i].ttype is None and tokens[i].value.strip():
                        target_column = tokens[i].value.strip().strip('`\"[]')
                        break
                    i += 1
            
            return ForeignKeyRelation(
                source_table=table_name,
                source_column=source_column,
                target_table=target_table,
                target_column=target_column
            )
            
        except Exception as e:
            self.logger.debug(f"Error parsing foreign key constraint: {str(e)}")
            return None
    
    def _parse_references_constraint(self, tokens: List, start_idx: int, table_name: str) -> Optional[ForeignKeyRelation]:
        """Parse inline REFERENCES table(column) constraint"""
        try:
            # Look backwards for column name
            i = start_idx - 1
            source_column = None
            
            while i >= 0:
                if tokens[i].ttype is None and tokens[i].value.strip() and tokens[i].value not in [',', '(', ')']:
                    # Skip data types
                    if tokens[i].value.upper() not in ['INTEGER', 'TEXT', 'VARCHAR', 'INT', 'CHAR', 'BOOLEAN', 'REAL']:
                        source_column = tokens[i].value.strip().strip('`\"[]')
                        break
                i -= 1
            
            if not source_column:
                return None
            
            # Look forward for target table
            i = start_idx + 1
            target_table = None
            
            while i < len(tokens):
                if tokens[i].ttype is None and tokens[i].value.strip() and tokens[i].value != '(':
                    target_table = tokens[i].value.strip().strip('`\"[]')
                    break
                i += 1
            
            if not target_table:
                return None
            
            # Get target column (default to 'id')
            target_column = 'id'
            
            # Look for target column in parentheses
            while i < len(tokens) and tokens[i].value != '(':
                i += 1
            
            if i < len(tokens):
                i += 1
                while i < len(tokens) and tokens[i].value != ')':
                    if tokens[i].ttype is None and tokens[i].value.strip():
                        target_column = tokens[i].value.strip().strip('`\"[]')
                        break
                    i += 1
            
            return ForeignKeyRelation(
                source_table=table_name,
                source_column=source_column,
                target_table=target_table,
                target_column=target_column
            )
            
        except Exception as e:
            self.logger.debug(f"Error parsing references constraint: {str(e)}")
            return None
    
    def _extract_foreign_keys_regex(self, schema_sql: str) -> List[ForeignKeyRelation]:
        """Fallback regex-based foreign key extraction"""
        foreign_keys = []
        
        # Pattern for FOREIGN KEY constraints
        fk_pattern = r'FOREIGN\s+KEY\s*\(\s*([^)]+)\s*\)\s+REFERENCES\s+([^\s(]+)\s*(?:\(\s*([^)]+)\s*\))?'
        
        # Pattern for inline REFERENCES
        ref_pattern = r'(\w+)\s+[^,\n]*REFERENCES\s+([^\s(]+)\s*(?:\(\s*([^)]+)\s*\))?'
        
        # Find all CREATE TABLE statements
        table_pattern = r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([^\s(]+)\s*\('
        
        tables_sql = re.findall(table_pattern, schema_sql, re.IGNORECASE)
        statements = re.split(r'CREATE\s+TABLE', schema_sql, flags=re.IGNORECASE)
        
        for i, statement in enumerate(statements[1:]):  # Skip first empty split
            if i < len(tables_sql):
                table_name = tables_sql[i].strip().strip('`\"[]')
                
                # Find FOREIGN KEY constraints
                for match in re.finditer(fk_pattern, statement, re.IGNORECASE):
                    source_col = match.group(1).strip().strip('`\"[]')
                    target_table = match.group(2).strip().strip('`\"[]')
                    target_col = match.group(3).strip().strip('`\"[]') if match.group(3) else 'id'
                    
                    foreign_keys.append(ForeignKeyRelation(
                        source_table=table_name,
                        source_column=source_col,
                        target_table=target_table,
                        target_column=target_col
                    ))
                
                # Find inline REFERENCES
                for match in re.finditer(ref_pattern, statement, re.IGNORECASE):
                    source_col = match.group(1).strip().strip('`\"[]')
                    target_table = match.group(2).strip().strip('`\"[]')
                    target_col = match.group(3).strip().strip('`\"[]') if match.group(3) else 'id'
                    
                    foreign_keys.append(ForeignKeyRelation(
                        source_table=table_name,
                        source_column=source_col,
                        target_table=target_table,
                        target_column=target_col
                    ))
        
        return foreign_keys
    
    def _build_dependency_graph(self, tables: List[Dict], foreign_keys: List[ForeignKeyRelation]) -> Dict[str, List[str]]:
        """Build dependency graph from foreign key relationships"""
        # Initialize graph with all tables
        table_names = [table["name"] for table in tables]
        dependency_graph = {table: [] for table in table_names}
        
        # Add dependencies based on foreign keys
        for fk in foreign_keys:
            if fk.source_table in dependency_graph and fk.target_table in table_names:
                if fk.target_table not in dependency_graph[fk.source_table]:
                    dependency_graph[fk.source_table].append(fk.target_table)
        
        return dependency_graph
    
    def _topological_sort(self, dependency_graph: Dict[str, List[str]]) -> List[str]:
        """
        Perform topological sort to determine generation order
        
        Tables with no dependencies come first, then tables that depend on them, etc.
        """
        # Calculate in-degrees (number of dependencies)
        in_degree = {table: 0 for table in dependency_graph}
        
        for table, dependencies in dependency_graph.items():
            for dep in dependencies:
                if dep in in_degree:
                    in_degree[table] += 1
        
        # Start with tables that have no dependencies
        queue = [table for table, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            # Sort by table name for consistent ordering
            queue.sort()
            current = queue.pop(0)
            result.append(current)
            
            # Find tables that depend on the current table
            for table, dependencies in dependency_graph.items():
                if current in dependencies:
                    in_degree[table] -= 1
                    if in_degree[table] == 0:
                        queue.append(table)
        
        # Check for circular dependencies
        if len(result) != len(dependency_graph):
            self.logger.warning("Circular dependencies detected, using fallback ordering")
            # Fallback: return remaining tables in alphabetical order
            remaining = set(dependency_graph.keys()) - set(result)
            result.extend(sorted(remaining))
        
        return result