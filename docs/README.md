# Vantage Architecture Documentation

Welcome to the comprehensive architecture documentation for the Vantage (LocalLens) project. This documentation provides detailed technical specifications, design decisions, and component breakdowns for the entire system.

## 📚 Documentation Index

### 1. [Overall System Architecture](./01_OVERALL_SYSTEM_ARCHITECTURE.md)
**Overview of the entire Vantage system**
- High-level architecture diagrams
- Component interaction maps
- Technology stack breakdown
- Deployment architecture
- Data flow patterns
- Performance characteristics
- Security & privacy architecture

**Best for**: Getting a high-level understanding of the entire system, technology choices, and how components interact.

---

### 2. [Backend Architecture](./02_BACKEND_ARCHITECTURE.md)
**Deep dive into the backend components**
- API layer architecture (FastAPI)
- Core services (OpenSearch, Reranker)
- Search engine architecture (Hybrid search flow)
- Document processing pipeline
- File watcher system
- Authentication & security
- Data models & schemas

**Best for**: Understanding the backend API, search implementation, document processing, and data storage.

---

### 3. [Agent System Architecture](./03_AGENT_SYSTEM_ARCHITECTURE.md)
**Multi-agent orchestration system**
- Zeus Orchestrator (LangGraph)
- Query classification & routing (Athena)
- 15+ specialized agents (Apollo, Odysseus, Themis, Diogenes, etc.)
- Document processing agents (Daedalus, Prometheus, Hypatia, Mnemosyne)
- Agent communication protocols
- State management

**Best for**: Understanding how agents collaborate, workflow routing, and the Greek mythology-themed agent roles.

---

### 4. [Memory System Architecture](./04_MEMORY_SYSTEM_ARCHITECTURE.md)
**Multi-tier memory architecture**
- Session Memory (Redis, Tier 1)
- Episodic Memory (SQLite, Tier 2)
- Procedural Memory (Tier 3)
- User Profile (Tier 4)
- Agentic Memory System (A-mem, Tier 5)
  - Note generation
  - Memory evolution
  - Consolidation & pruning
  - Proactive suggestions
- Memory Manager (Unified coordinator)

**Best for**: Understanding how the system learns, remembers, and personalizes responses.

---

### 5. [Frontend Architecture](./05_FRONTEND_ARCHITECTURE.md)
**React-based user interface**
- Component architecture & hierarchy
- State management (React hooks)
- Real-time communication (SSE)
- Component details (ChatInterface, Graph visualization, Memory explorer)
- Styling & theming (Dark mode)
- Performance optimizations
- Keyboard shortcuts

**Best for**: Understanding the UI/UX implementation, component structure, and frontend optimizations.

---

### 6. [Data Flow & Request Lifecycle](./06_DATA_FLOW_AND_REQUEST_LIFECYCLE.md)
**End-to-end request processing**
- Complete search query flow (with timings)
- Document attachment flow
- Feedback loop
- Session management
- Error handling
- Performance analysis & bottlenecks

**Best for**: Understanding the complete lifecycle of a user query from input to response, including performance characteristics.

---

### 7. [Ingestion Pipeline Architecture](./07_INGESTION_PIPELINE_ARCHITECTURE.md)
**Document processing and indexing**
- File discovery & validation
- Content extraction by file type (PDF, DOCX, Images, etc.)
- LLM-based summarization (Ollama qwen3-vl:8b)
- Embedding generation (Sentence-Transformers)
- Knowledge graph extraction
- OpenSearch indexing
- File watcher integration
- Error handling & recovery

**Best for**: Understanding how documents are processed, indexed, and made searchable.

---

## 🏗️ Architecture Overview

Vantage is a **local-first AI-powered semantic document search system** with the following key features:

### Core Components
1. **Backend (Python/FastAPI)**: REST API with SSE streaming
2. **Frontend (React/Vite)**: Interactive chat interface with visualizations
3. **Multi-Agent System**: 15+ specialized agents using LangGraph orchestration
4. **Memory System**: 5-tier memory architecture for learning and personalization
5. **Search Engine**: Hybrid search (vector + BM25) with cross-encoder reranking
6. **Knowledge Graph**: NetworkX-based entity-relationship tracking
7. **Ingestion Pipeline**: Automated document processing and indexing

### Technology Stack

**Backend:**
- FastAPI (API), LangGraph (Orchestration), Ollama (LLM)
- OpenSearch (Search), Sentence-Transformers (Embeddings)
- SQLite (Persistence), Redis (Sessions)

**Frontend:**
- React 18, Vite 5, React Force Graph 2D
- React Markdown, Custom hooks

**AI/ML:**
- qwen3-vl:8b (Unified vision-language model)
- nomic-embed-text (768-dim embeddings)
- ms-marco-MiniLM-L-6-v2 (Cross-encoder reranking)

---

## 🎯 Design Principles

1. **Local-First**: All processing happens locally, no cloud dependencies
2. **Privacy-Focused**: User data never leaves the machine
3. **Hybrid Search**: Combines vector similarity (70%) + BM25 (30%)
4. **Summary-Based Indexing**: LLM-generated summaries for better searchability
5. **Multi-Agent Collaboration**: Specialized agents for different tasks
6. **Learning & Adaptation**: Memory systems for personalization
7. **Real-Time Streaming**: SSE for live progress updates

