-- Business Intelligence RAG Chatbot Database Schema
-- Generated on: 2025-10-03
-- Purpose: Comprehensive database schema supporting multiple business types
-- Compatible with: SQLite 3.x
-- 
-- This schema supports three main business types:
-- 1. Retail - Products, customers, orders, inventory
-- 2. Healthcare - Patients, medical services, appointments, records
-- 3. Finance - Clients, accounts, transactions, investments

-- =================================================================
-- BASE SCHEMA (Common to all business types)
-- =================================================================

-- Companies table - Core company information
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    business_type TEXT CHECK (business_type IN ('retail', 'healthcare', 'finance')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Employees/Users table - Staff and user management
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE,
    department TEXT,
    position TEXT,
    hire_date DATE,
    salary DECIMAL(10,2),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'terminated')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =================================================================
-- RETAIL BUSINESS SCHEMA
-- =================================================================

-- Products table - Product catalog management
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    sku TEXT UNIQUE,
    category TEXT NOT NULL,
    price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
    cost DECIMAL(10,2) CHECK (cost >= 0),
    description TEXT,
    stock_quantity INTEGER DEFAULT 0 CHECK (stock_quantity >= 0),
    reorder_level INTEGER DEFAULT 10 CHECK (reorder_level >= 0),
    weight DECIMAL(8,2),
    dimensions TEXT,
    manufacturer TEXT,
    warranty_months INTEGER CHECK (warranty_months >= 0),
    launch_date DATE,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'discontinued')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customers table - Customer relationship management
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    date_of_birth DATE,
    registration_date DATE NOT NULL,
    segment TEXT NOT NULL,
    lifetime_value DECIMAL(10,2) DEFAULT 0.00 CHECK (lifetime_value >= 0),
    address TEXT,
    city TEXT,
    postal_code TEXT,
    country TEXT DEFAULT 'United States',
    preferred_contact TEXT CHECK (preferred_contact IN ('email', 'phone', 'mail', 'sms')),
    marketing_opt_in BOOLEAN DEFAULT 0,
    last_login DATE,
    account_status TEXT DEFAULT 'active' CHECK (account_status IN ('active', 'inactive', 'suspended')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table - Order management and tracking
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    order_date DATE NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL CHECK (total_amount >= 0),
    tax_amount DECIMAL(10,2) CHECK (tax_amount >= 0),
    shipping_amount DECIMAL(10,2) CHECK (shipping_amount >= 0),
    discount_amount DECIMAL(10,2) DEFAULT 0 CHECK (discount_amount >= 0),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled', 'returned')),
    payment_method TEXT,
    shipping_address TEXT,
    tracking_number TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers (id)
);

-- Order items table - Individual items within orders
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0),
    total_price DECIMAL(10,2) NOT NULL CHECK (total_price >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products (id)
);

-- Reviews table - Product reviews and ratings
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title TEXT,
    review_text TEXT,
    review_date DATE NOT NULL,
    sentiment TEXT CHECK (sentiment IN ('positive', 'neutral', 'negative')),
    helpful_votes INTEGER DEFAULT 0 CHECK (helpful_votes >= 0),
    verified_purchase BOOLEAN DEFAULT 0,
    response_text TEXT,
    response_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products (id),
    FOREIGN KEY (customer_id) REFERENCES customers (id)
);

-- Inventory transactions table - Stock movement tracking
CREATE TABLE IF NOT EXISTS inventory_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('purchase', 'sale', 'adjustment', 'return')),
    quantity INTEGER NOT NULL,
    cost_per_unit DECIMAL(10,2) CHECK (cost_per_unit >= 0),
    total_cost DECIMAL(10,2) CHECK (total_cost >= 0),
    supplier TEXT,
    transaction_date DATE NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products (id)
);

-- =================================================================
-- HEALTHCARE BUSINESS SCHEMA
-- =================================================================

