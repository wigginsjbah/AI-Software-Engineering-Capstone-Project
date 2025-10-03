"""
Robust Batch Data Generation Pipeline
=====================================

Multi-stage pipeline for reliable database population:
1. Schema Analysis → Table Dependency Mapping  
2. Sequential Generation → Validation & Retry
3. Ensures all tables reach target record counts

Key Features:
- Table dependency resolution (foreign key ordering)
- Per-table generation with focused context
- Validation and retry mechanisms
- Progress tracking and error recovery
- Domain-specific generation strategies
"""

import asyncio
import json
import re
import sqlite3
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import sqlparse
from openai import AsyncOpenAI

from config.settings import get_settings
from utils.logging import get_logger
from database.schema_analyzer import SchemaAnalyzer
from database.dependency_resolver import TableDependencyResolver


class GenerationStage(str, Enum):
    """Pipeline stages for batch generation"""
    ANALYZING = "analyzing"
    MAPPING_DEPENDENCIES = "mapping_dependencies"
    GENERATING_DATA = "generating_data"
    VALIDATING = "validating"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TableGenerationPlan:
    """Plan for generating data for a specific table"""
    table_name: str
    generation_order: int  # 0 = no dependencies, higher = depends on others
    dependencies: List[str]  # Tables this table depends on
    target_records: int
    domain_context: str
    generation_hints: Dict[str, Any]


@dataclass
class GenerationProgress:
    """Track progress of batch generation"""
    stage: GenerationStage
    completed_tables: List[str]
    failed_tables: List[str]
    current_table: Optional[str]
    total_tables: int
    progress_percentage: float


