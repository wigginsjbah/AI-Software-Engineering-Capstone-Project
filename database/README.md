# Database Folder - Your Business Data Storage

## What This Folder Does (Simple Explanation)
This folder is like a digital filing cabinet for all your business information. It stores everything about your products, customers, orders, and reviews in an organized way so the chatbot can quickly find and use this information to answer your questions. Think of it as the memory bank that remembers every sale, every customer, and every product detail.

## Technical Description
The `database/` directory implements the data persistence layer using SQLAlchemy ORM with async support. It provides database connectivity, schema management, and data access patterns for the business intelligence system.

### Structure:
- **`connection.py`** - Database connection management and session handling
- **`models.py`** - SQLAlchemy ORM models defining database schema
- **`schemas.py`** - Database table definitions and relationships
- **`seed_data.py`** - Sample data generation for development and testing
- **`migrations/`** - Database migration scripts for schema evolution

### Key Responsibilities:
1. **Data Storage**: Persistent storage of business entities (products, customers, orders, reviews)
2. **Query Execution**: Safe SQL query execution with parameter binding
3. **Connection Management**: Async database connection pooling and lifecycle management
4. **Schema Management**: Database table creation, indexing, and relationship definitions
5. **Data Integrity**: Transaction management and referential integrity constraints

## What's Stored Here:
- **Products**: All your product catalog with prices, descriptions, categories
- **Customers**: Customer profiles, contact info, and purchase history
- **Orders**: Every transaction with dates, amounts, and status
- **Reviews**: Customer feedback and ratings for products
- **Sales Data**: Performance metrics by region and time period

## Why This Matters:
Without this folder, the chatbot would have no memory of your business. It's like the difference between talking to someone with amnesia versus someone who remembers every detail about your company's performance and customers.