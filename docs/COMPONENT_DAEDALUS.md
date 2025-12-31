# Daedalus (Document Orchestrator) Architecture

**File:** `backend/agents/document_agents/daedalus_orchestrator.py`

---

## Purpose

Daedalus coordinates the **document‑specific processing pipeline**. It extracts content, performs semantic analysis, generates insights, caches results, and finally answers user queries that reference attached documents.

---

## High‑Level ASCII Diagram

```
+-------------------+      +----------------------+      +-------------------+
|   User Query      | ---> |   Daedalus Init      | ---> |   Process Docs   |
|   + Attachments   |      |   (should_activate)  |      +-------------------+
+-------------------+      +----------------------+                |
        |                         |                               |
        | (no docs)               | (docs present)                |
        v                         v                               v
+-------------------+      +----------------------+      +-------------------+
|   Bypass Zeus    |      |   Prometheus (Extract) |   |   Hypatia (Analyze) |
+-------------------+      +----------------------+      +-------------------+
                                                       |
                                                       v
                                                +-------------------+
                                                | Mnemosyne (Insights) |
                                                +-------------------+
                                                       |
                                                       v
                                                +-------------------+
                                                |   Build Context   |
                                                +-------------------+
                                                       |
                                                       v
                                                +-------------------+
                                                |   LLM Answer      |
                                                +-------------------+
                                                       |
                                                       v
                                                +-------------------+
                                                |   DocumentQueryResponse |
                                                +-------------------+
```

1. **Activation** – `should_activate` returns `True` when any document is attached.
2. **Extraction** – `PrometheusReader` reads raw text, OCR for images, and extracts tables.
3. **Semantic Analysis** – `HypatiaAnalyzer` determines document type, key concepts, and structure.
4. **Insight Extraction** – `MnemosyneExtractor` produces executive summary, key points, and entity list.
5. **Caching** – Processed documents are stored in `self._processed_cache` for reuse within the session.
6. **Context Building** – Combines insights from all documents into a single prompt.
7. **Answer Generation** – Calls Ollama with a detailed prompt that references each document.
8. **Response** – Returns `DocumentQueryResponse` containing answer, sources, confidence, agents used, and thinking steps.

---

## Key Methods

```python
class DaedalusOrchestrator:
    async def process_query(self, query: str, attached_documents: List[Dict],
                            conversation_history: Optional[List[Dict]] = None,
                            session_id: Optional[str] = None) -> DocumentQueryResponse:
        """Main entry point for document‑specific queries."""
        ...

    async def _process_documents(self, documents: List[Dict], session_id: Optional[str]) -> List[ProcessedDocument]:
        """Run Prometheus → Hypatia → Mnemosyne for each doc, cache results."""
        ...

    def _build_combined_context(self, docs: List[ProcessedDocument]) -> str:
        """Create a unified context string used by the LLM."""
        ...

    async def _answer_query(self, query: str, docs: List[ProcessedDocument],
                             context: str, history: Optional[List[Dict]]) -> Tuple[str, List[Dict], float]:
        """LLM call that generates the final answer and confidence."""
        ...
```

---

## Interaction with Other Components

- **Zeus** routes to Daedalus when `should_activate` is true.
- **PrometheusReader**, **HypatiaAnalyzer**, **MnemosyneExtractor** are sub‑agents invoked sequentially.
- **SessionMemory** provides the `session_id` for streaming steps via SSE.
- **Themis** can later score the confidence of the answer.
- **KnowledgeGraph** is updated during extraction for any newly discovered entities.

---

## Configuration (`config.yaml`)

```yaml
agents:
  document_orchestrator:
    enabled: true
    cache_ttl_seconds: 1800   # Keep processed docs for 30 min
    max_documents_per_query: 5
```

---

## Error Handling & Logging

- Each sub‑step logs with `loguru` (`🏛️` prefix).
- If extraction fails for a document, it is skipped and a warning is emitted.
- Critical failures raise `DocumentProcessingError` which bubbles up to Zeus, resulting in a fallback answer.

---

## Testing Strategy

1. **Unit Tests** for `_process_documents` with mocked Prometheus/Hypatia/Mnemosyne.
2. **Cache Tests** – Verify that repeated queries hit the cache.
3. **Integration Tests** – End‑to‑end query with attached PDFs, assert answer contains citations.
4. **Performance** – Processing ≤ 2 seconds per document on average.

---

## Key Data Classes

```python
@dataclass
class ProcessedDocument:
    document_id: str
    filename: str
    extracted: ExtractedContent
    analysis: SemanticAnalysis
    insights: DocumentInsights
    processed_at: str

@dataclass
class DocumentQueryResponse:
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    agents_used: List[str]
    thinking_steps: List[Dict[str, str]]
```

---

*Daedalus enables Vantage to answer questions that reference specific user‑uploaded documents, turning raw files into structured knowledge for the LLM.*
