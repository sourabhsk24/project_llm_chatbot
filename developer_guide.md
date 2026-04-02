# llm chatbot HR Chatbot - Technical Documentation

## 📋 Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Prerequisites](#prerequisites)
4. [Local Setup Guide](#local-setup-guide)
5. [MCP Server Setup](#mcp-server-setup)
6. [Core Components](#core-components)
7. [Query Flow Examples](#query-flow-examples)
8. [Database Schema](#database-schema)
9. [API Integrations](#api-integrations)
10. [Troubleshooting](#troubleshooting)
11. [Development Guidelines](#development-guidelines)

---

## 🎯 Overview

### What is llm chatbot HR Chatbot?

llm chatbot is an intelligent HR assistant that helps employees get information about:
- **Personal Data**: Leave balance, attendance, profile details
- **Company Information**: Holidays, work schedules, company details
- **Documentation**: Access to HR policies and guides through RAG (Retrieval Augmented Generation)
- **Employee Directory**: Search for colleagues and their details

### Key Features
- Natural language query understanding
- Real-time database queries for dynamic data
- Document-based RAG for static knowledge
- Multi-category query classification (4 types: DYNAMIC, STATIC, GREETING, DIRECTORY)
- Smart fallback mechanisms

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Query                            │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Query Classifier (OpenAI GPT-4o-mini)           │
│   Classifies into: DYNAMIC | STATIC | GREETING | DIRECTORY  │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   GREETING   │   │    STATIC    │   │   DYNAMIC    │
│   Handler    │   │  RAG Pipeline│   │Query Handler │
│   (Groq)     │   │   (Groq +    │   │  (OpenAI +   │
│              │   │   Chroma)    │   │   MCP SQL)   │
└──────────────┘   └──────────────┘   └──────┬───────┘
                                              │
                                              ▼
                                    ┌──────────────────┐
                                    │  Table Detection │
                                    │  (Fuzzy Match)   │
                                    └────────┬─────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │  SQL Generation  │
                                    │  (via MCP Tool)  │
                                    └────────┬─────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │ MySQL Database   │
                                    │  Execution       │
                                    └──────────────────┘
```

### Architecture Layers

| Layer | Component | Technology | Purpose |
|-------|-----------|------------|---------|
| **Interface** | Flask API | Flask 3.1.1 | HTTP endpoints |
| **Classification** | Query Classifier | OpenAI GPT-4o-mini | Route queries |
| **Dynamic Processing** | Query Handler | OpenAI + FastMCP | SQL generation |
| **Static Processing** | RAG Pipeline | Groq + Chroma | Document Q&A |
| **Data Access** | MCP Server | FastMCP + MySQL | Database queries |
| **Storage** | Vector DB | ChromaDB | Document embeddings |

---

## ✅ Prerequisites

### System Requirements

| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| **Python** | 3.8+ | 3.10 or 3.12 | Python 3.12 preferred |
| **Operating System** | Windows 10, Ubuntu 18.04, macOS 10.15 | Ubuntu 22.04, macOS 13+ | 64-bit required |
| **RAM** | 8GB | 16GB+ | More RAM helps with vector operations |
| **Storage** | 4GB free | 10GB+ free | For dependencies, models, and logs |
| **CPU** | 2 cores | 4+ cores | Better for concurrent requests |
| **MySQL** | 8.0+ | 8.0+ | Access to HR database required |

### Required Software

- Python 3.8+ (3.10 or 3.12 recommended)
- pip (Python package manager)
- virtualenv or venv
- Git (for version control)
- MySQL client tools
- Ollama (for local embeddings)
- curl or wget (for API testing)

### Required API Keys

1. **OpenAI API Key** (Required)
   - Purpose: Query classification and SQL generation
   - Get from: https://platform.openai.com/api-keys
   - Cost: ~$0.10-0.50 per 1000 queries (GPT-4o-mini)

2. **Groq API Key** (Required)
   - Purpose: Fast LLM responses (greeting & RAG)
   - Get from: https://console.groq.com/keys
   - Free tier: 30 requests/minute

3. **MySQL Database Access** (Required)
   - HR database with employee data
   - Permissions: SELECT queries only

---

## 🚀 Local Setup Guide

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd llm-chatbot-chatbot
ls -la  # Verify files (app.py, requirements.txt, etc.)
```

### Step 2: Create Virtual Environment

```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Verify installations
pip list | grep -E "langchain|flask|openai|fastmcp"
```

### Step 4: Install Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh  # macOS/Linux
# For Windows: https://ollama.ai/download

# Verify installation
ollama --version

# Pull embedding model (takes 2-3 minutes)
ollama pull nomic-embed-text

# Verify
ollama list  # Should show: nomic-embed-text
```

### Step 5: Environment Configuration

Create `.env` file in project root:

```bash
# API Keys (Required)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# MCP Server Configuration
MCP_URL=http://localhost:8000

# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASS=your_mysql_password
DB_NAME=llm_chatbot

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_PORT=5000

# Logging
LOG_LEVEL=INFO
```

**Secure the file:**
```bash
chmod 600 .env
echo ".env" >> .gitignore
```

### Step 6: Prepare RAG Documents

```bash
# Create data directory and add PDFs
mkdir -p data
cp /path/to/HR_Policy.pdf data/
cp /path/to/Leave_Guide.pdf data/
ls -lh data/  # Verify files
```

### Step 7: Build Vector Database

```bash
# Make sure Ollama is running
python3 -c "from rag_pipeline import build_or_load_vectorstore; build_or_load_vectorstore()"

# Verify creation
ls -lh rag_db/
```

### Step 8: Start Services (3 Terminals)

**Terminal 1 - Ollama:**
```bash
ollama serve
```

**Terminal 2 - MCP Server:**
```bash
cd llm-chatbot-chatbot
source venv/bin/activate
python3 mcp_server.py
# Should show: MCP Server running on http://0.0.0.0:8000
```

**Terminal 3 - Flask App:**
```bash
cd llm-chatbot-chatbot
source venv/bin/activate
python3 app.py
# Should show: Running on http://127.0.0.1:5000
```

### Step 9: Test the System

```bash
# Test 1: Greeting
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello", "user_id": 121, "org_id": 67}'

# Test 2: Dynamic query
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is my leave balance?", "user_id": 121, "org_id": 67}'

# Test 3: Static query
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I apply for leave?", "user_id": 121, "org_id": 67}'
```

---

## 🔌 MCP Server Setup

### What is MCP?

**MCP (Model Context Protocol)** is an open standard that enables AI models to securely interact with external data sources. In llm chatbot, MCP acts as a secure bridge between OpenAI and MySQL.

### Why Use MCP?

| Approach | Security | Control | Monitoring |
|----------|----------|---------|------------|
| **Direct DB** | ❌ OpenAI gets credentials | ❌ No validation | ❌ Hard to track |
| **MCP Bridge** | ✅ Credentials hidden | ✅ Query validation | ✅ Full logging |

### Create MCP Server File

```python
# mcp_server.py
from fastmcp import FastMCP
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "database": os.getenv("DB_NAME")
}

# Initialize MCP server
mcp = FastMCP("mysql-mcp-server")

@mcp.tool()
def execute_sql(query: str) -> dict:
    """Execute SQL query on MySQL and return results."""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        col_names = [desc[0] for desc in cursor.description]
        cursor.close()
        conn.close()
        return {"columns": col_names, "rows": rows}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_schema() -> dict:
    """Get database schema information."""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES;")
        tables = [t[0] for t in cursor.fetchall()]
        schema = {}
        for table in tables:
            cursor.execute(f"DESCRIBE {table};")
            schema[table] = [{"name": col[0], "type": col[1]} for col in cursor.fetchall()]
        cursor.close()
        conn.close()
        return schema
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000, stateless_http=True)
```

### MCP Configuration in Dynamic Query Handler

```python
# In dynamic_query_handler.py
tools = [
    {
        "type": "mcp",
        "server_label": "mysql-mcp-server",
        "server_url": os.getenv("MCP_URL"),  # http://localhost:8000
        "require_approval": "never"
    }
]

# Use in OpenAI call
response = gpt_client.responses.create(
    model="gpt-4o-mini",
    input=system_prompt,
    tools=tools  # OpenAI can now call MCP
)
```

### Test MCP Server

```bash
# Test 1: Health check
curl http://localhost:8000

# Test 2: Get schema
curl -X POST http://localhost:8000/tools/get_schema \
  -H "Content-Type: application/json" \
  -d '{}'

# Test 3: Execute SQL
curl -X POST http://localhost:8000/tools/execute_sql \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT COUNT(*) FROM llm_users"}'
```

### MCP Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 8000 in use | `lsof -i :8000` then `kill -9 <PID>` |
| DB connection failed | Check credentials in .env, verify MySQL is running |
| fastmcp not found | `pip install fastmcp==2.12.4` |

---

## 🔧 Core Components

### 1. Query Classifier (`query_classification.py`)

**Purpose**: Categorizes queries into 4 types using OpenAI GPT-4o-mini

**Classification Logic**:
- **DYNAMIC**: Real-time database queries (e.g., "my leave balance", "list employees")
- **STATIC**: Documentation queries (e.g., "how to apply leave", "user guide")
- **GREETING**: Conversational (e.g., "hi", "hello", "thanks")
- **DIRECTORY**: Person-specific (e.g., "who is Sai?")

**Configuration**:
```python
MODEL = "gpt-4o-mini"
TEMPERATURE = 0
MAX_TOKENS = 10
TIMEOUT = 30s
```

### 2. Dynamic Query Handler (`dynamic_query_handler.py`)

**Purpose**: Converts natural language to SQL queries

**Workflow**: `User Query → Table Detection → Schema Selection → SQL Generation → Execution`

**Table Detection Algorithm**:
1. Exact keyword match (e.g., "leave" → leave tables)
2. Fuzzy matching using RapidFuzz (score > 80)
3. Fallback: Use all available schemas

**Category Configuration** (`table_config.py`):
```python
categories = {
    "attendance": {
        "keywords": ["attendance", "clock in", "working hours"],
        "tables": {"llmchatbotmonthly_records": "schema_definition"}
    },
    "leave": {...},
    "holiday": {...}
}
```

### 3. RAG Pipeline (`rag_pipeline.py`)

**Purpose**: Answer questions from HR documentation

**Technology Stack**:
- **Embeddings**: Ollama nomic-embed-text (local)
- **Vector DB**: ChromaDB
- **LLM**: Groq Llama-3.1-8b-instant

**Workflow**: `Query → Embed → Search Vector DB → Retrieve Top K → LLM Generate`

**System Prompt**:
```
You are llm chatbot Assistant.
- Use ONLY the given context
- If info not available, say "Details are not available"
- Never mention "based on context"
- Keep answers concise and professional
```

### 4. Module Prompts (`modules_prompt/`)

Category-specific prompts for SQL generation:
```
modules_prompt/
├── attendance.py
├── leave.py
├── holiday.py
├── department.py
├── company.py
├── user_details.py
├── bank_details.py
├── work_week.py
├── directory/
│   ├── user_details.py
│   └── department.py
└── master.py
```

Each prompt includes:
- Table schemas with descriptions
- Mandatory filters (user_id, org_id)
- Example queries
- Business logic rules

### 5. Greeting Handler (`greeting_handler.py`)

Handles casual conversations using Groq:
- Max 50 tokens
- Temperature: 0.1
- Fast responses

### 6. MCP Server (`mcp_server.py`)

Bridge between OpenAI and MySQL:
- Exposes `execute_sql` and `get_schema` tools
- Runs on port 8000
- Stateless HTTP transport

---

## 🔄 Query Flow Examples

### Example 1: Dynamic Query (Leave Balance)

```
User: "What is my leave balance?"
  ↓
[Query Classifier] → DYNAMIC
  ↓
[Table Detection] → "leave" category
  ↓
[Schema Selection] → llm_assigned_leave_details
  ↓
[OpenAI + MCP] → SQL: SELECT SUM(leave_balance) FROM llm_assigned_leave_details WHERE user_id = 121
  ↓
[MySQL Execution] → Returns: 15.5
  ↓
[Response] → "Your current leave balance is 15.5 days"
```

### Example 2: Static Query (Documentation)

```
User: "How do I apply for leave?"
  ↓
[Query Classifier] → STATIC
  ↓
[RAG Pipeline] → Embeds query
  ↓
[Vector Search] → Finds relevant chunks from Leave_Policy.pdf
  ↓
[Groq LLM] → Generates natural answer
  ↓
[Response] → "To apply for leave in llm chatbot, follow these steps..."
```

### Example 3: Directory Query (Colleague Search)

```
User: "Who is Sai?"
  ↓
[Query Classifier] → DIRECTORY
  ↓
[Directory Handler] → Uses directory_personal schema
  ↓
[SQL Generation] → SELECT u.first_name, u.email FROM llm_users u WHERE u.first_name = 'Sai'
  ↓
[Response] → "Sai is a developer. Email: sai@company.com"
```

---

## 🗄️ Database Schema

### Core Tables

**llm_users** (Master Table):
```sql
id, org_id, first_name, last_name, email, employee_id, 
department_Id, designation_Id, subdepartment_Id
```

**llmchatbotmonthly_records** (Attendance):
```sql
id, user_id, org_id, date, first_clock_in, last_clock_out, 
total_minutes, status (Present/Absent/Half Day)
```

**llm_assigned_leave_details** (Leave Balance):
```sql
id, user_id, rule_id, credited_leaves, applied_leaves, 
leave_balance, carry_forward
```

**llm_leave_applications** (Leave History):
```sql
id, user_id, rule_id, start_date, end_date, total_leaves, 
status (Pending/Approved/Rejected), reason
```

**holiday_calender**:
```sql
id, org_id, holiday_description, date
```

---

## 🔌 API Integrations

### 1. OpenAI API

- **Usage**: Query classification, SQL generation
- **Model**: gpt-4o-mini
- **Rate Limits**: 10,000 requests/day (free tier)

```python
gpt_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
response = gpt_client.responses.create(
    model="gpt-4o-mini",
    input=system_prompt,
    tools=[{"type": "mcp", "server_url": "http://localhost:8000"}]
)
```

### 2. Groq API

- **Usage**: Greeting responses, RAG answers
- **Model**: llama-3.1-8b-instant
- **Rate Limits**: 30 requests/minute (free tier)

```python
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
response = session.post(GROQ_API_URL, json={
    "model": "llama-3.1-8b-instant",
    "messages": [...],
    "temperature": 0.2
})
```

### 3. Ollama (Local)

- **Usage**: Document embeddings
- **Model**: nomic-embed-text
- **Benefits**: Privacy, no API costs, no rate limits

```python
from langchain_ollama import OllamaEmbeddings
embeddings = OllamaEmbeddings(model="nomic-embed-text")
```

---

## 🐛 Troubleshooting

| Issue | Symptoms | Solution |
|-------|----------|----------|
| **MCP Connection Failed** | Connection refused to :8000 | `python3 mcp_server.py` |
| **Ollama Model Not Found** | Model 'nomic-embed-text' not found | `ollama pull nomic-embed-text` |
| **ChromaDB Lock Error** | Database is locked | `rm -rf rag_db/` and rebuild |
| **OpenAI Rate Limit** | Error 429 | Wait 1 minute or upgrade plan |
| **MySQL Connection Error** | Access denied | Verify credentials in .env |

---

## 👨‍💻 Development Guidelines

### Adding a New Query Category

**Step 1**: Update `table_config.py`
```python
categories = {
    "payroll": {
        "keywords": ["salary", "payslip", "ctc"],
        "tables": {"llm_payroll": "llm_payroll(id, user_id, basic_pay, ...)"}
    }
}
```

**Step 2**: Create prompt file
```python
# modules_prompt/payroll.py
def payroll_system_prompt():
    return """SQL expert for llm chatbot payroll..."""
```

**Step 3**: Register in `dynamic_query_handler.py`
```python
from modules_prompt.payroll import payroll_system_prompt
functions_dict = {"payroll": payroll_system_prompt()}
```

### Adding New RAG Documents

```bash
cp New_Policy.pdf data/
python3 -c "from rag_pipeline import build_or_load_vectorstore; build_or_load_vectorstore()"
```

---

## 📚 Quick Reference

### File Structure
```
llm-chatbot-chatbot/
├── app.py                          # Main Flask app
├── mcp_server.py                   # MCP server
├── query_classification.py         # Query classifier
├── dynamic_query_handler.py        # SQL generation
├── rag_pipeline.py                 # RAG for docs
├── greeting_handler.py             # Greetings
├── table_config.py                 # Schema definitions
├── requirements.txt                # Dependencies
├── .env                            # Environment variables
├── modules_prompt/                 # Category prompts
├── data/                           # PDF documents
├── rag_db/                         # Vector storage
└── venv/                           # Virtual environment
```

### Essential Commands

```bash
# Start services (3 terminals)
ollama serve                        # Terminal 1
python3 mcp_server.py              # Terminal 2
python3 app.py                      # Terminal 3

# Health checks
curl http://localhost:8000          # MCP server
curl http://localhost:5000/health   # Flask app
ollama list                         # Ollama models
```

### Component Overview

| Component | Technology | Port | Status Check |
|-----------|-----------|------|--------------|
| Flask App | Flask 3.1.1 | 5000 | `curl localhost:5000/health` |
| MCP Server | FastMCP 2.12.4 | 8000 | `curl localhost:8000` |
| Ollama | Ollama | 11434 | `ollama list` |
| MySQL | MySQL 8.0+ | 3306 | `mysql -e "SELECT 1;"` |

---

## 📖 External References

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [LangChain Docs](https://python.langchain.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Groq Documentation](https://console.groq.com/docs)
