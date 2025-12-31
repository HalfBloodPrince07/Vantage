# RetrievalController (Routing & Coordination) Architecture

**File:** `backend/agents/retrieval_controller.py`

---

## Purpose

The RetrievalController (sometimes called **Sisyphus**) orchestrates the **selection and execution of retrieval strategies** for a given query. It receives the chosen strategy from **Proteus**, invokes the appropriate retrievers (vector, BM25, temporal, graph), merges results, and forwards them to the ranking pipeline.

---

## High‑Level ASCII Diagram

```
+-------------------+      +----------------------+      +-------------------+
|   Query + Strategy| ---> |   RetrievalController| ---> |   Raw Results     |
+-------------------+      +----------------------+      +-------------------+
        |                         |                         |
        |  strategy = PRECISE    | 1. Vector Search          |
        |  strategy = SEMANTIC   | 2. BM25 Search           |
        |  strategy = TEMPORAL   | 3. Temporal Filter       |
        |  strategy = EXPLORATORY| 4. Graph Expansion (Apollo)
        v                         v                         v
+-------------------+      +----------------------+      +-------------------+
|   Vector Store    |      |   BM25 Index        |      |   Temporal Index |
+-------------------+      +----------------------+      +-------------------+
        |                         |                         |
        +-----------+-------------+-------------+-----------+
                    |                           |
                    v                           v
               +-------------------------------+
               |   MergedResultSet            |
               |   (dedup, score aggregation) |
               +-------------------------------+
```

---

## Core Methods

```python
class RetrievalController:
    async def retrieve(self, query: str, strategy: RetrievalStrategy) -> MergedResultSet:
        """Dispatch to the appropriate retrievers based on `strategy`."""
        results = []
        if strategy in {RetrievalStrategy.PRECISE, RetrievalStrategy.HYBRID}:
            results.append(await self._vector_search(query))
        if strategy in {RetrievalStrategy.SEMANTIC, RetrievalStrategy.HYBRID}:
            results.append(await self._bm25_search(query))
        if strategy == RetrievalStrategy.TEMPORAL:
            results.append(await self._temporal_search(query))
        if strategy == RetrievalStrategy.EXPLORATORY:
            results.append(await self._graph_expansion(query))
        merged = self._merge_results(results)
        return merged

    async def _vector_search(self, query: str) -> List[DocumentResult]:
        ...

    async def _bm25_search(self, query: str) -> List[DocumentResult]:
        ...

    async def _temporal_search(self, query: str) -> List[DocumentResult]:
        ...

    async def _graph_expansion(self, query: str) -> List[DocumentResult]:
        ...

    def _merge_results(self, result_lists: List[List[DocumentResult]]) -> MergedResultSet:
        ...
```

---

## Interaction with Other Components

- **Proteus** supplies the `RetrievalStrategy`.
- **Apollo** may be called directly for graph expansion.
- **Themis** receives the merged result set for confidence scoring.
- **Odysseus** can request a re‑run with a different strategy if confidence is low.
- **Zeus** receives the final `MergedResultSet` to continue the workflow.

---

## Configuration (`config.yaml`)

```yaml
agents:
  retrieval_controller:
    enabled: true
    top_k: 20          # Number of raw results before reranking
    deduplication: true
```

---

## Error Handling & Logging

- Each sub‑retriever logs its latency and result count.
- If a specific retriever fails, the controller logs a warning and continues with the remaining sources.
- Critical failures raise `RetrievalError` which propagates to Zeus, resulting in a fallback generic answer.

---

## Testing Strategy

1. **Unit Tests** for `_merge_results` deduplication logic.
2. **Mock Vector/BM25** to verify correct dispatch based on strategy.
3. **Integration Test**: End‑to‑end `/search` with a query that triggers `EXPLORATORY` and ensure graph results are included.
4. **Performance**: Retrieval latency ≤ 300 ms for HYBRID strategy.

---

## Data Classes

```python
@dataclass
class DocumentResult:
    doc_id: str
    score: float
    source: str  # e.g., "vector", "bm25", "graph"
    snippet: str

@dataclass
class MergedResultSet:
    results: List[DocumentResult]
    merged_score: float
```

---

*The RetrievalController unifies multiple retrieval modalities, providing a flexible backbone for Vantage’s adaptive search capabilities.*
