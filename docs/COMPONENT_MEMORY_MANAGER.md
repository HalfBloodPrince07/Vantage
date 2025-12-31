# MemoryManager (Multi‑Tier Memory Coordination) Architecture

**File:** `backend/memory/memory_manager.py`

---

## Purpose

`MemoryManager` orchestrates the **five‑tier memory system** (Session, Episodic, Procedural, User Profile, Agentic) and provides a unified API for agents to read/write contextual information.

---

## High‑Level ASCII Diagram

```
+-------------------+      +----------------------+      +-------------------+
|   Agent Request   | ---> |   MemoryManager      | ---> |   Memory Layer    |
+-------------------+      +----------------------+      +-------------------+
        |                         |                         |
        | 1. Resolve tier          | 2. Route to Redis /   |
        |    (session, user…)     |    SQLite / OpenSearch |
        v                         v                         v
+-------------------+      +----------------------+      +-------------------+
|   SessionMemory   |      |   EpisodicMemory    |      |   ProceduralMem   |
+-------------------+      +----------------------+      +-------------------+
        |                         |                         |
        | 3. Cache hit/miss       | 4. Store episode       |
        v                         v                         v
+-------------------+      +----------------------+      +-------------------+
|   UserProfileMem  |      |   AgenticMemory (A‑mem) |   |   Retrieval of   |
+-------------------+      +----------------------+      |   Contextual Data |
        |                         |                         |
        +-----------+-------------+-------------+-----------+
                    |                           |
                    v                           v
               +-------------------------------+
               |   Unified Context Object      |
               +-------------------------------+
```

---

## Core Methods

```python
class MemoryManager:
    async def get(self, key: str, tier: str) -> Any:
        """Retrieve a value from the specified tier (session, episodic, procedural, profile, a_mem)."""
        ...

    async def set(self, key: str, value: Any, tier: str, ttl: Optional[int] = None) -> None:
        """Store a value in the specified tier with optional TTL."""
        ...

    async def merge_context(self, session_id: str) -> UnifiedContext:
        """Collect data from all tiers and return a single context object for agents."""
        ...
```

---

## Interaction with Other Components

- **Agents** (e.g., Athena, Odysseus) call `MemoryManager.get/set` for session state, user preferences, or episodic recall.
- **Daedalus** stores document‑specific insights in the Episodic tier.
- **Themis** reads confidence‑related metadata from the Procedural tier.
- **KnowledgeGraph** updates are persisted via the AgenticMemory tier.
- **Frontend** receives session updates via SSE streamed from `MemoryManager`.

---

## Configuration (`config.yaml`)

```yaml
memory:
  enabled: true
  tiers:
    session:
      backend: redis
      ttl_seconds: 1800
    episodic:
      backend: sqlite
      db_path: "locallens_memory.db"
    procedural:
      backend: opensearch
      index: "procedural_mem"
    user_profile:
      backend: sqlite
      db_path: "locallens_user.db"
    agentic:
      backend: opensearch
      index: "a_mem"
```

---

## Error Handling & Logging

- Logs each read/write with `loguru` (`🧠 Memory`).
- On backend failure, falls back to in‑memory cache and emits a warning.
- Critical failures raise `MemoryError` which propagates to Zeus for graceful degradation.

---

## Testing Strategy

1. **Unit Tests** for `get/set` across all tiers using mock Redis/SQLite.
2. **Integration Test**: End‑to‑end query that stores a session variable, retrieves it in a later sub‑query, and verifies consistency.
3. **Performance**: Tier reads ≤ 20 ms, writes ≤ 30 ms.

---

## Data Classes

```python
@dataclass
class UnifiedContext:
    session: Dict[str, Any]
    episodic: List[Dict]
    procedural: Dict[str, Any]
    profile: Dict[str, Any]
    agentic: Dict[str, Any]
```

---

*MemoryManager is the glue that gives Vantage persistent, hierarchical state, enabling coherent multi‑turn conversations and long‑term learning.*
