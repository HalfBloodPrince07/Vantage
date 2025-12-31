# Mnemosyne (Insight Extraction) Architecture

**File:** `backend/agents/document_agents/mnemosyne_extractor.py`

---

## Purpose

Mnemosyne generates **high‑level insights** from the semantic representation produced by Hypatia. It creates executive summaries, key takeaways, and a list of salient entities that are later used to enrich LLM prompts and to populate the knowledge graph.

---

## High‑Level ASCII Diagram

```
+-------------------+      +----------------------+      +-------------------+
| StructuredDocInfo | ---> |   Insight Builder   | ---> |   Insight Object |
| (from Hypatia)   |      |   (summarize, key)  |      +-------------------+
+-------------------+      +----------------------+                |
        |                         |                               |
        v                         v                               v
+-------------------+      +----------------------+      +-------------------+
|   Executive      |      |   Key Points        |      |   Entity List    |
|   Summary        |      |   (bullet list)    |      +-------------------+
+-------------------+      +----------------------+                |
        |                         |                               |
        +-----------+-------------+-------------+-----------+
                    |                           |
                    v                           v
               +-------------------------------+
               |   MnemosyneInsight           |
               |   {summary, points, entities}|
               +-------------------------------+
```

---

## Core Methods

```python
class MnemosyneExtractor:
    async def extract_insights(self, doc_info: StructuredDocumentInfo) -> MnemosyneInsight:
        """Create summary, bullet‑point key takeaways, and entity list."""
        summary = self._summarize(doc_info)
        points = self._extract_key_points(doc_info)
        entities = self._filter_entities(doc_info.entities)
        return MnemosyneInsight(summary=summary, points=points, entities=entities)

    def _summarize(self, info: StructuredDocumentInfo) -> str:
        """Prompt LLM for a concise 2‑sentence summary."""
        ...

    def _extract_key_points(self, info: StructuredDocumentInfo) -> List[str]:
        """Prompt LLM to list up to 5 most important takeaways."""
        ...

    def _filter_entities(self, entities: List[Entity]) -> List[Entity]:
        """Deduplicate, prioritize by relevance score, and keep top‑N."""
        ...
```

---

## Interaction with Other Components

- **Hypatia** supplies `StructuredDocumentInfo`.
- **DaedalusOrchestrator** incorporates the `MnemosyneInsight` into the final LLM prompt.
- **KnowledgeGraph** may be updated with newly discovered high‑value entities.
- **Themis** can use the confidence of the summary when scoring the final answer.

---

## Configuration (`config.yaml`)

```yaml
agents:
  mnemosyne:
    enabled: true
    summary_prompt: "Provide a concise two‑sentence summary of the document."
    key_points_prompt: "List up to five bullet points that capture the most important information."
    max_entities: 15
```

---

## Error Handling & Logging

- Logs each stage with `loguru` (`🧠 Mnemosyne`).
- If the LLM fails, falls back to a simple heuristic summary (first 2 sentences).
- Critical failures raise `InsightExtractionError` which is caught by Daedalus and results in a generic "insight unavailable" response.

---

## Testing Strategy

1. **Unit Tests** for `_filter_entities` deduplication logic.
2. **Mock LLM** for summary and key‑point generation.
3. **Integration Test**: Run full Daedalus pipeline on a sample PDF and verify that the final prompt contains a summary and bullet points.
4. **Performance**: Insight extraction ≤ 500 ms per document.

---

## Data Class

```python
@dataclass
class MnemosyneInsight:
    summary: str
    points: List[str]
    entities: List[Entity]
```

---

*Mnemosyne turns raw semantic data into human‑readable insights, enabling concise answers and enriching the knowledge graph.*
