# VANTAGE - Memory System Architecture (Deep Dive)

## Table of Contents
- [Memory System Overview](#memory-system-overview)
- [Multi-Tier Memory Architecture](#multi-tier-memory-architecture)
- [Session Memory](#session-memory)
- [Episodic Memory](#episodic-memory)
- [Procedural Memory](#procedural-memory)
- [User Profile](#user-profile)
- [Agentic Memory System (A-mem)](#agentic-memory-system-a-mem)
- [Memory Manager](#memory-manager)

---

## Memory System Overview

The Vantage memory system implements a **multi-tiered memory architecture** inspired by human cognitive memory systems. It enables the system to learn from interactions, personalize responses, and maintain conversational context.

### Memory Hierarchy

```
┌─────────────────────────────────────────────────────────────────────┐
│                      VANTAGE MEMORY HIERARCHY                        │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  TIER 1: SESSION MEMORY (Short-term, Working Memory)                │
│  • Backend: Redis                                                    │
│  • TTL: 1 hour (sliding window)                                      │
│  • Scope: Current conversation                                       │
│  • Capacity: Last 10 turns                                           │
│  • Purpose: Maintain conversational context                          │
└─────────────────────────────────────────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  TIER 2: EPISODIC MEMORY (Long-term Event Memory)                   │
│  • Backend: SQLite                                                   │
│  • Retention: Permanent (with decay)                                 │
│  • Scope: Past query-response pairs                                  │
│  • Purpose: Learn from past interactions                             │
└─────────────────────────────────────────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  TIER 3: PROCEDURAL MEMORY (Skill & Pattern Memory)                 │
│  • Backend: SQLite + In-memory                                       │
│  • Retention: Permanent                                              │
│  • Scope: Learned behaviors and patterns                             │
│  • Purpose: Improve response quality over time                       │
└─────────────────────────────────────────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  TIER 4: USER PROFILE (Personalization Memory)                      │
│  • Backend: SQLite                                                   │
│  • Retention: Permanent                                              │
│  • Scope: User preferences and patterns                              │
│  • Purpose: Personalize search and responses                         │
└─────────────────────────────────────────────────────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  TIER 5: AGENTIC MEMORY (Structured Knowledge Memory)               │
│  • Backend: OpenSearch + SQLite                                      │
│  • Retention: Permanent (with consolidation)                         │
│  • Scope: Structured memory notes with relationships                 │
│  • Purpose: Advanced knowledge storage and retrieval                 │
└─────────────────────────────────────────────────────────────────────┘
```

### Memory Directory Structure

```
backend/memory/
│
├── __init__.py
│
├── memory_manager.py           # Unified coordinator for all memory tiers
├── session_memory.py           # Tier 1: Session/Working Memory (Redis)
├── episodic_memory.py          # Tier 2: Episodic/Event Memory (SQLite)
├── procedural_memory.py        # Tier 3: Procedural/Skill Memory (SQLite)
├── user_profile.py             # Tier 4: User Profile (SQLite)
├── conversation_manager.py     # Conversation tracking and persistence
├── memory_reflector.py         # Memory reflection and analysis
├── memory_tool.py              # Tool interface for agents
│
└── agentic_memory/             # Tier 5: Advanced Agentic Memory (A-mem)
    ├── __init__.py
    ├── system.py               # Main A-mem system coordinator
    ├── note.py                 # Memory note data structure
    ├── note_generator.py       # Automatic note generation from interactions
    ├── chains.py               # LangChain integration
    ├── evolution.py            # Memory link evolution over time
    ├── consolidation.py        # Periodic memory consolidation
    ├── pruning.py              # Memory decay and cleanup
    ├── multimodal.py           # Multi-modal memory support
    ├── proactive.py            # Proactive suggestions based on memory
    ├── reorganizer.py          # Memory graph reorganization
    ├── metrics.py              # Memory system metrics
    ├── tuning.py               # Performance tuning
    ├── nl_interface.py         # Natural language memory queries
    └── opensearch_memory.py    # OpenSearch-backed memory storage
```

---

## Multi-Tier Memory Architecture

### Overview Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                  MEMORY SYSTEM INTERACTION FLOW                      │
└─────────────────────────────────────────────────────────────────────┘

User Query
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        MEMORY MANAGER                                │
│                      (Unified Coordinator)                           │
└─────────────────────────────────────────────────────────────────────┘
    │
    ├──────────────┬──────────────┬──────────────┬──────────────┬──────┐
    ▼              ▼              ▼              ▼              ▼      ▼
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────┐
│Session  │  │Episodic │  │Procedural│ │  User   │  │ Agentic │  │ Conv │
│ Memory  │  │ Memory  │  │ Memory   │  │ Profile │  │ Memory  │  │ Mgr  │
│         │  │         │  │          │  │         │  │ (A-mem) │  │      │
│ Redis   │  │ SQLite  │  │ SQLite + │  │ SQLite  │  │OpenSearch│ │SQLite│
│ 1hr TTL │  │Permanent│  │ In-mem   │  │Permanent│  │+SQLite  │  │      │
└─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └──────┘
    │              │              │              │              │       │
    │              │              │              │              │       │
    ▼              ▼              ▼              ▼              ▼       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     QUERY PROCESSING PIPELINE                        │
│                                                                       │
│  1. Load session context (last 10 turns)                             │
│  2. Retrieve relevant episodes (similar past queries)                │
│  3. Apply learned procedural patterns                                │
│  4. Personalize based on user profile                                │
│  5. Query agentic memory for structured knowledge                    │
│  6. Process query with enhanced context                              │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
Response Generation
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     POST-PROCESSING & STORAGE                        │
│                                                                       │
│  1. Update session memory (add new turn)                             │
│  2. Store in episodic memory (query-response pair)                   │
│  3. Update procedural memory (learn patterns)                        │
│  4. Update user profile (interaction count, preferences)             │
│  5. Generate agentic memory note (if significant)                    │
│  6. Save conversation to database                                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Session Memory

**File**: `backend/memory/session_memory.py`

```
┌─────────────────────────────────────────────────────────────────────┐
│                          SESSION MEMORY                              │
│                        (Working Memory - Tier 1)                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  PURPOSE: Maintain short-term conversational context                 │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  STORAGE BACKEND                                                │ │
│  │                                                                  │ │
│  │  Primary: Redis                                                  │
│  │    • Host: localhost:6379                                       │ │
│  │    • Key format: "session:{session_id}"                         │ │
│  │    • TTL: 3600 seconds (1 hour)                                 │ │
│  │    • Sliding expiration: Resets on each access                  │ │
│  │                                                                  │ │
│  │  Fallback: In-memory dictionary                                 │ │
│  │    • Used when Redis unavailable                                │ │
│  │    • Warning logged to user                                     │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  DATA STRUCTURE                                                 │ │
│  │                                                                  │ │
│  │  {                                                               │ │
│  │    "session_id": "uuid",                                         │ │
│  │    "user_id": "uuid",                                            │ │
│  │    "conversation_history": [                                     │ │
│  │      {                                                            │ │
│  │        "role": "user",                                           │ │
│  │        "content": "What are transformers?",                      │ │
│  │        "timestamp": "2025-01-15T10:30:00Z"                       │ │
│  │      },                                                           │ │
│  │      {                                                            │ │
│  │        "role": "assistant",                                      │ │
│  │        "content": "Transformers are a neural network...",        │ │
│  │        "timestamp": "2025-01-15T10:30:05Z",                      │ │
│  │        "metadata": {                                             │ │
│  │          "confidence": 0.92,                                     │ │
│  │          "sources": ["doc1", "doc2"]                             │ │
│  │        }                                                          │ │
│  │      }                                                            │ │
│  │    ],                                                             │ │
│  │    "context_window": 10,  # Max turns to keep                    │ │
│  │    "created_at": "2025-01-15T10:25:00Z",                         │ │
│  │    "last_activity": "2025-01-15T10:30:05Z"                       │ │
│  │  }                                                               │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  OPERATIONS                                                     │ │
│  │                                                                  │ │
│  │  1. get_session(session_id) → SessionContext                    │ │
│  │     • Retrieve session from Redis                               │ │
│  │     • Deserialize JSON                                          │ │
│  │     • Update last_activity                                      │ │
│  │     • Extend TTL (sliding expiration)                           │ │
│  │                                                                  │ │
│  │  2. update_session(session_id, new_turn)                        │ │
│  │     • Append new turn to conversation_history                   │ │
│  │     • Enforce context window (keep last 10 turns)               │ │
│  │     • Update last_activity                                      │ │
│  │     • Serialize and save to Redis                               │ │
│  │                                                                  │ │
│  │  3. create_session(user_id) → session_id                        │ │
│  │     • Generate new UUID                                         │ │
│  │     • Initialize empty conversation history                     │ │
│  │     • Save to Redis with TTL                                    │ │
│  │                                                                  │ │
│  │  4. delete_session(session_id)                                  │ │
│  │     • Remove from Redis                                         │ │
│  │     • Optionally archive to SQLite                              │ │
│  │                                                                  │ │
│  │  5. extend_session(session_id)                                  │ │
│  │     • Reset TTL to 1 hour                                       │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  CONTEXT WINDOW MANAGEMENT                                      │ │
│  │                                                                  │ │
│  │  Sliding Window: Keep last N turns (default: 10)                │ │
│  │                                                                  │ │
│  │  Example with window=3:                                          │ │
│  │    Turn 1: User asks A                                          │ │
│  │    Turn 2: Assistant responds B                                 │ │
│  │    Turn 3: User asks C                                          │ │
│  │    Turn 4: Assistant responds D                                 │ │
│  │    Turn 5: User asks E  ← Oldest turn (Turn 1) dropped         │ │
│  │                                                                  │ │
│  │  Current context: [Turn 2, Turn 3, Turn 4, Turn 5]              │ │
│  │                                                                  │ │
│  │  Why limit?                                                      │ │
│  │    • Prevent context bloat in LLM prompts                       │ │
│  │    • Keep recent, relevant context                              │ │
│  │    • Older context available via episodic memory                │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  CONFIGURATION                                                  │ │
│  │                                                                  │ │
│  │  memory:                                                         │ │
│  │    session_backend: "redis"  # or "in_memory"                   │ │
│  │    session_ttl: 3600  # seconds                                 │ │
│  │    context_window: 10  # turns                                  │ │
│  │    redis_url: "redis://localhost:6379"                          │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Episodic Memory

**File**: `backend/memory/episodic_memory.py`

```
┌─────────────────────────────────────────────────────────────────────┐
│                         EPISODIC MEMORY                              │
│                      (Event Memory - Tier 2)                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  PURPOSE: Store and retrieve past query-response interactions        │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  STORAGE BACKEND                                                │ │
│  │                                                                  │ │
│  │  • Backend: SQLite (locallens_memory.db)                        │ │
│  │  • Table: episodes                                              │ │
│  │  • Retention: Permanent with decay mechanism                    │ │
│  │  • Indexing: By user_id, timestamp, embedding similarity        │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  DATABASE SCHEMA                                                │ │
│  │                                                                  │ │
│  │  CREATE TABLE episodes (                                         │ │
│  │      id TEXT PRIMARY KEY,                                        │ │
│  │      user_id TEXT NOT NULL,                                      │ │
│  │      session_id TEXT,                                            │ │
│  │      query TEXT NOT NULL,                                        │ │
│  │      query_embedding BLOB,  -- 768-dim vector                   │ │
│  │      response TEXT NOT NULL,                                     │ │
│  │      search_results JSON,  -- Top K documents                   │ │
│  │      confidence REAL,                                            │ │
│  │      feedback INTEGER,  -- -1 (bad), 0 (neutral), 1 (good)      │ │
│  │      timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,              │ │
│  │      access_count INTEGER DEFAULT 0,                             │ │
│  │      last_accessed TIMESTAMP,                                    │ │
│  │      decay_factor REAL DEFAULT 1.0,  -- Decays over time        │ │
│  │      FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)    │ │
│  │  );                                                              │ │
│  │                                                                  │ │
│  │  CREATE INDEX idx_episodes_user ON episodes(user_id);           │ │
│  │  CREATE INDEX idx_episodes_timestamp ON episodes(timestamp);    │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  OPERATIONS                                                     │ │
│  │                                                                  │ │
│  │  1. store_episode(query, response, metadata)                    │ │
│  │     • Generate query embedding                                  │ │
│  │     • Insert into episodes table                                │ │
│  │     • Initialize decay_factor = 1.0                             │ │
│  │                                                                  │ │
│  │  2. retrieve_similar_episodes(query, top_k=5)                   │ │
│  │     • Embed query                                               │ │
│  │     • Compute cosine similarity with all episode embeddings     │ │
│  │     • Apply decay factor to scores                              │ │
│  │     • Return top K episodes                                     │ │
│  │     • Update access_count and last_accessed                     │ │
│  │                                                                  │ │
│  │  3. update_feedback(episode_id, feedback)                       │ │
│  │     • User provides thumbs up/down                              │ │
│  │     • Update feedback field                                     │ │
│  │     • Affects future retrieval ranking                          │ │
│  │                                                                  │ │
│  │  4. decay_old_episodes()                                        │ │
│  │     • Run periodically (daily)                                  │ │
│  │     • Reduce decay_factor for old episodes                      │ │
│  │     • Formula: decay = 1.0 / (1 + days_since_created/365)       │ │
│  │                                                                  │ │
│  │  5. prune_episodes(threshold=0.1)                               │ │
│  │     • Remove episodes with decay_factor < threshold             │ │
│  │     • Keep at least last 100 episodes per user                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  RETRIEVAL STRATEGY                                             │ │
│  │                                                                  │ │
│  │  When a new query arrives:                                       │ │
│  │                                                                  │ │
│  │  1. Embed query → q_embedding                                   │ │
│  │                                                                  │ │
│  │  2. For each episode in database:                               │ │
│  │       similarity = cosine(q_embedding, episode.embedding)       │ │
│  │       score = similarity * episode.decay_factor                 │ │
│  │       if episode.feedback == 1:                                 │ │
│  │           score *= 1.2  # Boost positive feedback               │ │
│  │       if episode.feedback == -1:                                │ │
│  │           score *= 0.5  # Penalize negative feedback            │ │
│  │                                                                  │ │
│  │  3. Sort episodes by score (descending)                         │ │
│  │                                                                  │ │
│  │  4. Return top K episodes                                       │ │
│  │                                                                  │ │
│  │  5. Use retrieved episodes to:                                  │ │
│  │     • Inform current response                                   │ │
│  │     • Provide examples to LLM                                   │ │
│  │     • Personalize search strategy                               │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  DECAY MECHANISM                                                │ │
│  │                                                                  │ │
│  │  Purpose: Older memories become less relevant over time         │ │
│  │                                                                  │ │
│  │  Decay Formula:                                                  │ │
│  │    decay_factor = 1.0 / (1 + days_since_created / 365)          │ │
│  │                                                                  │ │
│  │  Examples:                                                       │ │
│  │    • Day 0 (new):      decay = 1.0                              │ │
│  │    • Day 30:           decay = 0.92                             │ │
│  │    • Day 180 (6 mos):  decay = 0.67                             │ │
│  │    • Day 365 (1 year): decay = 0.50                             │ │
│  │    • Day 730 (2 years):decay = 0.33                             │ │
│  │                                                                  │ │
│  │  Effect:                                                         │ │
│  │    Recent episodes have higher retrieval scores                 │ │
│  │    Old but frequently accessed episodes stay relevant           │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Procedural Memory

**File**: `backend/memory/procedural_memory.py`

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PROCEDURAL MEMORY                             │
│                     (Skill Memory - Tier 3)                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  PURPOSE: Learn and apply behavioral patterns and skills             │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  STORAGE BACKEND                                                │ │
│  │                                                                  │ │
│  │  • Primary: In-memory dictionary (fast access)                  │ │
│  │  • Persistence: SQLite (locallens_memory.db)                    │ │
│  │  • Table: procedural_patterns                                   │ │
│  │  • Sync: Save to SQLite every 5 minutes                         │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  PATTERN TYPES                                                  │ │
│  │                                                                  │ │
│  │  1. QUERY_REWRITING                                             │ │
│  │     • Learn effective query reformulations                      │ │
│  │     • Example: "ML papers" → "machine learning research papers" │ │
│  │                                                                  │ │
│  │  2. RETRIEVAL_STRATEGY                                          │ │
│  │     • Learn which retrieval methods work best for query types   │ │
│  │     • Example: Technical queries → Prefer vector search         │ │
│  │                                                                  │ │
│  │  3. RESPONSE_FORMATTING                                         │ │
│  │     • Learn user's preferred response formats                   │ │
│  │     • Example: User likes bullet points over paragraphs         │ │
│  │                                                                  │ │
│  │  4. SOURCE_SELECTION                                            │ │
│  │     • Learn which document types are most relevant              │ │
│  │     • Example: For "latest research" → Prefer PDFs from 2024    │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  DATABASE SCHEMA                                                │ │
│  │                                                                  │ │
│  │  CREATE TABLE procedural_patterns (                              │ │
│  │      id TEXT PRIMARY KEY,                                        │ │
│  │      pattern_type TEXT NOT NULL,                                 │ │
│  │      pattern_data JSON NOT NULL,                                 │ │
│  │      success_count INTEGER DEFAULT 0,                            │ │
│  │      failure_count INTEGER DEFAULT 0,                            │ │
│  │      confidence REAL,  -- success/(success+failure)             │ │
│  │      last_used TIMESTAMP,                                        │ │
│  │      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP              │ │
│  │  );                                                              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  LEARNING PROCESS                                               │ │
│  │                                                                  │ │
│  │  Example: Learning Query Rewriting                              │ │
│  │                                                                  │ │
│  │  Iteration 1:                                                    │ │
│  │    User query: "ML papers"                                      │ │
│  │    Rewritten: "machine learning papers"                         │ │
│  │    Result: 8 documents, confidence 0.85                         │ │
│  │    Feedback: Positive (thumbs up)                               │ │
│  │    → Store pattern: "ML" → "machine learning"                   │ │
│  │    → success_count = 1                                          │ │
│  │                                                                  │ │
│  │  Iteration 2:                                                    │ │
│  │    User query: "ML algorithms"                                  │ │
│  │    Apply learned pattern: "machine learning algorithms"         │ │
│  │    Result: 12 documents, confidence 0.92                        │ │
│  │    Feedback: Positive                                           │ │
│  │    → success_count = 2                                          │ │
│  │                                                                  │ │
│  │  Iteration 3:                                                    │ │
│  │    User query: "ML history"                                     │ │
│  │    Apply pattern: "machine learning history"                    │ │
│  │    Result: 2 documents, confidence 0.45                         │ │
│  │    Feedback: Negative (user clarifies)                          │ │
│  │    → failure_count = 1                                          │ │
│  │                                                                  │ │
│  │  Pattern confidence = 2/(2+1) = 0.67                            │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  PATTERN APPLICATION                                            │ │
│  │                                                                  │ │
│  │  When processing a query:                                        │ │
│  │                                                                  │ │
│  │  1. Check if any procedural patterns match                      │ │
│  │  2. Filter patterns by confidence > 0.6                         │ │
│  │  3. Apply patterns with highest confidence first                │ │
│  │  4. Track application outcome                                   │ │
│  │  5. Update success/failure counts based on feedback             │ │
│  │                                                                  │ │
│  │  Reinforcement Learning:                                         │ │
│  │    • Patterns that work → Strengthened (higher confidence)      │ │
│  │    • Patterns that fail → Weakened (lower confidence)           │ │
│  │    • Patterns below 0.3 confidence → Pruned                     │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  CONFIGURATION                                                  │ │
│  │                                                                  │ │
│  │  procedural_memory:                                              │ │
│  │    learning_rate: 0.1                                            │ │
│  │    min_confidence: 0.3  # Prune below this                      │ │
│  │    max_patterns: 1000  # Per pattern type                       │ │
│  │    sync_interval: 300  # seconds (5 min)                        │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## User Profile

**File**: `backend/memory/user_profile.py`

```
┌─────────────────────────────────────────────────────────────────────┐
│                           USER PROFILE                               │
│                    (Personalization - Tier 4)                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  PURPOSE: Track user preferences and interaction patterns            │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  DATABASE SCHEMA                                                │ │
│  │                                                                  │ │
│  │  CREATE TABLE user_profiles (                                    │ │
│  │      user_id TEXT PRIMARY KEY,                                   │ │
│  │      username TEXT,                                              │ │
│  │      preferences JSON,                                           │ │
│  │      interaction_stats JSON,                                     │ │
│  │      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,             │ │
│  │      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP              │ │
│  │  );                                                              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  PREFERENCES STRUCTURE                                          │ │
│  │                                                                  │ │
│  │  {                                                               │ │
│  │    "response_format": "bullet_points",  # or "paragraphs"       │ │
│  │    "detail_level": "detailed",  # "brief", "detailed", "verbose"│ │
│  │    "citation_style": "inline",  # or "footnotes", "none"        │ │
│  │    "preferred_sources": ["pdf", "docx"],                         │ │
│  │    "exclude_sources": [],                                        │ │
│  │    "language": "en",                                             │ │
│  │    "dark_mode": true,                                            │ │
│  │    "show_thinking_steps": true,                                  │ │
│  │    "auto_expand_graph": false                                    │ │
│  │  }                                                               │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  INTERACTION STATS                                              │ │
│  │                                                                  │ │
│  │  {                                                               │ │
│  │    "total_queries": 1250,                                        │ │
│  │    "avg_confidence": 0.87,                                       │ │
│  │    "positive_feedback": 980,                                     │ │
│  │    "negative_feedback": 45,                                      │ │
│  │    "neutral_feedback": 225,                                      │ │
│  │    "avg_session_length": 8.5,  # turns                          │ │
│  │    "most_queried_topics": [                                      │ │
│  │      "machine learning",                                         │ │
│  │      "neural networks",                                          │ │
│  │      "transformers"                                              │ │
│  │    ],                                                            │ │
│  │    "query_types": {                                              │ │
│  │      "DOCUMENT_SEARCH": 850,                                     │ │
│  │      "GENERAL_KNOWLEDGE": 200,                                   │ │
│  │      "COMPARISON": 100,                                          │ │
│  │      "SUMMARIZATION": 100                                        │ │
│  │    },                                                            │ │
│  │    "peak_usage_hours": [9, 10, 14, 15, 20],  # Hours of day    │ │
│  │    "last_login": "2025-01-15T10:30:00Z"                          │ │
│  │  }                                                               │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  PERSONALIZATION APPLICATIONS                                   │ │
│  │                                                                  │ │
│  │  1. Response Formatting                                          │ │
│  │     • If user prefers bullet points → Format as list            │ │
│  │     • If user prefers paragraphs → Format as prose              │ │
│  │                                                                  │ │
│  │  2. Search Biasing                                              │ │
│  │     • Boost preferred source types (e.g., PDFs)                 │ │
│  │     • Exclude unwanted sources                                  │ │
│  │                                                                  │ │
│  │  3. Proactive Suggestions                                       │ │
│  │     • "Based on your interest in ML, you might like..."         │ │
│  │     • Suggest related documents from queried topics             │ │
│  │                                                                  │ │
│  │  4. Adaptive Confidence Thresholds                              │ │
│  │     • If user tolerates lower confidence → Lower threshold      │ │
│  │     • If user demands high quality → Raise threshold            │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Agentic Memory System (A-mem)

**Directory**: `backend/memory/agentic_memory/`

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AGENTIC MEMORY SYSTEM (A-mem)                     │
│                  (Structured Knowledge - Tier 5)                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  PURPOSE: Advanced structured memory with automatic note generation, │
│           consolidation, evolution, and proactive suggestions        │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  ARCHITECTURE                                                   │ │
│  │                                                                  │ │
│  │  A-mem combines:                                                 │
│  │    • Structured memory notes (facts, concepts, relationships)   │ │
│  │    • Automatic note generation from interactions                │ │
│  │    • Memory link evolution over time                            │ │
│  │    • Periodic consolidation and pruning                         │ │
│  │    • Proactive suggestion engine                                │ │
│  │    • Natural language memory queries                            │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  MEMORY NOTE STRUCTURE (note.py)                               │ │
│  │                                                                  │ │
│  │  class MemoryNote:                                               │ │
│  │      id: str                    # Unique identifier             │ │
│  │      content: str               # The memory content            │ │
│  │      note_type: str             # FACT, CONCEPT, PROCEDURE,     │ │
│  │                                 # OBSERVATION, PREFERENCE       │ │
│  │      created_at: datetime                                        │ │
│  │      updated_at: datetime                                        │ │
│  │      last_accessed: datetime                                     │ │
│  │      access_count: int                                           │ │
│  │      importance: float          # [0, 1]                         │ │
│  │      decay_factor: float        # Time-based decay              │ │
│  │      embedding: List[float]     # 768-dim vector                │ │
│  │      links: List[MemoryLink]    # Connections to other notes    │ │
│  │      metadata: Dict             # Additional context            │ │
│  │                                                                  │ │
│  │  class MemoryLink:                                               │ │
│  │      target_note_id: str                                         │ │
│  │      link_type: str             # RELATED_TO, SUPPORTS,         │ │
│  │                                 # CONTRADICTS, DERIVED_FROM      │ │
│  │      strength: float            # [0, 1]                         │ │
│  │      created_at: datetime                                        │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  NOTE GENERATOR (note_generator.py)                            │ │
│  │                                                                  │ │
│  │  Automatically generates memory notes from interactions:         │ │
│  │                                                                  │ │
│  │  Input: Query-response pair                                     │ │
│  │                                                                  │ │
│  │  Process:                                                        │ │
│  │    1. Extract key facts from response                           │ │
│  │    2. Identify important concepts                               │ │
│  │    3. Detect user preferences (implicit/explicit)               │ │
│  │    4. Generate structured notes                                 │ │
│  │    5. Create embeddings for each note                           │ │
│  │    6. Link related notes                                        │ │
│  │    7. Store in OpenSearch + SQLite                              │ │
│  │                                                                  │ │
│  │  Example:                                                        │ │
│  │    Query: "What is attention mechanism in transformers?"        │ │
│  │    Response: "Attention mechanism allows the model to focus..." │ │
│  │                                                                  │ │
│  │    Generated Notes:                                              │ │
│  │      Note 1 (CONCEPT):                                          │ │
│  │        "Attention mechanism in transformers"                    │ │
│  │        Links: [Transformers (PART_OF), Neural Networks]         │ │
│  │                                                                  │ │
│  │      Note 2 (OBSERVATION):                                      │ │
│  │        "User interested in transformer architectures"           │ │
│  │        Links: [User Profile, Machine Learning]                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  MEMORY EVOLUTION (evolution.py)                               │ │
│  │                                                                  │ │
│  │  Memory links evolve based on usage patterns:                   │ │
│  │                                                                  │ │
│  │  1. Strengthening:                                              │ │
│  │     • When two notes are frequently accessed together           │ │
│  │     • Link strength increases                                   │ │
│  │     • Formula: new_strength = old_strength * 1.1 (capped at 1.0)│ │
│  │                                                                  │ │
│  │  2. Weakening:                                                  │ │
│  │     • Links not accessed recently decay                         │ │
│  │     • Formula: new_strength = old_strength * 0.95               │ │
│  │                                                                  │ │
│  │  3. New Link Creation:                                          │ │
│  │     • If notes co-occur in context > 3 times                    │ │
│  │     • Create new link with initial strength 0.5                 │ │
│  │                                                                  │ │
│  │  4. Link Pruning:                                               │ │
│  │     • Remove links with strength < 0.1                          │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  CONSOLIDATION (consolidation.py)                              │ │
│  │                                                                  │ │
│  │  Periodic background task (every 1 hour):                       │ │
│  │                                                                  │ │
│  │  1. Merge Duplicate Notes                                       │ │
│  │     • Find notes with high similarity (> 0.95)                  │ │
│  │     • Merge into single note                                    │ │
│  │     • Combine links                                             │ │
│  │                                                                  │ │
│  │  2. Strengthen Important Memories                               │ │
│  │     • Identify frequently accessed notes                        │ │
│  │     • Increase importance score                                 │ │
│  │                                                                  │ │
│  │  3. Reorganize Memory Graph                                     │ │
│  │     • Detect clusters of related notes                          │ │
│  │     • Create higher-level concept notes                         │ │
│  │                                                                  │ │
│  │  4. Generate Summary Notes                                      │ │
│  │     • Summarize clusters of notes                               │ │
│  │     • Create abstract concepts                                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  PRUNING (pruning.py)                                          │ │
│  │                                                                  │ │
│  │  Memory cleanup (weekly):                                        │ │
│  │                                                                  │ │
│  │  1. Remove Low-Importance Notes                                 │ │
│  │     • importance * decay_factor < 0.1                           │ │
│  │     • Not accessed in > 90 days                                 │ │
│  │                                                                  │ │
│  │  2. Archive Old Notes                                           │ │
│  │     • Move to long-term storage                                 │ │
│  │     • Keep summary only                                         │ │
│  │                                                                  │ │
│  │  3. Prune Weak Links                                            │ │
│  │     • Remove links with strength < 0.1                          │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  PROACTIVE SUGGESTIONS (proactive.py)                          │ │
│  │                                                                  │ │
│  │  Generate suggestions based on memory:                           │ │
│  │                                                                  │ │
│  │  1. Related Topics                                              │ │
│  │     • Analyze recent queries                                    │ │
│  │     • Traverse memory graph for related concepts                │ │
│  │     • Suggest: "You might also be interested in..."             │ │
│  │                                                                  │ │
│  │  2. Incomplete Knowledge Detection                              │ │
│  │     • Identify gaps in memory graph                             │ │
│  │     • Suggest: "Would you like to know more about...?"          │ │
│  │                                                                  │ │
│  │  3. Contradiction Detection                                     │ │
│  │     • Find contradictory notes                                  │ │
│  │     • Alert: "I found conflicting information about..."         │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  NATURAL LANGUAGE INTERFACE (nl_interface.py)                  │ │
│  │                                                                  │ │
│  │  Query memory using natural language:                            │ │
│  │                                                                  │ │
│  │  Examples:                                                       │ │
│  │    • "What do I know about transformers?"                       │ │
│  │    • "Show me all facts about neural networks"                  │ │
│  │    • "What did I learn last week?"                              │ │
│  │    • "What are my preferences for search?"                      │ │
│  │                                                                  │ │
│  │  Process:                                                        │ │
│  │    1. Parse natural language query                              │ │
│  │    2. Identify query intent (RETRIEVE, FILTER, AGGREGATE)       │ │
│  │    3. Construct memory query                                    │ │
│  │    4. Execute against A-mem system                              │ │
│  │    5. Format results for user                                   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  STORAGE BACKEND (opensearch_memory.py)                        │ │
│  │                                                                  │ │
│  │  • Primary: OpenSearch (for vector similarity search)           │ │
│  │  • Secondary: SQLite (for structured queries)                   │ │
│  │                                                                  │ │
│  │  OpenSearch Index Schema:                                        │ │
│  │    {                                                             │ │
│  │      "note_id": "keyword",                                      │ │
│  │      "content": "text",                                         │ │
│  │      "note_type": "keyword",                                    │ │
│  │      "importance": "float",                                     │ │
│  │      "embedding": "knn_vector (768 dims)",                      │ │
│  │      "links": "nested",                                         │ │
│  │      "created_at": "date",                                      │ │
│  │      "last_accessed": "date"                                    │ │
│  │    }                                                             │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Memory Manager

**File**: `backend/memory/memory_manager.py`

```
┌─────────────────────────────────────────────────────────────────────┐
│                          MEMORY MANAGER                              │
│                      (Unified Coordinator)                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  PURPOSE: Coordinate all memory tiers and provide unified interface  │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  INITIALIZATION                                                 │ │
│  │                                                                  │ │
│  │  class MemoryManager:                                            │ │
│  │      def __init__(self, config):                                 │ │
│  │          self.session_memory = SessionMemory(redis_url)          │ │
│  │          self.episodic_memory = EpisodicMemory(db_path)          │ │
│  │          self.procedural_memory = ProceduralMemory(db_path)      │ │
│  │          self.user_profile = UserProfile(db_path)                │ │
│  │          self.agentic_memory = AgenticMemorySystem(config)       │ │
│  │          self.conversation_manager = ConversationManager(db)     │ │
│  │                                                                  │ │
│  │          # Start background tasks                                │ │
│  │          self.start_consolidation_task()                         │ │
│  │          self.start_pruning_task()                               │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  CORE OPERATIONS                                                │ │
│  │                                                                  │ │
│  │  1. get_context_for_query(query, user_id, session_id)           │ │
│  │     • Load session history (Tier 1)                             │ │
│  │     • Retrieve similar episodes (Tier 2)                        │ │
│  │     • Get applicable procedural patterns (Tier 3)               │ │
│  │     • Load user preferences (Tier 4)                            │ │
│  │     • Query agentic memory (Tier 5)                             │ │
│  │     • Combine all context into unified structure                │ │
│  │     • Return to query processor                                 │ │
│  │                                                                  │ │
│  │  2. store_interaction(query, response, metadata)                │ │
│  │     • Update session memory (add turn)                          │ │
│  │     • Store episode                                             │ │
│  │     • Update procedural memory (learn patterns)                 │ │
│  │     • Update user profile (stats)                               │ │
│  │     • Generate agentic memory notes                             │ │
│  │     • Save conversation                                         │ │
│  │                                                                  │ │
│  │  3. apply_feedback(query_id, feedback)                          │ │
│  │     • Update episode feedback                                   │ │
│  │     • Adjust procedural memory confidence                       │ │
│  │     • Update user profile stats                                 │ │
│  │     • Strengthen/weaken memory links                            │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  BACKGROUND TASKS                                               │ │
│  │                                                                  │ │
│  │  1. Consolidation Task (every 1 hour)                           │ │
│  │     • Run A-mem consolidation                                   │ │
│  │     • Decay old episodes                                        │ │
│  │     • Sync procedural memory to disk                            │ │
│  │                                                                  │ │
│  │  2. Pruning Task (every 7 days)                                 │ │
│  │     • Run A-mem pruning                                         │ │
│  │     • Remove low-importance episodes                            │ │
│  │     • Clean up old sessions                                     │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

**Document Version**: 1.0
**Last Updated**: 2025-12-31
**Related Docs**: `01_OVERALL_SYSTEM_ARCHITECTURE.md`, `02_BACKEND_ARCHITECTURE.md`
