# LocaLense V2 - Project Structure & Working Documentation

**Last Updated:** December 3, 2025  
**Project Name:** Vantage (formerly LocaLense)  
**Type:** AI-Powered Semantic Document Search & Chat Assistant

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Complete File Structure](#complete-file-structure)
3. [Architecture Overview](#architecture-overview)
4. [How The System Works](#how-the-system-works)
5. [Backend Components](#backend-components)
6. [Frontend Components](#frontend-components)
7. [Data Flow](#data-flow)
8. [Configuration](#configuration)
9. [Database Schema](#database-schema)
10. [Development Workflow](#development-workflow)

---

## 🎯 Project Overview

**Vantage** is a sophisticated AI-powered document search and management system that combines semantic search, RAG (Retrieval-Augmented Generation), and multi-agent conversational AI to help users find and interact with their documents through natural language.

### Core Technologies
- **Frontend:** React 18 + Vite
- **Backend:** FastAPI (Python)
- **Vector Database:** OpenSearch
- **LLM:** Ollama (qwen2.5:7b for text, qwen2.5vl for vision)
- **Embeddings:** nomic-embed-text (768 dimensions)
- **Storage:** SQLite (users, conversations, memory)
- **File Monitoring:** Watchdog

### Key Features
✅ Password-protected multi-user authentication  
✅ Document indexing (PDF, DOCX, XLSX, images, text)  
✅ Semantic + hybrid search (vector + BM25)  
✅ Conversational UI with SSE streaming  
✅ Document attachment for focused queries  
✅ Real-time file watching for auto-indexing  
✅ Multi-agent system (orchestrator, search, analysis, clarification)  
✅ Memory system (session, user profile, procedural)  
✅ Dark mode UI  

---

## 📁 Complete File Structure

```
LocaLense_V2/
│
├── 📄 Root Configuration Files
│   ├── config.yaml                    # Main configuration (Ollama, OpenSearch, agents, memory)
│   ├── requirements.txt               # Python dependencies
│   ├── docker-compose.yml             # Docker setup for OpenSearch
│   ├── run.bat                        # Windows startup script
│   ├── run.sh                         # Linux/Mac startup script
│   ├── app.py                         # Legacy entry point (still functional)
│   ├── locallens_conversations.db     # SQLite DB for conversations
│   ├── locallens_memory.db            # SQLite DB for memory system
│   └── locallens_users.json           # User authentication data
│
├── 📖 Documentation
│   ├── README.md                      # Main project documentation
│   ├── ARCHITECTURE.md                # Detailed system architecture
│   ├── QUICKSTART.md                  # Quick setup guide
│   ├── LINKEDIN_POST.md               # Marketing content
│   └── working.md                     # This file (project structure)
│
├── 🛠️ Utility Scripts
│   ├── delete_index.py                # Delete OpenSearch index
│   ├── init_memory.py                 # Initialize memory database
│   ├── test_auth_endpoint.py          # Test authentication
│   ├── test_auth_endpoint_urllib.py   # Auth test (urllib)
│   ├── test_dual_models.py            # Test dual model loading
│   ├── test_ollama.py                 # Test Ollama connection
│   ├── test_timeout.py                # Test timeout handling
│   └── test_timeout2.py               # Additional timeout tests
│
├── 🔙 backend/                        # Backend API & Services
│   │
│   ├── 📄 Core Backend Files
│   │   ├── __init__.py                # Package initialization
│   │   ├── api.py                     # Main FastAPI application (60KB)
│   │   ├── auth.py                    # User authentication & session management
│   │   ├── auth_endpoints.py          # Authentication API routes
│   │   ├── ingestion.py               # Document processing pipeline (27KB)
│   │   ├── opensearch_client.py       # Vector search client (14KB)
│   │   ├── reranker.py                # Cross-encoder reranking (7.5KB)
│   │   ├── watcher.py                 # File system monitoring (8.7KB)
│   │   ├── watcher_endpoints.py       # File watcher API routes
│   │   ├── upload_endpoints.py        # File upload handling
│   │   ├── index_endpoint.py          # Document indexing routes
│   │   ├── a2a_agent.py               # Agent-to-Agent communication (22KB)
│   │   ├── mcp_tools.py               # MCP server tools (7.9KB)
│   │   └── streaming_steps.py         # SSE streaming utilities
│   │
│   ├── 🤖 agents/                     # AI Agent System
│   │   ├── __init__.py
│   │   ├── query_classifier.py        # Classifies user intent (16.6KB)
│   │   ├── analysis_agent.py          # Document analysis & summarization (9.9KB)
│   │   ├── clarification_agent.py     # Asks clarifying questions (9.2KB)
│   │   ├── critic_agent.py            # Quality control & validation (8.7KB)
│   │   ├── explanation_agent.py       # Explains search results (4.1KB)
│   │   └── summarization_agent.py     # Document summarization (4.6KB)
│   │
│   ├── 🧠 memory/                     # Memory System
│   │   ├── __init__.py
│   │   ├── memory_manager.py          # Central memory coordinator (11KB)
│   │   ├── conversation_manager.py    # Conversation history (12.5KB)
│   │   ├── session_memory.py          # Short-term session memory (8.9KB)
│   │   ├── user_profile.py            # Long-term user profiles (12.1KB)
│   │   └── procedural_memory.py       # Learning & patterns (8.2KB)
│   │
│   ├── 🎯 orchestration/              # Agent Coordination
│   │   ├── __init__.py
│   │   └── orchestrator.py            # Main agent orchestrator (19.7KB)
│   │
│   └── 🔧 utils/                      # Utility Functions
│       ├── llm_utils.py               # LLM interaction utilities (10KB)
│       └── model_manager.py           # Model loading & management (7.1KB)
│
├── 💻 frontend/                       # React Frontend
│   │
│   ├── 📦 Configuration
│   │   ├── package.json               # NPM dependencies
│   │   ├── package-lock.json          # Dependency lockfile
│   │   ├── vite.config.js             # Vite build configuration
│   │   ├── index.html                 # Main HTML entry point
│   │   ├── setup.bat                  # Frontend setup script
│   │   └── README.md                  # Frontend documentation
│   │
│   ├── 📂 src/                        # Source Code
│   │   ├── main.jsx                   # React entry point
│   │   ├── App.jsx                    # Root component (2.9KB)
│   │   ├── index.css                  # Global styles
│   │   │
│   │   ├── 🧩 components/             # React Components
│   │   │   ├── OnboardingWizard.jsx   # First-time setup (18.3KB)
│   │   │   ├── OnboardingWizard.css
│   │   │   ├── OnboardingWizard-watcher.css
│   │   │   ├── ChatInterface.jsx      # Main chat UI (13.2KB)
│   │   │   ├── ChatInterface.css
│   │   │   ├── ChatInterface-buttons.css
│   │   │   ├── ChatSidebar.jsx        # Conversation sidebar (5.8KB)
│   │   │   ├── ChatSidebar.css
│   │   │   ├── DocumentSelector.jsx   # Attach documents (8.7KB)
│   │   │   ├── DocumentSelector.css
│   │   │   ├── SettingsPanel.jsx      # System settings (18.3KB)
│   │   │   ├── SettingsPanel.css
│   │   │   ├── SettingsPanel-additions.css
│   │   │   ├── IndexingProgress.jsx   # Real-time indexing indicator (4.4KB)
│   │   │   ├── IndexingProgress.css
│   │   │   ├── LoginSettings.jsx      # Login/auth controls (6.8KB)
│   │   │   ├── LoginSettings.css
│   │   │   └── index.js               # Component exports
│   │   │
│   │   ├── 🪝 hooks/                  # Custom React Hooks
│   │   │   └── (React custom hooks)
│   │   │
│   │   └── 🎨 styles/                 # Additional Stylesheets
│   │       └── (Additional CSS files)
│   │
│   └── 📄 components/                 # Standalone Components
│       └── ConversationExporter.jsx   # Export conversation feature
│
└── 📂 Other Files
    ├── frontend_sse_example.jsx       # SSE implementation example
    ├── frontend_sse_vanilla.js        # Vanilla JS SSE example
    └── chat.html                      # Standalone chat interface
```

---

## 🏗️ Architecture Overview

### System Layers

```
┌──────────────────────────────────────────────────────┐
│         FRONTEND (React + Vite)                      │
│  ┌──────────────────────────────────────────────┐   │
│  │ OnboardingWizard → ChatInterface → Settings  │   │
│  └──────────────────────────────────────────────┘   │
└────────────────────┬─────────────────────────────────┘
                     │ HTTP REST + SSE
┌────────────────────┴─────────────────────────────────┐
│         BACKEND (FastAPI)                            │
│  ┌─────────────────────────────────────────────┐    │
│  │      Enhanced Orchestrator                  │    │
│  │  ┌──────────┬──────────┬──────────────┐    │    │
│  │  │ Query    │ Search   │ Analysis     │    │    │
│  │  │Classifier│  Agent   │  Agent       │    │    │
│  │  └──────────┴──────────┴──────────────┘    │    │
│  └─────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────┐    │
│  │      Memory System (Session + User)         │    │
│  └─────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────┐    │
│  │      Ingestion Pipeline                     │    │
│  │  File → Extract → Chunk → Embed → Index    │    │
│  └─────────────────────────────────────────────┘    │
└──────┬──────────┬──────────┬──────────┬─────────────┘
       │          │          │          │
┌──────┴───┐ ┌───┴────┐ ┌───┴────┐ ┌──┴─────┐
│OpenSearch│ │ Ollama │ │ SQLite │ │Watchdog│
│ Vector   │ │  LLM   │ │Memory/ │ │  File  │
│   DB     │ │Embedder│ │ Users  │ │Monitor │
└──────────┘ └────────┘ └────────┘ └────────┘
```

---

## ⚙️ How The System Works

### 1️⃣ User Onboarding Flow

```
User opens app (localhost:5173)
  ↓
Check if logged in (localStorage.session_token)
  ↓
NO → Show OnboardingWizard
  ├─ Step 1: Choose Sign Up / Sign In
  ├─ Step 2: Enter credentials
  │   POST /auth/register or /auth/login
  │   Returns session_token
  ├─ Step 3: Index documents
  │   Option A: Enter folder path → POST /index/directory
  │   Option B: Upload files → POST /upload-batch
  │   Returns task_id
  ├─ Step 4: Enable file watcher (optional)
  │   POST /watcher/enable
  └─ Complete → Save session_token to localStorage
  ↓
YES → Show ChatInterface
```

### 2️⃣ Document Indexing Flow

```
User provides documents (path or upload)
  ↓
Backend receives files
  ↓
For each file:
  ├─ 1. Detect file type (PDF, DOCX, XLSX, image, text)
  ├─ 2. Extract text
  │   PDF → PyPDF2 + pdfplumber
  │   DOCX → python-docx
  │   XLSX/CSV → pandas
  │   Image → pytesseract OCR
  │   Text → direct read
  ├─ 3. Split into chunks (800 tokens, 200 overlap)
  ├─ 4. Generate embeddings (nomic-embed-text via Ollama)
  │   Creates 768-dimensional vectors
  ├─ 5. Index to OpenSearch
  │   Vector field (knn_vector) + BM25 text field
  │   Store metadata: filename, path, user_id, timestamp
  └─ 6. Update progress status (task_id)
  ↓
Return task_id
  ↓
Frontend polls /index/status/{task_id} every 1 second
  ↓
Display real-time progress (IndexingProgress component)
```

### 3️⃣ Search & Conversation Flow

```
User types query in ChatInterface
  ↓
POST /search/enhanced
  ↓
Orchestrator receives query
  ↓
1. QUERY CLASSIFICATION (query_classifier.py)
   - Analyze intent
   - Categories: SEARCH, ANALYSIS, CLARIFICATION, GENERAL
   - Confidence scoring
  ↓
2. AGENT ROUTING
   ├─ SEARCH → Search Agent
   │   ├─ Generate query embedding
   │   ├─ Vector search (cosine similarity, top 50)
   │   ├─ BM25 keyword search (top 50)
   │   ├─ Hybrid fusion (RRF - Reciprocal Rank Fusion)
   │   └─ Rerank with cross-encoder (top 5)
   │
   ├─ ANALYSIS → Analysis Agent
   │   ├─ Summarize documents
   │   ├─ Extract key points
   │   └─ Topic classification
   │
   ├─ CLARIFICATION → Clarification Agent
   │   ├─ Detect ambiguity
   │   └─ Generate clarifying questions
   │
   └─ GENERAL → Direct LLM response
  ↓
3. MEMORY INTEGRATION
   ├─ Load conversation history (last 10 turns)
   ├─ Check attached documents
   ├─ Load user profile preferences
   └─ Update session memory
  ↓
4. RESPONSE GENERATION
   ├─ Combine agent outputs
   ├─ Format with citations
   ├─ Stream via SSE (thinking steps)
   └─ Save to conversation history
  ↓
5. FRONTEND DISPLAY
   ├─ Show search results with metadata
   ├─ Display LLM response
   ├─ Enable "Attach" and "Open" buttons
   └─ Update conversation sidebar
```

### 4️⃣ File Watcher Flow

```
User enables file watcher
  ↓
POST /watcher/enable with directory path
  ↓
Backend starts Watchdog observer
  ↓
Monitor file system events:
  ├─ on_created → New file added
  ├─ on_modified → File changed
  ├─ on_deleted → File removed (delete from index)
  └─ on_moved → File renamed (update index)
  ↓
Debounce events (3 seconds)
  ↓
Auto-index new/modified files
  ↓
Update user's document index in background
```

---

## 🔙 Backend Components

### Core Backend Files

| File | Purpose | Key Functions |
|------|---------|---------------|
| `api.py` | Main FastAPI app | All REST endpoints, CORS, SSE streaming, startup hooks |
| `auth.py` | Authentication | `register_user()`, `authenticate()`, `verify_session()` |
| `auth_endpoints.py` | Auth routes | `/auth/register`, `/auth/login`, `/auth/verify` |
| `ingestion.py` | Document processing | `process_file()`, `extract_text()`, `chunk_text()`, `embed()` |
| `opensearch_client.py` | Vector search | `create_index()`, `search()`, `hybrid_search()`, `delete()` |
| `reranker.py` | Result reranking | Cross-encoder scoring, relevance boosting |
| `watcher.py` | File monitoring | Watchdog integration, debouncing, event handling |
| `upload_endpoints.py` | File uploads | `/upload-batch` multipart handling |
| `index_endpoint.py` | Indexing routes | `/index/directory`, `/index/status/{task_id}` |

### Agent System (`backend/agents/`)

| Agent | File | Purpose | Input | Output |
|-------|------|---------|-------|--------|
| **Query Classifier** | `query_classifier.py` | Determines user intent | Query text | Intent category + confidence |
| **Analysis Agent** | `analysis_agent.py` | Document analysis | Documents | Summary, key points, entities |
| **Clarification Agent** | `clarification_agent.py` | Handles ambiguity | Ambiguous query | Clarifying questions |
| **Critic Agent** | `critic_agent.py` | Quality control | Agent responses | Quality score, improvements |
| **Explanation Agent** | `explanation_agent.py` | Explains results | Search results | User-friendly explanations |
| **Summarization Agent** | `summarization_agent.py` | Summarizes docs | Long documents | Concise summaries |

### Memory System (`backend/memory/`)

| Component | File | Storage | Purpose |
|-----------|------|---------|---------|
| **Memory Manager** | `memory_manager.py` | Coordinator | Central hub for all memory operations |
| **Session Memory** | `session_memory.py` | Redis/In-memory | Short-term conversation context (last 10 turns) |
| **User Profile** | `user_profile.py` | SQLite | Long-term preferences, search history |
| **Procedural Memory** | `procedural_memory.py` | Cache | Learning patterns, common queries |
| **Conversation Manager** | `conversation_manager.py` | SQLite | Full conversation history persistence |

### Orchestration (`backend/orchestration/`)

| Component | Purpose |
|-----------|---------|
| `orchestrator.py` | Routes queries to appropriate agents, coordinates multi-agent workflows, synthesizes responses |

### Utilities (`backend/utils/`)

| File | Purpose |
|------|---------|
| `llm_utils.py` | Helper functions for Ollama API calls, prompt formatting, streaming |
| `model_manager.py` | Dynamic model loading/unloading, GPU management |

---

## 💻 Frontend Components

### React Components (`frontend/src/components/`)

| Component | File | Purpose | Key Features |
|-----------|------|---------|--------------|
| **OnboardingWizard** | `OnboardingWizard.jsx` (18KB) | First-time setup | Sign up/in, document indexing, file watcher setup |
| **ChatInterface** | `ChatInterface.jsx` (13KB) | Main chat UI | Semantic search, streaming responses, result display |
| **ChatSidebar** | `ChatSidebar.jsx` (5.8KB) | Conversation list | Switch conversations, create new, delete |
| **DocumentSelector** | `DocumentSelector.jsx` (8.7KB) | Attach documents | Select docs for focused queries, visual doc list |
| **SettingsPanel** | `SettingsPanel.jsx` (18KB) | System management | Indexing tab, system health, settings |
| **IndexingProgress** | `IndexingProgress.jsx` (4.4KB) | Progress indicator | Non-blocking, real-time polling, collapsible |
| **LoginSettings** | `LoginSettings.jsx` (6.8KB) | Auth controls | Password change, logout |

### Component Hierarchy

```
App.jsx (root)
  ├─ indexingTaskId (global state)
  ├─ session_token (localStorage)
  │
  ├─── OnboardingWizard (if !logged in)
  │      ├─ Step 1: Sign Up / Sign In
  │      ├─ Step 2: Credentials
  │      ├─ Step 3: Index Documents
  │      └─ Step 4: File Watcher
  │
  └─── ChatInterface (if logged in)
         ├─ ChatSidebar (left panel)
         ├─ Search Input + Results (center)
         ├─ DocumentSelector (attached docs)
         ├─ SettingsPanel (gear icon)
         └─ IndexingProgress (bottom-right if taskId exists)
```

---

## 🔄 Data Flow

### Authentication Data Flow

```
Frontend                Backend               Storage
────────                ───────               ───────
[Sign Up Form]
  user_id + password
      │
      ├──POST /auth/register──→ auth_endpoints.py
      │                              │
      │                              ├─ Hash password (SHA-256)
      │                              ├─ Generate session token
      │                              └─ Save to locallens_users.json
      │                              
      ←──{session_token}─────────────┘
      │
      └─ Save to localStorage
```

### Search Data Flow

```
Frontend                 Backend                    OpenSearch      Ollama
────────                 ───────                    ──────────      ──────
[Search Query]
  "find my resume"
      │
      ├──POST /search/enhanced──→ api.py
      │                             │
      │                             ├─ orchestrator.py
      │                             │    ├─ query_classifier.py
      │                             │    └─ Determine: SEARCH
      │                             │
      │                             ├─ Generate embedding──────────→ nomic-embed-text
      │                             │                                     │
      │                             │    ←──[768-dim vector]──────────────┘
      │                             │
      │                             ├─ Vector search────────→ OpenSearch
      │                             │                            (cosine similarity)
      │                             │    ←──[top 50 results]─────┘
      │                             │
      │                             ├─ BM25 search──────────→ OpenSearch
      │                             │                            (keyword)
      │                             │    ←──[top 50 results]─────┘
      │                             │
      │                             ├─ Hybrid fusion (RRF)
      │                             │
      │                             ├─ Rerank────────────────────→ cross-encoder
      │                             │                                     │
      │                             │    ←──[top 5 results]───────────────┘
      │                             │
      │                             └─ Format response
      │
      ←──{results + metadata}───────┘
      │
      └─ Display in ChatInterface
```

### Indexing Data Flow

```
Frontend                 Backend                    OpenSearch      Ollama
────────                 ───────                    ──────────      ──────
[Upload Files]
  file1.pdf, file2.docx
      │
      ├──POST /upload-batch (multipart)──→ upload_endpoints.py
      │                                         │
      │                                         ├─ Save to temp dir
      │                                         ├─ Create task_id
      │                                         └─ Start ingestion
      │
      ←──{task_id}──────────────────────────────┘
      │
      ├─ Poll /index/status/{task_id} (1s interval)
      │
      │                                    ingestion.py
      │                                         │
      │                                    For each file:
      │                                         ├─ Extract text
      │                                         ├─ Split into chunks (800 tokens)
      │                                         ├─ Generate embeddings───→ nomic-embed-text
      │                                         │                              │
      │                                         │   ←──[vectors[]]─────────────┘
      │                                         │
      │                                         └─ Index documents────→ OpenSearch
      │                                                                     │
      │                                                  ←──{success}───────┘
      │
      ←──{processed: 2, total: 2}────────────────┘
```

---

## ⚙️ Configuration

### `config.yaml` Structure

```yaml
# LLM Models
ollama:
  base_url: "http://localhost:11434"
  text_model: "qwen2.5:7b"
  vision_model: "qwen2.5vl:latest"

# Vector Database
opensearch:
  host: "localhost"
  port: 9200
  index_name: "locallens_index"

# Embedding Model
models:
  embedding:
    name: "nomic-embed-text"
    dimension: 768

# Search Settings
search:
  hybrid: true
  vector_weight: 0.7
  bm25_weight: 0.3
  recall_top_k: 50
  rerank_top_k: 5

# Agents
agents:
  classifier: enabled
  clarification: enabled
  analysis: enabled
  summarization: enabled
  critic: enabled

# Memory System
memory:
  session:
    backend: "redis"  # or "memory"
    window_size: 10
  user_profile:
    backend: "sqlite"
    database_url: "sqlite+aiosqlite:///locallens_memory.db"
  procedural:
    enable_learning: true

# Ingestion
ingestion:
  chunk_size: 800
  chunk_overlap: 200
  max_workers: 1

# File Watcher
watcher:
  debounce_seconds: 3
  supported_extensions: [".pdf", ".docx", ".txt", ".xlsx", ".png", ".jpg"]
```

---

## 🗄️ Database Schema

### SQLite Databases

#### **locallens_conversations.db**

```sql
-- Conversations table
CREATE TABLE conversations (
    conversation_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Messages table
CREATE TABLE messages (
    message_id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    results JSON,        -- Search results if applicable
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
);

-- Attached documents
CREATE TABLE attached_documents (
    conversation_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    filename TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (conversation_id, document_id)
);
```

#### **locallens_memory.db**

```sql
-- User profiles
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    profile JSON,        -- Preferences, settings
    search_history JSON, -- Recent searches
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Session memory
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    context JSON,        -- Conversation context
    expires_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Procedural memory (learning)
CREATE TABLE patterns (
    pattern_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    query_pattern TEXT,
    frequency INTEGER DEFAULT 1,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### OpenSearch Index Schema

```json
{
  "mappings": {
    "properties": {
      "text": {
        "type": "text",
        "analyzer": "standard"
      },
      "embedding": {
        "type": "knn_vector",
        "dimension": 768,
        "method": {
          "name": "hnsw",
          "space_type": "l2",
          "engine": "nmslib",
          "parameters": {
            "ef_construction": 128,
            "m": 24
          }
        }
      },
      "filename": {"type": "keyword"},
      "file_path": {"type": "keyword"},
      "file_type": {"type": "keyword"},
      "file_size": {"type": "long"},
      "user_id": {"type": "keyword"},
      "chunk_index": {"type": "integer"},
      "timestamp": {"type": "date"},
      "metadata": {"type": "object"}
    }
  }
}
```

### User Authentication Storage (`locallens_users.json`)

```json
{
  "users": {
    "john_doe": {
      "password_hash": "sha256_hash_here",
      "created_at": "2025-12-01T10:30:00Z",
      "sessions": {
        "session_token_abc123": {
          "created_at": "2025-12-03T03:00:00Z",
          "expires_at": "2025-12-04T03:00:00Z"
        }
      }
    }
  }
}
```

---

## 🔧 Development Workflow

### Starting the Application

#### Prerequisites
1. **OpenSearch** running on port 9200
2. **Ollama** running on port 11434
3. Models pulled: `nomic-embed-text`, `qwen2.5:7b`

#### Option 1: Run Scripts
```bash
# Windows
run.bat

# Linux/Mac
chmod +x run.sh
./run.sh
```

#### Option 2: Manual Start
```bash
# Terminal 1: Backend
cd LocaLense_V2
python -m backend.api

# Terminal 2: Frontend
cd frontend
npm run dev
```

#### Option 3: Legacy Entry Point
```bash
python app.py
```

### API Endpoints

#### Authentication
- `POST /auth/register` - Create new user
- `POST /auth/login` - Login and get session token
- `GET /auth/verify` - Verify session token

#### Indexing
- `POST /index/directory` - Index folder path
- `POST /upload-batch` - Upload files
- `GET /index/status/{task_id}` - Check indexing progress

#### Search
- `POST /search/enhanced` - Semantic search
- `GET /search/enhanced/stream/{session_id}` - SSE stream

#### File Watcher
- `POST /watcher/enable` - Enable file monitoring
- `GET /watcher/status` - Check watcher status
- `POST /watcher/disable` - Stop monitoring

#### Conversations
- `GET /conversations` - List all conversations
- `POST /conversations` - Create new conversation
- `GET /conversations/{id}` - Get conversation details
- `DELETE /conversations/{id}` - Delete conversation

### Development Commands

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install

# Initialize memory database
python init_memory.py

# Delete OpenSearch index (reset)
python delete_index.py

# Test Ollama connection
python test_ollama.py

# Test authentication
python test_auth_endpoint.py
```

---

## 🎯 Key Workflows

### 1. Adding a New Agent

1. Create file in `backend/agents/new_agent.py`
2. Implement agent class with `process()` method
3. Register in `backend/agents/__init__.py`
4. Add configuration in `config.yaml` under `agents:`
5. Update orchestrator routing in `backend/orchestration/orchestrator.py`

### 2. Adding a New API Endpoint

1. Add route in `backend/api.py` or create new endpoint file
2. Import endpoint file in `backend/api.py`
3. Add authentication if needed (`verify_session()`)
4. Update frontend API calls in respective components

### 3. Modifying Search Algorithm

1. Edit `backend/opensearch_client.py` for vector search logic
2. Edit `backend/reranker.py` for reranking algorithm
3. Adjust weights in `config.yaml` under `search:`
4. Test with `test_dual_models.py` or similar

---

## 📊 System Flow Summary

```
USER JOURNEY
────────────

1. First Visit → OnboardingWizard
   ├─ Sign Up/In
   ├─ Index Documents
   └─ Enable File Watcher (optional)

2. Main Interface → ChatInterface
   ├─ Type query
   ├─ Orchestrator classifies intent
   ├─ Search Agent finds documents
   ├─ Memory system adds context
   ├─ LLM generates response
   └─ Results displayed with citations

3. Document Management
   ├─ View search results
   ├─ Attach documents to conversation
   ├─ Open files
   └─ Continue focused queries

4. Settings → SettingsPanel
   ├─ Index more documents
   ├─ Check system health
   └─ Manage file watcher

5. Background Processes
   ├─ File watcher auto-indexes new files
   ├─ Memory system learns patterns
   └─ Session cleanup
```

---

## 🚀 Future Enhancements

### Planned Features (from TODO)
- ✨ In-document chatting (direct Q&A with specific PDFs)
- ✨ Export features (conversations, search results)
- ✨ Analytics dashboard (search stats, popular docs)
- ✨ Advanced filters (date range, file type, size)
- ✨ Multi-language support
- ✨ Cross-document synthesis
- ✨ Plugin system
- ✨ Enterprise features (RBAC, SSO, audit logging)

---

## 📚 Related Documentation

- **[README.md](README.md)** - Main project overview
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed technical architecture
- **[QUICKSTART.md](QUICKSTART.md)** - Quick setup guide
- **[frontend/README.md](frontend/README.md)** - Frontend-specific docs

---

## 🔍 Quick Reference

### Port Map
- **Frontend:** `localhost:5173` (Vite dev server)
- **Backend API:** `localhost:8000` (FastAPI)
- **OpenSearch:** `localhost:9200`
- **Ollama:** `localhost:11434`
- **MCP Server:** `localhost:8001` (optional)

### File Size Summary
- **Backend API:** 60KB (`api.py`)
- **Ingestion Pipeline:** 27KB (`ingestion.py`)
- **Agent Orchestrator:** 19.7KB (`orchestrator.py`)
- **Settings Panel:** 18.3KB (`SettingsPanel.jsx`)
- **Onboarding Wizard:** 18.3KB (`OnboardingWizard.jsx`)

### Total Project Statistics
- **Backend Files:** ~58 Python files
- **Frontend Files:** ~34 JavaScript/JSX files
- **Configuration Files:** YAML, JSON, BAT, SH
- **Documentation:** 5 markdown files
- **Lines of Code:** ~15,000+ (estimated)

---

**Last Updated:** December 3, 2025  
**Version:** 2.0  
**Status:** Active Development  
**License:** MIT

**Made with ❤️ using AI-powered semantic search**
