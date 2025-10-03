"""
Enhanced Company Management API with robust database generation and file u        # Save metadata
        with open(company_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Register company with CompanyManager so it appears in the companies list
        try:
            company_manager = get_company_manager()
            
            # Create profile dictionary directly
            profile_data = {
                "id": company_id,
                "name": company_name,
                "business_type": business_type,
                "complexity": complexity,
                "company_description": company_description,
                "database_file": str(db_path),
                "vector_store_path": str(company_dir / "vector_store"),
                "created_at": metadata["created_at"],
                "updated_at": metadata["created_at"],
                "is_active": False,
                "metadata": {
                    "generation_type": "enhanced_ai",
                    "data_stats": stats
                }
            }
            
            # Add profile to company manager
            profiles = company_manager._load_profiles()
            profiles[company_id] = profile_data
            company_manager._save_profiles(profiles)
            
            logger.info(f"Registered AI-generated company '{company_name}' with CompanyManager")
            
        except Exception as e:
            logger.error(f"Failed to register AI company with CompanyManager: {str(e)}")
            # Don't fail the whole process if registration fails

        logger.info(f"Enhanced company created successfully: {company_name}") support
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from typing import List, Dict, Any, Optional
import json
import os
import sqlite3
import pandas as pd
import tempfile
import shutil
from pathlib import Path
import asyncio
import uuid

from config.settings import get_settings
from utils.logging import get_logger
from scripts.enhanced_data_generator import EnhancedBusinessDataGenerator
from app.services.company_manager import get_company_manager

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()

@router.post("/companies/create-enhanced")
async def create_company_with_enhanced_database(
    company_name: str = Form(...),
    company_description: str = Form(...),
    business_type: str = Form(...),
    complexity: str = Form(default="medium"),
    requirements: Optional[str] = Form(default=""),
    additional_context: Optional[str] = Form(default="")
):
    """
    Create a company with enhanced, realistic database generation
    """
    try:
        logger.info(f"Creating enhanced company: {company_name} ({business_type})")
        
        # Create company directory (use same path as CompanyManager)
        company_id = str(uuid.uuid4())[:8]
        company_dir = Path(f"companies/{company_id}")
        company_dir.mkdir(parents=True, exist_ok=True)
        
        # Database path - place in project root directory instead of company subdirectory
        # Generate a clean filename from company name
        clean_company_name = company_name.lower().replace(' ', '_').replace("'", "").replace('"', '')
        # Remove any characters that aren't alphanumeric or underscore
        import re
        clean_company_name = re.sub(r'[^\w]', '_', clean_company_name)
        db_path = Path(f"{clean_company_name}_database.db")
        
        # Initialize enhanced data generator
        generator = EnhancedBusinessDataGenerator(
            business_type=business_type,
            company_name=company_name,
            company_description=company_description
        )
        
        # Create database schema based on business type
        await create_enhanced_schema(str(db_path), business_type, complexity)
        
        # Generate comprehensive realistic data
        stats = await generate_enhanced_business_data(
            generator=generator,
            db_path=str(db_path),
            complexity=complexity,
            requirements=requirements.split(',') if requirements else [],
            additional_context=additional_context
        )
        
        # Create company metadata
        metadata = {
            "id": company_id,
            "name": company_name,
            "description": company_description,
            "business_type": business_type,
            "complexity": complexity,
            "database_path": str(db_path),
            "created_at": pd.Timestamp.now().isoformat(),
            "data_stats": stats,
            "generation_type": "enhanced_ai"
        }
        
        # Save metadata
        with open(company_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Register company with CompanyManager so it appears in the companies list
        try:
            company_manager = get_company_manager()
            
            # Create profile dictionary directly
            profile_data = {
                "id": company_id,
                "name": company_name,
                "business_type": business_type,
                "complexity": complexity,
                "company_description": company_description,
                "database_file": str(db_path),
                "vector_store_path": str(company_dir / "vector_store"),
                "created_at": metadata["created_at"],
                "updated_at": metadata["created_at"],
                "is_active": False,
                "metadata": {
                    "generation_type": "enhanced_ai",
                    "data_stats": stats
                }
            }
            
            # Add profile to company manager
            profiles = company_manager._load_profiles()
            profiles[company_id] = profile_data
            company_manager._save_profiles(profiles)
            
            logger.info(f"Registered company with CompanyManager: {company_name}")
        except Exception as e:
            logger.warning(f"Failed to register company with CompanyManager: {str(e)}")
        
        logger.info(f"Enhanced company created successfully: {company_name}")
        return {
            "success": True,
            "message": f"Company '{company_name}' created with enhanced database",
            "company_id": company_id,
            "company_name": company_name,
            "data_stats": stats,
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"Error creating enhanced company: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create company: {str(e)}")

@router.post("/companies/create-from-upload")
async def create_company_from_upload(
    background_tasks: BackgroundTasks,
    company_name: str = Form(...),
    company_description: str = Form(...),
    business_type: str = Form(default="custom"),
    auto_detect_relations: bool = Form(default=True),
    normalize_data: bool = Form(default=True),
    create_indexes: bool = Form(default=True),
    validate_data: bool = Form(default=False),
    files: List[UploadFile] = File(...)
):
    """
    Create a company from uploaded files (CSV, Excel, SQLite, JSON, etc.)
    """
    try:
        logger.info(f"Creating company from upload: {company_name}")
        
        if not files:
            raise HTTPException(status_code=400, detail="No files uploaded")
        
        # Generate unique company ID
        company_id = str(uuid.uuid4())[:8]
        
        # Create company directory using the same structure as CompanyManager
        company_dir = Path(f"companies/{company_id}")
        company_dir.mkdir(parents=True, exist_ok=True)
        
        # Create uploads subdirectory
        uploads_dir = company_dir / "uploads"
        uploads_dir.mkdir(exist_ok=True)
        
        # Save uploaded files
        uploaded_file_paths = []
        for file in files:
            if file.size > 100 * 1024 * 1024:  # 100MB limit
                raise HTTPException(status_code=400, detail=f"File {file.filename} too large (max 100MB)")
            
            file_path = uploads_dir / file.filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            uploaded_file_paths.append(file_path)
        
        # Process files and create database - place in project root directory
        # Generate a clean filename from company name
        clean_company_name = company_name.lower().replace(' ', '_').replace("'", "").replace('"', '')
        # Remove any characters that aren't alphanumeric or underscore
        import re
        clean_company_name = re.sub(r'[^\w]', '_', clean_company_name)
        db_path = Path(f"{clean_company_name}_database.db")
        
        # Process uploaded files in background
        background_tasks.add_task(
            process_uploaded_files,
            uploaded_file_paths,
            str(db_path),
            {
                "auto_detect_relations": auto_detect_relations,
                "normalize_data": normalize_data,
                "create_indexes": create_indexes,
                "validate_data": validate_data
            }
        )
        
        # Create basic metadata (will be updated after processing)
        metadata = {
            "id": company_id,
            "name": company_name,
            "description": company_description,
            "business_type": business_type,
            "database_path": str(db_path),
            "created_at": pd.Timestamp.now().isoformat(),
            "generation_type": "file_upload",
            "uploaded_files": [f.filename for f in files],
            "processing_status": "in_progress"
        }
        
        # Save metadata
        with open(company_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Register company with CompanyManager so it appears in the companies list
        try:
            company_manager = get_company_manager()
            
            # Create profile dictionary directly
            profile_data = {
                "id": company_id,
                "name": company_name,
                "business_type": business_type,
                "complexity": "medium",  # Default for file uploads
                "company_description": company_description,
                "database_file": str(db_path),
                "vector_store_path": str(company_dir / "vector_store"),
                "created_at": metadata["created_at"],
                "updated_at": metadata["created_at"],
                "is_active": False,
                "metadata": {
                    "generation_type": "file_upload",
                    "uploaded_files": [f.filename for f in files],
                    "processing_status": "in_progress"
                }
            }
            
            # Add profile to company manager
            profiles = company_manager._load_profiles()
            profiles[company_id] = profile_data
            company_manager._save_profiles(profiles)
            
            logger.info(f"Registered upload company with CompanyManager: {company_name}")
        except Exception as e:
            logger.warning(f"Failed to register upload company with CompanyManager: {str(e)}")
        
        return {
            "success": True,
            "message": f"Company '{company_name}' created. Files are being processed...",
            "company_id": company_id,
            "company_name": company_name,
            "processing_status": "in_progress",
            "uploaded_files": len(files)
        }
        
    except Exception as e:
        logger.error(f"Error creating company from upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create company: {str(e)}")

async def create_enhanced_schema(db_path: str, business_type: str, complexity: str):
    """Create enhanced database schema based on business type and complexity"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Base schema that all business types need
    base_schema = """
        -- Companies table
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            business_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Users/Employees table
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE,
            department TEXT,
            position TEXT,
            hire_date DATE,
            salary DECIMAL(10,2),
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """
    
    # Business-specific schemas
    business_schemas = {
        'retail': """
            -- Products table
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sku TEXT UNIQUE,
                category TEXT NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                cost DECIMAL(10,2),
                description TEXT,
                stock_quantity INTEGER DEFAULT 0,
                reorder_level INTEGER DEFAULT 10,
                weight DECIMAL(8,2),
                dimensions TEXT,
                manufacturer TEXT,
                warranty_months INTEGER,
                launch_date DATE,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Customers table
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                date_of_birth DATE,
                registration_date DATE NOT NULL,
                segment TEXT NOT NULL,
                lifetime_value DECIMAL(10,2) DEFAULT 0.00,
                address TEXT,
                city TEXT,
                postal_code TEXT,
                country TEXT DEFAULT 'United States',
                preferred_contact TEXT,
                marketing_opt_in BOOLEAN DEFAULT 0,
                last_login DATE,
                account_status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Orders table
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                order_date DATE NOT NULL,
                total_amount DECIMAL(10,2) NOT NULL,
                tax_amount DECIMAL(10,2),
                shipping_amount DECIMAL(10,2),
                discount_amount DECIMAL(10,2) DEFAULT 0,
                status TEXT DEFAULT 'pending',
                payment_method TEXT,
                shipping_address TEXT,
                tracking_number TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            );
            
            -- Order items table
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                total_price DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            );
            
            -- Reviews table
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                customer_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                title TEXT,
                review_text TEXT,
                review_date DATE NOT NULL,
                sentiment TEXT,
                helpful_votes INTEGER DEFAULT 0,
                verified_purchase BOOLEAN DEFAULT 0,
                response_text TEXT,
                response_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id),
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            );
            
            -- Inventory transactions
            CREATE TABLE IF NOT EXISTS inventory_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL, -- 'purchase', 'sale', 'adjustment', 'return'
                quantity INTEGER NOT NULL,
                cost_per_unit DECIMAL(10,2),
                total_cost DECIMAL(10,2),
                supplier TEXT,
                transaction_date DATE NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id)
            );
        """,
        
        'healthcare': """
            -- Patients table
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                date_of_birth DATE NOT NULL,
                gender TEXT,
                phone TEXT,
                email TEXT,
                address TEXT,
                city TEXT,
                postal_code TEXT,
                emergency_contact_name TEXT,
                emergency_contact_phone TEXT,
                insurance_provider TEXT,
                insurance_id TEXT,
                medical_record_number TEXT UNIQUE,
                registration_date DATE NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Medical services table
            CREATE TABLE IF NOT EXISTS medical_services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                duration_minutes INTEGER,
                base_cost DECIMAL(10,2),
                insurance_billable BOOLEAN DEFAULT 1,
                department TEXT,
                requires_referral BOOLEAN DEFAULT 0,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Appointments table
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                service_id INTEGER NOT NULL,
                doctor_id INTEGER,
                appointment_date DATETIME NOT NULL,
                duration_minutes INTEGER,
                status TEXT DEFAULT 'scheduled',
                notes TEXT,
                cost DECIMAL(10,2),
                insurance_claim_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id),
                FOREIGN KEY (service_id) REFERENCES medical_services (id),
                FOREIGN KEY (doctor_id) REFERENCES employees (id)
            );
            
            -- Medical records table
            CREATE TABLE IF NOT EXISTS medical_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                appointment_id INTEGER,
                record_type TEXT NOT NULL, -- 'diagnosis', 'prescription', 'lab_result', 'note'
                diagnosis_code TEXT,
                description TEXT,
                treatment_plan TEXT,
                medications TEXT,
                record_date DATE NOT NULL,
                doctor_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients (id),
                FOREIGN KEY (appointment_id) REFERENCES appointments (id),
                FOREIGN KEY (doctor_id) REFERENCES employees (id)
            );
        """,
        
        'finance': """
            -- Clients/Customers table
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                date_of_birth DATE,
                registration_date DATE NOT NULL,
                client_type TEXT NOT NULL, -- 'individual', 'business', 'institutional'
                risk_profile TEXT DEFAULT 'moderate', -- 'conservative', 'moderate', 'aggressive'
                investment_goal TEXT,
                annual_income DECIMAL(12,2),
                net_worth DECIMAL(15,2),
                address TEXT,
                city TEXT,
                postal_code TEXT,
                country TEXT DEFAULT 'United States',
                kyc_status TEXT DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
                account_status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Financial products table
            CREATE TABLE IF NOT EXISTS financial_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                product_type TEXT NOT NULL, -- 'investment', 'loan', 'insurance', 'savings', 'checking'
                category TEXT NOT NULL,
                description TEXT,
                minimum_amount DECIMAL(12,2),
                interest_rate DECIMAL(5,4),
                term_months INTEGER,
                risk_level TEXT, -- 'low', 'medium', 'high'
                fees DECIMAL(10,2),
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Accounts table
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                account_number TEXT UNIQUE NOT NULL,
                account_type TEXT NOT NULL,
                balance DECIMAL(15,2) DEFAULT 0.00,
                interest_rate DECIMAL(5,4),
                opening_date DATE NOT NULL,
                maturity_date DATE,
                status TEXT DEFAULT 'active',
                branch_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id),
                FOREIGN KEY (product_id) REFERENCES financial_products (id)
            );
            
            -- Transactions table
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL, -- 'deposit', 'withdrawal', 'transfer', 'payment', 'fee'
                amount DECIMAL(12,2) NOT NULL,
                balance_after DECIMAL(15,2),
                description TEXT,
                transaction_date DATETIME NOT NULL,
                reference_number TEXT UNIQUE,
                counterparty_account TEXT,
                fee_amount DECIMAL(10,2) DEFAULT 0.00,
                status TEXT DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts (id)
            );
            
            -- Loans table
            CREATE TABLE IF NOT EXISTS loans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                loan_type TEXT NOT NULL, -- 'personal', 'mortgage', 'business', 'auto'
                principal_amount DECIMAL(12,2) NOT NULL,
                interest_rate DECIMAL(5,4) NOT NULL,
                term_months INTEGER NOT NULL,
                monthly_payment DECIMAL(10,2),
                outstanding_balance DECIMAL(12,2),
                origination_date DATE NOT NULL,
                maturity_date DATE NOT NULL,
                status TEXT DEFAULT 'active', -- 'active', 'paid_off', 'defaulted'
                collateral_description TEXT,
                purpose TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            );
            
            -- Investment portfolio table
            CREATE TABLE IF NOT EXISTS portfolio_holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                security_type TEXT NOT NULL, -- 'stock', 'bond', 'mutual_fund', 'etf', 'options'
                quantity DECIMAL(12,4),
                purchase_price DECIMAL(10,4),
                current_price DECIMAL(10,4),
                purchase_date DATE NOT NULL,
                market_value DECIMAL(12,2),
                unrealized_gain_loss DECIMAL(12,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            );
        """
    }
    
    # Execute base schema
    cursor.executescript(base_schema)
    
    # Execute business-specific schema
    if business_type in business_schemas:
        cursor.executescript(business_schemas[business_type])
    
    # Add complexity-specific enhancements
    if complexity in ['medium', 'complex']:
        complexity_enhancements = """
            -- Audit trail table
            CREATE TABLE IF NOT EXISTS audit_trail (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                record_id INTEGER NOT NULL,
                action TEXT NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE'
                old_values TEXT, -- JSON
                new_values TEXT, -- JSON
                user_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Settings table
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, key)
            );
        """
        cursor.executescript(complexity_enhancements)
    
    if complexity == 'complex':
        complex_enhancements = """
            -- Analytics tables
            CREATE TABLE IF NOT EXISTS analytics_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                entity_type TEXT,
                entity_id INTEGER,
                properties TEXT, -- JSON
                user_id INTEGER,
                session_id TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- File attachments
            CREATE TABLE IF NOT EXISTS attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                mime_type TEXT,
                uploaded_by INTEGER,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        cursor.executescript(complex_enhancements)
    
    # Create indexes for better performance
    create_indexes_sql = """
        -- Performance indexes
        CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
        CREATE INDEX IF NOT EXISTS idx_customers_segment ON customers(segment);
        CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
        CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);
        CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
        CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
        CREATE INDEX IF NOT EXISTS idx_reviews_product_id ON reviews(product_id);
        CREATE INDEX IF NOT EXISTS idx_reviews_rating ON reviews(rating);
    """
    
    cursor.executescript(create_indexes_sql)
    conn.commit()
    conn.close()

async def generate_enhanced_business_data(
    generator: EnhancedBusinessDataGenerator,
    db_path: str,
    complexity: str,
    requirements: List[str],
    additional_context: str
) -> Dict[str, int]:
    """Generate comprehensive business data using the enhanced generator"""
    
    config = generator.get_business_config()
    
    # Adjust data volume based on complexity
    volume_multiplier = {
        'simple': 1.0,
        'medium': 2.0,
        'complex': 3.0
    }.get(complexity, 2.0)
    
    # Scale up data generation
    enhanced_config = config.copy()
    for key in ['customer_count', 'product_count', 'review_count', 'order_count']:
        if key in enhanced_config:
            enhanced_config[key] = int(enhanced_config[key] * volume_multiplier)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        stats = {}
        
        # Generate products
        if generator.business_type in ['retail', 'ecommerce']:
            products = generator.generate_comprehensive_products()
            for product in products:
                cursor.execute("""
                    INSERT INTO products (name, sku, category, price, description, stock_quantity, 
                                        weight, dimensions, manufacturer, warranty_months, launch_date, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    product['name'], product.get('sku'), product['category'], product['price'],
                    product['description'], product.get('stock_quantity', 0), product.get('weight'),
                    product.get('dimensions'), product.get('manufacturer'), product.get('warranty_months'),
                    product['launch_date'], product['status']
                ))
            stats['products'] = len(products)
        
        # Generate customers
        customers = generator.generate_realistic_customers(enhanced_config.get('customer_count', 500))
        for customer in customers:
            cursor.execute("""
                INSERT INTO customers (first_name, last_name, email, phone, date_of_birth, 
                                     registration_date, segment, lifetime_value, address, city, 
                                     postal_code, country, preferred_contact, marketing_opt_in, 
                                     last_login, account_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                customer['first_name'], customer['last_name'], customer['email'], customer.get('phone'),
                customer.get('date_of_birth'), customer['registration_date'], customer['segment'],
                customer['lifetime_value'], customer.get('address'), customer.get('city'),
                customer.get('postal_code'), customer.get('country'), customer.get('preferred_contact'),
                customer.get('marketing_opt_in'), customer.get('last_login'), customer['account_status']
            ))
        stats['customers'] = len(customers)
        
        # Generate comprehensive reviews (much more detailed)
        if generator.business_type in ['retail', 'ecommerce']:
            product_ids = [row[0] for row in cursor.execute("SELECT id FROM products").fetchall()]
            customer_ids = [row[0] for row in cursor.execute("SELECT id FROM customers").fetchall()]
            
            all_reviews = []
            for product_id in product_ids[:min(50, len(product_ids))]:
                product_name = cursor.execute("SELECT name, category FROM products WHERE id = ?", (product_id,)).fetchone()
                if product_name:
                    reviews = generator.generate_realistic_reviews(product_id, product_name[0], product_name[1])
                    all_reviews.extend(reviews)
            
            # Insert reviews
            for review in all_reviews:
                customer_id = random.choice(customer_ids) if customer_ids else None
                if customer_id:
                    cursor.execute("""
                        INSERT INTO reviews (product_id, customer_id, rating, review_text, review_date, 
                                           sentiment, helpful_votes, verified_purchase)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        review['product_id'], customer_id, review['rating'], review['review_text'],
                        review['review_date'], review['sentiment'], review['helpful_votes'],
                        review.get('verified_purchase', True)
                    ))
            
            stats['reviews'] = len(all_reviews)
        
        conn.commit()
        
        # Add complexity-specific data
        if complexity in ['medium', 'complex']:
            # Generate employee data
            employees = generate_employee_data(generator.business_type, int(20 * volume_multiplier))
            for employee in employees:
                cursor.execute("""
                    INSERT INTO employees (first_name, last_name, email, department, position, 
                                         hire_date, salary, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, employee)
            stats['employees'] = len(employees)
        
        conn.commit()
        return stats
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def generate_employee_data(business_type: str, count: int) -> List[tuple]:
    """Generate realistic employee data based on business type"""
    
    departments = {
        'retail': ['Sales', 'Customer Service', 'Inventory', 'Marketing', 'Finance', 'HR', 'Operations'],
        'healthcare': ['Medical', 'Nursing', 'Administration', 'Laboratory', 'Pharmacy', 'Radiology', 'IT'],
        'finance': ['Investment Banking', 'Retail Banking', 'Risk Management', 'Compliance', 'IT', 'HR'],
        'education': ['Academic', 'Administration', 'Student Services', 'Facilities', 'Technology', 'Library'],
        'manufacturing': ['Production', 'Quality Control', 'Engineering', 'Maintenance', 'Safety', 'Logistics']
    }.get(business_type, ['Sales', 'Marketing', 'Finance', 'HR', 'Operations', 'IT'])
    
    positions = {
        'Sales': ['Sales Associate', 'Sales Manager', 'Regional Sales Director'],
        'Customer Service': ['Customer Service Rep', 'Customer Service Manager', 'Support Specialist'],
        'Marketing': ['Marketing Coordinator', 'Marketing Manager', 'Digital Marketing Specialist'],
        'Finance': ['Accountant', 'Financial Analyst', 'Finance Manager'],
        'HR': ['HR Specialist', 'HR Manager', 'Recruiter'],
        'IT': ['Software Developer', 'System Admin', 'IT Manager'],
        'Operations': ['Operations Coordinator', 'Operations Manager', 'Process Analyst']
    }
    
    employees = []
    for _ in range(count):
        department = random.choice(departments)
        position_list = positions.get(department, [f'{department} Specialist', f'{department} Manager'])
        position = random.choice(position_list)
        
        # Salary based on position level
        if 'Manager' in position or 'Director' in position:
            salary = random.randint(75000, 150000)
        elif 'Specialist' in position or 'Analyst' in position:
            salary = random.randint(45000, 85000)
        else:
            salary = random.randint(30000, 65000)
        
        employee = (
            fake.first_name(),
            fake.last_name(),
            fake.email(),
            department,
            position,
            fake.date_between(start_date='-5y', end_date='-1m'),
            salary,
            random.choices(['active', 'inactive'], weights=[0.95, 0.05])[0]
        )
        employees.append(employee)
    
    return employees

async def process_uploaded_files(
    file_paths: List[Path],
    db_path: str,
    options: Dict[str, bool]
):
    """Process uploaded files and create database tables"""
    
    conn = sqlite3.connect(db_path)
    
    try:
        processed_tables = []
        
        for file_path in file_paths:
            logger.info(f"Processing file: {file_path}")
            
            # Determine file type and process accordingly
            if file_path.suffix.lower() in ['.xlsx', '.xls']:
                # Process Excel files
                tables = process_excel_file(file_path, conn, options)
                processed_tables.extend(tables)
                
            elif file_path.suffix.lower() == '.csv':
                # Process CSV files
                table_name = process_csv_file(file_path, conn, options)
                processed_tables.append(table_name)
                
            elif file_path.suffix.lower() in ['.sqlite', '.db']:
                # Process SQLite files
                tables = process_sqlite_file(file_path, conn, options)
                processed_tables.extend(tables)
                
            elif file_path.suffix.lower() == '.json':
                # Process JSON files
                tables = process_json_file(file_path, conn, options)
                processed_tables.extend(tables)
        
        # Create indexes if requested
        if options.get('create_indexes', True):
            create_automatic_indexes(conn, processed_tables)
        
        # Update metadata with processing results
        metadata_path = Path(db_path).parent / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            metadata.update({
                "processing_status": "completed",
                "processed_tables": processed_tables,
                "processing_completed_at": pd.Timestamp.now().isoformat()
            })
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Register company with CompanyManager so it appears in the companies list
            try:
                company_manager = get_company_manager()
                company_dir = Path(db_path).parent
                company_id = company_dir.name
                
                # Create profile dictionary directly (avoiding import issues)
                profile_data = {
                    "id": company_id,
                    "name": metadata["name"],
                    "business_type": metadata.get("business_type", "general"),
                    "complexity": "medium",  # Default for uploaded companies
                    "company_description": metadata.get("description", ""),
                    "database_file": str(db_path),
                    "vector_store_path": str(company_dir / "vector_store"),
                    "created_at": metadata["created_at"],
                    "updated_at": pd.Timestamp.now().isoformat(),
                    "is_active": False,
                    "metadata": {
                        "generation_type": metadata["generation_type"],
                        "uploaded_files": metadata.get("uploaded_files", []),
                        "processed_tables": processed_tables
                    }
                }
                
                # Add profile to company manager using internal method
                profiles = company_manager._load_profiles()
                profiles[company_id] = profile_data
                company_manager._save_profiles(profiles)
                
                logger.info(f"Registered company '{metadata['name']}' with CompanyManager")
                
            except Exception as e:
                logger.error(f"Failed to register company with CompanyManager: {str(e)}")
                # Don't fail the whole process if registration fails
        
        conn.commit()
        logger.info(f"Successfully processed {len(file_paths)} files into {len(processed_tables)} tables")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error processing uploaded files: {str(e)}")
        raise e
    finally:
        conn.close()

def process_excel_file(file_path: Path, conn: sqlite3.Connection, options: Dict) -> List[str]:
    """Process Excel file and create database tables"""
    tables = []
    
    try:
        # Read all sheets
        excel_file = pd.ExcelFile(file_path)
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            if df.empty:
                continue
            
            # Clean table name
            table_name = clean_table_name(f"{file_path.stem}_{sheet_name}")
            
            # Normalize data if requested
            if options.get('normalize_data', True):
                df = normalize_dataframe(df)
            
            # Create table and insert data
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            tables.append(table_name)
            
    except Exception as e:
        logger.error(f"Error processing Excel file {file_path}: {str(e)}")
        raise e
    
    return tables

def process_csv_file(file_path: Path, conn: sqlite3.Connection, options: Dict) -> str:
    """Process CSV file and create database table"""
    
    try:
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if df is None:
            raise ValueError(f"Could not read CSV file with any supported encoding")
        
        if df.empty:
            raise ValueError("CSV file is empty")
        
        # Clean table name
        table_name = clean_table_name(file_path.stem)
        
        # Normalize data if requested
        if options.get('normalize_data', True):
            df = normalize_dataframe(df)
        
        # Create table and insert data
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        
        return table_name
        
    except Exception as e:
        logger.error(f"Error processing CSV file {file_path}: {str(e)}")
        raise e

def clean_table_name(name: str) -> str:
    """Clean table name to be SQL-safe"""
    import re
    # Replace special characters with underscores
    name = re.sub(r'[^\w]', '_', name)
    # Remove consecutive underscores
    name = re.sub(r'_+', '_', name)
    # Remove leading/trailing underscores
    name = name.strip('_')
    # Ensure it doesn't start with a number
    if name and name[0].isdigit():
        name = f"table_{name}"
    return name.lower()

def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize dataframe data types and formats"""
    
    df_copy = df.copy()
    
    for column in df_copy.columns:
        # Try to convert date columns
        if df_copy[column].dtype == 'object':
            # Check if it looks like dates
            sample_values = df_copy[column].dropna().astype(str).head(10)
            if any('/' in str(val) or '-' in str(val) for val in sample_values):
                try:
                    df_copy[column] = pd.to_datetime(df_copy[column], errors='ignore')
                except:
                    pass
        
        # Try to convert numeric columns
        if df_copy[column].dtype == 'object':
            try:
                # Try to convert to numeric
                df_copy[column] = pd.to_numeric(df_copy[column], errors='ignore')
            except:
                pass
    
    return df_copy

def process_sqlite_file(file_path: Path, conn: sqlite3.Connection, options: Dict) -> List[str]:
    """Process SQLite files by copying tables to target database"""
    processed_tables = []
    
    try:
        # Connect to source SQLite file
        source_conn = sqlite3.connect(str(file_path))
        source_cursor = source_conn.cursor()
        
        # Get list of tables from source database
        source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = source_cursor.fetchall()
        
        for (table_name,) in tables:
            try:
                # Read table data
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", source_conn)
                
                if len(df) > 0:
                    # Clean and normalize data if requested
                    if options.get('normalize_data', True):
                        df = normalize_dataframe(df)
                    
                    # Create sanitized table name
                    clean_table_name = table_name.lower().replace(' ', '_').replace('-', '_')
                    clean_table_name = ''.join(c for c in clean_table_name if c.isalnum() or c == '_')
                    
                    # Write to target database
                    df.to_sql(clean_table_name, conn, if_exists='replace', index=False)
                    processed_tables.append(clean_table_name)
                    logger.info(f"Imported table '{table_name}' as '{clean_table_name}' with {len(df)} rows")
                    
            except Exception as e:
                logger.warning(f"Failed to process table '{table_name}': {str(e)}")
        
        source_conn.close()
        
    except Exception as e:
        logger.error(f"Error processing SQLite file {file_path}: {str(e)}")
        raise
    
    return processed_tables

def process_json_file(file_path: Path, conn: sqlite3.Connection, options: Dict) -> List[str]:
    """Process JSON files and convert to database tables"""
    processed_tables = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, list):
            # Array of objects - create single table
            if len(data) > 0 and isinstance(data[0], dict):
                df = pd.DataFrame(data)
                table_name = file_path.stem.lower().replace(' ', '_').replace('-', '_')
                
                if options.get('normalize_data', True):
                    df = normalize_dataframe(df)
                
                df.to_sql(table_name, conn, if_exists='replace', index=False)
                processed_tables.append(table_name)
                logger.info(f"Created table '{table_name}' from JSON array with {len(df)} rows")
                
        elif isinstance(data, dict):
            # Object with multiple arrays - create table for each array
            for key, value in data.items():
                if isinstance(value, list) and len(value) > 0:
                    if isinstance(value[0], dict):
                        df = pd.DataFrame(value)
                        table_name = key.lower().replace(' ', '_').replace('-', '_')
                        table_name = ''.join(c for c in table_name if c.isalnum() or c == '_')
                        
                        if options.get('normalize_data', True):
                            df = normalize_dataframe(df)
                        
                        df.to_sql(table_name, conn, if_exists='replace', index=False)
                        processed_tables.append(table_name)
                        logger.info(f"Created table '{table_name}' from JSON key '{key}' with {len(df)} rows")
        
    except Exception as e:
        logger.error(f"Error processing JSON file {file_path}: {str(e)}")
        raise
    
    return processed_tables

