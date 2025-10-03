# AI-Powered Business Intelligence Platform

A comprehensive AI-driven platform that generates custom business databases and provides intelligent business analytics through RAG (Retrieval-Augmented Generation) technology. The system combines OpenAI's GPT-4 with Tavily API for external market research, enabling businesses to get data-driven insights from both internal data and external market trends.

## 🚀 Key Features

### 🏗️ **AI Database Generation**
- **Custom Business Databases**: Generate complete database schemas for 11+ business types (E-commerce, Healthcare, Finance, Manufacturing, etc.)
- **Intelligent Schema Design**: AI-powered table relationships, constraints, and indexing
- **Realistic Sample Data**: Automatically populate databases with business-realistic data
- **Multiple Complexity Levels**: From simple (3-5 tables) to enterprise (25+ tables)

### 💬 **Intelligent Business Chatbot**
- **Natural Language Queries**: Ask business questions in plain English
- **Multi-Source RAG**: Combines database queries, vector search, and external research
- **Real-time Analysis**: Instant insights on sales, customers, products, and performance
- **External Market Research**: Industry trends and competitive intelligence via Tavily API

### 🏢 **Multi-Company Management**
- **Company Profiles**: Create and manage multiple business entities
- **Database Switching**: Seamlessly switch between different company databases
- **Custom Business Types**: Support for E-commerce, Healthcare, Finance, Technology, Retail, and more
- **Isolated Environments**: Each company maintains separate data and context

### 🤖 **Multi-Agent Architecture**
- **Data Analyst Agent**: SQL query generation and data extraction
- **Business Advisor Agent**: Strategic insights and recommendations
- **Trend Analysis Agent**: Market trends and temporal pattern analysis
- **Report Generator Agent**: Automated business report creation

### 🎨 **Modern React Frontend**
- **Glassmorphism Design**: Modern glass-like UI with backdrop blur effects
- **Responsive Layout**: Mobile and desktop optimized interface
- **Real-time Chat**: Interactive business intelligence conversations
- **Company Management**: Create and switch between business databases
- **Data Visualization**: Explore database schemas and sample data
- **AI-Generated Components**: All React components created with AI assistance

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │   FastAPI       │    │   RAG Engine    │
│   (HTML/JS)     │◄──►│   Backend       │◄──►│   (OpenAI)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │ AI Database     │    │   Vector Store  │
                       │ Generator       │    │   (ChromaDB)    │
                       │ (LLM-Powered)   │    └─────────────────┘
                       └─────────────────┘              │
                                │                       ▼
                                ▼                ┌─────────────────┐
                       ┌─────────────────┐    │   Tavily API    │
                       │  Company DBs    │    │   (External)    │
                       │  (SQLite)       │    └─────────────────┘
                       └─────────────────┘
