# KnowledgeGraph (Entity/Relationship Store) Architecture

**File:** `backend/graph/knowledge_graph.py`

---

## Purpose

The KnowledgeGraph stores **entities and their relationships** extracted from documents. It enables graph‑based retrieval (Apollo) and supports entity resolution, relationship extraction, and traversal for multi‑hop reasoning.

---

## High‑Level ASCII Diagram

```
+-------------------+      +----------------------+      +-------------------+
|   Entity Extractor| ---> |   KnowledgeGraph    | ---> |   Query Engine   |
+-------------------+      +----------------------+      +-------------------+
        |                         |                         |
        | 1. Add/Update entities   | 2. Store edges          |
        | 3. Resolve synonyms      | 3. Traverse hops        |
        v                         v                         v
+-------------------+      +----------------------+      +-------------------+
|   Neo4j / OpenSearch|   |   Nodes (entity_id) |   |   Path Finder    |
+-------------------+      +----------------------+      +-------------------+
```

---

## Core Classes & Methods

```python
class KnowledgeGraph:
    def __init__(self, config: Dict[str, Any]):
        self.backend = OpenSearchGraphBackend(config['graph']['opensearch'])

    def add_entity(self, entity: Entity) -> None:
        """Insert or update an entity node. Handles synonym merging."""
        self.backend.upsert_node(entity.id, entity.to_dict())

    def add_relationship(self, src_id: str, tgt_id: str, rel_type: str, weight: float = 1.0) -> None:
        """Create an edge between two entities with optional weight."""
        self.backend.upsert_edge(src_id, tgt_id, rel_type, {'weight': weight})

    def resolve(self, name: str) -> Optional[Entity]:
        """Return the canonical entity for a given name (handles synonyms)."""
        return self.backend.find_by_name(name)

    def traverse(self, start_id: str, max_hops: int = 2) -> List[EntityPath]:
        """Breadth‑first search returning paths up to `max_hops`."""
        return self.backend.bfs(start_id, max_hops)
```

---

## Interaction with Other Components

- **Prometheus** extracts raw text; **Hypatia** extracts entities → passed to `add_entity`.
- **Apollo** calls `traverse` to expand queries.
- **Mnemosyne** may add high‑value entities after insight extraction.
- **MemoryManager** can cache frequently accessed sub‑graphs.
- **Frontend** can visualize the graph via the `/graph` API.

---

## Configuration (`config.yaml`)

```yaml
graph:
  opensearch:
    host: "opensearch"
    port: 9200
    index: "knowledge_graph"
    auth:
      username: "admin"
      password: "LocalLens@1234"
    ssl: false
```

---

## Error Handling & Logging

- All operations log with `loguru` (`🕸️ Graph`).
- If the backend is unavailable, raises `GraphBackendError` which bubbles up to Zeus for a graceful fallback.
- Duplicate entity insertion merges attributes; conflicts are logged as warnings.

---

## Testing Strategy

1. **Unit Tests** for `add_entity` and `add_relationship` using a mock OpenSearch backend.
2. **Integration Test**: Insert a small graph (Person → Company → Product) and verify `traverse` returns expected paths.
3. **Performance**: Insertion ≤ 50 ms, traversal ≤ 100 ms for 2‑hop queries.

---

## Data Classes

```python
@dataclass
class Entity:
    id: str
    name: str
    type: str  # e.g., person, organization, product
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EntityPath:
    nodes: List[str]
    edges: List[str]
    total_weight: float
```

---

*The KnowledgeGraph gives Vantage a relational memory layer, enabling entity‑centric retrieval and reasoning beyond plain text search.*