-- Patients table - Patient information management
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    date_of_birth DATE NOT NULL,
    gender TEXT CHECK (gender IN ('M', 'F', 'O', 'male', 'female', 'other')),
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
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'deceased')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Medical services table - Available medical services and procedures
CREATE TABLE IF NOT EXISTS medical_services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    duration_minutes INTEGER CHECK (duration_minutes > 0),
    base_cost DECIMAL(10,2) CHECK (base_cost >= 0),
    insurance_billable BOOLEAN DEFAULT 1,
    department TEXT,
    requires_referral BOOLEAN DEFAULT 0,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Appointments table - Patient appointment scheduling
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    service_id INTEGER NOT NULL,
    doctor_id INTEGER,
    appointment_date DATETIME NOT NULL,
    duration_minutes INTEGER CHECK (duration_minutes > 0),
    status TEXT DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'completed', 'cancelled', 'no_show')),
    notes TEXT,
    cost DECIMAL(10,2) CHECK (cost >= 0),
    insurance_claim_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients (id),
    FOREIGN KEY (service_id) REFERENCES medical_services (id),
    FOREIGN KEY (doctor_id) REFERENCES employees (id)
);

-- Medical records table - Patient medical history and records
CREATE TABLE IF NOT EXISTS medical_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    appointment_id INTEGER,
    record_type TEXT NOT NULL CHECK (record_type IN ('diagnosis', 'prescription', 'lab_result', 'note', 'procedure')),
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

-- =================================================================
-- FINANCE BUSINESS SCHEMA
-- =================================================================

-- Note: For finance schema, customers table is redefined with finance-specific fields
-- In actual implementation, this would be handled programmatically based on business type

-- Financial customers table - Client information for financial services
CREATE TABLE IF NOT EXISTS financial_customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    date_of_birth DATE,
    registration_date DATE NOT NULL,
    client_type TEXT NOT NULL CHECK (client_type IN ('individual', 'business', 'institutional')),
    risk_profile TEXT DEFAULT 'moderate' CHECK (risk_profile IN ('conservative', 'moderate', 'aggressive')),
    investment_goal TEXT,
    annual_income DECIMAL(12,2) CHECK (annual_income >= 0),
    net_worth DECIMAL(15,2),
    address TEXT,
    city TEXT,
    postal_code TEXT,
    country TEXT DEFAULT 'United States',
    kyc_status TEXT DEFAULT 'pending' CHECK (kyc_status IN ('pending', 'approved', 'rejected')),
    account_status TEXT DEFAULT 'active' CHECK (account_status IN ('active', 'inactive', 'suspended')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Financial products table - Available financial products and services
CREATE TABLE IF NOT EXISTS financial_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    product_type TEXT NOT NULL CHECK (product_type IN ('investment', 'loan', 'insurance', 'savings', 'checking')),
    category TEXT NOT NULL,
    description TEXT,
    minimum_amount DECIMAL(12,2) CHECK (minimum_amount >= 0),
    interest_rate DECIMAL(5,4) CHECK (interest_rate >= 0),
    term_months INTEGER CHECK (term_months > 0),
    risk_level TEXT CHECK (risk_level IN ('low', 'medium', 'high')),
    fees DECIMAL(10,2) CHECK (fees >= 0),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Accounts table - Customer financial accounts
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    account_number TEXT UNIQUE NOT NULL,
    account_type TEXT NOT NULL,
    balance DECIMAL(15,2) DEFAULT 0.00,
    interest_rate DECIMAL(5,4) CHECK (interest_rate >= 0),
    opening_date DATE NOT NULL,
    maturity_date DATE,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'closed', 'suspended')),
    branch_code TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES financial_customers (id),
    FOREIGN KEY (product_id) REFERENCES financial_products (id)
);

-- Transactions table - Financial transaction records
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('deposit', 'withdrawal', 'transfer', 'payment', 'fee', 'interest')),
    amount DECIMAL(12,2) NOT NULL,
    balance_after DECIMAL(15,2),
    description TEXT,
    transaction_date DATETIME NOT NULL,
    reference_number TEXT UNIQUE,
    counterparty_account TEXT,
    fee_amount DECIMAL(10,2) DEFAULT 0.00 CHECK (fee_amount >= 0),
    status TEXT DEFAULT 'completed' CHECK (status IN ('pending', 'completed', 'failed', 'cancelled')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts (id)
);