class RobustBatchGenerator:
    """
    Robust batch data generation pipeline that ensures all tables are populated
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncOpenAI(api_key=self.settings.OPENAI_API_KEY)
        self.logger = get_logger(__name__)
        self.schema_analyzer = SchemaAnalyzer()
        self.dependency_resolver = TableDependencyResolver()
        
        # Pipeline state
        self.generation_plans: List[TableGenerationPlan] = []
        self.progress: GenerationProgress = None
        self.generated_data: Dict[str, List[Dict]] = {}
        self.schema_sql: str = ""  # Store original schema SQL for dependency analysis
        
    async def generate_all_tables(
        self, 
        schema: Dict[str, Any], 
        schema_sql: str,
        business_context: str,
        target_records_per_table: int = 50,
        progress_callback=None
    ) -> Dict[str, List[Dict]]:
        """
        Main entry point: Generate data for all tables with robust error handling
        """
        try:
            tables = schema.get("tables", [])
            self.schema_sql = schema_sql
            
            if not tables:
                self.logger.warning("No tables found in schema")
                return {}
                
            self.logger.info(f"Starting robust batch generation for {len(tables)} tables")
            
            # Initialize progress tracking
            self.progress = GenerationProgress(
                stage=GenerationStage.ANALYZING,
                completed_tables=[],
                failed_tables=[],
                current_table=None,
                total_tables=len(tables),
                progress_percentage=0.0
            )
            
            # Stage 1: Analyze schema and build generation plans
            await self._update_progress(GenerationStage.ANALYZING, progress_callback)
            await self._analyze_and_plan(schema, business_context, target_records_per_table)
            
            # Stage 2: Map table dependencies and determine generation order
            await self._update_progress(GenerationStage.MAPPING_DEPENDENCIES, progress_callback)
            await self._resolve_dependencies()
            
            # Stage 3: Generate data table by table in dependency order
            await self._update_progress(GenerationStage.GENERATING_DATA, progress_callback)
            await self._generate_in_order(business_context, progress_callback)
            
            # Stage 4: Validate all tables have correct record counts
            await self._update_progress(GenerationStage.VALIDATING, progress_callback)
            validation_results = await self._validate_generation()
            
            # Stage 5: Retry failed tables if needed
            if validation_results["failed_tables"]:
                await self._update_progress(GenerationStage.RETRYING, progress_callback)
                await self._retry_failed_tables(business_context, validation_results["failed_tables"])
                
                # Re-validate after retry
                final_validation = await self._validate_generation()
                if final_validation["failed_tables"]:
                    self.logger.warning(f"Some tables still failed after retry: {final_validation['failed_tables']}")
            
            # Stage 6: Complete
            await self._update_progress(GenerationStage.COMPLETED, progress_callback)
            
            success_count = len(self.progress.completed_tables)
            total_count = self.progress.total_tables
            self.logger.info(f"Batch generation completed: {success_count}/{total_count} tables successful")
            
            return self.generated_data
            
        except Exception as e:
            self.logger.error(f"Batch generation pipeline failed: {str(e)}")
            await self._update_progress(GenerationStage.FAILED, progress_callback)
            raise
    
    async def _analyze_and_plan(self, schema: Dict[str, Any], business_context: str, target_records: int):
        """Stage 1: Analyze schema and create generation plans for each table"""
        tables = schema.get("tables", [])
        self.generation_plans = []
        
        for table in tables:
            # Analyze table for domain-specific context
            domain_context = await self._analyze_table_domain(table, business_context)
            
            # Get generation hints from schema analyzer - Create table_info format
            table_info = []
            for i, col in enumerate(table.get("columns", [])):
                # Convert to PRAGMA table_info format: (cid, name, type, notnull, dflt_value, pk)
                col_name = col.get("name", f"col_{i}")
                col_type = col.get("type", "TEXT")
                is_pk = col.get("is_primary_key", False) or col_name.lower() == "id"
                not_null = not col.get("is_nullable", True)
                default_value = col.get("default_value", None)
                
                table_info.append((i, col_name, col_type, not_null, default_value, is_pk))
            
            # Get generation hints using the correct format
            if table_info:
                generation_hints = self.schema_analyzer.analyze_table_schema(table_info)
            else:
                generation_hints = {
                    'columns': [],
                    'primary_keys': [],
                    'foreign_keys': [],
                    'column_count': 0
                }
            
            plan = TableGenerationPlan(
                table_name=table["name"],
                generation_order=0,  # Will be updated in dependency resolution
                dependencies=[],      # Will be populated in dependency resolution
                target_records=target_records,
                domain_context=domain_context,
                generation_hints=generation_hints
            )
            
            self.generation_plans.append(plan)
            
        self.logger.info(f"Created generation plans for {len(self.generation_plans)} tables")
    
    async def _resolve_dependencies(self):
        """Stage 2: Analyze foreign key dependencies and determine generation order"""
        self.logger.info("Resolving table dependencies...")
        
        # Use the dependency resolver to analyze the schema
        generation_order, dependency_graph = self.dependency_resolver.resolve_dependencies(
            self.schema_sql, 
            [{"name": plan.table_name} for plan in self.generation_plans]
        )
        
        # Update generation order and dependencies in plans
        order_map = {table: i for i, table in enumerate(generation_order)}
        
        for plan in self.generation_plans:
            plan.generation_order = order_map.get(plan.table_name, 999)
            plan.dependencies = dependency_graph.get(plan.table_name, [])
        
        # Sort plans by generation order
        self.generation_plans.sort(key=lambda p: p.generation_order)
        
        self.logger.info(f"Dependency resolution complete. Generation order: {[p.table_name for p in self.generation_plans]}")
        
        # Log dependency relationships
        for plan in self.generation_plans:
            if plan.dependencies:
                self.logger.info(f"Table '{plan.table_name}' depends on: {plan.dependencies}")
    
    async def _generate_in_order(self, business_context: str, progress_callback=None):
        """Stage 3: Generate data for each table in dependency order"""
        self.logger.info("Starting sequential table generation...")
        
        for i, plan in enumerate(self.generation_plans):
            try:
                self.progress.current_table = plan.table_name
                
                # Update progress
                progress_pct = 20 + (i / len(self.generation_plans)) * 60  # 20-80% for generation phase
                self.progress.progress_percentage = progress_pct
                if progress_callback:
                    await progress_callback(f"Generating {plan.table_name}...", progress_pct)
                
                self.logger.info(f"Generating data for table {i+1}/{len(self.generation_plans)}: {plan.table_name}")
                
                # Generate data for this table
                table_data = await self._generate_single_table_robust(plan, business_context)
                
                if table_data and len(table_data) > 0:
                    self.generated_data[plan.table_name] = table_data
                    self.progress.completed_tables.append(plan.table_name)
                    self.logger.info(f"✓ Generated {len(table_data)} records for {plan.table_name}")
                else:
                    self.progress.failed_tables.append(plan.table_name)
                    self.logger.warning(f"✗ Failed to generate data for {plan.table_name}")
                
            except Exception as e:
                self.logger.error(f"Error generating data for {plan.table_name}: {str(e)}")
                self.progress.failed_tables.append(plan.table_name)
        
        self.progress.current_table = None
    
    async def _generate_single_table_robust(self, plan: TableGenerationPlan, business_context: str) -> List[Dict]:
        """Generate data for a single table with robust error handling"""
        
        # Build context from already-generated tables
        reference_context = self._build_reference_context(plan)
        
        # Create focused prompt for this specific table
        prompt = self._build_table_generation_prompt(plan, business_context, reference_context)
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": """You are a specialized data generator. Your ONLY job is to generate valid JSON arrays.

