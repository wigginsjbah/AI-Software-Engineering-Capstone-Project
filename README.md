# Business Intelligence RAG Chatbot

An AI-powered business intelligence chatbot that combines Retrieval-Augmented Generation (RAG) with real business data analysis. The system uses OpenAI for natural language processing and Tavily for external market research, providing comprehensive insights from your business database.

## 🚀 Features

- **Intelligent Query Processing**: Natural language queries converted to business insights
- **Multi-Source RAG**: Combines database queries, vector search, and external research
- **Business Data Analysis**: Analyzes products, customers, orders, reviews, and sales performance
- **External Market Research**: Uses Tavily API for industry and market context
- **Real-time Chat Interface**: Interactive web-based chat with business context
- **Multi-Agent Architecture**: Specialized agents for different types of analysis
- **SQL Query Generation**: Automatically generates and executes relevant database queries
- **Source Attribution**: Clear citations for all data sources and insights

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   RAG Engine    │
│   (HTML/JS)     │◄──►│   Backend       │◄──►│   (OpenAI)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Business      │    │   Vector Store  │
                       │   Database      │    │   (ChromaDB)    │
                       │   (SQLite)      │    └─────────────────┘
                       └─────────────────┘              │
                                                        ▼
                                                ┌─────────────────┐
                                                │   Tavily API    │
                                                │   (External)    │
                                                └─────────────────┘
```

## 📁 Project Structure

```
├── app/                    # Main application
│   ├── api/               # API endpoints
│   ├── core/              # Core business logic
│   └── models/            # Pydantic models
├── database/              # Database layer
├── rag/                   # RAG system components
├── agents/                # Multi-agent system
├── frontend/              # Web interface
├── config/                # Configuration
├── scripts/               # Utility scripts
├── data/                  # Data storage
├── utils/                 # Utility functions
└── guide/                 # Course materials
```

## 🛠️ Setup Instructions

### 1. Environment Setup

```powershell
# Install dependencies
pip install -r requirements.txt

# Verify your .env file has the required API keys
# OPENAI_API_KEY and TAVILY_API_KEY are already configured
```

### 2. Database Setup

```powershell
# Generate sample business data
python scripts/setup_database.py
```

This creates a SQLite database with:
- **Products**: 50 sample products across categories
- **Customers**: 200 customers with different segments
- **Orders**: 1,000 order records
- **Reviews**: 500 customer reviews with sentiment analysis
- **Sales Performance**: Monthly performance data by region

### 3. Run the Application

```powershell
# Start the FastAPI server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Access the Application

Open your browser and navigate to: `http://localhost:8000`

## 💬 Example Queries

Try these sample queries to explore the system:

### Data Analysis Queries
- "What are our top-performing products this quarter?"
- "Show me customer sentiment analysis for our electronics category"
- "Which customer segments have the highest lifetime value?"
- "What's our average order value by region?"

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

## 🔧 Configuration

Key configuration options in `.env`:

```env
# AI Models
OPENAI_MODEL="gpt-4"                    # OpenAI model for responses
EMBEDDING_MODEL="text-embedding-ada-002" # Embedding model for vector search
TEMPERATURE=0.3                         # Response creativity (0.0-1.0)

# Vector Store
VECTOR_STORE_TYPE="chroma"              # Vector database type
VECTOR_SEARCH_K=5                       # Number of search results

# External Research
ENABLE_EXTERNAL_RESEARCH=True           # Enable Tavily integration
TAVILY_MAX_RESULTS=5                    # Max external search results
```

## 🧠 System Components

### RAG Engine (`app/core/rag_engine.py`)
- Orchestrates the entire query processing pipeline
- Coordinates between database, vector store, and external APIs
- Manages conversation context and history

### Query Processor (`app/core/query_processor.py`)
- Analyzes user queries to determine intent and required data sources
- Classifies queries into types (data_query, trend_analysis, comparison, etc.)
- Uses OpenAI for sophisticated query understanding

### Context Builder (`app/core/context_builder.py`)
- Aggregates relevant context from multiple sources
- Performs database queries based on analyzed intent
- Searches vector store for relevant documents
- Fetches external market data via Tavily when needed

### Response Generator (`app/core/response_generator.py`)
- Generates comprehensive responses using OpenAI
- Incorporates data from all sources with proper attribution
- Provides confidence scores and source citations

## 📊 Database Schema

The system includes five main tables:

- **products**: Product catalog with categories, pricing, and descriptions
- **customers**: Customer profiles with segments and lifetime value
- **orders**: Transaction records with order details and status
- **reviews**: Customer feedback with ratings and sentiment analysis
- **sales_performance**: Monthly sales metrics by product and region

## 🔍 Advanced Features

### Multi-Agent Architecture
- **Data Analyst Agent**: Handles SQL queries and data extraction
- **Trend Analysis Agent**: Specializes in temporal pattern analysis
- **Business Advisor Agent**: Provides strategic business insights
- **Report Generator Agent**: Creates formatted business reports

### Vector Search
- Semantic search across business documents and data
- Embedding-based similarity matching
- Configurable similarity thresholds

### External Research Integration
- Tavily API integration for market research
- Industry trend analysis
- Competitive intelligence gathering

## 🚀 Deployment

### Development
```powershell
uvicorn app.main:app --reload --port 8000
```

### Production
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 🤝 Contributing

This is a capstone project demonstrating AI software engineering principles:

1. **RAG Systems**: Retrieval-Augmented Generation with multiple data sources
2. **Multi-Agent Architecture**: Specialized agents for different query types
3. **Vector Databases**: Semantic search and similarity matching
4. **API Integration**: External data sources and AI services
5. **Business Intelligence**: Real-world data analysis and insights

## 📝 License

Educational project for AI Software Engineering Capstone Course.

## 🆘 Troubleshooting

### Common Issues

1. **Database not found**: Run `python scripts/setup_database.py` first
2. **API key errors**: Verify your `.env` file has valid OPENAI_API_KEY and TAVILY_API_KEY
3. **Import errors**: Ensure all dependencies are installed: `pip install -r requirements.txt`
4. **ChromaDB issues**: The system falls back to simple vector store if ChromaDB fails

### Getting Help

Check the logs for detailed error messages. The system includes comprehensive logging at INFO level by default.