-- Loans table - Loan management and tracking
CREATE TABLE IF NOT EXISTS loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    loan_type TEXT NOT NULL CHECK (loan_type IN ('personal', 'mortgage', 'business', 'auto', 'student')),
    principal_amount DECIMAL(12,2) NOT NULL CHECK (principal_amount > 0),
    interest_rate DECIMAL(5,4) NOT NULL CHECK (interest_rate >= 0),
    term_months INTEGER NOT NULL CHECK (term_months > 0),
    monthly_payment DECIMAL(10,2) CHECK (monthly_payment > 0),
    outstanding_balance DECIMAL(12,2) CHECK (outstanding_balance >= 0),
    origination_date DATE NOT NULL,
    maturity_date DATE NOT NULL,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paid_off', 'defaulted', 'restructured')),
    collateral_description TEXT,
    purpose TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES financial_customers (id)
);

-- Portfolio holdings table - Investment portfolio management
CREATE TABLE IF NOT EXISTS portfolio_holdings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    security_type TEXT NOT NULL CHECK (security_type IN ('stock', 'bond', 'mutual_fund', 'etf', 'options', 'commodity')),
    quantity DECIMAL(12,4) CHECK (quantity > 0),
    purchase_price DECIMAL(10,4) CHECK (purchase_price > 0),
    current_price DECIMAL(10,4) CHECK (current_price >= 0),
    purchase_date DATE NOT NULL,
    market_value DECIMAL(12,2) CHECK (market_value >= 0),
    unrealized_gain_loss DECIMAL(12,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES financial_customers (id)
);

-- =================================================================
-- AUDIT AND SYSTEM TABLES (Common to all business types)
-- =================================================================

-- Audit trail table - System audit logging
CREATE TABLE IF NOT EXISTS audit_trail (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_values TEXT, -- JSON format
    new_values TEXT, -- JSON format
    user_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES employees (id)
);

-- Settings table - Application configuration
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    setting_key TEXT NOT NULL,
    setting_value TEXT,
    description TEXT,
    is_system BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category, setting_key)
);

-- =================================================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- =================================================================

-- Customer indexes
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_segment ON customers(segment);
CREATE INDEX IF NOT EXISTS idx_customers_registration_date ON customers(registration_date);

-- Product indexes
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);

-- Order indexes
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_order_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);

-- Review indexes
CREATE INDEX IF NOT EXISTS idx_reviews_product_id ON reviews(product_id);
CREATE INDEX IF NOT EXISTS idx_reviews_customer_id ON reviews(customer_id);
CREATE INDEX IF NOT EXISTS idx_reviews_rating ON reviews(rating);

-- Healthcare indexes
CREATE INDEX IF NOT EXISTS idx_patients_medical_record_number ON patients(medical_record_number);
CREATE INDEX IF NOT EXISTS idx_appointments_patient_id ON appointments(patient_id);
CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date);
CREATE INDEX IF NOT EXISTS idx_medical_records_patient_id ON medical_records(patient_id);

