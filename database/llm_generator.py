"""
LLM-powered database generator
Generates database schemas and sample data based on user parameters
"""

import json
import re
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from openai import AsyncOpenAI
import sqlalchemy as sa
from sqlalchemy import text

from config.settings import get_settings
from utils.logging import get_logger
from database.connection import get_database
from database.generation_prompts import get_enhanced_schema_prompt, get_enhanced_data_prompt
from database.schema_analyzer import SchemaAnalyzer, ColumnType


class BusinessType(str, Enum):
    """Supported business types for database generation"""
    ECOMMERCE = "ecommerce"
    HEALTHCARE = "healthcare" 
    FINANCE = "finance"
    EDUCATION = "education"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    TECHNOLOGY = "technology"
    HOSPITALITY = "hospitality"
    LOGISTICS = "logistics"
    CONSULTING = "consulting"
    CUSTOM = "custom"


class ComplexityLevel(str, Enum):
    """Database complexity levels"""
    SIMPLE = "simple"      # 3-5 tables
    MEDIUM = "medium"      # 6-12 tables  
    COMPLEX = "complex"    # 13-25 tables
    ENTERPRISE = "enterprise"  # 25+ tables


@dataclass
class DatabaseGenerationParams:
    """Parameters for database generation"""
    business_type: BusinessType
    complexity: ComplexityLevel
    company_description: str
    specific_requirements: List[str]
    include_sample_data: bool = True
    sample_data_size: str = "medium"  # small, medium, large
    additional_context: str = ""


class LLMDatabaseGenerator:
    """
    Uses LLM to generate database schemas and populate with realistic data
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncOpenAI(api_key=self.settings.OPENAI_API_KEY)
        self.logger = get_logger(__name__)
        self.schema_analyzer = SchemaAnalyzer()
        # Simple in-memory cache for schemas and data patterns
        self._schema_cache = {}
        self._data_cache = {}
    
    def _get_cache_key(self, params: DatabaseGenerationParams) -> str:
        """Generate cache key for database generation parameters"""
        key_data = f"{params.business_type.value}_{params.complexity.value}_{params.company_description[:50]}"
        return hashlib.md5(key_data.encode()).hexdigest()[:16]
    
    async def generate_database(self, params: DatabaseGenerationParams, progress_callback=None) -> Dict[str, Any]:
        """
        Generate complete database schema and data based on parameters - WITH CACHING
        """
        try:
            cache_key = self._get_cache_key(params)
            self.logger.info(f"Starting database generation for {params.business_type} business (complexity: {params.complexity})")
            
            if progress_callback:
                await progress_callback("Initializing generation...", 10)
            
            # Check cache first for similar schemas
            if cache_key in self._schema_cache:
                self.logger.info("Using cached schema for similar business profile")
                cached_schema = self._schema_cache[cache_key]
                schema_result = cached_schema['schema_sql']
                parsed_schema = cached_schema['parsed_schema']
                table_count = len(parsed_schema.get("tables", []))
                self.logger.info(f"Retrieved cached schema with {table_count} tables")
                if progress_callback:
                    await progress_callback("Retrieved cached schema", 50)
            else:
                # Step 1: Generate schema
                self.logger.info("Step 1/3: Generating database schema...")
                if progress_callback:
                    await progress_callback("Generating database schema...", 20)
                
                schema_result = await self._generate_schema(params)
                
                # Step 2: Validate and parse schema
                self.logger.info("Step 2/3: Parsing and validating schema...")
                if progress_callback:
                    await progress_callback("Parsing schema...", 40)
                
                parsed_schema = self._parse_schema(schema_result)
                table_count = len(parsed_schema.get("tables", []))
                self.logger.info(f"Generated schema with {table_count} tables")
                
                # Cache the schema
                self._schema_cache[cache_key] = {
                    'schema_sql': schema_result,
                    'parsed_schema': parsed_schema
                }
                
                if progress_callback:
                    await progress_callback("Schema generation complete", 50)
            
            # Step 3: Generate sample data if requested
            sample_data = None
            if params.include_sample_data:
                self.logger.info("Step 3/3: Generating sample data for all tables...")
                if progress_callback:
                    await progress_callback("Generating sample data...", 70)
                
                sample_data = await self._generate_sample_data(parsed_schema, params)
                data_table_count = len([k for k, v in sample_data.items() if v])
                self.logger.info(f"Generated sample data for {data_table_count} tables")
                
                if progress_callback:
                    await progress_callback("Sample data generation complete", 90)
            else:
                self.logger.info("Step 3/3: Skipping sample data generation (not requested)")
            
            if progress_callback:
                await progress_callback("Database generation completed!", 100)
            
            self.logger.info("Database generation completed successfully!")
            
            return {
                "schema": parsed_schema,
                "sample_data": sample_data,
                "metadata": {
                    "business_type": params.business_type,
                    "complexity": params.complexity,
                    "tables_count": len(parsed_schema.get("tables", [])),
                    "generation_timestamp": self._get_timestamp(),
                    "used_cache": cache_key in self._schema_cache
                }
            }
            
        except Exception as e:
            if progress_callback:
                await progress_callback(f"Error: {str(e)}", -1)
            self.logger.error(f"Error generating database: {str(e)}")
            raise
    
    async def _generate_schema(self, params: DatabaseGenerationParams) -> str:
        """Generate database schema using LLM - OPTIMIZED VERSION"""
        
        # Simplified, more focused prompt for faster generation
        optimized_prompt = f"""Generate SQL database schema for {params.business_type.value} business:

