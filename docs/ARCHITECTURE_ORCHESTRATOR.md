# Orchestrator Architecture (Zeus)

The **Zeus** orchestrator is the central state machine that coordinates all request handling. It is built with **LangGraph** and follows a deterministic workflow.

```
+----------------------------------------------------------+
|                     Zeus (EnhancedOrchestrator)         |
|----------------------------------------------------------|
| 1. Load Context                                            |
|    - Retrieve session data from Redis (SessionMemory)      |
|    - Load user preferences from SQLite (UserProfile)       |
|    - Pull episodic memory if needed                        |
|                                                            |
| 2. Classify Intent (Athena)                               |
|    - Rule‑based fast path                                 |
|    - LLM fallback for ambiguous queries                  |
|    - Returns: intent, confidence, entities, filters       |
|                                                            |
| 3. Strategy Selection (Proteus)                           |
|    - Heuristic analysis of query length, keywords, time   |
|    - Chooses one of: PRECISE, SEMANTIC, EXPLORATORY,      |
|      TEMPORAL, HYBRID                                    |
|                                                            |
| 4. Routing Decision                                        |
|    ┌───────────────────────────────────────┐            |
|    │   Attached Documents?                  │            |
|    └─────────────────────┬─────────────────┘            |
|          Yes            │   No                           |
|          ▼              ▼                               |
|    +----------------+  +----------------+                |
|    | Daedalus Path  |  | Athena Path   |                |
|    +----------------+  +----------------+                |
|                                                            |
| 5. Daedalus Path (Document‑specific)                      |
|    - Calls DaedalusOrchestrator (document agents)          |
|    - Returns DocumentQueryResponse with answer, sources   |
|                                                            |
| 6. Athena Path (General)                                  |
|    - AdaptiveRetriever (Proteus) selects retrieval strategy |
|    - Optional Graph Expansion (Apollo) if entities exist   |
|    - Hybrid Search (vector + BM25) → Raw results           |
|    - Cross‑Encoder Reranker → Top‑k results                |
|    - Explanation (Hermes) → human‑readable steps           |
|    - Confidence Scoring (Themis) → confidence score       |
|    - Optional Multi‑hop Reasoning (Odysseus) for complex   |
|      queries                                               |
|                                                            |
| 7. Post‑Processing                                         |
|    - Quality Check (Diogenes) – flag low‑confidence answers |
|    - Store Episode in EpisodicMemory (SQLite)              |
|    - Update SessionMemory (Redis) and UserProfile (SQLite) |
|    - Emit thinking steps via SSE to frontend               |
|                                                            |
| 8. Return Response                                         |
|    - JSON payload with answer, sources, confidence, steps  |
+----------------------------------------------------------+
```

**Key Sub‑components**

- `backend/orchestration/orchestrator.py` – defines the LangGraph `StateGraph` and all nodes.
- `backend/agents/query_classifier.py` – Athena.
- `backend/agents/adaptive_retriever.py` – Proteus.
- `backend/agents/graph_rag_agent.py` – Apollo.
- `backend/agents/reasoning_planner.py` – Odysseus.
- `backend/agents/confidence_scorer.py` – Themis.
- `backend/agents/clarification_agent.py` – Socrates.
- `backend/agents/critic_agent.py` – Diogenes.
- `backend/agents/retrieval_controller.py` – Sisyphus.
- `backend/agents/document_agents/daedalus_orchestrator.py` – Daedalus.

**Data Flow Summary**

1. **Input** – HTTP request (`/search`) → FastAPI → Zeus.
2. **Context** – SessionMemory (Redis) + UserProfile (SQLite).
3. **Decision** – Intent → Strategy → Routing.
4. **Processing** – Agent(s) interact with Data Layer (OpenSearch, KnowledgeGraph, SQLite).
5. **Output** – Structured JSON + SSE steps back to UI.
