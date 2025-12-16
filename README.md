# 🔍 Vantage (LocaLense V2)

> **AI-Powered Local Document Intelligence Platform**

A sophisticated RAG (Retrieval-Augmented Generation) system that transforms your local documents into an intelligent, searchable knowledge base with advanced AI agents, knowledge graphs, and personalized search.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![React](https://img.shields.io/badge/react-18+-blue.svg)

---

## 🌟 Features

### 🤖 **Multi-Agent AI Architecture**
- **Zeus (The Conductor)** - Master orchestrator routing queries to specialized agents
- **Athena (The Strategist)** - Intent classification and query understanding
- **Proteus (The Shape-Shifter)** - Adaptive retrieval strategy selection
- **Apollo (The Illuminator)** - Knowledge graph expansion for related entities
- **Odysseus (The Voyager)** - Multi-hop reasoning for complex queries
- **Hermes (The Messenger)** - Result explanation and relevance scoring
- **Diogenes (The Critic)** - Quality evaluation and hallucination detection
- **Themis (The Arbiter)** - Confidence scoring with evidence grading
- **Daedalus (The Architect)** - Document-specific query processing
- **Aristotle** - Deep document analysis and insight extraction
- **Sisyphus** - Iterative retrieval with quality-based correction

### 🔍 **Advanced Search Capabilities**
- **Hybrid Search** - Combines semantic (vector) + keyword (BM25) search
- **Cross-Encoder Reranking** - Neural reranker for precision
- **Multi-Strategy Retrieval** - Precise, broad, or hybrid modes
- **Real-time Thinking Steps** - Watch agents reason in real-time

### 📊 **Knowledge Graph Visualization**
- Automatic entity extraction during ingestion
- Interactive graph visualization for each document
- Displays entities, keywords, and topics as connected nodes

### 📁 **Document Processing**
- Supports: PDF, DOCX, TXT, MD, XLSX, CSV, Images (PNG, JPG, etc.)
- AI-powered summarization and keyword extraction
- Vision model integration for image understanding
- Batch processing with progress tracking

### 💾 **Persistent Memory**
- Conversation history across sessions
- Episodic memory for context-aware responses
- User preference learning (optional)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                         │
│  ┌──────────────┐ ┌───────────────┐ ┌─────────────────────────┐  │
│  │ ChatInterface│ │DocumentSelector│ │   EntityGraphModal     │  │
│  └──────────────┘ └───────────────┘ └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │ HTTP/SSE
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   EnhancedOrchestrator                    │   │
│  │  ┌────────┐ ┌──────────┐ ┌─────────┐ ┌───────────────┐   │   │
│  │  │ Athena │ │ Socrates │ │ Proteus │ │ Diogenes      │   │   │
│  │  │(Intent)│ │ (Query)  │ │(Strategy│ │ (Critic)      │   │   │
│  │  └────────┘ └──────────┘ └─────────┘ └───────────────┘   │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌────────────────┐ ┌───────────────┐ ┌─────────────────────┐   │
│  │ OpenSearchClient│ │ CrossEncoder  │ │  KnowledgeGraph    │   │
│  │  (Hybrid Search)│ │  Reranker    │ │  (Entity Store)    │   │
│  └────────────────┘ └───────────────┘ └─────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                  │
│  ┌────────────────┐ ┌───────────────┐ ┌─────────────────────┐   │
│  │   OpenSearch   │ │    SQLite     │ │      Ollama         │   │
│  │  (Vector+BM25) │ │ (Memory, Auth)│ │  (LLM + Vision)     │   │
│  └────────────────┘ └───────────────┘ └─────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **Docker** (for OpenSearch)
- **Ollama** (for local LLM)

### 1. Clone & Setup

```bash
git clone https://github.com/yourusername/LocaLense_V2.git
cd LocaLense_V2

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Start OpenSearch

```bash
docker-compose up -d
```

### 3. Start Ollama & Pull Models

```bash
# Install Ollama from https://ollama.ai
ollama pull qwen2.5:7b      # Text model
ollama pull llava:7b         # Vision model (optional)
```

### 4. Start Backend

```bash
python -m uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
```

### 5. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### 6. Access the App

Open **http://localhost:5173** in your browser.

---

## 📂 Project Structure

```
LocaLense_V2/
├── backend/
│   ├── agents/                 # AI Agents
│   │   ├── query_classifier.py     # Athena - Intent classification
│   │   ├── adaptive_retriever.py   # Proteus - Strategy selection
│   │   ├── graph_rag_agent.py      # Apollo - Knowledge graph
│   │   ├── reasoning_planner.py    # Odysseus - Multi-hop reasoning
│   │   ├── confidence_scorer.py    # Themis - Confidence scoring
│   │   ├── retrieval_controller.py # Sisyphus - Iterative retrieval
│   │   ├── critic_agent.py         # Diogenes - Quality critic
│   │   ├── explanation_agent.py    # Hermes - Result explanation
│   │   ├── analysis_agent.py       # Aristotle - Deep analysis
│   │   └── document_agents/        # Daedalus pipeline
│   ├── orchestration/
│   │   └── orchestrator.py     # Zeus - Main orchestrator
│   ├── graph/
│   │   └── knowledge_graph.py  # Entity knowledge graph
│   ├── memory/
│   │   ├── memory_manager.py   # Session memory
│   │   └── episodic_memory.py  # Long-term memory
│   ├── ranking/
│   │   └── personalized_ranker.py  # User preference learning
│   ├── utils/
│   │   ├── llm_utils.py        # LLM call utilities
│   │   └── model_manager.py    # Model loading/unloading
│   ├── api.py                  # FastAPI endpoints
│   ├── opensearch_client.py    # Search client
│   ├── reranker.py             # Cross-encoder reranker
│   ├── ingestion.py            # Document processing
│   └── feedback.py             # User feedback system
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── ChatInterface.jsx       # Main chat UI
│       │   ├── EntityGraphModal.jsx    # Knowledge graph view
│       │   ├── DocumentSelector.jsx    # Document attachment
│       │   ├── SettingsPanel.jsx       # Settings & indexing
│       │   └── OnboardingWizard.jsx    # First-time setup
│       └── App.jsx
├── config.yaml                 # Configuration
├── docker-compose.yml          # OpenSearch setup
└── requirements.txt            # Python dependencies
```

---

## ⚙️ Configuration

Edit `config.yaml` to customize:

```yaml
ollama:
  base_url: "http://localhost:11434"
  text_model:
    name: "qwen2.5:7b"
  vision_model:
    name: "llava:7b"

opensearch:
  host: "localhost"
  port: 9200
  index_name: "locallens_docs"
  auth:
    username: "admin"
    password: "your_password"

search:
  hybrid:
    enabled: true
    vector_weight: 0.6
    bm25_weight: 0.4
  reranker:
    enabled: true
    model: "cross-encoder/ms-marco-MiniLM-L-6-v2"

watcher:
  watch_directories:
    - "C:/Users/your_user/Documents"
  supported_extensions:
    - ".pdf"
    - ".docx"
    - ".txt"
```

---

## 🎯 Usage

### Basic Search
Type a question in the search bar:
- "Find documents about machine learning"
- "Show me invoices from 2024"
- "What does the report say about revenue?"

### Document Chat
1. Click **📎 Attach Documents** to select specific documents
2. Ask questions about the attached documents
3. The Daedalus agent will process them specifically

### Knowledge Graph
1. Search for documents
2. Click the **📊 Graph** button on any result
3. View entities, keywords, and topics as a visual graph

### Indexing Documents
1. Click the **⚙️** settings icon
2. Go to **Indexing** tab
3. Enter folder path and click **Start Indexing**

---

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/search/enhanced` | POST | Main search with AI agents |
| `/documents/{id}/entities` | GET | Get document entities for graph |
| `/documents/{id}/preview` | GET | Preview document content |
| `/index/start` | POST | Start document indexing |
| `/conversations` | GET | List user conversations |
| `/feedback` | POST | Submit result feedback |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **OpenSearch** - Vector and text search engine
- **Ollama** - Local LLM inference
- **LangGraph** - Agent workflow orchestration
- **Sentence-Transformers** - Embedding models
- **FastAPI** - High-performance API framework
- **React** - Frontend framework

---

<p align="center">
  Made with ❤️ for local-first AI
</p>