Business: {params.company_description[:150]}
Complexity: {params.complexity.value}
Requirements: {', '.join(params.specific_requirements[:3])}

Create {self._get_table_count_target(params.complexity)} tables with:
- Proper relationships (foreign keys)
- Realistic columns for the business
- Primary keys, constraints
- SQLite/PostgreSQL compatible

Return only SQL CREATE TABLE statements."""
        
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Generate SQL database schemas. Return only SQL statements."},
                {"role": "user", "content": optimized_prompt}
            ],
            temperature=0.3,
            max_tokens=2500  # Reduced from 4000
        )
        
        return response.choices[0].message.content
    
    def _get_table_count_target(self, complexity: ComplexityLevel) -> str:
        """Get target table count for complexity level"""
        targets = {
            ComplexityLevel.SIMPLE: "3-5",
            ComplexityLevel.MEDIUM: "6-10", 
            ComplexityLevel.COMPLEX: "11-18",
            ComplexityLevel.ENTERPRISE: "19-25"
        }
        return targets.get(complexity, "6-10")
    
    async def _generate_sample_data(self, schema: Dict[str, Any], params: DatabaseGenerationParams) -> Dict[str, List[Dict]]:
        """
        Generate sample data for all tables in the schema - OPTIMIZED VERSION
        """
        # For performance, always use batch generation with optimized parameters
        size_mapping = {
            "small": "15-25",      # Reduced from 25-35 for faster generation
            "medium": "30-40",     # Reduced from 50-75 for faster generation  
            "large": "45-60"       # Reduced from 80-120 for faster generation
        }
        record_count = size_mapping.get(params.sample_data_size, "30-40")
        
        self.logger.info(f"Using optimized batch generation for {record_count} records per table")
        return await self._generate_sample_data_batch_optimized(schema, params, record_count)
    
    async def _generate_sample_data_by_table(self, schema: Dict[str, Any], params: DatabaseGenerationParams) -> Dict[str, List[Dict]]:
        """
        Generate sample data table by table to handle larger record counts
        """
        all_sample_data = {}
        tables = schema.get("tables", [])
        
        for i, table in enumerate(tables):
            self.logger.info(f"Generating data for table {i+1}/{len(tables)}: {table['name']}")
            
            try:
                table_data = await self._generate_single_table_data(table, params, all_sample_data)
                all_sample_data[table['name']] = table_data
                self.logger.info(f"Generated {len(table_data)} records for {table['name']}")
                
            except Exception as e:
                self.logger.error(f"Error generating data for table {table['name']}: {e}")
                all_sample_data[table['name']] = []
        
        return all_sample_data
    
    async def _generate_single_table_data(self, table: Dict[str, Any], params: DatabaseGenerationParams, existing_data: Dict[str, List[Dict]]) -> List[Dict]:
        """
        Generate sample data for a single table with referential integrity
        """
        size_mapping = {
            "small": "25-35",
            "medium": "50-75", 
            "large": "80-120"
        }
        record_count = size_mapping.get(params.sample_data_size, "50-75")
        
        # Build context about existing data for foreign keys
        foreign_key_context = ""
        for existing_table, existing_records in existing_data.items():
            if existing_records:
                foreign_key_context += f"\nExisting {existing_table} IDs: {[r.get('id', r.get(f'{existing_table[:-1]}_id', 1)) for r in existing_records[:10]]}"
        
        prompt = f"""
        Generate realistic sample data for the '{table['name']}' table in a {params.business_type.value} business.
        
        Business Context: {params.company_description}
        
        Table Schema:
        Table: {table['name']}
        Columns: {', '.join([f"{col['name']} ({col['type']})" for col in table['columns']])}
        
        Requirements:
        1. **CRITICAL**: Generate EXACTLY {record_count} records
        2. Use realistic data appropriate for: {params.company_description}
        3. Ensure proper data types and formats
        4. For foreign keys, use existing IDs from related tables
        5. Make the data realistic and business-appropriate
        
        {foreign_key_context}
        
        **IMPORTANT**: Return ONLY a valid JSON array. No explanations, no markdown, no code blocks.
        
        Start with [ and end with ]. Each record should be a JSON object with proper comma separation.
        
        Example format:
        [
          {{"id": 1, "column1": "value1", "column2": "value2"}},
          {{"id": 2, "column1": "value3", "column2": "value4"}}
        ]
        
        Generate exactly {record_count} records for {table['name']}:
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a data generation expert. Generate realistic sample data in JSON array format. Return ONLY the JSON array, no additional text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=4000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up the content - remove markdown code blocks if present
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            # Extract JSON array from response
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                try:
                    table_data = json.loads(json_match.group())
                    return table_data
                except json.JSONDecodeError as e:
                    # Try to fix common JSON issues
                    json_str = json_match.group()
                    # Fix trailing commas
                    json_str = re.sub(r',\s*}', '}', json_str)
                    json_str = re.sub(r',\s*]', ']', json_str)
                    try:
                        table_data = json.loads(json_str)
                        return table_data
                    except json.JSONDecodeError:
                        self.logger.error(f"JSON parsing failed for table {table['name']}: {e}")
                        self.logger.error(f"Content sample: {content[:200]}...")
                        return []
            else:
                self.logger.warning(f"Could not find JSON array in response for table {table['name']}")
                self.logger.warning(f"Response sample: {content[:200]}...")
                return []
                
        except Exception as e:
            self.logger.error(f"Error generating data for table {table['name']}: {e}")
            return []
    
    async def _generate_sample_data_batch(self, schema: Dict[str, Any], params: DatabaseGenerationParams) -> Dict[str, List[Dict]]:
        """Generate realistic sample data for the schema in a single API call"""
        
        self.logger.info("Generating sample data for all tables in one batch")
        
        # Build comprehensive prompt for all tables
        tables_info = []
        for table in schema.get("tables", []):
            columns = table.get("columns", [])
            column_info = ", ".join([f"{col['name']} ({col['type']})" for col in columns])
            tables_info.append(f"Table '{table['name']}': {column_info}")
        
        size_mapping = {
            "small": "20-30",
            "medium": "50-100", 
            "large": "100-200"
        }
        record_count = size_mapping.get(params.sample_data_size, "50-100")
        
        batch_prompt = f"""
        Generate realistic sample data for ALL tables in this {params.business_type.value} business database.
        
        Business Context:
        - Type: {params.business_type.value}
        - Company Description: {params.company_description}
        - Complexity: {params.complexity.value}
        
        Database Schema:
        {chr(10).join(tables_info)}
        
        IMPORTANT: Base the sample data on the company description "{params.company_description}":
        - Generate products/services that match what this specific business actually offers
        - Use realistic names, categories, and attributes for their industry
        - Create customer data that reflects their target market
        - Include business processes and workflows specific to their operations
        
        Requirements:
        1. **CRITICAL**: Generate EXACTLY {record_count} records per table - NOT 10, but {record_count}!
        2. Ensure referential integrity (foreign keys must match primary keys)
        3. Use realistic data appropriate for the specific company description
        4. Make data internally consistent across tables
        5. Follow proper data formats (dates, numbers, etc.)
        6. Products/services should directly relate to the company description
        7. Create diverse, varied data that represents a real business in operation
        8. Include realistic customer demographics, purchase patterns, and business activity
        9. Generate meaningful product catalogs, inventory levels, and transaction history
        10. Use industry-appropriate terminology, pricing, and business practices
        
        **REMEMBER**: You MUST generate {record_count} records per table, not just 10!
        
        Return a JSON object where each key is a table name and each value is an array of records.
        
        Example format:
        {{
            "table1": [
                {{"column1": "value1", "column2": "value2"}},
                {{"column1": "value3", "column2": "value4"}}
            ],
            "table2": [
                {{"column1": "value5", "column2": "value6"}}
            ]
        }}
        
        IMPORTANT: Return ONLY the JSON object, no additional text or explanations.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a data generation expert. Generate realistic sample data in JSON format for entire database schemas. Always maintain referential integrity."},
                    {"role": "user", "content": batch_prompt}
                ],
                temperature=0.5,
                max_tokens=6000  # Reduced to fit context limit
            )
            
            # Parse the JSON response
            data_content = response.choices[0].message.content.strip()
            
            # Extract JSON from response (handle cases where LLM adds explanation)
            json_match = re.search(r'\{.*\}', data_content, re.DOTALL)
            if json_match:
                sample_data = json.loads(json_match.group())
                self.logger.info(f"Generated sample data for {len(sample_data)} tables")
                return sample_data
            else:
                self.logger.warning("Could not parse batch sample data response")
                return {}
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing batch sample data: {e}")
            self.logger.error(f"Response content: {data_content[:500]}...")
            return {}
        except Exception as e:
            self.logger.error(f"Error generating batch sample data: {str(e)}")
            return {}
    
    async def _generate_sample_data_batch(self, schema: Dict[str, Any], params: DatabaseGenerationParams) -> Dict[str, List[Dict]]:
        """
        Generate sample data for all tables in one batch (for smaller datasets)
        """
        tables_info = []
        for table in schema.get("tables", []):
            column_info = ", ".join([f"{col['name']} ({col['type']})" for col in table['columns']])
            tables_info.append(f"Table '{table['name']}': {column_info}")
        
        size_mapping = {
            "small": "20-30",
            "medium": "50-100", 
            "large": "100-200"
        }
        record_count = size_mapping.get(params.sample_data_size, "50-100")
        
        batch_prompt = f"""
        Generate realistic sample data for ALL tables in this {params.business_type.value} business database.
        
        Business Context:
        - Type: {params.business_type.value}
        - Company Description: {params.company_description}
        - Complexity: {params.complexity.value}
        
        Database Schema:
        {chr(10).join(tables_info)}
        
        IMPORTANT: Base the sample data on the company description "{params.company_description}":
        - Generate products/services that match what this specific business actually offers
        - Use realistic names, categories, and attributes for their industry
        - Create customer data that reflects their target market
        - Include business processes and workflows specific to their operations
        
        Requirements:
        1. **CRITICAL**: Generate EXACTLY {record_count} records per table - NOT 10, but {record_count}!
        2. Ensure referential integrity (foreign keys must match primary keys)
        3. Use realistic data appropriate for the specific company description
        4. Make data internally consistent across tables
        5. Follow proper data formats (dates, numbers, etc.)
        6. Products/services should directly relate to the company description
        7. Create diverse, varied data that represents a real business in operation
        8. Include realistic customer demographics, purchase patterns, and business activity
        9. Generate meaningful product catalogs, inventory levels, and transaction history
        10. Use industry-appropriate terminology, pricing, and business practices
        
        **REMEMBER**: You MUST generate {record_count} records per table, not just 10!
        
        Return a JSON object where each key is a table name and each value is an array of records.
        
        Example format:
        {{
            "table1": [
                {{"column1": "value1", "column2": "value2"}},
                {{"column1": "value3", "column2": "value4"}}
            ],
            "table2": [
                {{"column1": "value5", "column2": "value6"}}
            ]
        }}
        
        IMPORTANT: Return ONLY the JSON object, no additional text or explanations.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a data generation expert. Generate realistic sample data in JSON format for entire database schemas. Always maintain referential integrity."},
                    {"role": "user", "content": batch_prompt}
                ],
                temperature=0.5,
                max_tokens=6000  # Reduced to fit context limit
            )
            
            # Parse the JSON response
            data_content = response.choices[0].message.content.strip()
            
            # Extract JSON from response (handle cases where LLM adds explanation)
            json_match = re.search(r'\{.*\}', data_content, re.DOTALL)
            if json_match:
                sample_data = json.loads(json_match.group())
                self.logger.info(f"Generated sample data for {len(sample_data)} tables")
                return sample_data
            else:
                self.logger.warning("Could not parse batch sample data response")
                return {}
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing batch sample data: {e}")
            self.logger.error(f"Response content: {data_content[:500]}...")
            return {}
        except Exception as e:
            self.logger.error(f"Error generating batch sample data: {str(e)}")
            return {}
    
    async def _generate_sample_data_batch_optimized(self, schema: Dict[str, Any], params: DatabaseGenerationParams, record_count: str) -> Dict[str, List[Dict]]:
        """
        OPTIMIZED: Generate sample data for all tables with robust schema handling and reduced prompt size
        """
        tables = schema.get("tables", [])
        if not tables:
            return {}
        
        # Analyze schema for better data generation
        enhanced_tables = []
        for table in tables:
            table_analysis = self._analyze_table_for_generation(table)
            enhanced_tables.append(table_analysis)
        
        # Create compact but robust table descriptions with data type hints
        table_specs = []
        for table_analysis in enhanced_tables:
            table = table_analysis['table']
            hints = table_analysis['hints']
            
            # Build column specifications with type hints
            columns = []
            for col in table['columns'][:8]:  # Limit columns for brevity
                col_spec = f"{col['name']}:{col['type']}"
                
                # Add generation hints for better data quality
                if col['name'] in hints['data_patterns']:
                    pattern = hints['data_patterns'][col['name']]
                    if pattern == 'currency':
                        col_spec += "(price)"
                    elif pattern == 'name':
                        col_spec += "(name)"
                    elif pattern == 'recent_date':
                        col_spec += "(date)"
                    elif pattern == 'boolean':
                        col_spec += "(true/false)"
                
                columns.append(col_spec)
            
            table_specs.append(f"{table['name']}({', '.join(columns)})")
        
        # Compact, focused prompt for faster generation with robust type handling
        optimized_prompt = f"""Generate {record_count} realistic records per table for {params.business_type.value} business: "{params.company_description[:100]}..."

Tables: {' | '.join(table_specs)}

CRITICAL: Return ONLY valid JSON, no explanation:
{{"table1": [{{"col1": "val1", "col2": "val2"}}], "table2": [...]}}

Data Type Rules:
- IDs: sequential integers (1,2,3...)
- Prices: decimal numbers (e.g., 29.99)
- Dates: "YYYY-MM-DD" format
- Booleans: true/false (not "true"/"false")
- Names: realistic text appropriate for business
- Foreign keys: reference existing IDs from related tables

Generate exactly {record_count} records per table with proper data types."""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a data generation expert. Generate realistic sample data in valid JSON format. Follow data type requirements precisely."},
                    {"role": "user", "content": optimized_prompt}
                ],
                temperature=0.5,
                max_tokens=3000  # Reduced for faster processing
            )
            
            content = response.choices[0].message.content.strip()
            
            # Robust JSON parsing with fallback strategies
            sample_data = self._parse_json_with_fallbacks(content, enhanced_tables)
            
            if sample_data:
                # Validate and clean data types
                cleaned_data = self._validate_and_clean_data(sample_data, enhanced_tables)
                self.logger.info(f"Generated optimized sample data for {len(cleaned_data)} tables")
                return cleaned_data
            else:
                self.logger.warning("Optimized generation failed, using fallback")
                return await self._fallback_data_generation(enhanced_tables, params, record_count)
                
        except Exception as e:
            self.logger.error(f"Optimized generation failed: {str(e)}")
            return await self._fallback_data_generation(enhanced_tables, params, record_count)
    
    def _analyze_table_for_generation(self, table: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze table structure for better data generation hints
        """
        # Mock table_info format for schema analyzer
        table_info = []
        for i, col in enumerate(table['columns']):
            # Format: (cid, name, type, notnull, dflt_value, pk)
            is_pk = col.get('primary_key', False) or col.get('name', '').lower() == 'id'
            table_info.append((i, col['name'], col['type'], 1, None, 1 if is_pk else 0))
        
        schema_analysis = self.schema_analyzer.analyze_table_schema(table_info)
        hints = self.schema_analyzer.get_data_generation_hints(schema_analysis)
        
        return {
            'table': table,
            'schema_analysis': schema_analysis,
            'hints': hints
        }
    
    def _parse_json_with_fallbacks(self, content: str, enhanced_tables: List[Dict]) -> Optional[Dict]:
        """
        Parse JSON content with multiple fallback strategies
        """
        # Strategy 1: Direct JSON parsing
        try:
            # Clean content first
            cleaned_content = self._clean_json_content(content)
            return json.loads(cleaned_content)
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Extract JSON block from response
        try:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                cleaned_content = self._clean_json_content(json_match.group())
                return json.loads(cleaned_content)
        except json.JSONDecodeError:
            pass
        
        # Strategy 3: Line-by-line JSON reconstruction
        try:
            return self._reconstruct_json_from_lines(content, enhanced_tables)
        except Exception:
            pass
        
        self.logger.warning("All JSON parsing strategies failed")
        return None
    
    def _clean_json_content(self, content: str) -> str:
        """
        Clean JSON content to handle common LLM output issues
        """
        # Remove markdown code blocks
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*$', '', content)
        
        # Remove explanatory text before/after JSON
        lines = content.split('\n')
        start_idx = None
        end_idx = None
        
        for i, line in enumerate(lines):
            if line.strip().startswith('{'):
                start_idx = i
                break
        
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip().endswith('}'):
                end_idx = i
                break
        
        if start_idx is not None and end_idx is not None:
            content = '\n'.join(lines[start_idx:end_idx + 1])
        
        # Fix common JSON issues
        content = re.sub(r',\s*}', '}', content)  # Remove trailing commas
        content = re.sub(r',\s*]', ']', content)   # Remove trailing commas in arrays
        
        return content.strip()
    
    def _reconstruct_json_from_lines(self, content: str, enhanced_tables: List[Dict]) -> Dict:
        """
        Attempt to reconstruct valid JSON from malformed content
        """
        table_names = [t['table']['name'] for t in enhanced_tables]
        result = {}
        
        lines = content.split('\n')
        current_table = None
        current_records = []
        
        for line in lines:
            line = line.strip()
            
            # Look for table names
            for table_name in table_names:
                if table_name in line and ':' in line:
                    if current_table and current_records:
                        result[current_table] = current_records
                    current_table = table_name
                    current_records = []
                    break
            
            # Look for record-like structures
            if '{' in line and '}' in line and current_table:
                try:
                    # Extract potential JSON object
                    obj_match = re.search(r'\{[^}]+\}', line)
                    if obj_match:
                        obj = json.loads(obj_match.group())
                        current_records.append(obj)
                except json.JSONDecodeError:
                    continue
        
        # Add final table
        if current_table and current_records:
            result[current_table] = current_records
        
        return result if result else {}
    
    def _validate_and_clean_data(self, sample_data: Dict, enhanced_tables: List[Dict]) -> Dict:
        """
        Validate and clean generated data to ensure proper types and constraints
        """
        cleaned_data = {}
        table_map = {t['table']['name']: t for t in enhanced_tables}
        
        for table_name, records in sample_data.items():
            if table_name not in table_map:
                continue
            
            table_analysis = table_map[table_name]
            schema_analysis = table_analysis['schema_analysis']
            
            cleaned_records = []
            for record in records:
                cleaned_record = self._clean_record(record, schema_analysis)
                if cleaned_record:
                    cleaned_records.append(cleaned_record)
            
            cleaned_data[table_name] = cleaned_records
        
        return cleaned_data
    
    def _clean_record(self, record: Dict, schema_analysis: Dict) -> Optional[Dict]:
        """
        Clean a single record to ensure proper data types
        """
        if not isinstance(record, dict):
            return None
        
        cleaned_record = {}
        
        for column in schema_analysis['columns']:
            col_name = column['name']
            standard_type = column['standard_type']
            
            if col_name in record:
                value = record[col_name]
                cleaned_value = self._convert_value_to_type(value, standard_type)
                cleaned_record[col_name] = cleaned_value
            else:
                # Generate default value if missing
                cleaned_record[col_name] = self._generate_default_value(standard_type)
        
        return cleaned_record
    
    def _convert_value_to_type(self, value: Any, standard_type: str) -> Any:
        """
        Convert value to the appropriate type based on schema
        """
        if value is None:
            return None
        
        try:
            if standard_type == ColumnType.INTEGER.value:
                if isinstance(value, str):
                    # Extract numbers from string
                    numbers = re.findall(r'\d+', str(value))
                    if numbers:
                        return int(numbers[0])
                return int(float(value))
            
            elif standard_type == ColumnType.DECIMAL.value:
                if isinstance(value, str):
                    # Extract decimal numbers from string
                    numbers = re.findall(r'\d+\.?\d*', str(value))
                    if numbers:
                        return float(numbers[0])
                return float(value)
            
            elif standard_type == ColumnType.BOOLEAN.value:
                if isinstance(value, str):
                    return value.lower() in ['true', '1', 'yes', 'on']
                return bool(value)
            
            elif standard_type in [ColumnType.DATE.value, ColumnType.DATETIME.value]:
                if isinstance(value, str):
                    # Try to extract date pattern
                    date_match = re.search(r'\d{4}-\d{2}-\d{2}', str(value))
                    if date_match:
                        return date_match.group()
                return str(value)
            
            else:  # String, Text, JSON
                return str(value)
                
        except (ValueError, TypeError):
            return self._generate_default_value(standard_type)
    
    def _generate_default_value(self, standard_type: str) -> Any:
        """
        Generate appropriate default value for a data type
        """
        if standard_type == ColumnType.INTEGER.value:
            return 1
        elif standard_type == ColumnType.DECIMAL.value:
            return 0.0
        elif standard_type == ColumnType.BOOLEAN.value:
            return False
        elif standard_type == ColumnType.DATE.value:
            return "2024-01-01"
        elif standard_type == ColumnType.DATETIME.value:
            return "2024-01-01 12:00:00"
        else:
            return "default"
    
    async def _fallback_data_generation(self, enhanced_tables: List[Dict], params: DatabaseGenerationParams, record_count: str) -> Dict:
        """
        Fallback data generation when optimized generation fails
        """
        self.logger.info("Using fallback data generation")
        fallback_data = {}
        
        # Extract numeric count from record_count string
        count_match = re.search(r'\d+', record_count)
        num_records = int(count_match.group()) if count_match else 10
        
        for table_analysis in enhanced_tables:
            table = table_analysis['table']
            table_name = table['name']
            
            self.logger.info(f"Fallback generation for {table_name}")
            
            # Generate minimal realistic data
            records = []
            for i in range(min(num_records, 15)):  # Limit fallback to 15 records
                record = {}
                for col in table['columns']:
                    col_name = col['name']
                    col_type = col['type'].upper()
                    
                    if 'ID' in col_name.upper() and col_name.lower() != 'product_id':
                        record[col_name] = i + 1
                    elif 'NAME' in col_name.upper():
                        record[col_name] = f"Sample {table_name[:-1] if table_name.endswith('s') else table_name} {i + 1}"
                    elif 'PRICE' in col_name.upper() or 'COST' in col_name.upper():
                        record[col_name] = round(10.0 + (i * 5.0), 2)
                    elif 'DATE' in col_name.upper():
                        record[col_name] = f"2024-01-{(i % 28) + 1:02d}"
                    elif 'INT' in col_type or 'SERIAL' in col_type:
                        record[col_name] = i + 1
                    elif 'DECIMAL' in col_type or 'FLOAT' in col_type or 'REAL' in col_type:
                        record[col_name] = round(i * 1.5, 2)
                    elif 'BOOL' in col_type:
                        record[col_name] = i % 2 == 0
                    else:
                        record[col_name] = f"Value {i + 1}"
                
                records.append(record)
            
            fallback_data[table_name] = records
        
        return fallback_data
    
    def _get_schema_generation_prompt(self) -> str:
        """Get system prompt for schema generation"""
        return """
        You are a senior database architect with expertise in designing efficient, scalable database schemas.
        
        Your task is to generate comprehensive database schemas based on business requirements.
        
        Guidelines:
        1. Use appropriate data types (VARCHAR, INTEGER, DECIMAL, TIMESTAMP, BOOLEAN, etc.)
        2. Create proper relationships with foreign keys
        3. Add necessary constraints (NOT NULL, UNIQUE, CHECK)
        4. Include indexes for performance optimization
        5. Use clear, descriptive table and column names
        6. Add meaningful comments for documentation
        7. Follow database normalization principles
        8. Consider common business patterns and requirements
        9. Include audit fields (created_at, updated_at) where appropriate
        10. Design for scalability and maintainability
        
        Generate production-ready SQL that can be executed directly.
        Ensure the schema supports the business operations described.
        """
    
    def _get_data_generation_prompt(self, table: Dict[str, Any], params: DatabaseGenerationParams) -> str:
        """Get prompt for generating sample data"""
        
        columns = table.get("columns", [])
        column_info = "\n".join([f"- {col['name']}: {col['type']}" for col in columns])
        
        size_mapping = {
            "small": "20-30",
            "medium": "50-100", 
            "large": "100-200"
        }
        
        record_count = size_mapping.get(params.sample_data_size, "50-100")
        
        return f"""
        Generate realistic sample data for the following database table:
        
        Table: {table['name']}
        Business Type: {params.business_type.value}
        Industry: {params.company_description}
        
        Columns:
        {column_info}
        
        Requirements:
        1. Generate {record_count} realistic records (CREATE SUBSTANTIAL DATASETS)
        2. Ensure data is appropriate for {params.business_type.value} business
        3. Use realistic names, addresses, dates, and values specific to the company description
        4. Respect foreign key relationships if any
        5. Follow data type constraints
        6. Make data internally consistent and business-logical
        7. Create diverse, varied data representing real business operations
        8. Use industry-appropriate terminology and realistic pricing
        9. Include meaningful product descriptions, customer demographics
        10. Generate realistic transaction patterns and business activity
        
        Return ONLY a JSON array of objects, where each object represents one record.
        Use appropriate data formats (ISO dates, proper numbers, etc.).
        
        Example format:
        [
            {{"column1": "value1", "column2": "value2"}},
            {{"column1": "value3", "column2": "value4"}}
        ]
        """
    
    def _parse_schema(self, schema_sql: str) -> Dict[str, Any]:
        """Parse the generated SQL schema into structured format"""
        
        self.logger.info(f"Parsing schema SQL (length: {len(schema_sql)} chars)")
        
        # Extract table information using regex
        tables = []
        
        # Find all CREATE TABLE statements
        table_pattern = r'CREATE\s+TABLE\s+(\w+)\s*\((.*?)\);'
        table_matches = re.findall(table_pattern, schema_sql, re.DOTALL | re.IGNORECASE)
        
        self.logger.info(f"Found {len(table_matches)} CREATE TABLE statements")
        
        for table_name, table_definition in table_matches:
            columns = []
            
            # Parse column definitions
            column_lines = [line.strip() for line in table_definition.split('\n') if line.strip()]
            
            for line in column_lines:
                if not line.startswith('--') and not line.upper().startswith(('PRIMARY', 'FOREIGN', 'CONSTRAINT', 'INDEX')):
                    # Basic column parsing
                    parts = line.replace(',', '').split()
                    if len(parts) >= 2:
                        col_name = parts[0]
                        col_type = parts[1]
                        columns.append({
                            "name": col_name,
                            "type": col_type,
                            "definition": line
                        })
            
            table_obj = {
                "name": table_name,
                "columns": columns,
                "sql": f"CREATE TABLE {table_name} ({table_definition});"
            }
            tables.append(table_obj)
            self.logger.info(f"Parsed table '{table_name}' with {len(columns)} columns")
        
        result = {
            "raw_sql": schema_sql,
            "tables": tables
        }
        
        self.logger.info(f"Schema parsing complete: {len(tables)} tables parsed")
        return result
    
    async def deploy_schema(self, schema: Dict[str, Any], backup_existing: bool = True) -> Dict[str, Any]:
        """Deploy the generated schema to the database"""
        
        try:
            db = get_database()
            async with db.get_session() as session:
                
                # Backup existing schema if requested
                if backup_existing:
                    await self._backup_existing_schema(session)
                
                # Drop existing tables (be careful!)
                await self._drop_existing_tables(session)
                
                # Execute new schema
                for table in schema["tables"]:
                    self.logger.info(f"Creating table: {table['name']}")
                    await session.execute(text(table["sql"]))
                
                await session.commit()
                
                return {
                    "success": True,
                    "tables_created": len(schema["tables"]),
                    "message": "Database schema deployed successfully"
                }
                
        except Exception as e:
            self.logger.error(f"Error deploying schema: {str(e)}")
            raise
    
    async def deploy_sample_data(self, sample_data: Dict[str, List[Dict]], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy sample data to the database"""
        
        try:
            db = get_database()
            async with db.get_session() as session:
                
                total_records = 0
                
                for table_name, records in sample_data.items():
                    if not records:
                        continue
                        
                    self.logger.info(f"Inserting {len(records)} records into {table_name}")
                    
                    # Build insert statement
                    if records:
                        columns = list(records[0].keys())
                        placeholders = ", ".join([f":{col}" for col in columns])
                        insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                        
                        await session.execute(text(insert_sql), records)
                        total_records += len(records)
                
                await session.commit()
                
                return {
                    "success": True,
                    "total_records": total_records,
                    "tables_populated": len([k for k, v in sample_data.items() if v]),
                    "message": "Sample data deployed successfully"
                }
                
        except Exception as e:
            self.logger.error(f"Error deploying sample data: {str(e)}")
            raise
    
    async def _backup_existing_schema(self, session):
        """Create backup of existing schema"""
        # Implementation for schema backup
        pass
    
    async def _drop_existing_tables(self, session):
        """Drop existing tables"""
        # Implementation to safely drop tables
        pass
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()


# Factory function for easy usage
async def generate_database(params: DatabaseGenerationParams) -> Dict[str, Any]:
    """
    Factory function to generate a database with given parameters
    """
    generator = LLMDatabaseGenerator()
    return await generator.generate_database(params)