```

### 🎯 **Supported Business Types**
- **E-commerce**: Product catalogs, orders, customers, inventory
- **Healthcare**: Patients, appointments, medical records, staff
- **Finance**: Accounts, transactions, clients, portfolios
- **Technology**: Projects, developers, deployments, analytics
- **Manufacturing**: Products, inventory, suppliers, quality control
- **Retail**: Stores, sales, customers, inventory management
- **Education**: Students, courses, instructors, enrollments
- **Hospitality**: Reservations, guests, rooms, services
- **Logistics**: Shipments, warehouses, vehicles, tracking
- **Consulting**: Projects, clients, consultants, deliverables
- **Custom**: Define your own business requirements

## 📁 Project Structure

```
├── app/                    # FastAPI web application
│   ├── api/               # REST API endpoints
│   │   ├── chat.py        # AI chatbot endpoints
│   │   ├── companies.py   # Company management
│   │   ├── database_generation.py  # AI database generation
│   │   └── data.py        # Data management endpoints
│   ├── core/              # Core business logic
│   ├── models/            # Pydantic data models
│   └── services/          # Business services
├── database/              # AI database generation system
│   ├── llm_generator.py   # LLM-powered schema generation
│   ├── enhanced_llm_generator.py  # Advanced generation
│   ├── data_populator.py  # Realistic data generation
│   └── schema_analyzer.py # Schema validation & analysis
├── agents/                # Multi-agent AI system
│   └── orchestrator.py    # Agent coordination
├── rag/                   # RAG system components
├── react-frontend/        # React user interface
│   ├── src/               # React source code
│   │   ├── App.js         # Main React application
│   │   ├── components/    # React components
│   │   └── App.css        # Glassmorphism styles
│   ├── public/            # Static assets
│   └── package.json       # React dependencies
├── frontend/              # Legacy vanilla JS interface (backup)
│   ├── templates/         # HTML templates
│   └── static/           # CSS, JavaScript, assets
├── docs/                  # Project documentation
│   ├── PRD.md            # Product Requirements Document
│   ├── Architecture_Document.md  # System architecture with UML
│   ├── Security_Vulnerability_Report.md  # Security analysis
│   └── adr/              # Architecture Decision Records
├── tests/                 # Test suite
│   └── test_main.py      # Comprehensive unit tests
├── config/                # Configuration management
├── companies/             # Company data storage
├── scripts/               # Automation utilities
├── data/                  # Sample data and documents
├── utils/                 # Shared utilities
├── vector_store/          # Vector database files
├── ai_code_artifacts.py   # AI-generated code documentation
├── PRESENTATION.md        # Presentation slides and demo script
├── schema.sql            # Database schema example
└── requirements.txt       # Python dependencies
```

## 🛠️ Quick Start Guide

### 1. Prerequisites
- **Python 3.13+** with pip
- **Windows 10/11** with PowerShell
- **Git** for version control
- **Internet connection** for AI APIs

### 2. Installation

```powershell
# Clone the repository
git clone https://github.com/wigginsjbah/AI-Software-Engineering-Capstone-Project.git
cd AI-Software-Engineering-Capstone-Project

# Install dependencies (all compatibility issues resolved)
py -m pip install -r requirements.txt
```

### 3. Environment Setup
The system comes pre-configured with API keys. No additional setup required.

### 4. Launch the Application

**Backend Server:**
```powershell
# Start the FastAPI backend
py -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload

# Alternative ports if 8010 is busy
py -m uvicorn app.main:app --host 127.0.0.1 --port 8011 --reload
```

**React Frontend (Recommended):**
```powershell
# Navigate to React frontend
cd react-frontend

# Install React dependencies (first time only)
npm install

# Start React development server
npm start
```

**Legacy Frontend (Alternative):**
```powershell
# If React frontend is not available, the FastAPI backend serves
# a vanilla JS interface at the same URL
```

### 5. Access the Platform
- **React Frontend**: http://localhost:3000 (recommended)
- **Backend API + Legacy Frontend**: http://localhost:8010

## 🎯 Getting Started - Usage Examples

### Creating Your First Business Database

1. **Navigate to Company Management**: Click "Company Manager" in the web interface
2. **Create New Company**: 
   - Choose business type (e.g., "E-commerce", "Healthcare")
   - Set complexity level (Simple, Medium, Complex, Enterprise)
   - Provide business description
3. **AI Generation**: The system generates a complete database schema with sample data
4. **Switch & Analyze**: Switch to your new company and start asking business questions

### Example Business Questions

#### 📊 **Data Analysis**
- "What are our top 10 best-selling products this quarter?"
- "Show me customer lifetime value by segment"
- "Which regions have the highest profit margins?"
- "What's our average order value trend?"

#### 📈 **Trend Analysis**
- "How have our sales changed over the last 6 months?"
- "Which product categories are growing fastest?"
- "Show me seasonal patterns in customer behavior"
- "What are our customer retention rates by cohort?"

#### 🔍 **Comparative Analysis**
- "Compare performance between our Electronics and Clothing divisions"
- "Which customer segments have the best satisfaction scores?"
- "How do our Premium vs Standard customers differ?"

#### 🌍 **Market Research** (via Tavily API)
- "What are current trends in the healthcare technology market?"
- "How do our customer satisfaction scores compare to industry standards?"
- "What innovations are competitors introducing in e-commerce?"

### Trend Analysis
- "How have our sales trends changed over the last 6 months?"
- "Which product categories are growing fastest?"
- "Show me seasonal patterns in our customer orders"

### Comparative Analysis
- "Compare the performance of our Electronics vs Clothing categories"
- "Which regions have the best customer satisfaction ratings?"
- "How do our Premium customers differ from Standard customers?"

### Report Generation
- "Generate a comprehensive sales performance report"
- "Create a customer segmentation analysis report"
- "Show me a product performance dashboard"

### External Market Research
- "What are the current market trends in the electronics industry?"
- "How do our customer satisfaction scores compare to industry benchmarks?"
- "What are competitors doing in the smartphone market?"

## ⚙️ Advanced Configuration

### Environment Variables (`.env`)
The system is pre-configured, but you can customize:

```env
# AI Models
OPENAI_MODEL="gpt-4"                    # OpenAI model for responses
EMBEDDING_MODEL="text-embedding-ada-002" # Embedding model for vector search
TEMPERATURE=0.3                         # Response creativity (0.0-1.0)

