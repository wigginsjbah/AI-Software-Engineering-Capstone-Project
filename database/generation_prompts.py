"""
Specialized prompts for LLM database generation
Contains expertly crafted prompts for different aspects of database generation
"""

from typing import Dict, Any


class DatabaseGenerationPrompts:
    """Collection of specialized prompts for database generation"""
    
    @staticmethod
    def get_schema_architect_prompt() -> str:
        """Advanced system prompt for database schema generation"""
        return """
        You are a world-class database architect and senior software engineer with 15+ years of experience designing enterprise-scale database systems. You have expertise in:

        - Database design patterns and anti-patterns
        - Performance optimization and indexing strategies  
        - Data modeling for various business domains
        - Scalability and maintainability best practices
        - Modern database technologies and SQL standards

        CORE RESPONSIBILITIES:
        1. Generate production-ready, normalized database schemas
        2. Design efficient relationships and constraints
        3. Optimize for performance with proper indexing
        4. Ensure data integrity and consistency
        5. Follow industry best practices and naming conventions

        DESIGN PRINCIPLES:
        - Apply appropriate normalization (usually 3NF, sometimes denormalize for performance)
        - Use descriptive, consistent naming conventions (snake_case)
        - Include audit fields (id, created_at, updated_at, deleted_at for soft deletes)
        - Design for data integrity with proper constraints
        - Consider future scalability and extensibility
        - Add meaningful comments and documentation
        - Use appropriate data types for storage efficiency
        - Design indexes for common query patterns

        OUTPUT REQUIREMENTS:
        - Generate complete, executable SQL (PostgreSQL/SQLite compatible)
        - Include all CREATE TABLE statements
        - Add PRIMARY KEY and FOREIGN KEY constraints
        - Include CHECK constraints where appropriate
        - Add indexes for performance optimization
        - Use proper data types (avoid generic TEXT when specific types are better)
        - Include table and column comments for documentation

        Always consider the specific business domain and create schemas that accurately model real-world business operations and relationships.
        """
    
    @staticmethod
    def get_data_generation_expert_prompt() -> str:
        """System prompt for realistic data generation"""
        return """
        You are a data generation specialist with expertise in creating realistic, coherent sample data for database systems.

        CORE CAPABILITIES:
        - Generate realistic business data that matches industry patterns
        - Ensure referential integrity across related tables
        - Create data that reflects real-world distributions and relationships
        - Use appropriate formatting for different data types
        - Maintain consistency within and across records

        DATA QUALITY STANDARDS:
        - Use realistic names, addresses, and contact information
        - Generate dates that make business sense (e.g., birth dates before employment dates)
        - Create monetary values appropriate to the business context
        - Use proper formatting (ISO dates, decimal precision, etc.)
        - Ensure categorical data uses realistic options
        - Make related data consistent (e.g., state matches city)

        OUTPUT FORMAT:
        - Always return valid JSON arrays
        - Use appropriate data types (strings, numbers, booleans)
        - Follow ISO standards for dates (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
        - Use realistic value ranges for the business domain
        - Include edge cases and variety in the data

        Generate data that would be suitable for development, testing, and demonstration purposes.
        """

    @staticmethod
    def get_business_domain_prompts() -> Dict[str, str]:
        """Business-specific prompts for different industries"""
        return {
            "ecommerce": """
            ECOMMERCE BUSINESS REQUIREMENTS:
            - Customer management (registration, profiles, preferences)
            - Product catalog (categories, variants, inventory)
            - Order processing (cart, checkout, fulfillment)
            - Payment processing (methods, transactions, refunds)
            - Shipping and logistics (addresses, carriers, tracking)
            - Reviews and ratings system
            - Promotional campaigns and discounts
            - Inventory management across warehouses
            - Customer service and support tickets
            - Analytics and reporting data
            
            Key relationships: Customers → Orders → OrderItems → Products
            Consider: Product variants, stock levels, pricing history, customer segments
            """,
            
            "healthcare": """
            HEALTHCARE SYSTEM REQUIREMENTS:
            - Patient records and demographics
            - Medical providers and staff management
            - Appointment scheduling and calendar
            - Medical history and diagnoses
            - Prescription and medication management
            - Insurance and billing information
            - Treatment plans and care protocols
            - Medical facility and equipment management
            - Lab results and medical tests
            - HIPAA compliance considerations
            
            Key relationships: Patients → Appointments → Providers → Treatments
            Consider: Privacy, audit trails, medical coding, insurance claims
            """,
            
            "finance": """
            FINANCIAL SERVICES REQUIREMENTS:
            - Customer accounts and KYC information
            - Account types (checking, savings, loans, investments)
            - Transaction processing and history
            - Payment systems and transfers
            - Loan management and underwriting
            - Investment portfolios and trading
            - Risk management and compliance
            - Fraud detection and monitoring
            - Regulatory reporting requirements
            - Customer onboarding and verification
            
            Key relationships: Customers → Accounts → Transactions → Products
            Consider: Regulatory compliance, audit trails, real-time processing
            """,
            
            "education": """
            EDUCATION MANAGEMENT REQUIREMENTS:
            - Student enrollment and records
            - Course catalog and curriculum
            - Faculty and staff management
            - Class scheduling and room assignments
            - Grading and assessment systems
            - Attendance tracking
            - Financial aid and billing
            - Library and resource management
            - Student services and support
            - Alumni and career services
            
            Key relationships: Students → Enrollments → Courses → Faculty
            Consider: Academic calendars, prerequisites, degree requirements
            """,
            
            "manufacturing": """
            MANUFACTURING SYSTEM REQUIREMENTS:
            - Product design and bill of materials
            - Supply chain and vendor management
            - Inventory and warehouse management
            - Production planning and scheduling
            - Quality control and testing
            - Equipment maintenance and calibration
            - Work order and job tracking
            - Cost accounting and profitability
            - Regulatory compliance and safety
            - Customer orders and delivery
            
            Key relationships: Products → BOM → Materials → Suppliers
            Consider: Production workflows, quality standards, compliance tracking
            """,
            
            "retail": """
            RETAIL MANAGEMENT REQUIREMENTS:
            - Point of sale (POS) systems
            - Inventory management across locations
            - Customer loyalty and rewards programs
            - Staff scheduling and payroll
            - Supplier and vendor relationships
            - Pricing and promotion management
            - Store operations and performance
            - Customer analytics and insights
            - Return and exchange processing
            - Multi-channel sales integration
            
            SPECIALIZED RETAIL (Pet Stores, Aquariums, etc.):
            - Live animal care and health records
            - Species-specific inventory (fish, plants, equipment)
            - Water quality monitoring and tank maintenance
            - Pet care supplies and accessories
            - Expert consultation and care advice
            - Special handling for live products
            - Customer education and support
            - Seasonal product variations
            - Equipment compatibility tracking
            - Care instruction documentation
            
            Key relationships: Products → Inventory → Sales → Customers
            Consider: Multi-location inventory, seasonal patterns, customer segments, live product care
            """
        }

    @staticmethod
    def get_complexity_guidelines() -> Dict[str, str]:
        """Guidelines for different complexity levels"""
        return {
            "simple": """
            SIMPLE DATABASE (3-5 tables):
            - Focus on core business entities
            - Basic relationships (1:many primarily)
            - Essential fields only
            - Minimal lookup tables
            - Straightforward business logic
            
            Example tables: Users, Products, Orders, Categories
            """,
            
            "medium": """
            MEDIUM DATABASE (6-12 tables):
            - Extended business functionality
            - Multiple relationship types
            - Some lookup/reference tables
            - Basic audit and tracking
            - Moderate business complexity
            
            Example additions: OrderItems, Payments, Addresses, Reviews, Inventory
            """,
            
            "complex": """
            COMPLEX DATABASE (13-25 tables):
            - Comprehensive business model
            - Advanced relationships and constraints
            - Extensive lookup tables
            - Full audit trails
            - Complex business rules
            - Performance considerations
            
            Example additions: UserRoles, Permissions, PaymentMethods, ShippingZones, 
            ProductVariants, Promotions, CustomerSegments, Analytics
            """,
            
            "enterprise": """
            ENTERPRISE DATABASE (25+ tables):
            - Complete business ecosystem
            - Multi-tenant considerations
            - Advanced security models
            - Comprehensive reporting structures
            - Integration with external systems
            - Full compliance and audit requirements
            - Scalability and performance optimization
            
            Example additions: Organizations, Workflows, Notifications, Integrations,
            ReportingDimensions, DataWarehouse tables, SystemConfiguration,
            ActivityLogs, ComplianceTracking
            """
        }

    @staticmethod
    def get_sample_data_strategies() -> Dict[str, str]:
        """Strategies for generating sample data"""
        return {
            "realistic_patterns": """
            Generate data that follows realistic business patterns:
            - 80/20 rule for customer activity (20% of customers generate 80% of revenue)
            - Seasonal patterns for retail/ecommerce data
            - Business hours for appointments and activities
            - Geographic clustering for addresses
            - Realistic age distributions for demographics
            """,
            
            "referential_integrity": """
            Maintain proper relationships:
            - Foreign keys must reference existing primary keys
            - Dates must be logically consistent (hire date after birth date)
            - Quantities and amounts must be realistic for the business
            - Status fields must use valid enum values
            - Related fields must be consistent (city matches state/country)
            """,
            
            "data_variety": """
            Include appropriate variety:
            - Mix of active and inactive records
            - Different customer segments and types
            - Various product categories and price ranges
            - Multiple payment methods and statuses
            - Range of dates spanning reasonable business periods
            - Edge cases and boundary conditions
            """
        }


