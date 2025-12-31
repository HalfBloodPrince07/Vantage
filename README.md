# Vantage (LocalLens)

> **🚀 AI-Powered Local-First Semantic Document Search & Knowledge Management System**

Vantage (formerly LocalLens) is an advanced, privacy-focused intelligent document search platform that combines state-of-the-art semantic search, knowledge graphs, multi-agent orchestration, and conversational AI to help you discover, understand, and connect information across your entire document collection—**all running locally on your machine**.

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![React](https://img.shields.io/badge/react-18.2.0-61dafb)
![License](https://img.shields.io/badge/license-GPL--3.0-red)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture Highlights](#architecture-highlights)
- [Technology Stack](#technology-stack)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage Guide](#usage-guide)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Advanced Features](#advanced-features)
- [Performance](#performance)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## 🌟 Overview

### What is Vantage?

Vantage is a **next-generation document intelligence system** that transforms how you interact with your personal or organizational document collections. Unlike traditional search engines that rely on simple keyword matching, Vantage understands the **semantic meaning** of your queries and documents, enabling natural language questions and intelligent, context-aware responses.

### Why Vantage?

**🔒 Privacy-First Design**
- **100% Local Processing**: All data stays on your machine—no cloud uploads, no external API calls
- **Your Data, Your Control**: Complete ownership and control over your documents and search history
- **No Telemetry**: Zero data collection or tracking

**🧠 Intelligent Multi-Agent System**
- **15+ Specialized Agents**: Each agent has a specific role (search, analysis, quality control, etc.)
- **Greek Mythology Naming**: Easy-to-understand agent roles (Zeus orchestrates, Athena classifies, Apollo expands knowledge)
- **LangGraph Orchestration**: State-of-the-art workflow management with parallel execution

**🔍 Advanced Hybrid Search**
- **Vector Similarity (70%)**: Semantic understanding using 768-dimensional embeddings
- **BM25 Keyword Matching (30%)**: Traditional full-text search for precision
- **Cross-Encoder Reranking**: Top 50 results refined to top 5 with advanced scoring
- **Reciprocal Rank Fusion**: Intelligent combination of search strategies

**🧩 Knowledge Graph Integration**
- **Automatic Entity Extraction**: Identifies people, organizations, locations, concepts
- **Relationship Mapping**: Connects related entities across documents
- **Graph Traversal**: Expands search context with related information
- **Visual Exploration**: Interactive force-directed graph visualization

**💾 5-Tier Memory System**
- **Session Memory** (Tier 1): Current conversation context (Redis, 1-hour TTL)
- **Episodic Memory** (Tier 2): Past query-response pairs with decay (SQLite)
- **Procedural Memory** (Tier 3): Learned patterns and behaviors
- **User Profile** (Tier 4): Preferences and interaction statistics
- **Agentic Memory** (Tier 5): Structured knowledge notes with evolution and consolidation

**📄 Universal File Support**
- **Documents**: PDF (with OCR fallback), DOCX, TXT, MD
- **Spreadsheets**: XLSX, CSV
- **Images**: PNG, JPG, JPEG, GIF, BMP (with vision OCR)
- **Smart Processing**: Automatic content extraction, summarization, and indexing

---

## ✨ Key Features

### Core Capabilities

#### 1. **Semantic Search with Hybrid Ranking**
- Combine semantic understanding (vector embeddings) with keyword precision (BM25)
- 768-dimensional embeddings using `nomic-embed-text` model
- Cross-encoder reranking for top-5 precision
- Typical search time: 270-630ms (excluding LLM response generation)

#### 2. **Conversational AI Interface**
- Natural language queries: "What are the main findings in my research papers?"
- Context-aware responses based on conversation history
- Real-time streaming responses with Server-Sent Events (SSE)
- Agent thinking visualization showing each processing step

#### 3. **Multi-Agent Orchestration**
```
Zeus (Orchestrator) → Athena (Classifier) → Routing Decision
                                              ↓
                         ┌────────────────────┼────────────────────┐
                         ▼                    ▼                    ▼
                   Document Search      General Knowledge    Document Analysis
                   (15+ agents)         (Direct LLM)         (Daedalus Path)
```

**Agent Roster (Greek Mythology Theme):**
- **Zeus**: Master orchestrator using LangGraph state machines
- **Athena**: Query intent classification and routing
- **Apollo**: Knowledge graph-based retrieval augmentation
- **Odysseus**: Multi-hop reasoning and query decomposition
- **Proteus**: Adaptive retrieval strategy selection
- **Themis**: Confidence scoring and quality assessment
- **Diogenes**: Hallucination detection and fact-checking
- **Socrates**: Clarifying question generation
- **Aristotle**: Document comparison and analysis
- **Thoth**: Multi-document summarization
- **Hermes**: Search explanation and transparency
- **Sisyphus**: Corrective retrieval on failures
- **Daedalus**: Document processing orchestrator
- **Prometheus**: Content extraction from files
- **Hypatia**: Semantic document analysis
- **Mnemosyne**: Insight and knowledge extraction

#### 4. **Knowledge Graph Visualization**
- Interactive force-directed graph using D3.js
- Node types: Person, Organization, Location, Concept, Document
- Relationship types: Created_By, Related_To, Mentions, Co_Occurs
- Real-time graph expansion with search results
- Zoom, pan, and node exploration

#### 5. **Intelligent Document Processing**
```
File Discovery → Content Extraction → LLM Summarization → Embedding Generation
                                                                      ↓
OpenSearch Indexing ← Knowledge Graph Extraction ← Text Processing ←┘
```

**Processing Pipeline:**
- **Automatic summarization** using Ollama (qwen3-vl:8b)
- **Entity and topic extraction** for metadata enrichment
- **Summary-based embeddings** (not chunking) for better searchability
- **Batch processing** with progress streaming

#### 6. **Real-Time File Watching**
- Monitor indexed directories for changes (add, modify, delete)
- Automatic re-indexing with 3-second debounce
- Background processing without blocking searches
- SSE notifications to frontend

#### 7. **Memory & Learning**
- **Session Memory**: Last 10 conversation turns (sliding window)
- **Episodic Memory**: Similar past queries with time-based decay
- **Procedural Memory**: Learned query patterns (e.g., "ML" → "machine learning")
- **User Profiles**: Interaction statistics and preferences
- **Agentic Memory (A-mem)**:
  - Automatic note generation from conversations
  - Memory link evolution (strengthen frequently co-accessed notes)
  - Periodic consolidation (merge duplicates, strengthen important memories)
  - Proactive suggestions based on knowledge gaps
  - Natural language memory queries

#### 8. **Advanced UI Features**
- **Dark Mode**: System-wide theme toggle with CSS variables
- **Keyboard Shortcuts**:
  - `Ctrl+K`: Focus search
  - `Ctrl+N`: New conversation
  - `Ctrl+Enter`: Send message
  - `Ctrl+G`: Toggle graph
  - `Ctrl+M`: Toggle memory explorer
- **Export Conversations**: Markdown or JSON format
- **Document Attachment**: Select specific documents for focused queries
- **Confidence Visualization**: Real-time confidence graphs
- **Memory Explorer**: Visualize and query memory systems
- **Features Showcase**: Interactive landing page with demos

---

## 🏗️ Architecture Highlights

### System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                       VANTAGE ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              FRONTEND (React 18 + Vite 5)                 │  │
│  │  • Chat Interface  • Knowledge Graph  • Memory Explorer   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            ▲ SSE Stream                          │
│                            │ HTTP/REST                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              API GATEWAY (FastAPI)                        │  │
│  │  • CORS Middleware  • Auth  • Request Logging             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            │                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         ORCHESTRATION (Zeus - LangGraph)                  │  │
│  │  • State Management  • Parallel Execution  • Error Handling│ │
│  └──────────────────────────────────────────────────────────┘  │
│                            │                                     │
│  ┌────────────┬──────────────────┬───────────────┬──────────┐  │
│  │   AGENTS   │  SEARCH ENGINE   │  MEMORY SYS   │  GRAPH   │  │
│  │  (15+)     │  Hybrid Search   │  5 Tiers      │ NetworkX │  │
│  └────────────┴──────────────────┴───────────────┴──────────┘  │
│                            │                                     │
│  ┌────────────┬──────────────────┬───────────────┬──────────┐  │
│  │ OpenSearch │     SQLite       │    Redis      │  Ollama  │  │
│  │  (Search)  │  (Persistence)   │  (Sessions)   │  (LLM)   │  │
│  └────────────┴──────────────────┴───────────────┴──────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Local-First Architecture**: All processing happens on user's machine
2. **Hybrid Search Strategy**: 70% vector similarity + 30% BM25 keyword matching
3. **Summary-Based Indexing**: LLM-generated summaries instead of chunking
4. **Multi-Agent Collaboration**: Specialized agents for different tasks
5. **Memory-Augmented Responses**: Learn from past interactions
6. **Real-Time Streaming**: SSE for live progress updates
7. **Asynchronous Processing**: Non-blocking operations throughout

### Key Technical Decisions

| Decision | Rationale | Trade-off |
|----------|-----------|-----------|
| **Summary-based indexing** (not chunking) | LLM summaries are more semantically dense and searchable | May lose fine-grained details (mitigated with full content indexing) |
| **Local embeddings** (Sentence-Transformers) | More stable than Ollama HTTP endpoint under load | Requires PyTorch and GPU memory |
| **Hybrid search** (Vector + BM25) | Balances semantic understanding with exact keyword matching | ~2x query latency but significantly better recall |
| **LangGraph orchestration** | Built-in state management, conditional routing, parallelization | Added dependency complexity |
| **Greek mythology naming** | Memorable, thematic, human-readable logs | Learning curve for new developers |

---

## 🛠️ Technology Stack

### Backend Stack

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Web Framework** | FastAPI | 0.121.3 | High-performance async REST API |
| **ASGI Server** | Uvicorn | 0.38.0 | Production-grade async server |
| **Orchestration** | LangGraph | 1.0.3 | State machine for agent workflows |
| **LLM Integration** | LangChain | 1.0.8 | LLM abstraction & chains |
| **Local LLM** | Ollama | 0.6.1 | Local inference server |
| **Unified Model** | qwen3-vl:8b | - | Vision-language unified model |
| **Search Engine** | OpenSearch | 3.0.0 | Hybrid vector + full-text search |
| **Embeddings** | Sentence-Transformers | 5.1.2 | nomic-embed-text (768 dims) |
| **Reranking** | CrossEncoder | (via ST) | ms-marco-MiniLM-L-6-v2 |
| **Graph Database** | NetworkX | 3.4.2 | Knowledge graph storage |
| **Cache** | Redis | 7.1.0 | Session memory |
| **Database** | SQLite | 3.x | Conversations, memory, profiles |
| **ORM** | SQLAlchemy | 2.0.44 | Database abstraction |
| **File Watching** | Watchdog | 6.0.0 | Auto-reindexing |
| **Logging** | Loguru | 0.7.3 | Structured logging |
| **Config** | PyYAML | 6.0.3 | Configuration management |
| **Document Processing** | PyPDF, python-docx, pandas | Various | Multi-format support |

### Frontend Stack

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Framework** | React | 18.2.0 | UI component library |
| **Build Tool** | Vite | 5.0.8 | Fast dev server & bundling |
| **Graph Visualization** | React Force Graph 2D | 1.29.0 | Knowledge graph rendering |
| **Markdown** | React Markdown | 9.1.0 | Response formatting |
| **Styling** | CSS3 | - | Vanilla CSS (no frameworks) |
| **HTTP Client** | Fetch API | Native | REST requests |
| **Real-time** | EventSource | Native | Server-Sent Events |

### AI/ML Stack

| Component | Model/Technology | Details |
|-----------|-----------------|---------|
| **LLM** | qwen3-vl:8b | Vision-language unified model (8B params) |
| **Embeddings** | nomic-embed-text | 768 dimensions, local inference |
| **Reranker** | ms-marco-MiniLM-L-6-v2 | Cross-encoder for precision |
| **Vision OCR** | Qwen3-VL | Multimodal understanding for images |

### Infrastructure

| Service | Port | Purpose | Authentication |
|---------|------|---------|----------------|
| **OpenSearch** | 9200 | Search & indexing | admin / LocalLens@1234 |
| **OpenSearch Dashboards** | 5601 | Web UI | Same as OpenSearch |
| **Redis** | 6379 | Session cache | None (localhost only) |
| **Ollama** | 11434 | LLM inference | None (localhost only) |
| **FastAPI Backend** | 8000 | REST API | Optional (configurable) |
| **React Frontend** | 5173 (dev), 3000 (prod) | Web interface | Via backend session |

---

## 💻 System Requirements

### Minimum Requirements

| Component | Specification |
|-----------|---------------|
| **OS** | Linux, macOS, Windows 10+ |
| **CPU** | 4 cores, 2.5+ GHz |
| **RAM** | 16 GB |
| **GPU** | Not required (CPU fallback) |
| **Storage** | 10 GB free space + document storage |
| **Python** | 3.8 or higher |
| **Node.js** | 16.x or higher |
| **Docker** | 20.10+ (for OpenSearch & Redis) |

### Recommended Requirements

| Component | Specification |
|-----------|---------------|
| **OS** | Linux (Ubuntu 20.04+) or macOS 12+ |
| **CPU** | 8 cores, 3.0+ GHz |
| **RAM** | 32 GB |
| **GPU** | NVIDIA GPU with 8+ GB VRAM (CUDA 11.8+) |
| **Storage** | SSD with 50+ GB free space |
| **Python** | 3.10 or 3.11 |
| **Node.js** | 18.x or 20.x LTS |
| **Docker** | Latest stable version |

### Performance Impact of GPU

| Operation | CPU Time | GPU Time | Speedup |
|-----------|----------|----------|---------|
| Embedding generation (per doc) | 400-500ms | 100-150ms | ~3-4x |
| Cross-encoder reranking (50 docs) | 250-300ms | 100-150ms | ~2-3x |
| Overall query latency | 4-6s | 3-4.5s | ~1.3-1.5x |

---

## 📦 Installation

### Prerequisites Setup

#### 1. Install Python 3.8+

**Linux/macOS:**
```bash
# Check Python version
python --version

# Install Python 3.10 (recommended)
# Ubuntu/Debian
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip

# macOS (via Homebrew)
brew install python@3.10
```

**Windows:**
Download and install from [python.org](https://www.python.org/downloads/)

#### 2. Install Node.js 16+

**Linux/macOS:**
```bash
# Using NVM (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18

# Or via package manager
# Ubuntu/Debian
sudo apt install nodejs npm

# macOS
brew install node
```

**Windows:**
Download installer from [nodejs.org](https://nodejs.org/)

#### 3. Install Docker

**Linux:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER  # Add user to docker group
```

**macOS:**
Install [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)

**Windows:**
Install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)

#### 4. Install Ollama

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**macOS:**
```bash
brew install ollama
```

**Windows:**
Download installer from [ollama.com](https://ollama.com/download)

**Pull the required model:**
```bash
ollama pull qwen3-vl:8b
# This will download ~4.7 GB
```

### Vantage Installation

#### Method 1: Standard Installation

```bash
# 1. Clone the repository
git clone https://github.com/HalfBloodPrince07/Vantage.git
cd Vantage

# 2. Create Python virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or use conda
conda create -n vantage python=3.10
conda activate vantage

# 3. Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Install frontend dependencies
cd frontend
npm install
cd ..

# 5. Start infrastructure services
docker-compose up -d

# Wait for services to be healthy (30-60 seconds)
docker-compose ps

# 6. Verify OpenSearch is ready
curl -k -u admin:LocalLens@1234 https://localhost:9200/_cluster/health

# 7. Start Ollama (if not already running)
ollama serve &

# 8. Configure application (optional, defaults are fine)
cp config.yaml config.local.yaml
# Edit config.local.yaml if needed

# 9. Run the application
# Option A: Using run script (Windows)
run.bat

# Option B: Manual startup
# Terminal 1: Backend
python -m uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

#### Method 2: Conda Environment (Recommended for ML)

```bash
# 1. Clone repository
git clone https://github.com/HalfBloodPrince07/Vantage.git
cd Vantage

# 2. Create conda environment
conda create -n vantage python=3.10 -y
conda activate vantage

# 3. Install PyTorch with CUDA (if you have NVIDIA GPU)
# For CUDA 11.8
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia

# For CPU only
conda install pytorch torchvision torchaudio cpuonly -c pytorch

# 4. Install other dependencies
pip install -r requirements.txt

# 5. Continue with steps 4-9 from Method 1
```

#### Method 3: Docker-Only Installation (Coming Soon)

Full containerized deployment with Docker Compose.

### Verification

```bash
# Check backend health
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "opensearch": "connected", "redis": "connected", "ollama": "ready"}

# Check frontend
# Open browser to http://localhost:5173
```

---

## ⚙️ Configuration

All configuration is centralized in `config.yaml`. You can override settings by creating `config.local.yaml` (gitignored).

### Core Configuration Sections

#### 1. Ollama Settings

```yaml
ollama:
  base_url: "http://localhost:11434"
  unified_model:
    name: "qwen3-vl:8b"
    temperature: 0.3           # Lower = more deterministic
    max_tokens: 15000
    timeout: 60                # seconds
    thinking_mode: true        # Enable chain-of-thought
```

#### 2. OpenSearch Configuration

```yaml
opensearch:
  hosts:
    - "localhost"
  port: 9200
  use_ssl: true
  verify_certs: false          # For self-signed certs
  auth:
    username: "admin"
    password: "LocalLens@1234"
  index_name: "locallens_index"
  settings:
    number_of_shards: 1
    number_of_replicas: 0
```

#### 3. Model Settings

```yaml
models:
  embedding_model: "nomic-embed-text"
  embedding_dimension: 768
  reranking_model: "cross-encoder/ms-marco-MiniLM-L-6-v2"
  vision_model: "qwen3-vl:8b"  # For image OCR
```

#### 4. Search Configuration

```yaml
search:
  hybrid_weights:
    vector: 0.7               # Semantic similarity weight
    bm25: 0.3                 # Keyword matching weight
  query_expansion:
    enabled: true
    max_expansions: 3
  retrieval:
    top_k: 50                 # Initial retrieval
    min_score: 0.3
  reranking:
    enabled: true
    top_k: 5                  # Final results after reranking
```

#### 5. Agent Configuration

```yaml
agents:
  query_classifier:
    confidence_threshold: 0.7

  clarification:
    enabled: true
    min_confidence: 0.5

  analysis:
    enable_comparison: true
    enable_trends: true

  summarization:
    max_documents: 10
    style: "bullet_points"    # or "paragraph"

  explanation:
    include_reasoning: true

  critic:
    hallucination_detection: true
    factuality_threshold: 0.8
```

#### 6. Memory Configuration

```yaml
memory:
  session:
    backend: "redis"          # or "in_memory"
    redis_url: "redis://localhost:6379"
    ttl: 3600                 # 1 hour in seconds
    context_window: 10        # conversation turns

  episodic:
    enabled: true
    decay_factor: 0.95        # Per day

  procedural:
    enabled: true
    learning_rate: 0.1

  user_profile:
    track_preferences: true
    track_statistics: true

  agentic:
    enabled: true
    consolidation_interval: 3600  # 1 hour
    pruning_interval: 604800      # 1 week
    min_importance: 0.1
```

#### 7. File Watcher

```yaml
watcher:
  enabled: false              # Enable via API
  debounce_seconds: 3
  batch_size: 1
  supported_extensions:
    - ".pdf"
    - ".docx"
    - ".txt"
    - ".md"
    - ".xlsx"
    - ".csv"
    - ".png"
    - ".jpg"
    - ".jpeg"
    - ".gif"
    - ".bmp"
```

#### 8. Orchestration

```yaml
orchestration:
  langgraph_enabled: true
  parallel_execution: true
  max_concurrent_agents: 3
  timeout: 60                 # seconds
  retry_attempts: 2
```

#### 9. Performance & Monitoring

```yaml
performance:
  caching:
    enabled: true
    ttl: 3600                 # seconds

  gpu:
    enabled: true             # Auto-detect CUDA
    mixed_precision: true

  logging:
    level: "INFO"             # DEBUG, INFO, WARNING, ERROR
    format: "json"            # or "text"
    file: "logs/vantage.log"
```

### Environment Variables

You can override config values with environment variables:

```bash
export OLLAMA_BASE_URL="http://192.168.1.100:11434"
export OPENSEARCH_HOST="192.168.1.101"
export REDIS_URL="redis://192.168.1.102:6379"
```

---

## 📖 Usage Guide

### First-Time Setup: Onboarding Wizard

1. **Open the application**: Navigate to `http://localhost:5173`
2. **Welcome screen**: Click "Get Started"
3. **Select documents**: Choose a directory to index (e.g., `~/Documents`, `~/Downloads`)
4. **Indexing progress**: Watch real-time progress as documents are processed
5. **Ready to search**: Start asking questions!

### Basic Usage

#### Simple Search

```
Query: "What are my invoices from January 2024?"
```

The system will:
1. Classify intent (DOCUMENT_SEARCH)
2. Search indexed documents
3. Rerank results
4. Generate natural language response with sources

#### Document Attachment

1. Click the 📎 paperclip icon
2. Select specific documents from the modal
3. Ask questions about those specific documents

```
Query (with 2 attached PDFs): "Compare the methodologies in these papers"
```

#### Conversation Context

Vantage remembers your conversation (last 10 turns):

```
You: "What is machine learning?"
Assistant: "Machine learning is..."

You: "Give me examples from my documents"  # Uses context!
Assistant: "Based on your documents about ML..."
```

### Advanced Usage

#### Knowledge Graph Exploration

1. Click the graph icon (🔗) in the response
2. Explore entity relationships visually
3. Double-click nodes to expand connections
4. Search for specific entities

#### Memory Exploration

1. Click "Memory" button (or press `Ctrl+M`)
2. View **Memory Graph**: Visual representation of learned knowledge
3. Check **Insights**: Key learnings and patterns
4. See **Statistics**: Memory usage and performance

#### Natural Language Memory Queries

```
Query: "What do I know about transformers?"
# System searches agentic memory and returns structured knowledge
```

#### Exporting Conversations

1. Click the export button (📥)
2. Choose format: Markdown or JSON
3. Download your conversation history

### Power User Features

#### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+K` | Focus search input |
| `Ctrl+N` | Start new conversation |
| `Ctrl+Enter` | Send message |
| `Ctrl+G` | Toggle knowledge graph |
| `Ctrl+M` | Toggle memory explorer |
| `Ctrl+S` | Open settings panel |
| `Escape` | Close modals/panels |

#### Custom Preferences

1. Open Settings (`Ctrl+S`)
2. Configure:
   - **Response Format**: Bullet points or paragraphs
   - **Detail Level**: Brief, Detailed, or Verbose
   - **Citation Style**: Inline, Footnotes, or None
   - **Preferred Sources**: Filter by file type
   - **Dark Mode**: Toggle theme

#### Feedback Loop

- **Thumbs Up/Down**: Rate responses to improve future results
- **Comments**: Provide detailed feedback
- System learns from your feedback via procedural memory

---

## 🔌 API Documentation

### Base URL

```
http://localhost:8000
```

### Authentication

Currently optional. If enabled, include session token:

```bash
curl -H "Authorization: Bearer YOUR_SESSION_TOKEN" \
     http://localhost:8000/search
```

### Core Endpoints

#### 1. Search Documents

**Endpoint**: `POST /search`

**Request Body**:
```json
{
  "query": "What are the key findings in my research papers?",
  "top_k": 5,
  "session_id": "optional-session-uuid",
  "user_id": "optional-user-uuid",
  "attached_documents": [],
  "filters": {
    "file_type": ["pdf", "docx"],
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-12-31"
    }
  }
}
```

**Response** (Streaming SSE):
```
event: thinking_step
data: {"agent": "Athena", "action": "Classifying query intent"}

event: search_results
data: [{"doc_id": "abc123", "score": 0.94, "title": "Research Paper 1"}]

event: response_chunk
data: "Based on your research papers, the key findings are:\n"

event: confidence_score
data: 0.91

event: complete
data: {"response": "...", "results": [...], "confidence": 0.91}
```

#### 2. Index Documents

**Endpoint**: `POST /index`

**Request Body**:
```json
{
  "directory": "/home/user/Documents",
  "watch_mode": false,
  "recursive": true
}
```

**Response** (Streaming SSE):
```
event: progress
data: {"status": "processing", "current_file": "paper.pdf", "progress": "15/100"}

event: complete
data: {"indexed": 92, "failed": 5, "skipped": 3}
```

#### 3. Upload File

**Endpoint**: `POST /upload`

**Request**: Multipart form data

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@/path/to/document.pdf"
```

#### 4. List Documents

**Endpoint**: `GET /documents`

**Query Parameters**:
- `limit`: Max results (default: 100)
- `offset`: Pagination offset (default: 0)
- `file_type`: Filter by type (e.g., "pdf")
- `sort_by`: Sort field (default: "created_at")

**Response**:
```json
{
  "total": 1250,
  "documents": [
    {
      "id": "abc123",
      "filename": "research_paper.pdf",
      "file_type": "pdf",
      "document_type": "research_paper",
      "created_at": "2025-01-15T10:30:00Z",
      "file_size": 2048576,
      "keywords": ["ML", "transformers"]
    }
  ]
}
```

#### 5. Get Document Details

**Endpoint**: `GET /document/{doc_id}`

**Response**:
```json
{
  "id": "abc123",
  "filename": "research_paper.pdf",
  "detailed_summary": "This paper explores...",
  "keywords": ["ML", "transformers"],
  "entities": ["BERT", "Google"],
  "topics": ["NLP", "neural networks"],
  "created_at": "2025-01-15T10:30:00Z"
}
```

#### 6. Memory Management

**Get Session**: `GET /memory/session/{session_id}`

**Update Session**: `POST /memory/session`
```json
{
  "session_id": "uuid",
  "user_id": "uuid",
  "turn": {
    "role": "user",
    "content": "What is ML?"
  }
}
```

**Get Episodes**: `GET /memory/episodes?user_id={uuid}&limit=10`

**Memory Graph**: `GET /memory/graph?user_id={uuid}`

#### 7. File Watcher

**Enable**: `POST /watcher/enable`
```json
{"paths": ["/home/user/Documents"]}
```

**Disable**: `POST /watcher/disable`

**Status**: `GET /watcher/status`

#### 8. Feedback

**Submit Feedback**: `POST /feedback`
```json
{
  "query_id": "episode-uuid",
  "user_id": "user-uuid",
  "rating": 1,  // 1 (positive), -1 (negative), 0 (neutral)
  "comment": "Great answer!"
}
```

#### 9. Health Check

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "opensearch": "connected",
  "redis": "connected",
  "ollama": "ready",
  "version": "2.0.0"
}
```

### Error Responses

```json
{
  "error": true,
  "error_code": "SEARCH_FAILED",
  "message": "Failed to retrieve documents",
  "details": "OpenSearch connection timeout",
  "retry_after": 5
}
```

**HTTP Status Codes**:
- `200`: Success
- `400`: Bad request (invalid parameters)
- `401`: Unauthorized
- `404`: Not found
- `500`: Internal server error
- `503`: Service unavailable (dependencies down)

---

## 📁 Project Structure

```
Vantage/
│
├── backend/                          # Python backend (FastAPI)
│   ├── api.py                        # Main FastAPI application & endpoints
│   ├── ingestion.py                  # Document processing pipeline
│   ├── opensearch_client.py          # Search engine client
│   ├── reranker.py                   # Cross-encoder reranking
│   ├── watcher.py                    # File system monitoring
│   ├── watcher_endpoints.py          # File watcher API routes
│   ├── feedback.py                   # Feedback storage
│   ├── auth.py                       # Authentication logic
│   ├── auth_endpoints.py             # Auth API routes
│   ├── a2a_agent.py                  # Agent-to-Agent communication
│   ├── mcp_tools.py                  # MCP tool registry
│   ├── streaming_steps.py            # SSE streaming utilities
│   │
│   ├── orchestration/                # LangGraph orchestrator
│   │   └── orchestrator.py           # Zeus orchestrator
│   │
│   ├── agents/                       # Specialized AI agents (15+)
│   │   ├── query_classifier.py       # Athena (intent classification)
│   │   ├── graph_rag_agent.py        # Apollo (graph RAG)
│   │   ├── reasoning_planner.py      # Odysseus (multi-hop reasoning)
│   │   ├── adaptive_retriever.py     # Proteus (adaptive retrieval)
│   │   ├── confidence_scorer.py      # Themis (confidence scoring)
│   │   ├── critic_agent.py           # Diogenes (hallucination detection)
│   │   ├── clarification_agent.py    # Socrates (clarifying questions)
│   │   ├── analysis_agent.py         # Aristotle (document analysis)
│   │   ├── summarization_agent.py    # Thoth (summarization)
│   │   ├── explanation_agent.py      # Hermes (explanation)
│   │   ├── retrieval_controller.py   # Sisyphus (corrective retrieval)
│   │   │
│   │   └── document_agents/          # Document processing agents
│   │       ├── daedalus_orchestrator.py  # Daedalus (doc orchestrator)
│   │       ├── prometheus_reader.py      # Prometheus (content extraction)
│   │       ├── hypatia_analyzer.py       # Hypatia (semantic analysis)
│   │       └── mnemosyne_extractor.py    # Mnemosyne (insight extraction)
│   │
│   ├── graph/                        # Knowledge graph components
│   │   ├── knowledge_graph.py        # NetworkX graph implementation
│   │   ├── entity_resolver.py        # Entity resolution & merging
│   │   └── relationship_extractor.py # Relationship extraction
│   │
│   ├── memory/                       # 5-tier memory system
│   │   ├── memory_manager.py         # Unified memory coordinator
│   │   ├── session_memory.py         # Tier 1: Session (Redis)
│   │   ├── episodic_memory.py        # Tier 2: Episodic (SQLite)
│   │   ├── procedural_memory.py      # Tier 3: Procedural (SQLite)
│   │   ├── user_profile.py           # Tier 4: User profile (SQLite)
│   │   ├── conversation_manager.py   # Conversation tracking
│   │   ├── memory_reflector.py       # Memory reflection
│   │   ├── memory_tool.py            # Tool interface for agents
│   │   │
│   │   └── agentic_memory/           # Tier 5: Advanced A-mem system
│   │       ├── system.py             # Main A-mem coordinator
│   │       ├── note.py               # Memory note structure
│   │       ├── note_generator.py     # Auto note generation
│   │       ├── chains.py             # LangChain integration
│   │       ├── evolution.py          # Memory link evolution
│   │       ├── consolidation.py      # Memory consolidation
│   │       ├── pruning.py            # Memory decay & cleanup
│   │       ├── multimodal.py         # Multi-modal memory
│   │       ├── proactive.py          # Proactive suggestions
│   │       ├── reorganizer.py        # Graph reorganization
│   │       ├── metrics.py            # Memory metrics
│   │       ├── tuning.py             # Performance tuning
│   │       ├── nl_interface.py       # Natural language queries
│   │       └── opensearch_memory.py  # OpenSearch backend
│   │
│   ├── ranking/                      # Ranking components
│   │   └── personalized_ranker.py    # Feedback-based ranking
│   │
│   ├── utils/                        # Utility modules
│   │   ├── llm_utils.py              # Ollama utilities
│   │   ├── model_manager.py          # Model lifecycle management
│   │   └── session_logger.py         # Session logging
│   │
│   ├── tests/                        # Test scripts
│   │   ├── reproduce_memory_error.py
│   │   ├── verify_agents.py
│   │   └── verify_fixes.py
│   │
│   └── uploads/                      # Uploaded files directory
│
├── frontend/                         # React frontend (Vite)
│   ├── src/
│   │   ├── App.jsx                   # Root component
│   │   ├── main.jsx                  # Entry point
│   │   ├── index.css                 # Global styles
│   │   │
│   │   ├── components/               # React components
│   │   │   ├── ChatInterface.jsx     # Main chat UI
│   │   │   ├── ChatInterface.css
│   │   │   ├── ChatSidebar.jsx       # Conversation list
│   │   │   ├── DocumentSelector.jsx  # Document attachment
│   │   │   ├── EntityGraphModal.jsx  # Knowledge graph visualization
│   │   │   ├── AgentThinkingCinematic.jsx  # Agent visualization
│   │   │   ├── ConfidenceGraph.jsx   # Confidence visualization
│   │   │   ├── IndexingProgress.jsx  # Indexing progress bar
│   │   │   ├── OnboardingWizard.jsx  # First-time setup
│   │   │   ├── SettingsPanel.jsx     # Settings UI
│   │   │   ├── LoginSettings.jsx     # Authentication
│   │   │   ├── MemoryExplorer.jsx    # Memory system UI
│   │   │   ├── MemoryGraph.jsx       # Memory graph viz
│   │   │   ├── MemoryInsights.jsx    # Memory insights
│   │   │   ├── MemoryStats.jsx       # Memory statistics
│   │   │   ├── FeaturesShowcase.jsx  # Landing page
│   │   │   ├── CreatorBadge.jsx      # Attribution
│   │   │   ├── AIAgentAvatar.jsx     # Agent avatars
│   │   │   ├── AmbientParticles.jsx  # Background animation
│   │   │   └── index.js              # Component exports
│   │   │
│   │   ├── hooks/                    # Custom React hooks
│   │   │   ├── useDarkMode.jsx       # Dark mode toggle
│   │   │   ├── useKeyboardShortcuts.jsx  # Keyboard shortcuts
│   │   │   └── index.js
│   │   │
│   │   └── styles/                   # Additional styles
│   │       ├── dark-mode.css
│   │       └── ai-dashboard.css
│   │
│   ├── public/                       # Static assets
│   ├── index.html                    # Main HTML
│   ├── chat.html                     # Chat-only page
│   ├── package.json                  # NPM dependencies
│   ├── vite.config.js                # Vite configuration
│   └── .eslintrc.cjs                 # ESLint config
│
├── docs/                             # Comprehensive documentation
│   ├── README.md                     # Documentation index
│   ├── 01_OVERALL_SYSTEM_ARCHITECTURE.md
│   ├── 02_BACKEND_ARCHITECTURE.md
│   ├── 03_AGENT_SYSTEM_ARCHITECTURE.md
│   ├── 04_MEMORY_SYSTEM_ARCHITECTURE.md
│   ├── 05_FRONTEND_ARCHITECTURE.md
│   ├── 06_DATA_FLOW_AND_REQUEST_LIFECYCLE.md
│   └── 07_INGESTION_PIPELINE_ARCHITECTURE.md
│
├── logs/                             # Application logs
│   ├── vantage.log
│   └── ingestion_*.log
│
├── config.yaml                       # Main configuration file
├── config.local.yaml                 # Local overrides (gitignored)
├── docker-compose.yml                # Infrastructure services
├── requirements.txt                  # Python dependencies
├── run.bat                           # Windows run script
├── .gitignore                        # Git ignore rules
├── LICENSE                           # GPL-3.0 license
└── README.md                         # This file
```

---

## 🚀 Advanced Features

### 1. Query Classification & Routing

Athena automatically classifies queries into:
- **DOCUMENT_SEARCH**: Search indexed documents
- **GENERAL_KNOWLEDGE**: Use LLM knowledge (no search)
- **COMPARISON**: Compare multiple documents
- **SUMMARIZATION**: Summarize documents
- **ANALYSIS**: Analyze trends/patterns
- **CLARIFICATION_NEEDED**: Generate clarifying questions

### 2. Multi-Hop Reasoning (Odysseus)

For complex queries like:
> "Compare the methodologies in my ML papers and identify common datasets"

Odysseus decomposes into:
1. Find all ML papers
2. Extract methodologies from each
3. Extract datasets from each
4. Compare methodologies
5. Identify common datasets

### 3. Adaptive Retrieval (Proteus)

Proteus selects the best retrieval strategy based on query type:
- **Technical queries** → Prefer vector search
- **Specific names/dates** → Prefer BM25
- **Broad topics** → Balanced hybrid

### 4. Corrective Retrieval (Sisyphus)

If initial search fails (low confidence):
1. Try simplified query
2. Expand query with synonyms
3. Search with looser filters
4. Return best effort or clarify

### 5. Proactive Memory Suggestions

A-mem system can proactively suggest:
- "You might also be interested in X" (based on knowledge graph)
- "I noticed you haven't explored Y yet" (gap detection)
- "This contradicts what you learned earlier" (consistency check)

### 6. Natural Language Memory Queries

Ask your memory system directly:
- "What do I know about transformers?"
- "Show me all facts about neural networks"
- "What did I learn last week?"

### 7. Vision OCR for Images

Qwen3-VL can:
- Extract text from images (OCR)
- Describe visual content
- Answer questions about diagrams/charts

Example:
```
Attach: architecture_diagram.png
Query: "Explain the data flow in this diagram"
```

---

## ⚡ Performance

### Typical Query Latency Breakdown

| Stage | Time | % of Total |
|-------|------|------------|
| **Frontend Input** | 0ms | 0% |
| **Request Formation** | 5-10ms | 0.2% |
| **API Gateway** | 15-30ms | 0.6% |
| **Memory Context Loading** | 120-150ms | 3.8% |
| **Query Classification** (Athena) | 200-400ms | 8.5% |
| **Document Retrieval** | 270-630ms | 12.7% |
| **Graph Expansion** (Apollo) | 150-250ms | 5.6% |
| **LLM Response Generation** | **2000-5000ms** | **57-76%** ⚠️ |
| **Quality Control** (Themis + Diogenes) | 150-250ms | 5.6% |
| **Memory Storage** | 120-180ms | 4.2% |
| **Response Finalization** | 5-10ms | 0.2% |
| **Frontend Rendering** | 10-50ms | 0.8% |
| **TOTAL** | **2.9-6.6s** (avg: **3.5-4.5s**) | **100%** |

### Performance Optimization Tips

1. **Use GPU**: 1.3-1.5x overall speedup
2. **Enable Caching**: Reuse responses for common queries
3. **Reduce `max_tokens`**: Faster for simple queries
4. **Lower `top_k`**: Fewer documents to rerank
5. **Disable Graph Expansion**: Skip Apollo for simple searches
6. **Use Smaller Model**: qwen2:7b instead of qwen3-vl:8b (if vision not needed)

### Bottleneck: LLM Generation

The primary bottleneck is LLM response generation (2-5 seconds). This is a fundamental limitation of local inference. Optimizations:
- **Streaming**: User sees response as it's generated (better perceived performance)
- **Response Caching**: Reuse responses for identical/similar queries
- **Smaller Models**: Trade quality for speed on simple queries
- **GPU Inference**: 2-3x faster token generation

### Scalability

**Current System (Single Machine)**:
- Documents: Up to 100,000
- Concurrent Users: 1-5
- Queries/Second: 1-2

**For Larger Scale**:
- Use OpenSearch cluster (multi-node)
- Deploy multiple FastAPI workers
- Use PostgreSQL instead of SQLite
- Implement load balancing

---

## 🔧 Troubleshooting

### Common Issues

#### 1. OpenSearch Connection Refused

**Symptoms**: `ConnectionError: Connection refused [Errno 111]`

**Solutions**:
```bash
# Check if OpenSearch is running
docker ps | grep opensearch

# Restart OpenSearch
docker-compose restart opensearch

# Check logs
docker-compose logs opensearch

# Wait for health (can take 30-60 seconds)
curl -k -u admin:LocalLens@1234 https://localhost:9200/_cluster/health
```

#### 2. Ollama Model Not Found

**Symptoms**: `Error: model "qwen3-vl:8b" not found`

**Solutions**:
```bash
# Check running models
ollama list

# Pull the model
ollama pull qwen3-vl:8b

# Restart Ollama
ollama serve
```

#### 3. Redis Connection Error

**Symptoms**: `ConnectionError: Error connecting to Redis`

**Solutions**:
```bash
# Check if Redis is running
docker ps | grep redis

# Restart Redis
docker-compose restart redis

# Test connection
redis-cli ping  # Should return "PONG"

# Fallback: Use in-memory session (edit config.yaml)
memory:
  session:
    backend: "in_memory"
```

#### 4. Frontend Build Errors

**Symptoms**: `npm run dev` fails with dependency errors

**Solutions**:
```bash
cd frontend

# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf node_modules/.vite

# Try again
npm run dev
```

#### 5. Out of Memory (OOM)

**Symptoms**: Python process killed, `MemoryError`

**Solutions**:
- Reduce batch size in `config.yaml`:
  ```yaml
  search:
    retrieval:
      top_k: 30  # Instead of 50
  ```
- Close other applications
- Increase system swap space
- Use CPU instead of GPU (edit config):
  ```yaml
  performance:
    gpu:
      enabled: false
  ```

#### 6. Slow Indexing

**Symptoms**: Indexing takes > 1 minute per document

**Possible Causes**:
- Large PDF files
- Ollama timeout
- Network latency to Ollama

**Solutions**:
```yaml
# Increase timeout
ollama:
  timeout: 120  # 2 minutes

# Reduce summary length
summarization:
  max_tokens: 300  # Instead of 500
```

#### 7. GPU Not Detected

**Symptoms**: `Device: cpu` instead of `Device: cuda`

**Solutions**:
```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# If False, reinstall PyTorch with CUDA
pip uninstall torch torchvision
conda install pytorch torchvision pytorch-cuda=11.8 -c pytorch -c nvidia

# Verify
python -c "import torch; print(torch.cuda.get_device_name(0))"
```

### Debug Mode

Enable detailed logging:

```yaml
# config.yaml
performance:
  logging:
    level: "DEBUG"
```

View logs:
```bash
# Backend logs
tail -f logs/vantage.log

# Ingestion logs
tail -f logs/ingestion_*.log

# Docker logs
docker-compose logs -f opensearch
docker-compose logs -f redis
```

---

## 👨‍💻 Development

### Setting Up Development Environment

```bash
# 1. Clone repository
git clone https://github.com/HalfBloodPrince07/Vantage.git
cd Vantage

# 2. Create development environment
conda create -n vantage-dev python=3.10
conda activate vantage-dev

# 3. Install dependencies with dev tools
pip install -r requirements.txt
pip install pytest black flake8 mypy  # Dev tools

# 4. Install pre-commit hooks (optional)
pip install pre-commit
pre-commit install

# 5. Frontend development
cd frontend
npm install
npm run dev  # Hot reload enabled
```

### Running Tests

```bash
# Backend tests
pytest backend/tests/

# Specific test
pytest backend/tests/test_agents.py -v

# With coverage
pytest --cov=backend backend/tests/
```

### Code Quality

```bash
# Format code
black backend/

# Lint
flake8 backend/

# Type checking
mypy backend/
```

### Adding a New Agent

1. Create agent file: `backend/agents/my_agent.py`
2. Implement agent class:
```python
class MyAgent:
    def __init__(self, config):
        self.config = config

    async def execute(self, state):
        # Agent logic
        return updated_state
```
3. Register in orchestrator: `backend/orchestration/orchestrator.py`
4. Update config: `config.yaml`

### Architecture Documentation

Full architecture documentation available in `docs/`:
- `01_OVERALL_SYSTEM_ARCHITECTURE.md` - System overview
- `02_BACKEND_ARCHITECTURE.md` - Backend components
- `03_AGENT_SYSTEM_ARCHITECTURE.md` - Agent details
- `04_MEMORY_SYSTEM_ARCHITECTURE.md` - Memory systems
- `05_FRONTEND_ARCHITECTURE.md` - Frontend components
- `06_DATA_FLOW_AND_REQUEST_LIFECYCLE.md` - Request lifecycle
- `07_INGESTION_PIPELINE_ARCHITECTURE.md` - Document processing

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Contribution Guidelines

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Add tests** (if applicable)
5. **Format code**: `black backend/` (Python) or `npm run format` (JS)
6. **Commit**: `git commit -m "Add amazing feature"`
7. **Push**: `git push origin feature/amazing-feature`
8. **Open a Pull Request**

### Pull Request Checklist

- [ ] Code follows existing style (Black for Python, ESLint for JS)
- [ ] Tests added/updated (if applicable)
- [ ] Documentation updated (if changing functionality)
- [ ] Config schema updated (if adding new settings)
- [ ] No breaking changes (or clearly documented)
- [ ] Tested locally with all dependencies

### Areas for Contribution

**High Priority**:
- [ ] Additional document format support (epub, pptx, etc.)
- [ ] Multi-language support (i18n)
- [ ] Advanced filters (date range, author, etc.)
- [ ] Batch operations API
- [ ] Performance optimizations

**Medium Priority**:
- [ ] Alternative LLM backends (Anthropic, OpenAI)
- [ ] Cloud deployment guides (AWS, GCP, Azure)
- [ ] Mobile-responsive UI improvements
- [ ] Advanced analytics dashboard

**Low Priority / Nice to Have**:
- [ ] Browser extension
- [ ] Mobile app (React Native)
- [ ] Plugin system for custom agents
- [ ] Collaborative features (multi-user)

### Reporting Issues

**Bug Reports**: Include:
- OS and version
- Python version
- Error message and stack trace
- Steps to reproduce
- Expected vs actual behavior

**Feature Requests**: Include:
- Use case description
- Proposed solution
- Alternative solutions considered

---

## 📄 License

This project is licensed under the **GNU General Public License v3.0** (GPL-3.0).

**Key Points**:
- ✅ **Commercial use**: Allowed
- ✅ **Modification**: Allowed
- ✅ **Distribution**: Allowed
- ✅ **Private use**: Allowed
- ❌ **Liability**: No warranty provided
- ❌ **Warranty**: No warranty provided
- ⚠️ **Disclose source**: Must disclose source code
- ⚠️ **License and copyright notice**: Must include
- ⚠️ **Same license**: Derivatives must use GPL-3.0
- ⚠️ **State changes**: Must document changes

See [LICENSE](LICENSE) file for full text.

### Third-Party Licenses

This project uses the following open-source libraries:
- FastAPI (MIT License)
- React (MIT License)
- LangChain (MIT License)
- OpenSearch (Apache 2.0)
- And many others (see `requirements.txt` and `package.json`)

All dependencies have compatible open-source licenses.

---

## 🙏 Acknowledgments

### Core Technologies
- **Ollama**: Local LLM inference
- **OpenSearch**: Search and indexing
- **LangGraph**: Agent orchestration
- **Sentence-Transformers**: Embeddings
- **React & Vite**: Modern frontend stack

### Inspiration
- LangChain ecosystem
- Semantic Scholar
- Obsidian knowledge management
- Perplexity AI

### Contributors
Special thanks to all contributors who have helped make Vantage better!

---

## 📞 Support & Community

### Getting Help

- **📚 Documentation**: [docs/](./docs/)
- **🐛 Issues**: [GitHub Issues](https://github.com/HalfBloodPrince07/Vantage/issues)
- **💬 Discussions**: [GitHub Discussions](https://github.com/HalfBloodPrince07/Vantage/discussions)

### Stay Updated

- **⭐ Star this repo** to stay notified of updates
- **👀 Watch releases** for new versions
- **🍴 Fork** to start building your own features

---

## 🗺️ Roadmap

### Version 2.1 (Q1 2025)
- [ ] Enhanced multi-modal support (audio, video)
- [ ] Distributed search (multi-node OpenSearch)
- [ ] Advanced query syntax (Boolean operators, filters)
- [ ] Collaborative features (shared workspaces)

### Version 2.2 (Q2 2025)
- [ ] Plugin system for custom agents
- [ ] Alternative LLM backends (API-based)
- [ ] Advanced analytics dashboard
- [ ] Mobile app (React Native)

### Version 3.0 (Q3 2025)
- [ ] Federated search (multiple Vantage instances)
- [ ] Advanced security (encryption, access control)
- [ ] Enterprise features (SSO, audit logs)
- [ ] Cloud deployment options

---

## 📊 Project Stats

- **Lines of Code**: ~50,000+
- **Languages**: Python (60%), JavaScript (30%), CSS (5%), YAML (5%)
- **Dependencies**: 80+ Python packages, 30+ NPM packages
- **Documentation**: 30,000+ lines
- **Architecture Diagrams**: 50+ ASCII diagrams
- **Agents**: 15+ specialized agents
- **Supported File Types**: 11 formats

---

**Built with ❤️ by the Vantage Team**

**Version**: 2.0.0
**Last Updated**: December 31, 2025
**Status**: Active Development

---

**Happy Searching! 🚀**