# Database Generation
DEFAULT_BUSINESS_TYPE="ecommerce"       # Default business type
DEFAULT_COMPLEXITY="medium"             # Default complexity level
ENABLE_SAMPLE_DATA=True                 # Generate sample data by default

# Vector Store
VECTOR_STORE_TYPE="chroma"              # Vector database type
VECTOR_SEARCH_K=5                       # Number of search results

# External Research
ENABLE_EXTERNAL_RESEARCH=True           # Enable Tavily integration
TAVILY_MAX_RESULTS=5                    # Max external search results

# Server Configuration
DEFAULT_PORT=8002                       # Default server port
DEBUG_MODE=True                         # Enable debug logging
```

## 🧠 Technical Architecture Details

### AI Database Generation Pipeline
1. **Business Analysis**: LLM analyzes business description and requirements
2. **Schema Design**: Generates tables, relationships, and constraints
3. **Data Population**: Creates realistic, relational sample data
4. **Validation**: Ensures referential integrity and business logic
5. **Deployment**: Creates SQLite database ready for analysis

### RAG (Retrieval-Augmented Generation) System
- **Query Processing**: Natural language understanding with OpenAI
- **Context Retrieval**: Multi-source data aggregation (DB + Vector + External)
- **Response Generation**: Business-specific prompting with citations
- **Source Attribution**: Clear tracking of information sources

### Multi-Agent Coordination
- **Agent Orchestrator**: Routes queries to specialized agents
- **Data Analyst**: SQL generation and statistical analysis
- **Business Advisor**: Strategic insights and recommendations
- **Trend Analyst**: Temporal pattern analysis and forecasting
- **Report Generator**: Automated report creation and formatting

## � Supported Database Schemas

### Complexity Levels
- **Simple** (3-5 tables): Basic business operations
- **Medium** (6-12 tables): Standard business with relationships
- **Complex** (13-25 tables): Advanced business with detailed tracking
- **Enterprise** (25+ tables): Full-scale enterprise operations

### Example Generated Tables
- **E-commerce**: products, customers, orders, order_items, reviews, categories, inventory
- **Healthcare**: patients, appointments, doctors, medical_records, prescriptions, insurance
- **Finance**: accounts, transactions, clients, portfolios, investments, compliance_records
- **Technology**: projects, developers, deployments, bugs, features, analytics_events

## 🚀 Deployment Options

### Development Server
```powershell
# Standard development with auto-reload
py -m uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload

# Debug mode with verbose logging
py -m uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload --log-level debug
```

### Production Deployment
```powershell
# Production server with multiple workers
py -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --workers 4