CRITICAL RULES:
1. Return ONLY a JSON array, nothing else
2. Use double quotes for all strings
3. Ensure all JSON objects are complete and properly closed
4. No trailing commas after the last object
5. No explanations, no markdown, no additional text

RESPONSE FORMAT: [{"key": "value"}, {"key": "value"}]"""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent formatting
                max_tokens=4000,  # Increased token limit for larger datasets
                top_p=0.8,        # Reduce randomness for better structure
                frequency_penalty=0.1,  # Slight penalty to reduce repetition
                presence_penalty=0.1    # Encourage variety while maintaining structure
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse and validate the response
            data = self._parse_and_validate_response(content, plan)
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error in LLM call for {plan.table_name}: {str(e)}")
            return []
    
    def _build_table_generation_prompt(self, plan: TableGenerationPlan, business_context: str, reference_context: str) -> str:
        """Build a focused prompt for generating data for a specific table"""
        
        # Extract column information for clearer guidance
        columns_info = []
        if 'columns' in plan.generation_hints:
            for col in plan.generation_hints['columns']:
                col_name = col.get('name', 'unknown')
                col_type = col.get('type', 'TEXT')
                columns_info.append(f"  {col_name}: {col_type}")
        
        columns_str = "\n".join(columns_info) if columns_info else "  (column information not available)"
        
        return f"""Generate realistic sample data for the '{plan.table_name}' table.

Business Context: {business_context}
Domain Context: {plan.domain_context}

Table Schema:
{columns_str}

{reference_context}

CRITICAL REQUIREMENTS:
1. Generate EXACTLY {plan.target_records} records
2. Return ONLY a valid JSON array - no explanations, no markdown, no additional text
3. Each record must be a complete JSON object with all required fields
4. Use realistic data appropriate for: {business_context}
5. Ensure ALL strings are properly quoted with double quotes
6. Do NOT use single quotes, use double quotes only
7. End every record with a comma except the last one
8. Make sure the JSON is properly terminated

FORMAT EXAMPLE:
[
  {{"id": 1, "name": "John Doe", "email": "john@example.com"}},
  {{"id": 2, "name": "Jane Smith", "email": "jane@example.com"}}
]

IMPORTANT: 
- Start with [ and end with ]
- Every string must use double quotes "like this"
- No trailing commas after the last object
- Each object must be complete and valid JSON