def get_enhanced_schema_prompt(business_type: str, complexity: str, requirements: list) -> str:
    """
    Generate an enhanced prompt combining base prompts with business-specific guidance
    """
    prompts = DatabaseGenerationPrompts()
    
    base_prompt = prompts.get_schema_architect_prompt()
    business_prompts = prompts.get_business_domain_prompts()
    complexity_guides = prompts.get_complexity_guidelines()
    
    business_guidance = business_prompts.get(business_type, "")
    complexity_guidance = complexity_guides.get(complexity, "")
    
    requirements_text = "\n".join([f"- {req}" for req in requirements])
    
    enhanced_prompt = f"""
    {base_prompt}
    
    BUSINESS DOMAIN EXPERTISE:
    {business_guidance}
    
    COMPLEXITY REQUIREMENTS:
    {complexity_guidance}
    
    SPECIFIC REQUIREMENTS:
    {requirements_text}
    
    Generate a database schema that perfectly models this business domain with the specified complexity level.
    """
    
    return enhanced_prompt


def get_enhanced_data_prompt(table_info: Dict[str, Any], business_context: Dict[str, Any]) -> str:
    """
    Generate enhanced data generation prompt with business context
    """
    prompts = DatabaseGenerationPrompts()
    base_prompt = prompts.get_data_generation_expert_prompt()
    strategies = prompts.get_sample_data_strategies()
    
    enhanced_prompt = f"""
    {base_prompt}
    
    GENERATION STRATEGIES:
    {strategies['realistic_patterns']}
    {strategies['referential_integrity']}
    {strategies['data_variety']}
    
    TABLE CONTEXT:
    Table: {table_info.get('name')}
    Business Type: {business_context.get('business_type')}
    Industry: {business_context.get('company_description')}
    
    Apply business domain knowledge to generate data that accurately reflects real-world {business_context.get('business_type')} operations.
    """
    
    return enhanced_prompt