# RankingSystem (Hybrid Search & Reranking) Architecture

**File:** `backend/ranking/ranking_system.py`

---

## Purpose

The RankingSystem combines **vector similarity**, **BM25 keyword matching**, and **cross‑encoder reranking** to produce a final ordered list of documents. It implements the hybrid search pipeline used throughout Vantage.

---

## High‑Level ASCII Diagram

```
+-------------------+      +----------------------+      +-------------------+
|   Query Vector    | ---> |   Hybrid Retriever   | ---> |   Raw Candidates  |
+-------------------+      +----------------------+      +-------------------+
        |                         |                         |
        | 1. Vector search (k‑NN) | 2. BM25 search          |
        | 3. Merge results (RRF)  |                         |
        v                         v                         v
+-------------------+      +----------------------+      +-------------------+
|   Cross‑Encoder   | ---> |   Reranker (MMR)    | ---> |   Final Ranking   |
+-------------------+      +----------------------+      +-------------------+
```

---

## Core Steps

1. **Vector Search** – Calls `OpenSearchClient.search_vectors` (k‑NN) to retrieve top‑k embeddings.
2. **BM25 Search** – Calls `OpenSearchClient.search_bm25` for keyword relevance.
3. **Reciprocal Rank Fusion (RRF)** – Merges the two result sets using the formula `score = Σ 1/(k + rank)`.
4. **Cross‑Encoder Reranker** – Sends the merged list to a cross‑encoder (`ms‑marco‑MiniLM‑L‑6‑v2`) to obtain a refined relevance score.
5. **MMR Diversity** – Applies Maximal Marginal Relevance to ensure result diversity.
6. **Return Final Ranked List** – Each entry includes `doc_id`, `final_score`, `source` (vector/bm25), and a short `snippet`.

---

## Key Methods

```python
class RankingSystem:
    def __init__(self, config: Dict[str, Any]):
        self.opensearch = OpenSearchClient(config['opensearch'])
        self.cross_encoder = CrossEncoderReranker(config['reranker'])
        self.rerank_k = config['ranking']['rerank_k']
        self.mmr_lambda = config['ranking']['mmr_lambda']

    async def rank(self, query: str, top_k: int = 20) -> List[DocumentResult]:
        vec_hits = await self.opensearch.search_vectors(query, k=top_k)
        bm25_hits = await self.opensearch.search_bm25(query, k=top_k)
        merged = self._rrf_merge(vec_hits, bm25_hits)
        reranked = await self.cross_encoder.rerank(query, merged, top_n=self.rerank_k)
        return self._apply_mmr(reranked)

    def _rrf_merge(self, vec_hits, bm25_hits, k: int = 60) -> List[DocumentResult]:
        """Reciprocal Rank Fusion – combine two ranked lists."""
        scores: Dict[str, float] = {}
        for rank, hit in enumerate(vec_hits, start=1):
            scores[hit.doc_id] = scores.get(hit.doc_id, 0) + 1 / (k + rank)
        for rank, hit in enumerate(bm25_hits, start=1):
            scores[hit.doc_id] = scores.get(hit.doc_id, 0) + 1 / (k + rank)
        # Build DocumentResult list sorted by fused score
        return sorted([DocumentResult(doc_id=doc_id, score=sc, source="rrf", snippet="")
                      for doc_id, sc in scores.items()], key=lambda r: r.score, reverse=True)

    def _apply_mmr(self, results: List[DocumentResult]) -> List[DocumentResult]:
        """Maximal Marginal Relevance to promote diversity."""
        selected = []
        while results and len(selected) < self.rerank_k:
            if not selected:
                selected.append(results.pop(0))
                continue
            # compute MMR score for each candidate
            mmr_scores = []
            for cand in results:
                relevance = cand.score
                similarity = max(self._jaccard(cand.snippet, s.snippet) for s in selected)
                mmr = self.mmr_lambda * relevance - (1 - self.mmr_lambda) * similarity
                mmr_scores.append((mmr, cand))
            best = max(mmr_scores, key=lambda x: x[0])[1]
            selected.append(best)
            results.remove(best)
        return selected

    @staticmethod
    def _jaccard(a: str, b: str) -> float:
        set_a = set(a.lower().split())
        set_b = set(b.lower().split())
        if not set_a or not set_b:
            return 0.0
        return len(set_a & set_b) / len(set_a | set_b)
```

---

## Interaction with Other Components

- **Proteus** decides whether to use the hybrid pipeline or a single modality.
- **Themis** consumes the final scores to compute overall confidence.
- **Odysseus** may request reranking for sub‑queries.
- **Frontend** displays the ranked list with snippets and source indicators.

---

## Configuration (`config.yaml`)

```yaml
ranking:
  rerank_k: 10          # Number of docs after cross‑encoder rerank
  mmr_lambda: 0.7        # Weight for relevance vs diversity
  rrf_k: 60              # Constant used in RRF formula
```

---

## Error Handling & Logging

- Each stage logs with `loguru` (`🔀 Ranking`).
- If the cross‑encoder service fails, the system falls back to the RRF‑merged list.
- Exceptions raise `RankingError` which is caught by Zeus to provide a generic answer.

---

## Testing Strategy

1. **Unit Tests** for `_rrf_merge` verifying the RRF formula.
2. **Mock OpenSearch** responses to test end‑to‑end `rank`.
3. **Integration Test**: Verify that the final list respects diversity (MMR) by checking overlap of snippets.
4. **Performance**: Full ranking pipeline ≤ 500 ms for a typical query.

---

## Data Classes

```python
@dataclass
class DocumentResult:
    doc_id: str
    score: float
    source: str   # "vector", "bm25", "rrf"
    snippet: str
```

---

*The RankingSystem is the core of Vantage’s retrieval quality, blending fast vector similarity with robust lexical matching and sophisticated reranking.*
