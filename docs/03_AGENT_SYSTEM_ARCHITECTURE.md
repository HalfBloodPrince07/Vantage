# VANTAGE - Agent System Architecture (Deep Dive)

## Table of Contents
- [Agent System Overview](#agent-system-overview)
- [Zeus Orchestrator (LangGraph)](#zeus-orchestrator-langgraph)
- [Query Classification & Routing](#query-classification--routing)
- [Specialized Agents](#specialized-agents)
- [Document Processing Agents](#document-processing-agents)
- [Agent Communication](#agent-communication)
- [State Management](#state-management)

---

## Agent System Overview

The Vantage agent system is built on a **multi-agent architecture** where specialized agents collaborate to handle different aspects of document search and knowledge management. The system uses **Greek mythology-themed naming** for memorability and clear role definition.

### Agent Hierarchy

```
┌─────────────────────────────────────────────────────────────────────┐
│                    VANTAGE AGENT HIERARCHY                           │
└─────────────────────────────────────────────────────────────────────┘

                        ┌──────────────────┐
                        │      ZEUS        │
                        │  (Orchestrator)  │
                        │   [LangGraph]    │
                        └──────────────────┘
                                │
                                ▼
                        ┌──────────────────┐
                        │     ATHENA       │
                        │(Query Classifier)│
                        └──────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
        ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
        │ ATHENA PATH  │ │ GENERAL PATH │ │DAEDALUS PATH │
        │ (Doc Search) │ │  (LLM Only)  │ │ (Doc Agents) │
        └──────────────┘ └──────────────┘ └──────────────┘
                │                                   │
                ▼                                   ▼
    ┌───────────────────────────┐         ┌─────────────────┐
    │   SEARCH & RAG AGENTS     │         │ DOCUMENT AGENTS │
    │                           │         │                 │
    │  • Apollo (Graph RAG)     │         │ • Prometheus    │
    │  • Odysseus (Reasoning)   │         │ • Hypatia       │
    │  • Proteus (Adaptive)     │         │ • Mnemosyne     │
    │  • Themis (Confidence)    │         └─────────────────┘
    │  • Diogenes (Critic)      │
    │  • Socrates (Clarify)     │
    │  • Aristotle (Analysis)   │
    │  • Thoth (Summarize)      │
    │  • Hermes (Explanation)   │
    │  • Sisyphus (Retrieval)   │
    └───────────────────────────┘
```

### Agent Directory Structure

```
backend/agents/
│
├── __init__.py
│
├── query_classifier.py          # Athena (Query Intent Classification)
├── graph_rag_agent.py           # Apollo (Graph-based RAG)
├── reasoning_planner.py         # Odysseus (Multi-hop Reasoning)
├── adaptive_retriever.py        # Proteus (Adaptive Retrieval)
├── confidence_scorer.py         # Themis (Confidence Scoring)
├── critic_agent.py              # Diogenes (Quality Control)
├── clarification_agent.py       # Socrates (Clarifying Questions)
├── analysis_agent.py            # Aristotle (Document Analysis)
├── summarization_agent.py       # Thoth (Multi-doc Summarization)
├── explanation_agent.py         # Hermes (Search Explanation)
├── retrieval_controller.py      # Sisyphus (Corrective Retrieval)
│
└── document_agents/
    ├── __init__.py
    ├── daedalus_orchestrator.py # Daedalus (Document Workflow Orchestrator)
    ├── prometheus_reader.py     # Prometheus (Content Extraction)
    ├── hypatia_analyzer.py      # Hypatia (Semantic Analysis)
    └── mnemosyne_extractor.py   # Mnemosyne (Insight Extraction)
```

---

## Zeus Orchestrator (LangGraph)

**File**: `backend/orchestration/orchestrator.py`

Zeus is the master orchestrator that manages the entire agent workflow using **LangGraph** (a state machine framework from LangChain).

```
┌─────────────────────────────────────────────────────────────────────┐
│                          ZEUS ORCHESTRATOR                           │
│                         (LangGraph StateGraph)                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  WORKFLOW STATE SCHEMA                                          │ │
│  │                                                                  │ │
│  │  class WorkflowState(TypedDict):                                │ │
│  │      query: str                      # User's query             │ │
│  │      intent: str                     # Classified intent        │ │
│  │      attached_documents: List[str]   # Attached doc IDs         │ │
│  │      session_context: Dict           # Conversation history     │ │
│  │      search_results: List[Dict]      # Retrieved documents      │ │
│  │      graph_context: Dict             # Graph expansion results  │ │
│  │      intermediate_steps: List[Dict]  # Agent thinking steps     │ │
│  │      response: str                   # Final response           │ │
│  │      confidence_score: float         # Confidence (0-1)         │ │
│  │      error: Optional[str]            # Error message if any     │ │
│  │      metadata: Dict                  # Additional metadata      │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  WORKFLOW GRAPH STRUCTURE                                       │ │
│  │                                                                  │ │
│  │  START                                                           │ │
│  │    ↓                                                             │ │
│  │  [load_session_context]                                         │ │
│  │    • Load conversation history from Memory Manager              │ │
│  │    • Retrieve user profile                                      │ │
│  │    ↓                                                             │ │
│  │  [classify_intent]  (Athena Agent)                              │ │
│  │    • Classify query intent                                      │ │
│  │    • Options: DOCUMENT_SEARCH, GENERAL_KNOWLEDGE,               │ │
│  │               COMPARISON, SUMMARIZATION, ANALYSIS,              │ │
│  │               CLARIFICATION_NEEDED                              │ │
│  │    ↓                                                             │ │
│  │  [route_query]  (Conditional Router)                            │ │
│  │    ├─> If DOCUMENT_SEARCH → [athena_path]                       │ │
│  │    ├─> If GENERAL_KNOWLEDGE → [general_path]                    │ │
│  │    ├─> If has attached_documents → [daedalus_path]              │ │
│  │    └─> If CLARIFICATION_NEEDED → [clarify]                      │ │
│  │                                                                  │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │  ATHENA PATH (Document Search)                            │  │ │
│  │  │                                                            │  │ │
│  │  │  [expand_query]  (Odysseus - optional)                    │  │ │
│  │  │    • Multi-hop reasoning                                  │  │ │
│  │  │    • Query decomposition if complex                       │  │ │
│  │  │    ↓                                                       │  │ │
│  │  │  [retrieve_documents]  (Proteus)                          │  │ │
│  │  │    • Adaptive retrieval strategy                          │  │ │
│  │  │    • Hybrid search (vector + BM25)                        │  │ │
│  │  │    • Rerank with cross-encoder                            │  │ │
│  │  │    ↓                                                       │  │ │
│  │  │  [expand_graph_context]  (Apollo - optional)              │  │ │
│  │  │    • Extract entities from top results                    │  │ │
│  │  │    • Traverse knowledge graph                             │  │ │
│  │  │    • Add related context                                  │  │ │
│  │  │    ↓                                                       │  │ │
│  │  │  [generate_response]  (Ollama LLM)                        │  │ │
│  │  │    • Combine query + documents + graph context            │  │ │
│  │  │    • Stream response generation                           │  │ │
│  │  └────────────────────────────────────────────────────────────┘  │ │
│  │                                                                  │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │  GENERAL PATH (No Document Search)                        │  │ │
│  │  │                                                            │  │ │
│  │  │  [generate_direct_response]  (Ollama LLM)                 │  │ │
│  │  │    • Direct LLM call without document retrieval           │  │ │
│  │  │    • Use only conversation context                        │  │ │
│  │  └────────────────────────────────────────────────────────────┘  │ │
│  │                                                                  │ │
│  │  ┌──────────────────────────────────────────────────────────┐  │ │
│  │  │  DAEDALUS PATH (Document-Attached Queries)                │  │ │
│  │  │                                                            │  │ │
│  │  │  [daedalus_orchestrate]                                   │  │ │
│  │  │    ↓                                                       │  │ │
│  │  │  [prometheus_read]  (Content Extraction)                  │  │ │
│  │  │    ↓                                                       │  │ │
│  │  │  [hypatia_analyze]  (Semantic Analysis)                   │  │ │
│  │  │    ↓                                                       │  │ │
│  │  │  [mnemosyne_extract]  (Insight Extraction)                │  │ │
│  │  └────────────────────────────────────────────────────────────┘  │ │
│  │                                                                  │ │
│  │  ↓ (All paths converge)                                         │ │
│  │                                                                  │ │
│  │  [quality_control]                                              │ │
│  │    ├─> [themis_score]  (Confidence Scoring)                    │ │
│  │    └─> [diogenes_critique]  (Hallucination Detection)          │ │
│  │    ↓                                                             │ │
│  │  [check_quality]  (Conditional)                                 │ │
│  │    ├─> If confidence < 0.5 → [sisyphus_retry]                  │ │
│  │    └─> If confidence >= 0.5 → [finalize]                       │ │
│  │    ↓                                                             │ │
│  │  [finalize]                                                      │ │
│  │    • Format response with citations                             │ │
│  │    • Add thinking steps to response                             │ │
│  │    • Store in episodic memory                                   │ │
│  │    • Update user profile                                        │ │
│  │    ↓                                                             │ │
│  │  END                                                             │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  PARALLEL EXECUTION                                             │ │
│  │                                                                  │ │
│  │  Zeus can execute multiple agents in parallel:                  │ │
│  │                                                                  │ │
│  │  • Max concurrent agents: 3 (configurable)                      │ │
│  │  • Example parallelization:                                     │ │
│  │    [retrieve_documents] || [expand_graph_context]               │ │
│  │    (Both run simultaneously, wait for both to complete)         │ │
│  │                                                                  │ │
│  │  Benefits:                                                       │ │
│  │    • Reduced latency (2-3x speedup)                             │ │
│  │    • Better resource utilization                                │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  ERROR HANDLING & RECOVERY                                      │ │
│  │                                                                  │ │
│  │  • Retry logic: Max 2 retries per agent                         │ │
│  │  • Fallback strategies:                                         │ │
│  │    - If search fails → Try simplified query                     │ │
│  │    - If LLM fails → Use cached response (if available)          │ │
│  │    - If agent crashes → Skip agent, log error, continue         │ │
│  │  • Timeout: 60 seconds per workflow                             │ │
│  │  • Partial results: Return best-effort response on timeout      │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  CONFIGURATION                                                  │ │
│  │                                                                  │ │
│  │  orchestration:                                                  │ │
│  │    langgraph_enabled: true                                       │ │
│  │    parallel_execution: true                                      │ │
│  │    max_concurrent_agents: 3                                      │ │
│  │    workflow_timeout: 60  # seconds                               │ │
│  │    retry_attempts: 2                                             │ │
│  │    enable_thinking_steps: true  # SSE streaming                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Query Classification & Routing

### Athena (Query Classifier)

**File**: `backend/agents/query_classifier.py`

```
┌─────────────────────────────────────────────────────────────────────┐
│                       ATHENA - QUERY CLASSIFIER                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  PURPOSE: Classify user queries to route to appropriate agents       │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  CLASSIFICATION TAXONOMY                                        │ │
│  │                                                                  │ │
│  │  1. DOCUMENT_SEARCH                                             │ │
│  │     • Queries about document contents                           │ │
│  │     • Examples:                                                  │ │
│  │       - "What are the key findings in my papers?"               │ │
│  │       - "Find documents about neural networks"                  │ │
│  │       - "Show me all PDFs from 2024"                            │ │
│  │                                                                  │ │
│  │  2. GENERAL_KNOWLEDGE                                           │ │
│  │     • Factual questions not requiring document search           │ │
│  │     • Examples:                                                  │ │
│  │       - "What is machine learning?"                             │ │
│  │       - "Explain transformers"                                  │ │
│  │       - "How does BERT work?"                                   │ │
│  │                                                                  │ │
│  │  3. COMPARISON                                                  │ │
│  │     • Compare multiple documents or concepts                    │ │
│  │     • Examples:                                                  │ │
│  │       - "Compare GPT-4 and BERT"                                │ │
│  │       - "What's the difference between these papers?"           │ │
│  │                                                                  │ │
│  │  4. SUMMARIZATION                                               │ │
│  │     • Summarize document(s) or topics                           │ │
│  │     • Examples:                                                  │ │
│  │       - "Summarize all my research papers"                      │ │
│  │       - "Give me a summary of this PDF"                         │ │
│  │                                                                  │ │
│  │  5. ANALYSIS                                                    │ │
│  │     • Deep analysis, trends, patterns                           │ │
│  │     • Examples:                                                  │ │
│  │       - "Analyze trends in my reading list"                     │ │
│  │       - "What topics appear most frequently?"                   │ │
│  │                                                                  │ │
│  │  6. CLARIFICATION_NEEDED                                        │ │
│  │     • Ambiguous or unclear queries                              │ │
│  │     • Examples:                                                  │ │
│  │       - "that thing"                                            │ │
│  │       - "show me"                                               │ │
│  │                                                                  │ │
│  │  7. SYSTEM_META                                                 │ │
│  │     • Questions about the system itself                         │ │
│  │     • Examples:                                                  │ │
│  │       - "How does search work?"                                 │ │
│  │       - "What can you do?"                                      │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  CLASSIFICATION PROCESS                                         │ │
│  │                                                                  │ │
│  │  Input: User query                                              │ │
│  │                                                                  │ │
│  │  Step 1: Feature Extraction                                     │ │
│  │    • Query length                                               │ │
│  │    • Contains document-specific terms? (PDF, file, document)    │ │
│  │    • Contains comparison words? (vs, compare, difference)       │ │
│  │    • Contains summary words? (summarize, overview, tldr)        │ │
│  │    • Contains analysis words? (trend, pattern, analyze)         │ │
│  │    • Interrogative type? (what, how, why, when, where)          │ │
│  │                                                                  │ │
│  │  Step 2: LLM Classification                                     │ │
│  │    • Prompt Template:                                           │ │
│  │      "Classify the following query into one of these categories:│ │
│  │       DOCUMENT_SEARCH, GENERAL_KNOWLEDGE, COMPARISON,           │ │
│  │       SUMMARIZATION, ANALYSIS, CLARIFICATION_NEEDED,            │ │
│  │       SYSTEM_META                                               │ │
│  │                                                                  │ │
│  │       Query: {user_query}                                       │ │
│  │       Context: {session_context}                                │ │
│  │                                                                  │ │
│  │       Respond with ONLY the category name."                     │ │
│  │                                                                  │ │
│  │    • Model: qwen3-vl:8b                                         │ │
│  │    • Temperature: 0.0 (deterministic)                           │ │
│  │    • Max tokens: 50                                             │ │
│  │                                                                  │ │
│  │  Step 3: Confidence Scoring                                     │ │
│  │    • Parse LLM response                                         │ │
│  │    • Validate category                                          │ │
│  │    • Assign confidence based on clarity                         │ │
│  │                                                                  │ │
│  │  Output:                                                         │ │
│  │    {                                                             │ │
│  │      "intent": "DOCUMENT_SEARCH",                               │ │
│  │      "confidence": 0.95,                                         │ │
│  │      "reasoning": "Query asks about document contents"          │ │
│  │    }                                                             │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  ROUTING LOGIC                                                  │ │
│  │                                                                  │ │
│  │  if intent == "DOCUMENT_SEARCH":                                │ │
│  │      route_to: athena_path (hybrid search workflow)             │ │
│  │                                                                  │ │
│  │  elif intent == "GENERAL_KNOWLEDGE":                            │ │
│  │      route_to: general_path (direct LLM)                        │ │
│  │                                                                  │ │
│  │  elif intent in ["COMPARISON", "ANALYSIS"]:                     │ │
│  │      route_to: athena_path → aristotle_agent                    │ │
│  │                                                                  │ │
│  │  elif intent == "SUMMARIZATION":                                │ │
│  │      route_to: athena_path → thoth_agent                        │ │
│  │                                                                  │ │
│  │  elif intent == "CLARIFICATION_NEEDED":                         │ │
│  │      route_to: socrates_agent (generate questions)              │ │
│  │                                                                  │ │
│  │  elif intent == "SYSTEM_META":                                  │ │
│  │      route_to: hermes_agent (explain system)                    │ │
│  │                                                                  │ │
│  │  if has_attached_documents:                                     │ │
│  │      override_route_to: daedalus_path (document agents)         │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  PERFORMANCE METRICS                                            │ │
│  │                                                                  │ │
│  │  • Classification accuracy: ~92%                                │ │
│  │  • Avg latency: 200-400ms                                       │ │
│  │  • Fallback: If uncertain, default to DOCUMENT_SEARCH          │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Specialized Agents

### Apollo (Graph RAG Agent)

**File**: `backend/agents/graph_rag_agent.py`

```
┌─────────────────────────────────────────────────────────────────────┐
│                      APOLLO - GRAPH RAG AGENT                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  PURPOSE: Enhance search results with knowledge graph context        │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  WORKFLOW                                                       │ │
│  │                                                                  │ │
│  │  Input: Top K search results (e.g., 5 documents)                │ │
│  │                                                                  │ │
│  │  Step 1: Entity Extraction                                      │ │
│  │    • Extract entities from document summaries                   │ │
│  │    • Entity types: PERSON, ORG, LOCATION, CONCEPT, DATE         │ │
│  │    • Use spaCy NER or LLM-based extraction                      │ │
│  │                                                                  │ │
│  │  Step 2: Graph Traversal                                        │ │
│  │    • Query knowledge graph for related entities                 │ │
│  │    • Traverse relationships (1-2 hops)                          │ │
│  │    • Example:                                                    │ │
│  │      Document mentions "GPT-4"                                  │ │
│  │        → Graph lookup: GPT-4 (entity)                           │ │
│  │        → Related: OpenAI (organization)                         │ │
│  │        → Related: Transformers (concept)                        │ │
│  │        → Related: BERT (concept, co-occurrence)                 │ │
│  │                                                                  │ │
│  │  Step 3: Context Expansion                                      │ │
│  │    • Retrieve documents linked to related entities              │ │
│  │    • Rank by graph distance and relevance                       │ │
│  │    • Add top 3 related documents to context                     │ │
│  │                                                                  │ │
│  │  Step 4: Context Synthesis                                      │ │
│  │    • Combine original results + graph-expanded results          │ │
│  │    • Deduplicate by document ID                                 │ │
│  │    • Rerank combined set                                        │ │
│  │                                                                  │ │
│  │  Output:                                                         │ │
│  │    {                                                             │ │
│  │      "expanded_results": [...],  # Original + graph results     │ │
│  │      "graph_context": {                                         │ │
│  │        "entities": [...],                                       │ │
│  │        "relationships": [...],                                  │ │
│  │        "expansion_paths": [...]                                 │ │
│  │      }                                                           │ │
│  │    }                                                             │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  CONFIGURATION                                                  │ │
│  │                                                                  │ │
│  │  graph_rag:                                                      │ │
│  │    enabled: true                                                 │ │
│  │    max_hops: 2                                                   │ │
│  │    max_related_docs: 3                                           │ │
│  │    min_relationship_strength: 0.3                                │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Odysseus (Reasoning & Planning Agent)

**File**: `backend/agents/reasoning_planner.py`

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ODYSSEUS - REASONING & PLANNING                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  PURPOSE: Handle complex multi-hop reasoning and query decomposition │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  CAPABILITIES                                                   │ │
│  │                                                                  │ │
│  │  1. Query Decomposition                                         │ │
│  │     Complex query → Sub-queries                                 │ │
│  │     Example:                                                     │ │
│  │       "Compare the methodologies used in my ML papers and       │ │
│  │        identify common datasets"                                │ │
│  │       ↓                                                          │ │
│  │       Sub-query 1: "Find all machine learning papers"           │ │
│  │       Sub-query 2: "Extract methodologies from each paper"      │ │
│  │       Sub-query 3: "Extract datasets from each paper"           │ │
│  │       Sub-query 4: "Compare methodologies"                      │ │
│  │       Sub-query 5: "Identify common datasets"                   │ │
│  │                                                                  │ │
│  │  2. Multi-Hop Reasoning                                         │ │
│  │     Chain multiple retrieval steps                              │ │
│  │     Example:                                                     │ │
│  │       Hop 1: Retrieve papers about "transformers"               │ │
│  │       Hop 2: From those, find papers citing "attention"         │ │
│  │       Hop 3: From those, find papers with code                  │ │
│  │                                                                  │ │
│  │  3. Query Expansion                                             │ │
│  │     Expand query with synonyms and related terms                │ │
│  │     Example:                                                     │ │
│  │       "machine learning" →                                      │ │
│  │       ["machine learning", "ML", "deep learning",               │ │
│  │        "neural networks", "AI models"]                          │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  WORKFLOW                                                       │ │
│  │                                                                  │ │
│  │  Input: Complex query                                           │ │
│  │                                                                  │ │
│  │  Step 1: Complexity Analysis                                    │ │
│  │    • Count number of sub-questions                              │ │
│  │    • Identify conjunctions (and, or, but)                       │ │
│  │    • Detect multi-step requirements                             │ │
│  │                                                                  │ │
│  │  Step 2: Planning                                               │ │
│  │    • If complex → Decompose into sub-queries                    │ │
│  │    • If simple → Expand terms                                   │ │
│  │    • Generate execution plan                                    │ │
│  │                                                                  │ │
│  │  Step 3: Execution                                              │ │
│  │    • Execute sub-queries sequentially or in parallel            │ │
│  │    • Aggregate results                                          │ │
│  │    • Synthesize final answer                                    │ │
│  │                                                                  │ │
│  │  Output:                                                         │ │
│  │    {                                                             │ │
│  │      "plan": [...],  # Execution steps                          │ │
│  │      "expanded_queries": [...],                                 │ │
│  │      "results_per_step": [...]                                  │ │
│  │    }                                                             │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Themis (Confidence Scorer)

**File**: `backend/agents/confidence_scorer.py`

```
┌─────────────────────────────────────────────────────────────────────┐
│                     THEMIS - CONFIDENCE SCORER                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  PURPOSE: Assess confidence and quality of generated responses       │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  SCORING FACTORS                                                │ │
│  │                                                                  │ │
│  │  1. Retrieval Quality (40% weight)                              │ │
│  │     • Top document score                                        │ │
│  │     • Score distribution (gap between top & 2nd)                │ │
│  │     • Number of results above threshold                         │ │
│  │                                                                  │ │
│  │  2. Response Grounding (30% weight)                             │ │
│  │     • Overlap between response and source documents             │ │
│  │     • Citation presence                                         │ │
│  │     • Factual consistency check                                 │ │
│  │                                                                  │ │
│  │  3. Coherence (20% weight)                                      │ │
│  │     • Response length appropriateness                           │ │
│  │     • Grammatical correctness                                   │ │
│  │     • Logical flow                                              │ │
│  │                                                                  │ │
│  │  4. Completeness (10% weight)                                   │ │
│  │     • All parts of query addressed                              │ │
│  │     • Sufficient detail provided                                │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  SCORING PROCESS                                                │ │
│  │                                                                  │ │
│  │  confidence_score =                                              │ │
│  │    0.4 * retrieval_score +                                       │ │
│  │    0.3 * grounding_score +                                       │ │
│  │    0.2 * coherence_score +                                       │ │
│  │    0.1 * completeness_score                                      │ │
│  │                                                                  │ │
│  │  Output range: [0.0, 1.0]                                        │ │
│  │                                                                  │ │
│  │  Interpretation:                                                 │ │
│  │    • 0.8 - 1.0: High confidence (excellent)                     │ │
│  │    • 0.6 - 0.8: Medium confidence (good)                        │ │
│  │    • 0.4 - 0.6: Low confidence (uncertain)                      │ │
│  │    • 0.0 - 0.4: Very low confidence (unreliable)                │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Diogenes (Critic Agent)

**File**: `backend/agents/critic_agent.py`

```
┌─────────────────────────────────────────────────────────────────────┐
│                      DIOGENES - CRITIC AGENT                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  PURPOSE: Detect hallucinations and quality issues in responses      │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  DETECTION METHODS                                              │ │
│  │                                                                  │ │
│  │  1. Factual Consistency Check                                   │ │
│  │     • Compare response claims with source documents             │ │
│  │     • Flag unsupported statements                               │ │
│  │     • Use entailment model (NLI)                                │ │
│  │                                                                  │ │
│  │  2. Self-Contradiction Detection                                │ │
│  │     • Check for contradictory statements within response        │ │
│  │     • Use sentence-pair classification                          │ │
│  │                                                                  │ │
│  │  3. Confidence Calibration                                      │ │
│  │     • Compare model confidence with actual accuracy             │ │
│  │     • Flag overconfident responses                              │ │
│  │                                                                  │ │
│  │  4. Relevance Check                                             │ │
│  │     • Ensure response addresses the query                       │ │
│  │     • Detect topic drift                                        │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  OUTPUT                                                         │ │
│  │                                                                  │ │
│  │  {                                                               │ │
│  │    "is_hallucinating": false,                                   │ │
│  │    "quality_score": 0.92,                                       │ │
│  │    "issues": [],                                                │ │
│  │    "recommendations": [                                         │ │
│  │      "Add citation for claim X"                                 │ │
│  │    ]                                                             │ │
│  │  }                                                               │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Other Specialized Agents (Summary)

| Agent | File | Purpose | Key Features |
|-------|------|---------|--------------|
| **Socrates** | clarification_agent.py | Generate clarifying questions | Handles ambiguous queries, asks for specifics |
| **Aristotle** | analysis_agent.py | Document comparison & analysis | Multi-doc comparison, trend identification |
| **Thoth** | summarization_agent.py | Multi-document summarization | Abstractive + extractive summarization |
| **Hermes** | explanation_agent.py | Explain search results & ranking | Transparency, interpretability |
| **Proteus** | adaptive_retriever.py | Adaptive retrieval strategies | Adjusts search based on query type |
| **Sisyphus** | retrieval_controller.py | Corrective retrieval on failures | Retries with modified queries |

---

## Document Processing Agents

### Daedalus Orchestrator

**File**: `backend/agents/document_agents/daedalus_orchestrator.py`

```
┌─────────────────────────────────────────────────────────────────────┐
│                   DAEDALUS - DOCUMENT ORCHESTRATOR                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  PURPOSE: Coordinate document processing agents for attached files   │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  WORKFLOW                                                       │ │
│  │                                                                  │ │
│  │  Input: Query + Attached document IDs                           │ │
│  │                                                                  │ │
│  │  Step 1: PROMETHEUS (Content Reader)                            │ │
│  │    • Retrieve document content from OpenSearch                  │ │
│  │    • Extract relevant sections based on query                   │ │
│  │    • Output: Extracted content chunks                           │ │
│  │                                                                  │ │
│  │  Step 2: HYPATIA (Semantic Analyzer)                            │ │
│  │    • Analyze content for semantic meaning                       │ │
│  │    • Identify key concepts and themes                           │ │
│  │    • Map to query intent                                        │ │
│  │    • Output: Semantic annotations                               │ │
│  │                                                                  │ │
│  │  Step 3: MNEMOSYNE (Insight Extractor)                          │ │
│  │    • Extract insights relevant to query                         │ │
│  │    • Generate answer based on document content                  │ │
│  │    • Include citations to specific sections                     │ │
│  │    • Output: Insights + answer                                  │ │
│  │                                                                  │ │
│  │  Step 4: Synthesis                                              │ │
│  │    • Combine insights from all documents                        │ │
│  │    • Generate comprehensive response                            │ │
│  │    • Add document metadata and citations                        │ │
│  │                                                                  │ │
│  │  Output: Final response with document-grounded answer           │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Prometheus (Content Reader)

**File**: `backend/agents/document_agents/prometheus_reader.py`

- Extracts content from documents
- Supports all indexed file types
- Returns structured content with metadata

### Hypatia (Semantic Analyzer)

**File**: `backend/agents/document_agents/hypatia_analyzer.py`

- Performs deep semantic analysis
- Identifies themes, concepts, arguments
- Maps content to query requirements

### Mnemosyne (Insight Extractor)

**File**: `backend/agents/document_agents/mnemosyne_extractor.py`

- Extracts key insights and takeaways
- Generates query-specific answers
- Provides evidence-based citations

---

## Agent Communication

### Agent-to-Agent Communication Protocol

**File**: `backend/a2a_agent.py`

```
┌─────────────────────────────────────────────────────────────────────┐
│                  AGENT-TO-AGENT COMMUNICATION                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  MESSAGE FORMAT                                                 │ │
│  │                                                                  │ │
│  │  {                                                               │ │
│  │    "sender": "athena",                                           │ │
│  │    "receiver": "apollo",                                         │ │
│  │    "message_type": "request",  # request, response, notification│ │
│  │    "payload": {                                                  │ │
│  │      "action": "expand_graph_context",                          │ │
│  │      "parameters": {                                             │ │
│  │        "entities": ["GPT-4", "OpenAI"],                         │ │
│  │        "max_hops": 2                                             │ │
│  │      }                                                            │ │
│  │    },                                                            │ │
│  │    "correlation_id": "uuid",  # For tracking request-response   │ │
│  │    "timestamp": "2025-01-15T10:30:00Z"                           │ │
│  │  }                                                               │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  COMMUNICATION PATTERNS                                         │ │
│  │                                                                  │ │
│  │  1. Request-Response                                            │ │
│  │     Agent A sends request → Agent B processes → Returns response│ │
│  │                                                                  │ │
│  │  2. Publish-Subscribe                                           │ │
│  │     Agent A publishes event → All subscribed agents notified    │ │
│  │                                                                  │ │
│  │  3. Pipeline                                                    │ │
│  │     Agent A → Agent B → Agent C (sequential)                    │ │
│  │                                                                  │ │
│  │  4. Parallel Fanout                                             │ │
│  │     Orchestrator → [Agent A, Agent B, Agent C] (parallel)       │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## State Management

### LangGraph State Persistence

```
┌─────────────────────────────────────────────────────────────────────┐
│                         STATE MANAGEMENT                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  • State Backend: In-memory (default) or Redis (configurable)        │
│  • State Lifecycle: Per-query (ephemeral) or session (persistent)    │
│  • State Serialization: JSON                                         │
│                                                                       │
│  State Transitions:                                                  │
│    INITIAL → CLASSIFYING → ROUTING → RETRIEVING → GENERATING →      │
│    SCORING → FINALIZING → COMPLETE                                   │
│                                                                       │
│  Each state includes:                                                │
│    • Current stage                                                   │
│    • Accumulated data (results, context, etc.)                       │
│    • Agent execution history                                         │
│    • Error state (if any)                                            │
└─────────────────────────────────────────────────────────────────────┘
```

---

**Document Version**: 1.0
**Last Updated**: 2025-12-31
**Related Docs**: `01_OVERALL_SYSTEM_ARCHITECTURE.md`, `02_BACKEND_ARCHITECTURE.md`
