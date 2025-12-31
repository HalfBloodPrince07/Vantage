# SummarizationAgent (Document Summarizer) Architecture

**File:** `backend/agents/summarization_agent.py`

---

## Purpose

The SummarizationAgent generates concise **summaries** of long documents or collections of search results. It is used both during ingestion (to create document abstracts) and at query time (to provide brief overviews).

---

## High‑Level ASCII Diagram

```
+-------------------+      +----------------------+      +-------------------+
|   Long Text       | ---> |   Chunker            | ---> |   LLM Summarizer |
+-------------------+      +----------------------+      +-------------------+
        |                         |                         |
        | 1. Split into chunks   | 2. Summarize each chunk |
        | 3. Merge summaries      | 4. Final concise output |
        v                         v                         v
+-------------------+      +----------------------+      +-------------------+
|   Chunk Summaries |      |   Merge Algorithm   |      |   Final Summary   |
+-------------------+      +----------------------+      +-------------------+
```

---

## Core Methods

```python
class SummarizationAgent:
    async def summarize(self, text: str, max_length: int = 200) -> str:
        """Return a concise summary not exceeding `max_length` characters."""
        chunks = self._chunk_text(text)
        chunk_summaries = [await self._summarize_chunk(c) for c in chunks]
        return self._merge_summaries(chunk_summaries, max_length)

    def _chunk_text(self, text: str) -> List[str]:
        """Split `text` into ~500‑token pieces for the LLM."""
        ...

    async def _summarize_chunk(self, chunk: str) -> str:
        """Prompt Ollama to summarise a single chunk."""
        ...

    def _merge_summaries(self, summaries: List[str], max_length: int) -> str:
        """Combine chunk summaries, optionally re‑summarise to fit `max_length`."""
        ...
```

---

## Interaction with Other Components

- **IngestionPipeline** calls this agent to produce `document_summary` stored in OpenSearch.
- **DaedalusOrchestrator** may request a summary of attached documents for the LLM prompt.
- **Frontend** can request on‑demand summarisation of search results.
- **MemoryManager** stores generated summaries for quick retrieval.

---

## Configuration (`config.yaml`)

```yaml
agents:
  summarization_agent:
    enabled: true
    chunk_size_tokens: 500
    llm:
      temperature: 0.2
      max_tokens: 150
```

---

## Error Handling & Logging

- Logs each chunk processing step.
- If the LLM fails for a chunk, that chunk is skipped and a warning emitted.
- Returns the best‑effort summary even if some chunks fail.

---

## Testing Strategy

1. **Unit Tests** for `_chunk_text` boundary conditions.
2. **Mock LLM** to verify that `_summarize_chunk` receives the correct prompt.
3. **Integration Test**: Summarise a 3000‑word document and assert length ≤ 200 characters.
4. **Performance**: Summarisation of a typical 10 KB document ≤ 1 second.

---

*SummarizationAgent provides the concise context needed for efficient RAG and improves UI readability.*
