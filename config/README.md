# Config Folder - The Settings and Rules

## What This Folder Does (Simple Explanation)
This folder is like the control panel for your entire chatbot system. It contains all the settings, rules, and instructions that tell the application how to behave. Think of it like the settings on your phone - it determines things like which AI model to use, how the system should respond to different types of questions, what the API keys are, and how various components should work together. It's the configuration center that makes everything else work properly.

## Technical Description
The `config/` directory contains application configuration management, system settings, and prompt engineering for the business intelligence RAG system. It implements the configuration pattern for centralized settings management and prompt templates.

### Structure:
- **`settings.py`** - Application configuration using Pydantic Settings with environment variable support
- **`prompts.py`** - System prompts and prompt templates for different agent types and scenarios
- **`agent_configs.py`** - Agent-specific configuration and behavior parameters
- **`__init__.py`** - Package initialization and configuration loading

### Key Technical Components:
1. **Environment Configuration**: Centralized management of environment variables and secrets
2. **Model Parameters**: AI model settings, temperature, token limits, and response parameters
3. **System Prompts**: Carefully crafted prompts that define agent behavior and response style
4. **API Configuration**: External service configurations (OpenAI, Tavily, database connections)
5. **Feature Flags**: Toggles for enabling/disabling system features and experimental functionality

## What's Configured Here:

### 🔑 **API Keys & Secrets**
- OpenAI API credentials for AI processing
- Tavily API keys for external research
- Database connection strings
- Security tokens and authentication settings

### 🤖 **AI Model Settings**
- Which OpenAI model to use (GPT-4, GPT-3.5-turbo, etc.)
- Response creativity level (temperature setting)
- Maximum response length (token limits)
- Embedding model for vector search

### 💬 **System Prompts**
- **Data Analyst Prompt**: Instructions for handling data queries
- **Business Advisor Prompt**: Guidelines for strategic insights
- **Report Generator Prompt**: Templates for creating formatted reports
- **General Assistant Prompt**: Conversational behavior rules

### ⚙️ **System Behavior**
- How many search results to return
- Confidence thresholds for answers
- Rate limiting and security settings
- Logging levels and debug modes

### 🎯 **Feature Controls**
- Enable/disable external research
- Vector search parameters
- Chat history limits
- Error handling preferences

## Example Settings:

```python
# AI Model Configuration
OPENAI_MODEL = "gpt-4"              # Use GPT-4 for responses
TEMPERATURE = 0.3                   # Low creativity, high accuracy
MAX_TOKENS = 1500                   # Comprehensive but concise responses

# Search Configuration
VECTOR_SEARCH_K = 5                 # Return top 5 relevant documents
SIMILARITY_THRESHOLD = 0.7          # High relevance requirement

# External Research
ENABLE_EXTERNAL_RESEARCH = True     # Use Tavily for market data
TAVILY_MAX_RESULTS = 5              # Limit external sources
```

## Why This Matters:
- **Consistency**: All parts of the system follow the same rules
- **Flexibility**: Easy to adjust behavior without changing code
- **Security**: Keeps sensitive information like API keys organized
- **Customization**: Can fine-tune the chatbot's personality and accuracy
- **Maintenance**: One place to update settings for the entire system

This folder is like the "DNA" of your chatbot - it defines how intelligent, accurate, and helpful your system will be!