---

## 📊 Performance Characteristics

| Operation | Typical Latency | Bottleneck |
|-----------|----------------|------------|
| Query Classification | 200-400ms | LLM inference |
| Hybrid Search | 50-150ms | OpenSearch I/O |
| Reranking (50→5) | 100-300ms | Cross-encoder |
| LLM Response | 2-5 seconds | Token generation |
| Document Ingestion | 5-30s/doc | LLM summarization |

**Total Query Time**: 2.9-6.6 seconds (typical: 3.5-4.5 seconds)

---

## 🔄 Request Flow Summary

```
User Query
  ↓
Frontend (React)
  ↓
FastAPI API Gateway
  ↓
Memory Context Loading (5 tiers)
  ↓
Zeus Orchestrator (LangGraph)
  ↓
Athena Classifier → Route Decision
  ↓
Specialized Agents (Search, Graph, Quality Control)
  ↓
Ollama LLM (Response Generation)
  ↓
Memory Storage (All tiers)
  ↓
SSE Stream → Frontend
  ↓
User sees Response
```

---

## 🧩 Key Architectural Patterns

### 1. Multi-Agent Orchestration
- **Pattern**: State machine with LangGraph
- **Benefits**: Clear workflow, parallelization, error handling
- **Implementation**: `backend/orchestration/orchestrator.py`

### 2. Hybrid Search
- **Pattern**: Combine vector similarity + keyword matching
- **Benefits**: High recall + high precision
- **Implementation**: `backend/opensearch_client.py`

### 3. Memory Tiers
- **Pattern**: Hierarchical memory (short-term → long-term)
- **Benefits**: Fast access + learning capability
- **Implementation**: `backend/memory/`

### 4. SSE Streaming
- **Pattern**: Server-Sent Events for real-time updates
- **Benefits**: Low latency, live progress, better UX
- **Implementation**: `backend/streaming_steps.py` + Frontend EventSource

### 5. Dependency Injection
- **Pattern**: Singleton services injected into endpoints
- **Benefits**: Testability, lifecycle management
- **Implementation**: FastAPI `Depends()`

---

## 📁 Project Structure

```
Vantage/
├── backend/
│   ├── api.py                    # Main FastAPI application
│   ├── orchestration/            # Zeus orchestrator
│   ├── agents/                   # 15+ specialized agents
│   ├── memory/                   # 5-tier memory system
│   ├── graph/                    # Knowledge graph
│   ├── utils/                    # Utilities
│   └── uploads/                  # Uploaded files
│
├── frontend/
│   ├── src/
│   │   ├── components/           # React components
│   │   ├── hooks/                # Custom hooks
│   │   └── styles/               # CSS files
│   └── public/
│
├── config.yaml                   # System configuration
├── docker-compose.yml            # Infrastructure (OpenSearch, Redis)
└── docs/                         # This documentation
```

---

## 🚀 Getting Started

1. **Read** `01_OVERALL_SYSTEM_ARCHITECTURE.md` for a high-level overview
2. **Explore** specific components based on your interest (backend, frontend, agents, memory)
3. **Deep Dive** into data flow (`06_DATA_FLOW_AND_REQUEST_LIFECYCLE.md`) to understand request processing
4. **Reference** as needed when working on specific features

---

## 🔍 Quick Reference

### Searching for Specific Topics

| Topic | Document |
|-------|----------|
| API Endpoints | `02_BACKEND_ARCHITECTURE.md` |
| Agent Workflows | `03_AGENT_SYSTEM_ARCHITECTURE.md` |
| Memory Systems | `04_MEMORY_SYSTEM_ARCHITECTURE.md` |
| UI Components | `05_FRONTEND_ARCHITECTURE.md` |
| Search Algorithm | `02_BACKEND_ARCHITECTURE.md`, `06_DATA_FLOW_AND_REQUEST_LIFECYCLE.md` |
| Document Processing | `07_INGESTION_PIPELINE_ARCHITECTURE.md` |
| Performance Tuning | `06_DATA_FLOW_AND_REQUEST_LIFECYCLE.md` |
| Error Handling | `06_DATA_FLOW_AND_REQUEST_LIFECYCLE.md`, `07_INGESTION_PIPELINE_ARCHITECTURE.md` |

---

## 📝 Documentation Conventions

### Diagram Format
All architecture diagrams are created using **ASCII art boxes** for maximum compatibility and readability in markdown files.

### Code Examples
Code snippets include:
- Language specification (Python, JavaScript, etc.)
- Comments explaining key parts
- Realistic example data

### Timing Information
Performance metrics include:
- Minimum, average, and maximum latencies
- Bottleneck identification
- Optimization suggestions

---

## 🤝 Contributing

When updating the architecture:
1. Update the relevant documentation file(s)
2. Keep diagrams and text synchronized
3. Add performance impact notes if applicable
4. Update this README if adding new documents

---

## 📄 License

This documentation is part of the Vantage project.

---

## 🔗 Related Resources

- **Main README**: `../README.md`
- **Configuration**: `../config.yaml`
- **Code**: `../backend/` and `../frontend/`

---

**Last Updated**: 2025-12-31
**Documentation Version**: 1.0
**Author**: Vantage Development Team