def create_automatic_indexes(conn: sqlite3.Connection, table_names: List[str]):
    """Create automatic indexes on common columns"""
    
    try:
        cursor = conn.cursor()
        
        for table_name in table_names:
            try:
                # Get table info
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                for column_info in columns:
                    column_name = column_info[1]
                    column_type = column_info[2].upper()
                    
                    # Create indexes on common patterns
                    should_index = False
                    
                    # Index ID columns
                    if column_name.lower().endswith('_id') or column_name.lower() == 'id':
                        should_index = True
                    
                    # Index date columns
                    elif 'date' in column_name.lower() or 'time' in column_name.lower():
                        should_index = True
                    
                    # Index name columns
                    elif 'name' in column_name.lower():
                        should_index = True
                    
                    # Index email columns
                    elif 'email' in column_name.lower():
                        should_index = True
                    
                    if should_index:
                        try:
                            index_name = f"idx_{table_name}_{column_name}"
                            cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({column_name})")
                            logger.info(f"Created index {index_name}")
                        except Exception as e:
                            logger.warning(f"Failed to create index on {table_name}.{column_name}: {str(e)}")
                            
            except Exception as e:
                logger.warning(f"Failed to analyze table {table_name} for indexing: {str(e)}")
        
        conn.commit()
        
    except Exception as e:
        logger.error(f"Error creating automatic indexes: {str(e)}")

# Additional helper functions would continue here...

import random
from faker import Faker
fake = Faker()