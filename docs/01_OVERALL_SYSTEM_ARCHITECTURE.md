# VANTAGE - Overall System Architecture

## Table of Contents
- [System Overview](#system-overview)
- [High-Level Architecture](#high-level-architecture)
- [Component Interaction Map](#component-interaction-map)
- [Technology Stack](#technology-stack)
- [Deployment Architecture](#deployment-architecture)

---

## System Overview

**Vantage (LocalLens)** is a local-first, AI-powered semantic document search and knowledge management system that combines:
- Multi-agent orchestration using Greek mythology-named specialized agents
- Hybrid search (vector + BM25) with cross-encoder reranking
- Knowledge graphs for entity relationship tracking
- Multi-tier memory systems for learning and personalization
- Real-time streaming responses with agent thinking visualization

**Core Philosophy**: All processing happens locally on the user's machine using local LLMs (Ollama) and embedding models (Sentence Transformers), ensuring privacy and data sovereignty.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE LAYER                                │
│                                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                   React Frontend (Port 5173/3000)                        │   │
│  │                                                                           │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │   │
│  │  │ Chat         │  │ Document     │  │ Knowledge    │  │ Memory      │ │   │
│  │  │ Interface    │  │ Selector     │  │ Graph        │  │ Explorer    │ │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ │   │
│  │                                                                           │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │   │
│  │  │ Agent        │  │ Indexing     │  │ Settings     │  │ Features    │ │   │
│  │  │ Thinking     │  │ Progress     │  │ Panel        │  │ Showcase    │ │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ │   │
│  │                                                                           │   │
│  │                   WebSockets (SSE) for Real-time Updates                 │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        ▲
                                        │ HTTP/REST + SSE
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              API GATEWAY LAYER                                   │
│                                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                FastAPI Application (Port 8000)                           │   │
│  │                                                                           │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐           │   │
│  │  │  Search   │  │ Document  │  │  Memory   │  │  File     │           │   │
│  │  │ Endpoints │  │ Endpoints │  │ Endpoints │  │  Watcher  │           │   │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────┘           │   │
│  │                                                                           │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐           │   │
│  │  │   Auth    │  │ Feedback  │  │  Health   │  │ Streaming │           │   │
│  │  │ Endpoints │  │ Endpoints │  │  Check    │  │    SSE    │           │   │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────┘           │   │
│  │                                                                           │   │
│  │              CORS Middleware │ Authentication │ Logging                  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        ▲
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATION & AGENT LAYER                              │
│                                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    ZEUS ORCHESTRATOR (LangGraph)                         │   │
│  │                                                                           │   │
│  │              State Management │ Workflow Routing │ Parallelization       │   │
│  │                                                                           │   │
│  │  ┌───────────────────────────────────────────────────────────────────┐  │   │
│  │  │                      Athena (Query Classifier)                     │  │   │
│  │  │                                                                     │  │   │
│  │  │      Routes to: ┌──────────────┐  ┌──────────────┐              │  │   │
│  │  │                 │  Athena Path │  │ Daedalus Path│              │  │   │
│  │  │                 │ (No Attach.) │  │(w/ Documents)│              │  │   │
│  │  │                 └──────────────┘  └──────────────┘              │  │   │
│  │  └───────────────────────────────────────────────────────────────────┘  │   │
│  │                                                                           │   │
│  │  ┌──────────────────────────────────────────────────────────────────┐   │   │
│  │  │              SPECIALIZED AGENTS (15+ Agents)                      │   │   │
│  │  │                                                                    │   │   │
│  │  │  [Apollo]      [Odysseus]    [Proteus]     [Themis]              │   │   │
│  │  │  Graph RAG     Reasoning     Adaptive      Confidence            │   │   │
│  │  │                Planner       Retriever     Scorer                │   │   │
│  │  │                                                                    │   │   │
│  │  │  [Diogenes]    [Socrates]    [Aristotle]   [Thoth]               │   │   │
│  │  │  Critic        Clarification  Analysis     Summarization         │   │   │
│  │  │                                                                    │   │   │
│  │  │  [Hermes]      [Sisyphus]                                         │   │   │
│  │  │  Explanation   Retrieval Controller                              │   │   │
│  │  └──────────────────────────────────────────────────────────────────┘   │   │
│  │                                                                           │   │
│  │  ┌──────────────────────────────────────────────────────────────────┐   │   │
│  │  │            DOCUMENT AGENTS (Daedalus Orchestrator)                │   │   │
│  │  │                                                                    │   │   │
│  │  │  [Prometheus]  [Hypatia]     [Mnemosyne]                          │   │   │
│  │  │  Reader        Analyzer      Extractor                            │   │   │
│  │  └──────────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        ▲
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           CORE SERVICES LAYER                                    │
│                                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐              │
│  │  SEARCH ENGINE   │  │  MEMORY SYSTEM   │  │ KNOWLEDGE GRAPH  │              │
│  │                  │  │                  │  │                  │              │
│  │  ┌────────────┐  │  │  ┌────────────┐  │  │  ┌────────────┐  │              │
│  │  │ OpenSearch │  │  │  │  Session   │  │  │  │  NetworkX  │  │              │
│  │  │  Client    │  │  │  │  Memory    │  │  │  │   Graph    │  │              │
│  │  └────────────┘  │  │  └────────────┘  │  │  └────────────┘  │              │
│  │                  │  │                  │  │                  │              │
│  │  ┌────────────┐  │  │  ┌────────────┐  │  │  ┌────────────┐  │              │
│  │  │  Reranker  │  │  │  │  Episodic  │  │  │  │  Entity    │  │              │
│  │  │ (CrossEnc.)│  │  │  │  Memory    │  │  │  │  Resolver  │  │              │
│  │  └────────────┘  │  │  └────────────┘  │  │  └────────────┘  │              │
│  │                  │  │                  │  │                  │              │
│  │  ┌────────────┐  │  │  ┌────────────┐  │  │  ┌────────────┐  │              │
│  │  │   Hybrid   │  │  │  │Procedural  │  │  │  │Relationship│  │              │
│  │  │   Search   │  │  │  │  Memory    │  │  │  │ Extractor  │  │              │
│  │  └────────────┘  │  │  └────────────┘  │  │  └────────────┘  │              │
│  │                  │  │                  │  │                  │              │
│  │  • Vector (70%)  │  │  ┌────────────┐  │  │  • Entity Types│              │
│  │  • BM25 (30%)    │  │  │User Profile│  │  │  • Relations   │              │
│  │  • RRF Fusion    │  │  └────────────┘  │  │  • Multi-hop   │              │
│  │                  │  │                  │  │  • Persistence │              │
│  │                  │  │  ┌────────────┐  │  │                  │              │
│  │                  │  │  │  Agentic   │  │  │                  │              │
│  │                  │  │  │  Memory    │  │  │                  │              │
│  │                  │  │  │  (A-mem)   │  │  │                  │              │
│  │                  │  │  └────────────┘  │  │                  │              │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘              │
│                                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐              │
│  │INGESTION PIPELINE│  │  FILE WATCHER    │  │   FEEDBACK SYS   │              │
│  │                  │  │                  │  │                  │              │
│  │  • Extract       │  │  • Monitor Dirs  │  │  • User Ratings  │              │
│  │  • Summarize     │  │  • Auto-Reindex  │  │  • Learning      │              │
│  │  • Embed         │  │  • Debounce 3s   │  │  • Personalize   │              │
│  │  • Index         │  │  • Batch Process │  │  • Analytics     │              │
│  │  • Graph Extract │  │                  │  │                  │              │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        ▲
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         AI & MACHINE LEARNING LAYER                              │
│                                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐              │
│  │  OLLAMA SERVER   │  │ SENTENCE TRANS.  │  │  CROSS-ENCODER   │              │
│  │  (Port 11434)    │  │                  │  │                  │              │
│  │                  │  │  ┌────────────┐  │  │  ┌────────────┐  │              │
│  │  ┌────────────┐  │  │  │nomic-embed │  │  │  │ms-marco-   │  │              │
│  │  │ qwen3-vl   │  │  │  │  -text     │  │  │  │MiniLM-L6   │  │              │
│  │  │   :8b      │  │  │  │            │  │  │  │            │  │              │
│  │  │            │  │  │  │768 dims    │  │  │  │Reranking   │  │              │
│  │  │Vision+Text │  │  │  └────────────┘  │  │  └────────────┘  │              │
│  │  │Unified LLM │  │  │                  │  │                  │              │
│  │  └────────────┘  │  │  • Documents     │  │  • Top 50→5     │              │
│  │                  │  │  • Queries       │  │  • Score Docs   │              │
│  │  • Summarize     │  │  • Fast & Stable │  │  • Precision    │              │
│  │  • Analyze       │  │  • Local         │  │  • Improve Top-K│              │
│  │  • Generate      │  │                  │  │                  │              │
│  │  • Vision OCR    │  │                  │  │                  │              │
│  │  • Temp 0.3-0.7  │  │                  │  │                  │              │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        ▲
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            DATA PERSISTENCE LAYER                                │
│                                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐              │
│  │   OPENSEARCH     │  │     SQLITE       │  │      REDIS       │              │
│  │   (Port 9200)    │  │   DATABASES      │  │   (Port 6379)    │              │
│  │                  │  │                  │  │                  │              │
│  │  ┌────────────┐  │  │  ┌────────────┐  │  │  ┌────────────┐  │              │
│  │  │locallens_  │  │  │  │conversations│ │  │  │  Session   │  │              │
│  │  │  index     │  │  │  │    .db     │  │  │  │   Cache    │  │              │
│  │  │            │  │  │  └────────────┘  │  │  └────────────┘  │              │
│  │  │• Documents │  │  │                  │  │                  │              │
│  │  │• Vectors   │  │  │  ┌────────────┐  │  │  • TTL: 1hr    │              │
│  │  │• Metadata  │  │  │  │  memory.db │  │  │  • Sliding Win │              │
│  │  │• Full Text │  │  │  └────────────┘  │  │  • 10 turns    │              │
│  │  └────────────┘  │  │                  │  │                  │              │
│  │                  │  │  ┌────────────┐  │  │                  │              │
│  │  • k-NN Plugin   │  │  │  graph.db  │  │  │                  │              │
│  │  • BM25          │  │  └────────────┘  │  │                  │              │
│  │  • Hybrid Search │  │                  │  │                  │              │
│  │                  │  │  ┌────────────┐  │  │                  │              │
│  │                  │  │  │episodes.db │  │  │                  │              │
│  │                  │  │  └────────────┘  │  │                  │              │
│  │                  │  │                  │  │                  │              │
│  │                  │  │  ┌────────────┐  │  │                  │              │
│  │                  │  │  │  users.json│  │  │                  │              │
│  │                  │  │  └────────────┘  │  │                  │              │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘              │
│                                                                                   │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                         LOCAL FILE SYSTEM                                 │   │
│  │                                                                            │   │
│  │  • Uploaded Documents (backend/uploads/)                                  │   │
│  │  • Indexed Documents (User-selected directories)                          │   │
│  │  • Logs (logs/)                                                            │   │
│  │  • Configuration (config.yaml)                                             │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Interaction Map

### Request Flow Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          REQUEST PROCESSING FLOW                              │
└──────────────────────────────────────────────────────────────────────────────┘

USER ACTION: Submit Query "What are the key findings in my research papers?"
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 1. FRONTEND (React)                                                  │
│    • ChatInterface.jsx captures query                                │
│    • Establishes SSE connection for streaming                        │
│    • Sends POST /search with { query, top_k, session_id }           │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. API GATEWAY (FastAPI)                                             │
│    • api.py receives request at /search endpoint                     │
│    • Validates SearchRequest schema (Pydantic)                       │
│    • Initializes SSE stream for step-by-step updates                │
│    • Passes to Zeus Orchestrator                                     │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. ORCHESTRATOR (Zeus - LangGraph)                                   │
│    • Load session context from Memory Manager                        │
│    • Create workflow state                                           │
│    • Call Athena for query classification                            │
│    • Athena returns: DOCUMENT_SEARCH                                 │
│    • Route to Athena Path (document search workflow)                 │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. SEARCH ENGINE                                                     │
│    a. Query Expansion (Odysseus - optional)                          │
│       • Expands "key findings" → ["key findings", "main results",    │
│         "conclusions", "discoveries"]                                │
│                                                                       │
│    b. OpenSearch Client                                              │
│       • Vector Search: Embed query using Sentence-Transformers       │
│       • BM25 Search: Full-text keyword search                        │
│       • Hybrid combination (70% vector + 30% BM25)                   │
│       • RRF (Reciprocal Rank Fusion) to merge results               │
│       • Returns top 50 candidates                                    │
│       → SSE Event: "Retrieved 50 documents from hybrid search"       │
│                                                                       │
│    c. Reranker                                                       │
│       • Cross-encoder scores all 50 documents                        │
│       • Ranks by relevance to original query                         │
│       • Returns top 5 documents                                      │
│       → SSE Event: "Reranked to top 5 most relevant documents"       │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 5. KNOWLEDGE GRAPH (Apollo - optional)                               │
│    • Extract entities from top documents                             │
│    • Traverse graph for related entities                             │
│    • Expand context with connected knowledge                         │
│    → SSE Event: "Expanded context with 12 related entities"          │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 6. RESPONSE GENERATION                                               │
│    a. LLM Call (Ollama - qwen3-vl:8b)                                │
│       • Prompt: Query + Top 5 documents + Instructions               │
│       • Stream response tokens                                       │
│       → SSE Events: Streaming response text                          │
│                                                                       │
│    b. Quality Control                                                │
│       • Themis: Confidence scoring (0-1)                             │
│       • Diogenes: Hallucination detection                            │
│       → SSE Event: "Confidence score: 0.87"                          │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 7. POST-PROCESSING                                                   │
│    • Format citations and sources                                    │
│    • Store interaction in Episodic Memory                            │
│    • Update User Profile (interaction patterns)                      │
│    • Save to Conversation Database                                   │
│    → SSE Event: "Response complete"                                  │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 8. FRONTEND RENDERING                                                │
│    • Display response with markdown formatting                       │
│    • Show agent thinking steps timeline                              │
│    • Render confidence graph                                         │
│    • Display source document cards with highlights                   │
│    • Update conversation history sidebar                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Backend Stack

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Web Framework** | FastAPI | 0.121.3 | REST API & SSE streaming |
| **ASGI Server** | Uvicorn | 0.38.0 | Async web server |
| **Orchestration** | LangGraph | 1.0.3 | State machine for agent workflows |
| **LLM Integration** | LangChain | 1.0.8 | LLM abstraction & chains |
| **Local LLM** | Ollama | 0.6.1 | Local inference (qwen3-vl:8b) |
| **Search Engine** | OpenSearch | 3.0.0 | Hybrid search (vector + BM25) |
| **Embeddings** | Sentence-Transformers | 5.1.2 | nomic-embed-text (768d) |
| **Reranking** | CrossEncoder | (ST) | ms-marco-MiniLM-L-6-v2 |
| **Graph Database** | NetworkX | 3.4.2 | Knowledge graph storage |
| **Cache** | Redis | 7.1.0 | Session memory |
| **Database** | SQLite | 3.x | Conversations, memory, profiles |
| **ORM** | SQLAlchemy | 2.0.44 | Database abstraction |
| **File Watching** | Watchdog | 6.0.0 | Auto-reindexing |
| **Logging** | Loguru | 0.7.3 | Structured logging |
| **Config** | PyYAML | 6.0.3 | Configuration management |

### Frontend Stack

| Category | Technology | Version | Purpose |
|----------|-----------|---------|---------|
| **Framework** | React | 18.2.0 | UI components |
| **Build Tool** | Vite | 5.0.8 | Fast dev server & bundling |
| **Graph Viz** | React Force Graph 2D | 1.29.0 | Knowledge graph rendering |
| **Markdown** | React Markdown | 9.1.0 | Response formatting |
| **Styling** | CSS3 | - | Custom styling (no frameworks) |

### AI/ML Stack

| Component | Model | Details |
|-----------|-------|---------|
| **LLM** | qwen3-vl:8b | Vision-language unified model |
| **Embeddings** | nomic-embed-text | 768 dimensions, local |
| **Reranker** | ms-marco-MiniLM-L-6-v2 | Cross-encoder for precision |

### Infrastructure

| Service | Port | Purpose |
|---------|------|---------|
| OpenSearch | 9200 | Search & indexing |
| OpenSearch Dashboards | 5601 | Web UI |
| Redis | 6379 | Session cache |
| Ollama | 11434 | LLM inference |
| FastAPI | 8000 | Backend API |
| React Dev | 5173 | Frontend (dev) |

---

## Deployment Architecture

### Docker Compose Setup

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOCKER HOST MACHINE                           │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  opensearch-node                                            │ │
│  │  • Image: opensearchproject/opensearch:2.11.0              │ │
│  │  • Ports: 9200:9200, 9600:9600                             │ │
│  │  • Plugins: k-NN for vector search                         │ │
│  │  • Volume: opensearch-data                                 │ │
│  │  • Env: Single-node cluster, JVM heap 2GB                  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  opensearch-dashboards                                      │ │
│  │  • Image: opensearchproject/opensearch-dashboards:2.11.0   │ │
│  │  • Ports: 5601:5601                                         │ │
│  │  • Links: opensearch-node                                   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  redis                                                       │ │
│  │  • Image: redis:7-alpine                                     │ │
│  │  • Ports: 6379:6379                                          │ │
│  │  • Volume: redis-data                                        │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    LOCAL HOST MACHINE                            │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Ollama Server                                              │ │
│  │  • Port: 11434                                              │ │
│  │  • Model: qwen3-vl:8b                                       │ │
│  │  • GPU: CUDA support                                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  FastAPI Backend                                            │ │
│  │  • Port: 8000                                               │ │
│  │  • Process: uvicorn backend.api:app                         │ │
│  │  • Workers: 1 (async)                                       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  React Frontend                                             │ │
│  │  • Dev Port: 5173 (Vite)                                    │ │
│  │  • Prod: Static files served by FastAPI                     │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Startup Sequence

```
1. Start Docker services
   └─> docker-compose up -d
       ├─> OpenSearch (wait for healthy)
       ├─> Redis (immediate)
       └─> Dashboards (after OpenSearch)

2. Start Ollama (if not running)
   └─> ollama serve
       └─> Pull model: ollama pull qwen3-vl:8b

3. Start Backend
   └─> uvicorn backend.api:app --reload --port 8000
       ├─> Load config.yaml
       ├─> Initialize OpenSearch client
       ├─> Connect to Redis
       ├─> Initialize SQLite databases
       ├─> Load agents and orchestrator
       └─> Start FastAPI server

4. Start Frontend (development)
   └─> cd frontend && npm run dev
       └─> Vite dev server on port 5173

5. Access Application
   └─> http://localhost:5173 (dev) or http://localhost:8000 (prod)
```

---

## Data Flow Patterns

### 1. Document Ingestion Flow

```
User selects directory
    ↓
POST /index
    ↓
IngestionPipeline
    ├─> For each file:
    │   ├─> Extract content (PDF/DOCX/Image/etc.)
    │   ├─> Generate summary (Ollama)
    │   ├─> Extract keywords/entities (Ollama)
    │   ├─> Generate embedding (Sentence-Transformers)
    │   ├─> Index in OpenSearch
    │   └─> Extract entities → Knowledge Graph
    └─> Stream progress via SSE
```

### 2. Search Query Flow

```
User query
    ↓
Athena classification
    ↓
Route decision
    ├─> DOCUMENT_SEARCH
    │   ├─> Hybrid search (OpenSearch)
    │   ├─> Rerank (CrossEncoder)
    │   ├─> Graph expansion (Apollo)
    │   └─> LLM generation (Ollama)
    │
    ├─> GENERAL_KNOWLEDGE
    │   └─> Direct LLM call (Ollama)
    │
    └─> DOCUMENT_ATTACHED
        └─> Daedalus orchestrator
            ├─> Prometheus (read)
            ├─> Hypatia (analyze)
            └─> Mnemosyne (extract)
```

### 3. Memory Flow

```
Query → Response Cycle
    ↓
Session Memory (Redis, 1hr TTL)
    ├─> Current conversation context
    └─> Sliding window (10 turns)
    ↓
Episodic Memory (SQLite)
    ├─> Past query-response pairs
    └─> Pattern learning
    ↓
User Profile (SQLite)
    ├─> Interaction patterns
    └─> Preferences
    ↓
Procedural Memory (SQLite + in-memory)
    └─> Learned behaviors
    ↓
Agentic Memory (A-mem)
    ├─> Structured notes
    ├─> Evolution & consolidation
    └─> Proactive suggestions
```

---

## Security & Privacy Architecture

### Local-First Design

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER'S LOCAL MACHINE                          │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Documents  │  │   Vectors    │  │    Models    │          │
│  │    (Local)   │  │   (Local)    │  │   (Local)    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
│  NO EXTERNAL API CALLS │ NO CLOUD UPLOADS │ COMPLETE PRIVACY    │
└─────────────────────────────────────────────────────────────────┘
```

### Authentication Flow

```
User Login
    ↓
POST /auth/login
    ↓
Verify credentials (SQLite)
    ↓
Generate session token
    ↓
Store in Redis (TTL: 24hr)
    ↓
Return token to frontend
    ↓
Frontend stores in localStorage
    ↓
All requests include Authorization header
```

---

## Monitoring & Observability

### Logging Architecture

```
Application Logs
    ↓
Loguru Handler
    ├─> Console (INFO level)
    ├─> File logs/app.log (rotation: 10MB)
    └─> Session-specific logs (logs/ingestion_*.log)

SSE Streaming
    ├─> Step-by-step agent actions
    ├─> Search results
    ├─> Confidence scores
    └─> Error messages
```

### Health Checks

```
GET /health
    ├─> Check OpenSearch connectivity
    ├─> Check Redis connectivity
    ├─> Check Ollama availability
    ├─> Check database integrity
    └─> Return health status + metrics
```

---

## Performance Characteristics

| Operation | Latency | Bottleneck | Optimization |
|-----------|---------|------------|--------------|
| Query classification | 200-500ms | LLM inference | Cache common patterns |
| Hybrid search | 50-150ms | OpenSearch I/O | Index optimization |
| Reranking (50→5) | 100-300ms | Cross-encoder | Reduce candidate pool |
| LLM generation | 1-5s | Token generation | Stream responses |
| Document ingestion | 5-30s/doc | LLM summarization | Batch processing |
| Embedding generation | 100-500ms | Model inference | GPU acceleration |

---

## Scalability Considerations

### Current Limitations
- Single-node OpenSearch (suitable for personal use)
- Single FastAPI worker (async handles concurrency)
- Local LLM (limited by GPU memory)
- SQLite (suitable for < 100K documents)

### Future Scaling Paths
1. **OpenSearch Cluster**: Multi-node for larger document sets
2. **Redis Cluster**: Distributed session storage
3. **PostgreSQL**: Replace SQLite for concurrent writes
4. **Load Balancer**: Multiple FastAPI workers
5. **Model Serving**: Dedicated inference servers

---

## Configuration Management

### config.yaml Structure

```yaml
ollama:
  base_url: http://localhost:11434
  unified_model: qwen3-vl:8b
  temperature: 0.3

opensearch:
  hosts: localhost:9200
  index_name: locallens_index

models:
  embedding_model: nomic-embed-text
  reranking_model: ms-marco-MiniLM-L-6-v2

search:
  hybrid_weights:
    vector: 0.7
    bm25: 0.3
  reranking:
    enabled: true
    top_k: 5

orchestration:
  langgraph_enabled: true
  max_concurrent_agents: 3
  timeout: 60

memory:
  session_backend: redis
  session_ttl: 3600
  consolidation_interval: 3600
```

---

## Error Handling & Resilience

### Fallback Strategies

```
Primary: Redis Session Memory
    ↓ (on failure)
Fallback: In-memory dictionary

Primary: OpenSearch
    ↓ (on failure)
Fallback: Error message + retry logic

Primary: Ollama LLM
    ↓ (on failure)
Fallback: Error message + cached response (if available)

Primary: Cross-encoder reranking
    ↓ (on failure)
Fallback: Use search scores only
```

### Retry Logic
- Max retries: 2
- Exponential backoff: 1s, 2s, 4s
- Circuit breaker: Disable failing component after 5 consecutive failures

---

## Version History

| Version | Release Date | Key Changes |
|---------|--------------|-------------|
| 2.0.0 | 2025-01 | LangGraph orchestration, unified qwen3-vl model |
| 1.5.0 | 2024-12 | Agentic memory system, memory explorer UI |
| 1.0.0 | 2024-11 | Initial release with multi-agent system |

---

**Document Version**: 1.0
**Last Updated**: 2025-12-31
**Architecture Owner**: Vantage Development Team
