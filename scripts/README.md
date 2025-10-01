# Scripts Folder - The Automation Tools

## What This Folder Does (Simple Explanation)
This folder contains automated scripts that help you set up, maintain, and manage your business intelligence chatbot. Think of these as "power tools" that automate repetitive tasks - like having a robot assistant that can set up your database, generate test data, create backups, or run maintenance tasks. Instead of doing these complex setup tasks manually (which could take hours), you just run a script and it does everything for you automatically.

## Technical Description
The `scripts/` directory contains executable Python scripts for system administration, data management, development workflows, and operational tasks. These scripts implement automation for common administrative and maintenance operations.

### Structure:
- **`setup_database.py`** - Database initialization and schema creation
- **`generate_embeddings.py`** - Vector database population and indexing
- **`load_sample_data.py`** - Sample business data generation for development
- **`run_evaluation.py`** - System performance and accuracy evaluation
- **`backup_data.py`** - Data backup and export utilities
- **`migrate_data.py`** - Data migration and schema updates
- **`health_check.py`** - System health monitoring and diagnostics
- **`deploy.py`** - Deployment automation and configuration

### Key Technical Functions:
1. **Environment Setup**: Automated system initialization and configuration
2. **Data Management**: Bulk data operations, migrations, and transformations
3. **System Maintenance**: Health checks, backups, and routine maintenance tasks
4. **Development Workflows**: Testing data generation and development environment setup
5. **Deployment Operations**: Production deployment and configuration management
6. **Performance Monitoring**: System evaluation and optimization scripts

## Your Automation Toolkit:

### 🏗️ **Setup Database (`setup_database.py`)**
- **What it does**: Creates your business database from scratch with sample data
- **When to use**: First time setup or when you need fresh test data
- **What it creates**: 
  - 50+ sample products across different categories
  - 200+ customer profiles with realistic data
  - 1,000+ order records with purchase history
  - 500+ customer reviews with sentiment analysis
  - Sales performance data by region and time

### 🧠 **Generate Embeddings (`generate_embeddings.py`)**
- **What it does**: Converts all your business documents into searchable "fingerprints"
- **When to use**: After adding new documents or when setting up the RAG system
- **Technical process**: Creates vector embeddings for semantic search

### 📊 **Load Sample Data (`load_sample_data.py`)**
- **What it does**: Adds realistic business data for testing and demonstration
- **When to use**: Development, testing, or demo environments
- **Data includes**: Products, customers, orders, reviews with realistic relationships

### 🔍 **Run Evaluation (`run_evaluation.py`)**
- **What it does**: Tests how well your chatbot is performing and identifies areas for improvement
- **When to use**: Regular performance checks or after making system changes
- **What it measures**: Response accuracy, speed, source attribution quality

### 💾 **Backup Data (`backup_data.py`)**
- **What it does**: Creates secure backups of your business data and system configuration
- **When to use**: Before major updates, regularly for data protection
- **Backup includes**: Database, vector store, configuration files, generated reports

### 🔄 **Migrate Data (`migrate_data.py`)**
- **What it does**: Safely updates your database structure when the system evolves
- **When to use**: System updates that require database changes
- **Safety features**: Backup before migration, rollback capability

### 🏥 **Health Check (`health_check.py`)**
- **What it does**: Comprehensive system diagnostics and performance monitoring
- **When to use**: Troubleshooting issues or regular system monitoring
- **Checks include**: Database connectivity, API availability, system resources

### 🚀 **Deploy (`deploy.py`)**
- **What it does**: Automates deployment to production environments
- **When to use**: Moving from development to production
- **Handles**: Configuration, dependencies, database setup, service startup

## How to Use These Scripts:

### For Initial Setup:
```powershell
# 1. Set up the database with sample data
python scripts/setup_database.py

# 2. Generate embeddings for search
python scripts/generate_embeddings.py

# 3. Run health check to verify everything works
python scripts/health_check.py
```

### For Regular Maintenance:
```powershell
# Weekly backup
python scripts/backup_data.py

# Monthly performance evaluation
python scripts/run_evaluation.py

# As needed: add new sample data
python scripts/load_sample_data.py
```

## Why Scripts Are Essential:

### ⏰ **Time Saving**
- Tasks that would take hours are completed in minutes
- Consistent, repeatable processes
- No human error in complex setup procedures

### 🎯 **Consistency**
- Same setup process every time
- Standardized data formats and structures
- Reliable development and production environments

### 🛡️ **Safety**
- Built-in backup and rollback procedures
- Validation checks before making changes
- Error handling and recovery mechanisms

### 📈 **Scalability**
- Can handle large amounts of data
- Automated processes work the same regardless of data size
- Easy to schedule for regular execution

These scripts turn complex system administration into simple one-command operations - they're like having an expert system administrator on your team 24/7!