Generate {plan.target_records} records for {plan.table_name} table following the exact format above:"""

    def _build_reference_context(self, plan: TableGenerationPlan) -> str:
        """Build context about already-generated tables for foreign key references"""
        context_parts = []
        
        for dep_table in plan.dependencies:
            if dep_table in self.generated_data:
                dep_data = self.generated_data[dep_table]
                if dep_data:
                    # Show sample IDs from dependent tables
                    sample_ids = [record.get('id', 1) for record in dep_data[:10]]
                    context_parts.append(f"Available {dep_table} IDs: {sample_ids}")
        
        if context_parts:
            return "Reference Data:\n" + "\n".join(context_parts) + "\n"
        else:
            return ""
    
    def _parse_and_validate_response(self, content: str, plan: TableGenerationPlan) -> List[Dict]:
        """Parse LLM response and validate the data with ENHANCED error recovery"""
        
        # Step 1: Enhanced content cleaning
        cleaned_content = self._aggressively_clean_json_content(content)
        
        # Step 2: Multiple parsing strategies
        parsing_strategies = [
            self._parse_direct_json,
            self._parse_with_json_repair,
            self._parse_with_regex_extraction,
            self._parse_with_manual_fixes,
            self._parse_with_truncation
        ]
        
        for i, strategy in enumerate(parsing_strategies):
            try:
                self.logger.debug(f"Trying parsing strategy {i+1} for {plan.table_name}")
                data = strategy(cleaned_content, plan)
                
                if data and isinstance(data, list) and len(data) > 0:
                    self.logger.info(f"✓ Successfully parsed {plan.table_name} with strategy {i+1}: {len(data)} records")
                    
                    # Validate record count
                    if len(data) < plan.target_records * 0.5:  # At least 50% of target
                        self.logger.warning(f"Low record count for {plan.table_name}: {len(data)}/{plan.target_records}")
                    
                    return data
                    
            except Exception as e:
                self.logger.debug(f"Strategy {i+1} failed for {plan.table_name}: {str(e)}")
                continue
        
        # All strategies failed
        self.logger.error(f"All parsing strategies failed for {plan.table_name}")
        self.logger.debug(f"Original content length: {len(content)}, cleaned length: {len(cleaned_content)}")
        self.logger.debug(f"Content preview: {cleaned_content[:300]}...")
        return []
    
    def _aggressively_clean_json_content(self, content: str) -> str:
        """Aggressively clean LLM response to extract valid JSON"""
        
        # Remove markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            # Handle cases where it's just ``` without json
            parts = content.split("```")
            if len(parts) >= 3:
                content = parts[1]
            elif len(parts) == 2:
                # Might be missing closing ```
                content = parts[1]
        
        # Remove common prefixes and suffixes
        content = content.strip()
        
        # Remove explanatory text before JSON
        patterns_to_remove_before = [
            r'^.*?(?=\[)',  # Remove everything before first [
            r'^[^[]*',      # Remove non-array characters at start
        ]
        
        for pattern in patterns_to_remove_before:
            import re
            match = re.search(pattern, content, re.DOTALL)
            if match and match.start() > 0:
                content = content[match.end():]
                break
        
        # Remove explanatory text after JSON
        # Find the last ] and cut everything after it
        last_bracket = content.rfind(']')
        if last_bracket != -1:
            # Look for any non-whitespace after the bracket
            after_bracket = content[last_bracket + 1:].strip()
            if after_bracket and not after_bracket.startswith(','):
                content = content[:last_bracket + 1]
        
        # Fix common JSON issues
        content = self._fix_common_json_issues(content)
        
        return content.strip()
    
    def _fix_common_json_issues(self, content: str) -> str:
        """Fix common JSON formatting issues"""
        import re
        
        # Fix unterminated strings (add missing quotes)
        # This is complex - for now, we'll rely on other strategies
        
        # Fix trailing commas
        content = re.sub(r',\s*}', '}', content)
        content = re.sub(r',\s*]', ']', content)
        
        # Fix missing commas between objects
        content = re.sub(r'}\s*{', '}, {', content)
        
        # Fix single quotes to double quotes
        content = re.sub(r"'([^']*)':", r'"\1":', content)
        content = re.sub(r":\s*'([^']*)'", r': "\1"', content)
        
        # Fix Python-style booleans
        content = content.replace('True', 'true')
        content = content.replace('False', 'false')
        content = content.replace('None', 'null')
        
        return content
    
    def _parse_direct_json(self, content: str, plan: TableGenerationPlan) -> List[Dict]:
        """Strategy 1: Direct JSON parsing"""
        return json.loads(content)
    
    def _parse_with_json_repair(self, content: str, plan: TableGenerationPlan) -> List[Dict]:
        """Strategy 2: Attempt to repair malformed JSON"""
        import re
        
        # Try to fix unterminated strings by finding patterns
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # If line has an odd number of quotes, try to fix it
            quote_count = line.count('"')
            if quote_count % 2 != 0:
                # Try to add a closing quote before common terminators
                if line.rstrip().endswith(','):
                    line = line.rstrip()[:-1] + '",'
                elif line.rstrip().endswith('}'):
                    line = line.rstrip()[:-1] + '"}'
                elif line.rstrip().endswith(']'):
                    line = line.rstrip()[:-1] + '"]'
                else:
                    line = line.rstrip() + '"'
            
            fixed_lines.append(line)
        
        repaired_content = '\n'.join(fixed_lines)
        return json.loads(repaired_content)
    
    def _parse_with_regex_extraction(self, content: str, plan: TableGenerationPlan) -> List[Dict]:
        """Strategy 3: Extract JSON objects using regex"""
        import re
        
        # Find all JSON object patterns
        object_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(object_pattern, content, re.DOTALL)
        
        objects = []
        for match in matches:
            try:
                obj = json.loads(match)
                if isinstance(obj, dict):
                    objects.append(obj)
            except:
                continue
        
        return objects
    
    def _parse_with_manual_fixes(self, content: str, plan: TableGenerationPlan) -> List[Dict]:
        """Strategy 4: Manual fixes for common issues"""
        
        # Try to extract just the array content
        start = content.find('[')
        end = content.rfind(']')
        
        if start == -1 or end == -1 or start >= end:
            raise ValueError("No valid array structure found")
        
        array_content = content[start:end+1]
        
        # Try to fix the array by parsing individual objects
        # Remove the outer brackets
        inner_content = array_content[1:-1].strip()
        
        if not inner_content:
            return []
        
        # Split by },{ pattern and fix each object
        import re
        
        # Split objects while preserving the braces
        object_parts = re.split(r'}\s*,\s*{', inner_content)
        
        objects = []
        for i, part in enumerate(object_parts):
            # Add back the braces
            if i == 0 and not part.strip().startswith('{'):
                part = '{' + part
            if i == len(object_parts) - 1 and not part.strip().endswith('}'):
                part = part + '}'
            if i > 0 and i < len(object_parts) - 1:
                part = '{' + part + '}'
            
            part = part.strip()
            
            # Try to parse this object
            try:
                obj = json.loads(part)
                objects.append(obj)
            except json.JSONDecodeError:
                # Try to fix common issues in this object
                fixed_part = self._fix_object_json(part)
                try:
                    obj = json.loads(fixed_part)
                    objects.append(obj)
                except:
                    self.logger.debug(f"Could not parse object part: {part[:100]}...")
                    continue
        
        return objects
    
    def _fix_object_json(self, obj_str: str) -> str:
        """Fix JSON issues in a single object"""
        import re
        
        # Fix unterminated strings by looking for quote patterns
        # This is a simplified approach
        
        # Find all key-value pairs
        lines = obj_str.split('\n')
        fixed_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and braces
            if not line or line in ['{', '}']:
                fixed_lines.append(line)
                continue
            
            # Check if this looks like a key-value pair
            if ':' in line:
                # Fix quote issues
                if line.count('"') % 2 != 0:
                    # Try to add missing quote
                    if line.endswith(','):
                        line = line[:-1] + '",'
                    elif line.endswith('}'):
                        line = line[:-1] + '"}'
                    else:
                        line = line + '"'
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _parse_with_truncation(self, content: str, plan: TableGenerationPlan) -> List[Dict]:
        """Strategy 5: Parse partial JSON by truncating at last complete object"""
        
        # Find the array start
        start = content.find('[')
        if start == -1:
            raise ValueError("No array start found")
        
        # Find complete objects within the array
        objects = []
        brace_count = 0
        current_object = ""
        in_string = False
        escape_next = False
        
        content_from_array = content[start+1:]  # Skip the opening [
        
        for char in content_from_array:
            if escape_next:
                escape_next = False
                current_object += char
                continue
            
            if char == '\\':
                escape_next = True
                current_object += char
                continue
            
            if char == '"' and not escape_next:
                in_string = not in_string
                current_object += char
                continue
            
            if in_string:
                current_object += char
                continue
            
            if char == '{':
                brace_count += 1
                current_object += char
            elif char == '}':
                brace_count -= 1
                current_object += char
                
                # If we've closed all braces, we have a complete object
                if brace_count == 0 and current_object.strip():
                    try:
                        obj = json.loads(current_object.strip())
                        objects.append(obj)
                        current_object = ""
                    except:
                        # This object is malformed, skip it
                        current_object = ""
            elif char == ']':
                # End of array
                break
            elif char == ',':
                if brace_count == 0:
                    # Comma between objects
                    current_object = ""
                else:
                    current_object += char
            else:
                current_object += char
        
        return objects
    
    async def _validate_generation(self) -> Dict[str, Any]:
        """Stage 4: Validate that all tables have the correct number of records"""
        self.logger.info("Validating generation results...")
        
        successful_tables = []
        failed_tables = []
        
        for plan in self.generation_plans:
            table_name = plan.table_name
            target_count = plan.target_records
            
            if table_name in self.generated_data:
                actual_count = len(self.generated_data[table_name])
                if actual_count >= target_count * 0.8:  # Allow 20% tolerance
                    successful_tables.append(table_name)
                else:
                    failed_tables.append(table_name)
                    self.logger.warning(f"Table {table_name}: expected ~{target_count}, got {actual_count}")
            else:
                failed_tables.append(table_name)
                self.logger.warning(f"Table {table_name}: no data generated")
        
        return {
            "successful_tables": successful_tables,
            "failed_tables": failed_tables,
            "success_rate": len(successful_tables) / len(self.generation_plans) if self.generation_plans else 0
        }
    
    async def _retry_failed_tables(self, business_context: str, failed_tables: List[str]):
        """Stage 5: Retry generation for failed tables"""
        self.logger.info(f"Retrying generation for {len(failed_tables)} failed tables...")
        
        for table_name in failed_tables:
            try:
                plan = next(p for p in self.generation_plans if p.table_name == table_name)
                
                self.logger.info(f"Retrying {table_name}...")
                
                # Try with simplified approach
                table_data = await self._generate_single_table_robust(plan, business_context)
                
                if table_data and len(table_data) > 0:
                    self.generated_data[table_name] = table_data
                    self.progress.completed_tables.append(table_name)
                    if table_name in self.progress.failed_tables:
                        self.progress.failed_tables.remove(table_name)
                    self.logger.info(f"✓ Retry successful for {table_name}: {len(table_data)} records")
                
            except Exception as e:
                self.logger.error(f"Retry failed for {table_name}: {str(e)}")
    
    async def _update_progress(self, stage: GenerationStage, progress_callback=None):
        """Update pipeline progress and notify callback"""
        self.progress.stage = stage
        
        stage_progress = {
            GenerationStage.ANALYZING: 5,
            GenerationStage.MAPPING_DEPENDENCIES: 15,
            GenerationStage.GENERATING_DATA: 50,  # This will be updated during generation
            GenerationStage.VALIDATING: 85,
            GenerationStage.RETRYING: 90,
            GenerationStage.COMPLETED: 100,
            GenerationStage.FAILED: -1
        }
        
        self.progress.progress_percentage = stage_progress.get(stage, 0)
        
        if progress_callback:
            stage_messages = {
                GenerationStage.ANALYZING: "Analyzing schema and planning generation...",
                GenerationStage.MAPPING_DEPENDENCIES: "Resolving table dependencies...",
                GenerationStage.GENERATING_DATA: "Generating table data sequentially...",
                GenerationStage.VALIDATING: "Validating generation results...",
                GenerationStage.RETRYING: "Retrying failed tables...",
                GenerationStage.COMPLETED: "Batch generation completed successfully!",
                GenerationStage.FAILED: "Batch generation failed"
            }
            
            message = stage_messages.get(stage, f"Stage: {stage}")
            await progress_callback(message, self.progress.progress_percentage)
    
    # Helper methods
    async def _analyze_table_domain(self, table: Dict[str, Any], business_context: str) -> str:
        """Analyze table to determine domain-specific context"""
        table_name = table["name"].lower()
        columns = [col["name"].lower() for col in table.get("columns", [])]
        
        # Domain pattern matching
        if any(word in table_name for word in ["patient", "doctor", "medical", "treatment", "diagnosis"]):
            return f"Healthcare data for {business_context} - medical records, patient care, clinical operations"
        elif any(word in table_name for word in ["product", "inventory", "order", "customer", "purchase"]):
            return f"E-commerce/Retail data for {business_context} - products, customers, transactions, inventory"
        elif any(word in table_name for word in ["account", "transaction", "payment", "finance", "balance"]):
            return f"Financial data for {business_context} - accounts, transactions, financial records"
        elif any(word in table_name for word in ["student", "course", "teacher", "class", "grade"]):
            return f"Educational data for {business_context} - students, courses, academic records"
        else:
            return f"Business data for {business_context} - operational records and business processes"