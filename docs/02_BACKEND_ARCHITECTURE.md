# VANTAGE - Backend Architecture (Deep Dive)

## Table of Contents
- [Backend Overview](#backend-overview)
- [API Layer Architecture](#api-layer-architecture)
- [Core Services](#core-services)
- [Search Engine Architecture](#search-engine-architecture)
- [Document Processing](#document-processing)
- [File Watcher System](#file-watcher-system)
- [Authentication & Security](#authentication--security)
- [Data Models & Schemas](#data-models--schemas)

---

## Backend Overview

The Vantage backend is a **FastAPI-based asynchronous application** that orchestrates multiple specialized services for semantic document search and knowledge management. It follows a **layered architecture** with clear separation of concerns.

### Directory Structure

```
backend/
├── api.py                          # Main FastAPI application (entry point)
├── ingestion.py                    # Document ingestion pipeline
├── opensearch_client.py            # Search engine client
├── reranker.py                     # Cross-encoder reranking
├── watcher.py                      # File system monitoring
├── watcher_endpoints.py            # File watcher API routes
├── feedback.py                     # User feedback storage
├── auth.py                         # Authentication logic
├── auth_endpoints.py               # Authentication routes
├── a2a_agent.py                    # Agent-to-Agent communication
├── mcp_tools.py                    # MCP tool registry
├── streaming_steps.py              # SSE streaming utilities
│
├── orchestration/
│   └── orchestrator.py             # Zeus (LangGraph orchestrator)
│
├── agents/                         # Specialized agents (15+)
│   ├── query_classifier.py
│   ├── graph_rag_agent.py
│   ├── reasoning_planner.py
│   ├── adaptive_retriever.py
│   ├── confidence_scorer.py
│   ├── critic_agent.py
│   ├── clarification_agent.py
│   ├── analysis_agent.py
│   ├── summarization_agent.py
│   ├── explanation_agent.py
│   ├── retrieval_controller.py
│   └── document_agents/
│       ├── daedalus_orchestrator.py
│       ├── prometheus_reader.py
│       ├── hypatia_analyzer.py
│       └── mnemosyne_extractor.py
│
├── graph/
│   ├── knowledge_graph.py
│   ├── entity_resolver.py
│   └── relationship_extractor.py
│
├── memory/
│   ├── memory_manager.py
│   ├── session_memory.py
│   ├── user_profile.py
│   ├── procedural_memory.py
│   ├── episodic_memory.py
│   ├── conversation_manager.py
│   ├── memory_reflector.py
│   └── agentic_memory/             # Advanced memory system
│
├── ranking/
│   └── personalized_ranker.py
│
├── utils/
│   ├── llm_utils.py
│   ├── model_manager.py
│   └── session_logger.py
│
└── uploads/                        # Uploaded files directory
```

---

## API Layer Architecture

### FastAPI Application Structure

**File**: `backend/api.py`

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                           │
│                         (api.py - Port 8000)                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                      MIDDLEWARE STACK                           │ │
│  │                                                                  │ │
│  │  1. CORS Middleware                                             │ │
│  │     • Allow Origins: ["http://localhost:5173",                  │ │
│  │                       "http://localhost:3000"]                  │ │
│  │     • Allow Credentials: True                                   │ │
│  │     • Allow Methods: ["*"]                                      │ │
│  │     • Allow Headers: ["*"]                                      │ │
│  │                                                                  │ │
│  │  2. Request Logging Middleware (Custom)                         │ │
│  │     • Log request method, path, client IP                       │ │
│  │     • Log response status, latency                              │ │
│  │                                                                  │ │
│  │  3. Error Handling Middleware                                   │ │
│  │     • Catch all exceptions                                      │ │
│  │     • Return structured error responses                         │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                      ENDPOINT GROUPS                            │ │
│  │                                                                  │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │  SEARCH ENDPOINTS                                         │  │ │
│  │  │  • POST   /search                   [Main search]         │  │ │
│  │  │  • POST   /search/enhanced          [Memory-enhanced]     │  │ │
│  │  │  • POST   /search/graph             [Graph-enhanced]      │  │ │
│  │  │  • GET    /stream-search-steps      [SSE streaming]       │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  │                                                                  │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │  DOCUMENT MANAGEMENT ENDPOINTS                            │  │ │
│  │  │  • POST   /index                    [Index documents]     │  │ │
│  │  │  • POST   /upload                   [Upload files]        │  │ │
│  │  │  • GET    /documents                [List documents]      │  │ │
│  │  │  • GET    /document/{id}            [Get metadata]        │  │ │
│  │  │  • DELETE /document/{id}            [Delete document]     │  │ │
│  │  │  • GET    /files/serve/{path}       [Serve files]         │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  │                                                                  │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │  MEMORY ENDPOINTS                                         │  │ │
│  │  │  • GET    /memory/session           [Get session]         │  │ │
│  │  │  • POST   /memory/session           [Update session]      │  │ │
│  │  │  • GET    /memory/episodes          [Get episodes]        │  │ │
│  │  │  • GET    /memory/graph             [Memory graph]        │  │ │
│  │  │  • POST   /memory/clear             [Clear memory]        │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  │                                                                  │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │  FILE WATCHER ENDPOINTS (from watcher_endpoints.py)      │  │ │
│  │  │  • POST   /watcher/enable           [Enable watcher]      │  │ │
│  │  │  • POST   /watcher/disable          [Disable watcher]     │  │ │
│  │  │  • GET    /watcher/status           [Watcher status]      │  │ │
│  │  │  • POST   /watcher/add-path         [Watch new path]      │  │ │
│  │  │  • POST   /watcher/remove-path      [Unwatch path]        │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  │                                                                  │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │  AUTHENTICATION ENDPOINTS (from auth_endpoints.py)        │  │ │
│  │  │  • POST   /auth/login               [User login]          │  │ │
│  │  │  • POST   /auth/register            [User registration]   │  │ │
│  │  │  • POST   /auth/logout              [User logout]         │  │ │
│  │  │  • GET    /auth/me                  [Current user]        │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  │                                                                  │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │  FEEDBACK & ANALYTICS ENDPOINTS                           │  │ │
│  │  │  • POST   /feedback                 [Submit feedback]     │  │ │
│  │  │  • GET    /stats                    [System statistics]   │  │ │
│  │  │  • GET    /analytics/queries        [Query analytics]     │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  │                                                                  │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │  SYSTEM ENDPOINTS                                         │  │ │
│  │  │  • GET    /health                   [Health check]        │  │ │
│  │  │  • GET    /                         [Root/Welcome]        │  │ │
│  │  └──────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    DEPENDENCY INJECTION                         │ │
│  │                                                                  │ │
│  │  • OpenSearchClient (singleton)                                 │ │
│  │  • MemoryManager (singleton)                                    │ │
│  │  • KnowledgeGraph (singleton)                                   │ │
│  │  • ZeusOrchestrator (singleton)                                 │ │
│  │  • IngestionPipeline (per-request)                              │ │
│  │  • FileWatcher (singleton)                                      │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    STARTUP & SHUTDOWN EVENTS                    │ │
│  │                                                                  │ │
│  │  Startup:                                                        │ │
│  │    1. Load config.yaml                                           │ │
│  │    2. Initialize OpenSearch connection                           │ │
│  │    3. Create index if not exists                                 │ │
│  │    4. Initialize Redis connection                                │ │
│  │    5. Initialize SQLite databases                                │ │
│  │    6. Load all agents                                            │ │
│  │    7. Initialize orchestrator                                    │ │
│  │    8. Start background tasks (memory consolidation)              │ │
│  │                                                                  │ │
│  │  Shutdown:                                                       │ │
│  │    1. Close OpenSearch connection                                │ │
│  │    2. Close Redis connection                                     │ │
│  │    3. Close SQLite connections                                   │ │
│  │    4. Save in-memory state                                       │ │
│  │    5. Stop background tasks                                      │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Request Processing Flow

```
1. HTTP Request arrives at FastAPI
   ↓
2. CORS Middleware validates origin
   ↓
3. Request Logging Middleware logs details
   ↓
4. Route matching (path + method)
   ↓
5. Pydantic model validation (request body)
   ↓
6. Dependency injection (DB connections, services)
   ↓
7. Endpoint handler execution
   ↓
8. Response serialization (Pydantic models)
   ↓
9. Response logging
   ↓
10. Return to client
```

---

## Core Services

### 1. OpenSearch Client

**File**: `backend/opensearch_client.py`

```
┌─────────────────────────────────────────────────────────────────────┐
│                       OpenSearchClient                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  CONNECTION MANAGEMENT                                          │ │
│  │                                                                  │ │
│  │  • Host: localhost:9200                                         │ │
│  │  • Auth: Basic (admin / LocalLens@1234)                         │ │
│  │  • Connection: Async (opensearch-py AsyncOpenSearch)            │ │
│  │  • SSL: Disabled for localhost (configurable)                   │ │
│  │  • Timeout: 30 seconds                                          │ │
│  │  • Max retries: 3                                               │ │
│  │  • Connection pool: 10 connections                              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  INDEX MANAGEMENT                                               │ │
│  │                                                                  │ │
│  │  Index Name: locallens_index                                    │ │
│  │                                                                  │ │
│  │  Schema:                                                         │ │
│  │  {                                                               │ │
│  │    "mappings": {                                                 │ │
│  │      "properties": {                                             │ │
│  │        "id": { "type": "keyword" },                              │ │
│  │        "filename": { "type": "text" },                           │ │
│  │        "file_type": { "type": "keyword" },                       │ │
│  │        "file_path": { "type": "keyword" },                       │ │
│  │        "document_type": { "type": "keyword" },                   │ │
│  │        "detailed_summary": { "type": "text" },                   │ │
│  │        "full_content": {                                         │ │
│  │          "type": "text",                                         │ │
│  │          "index_options": "offsets"                              │ │
│  │        },                                                         │ │
│  │        "keywords": { "type": "keyword" },                        │ │
│  │        "entities": { "type": "keyword" },                        │ │
│  │        "topics": { "type": "keyword" },                          │ │
│  │        "vector_embedding": {                                     │ │
│  │          "type": "knn_vector",                                   │ │
│  │          "dimension": 768,                                       │ │
│  │          "method": {                                             │ │
│  │            "name": "hnsw",                                       │ │
│  │            "space_type": "cosinesimil",                          │ │
│  │            "engine": "nmslib",                                   │ │
│  │            "parameters": {                                       │ │
│  │              "ef_construction": 128,                             │ │
│  │              "m": 24                                             │ │
│  │            }                                                      │ │
│  │          }                                                        │ │
│  │        },                                                         │ │
│  │        "created_at": { "type": "date" },                         │ │
│  │        "updated_at": { "type": "date" },                         │ │
│  │        "file_size": { "type": "long" },                          │ │
│  │        "page_count": { "type": "integer" }                       │ │
│  │      }                                                            │ │
│  │    },                                                             │ │
│  │    "settings": {                                                 │ │
│  │      "index": {                                                  │ │
│  │        "knn": true,                                              │ │
│  │        "number_of_shards": 1,                                    │ │
│  │        "number_of_replicas": 0                                   │ │
│  │      }                                                            │ │
│  │    }                                                              │ │
│  │  }                                                               │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  SEARCH OPERATIONS                                              │ │
│  │                                                                  │ │
│  │  1. Vector Search (k-NN)                                        │ │
│  │     • Method: HNSW (Hierarchical Navigable Small World)         │ │
│  │     • Space: Cosine similarity                                  │ │
│  │     • ef_search: 100 (query time parameter)                     │ │
│  │     • k: 50 (recall top 50 candidates)                          │ │
│  │                                                                  │ │
│  │  2. BM25 Full-Text Search                                       │ │
│  │     • Fields: detailed_summary, full_content, keywords          │ │
│  │     • Boost: summary (2.0), content (1.0), keywords (1.5)       │ │
│  │     • Min score: 0.3                                            │ │
│  │                                                                  │ │
│  │  3. Hybrid Search (Vector + BM25)                               │ │
│  │     • Combine using Reciprocal Rank Fusion (RRF)                │ │
│  │     • Weights: 70% vector, 30% BM25                             │ │
│  │     • Formula: score = 0.7*vector_score + 0.3*bm25_score        │ │
│  │     • Deduplication: By document ID                             │ │
│  │     • Final top_k: 50                                           │ │
│  │                                                                  │ │
│  │  4. Filtered Search                                             │ │
│  │     • By document_type                                          │ │
│  │     • By file_type                                              │ │
│  │     • By date range                                             │ │
│  │     • By keywords/entities                                      │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  DOCUMENT OPERATIONS                                            │ │
│  │                                                                  │ │
│  │  • index_document(doc_id, content, metadata, embedding)         │ │
│  │  • bulk_index(documents[])                                      │ │
│  │  • update_document(doc_id, fields)                              │ │
│  │  • delete_document(doc_id)                                      │ │
│  │  • get_document(doc_id)                                         │ │
│  │  • list_documents(filter, sort, pagination)                     │ │
│  │  • count_documents(filter)                                      │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  ERROR HANDLING                                                 │ │
│  │                                                                  │ │
│  │  • ConnectionError → Retry with exponential backoff             │ │
│  │  • IndexNotFoundError → Auto-create index                       │ │
│  │  • RequestTimeout → Return partial results                      │ │
│  │  • BulkIndexError → Log failed documents, continue              │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### 2. Reranker

**File**: `backend/reranker.py`

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Reranker Service                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  MODEL CONFIGURATION                                            │ │
│  │                                                                  │ │
│  │  • Model: cross-encoder/ms-marco-MiniLM-L-6-v2                  │ │
│  │  • Type: Cross-encoder (pairwise scoring)                       │ │
│  │  • Input: (query, document) pairs                               │ │
│  │  • Output: Relevance score [0, 1]                               │ │
│  │  • Device: CUDA if available, else CPU                          │ │
│  │  • Max length: 512 tokens                                       │ │
│  │  • Batch size: 32 (for efficient processing)                    │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  RERANKING PROCESS                                              │ │
│  │                                                                  │ │
│  │  Input:                                                          │ │
│  │    • Query: "What are the main findings?"                       │ │
│  │    • Documents: List[50] (from hybrid search)                   │ │
│  │                                                                  │ │
│  │  Process:                                                        │ │
│  │    1. Create query-document pairs:                              │ │
│  │       [(query, doc1), (query, doc2), ..., (query, doc50)]       │ │
│  │                                                                  │ │
│  │    2. Score all pairs with cross-encoder:                       │ │
│  │       model.predict(pairs) → [score1, score2, ..., score50]     │ │
│  │                                                                  │ │
│  │    3. Sort documents by score (descending):                     │ │
│  │       [(doc_i, 0.92), (doc_j, 0.87), ..., (doc_k, 0.15)]        │ │
│  │                                                                  │ │
│  │    4. Return top_k documents:                                   │ │
│  │       Top 5 highest scoring documents                           │ │
│  │                                                                  │ │
│  │  Output:                                                         │ │
│  │    • Reranked List[5] with scores                               │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  PERFORMANCE OPTIMIZATION                                       │ │
│  │                                                                  │ │
│  │  • Batching: Process 32 pairs at once                           │ │
│  │  • GPU acceleration: Use CUDA when available                    │ │
│  │  • Mixed precision: FP16 for faster inference                   │ │
│  │  • Truncation: Limit input to 512 tokens                        │ │
│  │  • Caching: Cache model in memory (singleton)                   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  QUALITY METRICS                                                │ │
│  │                                                                  │ │
│  │  • Precision@5: Proportion of relevant docs in top 5            │ │
│  │  • NDCG@5: Normalized Discounted Cumulative Gain                │ │
│  │  • MRR: Mean Reciprocal Rank of first relevant doc              │ │
│  │  • Latency: Avg time to rerank 50 → 5 (~100-300ms)              │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Search Engine Architecture

### Hybrid Search Flow

```
┌────────────────────────────────────────────────────────────────────┐
│                       HYBRID SEARCH PIPELINE                        │
└────────────────────────────────────────────────────────────────────┘

User Query: "What are the key findings in my research papers?"
    ↓
┌────────────────────────────────────────────────────────────────────┐
│ STEP 1: QUERY PREPROCESSING                                         │
│                                                                      │
│ • Remove stop words (optional, configurable)                        │
│ • Expand abbreviations (via query expansion)                        │
│ • Extract intent (via Athena classifier)                            │
│ • Generate query embedding (Sentence-Transformers)                  │
│   → 768-dimensional vector                                          │
└────────────────────────────────────────────────────────────────────┘
    ↓
┌────────────────────────────────────────────────────────────────────┐
│ STEP 2: PARALLEL SEARCH                                             │
│                                                                      │
│  ┌──────────────────────────┐    ┌──────────────────────────┐      │
│  │  VECTOR SEARCH (k-NN)    │    │  BM25 FULL-TEXT SEARCH   │      │
│  │                          │    │                          │      │
│  │ • Query embedding        │    │ • Keywords: "key",       │      │
│  │ • Cosine similarity      │    │   "findings", "research" │      │
│  │ • HNSW algorithm         │    │ • Multi-field search     │      │
│  │ • k=50 candidates        │    │ • Boost weights          │      │
│  │                          │    │ • k=50 candidates        │      │
│  │ Results:                 │    │ Results:                 │      │
│  │ [doc1: 0.89,             │    │ [doc3: 15.2,             │      │
│  │  doc2: 0.87,             │    │  doc1: 14.8,             │      │
│  │  doc5: 0.85, ...]        │    │  doc7: 13.5, ...]        │      │
│  └──────────────────────────┘    └──────────────────────────┘      │
│         │                                  │                         │
│         └──────────────┬───────────────────┘                         │
│                        ▼                                             │
└────────────────────────────────────────────────────────────────────┘
    ↓
┌────────────────────────────────────────────────────────────────────┐
│ STEP 3: SCORE FUSION (Reciprocal Rank Fusion)                      │
│                                                                      │
│ For each document, calculate hybrid score:                          │
│                                                                      │
│   hybrid_score = w_v * normalize(vector_score) +                    │
│                  w_b * normalize(bm25_score)                        │
│                                                                      │
│   where w_v = 0.7, w_b = 0.3                                        │
│                                                                      │
│ Normalization:                                                       │
│   • Vector scores: Already [0, 1] from cosine similarity            │
│   • BM25 scores: Normalize to [0, 1] using min-max scaling          │
│                                                                      │
│ Deduplication: Merge scores for same document ID                    │
│                                                                      │
│ Sort by hybrid_score (descending)                                   │
│                                                                      │
│ Results (top 50):                                                   │
│   [doc1: 0.91, doc2: 0.88, doc3: 0.85, ..., doc50: 0.42]            │
└────────────────────────────────────────────────────────────────────┘
    ↓
┌────────────────────────────────────────────────────────────────────┐
│ STEP 4: CROSS-ENCODER RERANKING                                    │
│                                                                      │
│ • Create (query, doc) pairs for all 50 documents                    │
│ • Score with ms-marco-MiniLM-L-6-v2 cross-encoder                   │
│ • Sort by cross-encoder score                                       │
│ • Select top 5                                                      │
│                                                                      │
│ Final Results (top 5):                                              │
│   [doc2: 0.94, doc1: 0.92, doc5: 0.89, doc3: 0.86, doc7: 0.84]      │
└────────────────────────────────────────────────────────────────────┘
    ↓
┌────────────────────────────────────────────────────────────────────┐
│ STEP 5: RESPONSE GENERATION                                         │
│                                                                      │
│ • Pass top 5 documents + query to Ollama (qwen3-vl:8b)              │
│ • Generate natural language response                                │
│ • Include citations to source documents                             │
│ • Stream response to frontend                                       │
└────────────────────────────────────────────────────────────────────┘
```

### Search Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| **Vector Search Latency** | 30-80ms | Depends on index size |
| **BM25 Search Latency** | 20-50ms | Fast full-text search |
| **Fusion Overhead** | 5-10ms | Simple arithmetic |
| **Reranking Latency** | 100-300ms | Bottleneck for 50 docs |
| **Total Search Time** | 155-440ms | Before LLM generation |
| **Recall@50** | ~95% | High recall from hybrid |
| **Precision@5** | ~85% | After reranking |

---

## Document Processing

### Ingestion Pipeline Architecture

**File**: `backend/ingestion.py`

```
┌─────────────────────────────────────────────────────────────────────┐
│                      DOCUMENT INGESTION PIPELINE                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  INPUT: User selects directory path                                  │
│         POST /index { "directory": "/path/to/docs" }                 │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ STEP 1: FILE DISCOVERY                                          │ │
│  │                                                                  │ │
│  │ • Scan directory recursively                                    │ │
│  │ • Filter by supported extensions:                               │ │
│  │   - Documents: .pdf, .docx, .txt, .md                           │ │
│  │   - Spreadsheets: .xlsx, .csv                                   │ │
│  │   - Images: .png, .jpg, .jpeg, .gif, .bmp                       │ │
│  │ • Skip hidden files (starting with .)                           │ │
│  │ • Skip files > 100MB (configurable)                             │ │
│  │ • Collect metadata: path, size, modified time                   │ │
│  │                                                                  │ │
│  │ Output: List of file paths to process                           │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ STEP 2: CONTENT EXTRACTION (Per File)                          │ │
│  │                                                                  │ │
│  │ PDF Files (.pdf):                                               │ │
│  │   • Library: PyPDF (pypdf)                                      │ │
│  │   • Extract text from all pages                                 │ │
│  │   • Extract images (if any)                                     │ │
│  │   • Metadata: page count, author, title                         │ │
│  │   • Fallback: If text extraction fails, use Qwen vision OCR     │ │
│  │                                                                  │ │
│  │ Word Documents (.docx):                                         │ │
│  │   • Library: python-docx                                        │ │
│  │   • Extract paragraphs and tables                               │ │
│  │   • Preserve formatting metadata                                │ │
│  │                                                                  │ │
│  │ Plain Text (.txt, .md):                                         │ │
│  │   • Direct file read with encoding detection                    │ │
│  │   • Encodings tried: UTF-8, UTF-16, Latin-1                     │ │
│  │                                                                  │ │
│  │ Spreadsheets (.xlsx, .csv):                                     │ │
│  │   • Library: pandas, openpyxl                                   │ │
│  │   • Convert to text representation                              │ │
│  │   • Preserve column headers and structure                       │ │
│  │                                                                  │ │
│  │ Images (.png, .jpg, .gif, .bmp):                                │ │
│  │   • Use Qwen3-VL vision model for OCR + description             │ │
│  │   • Extract: text content, visual description                   │ │
│  │   • Store image path for later retrieval                        │ │
│  │                                                                  │ │
│  │ Output: Raw text content + metadata                             │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ STEP 3: TEXT PROCESSING                                        │ │
│  │                                                                  │ │
│  │ • Truncate to 50,000 characters (configurable)                  │ │
│  │ • Clean whitespace and control characters                       │ │
│  │ • Normalize unicode (NFKC)                                      │ │
│  │ • Remove excessive newlines                                     │ │
│  │                                                                  │ │
│  │ Output: Cleaned full_content                                    │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ STEP 4: LLM-BASED SUMMARIZATION (Ollama qwen3-vl:8b)           │ │
│  │                                                                  │ │
│  │ Prompt Template:                                                 │ │
│  │   "Analyze the following document and provide:                  │ │
│  │    1. A detailed 3-5 sentence summary                           │ │
│  │    2. Key topics (comma-separated)                              │ │
│  │    3. Named entities (people, orgs, locations)                  │ │
│  │    4. Important keywords                                        │ │
│  │    5. Document type classification                              │ │
│  │                                                                  │ │
│  │    Document content:                                             │ │
│  │    {full_content}                                                │ │
│  │                                                                  │ │
│  │    Respond in JSON format."                                      │ │
│  │                                                                  │ │
│  │ LLM Call:                                                        │ │
│  │   • Model: qwen3-vl:8b                                          │ │
│  │   • Temperature: 0.3 (deterministic)                            │ │
│  │   • Max tokens: 500                                             │ │
│  │   • Timeout: 30 seconds                                         │ │
│  │                                                                  │ │
│  │ Output Example:                                                  │ │
│  │   {                                                              │ │
│  │     "summary": "This research paper explores...",               │ │
│  │     "topics": ["machine learning", "NLP", "transformers"],      │ │
│  │     "entities": ["OpenAI", "GPT-4", "San Francisco"],           │ │
│  │     "keywords": ["neural networks", "attention", "BERT"],       │ │
│  │     "document_type": "research_paper"                           │ │
│  │   }                                                              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ STEP 5: EMBEDDING GENERATION (Sentence-Transformers)           │ │
│  │                                                                  │ │
│  │ • Model: nomic-embed-text (768 dimensions)                      │ │
│  │ • Input: detailed_summary (not full content)                    │ │
│  │ • Normalization: L2 normalization                               │ │
│  │ • Device: CUDA if available, else CPU                           │ │
│  │                                                                  │ │
│  │ Output: 768-dimensional vector [0.12, -0.45, 0.89, ...]         │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ STEP 6: KNOWLEDGE GRAPH EXTRACTION                             │ │
│  │                                                                  │ │
│  │ • Extract entities from summary and content                     │ │
│  │ • Identify relationships between entities                       │ │
│  │ • Classify entity types:                                        │ │
│  │   - PERSON, ORGANIZATION, LOCATION, DATE, CONCEPT, DOCUMENT     │ │
│  │ • Add to KnowledgeGraph (NetworkX)                              │ │
│  │ • Link document node to entity nodes                            │ │
│  │                                                                  │ │
│  │ Output: Graph edges added                                       │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ STEP 7: INDEX IN OPENSEARCH                                    │ │
│  │                                                                  │ │
│  │ Document Structure:                                              │ │
│  │   {                                                              │ │
│  │     "id": "hash_of_filepath",                                    │ │
│  │     "filename": "research_paper.pdf",                            │ │
│  │     "file_path": "/path/to/research_paper.pdf",                 │ │
│  │     "file_type": "pdf",                                          │ │
│  │     "file_size": 2048576,                                        │ │
│  │     "document_type": "research_paper",                           │ │
│  │     "detailed_summary": "This research explores...",             │ │
│  │     "full_content": "Abstract\nIntroduction\n...",               │ │
│  │     "keywords": ["neural networks", "attention"],                │ │
│  │     "entities": ["OpenAI", "GPT-4"],                             │ │
│  │     "topics": ["machine learning", "NLP"],                       │ │
│  │     "vector_embedding": [0.12, -0.45, ...],  # 768 dims         │ │
│  │     "created_at": "2025-01-15T10:30:00Z",                        │ │
│  │     "updated_at": "2025-01-15T10:30:00Z"                         │ │
│  │   }                                                              │ │
│  │                                                                  │ │
│  │ • Bulk indexing for efficiency (batch size: 10)                 │ │
│  │ • Upsert: Update if doc_id exists                               │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ STEP 8: PROGRESS STREAMING (SSE)                               │ │
│  │                                                                  │ │
│  │ • Stream updates to frontend via Server-Sent Events             │ │
│  │ • Update format:                                                 │ │
│  │   {                                                              │ │
│  │     "status": "processing",                                      │ │
│  │     "current_file": "research_paper.pdf",                        │ │
│  │     "progress": "15/100",                                        │ │
│  │     "stage": "Generating summary"                                │ │
│  │   }                                                              │ │
│  │ • Error handling: Continue on failure, log errors               │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  OUTPUT: All documents indexed, ready for search                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Supported File Types & Extraction Methods

| File Type | Extensions | Extraction Method | Special Handling |
|-----------|-----------|-------------------|------------------|
| **PDF** | .pdf | PyPDF text extraction | OCR fallback with Qwen vision |
| **Word** | .docx | python-docx | Tables preserved |
| **Text** | .txt, .md | Direct read | Encoding detection |
| **Spreadsheet** | .xlsx, .csv | pandas → text | Column headers kept |
| **Image** | .png, .jpg, .jpeg, .gif, .bmp | Qwen3-VL OCR + vision | Text + description |

---

## File Watcher System

**Files**: `backend/watcher.py`, `backend/watcher_endpoints.py`

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FILE WATCHER SYSTEM                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  ARCHITECTURE                                                   │ │
│  │                                                                  │ │
│  │  • Library: watchdog (Python)                                   │ │
│  │  • Pattern: Observer pattern with event handlers                │ │
│  │  • Threading: Background thread for monitoring                  │ │
│  │  • Debouncing: 3-second delay before reindexing                 │ │
│  │  • Batch processing: Group events within debounce window        │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  EVENT HANDLING                                                 │ │
│  │                                                                  │ │
│  │  Events Monitored:                                              │ │
│  │    1. FILE_CREATED                                              │ │
│  │       • Check file extension                                    │ │
│  │       • If supported → Queue for indexing                       │ │
│  │                                                                  │ │
│  │    2. FILE_MODIFIED                                             │ │
│  │       • Check if file is indexed                                │ │
│  │       • If yes → Queue for reindexing                           │ │
│  │                                                                  │ │
│  │    3. FILE_DELETED                                              │ │
│  │       • Check if file is indexed                                │ │
│  │       • If yes → Remove from OpenSearch                         │ │
│  │       • Update knowledge graph                                  │ │
│  │                                                                  │ │
│  │    4. FILE_MOVED                                                │ │
│  │       • Update file_path in OpenSearch                          │ │
│  │       • Keep same doc_id                                        │ │
│  │                                                                  │ │
│  │  Events Ignored:                                                │ │
│  │    • Directory changes                                          │ │
│  │    • Temporary files (.tmp, .swp)                               │ │
│  │    • Hidden files (starting with .)                             │ │
│  │    • System files                                               │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  DEBOUNCE MECHANISM                                             │ │
│  │                                                                  │ │
│  │  Problem: File editors generate multiple events per save        │ │
│  │           (e.g., create temp, write, rename, delete temp)       │ │
│  │                                                                  │ │
│  │  Solution: Debounce timer                                       │ │
│  │    1. Event received → Start 3-second timer                     │ │
│  │    2. If another event for same file → Reset timer              │ │
│  │    3. Timer expires → Process accumulated events                │ │
│  │    4. Batch process all pending files                           │ │
│  │                                                                  │ │
│  │  Benefits:                                                       │ │
│  │    • Prevents redundant processing                              │ │
│  │    • Reduces LLM API calls                                      │ │
│  │    • Improves performance                                       │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  REINDEXING FLOW                                                │ │
│  │                                                                  │ │
│  │  File Modified: research_paper.pdf                              │ │
│  │      ↓                                                           │ │
│  │  Debounce timer (3s)                                            │ │
│  │      ↓                                                           │ │
│  │  Extract new content                                            │ │
│  │      ↓                                                           │ │
│  │  Generate new summary & embedding                               │ │
│  │      ↓                                                           │ │
│  │  Update OpenSearch document                                     │ │
│  │      ↓                                                           │ │
│  │  Update knowledge graph                                         │ │
│  │      ↓                                                           │ │
│  │  Notify frontend (SSE)                                          │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  API ENDPOINTS (watcher_endpoints.py)                           │ │
│  │                                                                  │ │
│  │  POST /watcher/enable                                           │ │
│  │    • Start file watching for all indexed directories            │ │
│  │    • Return: { "status": "enabled", "watching": [paths] }       │ │
│  │                                                                  │ │
│  │  POST /watcher/disable                                          │ │
│  │    • Stop all file watching                                     │ │
│  │    • Clean up resources                                         │ │
│  │    • Return: { "status": "disabled" }                           │ │
│  │                                                                  │ │
│  │  GET /watcher/status                                            │ │
│  │    • Check if watcher is active                                 │ │
│  │    • Return watched paths and event counts                      │ │
│  │    • Return: {                                                  │ │
│  │        "enabled": true,                                         │ │
│  │        "paths": ["/path1", "/path2"],                           │ │
│  │        "events_processed": 142                                  │ │
│  │      }                                                           │ │
│  │                                                                  │ │
│  │  POST /watcher/add-path                                         │ │
│  │    • Add new directory to watch list                            │ │
│  │    • Body: { "path": "/new/path" }                              │ │
│  │                                                                  │ │
│  │  POST /watcher/remove-path                                      │ │
│  │    • Remove directory from watch list                           │ │
│  │    • Body: { "path": "/remove/path" }                           │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  ERROR HANDLING                                                 │ │
│  │                                                                  │ │
│  │  • Directory not accessible → Log warning, skip                 │ │
│  │  • File locked → Retry after 1 second (max 3 retries)           │ │
│  │  • Indexing failed → Log error, notify frontend, continue       │ │
│  │  • Watcher crash → Auto-restart with exponential backoff        │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Authentication & Security

**Files**: `backend/auth.py`, `backend/auth_endpoints.py`

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION SYSTEM                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  USER STORAGE                                                   │ │
│  │                                                                  │ │
│  │  • Backend: SQLite (locallens_users.json fallback)              │ │
│  │  • Table: users                                                 │ │
│  │  • Schema:                                                       │ │
│  │    {                                                             │ │
│  │      "id": "uuid",                                               │ │
│  │      "username": "string (unique)",                              │ │
│  │      "email": "string (unique)",                                 │ │
│  │      "password_hash": "bcrypt hash",                             │ │
│  │      "created_at": "timestamp",                                  │ │
│  │      "last_login": "timestamp",                                  │ │
│  │      "is_active": "boolean",                                     │ │
│  │      "preferences": "json"                                       │ │
│  │    }                                                             │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  PASSWORD HASHING                                               │ │
│  │                                                                  │ │
│  │  • Algorithm: bcrypt                                            │ │
│  │  • Work factor: 12 rounds                                       │ │
│  │  • Salt: Generated per password                                 │ │
│  │  • Library: passlib                                             │ │
│  │                                                                  │ │
│  │  Registration:                                                   │ │
│  │    password → bcrypt(password, rounds=12) → store hash          │ │
│  │                                                                  │ │
│  │  Login:                                                          │ │
│  │    password → bcrypt.verify(password, stored_hash) → bool       │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  SESSION MANAGEMENT                                             │ │
│  │                                                                  │ │
│  │  • Backend: Redis                                               │ │
│  │  • Session ID: UUID v4                                          │ │
│  │  • TTL: 24 hours (configurable)                                 │ │
│  │  • Sliding expiration: Extends on activity                      │ │
│  │                                                                  │ │
│  │  Session Data:                                                   │ │
│  │    {                                                             │ │
│  │      "user_id": "uuid",                                          │ │
│  │      "username": "string",                                       │ │
│  │      "created_at": "timestamp",                                  │ │
│  │      "last_activity": "timestamp",                               │ │
│  │      "ip_address": "string"                                      │ │
│  │    }                                                             │ │
│  │                                                                  │ │
│  │  Storage Key: "session:{session_id}"                             │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  AUTHENTICATION FLOW                                            │ │
│  │                                                                  │ │
│  │  Registration:                                                   │ │
│  │    POST /auth/register                                           │ │
│  │    Body: { "username", "email", "password" }                     │ │
│  │      ↓                                                           │ │
│  │    Validate input (length, format)                              │ │
│  │      ↓                                                           │ │
│  │    Check if username/email exists                               │ │
│  │      ↓                                                           │ │
│  │    Hash password (bcrypt)                                       │ │
│  │      ↓                                                           │ │
│  │    Create user record in SQLite                                 │ │
│  │      ↓                                                           │ │
│  │    Create session in Redis                                      │ │
│  │      ↓                                                           │ │
│  │    Return: { "session_id", "user_id" }                          │ │
│  │                                                                  │ │
│  │  Login:                                                          │ │
│  │    POST /auth/login                                              │ │
│  │    Body: { "username", "password" }                              │ │
│  │      ↓                                                           │ │
│  │    Lookup user by username                                      │ │
│  │      ↓                                                           │ │
│  │    Verify password (bcrypt)                                     │ │
│  │      ↓                                                           │ │
│  │    Create session in Redis                                      │ │
│  │      ↓                                                           │ │
│  │    Update last_login timestamp                                  │ │
│  │      ↓                                                           │ │
│  │    Return: { "session_id", "user_id" }                          │ │
│  │                                                                  │ │
│  │  Logout:                                                         │ │
│  │    POST /auth/logout                                             │ │
│  │    Header: Authorization: Bearer {session_id}                   │ │
│  │      ↓                                                           │ │
│  │    Delete session from Redis                                    │ │
│  │      ↓                                                           │ │
│  │    Return: { "success": true }                                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  AUTHORIZATION (Middleware)                                     │ │
│  │                                                                  │ │
│  │  Protected endpoints require Authorization header:              │ │
│  │    Authorization: Bearer {session_id}                           │ │
│  │                                                                  │ │
│  │  Middleware flow:                                                │ │
│  │    1. Extract session_id from header                            │ │
│  │    2. Lookup session in Redis                                   │ │
│  │    3. If not found → 401 Unauthorized                           │ │
│  │    4. If expired → 401 Unauthorized, delete session             │ │
│  │    5. If valid → Extend TTL (sliding expiration)                │ │
│  │    6. Inject user_id into request context                       │ │
│  │    7. Proceed to endpoint handler                               │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  SECURITY FEATURES                                              │ │
│  │                                                                  │ │
│  │  • Password strength: Min 8 chars, complexity requirements      │ │
│  │  • Rate limiting: Max 5 login attempts per 15 minutes           │ │
│  │  • Session fixation prevention: New session ID on login         │ │
│  │  • HTTPS enforcement: Redirect HTTP → HTTPS (production)        │ │
│  │  • CORS: Whitelist allowed origins                              │ │
│  │  • XSS protection: Content-Security-Policy headers              │ │
│  │  • SQL injection prevention: Parameterized queries              │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Models & Schemas

### Pydantic Request/Response Models

**File**: `backend/api.py` (inline definitions)

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# =====================
# SEARCH MODELS
# =====================

class SearchRequest(BaseModel):
    """Request model for search endpoint"""
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=50)
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    attached_documents: List[str] = Field(default_factory=list)
    filters: Optional[Dict[str, Any]] = None

class SearchResult(BaseModel):
    """Individual search result"""
    doc_id: str
    filename: str
    file_type: str
    document_type: str
    summary: str
    score: float
    highlights: Optional[List[str]] = None

class SearchResponse(BaseModel):
    """Response model for search endpoint"""
    query: str
    response: str
    results: List[SearchResult]
    confidence_score: float
    thinking_steps: List[Dict[str, Any]]
    session_id: str
    timestamp: datetime

# =====================
# DOCUMENT MODELS
# =====================

class IndexRequest(BaseModel):
    """Request to index documents"""
    directory: str
    watch_mode: bool = False
    recursive: bool = True

class DocumentMetadata(BaseModel):
    """Document metadata"""
    id: str
    filename: str
    file_path: str
    file_type: str
    file_size: int
    document_type: str
    created_at: datetime
    updated_at: datetime
    indexed_at: datetime
    keywords: List[str]
    entities: List[str]
    topics: List[str]

class IndexingProgress(BaseModel):
    """Progress update during indexing"""
    status: str  # "processing", "completed", "failed"
    current_file: str
    progress: str  # "15/100"
    stage: str  # "Extracting content", "Generating summary", etc.
    error: Optional[str] = None

# =====================
# MEMORY MODELS
# =====================

class SessionContext(BaseModel):
    """Session memory context"""
    session_id: str
    user_id: str
    conversation_history: List[Dict[str, str]]
    context_window: int = 10

class Episode(BaseModel):
    """Episodic memory entry"""
    id: str
    user_id: str
    query: str
    response: str
    confidence: float
    timestamp: datetime
    feedback: Optional[int] = None  # 1 (positive), -1 (negative)

# =====================
# FEEDBACK MODELS
# =====================

class FeedbackRequest(BaseModel):
    """User feedback on search results"""
    query_id: str
    user_id: str
    rating: int = Field(..., ge=-1, le=1)  # -1, 0, 1
    comment: Optional[str] = None

# =====================
# AUTH MODELS
# =====================

class RegisterRequest(BaseModel):
    """User registration"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    password: str = Field(..., min_length=8)

class LoginRequest(BaseModel):
    """User login"""
    username: str
    password: str

class AuthResponse(BaseModel):
    """Authentication response"""
    session_id: str
    user_id: str
    username: str
```

### Database Schemas (SQLite)

```sql
-- =====================
-- CONVERSATIONS DATABASE
-- =====================

CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,  -- Search results, confidence, etc.
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

-- =====================
-- MEMORY DATABASE
-- =====================

CREATE TABLE user_profiles (
    user_id TEXT PRIMARY KEY,
    preferences JSON,
    interaction_count INTEGER DEFAULT 0,
    avg_confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE episodes (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    query TEXT NOT NULL,
    response TEXT NOT NULL,
    confidence REAL,
    feedback INTEGER,  -- -1, 0, 1
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
);

CREATE TABLE procedural_patterns (
    id TEXT PRIMARY KEY,
    pattern_type TEXT,
    pattern_data JSON,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    last_used TIMESTAMP
);

-- =====================
-- KNOWLEDGE GRAPH DATABASE
-- =====================

CREATE TABLE entities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,  -- PERSON, ORG, LOCATION, etc.
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE relationships (
    id TEXT PRIMARY KEY,
    source_entity_id TEXT NOT NULL,
    target_entity_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    strength REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_entity_id) REFERENCES entities(id),
    FOREIGN KEY (target_entity_id) REFERENCES entities(id)
);

-- =====================
-- USERS DATABASE
-- =====================

CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);
```

---

**Document Version**: 1.0
**Last Updated**: 2025-12-31
**Related Docs**: `01_OVERALL_SYSTEM_ARCHITECTURE.md`
