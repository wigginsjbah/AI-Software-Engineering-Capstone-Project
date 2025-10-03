"""
Database migration handler for safely deploying generated schemas
"""

import os
import json
import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import sqlalchemy as sa
from sqlalchemy import text, MetaData, create_engine
from sqlalchemy.exc import SQLAlchemyError

from config.settings import get_settings
from database.connection import get_database
from utils.logging import get_logger


class DatabaseMigrationHandler:
    """
    Handles safe migration to new database schemas with backup and rollback capabilities
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.backup_dir = Path("database/backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    async def deploy_new_schema(
        self, 
        schema: Dict[str, Any], 
        sample_data: Optional[Dict[str, List[Dict]]] = None,
        backup_existing: bool = True,
        validate_first: bool = True
    ) -> Dict[str, Any]:
        """
        Deploy a new schema with proper backup and validation
        """
        deployment_id = self._generate_deployment_id()
        
        try:
            self.logger.info(f"Starting schema deployment {deployment_id}")
            
            # Step 1: Validate schema
            if validate_first:
                validation_result = await self._validate_schema(schema)
                if not validation_result['valid']:
                    return {
                        'success': False,
                        'error': 'Schema validation failed',
                        'details': validation_result['errors']
                    }
            
            # Step 2: Create backup
            backup_info = None
            if backup_existing:
                backup_info = await self._create_backup(deployment_id)
            
            # Step 3: Deploy new schema
            deployment_result = await self._execute_schema_deployment(schema)
            
            # Step 4: Populate with sample data if provided
            if sample_data and deployment_result['success']:
                data_result = await self._deploy_sample_data(sample_data)
                deployment_result['data_deployment'] = data_result
            
            # Step 5: Record deployment
            await self._record_deployment(deployment_id, schema, backup_info, deployment_result)
            
            return {
                'success': deployment_result['success'],
                'deployment_id': deployment_id,
                'backup_info': backup_info,
                'tables_created': deployment_result.get('tables_created', 0),
                'records_inserted': deployment_result.get('data_deployment', {}).get('total_records', 0),
                'message': 'Schema deployed successfully'
            }
            
        except Exception as e:
            self.logger.error(f"Error in schema deployment {deployment_id}: {str(e)}")
            
            # Attempt rollback if backup exists
            if backup_existing and 'backup_info' in locals():
                await self._rollback_to_backup(backup_info)
            
            return {
                'success': False,
                'error': str(e),
                'deployment_id': deployment_id
            }
    
    async def _validate_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate schema before deployment"""
        
        errors = []
        warnings = []
        
        try:
            tables = schema.get('tables', [])
            
            if not tables:
                errors.append("No tables found in schema")
                return {'valid': False, 'errors': errors}
            
            table_names = set()
            
            for table in tables:
                table_name = table.get('name')
                if not table_name:
                    errors.append("Table missing name")
                    continue
                
                if table_name in table_names:
                    errors.append(f"Duplicate table name: {table_name}")
                
                table_names.add(table_name)
                
                # Validate columns
                columns = table.get('columns', [])
                if not columns:
                    errors.append(f"Table {table_name} has no columns")
                    continue
                
                column_names = set()
                has_primary_key = False
                
                for column in columns:
                    col_name = column.get('name')
                    col_type = column.get('type')
                    
                    if not col_name:
                        errors.append(f"Column in table {table_name} missing name")
                        continue
                    
                    if col_name in column_names:
                        errors.append(f"Duplicate column name {col_name} in table {table_name}")
                    
                    column_names.add(col_name)
                    
                    if not col_type:
                        errors.append(f"Column {col_name} in table {table_name} missing type")
                    
                    # Check for primary key
                    if col_name.lower() == 'id' or 'primary key' in column.get('definition', '').lower():
                        has_primary_key = True
                
                if not has_primary_key:
                    warnings.append(f"Table {table_name} has no apparent primary key")
            
            # Test SQL syntax
            for table in tables:
                sql = table.get('sql', '')
                if sql:
                    try:
                        # Basic syntax check (create in-memory SQLite)
                        test_engine = create_engine('sqlite:///:memory:')
                        with test_engine.connect() as conn:
                            conn.execute(text(sql))
                    except SQLAlchemyError as e:
                        errors.append(f"SQL syntax error in table {table.get('name')}: {str(e)}")
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings
            }
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Validation error: {str(e)}"]
            }
    
    async def _create_backup(self, deployment_id: str) -> Dict[str, Any]:
        """Create backup of existing database"""
        
        try:
            backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{deployment_id}_{backup_timestamp}.db"
            backup_path = self.backup_dir / backup_filename
            
            # For SQLite databases, we can copy the file
            if 'sqlite' in self.settings.DATABASE_URL.lower():
                db_path = self.settings.DATABASE_URL.replace('sqlite:///', '')
                if os.path.exists(db_path):
                    import shutil
                    shutil.copy2(db_path, backup_path)
                    
                    # Also create a metadata backup
                    metadata_backup = await self._export_database_metadata()
                    metadata_path = self.backup_dir / f"metadata_{deployment_id}_{backup_timestamp}.json"
                    with open(metadata_path, 'w') as f:
                        json.dump(metadata_backup, f, indent=2, default=str)
                    
                    return {
                        'backup_path': str(backup_path),
                        'metadata_path': str(metadata_path),
                        'timestamp': backup_timestamp,
                        'size_mb': round(backup_path.stat().st_size / (1024 * 1024), 2)
                    }
            
            # For other databases, export schema and data
            schema_backup = await self._export_schema_as_sql()
            backup_path = self.backup_dir / f"schema_backup_{deployment_id}_{backup_timestamp}.sql"
            with open(backup_path, 'w') as f:
                f.write(schema_backup)
            
            return {
                'backup_path': str(backup_path),
                'timestamp': backup_timestamp,
                'type': 'schema_export'
            }
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {str(e)}")
            raise
    
    async def _export_database_metadata(self) -> Dict[str, Any]:
        """Export current database metadata"""
        
        try:
            db = get_database()
            async with db.get_session() as session:
                metadata = {}
                
                # Get table information
                if 'sqlite' in self.settings.DATABASE_URL.lower():
                    result = await session.execute(text(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ))
                    tables = [row[0] for row in result]
                    
                    metadata['tables'] = {}
                    for table in tables:
                        # Get column info
                        result = await session.execute(text(f"PRAGMA table_info({table})"))
                        columns = []
                        for row in result:
                            columns.append({
                                'name': row[1],
                                'type': row[2],
                                'not_null': bool(row[3]),
                                'default': row[4],
                                'primary_key': bool(row[5])
                            })
                        
                        # Get row count
                        result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        row_count = result.scalar()
                        
                        metadata['tables'][table] = {
                            'columns': columns,
                            'row_count': row_count
                        }
                
                return metadata
                
        except Exception as e:
            self.logger.error(f"Error exporting metadata: {str(e)}")
            return {}
    
    async def _export_schema_as_sql(self) -> str:
        """Export current schema as SQL"""
        
        try:
            db = get_database()
            async with db.get_session() as session:
                sql_statements = []
                
                if 'sqlite' in self.settings.DATABASE_URL.lower():
                    # Export SQLite schema
                    result = await session.execute(text(
                        "SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL"
                    ))
                    
                    for row in result:
                        sql_statements.append(row[0] + ';')
                
                return '\n\n'.join(sql_statements)
                
        except Exception as e:
            self.logger.error(f"Error exporting schema: {str(e)}")
            return ""
    
    async def _execute_schema_deployment(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the schema deployment"""
        
        try:
            db = get_database()
            async with db.get_session() as session:
                
                # Drop existing tables (in correct order to handle foreign keys)
                await self._drop_existing_tables(session)
                
                # Create new tables
                tables = schema.get('tables', [])
                tables_created = 0
                
                for table in tables:
                    table_sql = table.get('sql', '')
                    if table_sql:
                        self.logger.info(f"Creating table: {table.get('name')}")
                        await session.execute(text(table_sql))
                        tables_created += 1
                
                await session.commit()
                
                return {
                    'success': True,
                    'tables_created': tables_created
                }
                
        except Exception as e:
            self.logger.error(f"Error executing schema deployment: {str(e)}")
            raise
    
    async def _deploy_sample_data(self, sample_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Deploy sample data to the database"""
        
        try:
            db = get_database()
            async with db.get_session() as session:
                
                total_records = 0
                tables_populated = 0
                
                # Sort tables by dependency (simple approach: tables with no foreign keys first)
                sorted_tables = self._sort_tables_by_dependency(sample_data)
                
                for table_name in sorted_tables:
                    records = sample_data.get(table_name, [])
                    if not records:
                        continue
                    
                    self.logger.info(f"Inserting {len(records)} records into {table_name}")
                    
                    # Build insert statement
                    columns = list(records[0].keys())
                    placeholders = ", ".join([f":{col}" for col in columns])
                    insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                    
                    await session.execute(text(insert_sql), records)
                    total_records += len(records)
                    tables_populated += 1
                
                await session.commit()
                
                return {
                    'success': True,
                    'total_records': total_records,
                    'tables_populated': tables_populated
                }
                
        except Exception as e:
            self.logger.error(f"Error deploying sample data: {str(e)}")
            raise
    
    def _sort_tables_by_dependency(self, sample_data: Dict[str, List[Dict]]) -> List[str]:
        """Sort tables by dependency to avoid foreign key issues"""
        
        # Simple heuristic: tables with '_id' columns come after their referenced tables
        independent_tables = []
        dependent_tables = []
        
        for table_name, records in sample_data.items():
            if records:
                has_foreign_keys = any(
                    col.endswith('_id') and col != 'id' 
                    for col in records[0].keys()
                )
                
                if has_foreign_keys:
                    dependent_tables.append(table_name)
                else:
                    independent_tables.append(table_name)
        
        return independent_tables + dependent_tables
    
    async def _drop_existing_tables(self, session):
        """Drop existing tables safely"""
        
        try:
            if 'sqlite' in self.settings.DATABASE_URL.lower():
                # Get all tables
                result = await session.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                ))
                tables = [row[0] for row in result]
                
                # Drop tables (disable foreign key checks first)
                await session.execute(text("PRAGMA foreign_keys = OFF"))
                
                for table in tables:
                    await session.execute(text(f"DROP TABLE IF EXISTS {table}"))
                
                await session.execute(text("PRAGMA foreign_keys = ON"))
                
        except Exception as e:
            self.logger.error(f"Error dropping tables: {str(e)}")
            raise
    
    async def _record_deployment(
        self, 
        deployment_id: str, 
        schema: Dict[str, Any], 
        backup_info: Optional[Dict[str, Any]], 
        result: Dict[str, Any]
    ):
        """Record deployment information"""
        
        deployment_record = {
            'deployment_id': deployment_id,
            'timestamp': datetime.now().isoformat(),
            'schema_summary': {
                'tables_count': len(schema.get('tables', [])),
                'table_names': [t.get('name') for t in schema.get('tables', [])]
            },
            'backup_info': backup_info,
            'result': result
        }
        
        # Save to deployment log
        log_path = self.backup_dir / "deployment_log.json"
        
        try:
            if log_path.exists():
                with open(log_path, 'r') as f:
                    log_data = json.load(f)
            else:
                log_data = {'deployments': []}
            
            log_data['deployments'].append(deployment_record)
            
            with open(log_path, 'w') as f:
                json.dump(log_data, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Error recording deployment: {str(e)}")
    
    async def _rollback_to_backup(self, backup_info: Dict[str, Any]):
        """Rollback to a previous backup"""
        
        try:
            backup_path = backup_info.get('backup_path')
            if backup_path and os.path.exists(backup_path):
                
                if 'sqlite' in self.settings.DATABASE_URL.lower():
                    db_path = self.settings.DATABASE_URL.replace('sqlite:///', '')
                    import shutil
                    shutil.copy2(backup_path, db_path)
                    self.logger.info(f"Rolled back to backup: {backup_path}")
                    
        except Exception as e:
            self.logger.error(f"Error during rollback: {str(e)}")
    
    def _generate_deployment_id(self) -> str:
        """Generate unique deployment ID"""
        from uuid import uuid4
        return str(uuid4())[:8]
    
    async def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups"""
        
        backups = []
        
        try:
            for file_path in self.backup_dir.glob("backup_*.db"):
                stat = file_path.stat()
                backups.append({
                    'filename': file_path.name,
                    'path': str(file_path),
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'created': datetime.fromtimestamp(stat.st_ctime).isoformat()
                })
            
            return sorted(backups, key=lambda x: x['created'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error listing backups: {str(e)}")
            return []


# Factory function
def create_migration_handler() -> DatabaseMigrationHandler:
    """Create a database migration handler"""
    return DatabaseMigrationHandler()