# With custom settings
py -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --workers 4 --access-log
```

## 🤝 Project Vision & Educational Goals

This **AI Software Engineering Capstone Project** demonstrates advanced AI engineering concepts:

### 🎓 **Core Learning Objectives**
1. **RAG Systems**: Building production-ready Retrieval-Augmented Generation with multiple data sources
2. **AI Database Generation**: Using LLMs to create realistic, business-specific database schemas
3. **Multi-Agent Architecture**: Coordinating specialized AI agents for complex business workflows
4. **Vector Databases**: Implementing semantic search and similarity matching for business intelligence
5. **API Integration**: Combining multiple AI services (OpenAI, Tavily) into cohesive business solutions
6. **Full-Stack AI**: End-to-end AI application development from database to user interface

### 🏗️ **Engineering Best Practices**
- **Modular Architecture**: Clean separation of concerns across database, RAG, agents, and API layers
- **Configuration Management**: Environment-based configuration with secure API key handling
- **Error Handling**: Comprehensive logging and graceful degradation
- **Testing Strategy**: Automated testing for database generation and API endpoints
- **Documentation**: Extensive documentation and setup instructions
- **Scalability**: Multi-company support with isolated data environments

### 🌟 **Innovation Highlights**
- **Dynamic Business Modeling**: AI generates complete business databases from natural language descriptions
- **Context-Aware Intelligence**: RAG system that understands business context and provides relevant insights
- **Real-World Application**: Solves actual business intelligence challenges faced by modern companies
- **Multi-Source Integration**: Combines internal data analysis with external market research

## 🆘 Troubleshooting & Support

### Common Issues & Solutions

#### Database Generation Issues
```powershell
# Issue: Database generation fails
# Solution: Check OpenAI API connectivity
py -c "import openai; print('OpenAI connected')"

# Issue: Sample data inconsistencies  
# Solution: Re-generate with validation
py -m database.data_populator --validate
```

#### Server Connection Issues
```powershell
# Issue: Port already in use
# Solution: Try alternative ports
py -m uvicorn app.main:app --host 127.0.0.1 --port 8003 --reload

# Check which process is using the port
netstat -ano | findstr :8002
```

#### API Integration Issues
```powershell
# Issue: External research not working
# Solution: Verify Tavily API status
py -c "from rag.external_research import test_tavily; test_tavily()"

# Issue: Vector search errors
# Solution: Rebuild vector store
py -m rag.vector_store --rebuild
```

### Getting Help
- **Logs**: Check `server.log` for detailed error information
- **Debug Mode**: Run with `--log-level debug` for verbose output
- **Health Check**: Visit `http://127.0.0.1:8002/api/v1/health` to verify system status
- **Documentation**: See `SETUP_INSTRUCTIONS.md` for detailed setup guidance

## 🏆 Project Achievements & Impact

### 📈 **Technical Accomplishments**
- ✅ **11+ Business Types Supported**: From E-commerce to Healthcare, with custom options
- ✅ **4 Complexity Levels**: Simple to Enterprise-grade database schemas
- ✅ **Multi-Agent AI System**: Specialized agents for different business functions
- ✅ **Real-Time Intelligence**: Instant business insights from natural language queries
- ✅ **External Market Research**: Tavily API integration for industry analysis
- ✅ **Zero-Setup Experience**: Pre-configured with working API keys
- ✅ **Production-Ready**: Full error handling, logging, and scalability features

### 🎯 **Business Value Delivered**
- **Rapid Prototyping**: Generate complete business databases in minutes, not weeks
- **Data-Driven Decisions**: Transform raw business data into actionable insights
- **Market Intelligence**: Combine internal analytics with external market trends
- **Cost Efficiency**: Reduce database design and business intelligence development time by 90%
- **Accessibility**: Non-technical users can perform complex business analysis

### 🔬 **Innovation Impact**
This project pushes the boundaries of AI application in business intelligence by:
- Demonstrating how LLMs can generate realistic, production-ready database schemas
- Showing the power of RAG systems that combine multiple data sources intelligently
- Proving that AI agents can coordinate to solve complex business problems
- Creating a template for AI-driven business application development

---

## 📝 License & Academic Use

**Educational Project** - AI Software Engineering Capstone Course  
**Repository**: [github.com/wigginsjbah/AI-Software-Engineering-Capstone-Project](https://github.com/wigginsjbah/AI-Software-Engineering-Capstone-Project)  
**Purpose**: Demonstrates advanced AI engineering concepts in production-ready applications

---

*Built with ❤️ using OpenAI GPT-4, Tavily API, FastAPI, and modern AI engineering practices*
