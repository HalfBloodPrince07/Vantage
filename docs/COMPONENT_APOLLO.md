# Apollo (Graph RAG Agent) Architecture

**File:** `backend/agents/graph_rag_agent.py`

---

## Purpose

Apollo enriches retrieval by **expanding the query with graph‑derived entities** and fetching documents that are semantically linked via the knowledge graph. It enables entity‑aware RAG, improving relevance for queries that reference people, organizations, or concepts.

---

## High‑Level Flow (ASCII Diagram)

```
+-------------------+      +----------------------+      +-------------------+
|   User Query      | ---> |   Entity Extraction  | ---> |   Graph Expansion |
+-------------------+      +----------------------+      +-------------------+
        |                         |                         |
        | (fallback)              | (fallback)              |
        v                         v                         v
+-------------------+      +----------------------+      +-------------------+
|   LLM Prompt      | ---> |   LLM Entity Detect  | ---> |   LLM Expansion   |
+-------------------+      +----------------------+      +-------------------+
```

1. **Entity Extraction** – Fast rule‑based NER + optional LLM fallback.
2. **Graph Expansion** – Traverses the knowledge graph (max 2 hops) to collect related entities and document IDs.
3. **Result** – Returns a `GraphExpansion` dataclass with:
   - `original_entities`
   - `expanded_entities`
   - `related_documents`
   - `entity_context`
   - `expansion_path`

---

## Detailed Steps

1. **Extract Entities from Query**

   ```python
   entities = self._extract_entities(query)
   ```

   - Uses a regex dictionary for known entity patterns (e.g., dates, quarters).
   - If confidence < 0.7, calls Ollama (`call_ollama_json`) with a prompt to list entities.
2. **Resolve to Canonical IDs**

   ```python
   resolved = self.entity_resolver.resolve(entities, self.graph)
   ```

   - Deduplicates and maps synonyms (e.g., "Google" → entity_id "org_001").
3. **Graph Traversal** (`_traverse_graph`)
   - Breadth‑first search up to `max_hops` (default 2).
   - Collects neighboring entities and associated document IDs.
   - Scores each neighbor by edge weight and hop distance.
4. **Build Expanded Query Context**

   ```python
   expanded_query = f"{query} {' '.join(expanded_entities)}"
   ```

   - The expanded query is later fed to the hybrid search.
5. **Return `GraphExpansion`**

   ```python
   return GraphExpansion(
       original_entities=entities,
       expanded_entities=expanded_entities,
       related_documents=related_doc_ids,
       entity_context=entity_context,
       expansion_path=paths
   )
   ```

---

## Inputs & Outputs

| Input | Description |
|-------|-------------|
| `query: str` | Raw user query |
| `max_hops: int` (optional) | Depth of graph traversal |

| Output | Description |
|--------|-------------|
| `GraphExpansion` dataclass | Contains original & expanded entities, related document IDs, and context information |

---

## Interaction with Other Components

- **Zeus** calls `Apollo.expand_query` when the classified intent includes entities and the strategy is `EXPLORATORY`.
- **Proteus** may request graph expansion as part of its retrieval strategy.
- **Knowledge Graph** (`backend/graph/knowledge_graph.py`) stores entities and relationships; Apollo reads from it.
- **Retrieval** – The `related_documents` list is merged with the hybrid search results before reranking.
- **Themis** can use `entity_context` to improve confidence scoring (more entities → higher confidence).

---

## Configuration (`config.yaml`)

```yaml
agents:
  graph_rag:
    enabled: true
    max_hops: 2
    expansion_weight: 0.3   # Contribution of expanded docs to final ranking
    llm:
      temperature: 0.3
      max_tokens: 512
```

---

## Error Handling & Logging

- All steps log with `loguru` at `INFO` level.
- If graph traversal fails (e.g., missing entity), Apollo logs a warning and returns an empty expansion.
- LLM failures fall back to the original query without expansion.

---

## Testing Strategy

1. **Unit Tests** for `_extract_entities`, `_resolve_entities`, and `_traverse_graph` using mock graphs.
2. **Integration Tests**: End‑to‑end query with known entities, verify that expanded documents appear in the final result set.
3. **Performance Benchmark**: Graph traversal ≤ 50 ms for typical queries.
4. **Coverage**: 90 % line coverage for `graph_rag_agent.py`.

---

## Key Classes & Functions

```python
@dataclass
class GraphExpansion:
    original_entities: List[str]
    expanded_entities: List[str]
    related_documents: Set[str]
    entity_context: Dict[str, Any]
    expansion_path: List[Tuple[str, str, int]]  # (src, tgt, hop)

class GraphRAGAgent:
    def __init__(self, config: Dict[str, Any]):
        self.graph = KnowledgeGraph()
        self.entity_resolver = EntityResolver()
        self.max_hops = config['agents']['graph_rag'].get('max_hops', 2)
        
    async def expand_query(self, query: str, attached_entities: List[str] = None) -> GraphExpansion:
        # Core method used by Zeus
        ...
```

---

*Apollo enables Vantage to go beyond keyword matching, leveraging the rich relational structure of the knowledge graph for deeper, entity‑centric retrieval.*
