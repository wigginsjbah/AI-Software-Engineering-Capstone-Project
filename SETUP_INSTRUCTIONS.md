# Setup Instructions for Business Intelligence RAG Chatbot

## 📋 Prerequisites
- Windows 10/11 with PowerShell
- Git installed
- Internet connection for package downloads

## 🚀 Quick Setup Guide

### Step 1: Clone and Navigate to Project
```powershell
# If you haven't cloned yet:
git clone https://github.com/wigginsjbah/AI-Software-Engineering-Capstone-Project.git
cd AI-Software-Engineering-Capstone-Project

# Switch to the nathaniel-branch (where all the latest changes are)
git checkout nathaniel-branch
```

### Step 2: Verify Python Installation
```powershell
# Check if Python is installed
py --version
# Should show: Python 3.13.7

# If Python is not installed, download from: https://python.org
# Make sure to check "Add Python to PATH" during installation
```

### Step 3: Install Dependencies
We've resolved all compatibility issues with Python 3.13. Install dependencies step by step:

```powershell
# Step 3a: Upgrade pip and build tools
py -m pip install --upgrade pip setuptools wheel

# Step 3b: Install core web framework
py -m pip install fastapi uvicorn pydantic python-multipart

# Step 3c: Install AI services
py -m pip install openai tavily-python

# Step 3d: Install database components
py -m pip install sqlalchemy alembic aiosqlite python-dotenv pydantic-settings

# Step 3e: Install data processing tools
py -m pip install pandas faker loguru

# Step 3f: Verify installation
py -c "import fastapi, openai, tavily, sqlalchemy, pandas; print('✅ All dependencies installed successfully!')"
```

### Step 4: Set Up Database
```powershell
# Create sample business database
py simple_setup.py

# Verify database creation
py -c "import sqlite3; conn = sqlite3.connect('business_data.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM products'); print(f'Database has {cursor.fetchone()[0]} products'); conn.close()"
```

### Step 5: Verify API Keys
Check that your `.env` file has the required API keys:
```powershell
# View the .env file
type .env
```

Should show:
```
TAVILY_API_KEY="your-tavily-api-key-here"
OPENAI_API_KEY="your-openai-api-key-here"
```

### Step 6: Test Core Components
```powershell
# Test API keys work
py -c "import openai; print('OpenAI available'); import tavily; print('Tavily available')"

# Test database connectivity
py -c "import sqlite3; conn = sqlite3.connect('business_data.db'); cursor = conn.cursor(); cursor.execute('SELECT name, category FROM products LIMIT 3'); print('Sample products:', cursor.fetchall()); conn.close()"
```

## 🎯 Project Structure Overview

After setup, you'll have this structure:
```
├── app/                    # Main FastAPI application
│   ├── api/               # REST API endpoints
│   ├── core/              # Business logic & RAG engine
│   └── models/            # Data models
├── database/              # Database management
├── rag/                   # RAG system components
├── agents/                # Multi-agent system
├── frontend/              # Web interface
├── config/                # Configuration & settings
├── scripts/               # Automation tools
├── data/                  # Data storage
├── utils/                 # Utility functions
├── tests/                 # Quality assurance
├── docs/                  # Documentation
├── business_data.db       # SQLite database (created in step 4)
└── simple_setup.py        # Database setup script
```

## 🔧 Development Commands

### Running the Application
```powershell
# Start the FastAPI server (when ready)
py -m uvicorn app.main:app --reload --port 8000

# Access the application at: http://localhost:8000
```

### Database Operations
```powershell
# Recreate database with fresh data
py simple_setup.py

# Query database directly
py -c "import sqlite3; conn = sqlite3.connect('business_data.db'); cursor = conn.cursor(); cursor.execute('SELECT * FROM products'); print(cursor.fetchall()); conn.close()"
```

### Development Workflow
```powershell
# Pull latest changes
git pull origin nathaniel-branch

# Make your changes...

# Commit and push
git add .
git commit -m "Your descriptive commit message"
git push origin nathaniel-branch
```

## 🆘 Troubleshooting

### Common Issues:

1. **"Python was not found"**
   - Install Python from python.org
   - Use `py` command instead of `python`

2. **"faiss-cpu version error"**
   - Already fixed in our requirements.txt
   - Use the step-by-step installation above

3. **"Module not found" errors**
   - Run the installation steps in order
   - Don't try to run the full app until all dependencies are installed

4. **Database errors**
   - Run `py simple_setup.py` to recreate the database
   - Check that `business_data.db` file exists

5. **Import errors from app.main**
   - The full application has advanced dependencies not yet installed
   - Use the testing commands provided above instead

### Getting Help
- Check the README files in each folder for detailed explanations
- Use the testing commands to verify each component
- Ask in the team chat with specific error messages

## 📚 Next Steps for Development

1. **Study the Project Structure**: Read the README.md files in each folder
2. **Understand the Architecture**: Review the main README.md for system overview
3. **Start with Simple Components**: Begin with basic API endpoints
4. **Add Features Incrementally**: Build up the RAG system step by step
5. **Test Frequently**: Use the verification commands throughout development

## 🔑 Important Notes

- **API Keys**: Never commit API keys to git (they're already in .env and .gitignore)
- **Database**: The SQLite file is local - each developer needs to run setup
- **Branch**: Work on `nathaniel-branch` where all the latest changes are
- **Testing**: Always test your changes with the verification commands
- **Documentation**: Update README files when adding new features

Happy coding! 🚀