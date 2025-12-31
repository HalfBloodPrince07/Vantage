# VANTAGE - Data Flow & Request Lifecycle (Deep Dive)

## Table of Contents
- [Request Lifecycle Overview](#request-lifecycle-overview)
- [Search Query Flow (End-to-End)](#search-query-flow-end-to-end)
- [Document Attachment Flow](#document-attachment-flow)
- [Feedback Loop](#feedback-loop)
- [Session Management Flow](#session-management-flow)
- [Error Handling Flow](#error-handling-flow)
- [Performance Analysis](#performance-analysis)

---

## Request Lifecycle Overview

This document provides a comprehensive, step-by-step breakdown of how data flows through the Vantage system for different types of requests.

```
┌─────────────────────────────────────────────────────────────────────┐
│                     REQUEST LIFECYCLE STAGES                         │
└─────────────────────────────────────────────────────────────────────┘

1. USER INPUT
   └─> User types query in frontend

2. REQUEST FORMATION
   └─> Frontend prepares API request

3. API GATEWAY
   └─> FastAPI receives and validates request

4. MEMORY CONTEXT LOADING
   └─> Load session history and user profile

5. ORCHESTRATION
   └─> Zeus routes to appropriate agents

6. PROCESSING
   └─> Agents execute their tasks (parallel/sequential)

7. QUALITY CONTROL
   └─> Confidence scoring and hallucination detection

8. RESPONSE GENERATION
   └─> LLM generates final response

9. MEMORY STORAGE
   └─> Store interaction in all memory tiers

10. RESPONSE DELIVERY
    └─> Stream back to frontend via SSE

11. UI UPDATE
    └─> Frontend renders response

12. POST-PROCESSING
    └─> Background tasks (consolidation, analytics)
```

---

## Search Query Flow (End-to-End)

### Complete Request Lifecycle

```
┌─────────────────────────────────────────────────────────────────────┐
│           DETAILED SEARCH QUERY FLOW (WITH TIMINGS)                  │
└─────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════
STAGE 1: USER INPUT (Frontend)
═══════════════════════════════════════════════════════════════════════

User Action:
  • Enters query: "What are the key findings in my research papers?"
  • Clicks send button (or presses Ctrl+Enter)

Frontend State Changes:
  • setInputValue('')
  • setIsLoading(true)
  • setThinkingSteps([])
  • addMessage({ role: 'user', content: query })

Time: 0ms (instant UI update)

───────────────────────────────────────────────────────────────────────

═══════════════════════════════════════════════════════════════════════
STAGE 2: REQUEST FORMATION (Frontend)
═══════════════════════════════════════════════════════════════════════

Prepare Request Payload:
  {
    "query": "What are the key findings in my research papers?",
    "top_k": 5,
    "session_id": "session-uuid-12345",
    "user_id": "user-uuid-67890",
    "attached_documents": [],
    "filters": {}
  }

Establish SSE Connection:
  const eventSource = new EventSource(
    `/stream-search-steps?query=...&session_id=...`
  );

Register Event Listeners:
  • thinking_step
  • search_results
  • response_chunk
  • confidence_score
  • complete
  • error

Time: 5-10ms

───────────────────────────────────────────────────────────────────────

═══════════════════════════════════════════════════════════════════════
STAGE 3: API GATEWAY (FastAPI)
═══════════════════════════════════════════════════════════════════════

Request Received: POST /search
  ↓
CORS Middleware:
  • Validate origin: localhost:5173 ✓
  • Add CORS headers
  ↓
Request Logging Middleware:
  • Log: "POST /search from 127.0.0.1 at 10:30:00"
  ↓
Pydantic Validation:
  • Validate SearchRequest schema
  • Check required fields: query ✓
  • Validate types: top_k is int ✓
  ↓
Dependency Injection:
  • Inject OpenSearchClient (singleton)
  • Inject MemoryManager (singleton)
  • Inject ZeusOrchestrator (singleton)
  ↓
Route to Endpoint Handler:
  async def search(request: SearchRequest):
      ...

SSE Stream Initialization:
  • Set headers: Content-Type: text/event-stream
  • Keep connection alive
  • Start streaming

Time: 15-30ms

───────────────────────────────────────────────────────────────────────

═══════════════════════════════════════════════════════════════════════
STAGE 4: MEMORY CONTEXT LOADING
═══════════════════════════════════════════════════════════════════════

MemoryManager.get_context_for_query(query, user_id, session_id)

Parallel Loading (async):
  ┌────────────────────────────────────────────────────────────────┐
  │ 1. Session Memory (Redis)                                      │
  │    • GET session:session-uuid-12345                            │
  │    • Retrieve last 10 conversation turns                       │
  │    • Found: 3 previous turns                                   │
  │    Time: 5-10ms                                                │
  └────────────────────────────────────────────────────────────────┘
  ┌────────────────────────────────────────────────────────────────┐
  │ 2. Episodic Memory (SQLite)                                    │
  │    • Embed query → [0.12, -0.45, ...]                          │
  │    • Cosine similarity search against all episodes             │
  │    • Apply decay factors                                       │
  │    • Retrieved: 5 similar past queries                         │
  │    Time: 80-120ms                                              │
  └────────────────────────────────────────────────────────────────┘
  ┌────────────────────────────────────────────────────────────────┐
  │ 3. Procedural Memory (In-memory + SQLite)                      │
  │    • Check for applicable patterns                             │
  │    • Found: "research" → expand to "academic research"         │
  │    Time: 2-5ms                                                 │
  └────────────────────────────────────────────────────────────────┘
  ┌────────────────────────────────────────────────────────────────┐
  │ 4. User Profile (SQLite)                                       │
  │    • Load preferences and stats                                │
  │    • Response format: bullet_points                            │
  │    • Preferred sources: ["pdf", "docx"]                        │
  │    Time: 10-15ms                                               │
  └────────────────────────────────────────────────────────────────┘

Combined Context:
  {
    "session_history": [...],
    "similar_episodes": [...],
    "procedural_patterns": [...],
    "user_preferences": {...}
  }

Total Time: 120-150ms (parallel execution)

SSE Event: thinking_step
  data: {"agent": "MemoryManager", "action": "Loaded context"}

───────────────────────────────────────────────────────────────────────

═══════════════════════════════════════════════════════════════════════
STAGE 5: ORCHESTRATION (Zeus - LangGraph)
═══════════════════════════════════════════════════════════════════════

Initialize Workflow State:
  state = WorkflowState(
    query="What are the key findings...",
    intent=None,
    attached_documents=[],
    session_context={...},
    search_results=[],
    graph_context={},
    intermediate_steps=[],
    response="",
    confidence_score=0.0,
    error=None,
    metadata={}
  )

Execute Workflow Graph:

  ┌─────────────────────────────────────────────────────────────────┐
  │ NODE: classify_intent (Athena Agent)                            │
  │                                                                  │
  │ Input: query + session_context                                  │
  │                                                                  │
  │ LLM Call (Ollama qwen3-vl:8b):                                  │
  │   Prompt: "Classify this query: ..."                            │
  │   Temperature: 0.0                                              │
  │   Max tokens: 50                                                │
  │                                                                  │
  │ Output:                                                          │
  │   intent: "DOCUMENT_SEARCH"                                     │
  │   confidence: 0.95                                              │
  │                                                                  │
  │ Time: 200-400ms                                                 │
  └─────────────────────────────────────────────────────────────────┘

  SSE Event: thinking_step
    data: {"agent": "Athena", "action": "Classified as DOCUMENT_SEARCH"}

  ▼

  ┌─────────────────────────────────────────────────────────────────┐
  │ NODE: route_query (Conditional Router)                          │
  │                                                                  │
  │ if intent == "DOCUMENT_SEARCH":                                 │
  │     next_node = "athena_path"                                   │
  │                                                                  │
  │ Time: <1ms                                                      │
  └─────────────────────────────────────────────────────────────────┘

  ▼

  ┌─────────────────────────────────────────────────────────────────┐
  │ NODE: athena_path (Document Search Workflow)                    │
  │                                                                  │
  │ SUB-NODE 1: expand_query (Odysseus Agent - Optional)            │
  │   • Analyze query complexity                                    │
  │   • Not complex → Skip expansion                                │
  │   Time: 50ms (analysis only, no expansion)                      │
  │                                                                  │
  │ SUB-NODE 2: retrieve_documents (Proteus + OpenSearch)           │
  │   ┌─────────────────────────────────────────────────────────┐  │
  │   │ Step 1: Generate Query Embedding                         │  │
  │   │   • Sentence-Transformers (nomic-embed-text)             │  │
  │   │   • Input: "key findings research papers"                │  │
  │   │   • Output: 768-dim vector                               │  │
  │   │   Time: 100-200ms                                        │  │
  │   └─────────────────────────────────────────────────────────┘  │
  │                                                                  │
  │   ┌─────────────────────────────────────────────────────────┐  │
  │   │ Step 2: Hybrid Search (OpenSearch)                       │  │
  │   │                                                           │  │
  │   │   Parallel Queries:                                       │  │
  │   │   ┌───────────────────┐  ┌──────────────────┐           │  │
  │   │   │ Vector Search     │  │ BM25 Search      │           │  │
  │   │   │ (k-NN)            │  │ (Full-text)      │           │  │
  │   │   │                   │  │                  │           │  │
  │   │   │ • Cosine sim      │  │ • Match keywords │           │  │
  │   │   │ • Top 50 docs     │  │ • Top 50 docs    │           │  │
  │   │   │ Time: 40-70ms     │  │ Time: 30-50ms    │           │  │
  │   │   └───────────────────┘  └──────────────────┘           │  │
  │   │              │                     │                      │  │
  │   │              └──────────┬──────────┘                      │  │
  │   │                         ▼                                 │  │
  │   │   ┌────────────────────────────────────┐                 │  │
  │   │   │ Reciprocal Rank Fusion (RRF)       │                 │  │
  │   │   │                                    │                 │  │
  │   │   │ score = 0.7*vector + 0.3*bm25     │                 │  │
  │   │   │ Deduplicate by doc_id              │                 │  │
  │   │   │ Sort by score                      │                 │  │
  │   │   │ Time: 5-10ms                       │                 │  │
  │   │   └────────────────────────────────────┘                 │  │
  │   │                                                           │  │
  │   │   Results: 50 documents with hybrid scores               │  │
  │   │   Total Time: 70-130ms                                   │  │
  │   └─────────────────────────────────────────────────────────┘  │
  │                                                                  │
  │   SSE Event: thinking_step                                       │
  │     data: {"agent": "Search", "action": "Retrieved 50 documents"}│
  │                                                                  │
  │   ┌─────────────────────────────────────────────────────────┐  │
  │   │ Step 3: Cross-Encoder Reranking                          │  │
  │   │                                                           │  │
  │   │ • Model: ms-marco-MiniLM-L-6-v2                          │  │
  │   │ • Create (query, doc) pairs for all 50 docs              │  │
  │   │ • Score each pair                                        │  │
  │   │ • Batch size: 32                                         │  │
  │   │ • Sort by score                                          │  │
  │   │ • Select top 5                                           │  │
  │   │                                                           │  │
  │   │ Results: Top 5 documents                                 │  │
  │   │   [                                                       │  │
  │   │     {id: "doc1", score: 0.94, title: "ML Research 2024"},│  │
  │   │     {id: "doc2", score: 0.92, title: "Neural Nets"},     │  │
  │   │     {id: "doc3", score: 0.89, title: "Deep Learning"},   │  │
  │   │     {id: "doc4", score: 0.86, title: "AI Survey"},       │  │
  │   │     {id: "doc5", score: 0.84, title: "Transformers"}     │  │
  │   │   ]                                                       │  │
  │   │                                                           │  │
  │   │ Time: 100-300ms                                          │  │
  │   └─────────────────────────────────────────────────────────┘  │
  │                                                                  │
  │   SSE Event: search_results                                      │
  │     data: [{"doc_id": "doc1", "score": 0.94, ...}, ...]          │
  │                                                                  │
  │ Total Retrieval Time: 270-630ms                                 │
  │                                                                  │
  │ SUB-NODE 3: expand_graph_context (Apollo Agent - Optional)      │
  │   • Extract entities from top 5 docs                            │
  │   • Entities: ["machine learning", "neural networks", ...]      │
  │   • Query knowledge graph for related entities                  │
  │   • Traverse 1-2 hops                                           │
  │   • Add 3 related documents to context                          │
  │   Time: 150-250ms                                               │
  │                                                                  │
  │   SSE Event: thinking_step                                       │
  │     data: {"agent": "Apollo", "action": "Expanded with 12 entities"}│
  │                                                                  │
  │   SSE Event: graph_data                                          │
  │     data: {"nodes": [...], "links": [...]}                       │
  │                                                                  │
  │ SUB-NODE 4: generate_response (Ollama LLM)                      │
  │   ┌─────────────────────────────────────────────────────────┐  │
  │   │ Prepare Prompt                                           │  │
  │   │                                                           │  │
  │   │ System: "You are a helpful research assistant..."        │  │
  │   │                                                           │  │
  │   │ Context:                                                  │  │
  │   │   • Top 5 documents (summaries + content snippets)       │  │
  │   │   • Graph context (related entities)                     │  │
  │   │   • Session history (last 3 turns)                       │  │
  │   │   • User preferences (format: bullet points)             │  │
  │   │                                                           │  │
  │   │ User Query: "What are the key findings..."               │  │
  │   │                                                           │  │
  │   │ Instructions:                                             │  │
  │   │   • Answer based only on provided documents              │  │
  │   │   • Include citations [1], [2], etc.                     │  │
  │   │   • Format as bullet points (user preference)            │  │
  │   └─────────────────────────────────────────────────────────┘  │
  │                                                                  │
  │   ┌─────────────────────────────────────────────────────────┐  │
  │   │ LLM Call (Ollama - qwen3-vl:8b)                          │  │
  │   │                                                           │  │
  │   │ • Model: qwen3-vl:8b                                     │  │
  │   │ • Temperature: 0.7                                       │  │
  │   │ • Max tokens: 1000                                       │  │
  │   │ • Stream: true                                           │  │
  │   │                                                           │  │
  │   │ Streaming Response:                                       │  │
  │   │   "Based on the research papers, the key findings are:   │  │
  │   │    • Finding 1: Neural networks achieve 95% accuracy [1] │  │
  │   │    • Finding 2: Transformer architecture is effective [2]│  │
  │   │    • Finding 3: ..."                                     │  │
  │   │                                                           │  │
  │   │ Time: 2000-5000ms (streaming, ~20 tokens/sec)            │  │
  │   └─────────────────────────────────────────────────────────┘  │
  │                                                                  │
  │   SSE Events: response_chunk (multiple)                          │
  │     data: "Based on the research"                                │
  │     data: " papers, the key"                                     │
  │     data: " findings are:\n• Finding 1..."                       │
  │     ... (continues until complete)                               │
  │                                                                  │
  └─────────────────────────────────────────────────────────────────┘

Total Orchestration Time: 2470-5880ms

───────────────────────────────────────────────────────────────────────

═══════════════════════════════════════════════════════════════════════
STAGE 6: QUALITY CONTROL
═══════════════════════════════════════════════════════════════════════

Parallel Quality Checks:

┌────────────────────────────────────────────────────────────────┐
│ Themis (Confidence Scorer)                                      │
│                                                                  │
│ Scoring Factors:                                                │
│   • Retrieval quality (top doc score): 0.94 → 0.95             │
│   • Response grounding (overlap): 0.88                          │
│   • Coherence (grammar, flow): 0.92                             │
│   • Completeness: 0.85                                          │
│                                                                  │
│ Final Confidence: 0.4*0.95 + 0.3*0.88 + 0.2*0.92 + 0.1*0.85    │
│                  = 0.91                                          │
│                                                                  │
│ Time: 150-250ms                                                 │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ Diogenes (Critic Agent)                                         │
│                                                                  │
│ Checks:                                                          │
│   • Factual consistency: ✓ (all claims supported by docs)      │
│   • Self-contradiction: ✓ (no contradictions found)            │
│   • Relevance: ✓ (addresses query)                             │
│                                                                  │
│ Issues: None                                                     │
│ Quality Score: 0.92                                             │
│                                                                  │
│ Time: 100-200ms                                                 │
└────────────────────────────────────────────────────────────────┘

SSE Event: confidence_score
  data: 0.91

Total Quality Control Time: 150-250ms (parallel)

───────────────────────────────────────────────────────────────────────

═══════════════════════════════════════════════════════════════════════
STAGE 7: MEMORY STORAGE
═══════════════════════════════════════════════════════════════════════

MemoryManager.store_interaction(query, response, metadata)

Parallel Storage:

┌────────────────────────────────────────────────────────────────┐
│ 1. Session Memory (Redis)                                       │
│    • Add turn to conversation history                           │
│    • Enforce 10-turn window (drop oldest if needed)             │
│    • Update last_activity timestamp                             │
│    • Extend TTL to 1 hour                                       │
│    Time: 5-10ms                                                 │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ 2. Episodic Memory (SQLite)                                     │
│    • Generate query embedding                                   │
│    • Insert episode record                                      │
│    • Store: query, response, results, confidence, timestamp     │
│    • Initialize decay_factor = 1.0                              │
│    Time: 100-150ms                                              │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ 3. Procedural Memory (In-memory + SQLite)                       │
│    • Update pattern success counts                              │
│    • Pattern "research" → "academic research" worked well       │
│    • Increment success_count                                    │
│    • Recalculate confidence                                     │
│    Time: 2-5ms                                                  │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ 4. User Profile (SQLite)                                        │
│    • Increment total_queries                                    │
│    • Update avg_confidence                                      │
│    • Update most_queried_topics                                 │
│    • Update last_login                                          │
│    Time: 10-15ms                                                │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ 5. Agentic Memory (A-mem - Background)                         │
│    • Queue note generation (async)                              │
│    • Will process in background                                 │
│    Time: <1ms (queued)                                          │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ 6. Conversation Manager (SQLite)                                │
│    • Save message to conversations.db                           │
│    • Update conversation timestamp                              │
│    Time: 20-30ms                                                │
└────────────────────────────────────────────────────────────────┘

Total Memory Storage Time: 120-180ms (parallel)

───────────────────────────────────────────────────────────────────────

═══════════════════════════════════════════════════════════════════════
STAGE 8: RESPONSE FINALIZATION
═══════════════════════════════════════════════════════════════════════

Format Final Response:
  {
    "query": "What are the key findings...",
    "response": "Based on the research papers, the key findings...",
    "results": [
      {doc_id: "doc1", score: 0.94, title: "...", summary: "..."},
      ...
    ],
    "confidence_score": 0.91,
    "thinking_steps": [
      {agent: "Athena", action: "..."},
      ...
    ],
    "session_id": "session-uuid-12345",
    "timestamp": "2025-01-15T10:30:15Z",
    "metadata": {
      "total_time_ms": 3500,
      "documents_searched": 50,
      "documents_returned": 5
    }
  }

SSE Event: complete
  data: {entire final response object as JSON}

Close SSE Connection

Time: 5-10ms

───────────────────────────────────────────────────────────────────────

═══════════════════════════════════════════════════════════════════════
STAGE 9: FRONTEND UPDATE
═══════════════════════════════════════════════════════════════════════

EventSource receives 'complete' event:
  ↓
Update React State:
  • setIsLoading(false)
  • setThinkingSteps(final_steps)
  • setMessages([...messages, {role: 'assistant', content: response}])
  • setSearchResults(results)
  • setConfidenceScore(0.91)
  ↓
React Re-renders:
  • Message bubble with formatted response (markdown)
  • Source citations with links
  • Confidence badge (green, 0.91)
  • Thinking steps timeline (collapsed by default)
  ↓
Auto-scroll to bottom of chat
  ↓
setInputValue('') (ready for next query)

Time: 10-50ms (render time)

───────────────────────────────────────────────────────────────────────

═══════════════════════════════════════════════════════════════════════
STAGE 10: POST-PROCESSING (Background)
═══════════════════════════════════════════════════════════════════════

Background Tasks (Async, Non-blocking):

1. Agentic Memory Note Generation
   • Extract key facts from response
   • Generate memory notes
   • Create links to related notes
   Time: 500-1000ms (background)

2. Analytics Update
   • Log query for analytics
   • Update query trends
   Time: 10-20ms (background)

3. Cache Warming (if applicable)
   • Pre-fetch related documents
   Time: varies (background)

───────────────────────────────────────────────────────────────────────

═══════════════════════════════════════════════════════════════════════
TOTAL END-TO-END TIME BREAKDOWN
═══════════════════════════════════════════════════════════════════════

Stage 1: User Input                           0ms       (instant)
Stage 2: Request Formation                    5-10ms
Stage 3: API Gateway                          15-30ms
Stage 4: Memory Context Loading               120-150ms
Stage 5: Orchestration                        2470-5880ms
  └─ Classification                          200-400ms
  └─ Query Expansion                         50ms
  └─ Document Retrieval                      270-630ms
  └─ Graph Expansion                         150-250ms
  └─ LLM Response Generation                 2000-5000ms
Stage 6: Quality Control                      150-250ms
Stage 7: Memory Storage                       120-180ms
Stage 8: Response Finalization                5-10ms
Stage 9: Frontend Update                      10-50ms

─────────────────────────────────────────────────────────────────
TOTAL: ~2.9-6.6 seconds (typical: 3.5-4.5 seconds)
─────────────────────────────────────────────────────────────────

Bottlenecks:
  1. LLM Response Generation: 2-5 seconds (57-76% of total time)
  2. Document Retrieval: 270-630ms (8-10%)
  3. Graph Expansion: 150-250ms (4-5%)

Optimization Opportunities:
  • Use smaller/faster LLM for simple queries
  • Cache frequent query responses
  • Reduce reranking candidate pool (50 → 30)
  • Parallel graph expansion with retrieval
```

---

## Document Attachment Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│              DOCUMENT ATTACHMENT QUERY FLOW                          │
└─────────────────────────────────────────────────────────────────────┘

User attaches documents via DocumentSelector:
  • Selected: ["doc1", "doc2"]
  ↓
Submit query: "Summarize these papers"
  ↓
Request:
  {
    "query": "Summarize these papers",
    "attached_documents": ["doc1", "doc2"]
  }
  ↓
Zeus Orchestrator:
  • Override routing → Daedalus Path (document agents)
  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ Daedalus Orchestrator Workflow                                      │
│                                                                      │
│ For each attached document:                                          │
│                                                                      │
│   ┌──────────────────────────────────────────────────────────────┐ │
│   │ Prometheus (Reader)                                           │ │
│   │ • Retrieve document content from OpenSearch                   │ │
│   │ • Extract relevant sections                                   │ │
│   │ Time: 50-100ms per doc                                        │ │
│   └──────────────────────────────────────────────────────────────┘ │
│   ↓                                                                  │
│   ┌──────────────────────────────────────────────────────────────┐ │
│   │ Hypatia (Analyzer)                                            │ │
│   │ • Semantic analysis of content                                │ │
│   │ • Identify themes, concepts                                   │ │
│   │ Time: 100-200ms per doc                                       │ │
│   └──────────────────────────────────────────────────────────────┘ │
│   ↓                                                                  │
│   ┌──────────────────────────────────────────────────────────────┐ │
│   │ Mnemosyne (Extractor)                                         │ │
│   │ • Extract key insights                                        │ │
│   │ • Generate document-specific summary                          │ │
│   │ Time: 150-300ms per doc                                       │ │
│   └──────────────────────────────────────────────────────────────┘ │
│                                                                      │
│ Combine insights from all documents:                                │
│   • doc1_summary                                                    │
│   • doc2_summary                                                    │
│                                                                      │
│ LLM Synthesis:                                                       │
│   • Prompt: "Summarize the following documents: ..."                │
│   • Include both summaries                                          │
│   • Generate unified summary                                        │
│   Time: 2-4 seconds                                                 │
│                                                                      │
│ Total: 2.6-5.2 seconds for 2 documents                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Feedback Loop

```
┌─────────────────────────────────────────────────────────────────────┐
│                     USER FEEDBACK FLOW                               │
└─────────────────────────────────────────────────────────────────────┘

User clicks thumbs up/down on response:
  ↓
Frontend sends: POST /feedback
  {
    "query_id": "episode-uuid",
    "user_id": "user-uuid",
    "rating": 1,  // 1 (positive), -1 (negative), 0 (neutral)
    "comment": "Great answer!"  // optional
  }
  ↓
Backend processes feedback:
  ↓
  ┌──────────────────────────────────────────────────────────────────┐
  │ 1. Update Episodic Memory                                        │
  │    • UPDATE episodes SET feedback = 1 WHERE id = 'episode-uuid'  │
  │    • Affects future retrieval ranking                            │
  └──────────────────────────────────────────────────────────────────┘
  ↓
  ┌──────────────────────────────────────────────────────────────────┐
  │ 2. Update Procedural Memory                                      │
  │    • If positive: Strengthen applied patterns                    │
  │    • If negative: Weaken applied patterns                        │
  │    • Adjust confidence scores                                    │
  └──────────────────────────────────────────────────────────────────┘
  ↓
  ┌──────────────────────────────────────────────────────────────────┐
  │ 3. Update User Profile                                           │
  │    • Increment positive_feedback or negative_feedback            │
  │    • Recalculate avg_confidence                                  │
  └──────────────────────────────────────────────────────────────────┘
  ↓
  ┌──────────────────────────────────────────────────────────────────┐
  │ 4. Store Feedback Record                                         │
  │    • Log to feedback database                                    │
  │    • For analytics and system improvement                        │
  └──────────────────────────────────────────────────────────────────┘
  ↓
Return: { "success": true }
  ↓
Frontend shows: "Thank you for your feedback!"
```

---

## Session Management Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SESSION LIFECYCLE                                 │
└─────────────────────────────────────────────────────────────────────┘

╔════════════════════════════════════════════════════════════════════╗
║ SESSION CREATION                                                    ║
╚════════════════════════════════════════════════════════════════════╝

User opens application:
  ↓
Frontend checks localStorage for existing session:
  const sessionId = localStorage.getItem('sessionId');
  ↓
If no session:
  ↓
  POST /memory/session/create
    { "user_id": "user-uuid" }
    ↓
  Backend:
    • Generate session_id (UUID)
    • Create in Redis with TTL 1hr
    • Return session_id
    ↓
  Frontend:
    • localStorage.setItem('sessionId', session_id)
    • Store in React state
    ↓
If existing session:
  ↓
  GET /memory/session/{session_id}
    ↓
  Backend:
    • Check if session exists in Redis
    • If exists → Extend TTL, return session data
    • If expired → Create new session
    ↓
  Frontend:
    • Load session data
    • Restore conversation history

─────────────────────────────────────────────────────────────────────

╔════════════════════════════════════════════════════════════════════╗
║ SESSION UPDATE (Every Query)                                       ║
╚════════════════════════════════════════════════════════════════════╝

After each query-response cycle:
  ↓
Backend automatically:
  • Adds turn to session.conversation_history
  • Enforces 10-turn window
  • Updates last_activity timestamp
  • Extends TTL to 1hr (sliding expiration)
  ↓
No explicit frontend action required

─────────────────────────────────────────────────────────────────────

╔════════════════════════════════════════════════════════════════════╗
║ SESSION EXPIRATION                                                  ║
╚════════════════════════════════════════════════════════════════════╝

After 1 hour of inactivity:
  ↓
Redis TTL expires:
  • Session deleted from Redis
  • Conversation archived to SQLite (conversations.db)
  ↓
Next user action:
  ↓
Frontend sends request with expired session_id:
  ↓
Backend:
  • Session not found in Redis
  • Return 401 or create new session
  ↓
Frontend:
  • Clear localStorage
  • Create new session
  • Show: "Your session expired. Starting a new conversation."

─────────────────────────────────────────────────────────────────────

╔════════════════════════════════════════════════════════════════════╗
║ SESSION PERSISTENCE                                                 ║
╚════════════════════════════════════════════════════════════════════╝

All conversations saved permanently:
  • SQLite: conversations.db
  • Table: conversations, messages
  • Accessible via ChatSidebar
  • Can resume old conversations
```

---

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                      ERROR HANDLING FLOW                             │
└─────────────────────────────────────────────────────────────────────┘

Error occurs at any stage:
  ↓
┌──────────────────────────────────────────────────────────────────────┐
│ Backend Error Handling                                               │
│                                                                       │
│ Try-Except Blocks:                                                   │
│   try:                                                               │
│       # Process query                                                │
│   except OpenSearchConnectionError:                                  │
│       # Retry 3 times with exponential backoff                       │
│       # If still fails → Return error response                       │
│   except OllamaTimeoutError:                                         │
│       # Return cached response if available                          │
│       # Else return error                                            │
│   except Exception as e:                                             │
│       # Log error with full traceback                                │
│       # Return generic error response                                │
│                                                                       │
│ Error Response Format:                                               │
│   {                                                                  │
│     "error": true,                                                   │
│     "error_code": "SEARCH_FAILED",                                   │
│     "message": "Failed to retrieve documents",                       │
│     "retry_after": 5  // seconds                                     │
│   }                                                                  │
└──────────────────────────────────────────────────────────────────────┘
  ↓
SSE Event: error
  data: {error details}
  ↓
┌──────────────────────────────────────────────────────────────────────┐
│ Frontend Error Handling                                              │
│                                                                       │
│ EventSource 'error' listener:                                        │
│   eventSource.addEventListener('error', (event) => {                 │
│       const error = JSON.parse(event.data);                          │
│       setIsLoading(false);                                           │
│       showErrorMessage(error.message);                               │
│       eventSource.close();                                           │
│   });                                                                │
│                                                                       │
│ UI Update:                                                           │
│   • Display error message in chat                                    │
│   • Show retry button                                                │
│   • Log error to console                                             │
│   • Optionally report to error tracking service                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Performance Analysis

### Latency Breakdown (Typical Query)

```
Component                    Min      Avg      Max      % of Total
──────────────────────────────────────────────────────────────────
Frontend Input               0ms      0ms      0ms      0%
Request Formation            5ms      7ms      10ms     0.2%
API Gateway                  15ms     22ms     30ms     0.6%
Memory Context Loading       120ms    135ms    150ms    3.8%
Query Classification         200ms    300ms    400ms    8.5%
Document Retrieval           270ms    450ms    630ms    12.7%
Graph Expansion              150ms    200ms    250ms    5.6%
LLM Generation               2000ms   3500ms   5000ms   98.6%  ← BOTTLENECK
Quality Control              150ms    200ms    250ms    5.6%
Memory Storage               120ms    150ms    180ms    4.2%
Response Finalization        5ms      7ms      10ms     0.2%
Frontend Rendering           10ms     30ms     50ms     0.8%
──────────────────────────────────────────────────────────────────
TOTAL                        2900ms   3500ms   6600ms   100%
```

### Optimization Strategies

1. **LLM Optimization** (Biggest impact)
   - Use smaller model for simple queries
   - Implement response caching
   - Reduce max_tokens for concise answers

2. **Parallel Execution**
   - Already parallelized: Memory loading, quality control
   - Opportunity: Parallel graph expansion + retrieval

3. **Caching**
   - Cache frequent queries (implemented)
   - Cache embeddings for repeated documents
   - Cache reranking scores

4. **Reduce Network Latency**
   - HTTP/2 for multiplexing
   - Compression (gzip)

---

**Document Version**: 1.0
**Last Updated**: 2025-12-31
**Related Docs**: All previous architecture documents