-- Finance indexes
CREATE INDEX IF NOT EXISTS idx_accounts_customer_id ON accounts(customer_id);
CREATE INDEX IF NOT EXISTS idx_accounts_account_number ON accounts(account_number);
CREATE INDEX IF NOT EXISTS idx_transactions_account_id ON transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_loans_customer_id ON loans(customer_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_customer_id ON portfolio_holdings(customer_id);

-- System indexes
CREATE INDEX IF NOT EXISTS idx_audit_trail_table_record ON audit_trail(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_audit_trail_timestamp ON audit_trail(timestamp);

-- =================================================================
-- VIEWS FOR COMMON BUSINESS INTELLIGENCE QUERIES
-- =================================================================

-- Customer lifetime value view
CREATE VIEW IF NOT EXISTS customer_analytics AS
SELECT 
    c.id,
    c.first_name,
    c.last_name,
    c.email,
    c.segment,
    c.registration_date,
    COUNT(o.id) as total_orders,
    COALESCE(SUM(o.total_amount), 0) as total_spent,
    COALESCE(AVG(o.total_amount), 0) as avg_order_value,
    MAX(o.order_date) as last_order_date,
    ROUND(JULIANDAY('now') - JULIANDAY(MAX(o.order_date))) as days_since_last_order
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
GROUP BY c.id, c.first_name, c.last_name, c.email, c.segment, c.registration_date;

-- Product performance view
CREATE VIEW IF NOT EXISTS product_performance AS
SELECT 
    p.id,
    p.name,
    p.category,
    p.price,
    p.stock_quantity,
    COUNT(oi.id) as times_ordered,
    COALESCE(SUM(oi.quantity), 0) as total_quantity_sold,
    COALESCE(SUM(oi.total_price), 0) as total_revenue,
    COALESCE(AVG(r.rating), 0) as avg_rating,
    COUNT(r.id) as review_count
FROM products p
LEFT JOIN order_items oi ON p.id = oi.product_id
LEFT JOIN reviews r ON p.id = r.product_id
GROUP BY p.id, p.name, p.category, p.price, p.stock_quantity;

-- Monthly sales summary view
CREATE VIEW IF NOT EXISTS monthly_sales AS
SELECT 
    strftime('%Y-%m', order_date) as month,
    COUNT(*) as order_count,
    SUM(total_amount) as total_revenue,
    AVG(total_amount) as avg_order_value,
    COUNT(DISTINCT customer_id) as unique_customers
FROM orders
GROUP BY strftime('%Y-%m', order_date)
ORDER BY month;

-- =================================================================
-- TRIGGERS FOR DATA INTEGRITY AND AUDIT
-- =================================================================

-- Update customer lifetime value when orders change
CREATE TRIGGER IF NOT EXISTS update_customer_ltv 
AFTER INSERT ON orders
BEGIN
    UPDATE customers 
    SET lifetime_value = (
        SELECT COALESCE(SUM(total_amount), 0) 
        FROM orders 
        WHERE customer_id = NEW.customer_id
    )
    WHERE id = NEW.customer_id;
END;

-- Audit trigger for important table changes
CREATE TRIGGER IF NOT EXISTS audit_customers_changes 
AFTER UPDATE ON customers
BEGIN
    INSERT INTO audit_trail (table_name, record_id, action, old_values, new_values)
    VALUES (
        'customers', 
        NEW.id, 
        'UPDATE',
        json_object(
            'first_name', OLD.first_name,
            'last_name', OLD.last_name,
            'email', OLD.email,
            'segment', OLD.segment,
            'account_status', OLD.account_status
        ),
        json_object(
            'first_name', NEW.first_name,
            'last_name', NEW.last_name,
            'email', NEW.email,
            'segment', NEW.segment,
            'account_status', NEW.account_status
        )
    );
END;

-- =================================================================
-- INITIAL DATA SETUP
-- =================================================================

-- Default settings
INSERT OR IGNORE INTO settings (category, setting_key, setting_value, description, is_system) VALUES
('system', 'schema_version', '1.0', 'Database schema version', 1),
('system', 'created_date', date('now'), 'Database creation date', 1),
('business', 'default_currency', 'USD', 'Default currency for transactions', 0),
('business', 'tax_rate', '0.08', 'Default tax rate percentage', 0),
('business', 'fiscal_year_start', '01-01', 'Fiscal year start date (MM-DD)', 0);

-- =================================================================
-- COMMENTS AND DOCUMENTATION
-- =================================================================

/*
BUSINESS INTELLIGENCE SCHEMA NOTES:

1. MULTI-BUSINESS TYPE SUPPORT:
   - Retail: Focus on products, customers, orders, inventory
   - Healthcare: Focus on patients, appointments, medical records
   - Finance: Focus on accounts, transactions, investments

2. DATA INTEGRITY:
   - Foreign key constraints ensure referential integrity
   - Check constraints validate data ranges and values
   - Unique constraints prevent duplicate critical data

3. PERFORMANCE OPTIMIZATION:
   - Strategic indexes on frequently queried columns
   - Views for common business intelligence queries
   - Proper normalization to reduce redundancy

4. AUDIT AND COMPLIANCE:
   - Audit trail for tracking changes
   - Timestamp fields for data lineage
   - Status fields for soft deletes and state tracking

5. EXTENSIBILITY:
   - Settings table for configuration
   - JSON fields for flexible data storage
   - Modular design for adding new business types

6. BUSINESS INTELLIGENCE READY:
   - Pre-built views for common analytics
   - Calculated fields for KPIs
   - Time-based partitioning friendly structure

This schema is designed to be used by the AI-powered RAG chatbot system
for generating intelligent business insights and answering natural language
queries about business data.
*/