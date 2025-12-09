# Vantage 🔍

**AI-Powered Semantic Document Search & Chat Assistant**

Vantage is an intelligent document management system that uses semantic search, RAG (Retrieval-Augmented Generation), and a multi-agent AI architecture inspired by Greek mythology to help you find and interact with your documents naturally.

---

## 🌟 Features

### ✅ Core Capabilities
- **🔐 Secure Authentication** - Password-protected user accounts with session management
- **📁 Document Indexing** - Support for PDFs, Word, Excel, images, text files
- **🔍 Semantic Search** - AI-powered vector search with hybrid BM25 + embeddings
- **💬 Conversational UI** - Natural language queries with contextual understanding
- **📎 Document Attachment** - Attach documents to conversations for focused queries
- **🎯 Real-time Progress** - Visual feedback for indexing operations
- **👁️ File Watcher** - Auto-index new files in monitored folders
- **🌓 Dark Mode** - Beautiful dark theme support

### 🤖 Multi-Agent Architecture (Greek Pantheon)
- **⚡ Zeus** - Main orchestrator that routes all queries
- **🦉 Athena** - Intent classification and strategy
- **🏛️ Daedalus** - Document-specific query handling
- **📊 Aristotle** - Document analysis and comparison
- **🤔 Socrates** - Clarifying questions for ambiguous queries
- **📜 Thoth** - Multi-document summarization
- **📨 Hermes** - Result explanations
- **🔎 Diogenes** - Quality control and verification

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** & npm
- **OpenSearch 2.x** (or Docker)
- **Ollama** with models:
  - `nomic-embed-text` (embeddings)
  - `qwen2.5:7b` (LLM)

### Installation

```bash
# 1. Clone repository
git clone <repository-url>
cd LocaLense_V2

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install frontend dependencies
cd frontend && npm install && cd ..

# 4. Start OpenSearch (Docker)
docker-compose up -d

# 5. Start Ollama and pull models
ollama serve
ollama pull nomic-embed-text
ollama pull qwen2.5:7b
```

### Running Vantage

**Windows:**
```bash
run.bat
```

**Linux/Mac:**
```bash
chmod +x run.sh
./run.sh
```

**Manual Start:**
```bash
# Terminal 1: Backend
python -m backend.api

# Terminal 2: Frontend
cd frontend && npm run dev
```

### First Time Setup

1. Open http://localhost:5173
2. Choose **Sign Up** or **Sign In**
3. Index your documents:
   - Enter folder path (e.g., `C:\Users\You\Documents`)
   - Or upload files directly
4. Start searching!

---

## 🏗️ Architecture Overview

```
USER QUERY
    │
    ▼
┌──────────────────────────────────────────────────┐
│     ⚡ ZEUS (The Conductor)                       │
│     Main Orchestrator - Routes all queries       │
└──────────────────────────────────────────────────┘
    │
    ├─── Has attached documents? ───────────────────────┐
    │              │                                     │
    │              NO                                   YES
    │              │                                     │
    │              ▼                                     ▼
    │   ┌─────────────────────┐          ┌──────────────────────────────┐
    │   │ 🦉 ATHENA            │          │ 🏛️ DAEDALUS                  │
    │   │ The Strategist      │          │ The Architect               │
    │   │ Intent Classifier   │          │ Document Orchestrator       │
    │   └─────────────────────┘          └──────────────────────────────┘
    │              │                                     │
    │              ▼                                     ▼
    │   ┌─────────────────────┐          ┌──────────────────────────────┐
    │   │ Route by Intent:    │          │ 🔥 PROMETHEUS → Extract text │
    │   │ 📊 ARISTOTLE        │          │ 📚 HYPATIA → Analyze         │
    │   │ 🤔 SOCRATES         │          │ 🧠 MNEMOSYNE → Insights      │
    │   │ 📜 THOTH            │          └──────────────────────────────┘
    │   │ 📨 HERMES           │                          │
    │   │ 🔎 DIOGENES         │                          ▼
    │   └─────────────────────┘               Generate Answer
    │              │                                     │
    └──────────────┴─────────────────────────────────────┘
                                    │
                                    ▼
                                RESPONSE
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React 18 + Vite | Modern UI with dark mode |
| **Backend** | FastAPI | REST API + SSE streaming |
| **Vector DB** | OpenSearch | Hybrid vector + BM25 search |
| **LLM** | Ollama (qwen2.5:7b) | Local language model |
| **Embeddings** | nomic-embed-text | 768-dim text embeddings |
| **Storage** | SQLite | Users, conversations, memory |

---

## 📂 Project Structure

```
LocaLense_V2/
├── backend/
│   ├── api.py                    # FastAPI application
│   ├── orchestration/
│   │   └── orchestrator.py       # ⚡ Zeus - Main orchestrator
│   ├── agents/
│   │   ├── query_classifier.py   # 🦉 Athena - Intent classification
│   │   ├── analysis_agent.py     # 📊 Aristotle - Analysis
│   │   ├── clarification_agent.py# 🤔 Socrates - Clarification
│   │   ├── summarization_agent.py# 📜 Thoth - Summarization
│   │   ├── explanation_agent.py  # 📨 Hermes - Explanations
│   │   ├── critic_agent.py       # 🔎 Diogenes - Quality control
│   │   └── document_agents/
│   │       ├── daedalus_orchestrator.py  # 🏛️ Daedalus
│   │       ├── prometheus_reader.py      # 🔥 Prometheus
│   │       ├── hypatia_analyzer.py       # 📚 Hypatia
│   │       └── mnemosyne_extractor.py    # 🧠 Mnemosyne
│   ├── memory/                   # Session & user memory
│   └── ingestion.py              # Document processing
├── frontend/
│   └── src/components/           # React components
├── config.yaml                   # Configuration
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

---

## 🔧 Configuration

Edit `config.yaml`:

```yaml
# LLM Models
ollama:
  base_url: "http://localhost:11434"
  text_model:
    name: "qwen2.5:7b"
  vision_model:
    name: "qwen2.5vl:latest"

# OpenSearch
opensearch:
  host: "localhost"
  port: 9200

# Search Settings
search:
  hybrid:
    enabled: true
    vector_weight: 0.7
    bm25_weight: 0.3
```

---

## 📖 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed system architecture

---

## 🐛 Troubleshooting

**OpenSearch not connecting?**
```bash
curl http://localhost:9200
docker-compose logs opensearch
```

**Ollama models not found?**
```bash
ollama list
ollama pull nomic-embed-text
ollama pull qwen2.5:7b
```

**Frontend not loading?**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install && npm run dev
```

---

## 📝 License

MIT License

---

**Made with ❤️ using AI-powered semantic search and the wisdom of the Greek Pantheon**
