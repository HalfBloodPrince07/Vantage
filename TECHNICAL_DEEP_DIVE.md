# 🔬 Technical Deep Dive

> Step-by-step execution flow of every component in Vantage

---

## Table of Contents

1. [Application Startup](#application-startup)
2. [Search Execution Flow](#search-execution-flow)
3. [Document Ingestion Flow](#document-ingestion-flow)
4. [Agent Execution Details](#agent-execution-details)
5. [Frontend Component Flow](#frontend-component-flow)
6. [Database Schemas](#database-schemas)
7. [API Request/Response Examples](#api-requestresponse-examples)
8. [Error Handling & Fallbacks](#error-handling--fallbacks)

---

## Application Startup

### Backend Initialization Sequence

```python
# backend/api.py - on startup

1. LOAD CONFIGURATION
   ├── Read config.yaml
   ├── Parse model settings (ollama, embedding, reranker)
   └── Parse search settings (hybrid weights, reranker threshold)

2. INITIALIZE OPENSEARCH CLIENT
   ├── Connect to OpenSearch (localhost:9200)
   ├── Verify cluster health
   └── Create index if not exists (locallens_docs)

3. INITIALIZE EMBEDDING MODEL
   ├── Load SentenceTransformer (nomic-ai/nomic-embed-text-v1.5)
   ├── Detect CUDA/CPU device
   └── Log embedding dimension (768)

4. INITIALIZE RERANKER
   ├── Load CrossEncoder (ms-marco-MiniLM-L-6-v2)
   └── Configure diversity settings (MMR)

5. INITIALIZE ORCHESTRATOR
   ├── Create EnhancedOrchestrator instance
   ├── Initialize all agents (Athena, Proteus, etc.)
   ├── Build LangGraph workflow
   └── Compile state machine

6. INITIALIZE MEMORY SYSTEMS
   ├── MemoryManager (session context)
   ├── EpisodicMemory (long-term storage)
   └── FeedbackStore (user ratings)

7. START UVICORN SERVER
   └── Listen on 0.0.0.0:8000
```

### Frontend Initialization

```javascript
// App.jsx - on mount

1. CHECK AUTHENTICATION
   ├── Read localStorage('locallens_user')
   ├── If not logged in → Show LoginSettings
   └── If logged in → Show ChatInterface

2. CHATINTERFACE MOUNT
   ├── Initialize state (messages, steps, query)
   ├── Load conversation history from API
   └── Setup event handlers

3. DOCUMENT SELECTOR MOUNT
   ├── Fetch available documents
   └── Restore attached documents (if any)
```

---

## Search Execution Flow

### Complete Request Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: USER INPUT                                              │
│ User types: "Find documents about machine learning"            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: FRONTEND PROCESSING (ChatInterface.jsx)                 │
│                                                                 │
│ handleSearch() {                                                │
│   1. Create user message object                                 │
│   2. Add to messages state                                      │
│   3. Clear input field                                          │
│   4. Set loading = true                                         │
│   5. POST to /search/enhanced:                                  │
│      {                                                          │
│        query: "Find documents about machine learning",          │
│        user_id: "user_1",                                       │
│        conversation_id: "conv_abc123",                          │
│        attached_documents: []                                   │
│      }                                                          │
│   6. Open SSE connection for real-time steps                    │
│ }                                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: API LAYER (backend/api.py)                              │
│                                                                 │
│ @app.post("/search/enhanced")                                   │
│ async def enhanced_search(request):                             │
│   1. Extract query, user_id, conversation_id                    │
│   2. Get step_queue for SSE streaming                           │
│   3. Call orchestrator.process(query, context)                  │
│   4. Return: {results, response_message, confidence, steps}     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: ORCHESTRATOR (backend/orchestration/orchestrator.py)    │
│                                                                 │
│ class EnhancedOrchestrator:                                     │
│   async def process(query, context):                            │
│     1. Check attached_documents                                 │
│       - If attached → route_to_daedalus()                       │
│       - If empty → continue to Athena path                      │
│                                                                 │
│     2. Load session context from MemoryManager                  │
│       - Previous queries                                        │
│       - Relevant memories                                       │
│                                                                 │
│     3. Execute LangGraph workflow:                              │
│       classify_node → search_node → explain_node → finalize     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: CLASSIFICATION (Athena - query_classifier.py)           │
│                                                                 │
│ QueryClassifier.classify(query):                                │
│   1. Rule-based classification:                                 │
│      - Check for keywords: "find", "show", "list" → INFO_SEEK   │
│      - Check for keywords: "compare", "vs" → COMPARISON         │
│      - Check for file patterns: ".pdf", ".docx" → SPECIFIC_DOC  │
│                                                                 │
│   2. If confidence < 0.8, use LLM:                              │
│      prompt = "Classify this query: {query}"                    │
│      response = await call_ollama_json(prompt)                  │
│                                                                 │
│   3. Return:                                                    │
│      {                                                          │
│        intent: "INFO_SEEKING",                                  │
│        confidence: 0.85,                                        │
│        entities: ["machine learning"],                          │
│        should_search: true                                      │
│      }                                                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: STRATEGY SELECTION (Proteus - adaptive_retriever.py)    │
│                                                                 │
│ AdaptiveRetriever.select_strategy(query, intent):               │
│   1. Analyze query characteristics:                             │
│      - Length (short vs long)                                   │
│      - Specificity (entity names, dates)                        │
│      - Question type (factual vs exploratory)                   │
│                                                                 │
│   2. Select strategy:                                           │
│      "machine learning" → BROAD (conceptual topic)              │
│                                                                 │
│   3. Return:                                                    │
│      {                                                          │
│        strategy: "broad",                                       │
│        vector_weight: 0.7,                                      │
│        bm25_weight: 0.3,                                        │
│        top_k: 50                                                │
│      }                                                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: HYBRID SEARCH (opensearch_client.py)                    │
│                                                                 │
│ OpenSearchClient.hybrid_search(query, vector, top_k, filters):  │
│                                                                 │
│   1. Generate query embedding:                                  │
│      vector = embedding_model.encode(query)  # [768 dims]       │
│                                                                 │
│   2. Vector search (k-NN):                                      │
│      POST /{index}/_search                                      │
│      {                                                          │
│        "query": {                                               │
│          "knn": {                                               │
│            "vector_embedding": {                                │
│              "vector": [0.123, -0.456, ...],                    │
│              "k": 50                                            │
│            }                                                    │
│          }                                                      │
│        }                                                        │
│      }                                                          │
│                                                                 │
│   3. BM25 text search:                                          │
│      POST /{index}/_search                                      │
│      {                                                          │
│        "query": {                                               │
│          "multi_match": {                                       │
│            "query": "machine learning",                         │
│            "fields": ["detailed_summary^3", "full_content^2"]   │
│          }                                                      │
│        }                                                        │
│      }                                                          │
│                                                                 │
│   4. Reciprocal Rank Fusion:                                    │
│      for each doc:                                              │
│        score = (vector_weight / (k + vector_rank + 1)) +        │
│                (bm25_weight / (k + bm25_rank + 1))              │
│                                                                 │
│   5. Return top 50 combined results                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 8: RERANKING (reranker.py)                                 │
│                                                                 │
│ CrossEncoderReranker.rerank(query, documents, top_k=10):        │
│                                                                 │
│   1. Create query-doc pairs:                                    │
│      pairs = [(query, doc.summary) for doc in documents]        │
│                                                                 │
│   2. Score with cross-encoder:                                  │
│      scores = cross_encoder.predict(pairs)                      │
│                                                                 │
│   3. Apply diversity (MMR):                                     │
│      - Avoid similar documents scoring high                     │
│      - Balance relevance vs diversity                           │
│                                                                 │
│   4. Apply feedback boosts (if user_id provided):               │
│      boosts = feedback_store.get_boosts(user_id, query)         │
│      for doc in results:                                        │
│        doc.score += boosts.get(doc.id, 0)                       │
│                                                                 │
│   5. Return top 10 reranked results                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 9: QUALITY EVALUATION (Diogenes - critic_agent.py)         │
│                                                                 │
│ CriticAgent.evaluate_quality(query, results):                   │
│   1. Check result count                                         │
│   2. Analyze relevance scores                                   │
│   3. Detect potential hallucination risk                        │
│   4. Score overall quality (0.0 - 1.0)                          │
│                                                                 │
│   Return: {quality_score: 0.82, issues: [], suggestions: []}    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 10: EXPLANATION (Hermes - explanation_agent.py)            │
│                                                                 │
│ ExplanationAgent.explain_results(query, results):               │
│   1. Generate natural language response                         │
│   2. Explain why results are relevant                           │
│   3. Add suggested follow-up questions                          │
│                                                                 │
│   Return: "I found 10 documents about machine learning..."      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 11: CONFIDENCE SCORING (Themis - confidence_scorer.py)     │
│                                                                 │
│ ConfidenceScorer.score(query, results, quality):                │
│   1. Evidence strength assessment                               │
│   2. Source count weighting                                     │
│   3. Query-result alignment check                               │
│                                                                 │
│   Return: {                                                     │
│     confidence: 0.85,                                           │
│     evidence_strength: "strong",                                │
│     supporting_sources: 8                                       │
│   }                                                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 12: RESPONSE ASSEMBLY                                      │
│                                                                 │
│ Final response to frontend:                                     │
│ {                                                               │
│   "results": [                                                  │
│     {                                                           │
│       "id": "abc123",                                           │
│       "filename": "ML_Guide.pdf",                               │
│       "detailed_summary": "This document explains...",          │
│       "score": 0.92,                                            │
│       "file_path": "C:/Documents/ML_Guide.pdf",                 │
│       "file_type": ".pdf",                                      │
│       "entities": ["neural networks", "deep learning"],         │
│       "keywords": "machine learning, AI, algorithms"            │
│     },                                                          │
│     ...                                                         │
│   ],                                                            │
│   "response_message": "Found 10 documents about ML...",         │
│   "confidence": 0.85,                                           │
│   "evidence_strength": {"level": "strong", "sources": 8},       │
│   "suggested_followups": ["What are neural networks?", ...],    │
│   "steps": [                                                    │
│     {"agent": "Athena", "action": "Classifying query..."},      │
│     {"agent": "Proteus", "action": "Selecting strategy..."},    │
│     ...                                                         │
│   ],                                                            │
│   "search_time": 1.23                                           │
│ }                                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 13: FRONTEND RENDER (ChatInterface.jsx)                    │
│                                                                 │
│ 1. Add assistant message to messages state                      │
│ 2. Render ResultCard/ResultItem for each result                 │
│ 3. Display confidence badge                                     │
│ 4. Show thinking steps (collapsible)                            │
│ 5. Render follow-up suggestions as clickable buttons            │
│ 6. Set loading = false                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Document Ingestion Flow

### File Processing Sequence

```
┌─────────────────────────────────────────────────────────────────┐
│ TRIGGER: User clicks "Start Indexing" in SettingsPanel          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ POST /index/start {directory: "C:/Documents"}                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ IngestionPipeline.process_directory(directory, task_id):        │
│                                                                 │
│   1. DISCOVER FILES                                             │
│      files = directory.rglob("*.pdf", "*.docx", ...)            │
│      total = len(files)  # e.g., 150 files                      │
│                                                                 │
│   2. BATCH PROCESSING (batch_size = 5)                          │
│      for batch in chunks(files, 5):                             │
│        await process_batch(batch)                               │
│        emit_progress(processed / total)                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ IngestionPipeline.process_file(file_path):                      │
│                                                                 │
│   1. CHECK IF EXISTS                                            │
│      doc_id = md5(file_path)                                    │
│      if await opensearch.document_exists(doc_id):               │
│        return {"status": "skipped"}                             │
│                                                                 │
│   2. EXTRACT CONTENT (based on file type)                       │
│      ┌────────────────────────────────────────────────────────┐ │
│      │ .pdf  → PdfReader.pages[].extract_text()               │ │
│      │ .docx → Document(file).paragraphs                      │ │
│      │ .txt  → file.read()                                    │ │
│      │ .xlsx → pd.read_excel() → DataFrame.to_string()        │ │
│      │ .png  → Ollama vision: "Describe this image"           │ │
│      └────────────────────────────────────────────────────────┘ │
│                                                                 │
│   3. GENERATE SUMMARY (LLM)                                     │
│      prompt = """                                               │
│        Analyze this document and provide:                       │
│        SUMMARY: [detailed summary]                              │
│        KEYWORDS: [comma-separated]                              │
│        ENTITIES: [people, orgs, locations]                      │
│        TOPICS: [main topics]                                    │
│        RELATIONSHIPS: [entity1 -> relation -> entity2]          │
│      """                                                        │
│      response = await call_ollama(prompt, content[:8000])       │
│                                                                 │
│   4. PARSE RESPONSE                                             │
│      parsed = _parse_detailed_response(response)                │
│      # Extract: summary, keywords, entities, topics, relations  │
│                                                                 │
│   5. GENERATE EMBEDDING                                         │
│      embedding = embedding_model.encode(summary)                │
│      # Returns: [768 float values]                              │
│                                                                 │
│   6. BUILD DOCUMENT OBJECT                                      │
│      document = {                                               │
│        "id": doc_id,                                            │
│        "filename": "report.pdf",                                │
│        "file_path": "C:/Documents/report.pdf",                  │
│        "file_type": ".pdf",                                     │
│        "detailed_summary": "This report covers...",             │
│        "full_content": "[first 50000 chars]",                   │
│        "keywords": "quarterly, revenue, growth",                │
│        "entities": ["Q3 2024", "Sales Dept"],                   │
│        "topics": ["finance", "reporting"],                      │
│        "vector_embedding": [0.123, -0.456, ...],                │
│        "word_count": 5230,                                      │
│        "page_count": 12,                                        │
│        "file_size_bytes": 1048576,                              │
│        "created_at": "2024-01-15T10:30:00Z"                     │
│      }                                                          │
│                                                                 │
│   7. INDEX TO OPENSEARCH                                        │
│      await opensearch.index_document(document)                  │
│                                                                 │
│   8. INDEX TO KNOWLEDGE GRAPH                                   │
│      if entities or relationships:                              │
│        await _index_to_knowledge_graph(                         │
│          doc_id, filename, entities, relationships              │
│        )                                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Agent Execution Details

### Athena (Query Classifier)

```python
# Intent Classification Logic

INTENT_PATTERNS = {
    "SPECIFIC_DOCUMENT": [
        r"find.*specific",
        r"show me.*file",
        r"open.*document"
    ],
    "INFORMATION_SEEKING": [
        r"what is",
        r"how does",
        r"explain"
    ],
    "COMPARISON": [
        r"compare",
        r"difference between",
        r"vs\.?"
    ],
    "AGGREGATION": [
        r"list all",
        r"show me all",
        r"how many"
    ]
}

# Classification flow:
1. Try rule-based matching (fast, no LLM)
2. If no match or low confidence → LLM classification
3. Return intent + confidence + extracted entities
```

### Daedalus (Document Mode)

```python
# When user has attached documents

DAEDALUS_PIPELINE = [
    "Prometheus: Extract key content from attached docs",
    "Hypatia: Analyze content for the specific query",
    "Mnemosyne: Check memory for related context",
    "Daedalus: Synthesize final response"
]

# Process:
1. Load full content of attached documents from OpenSearch
2. Build focused context (summaries + relevant sections)
3. Generate response using only attached document context
4. Return with "document_mode": true flag
```

---

## Frontend Component Flow

### ChatInterface State Machine

```
                 ┌──────────────┐
                 │    IDLE      │
                 │ (query="")   │
                 └──────┬───────┘
                        │ User types
                        ▼
                 ┌──────────────┐
                 │   TYPING     │
                 │ (query="...")│
                 └──────┬───────┘
                        │ Submit
                        ▼
                 ┌──────────────┐
                 │   LOADING    │
                 │ (loading=T)  │◄──────────┐
                 └──────┬───────┘           │
                        │ Response          │ Retry
                        ▼                   │
                 ┌──────────────┐           │
                 │   DISPLAY    │───────────┘
                 │ (results)    │
                 └──────┬───────┘
                        │ New query
                        ▼
                 ┌──────────────┐
                 │    IDLE      │
                 └──────────────┘
```

### EntityGraphModal Flow

```javascript
// User clicks 📊 Graph button

1. handleViewGraph(docId, filename)
   └── setGraphModal({isOpen: true, documentId, documentName})

2. EntityGraphModal mounts
   └── useEffect → fetchEntityData()

3. GET /documents/{id}/entities
   └── Returns: {entities, keywords, topics, graph}

4. drawGraph(canvas, graph)
   ├── Position nodes radially
   ├── Draw edges (lines)
   └── Draw nodes (circles with labels)

5. Render legend + tag cloud
```

---

## Database Schemas

### OpenSearch Index (locallens_docs)

```json
{
  "mappings": {
    "properties": {
      "id": {"type": "keyword"},
      "filename": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
      "file_path": {"type": "keyword"},
      "file_type": {"type": "keyword"},
      "content_type": {"type": "keyword"},
      "document_type": {"type": "keyword"},
      "is_image": {"type": "boolean"},
      "detailed_summary": {"type": "text", "analyzer": "content_analyzer"},
      "full_content": {"type": "text", "analyzer": "content_analyzer"},
      "keywords": {"type": "text"},
      "entities": {"type": "keyword"},
      "topics": {"type": "keyword"},
      "vector_embedding": {
        "type": "knn_vector",
        "dimension": 768,
        "method": {"name": "hnsw", "space_type": "innerproduct"}
      },
      "word_count": {"type": "integer"},
      "page_count": {"type": "integer"},
      "file_size_bytes": {"type": "long"},
      "created_at": {"type": "date"},
      "last_modified": {"type": "date"}
    }
  }
}
```

### SQLite: Conversations (locallens_conversations.db)

```sql
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    metadata TEXT,  -- JSON: results, confidence, steps
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);
```

### SQLite: Feedback (locallens.db)

```sql
CREATE TABLE feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    query TEXT NOT NULL,
    document_id TEXT NOT NULL,
    feedback_score INTEGER,  -- 1 (helpful) or -1 (not helpful)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### SQLite: Knowledge Graph (locallens_graph.db)

```sql
CREATE TABLE entities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    properties TEXT,  -- JSON
    document_ids TEXT,  -- JSON array
    created_at TIMESTAMP
);

CREATE TABLE relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    properties TEXT,
    document_id TEXT
);
```

---

## API Request/Response Examples

### Search Request

```bash
curl -X POST http://localhost:8000/search/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find documents about machine learning",
    "user_id": "user_123",
    "conversation_id": "conv_456",
    "attached_documents": []
  }'
```

### Search Response

```json
{
  "results": [
    {
      "id": "a1b2c3d4",
      "filename": "ML_Handbook.pdf",
      "detailed_summary": "Comprehensive guide to machine learning covering supervised learning, neural networks, and practical applications...",
      "score": 0.92,
      "file_path": "C:/Documents/ML_Handbook.pdf",
      "file_type": ".pdf",
      "file_size_bytes": 2456789,
      "entities": ["neural networks", "TensorFlow", "scikit-learn"],
      "keywords": "machine learning, AI, deep learning, algorithms"
    }
  ],
  "response_message": "I found 8 documents related to machine learning. The most relevant is 'ML_Handbook.pdf' which provides a comprehensive overview...",
  "confidence": 0.88,
  "evidence_strength": {
    "level": "strong",
    "supporting_sources": 6
  },
  "suggested_followups": [
    "What are the main types of machine learning?",
    "How does deep learning differ from traditional ML?"
  ],
  "steps": [
    {
      "agent": "Athena",
      "action": "Classified as information-seeking query",
      "timestamp": "2024-01-15T10:30:01Z"
    },
    {
      "agent": "Proteus",
      "action": "Selected 'broad' retrieval strategy",
      "timestamp": "2024-01-15T10:30:02Z"
    }
  ],
  "search_time": 1.45
}
```

---

## Error Handling & Fallbacks

### Search Fallback Chain

```
1. Hybrid Search Fails
   └── Fallback: Vector-only search

2. Vector Search Fails
   └── Fallback: BM25-only search

3. All Search Fails
   └── Return: "No results found"

4. LLM Classification Fails
   └── Fallback: Rule-based classification

5. Reranker Fails
   └── Fallback: Return unreranked results

6. Response Generation Fails
   └── Fallback: "Found {n} results for your query"
```

### LLM Response Sanitization

```python
# sanitize_llm_response() handles:
1. Markdown code blocks: ```json ... ```
2. Text before/after JSON
3. Multiple JSON objects
4. Empty responses → {}
5. Invalid JSON → original text
```

---

<p align="center">
  <i>Document version: 2024-12-17</i>
</p>
