"""
Company management system for multi-tenant business intelligence
Allows storing and switching between different company databases and contexts
"""

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import uuid
import shutil
import sqlite3
from sqlalchemy import text

from database.connection import get_database
from database.llm_generator import BusinessType, ComplexityLevel
from utils.logging import get_logger


@dataclass
class CompanyProfile:
    """Company profile information"""
    id: str
    name: str
    business_type: str
    complexity: str
    company_description: str
    database_file: str
    vector_store_path: str
    created_at: str
    updated_at: str
    is_active: bool = False
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CompanyManager:
    """
    Manages multiple company contexts and databases
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.companies_dir = Path("companies")
        self.companies_dir.mkdir(exist_ok=True)
        self.profiles_file = self.companies_dir / "company_profiles.json"
        self.current_company_file = self.companies_dir / "current_company.txt"
        
        # Initialize profiles storage
        if not self.profiles_file.exists():
            self._save_profiles({})
    
    def create_company(
        self,
        name: str,
        business_type: BusinessType,
        complexity: ComplexityLevel,
        company_description: str,
        additional_metadata: Dict[str, Any] = None
    ) -> CompanyProfile:
        """Create a new company profile"""
        
        try:
            # Generate unique ID
            company_id = str(uuid.uuid4())[:8]
            
            # Create company directory
            company_dir = self.companies_dir / company_id
            company_dir.mkdir(exist_ok=True)
            
            # Set up database and vector store paths
            database_file = str(company_dir / f"{company_id}_database.db")
            vector_store_path = str(company_dir / "vector_store")
            
            # Create company profile
            profile = CompanyProfile(
                id=company_id,
                name=name,
                business_type=business_type.value,
                complexity=complexity.value,
                company_description=company_description,
                database_file=database_file,
                vector_store_path=vector_store_path,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                metadata=additional_metadata or {}
            )
            
            # Save profile
            self._add_profile(profile)
            
            self.logger.info(f"Created company profile: {name} ({company_id})")
            return profile
            
        except Exception as e:
            self.logger.error(f"Error creating company: {str(e)}")
            raise
    
    def get_company(self, company_id: str) -> Optional[CompanyProfile]:
        """Get company profile by ID"""
        profiles = self._load_profiles()
        profile_data = profiles.get(company_id)
        
        if profile_data:
            # Handle field migration from industry_description to company_description
            if 'industry_description' in profile_data and 'company_description' not in profile_data:
                profile_data['company_description'] = profile_data.pop('industry_description')
            # Handle field migration from description to company_description
            if 'description' in profile_data and 'company_description' not in profile_data:
                profile_data['company_description'] = profile_data.pop('description')
            # Add default values for missing required fields
            if 'complexity' not in profile_data:
                profile_data['complexity'] = 'medium'
            if 'company_description' not in profile_data:
                profile_data['company_description'] = 'No description available'
            return CompanyProfile(**profile_data)
        return None
    
    def list_companies(self) -> List[CompanyProfile]:
        """List all company profiles"""
        profiles = self._load_profiles()
        company_list = []
        for data in profiles.values():
            # Handle field migration from industry_description to company_description
            if 'industry_description' in data and 'company_description' not in data:
                data['company_description'] = data.pop('industry_description')
            # Handle field migration from description to company_description
            if 'description' in data and 'company_description' not in data:
                data['company_description'] = data.pop('description')
            # Add default values for missing required fields
            if 'complexity' not in data:
                data['complexity'] = 'medium'
            if 'company_description' not in data:
                data['company_description'] = 'No description available'
            company_list.append(CompanyProfile(**data))
        return company_list
    
    def get_current_company(self) -> Optional[CompanyProfile]:
        """Get the currently active company"""
        try:
            if self.current_company_file.exists():
                with open(self.current_company_file, 'r') as f:
                    company_id = f.read().strip()
                    return self.get_company(company_id)
        except Exception as e:
            self.logger.error(f"Error getting current company: {str(e)}")
        return None
    
    def set_current_company(self, company_id: str) -> bool:
        """Set the active company"""
        try:
            company = self.get_company(company_id)
            if not company:
                return False
            
            # Update all companies to inactive
            profiles = self._load_profiles()
            for profile_data in profiles.values():
                profile_data['is_active'] = False
            
            # Set target company as active
            profiles[company_id]['is_active'] = True
            profiles[company_id]['updated_at'] = datetime.now().isoformat()
            
            self._save_profiles(profiles)
            
            # Save current company ID
            with open(self.current_company_file, 'w') as f:
                f.write(company_id)
            
            self.logger.info(f"Switched to company: {company.name} ({company_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting current company: {str(e)}")
            return False
    
    def update_company(
        self,
        company_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update company profile"""
        try:
            profiles = self._load_profiles()
            if company_id not in profiles:
                return False
            
            # Update fields
            profiles[company_id].update(updates)
            profiles[company_id]['updated_at'] = datetime.now().isoformat()
            
            self._save_profiles(profiles)
            
            self.logger.info(f"Updated company: {company_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating company: {str(e)}")
            return False
    
    def delete_company(self, company_id: str) -> bool:
        """Delete company and all associated data"""
        try:
            company = self.get_company(company_id)
            if not company:
                return False
            
            # Remove from profiles FIRST before attempting file deletion
            profiles = self._load_profiles()
            if company_id in profiles:
                del profiles[company_id]
                self._save_profiles(profiles)
            
            # Clear current company if it was the active one
            current = self.get_current_company()
            if current and current.id == company_id:
                if self.current_company_file.exists():
                    self.current_company_file.unlink()
            
            # Force close any open database connections to this company's database
            try:
                import gc
                import sqlite3
                
                # Get the database path
                db_path = company.database_file
                
                # Force garbage collection to close any lingering connections
                gc.collect()
                
                # Try to close any SQLite connections that might be open
                if os.path.exists(db_path):
                    try:
                        # Create a temporary connection to force unlock, then close immediately
                        temp_conn = sqlite3.connect(db_path, timeout=0.1)
                        temp_conn.close()
                        del temp_conn
                    except:
                        pass  # Ignore errors here
                        
                    # Force garbage collection again
                    gc.collect()
                    
                    # Wait a moment for file handles to be released
                    import time
                    time.sleep(0.2)
                
            except Exception as cleanup_error:
                self.logger.warning(f"Database cleanup warning: {str(cleanup_error)}")
            
            # Delete company directory and all files with enhanced retry logic
            company_dir = self.companies_dir / company_id
            if company_dir.exists():
                success = self._delete_company_directory_with_retries(company_dir)
                if not success:
                    # Even if file deletion failed, we removed it from profiles
                    # so it won't show up in the UI anymore
                    self.logger.warning(f"Company {company_id} removed from profiles but some files may remain")
            
            self.logger.info(f"Deleted company: {company.name} ({company_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting company: {str(e)}")
            return False
    
    def _delete_company_directory_with_retries(self, company_dir: Path) -> bool:
        """Delete company directory with enhanced retry logic"""
        max_retries = 5
        
        for attempt in range(max_retries):
            try:
                shutil.rmtree(company_dir)
                self.logger.info(f"Successfully deleted directory on attempt {attempt + 1}")
                return True
            except OSError as e:
                if "being used by another process" in str(e) and attempt < max_retries - 1:
                    self.logger.warning(f"File in use, retrying deletion (attempt {attempt + 1})")
                    import time
                    time.sleep(1.0)  # Wait longer between retries
                    
                    # Try additional cleanup between retries
                    try:
                        import gc
                        gc.collect()
                    except:
                        pass
                else:
                    # If all retries failed, try to delete what we can
                    self.logger.warning(f"Failed to delete directory after {max_retries} attempts: {str(e)}")
                    return self._partial_delete_directory(company_dir)
        
        return False
    
    def _partial_delete_directory(self, directory_path: Path) -> bool:
        """Delete what files we can, leave the rest"""
        try:
            deleted_something = False
            
            # Try to delete files that aren't locked
            for item in directory_path.rglob('*'):
                if item.is_file():
                    try:
                        item.unlink()
                        deleted_something = True
                        self.logger.info(f"Deleted file: {item}")
                    except OSError:
                        self.logger.warning(f"Could not delete locked file: {item}")
            
            # Try to remove empty directories
            for item in sorted(directory_path.rglob('*'), key=lambda p: len(str(p)), reverse=True):
                if item.is_dir():
                    try:
                        item.rmdir()
                        deleted_something = True
                    except OSError:
                        pass  # Directory not empty or locked
            
            # Try to remove the main directory
            try:
                directory_path.rmdir()
                deleted_something = True
                self.logger.info(f"Removed main directory: {directory_path}")
            except OSError:
                self.logger.warning(f"Main directory not empty or locked: {directory_path}")
            
            return deleted_something
                
        except Exception as e:
            self.logger.error(f"Error in partial delete: {str(e)}")
            return False
    
    def get_company_database_url(self, company_id: str) -> Optional[str]:
        """Get database URL for a specific company"""
        company = self.get_company(company_id)
        if company:
            return f"sqlite:///{company.database_file}"
        return None
    
    def get_company_vector_store_path(self, company_id: str) -> Optional[str]:
        """Get vector store path for a specific company"""
        company = self.get_company(company_id)
        if company:
            return company.vector_store_path
        return None
    
    def initialize_company_database(self, company_id: str) -> bool:
        """Initialize database file for a company"""
        try:
            company = self.get_company(company_id)
            if not company:
                return False
            
            # Create empty SQLite database
            db_path = Path(company.database_file)
            db_path.parent.mkdir(exist_ok=True)
            
            # Create empty database with basic structure
            conn = sqlite3.connect(company.database_file)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS _company_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            conn.execute(
                "INSERT OR REPLACE INTO _company_metadata (key, value) VALUES (?, ?)",
                ("company_id", company_id)
            )
            conn.execute(
                "INSERT OR REPLACE INTO _company_metadata (key, value) VALUES (?, ?)",
                ("company_name", company.name)
            )
            conn.execute(
                "INSERT OR REPLACE INTO _company_metadata (key, value) VALUES (?, ?)",
                ("initialized_at", datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing company database: {str(e)}")
            return False
    
    def get_company_stats(self, company_id: str) -> Dict[str, Any]:
        """Get statistics and metadata for a company"""
        try:
            company = self.get_company(company_id)
            if not company:
                return {}
            
            stats = {
                "profile": asdict(company),
                "database_exists": os.path.exists(company.database_file),
                "database_size_mb": 0,
                "table_count": 0,
                "record_count": 0,
                "vector_store_exists": os.path.exists(company.vector_store_path)
            }
            
            # Get database stats
            if stats["database_exists"]:
                try:
                    stats["database_size_mb"] = round(
                        os.path.getsize(company.database_file) / (1024 * 1024), 2
                    )
                    
                    # Count tables and records
                    conn = sqlite3.connect(company.database_file)
                    cursor = conn.cursor()
                    
                    # Count tables
                    cursor.execute(
                        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    )
                    stats["table_count"] = cursor.fetchone()[0]
                    
                    # Count total records across all tables
                    cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    )
                    tables = cursor.fetchall()
                    total_records = 0
                    
                    for table in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                        total_records += cursor.fetchone()[0]
                    
                    stats["record_count"] = total_records
                    conn.close()
                    
                except Exception as e:
                    self.logger.error(f"Error getting database stats: {str(e)}")
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting company stats: {str(e)}")
            return {}
    
    def _load_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Load company profiles from file"""
        try:
            if self.profiles_file.exists():
                with open(self.profiles_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading profiles: {str(e)}")
        return {}
    
    def _save_profiles(self, profiles: Dict[str, Dict[str, Any]]):
        """Save company profiles to file"""
        try:
            with open(self.profiles_file, 'w') as f:
                json.dump(profiles, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving profiles: {str(e)}")
    
    def _add_profile(self, profile: CompanyProfile):
        """Add a new profile to storage"""
        profiles = self._load_profiles()
        profiles[profile.id] = asdict(profile)
        self._save_profiles(profiles)


# Global company manager instance
_company_manager: Optional[CompanyManager] = None

def get_company_manager() -> CompanyManager:
    """Get global company manager instance"""
    global _company_manager
    if _company_manager is None:
        _company_manager = CompanyManager()
    return _company_manager


# Utility functions for easy access
async def get_current_company_database():
    """Get database connection for current company"""
    manager = get_company_manager()
    current_company = manager.get_current_company()
    
    if current_company:
        # Temporarily switch database URL
        from config.settings import get_settings
        settings = get_settings()
        original_url = settings.DATABASE_URL
        
        try:
            # Override database URL for current company
            settings.DATABASE_URL = f"sqlite:///{current_company.database_file}"
            db = get_database()
            await db.initialize()
            return db
        finally:
            # Restore original URL
            settings.DATABASE_URL = original_url
    
    return get_database()


def get_current_company_context() -> Dict[str, Any]:
    """Get context information for current company"""
    manager = get_company_manager()
    current_company = manager.get_current_company()
    
    if current_company:
        return {
            "company_id": current_company.id,
            "company_name": current_company.name,
            "business_type": current_company.business_type,
            "complexity": current_company.complexity,
            "company_description": current_company.company_description,
            "database_file": current_company.database_file,
            "vector_store_path": current_company.vector_store_path
        }
    
    return {
        "company_id": None,
        "company_name": "Default",
        "business_type": "general",
        "complexity": "medium",
        "company_description": "General business",
        "database_file": "./business_data.db",
        "vector_store_path": "./data/embeddings"
    }