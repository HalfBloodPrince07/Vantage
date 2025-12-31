# Hypatia (Semantic Analysis) Architecture

**File:** `backend/agents/document_agents/hypatia_analyzer.py`

---

## Purpose

Hypatia performs **semantic analysis** on the raw text extracted by Prometheus. It identifies the document type, extracts key concepts, detects entities, and generates a structured representation used by downstream agents (Mnemosyne, Daedalus, Retrieval).

---

## High‑Level ASCII Diagram

```
+-------------------+      +----------------------+      +-------------------+
|   Raw Text        | ---> |   Concept Extractor | ---> |   Entity Finder   |
|   (from Prometheus) |   |   (Key Phrases)    |      |   (NER)          |
+-------------------+      +----------------------+      +-------------------+
        |                         |                         |
        v                         v                         v
+-------------------+      +----------------------+      +-------------------+
|   Document Type   |      |   Concept List      |      |   Entity List    |
|   Classifier      |      |   (topic, keywords) |      |   (people, orgs) |
+-------------------+      +----------------------+      +-------------------+
        |                         |                         |
        +-----------+-------------+-------------+-----------+
                    |                           |
                    v                           v
               +-------------------------------+
               |   StructuredDocumentInfo      |
               |   { type, concepts, entities }|
               +-------------------------------+
```

---

## Core Methods

```python
class HypatiaAnalyzer:
    async def analyze(self, raw_text: str) -> StructuredDocumentInfo:
        """Run type classification, concept extraction, and NER on the given text."""
        doc_type = self._classify_type(raw_text)
        concepts = self._extract_concepts(raw_text)
        entities = await self._extract_entities(raw_text)
        return StructuredDocumentInfo(
            document_type=doc_type,
            concepts=concepts,
            entities=entities,
        )

    def _classify_type(self, text: str) -> str:
        """Simple rule‑based classifier (report, research paper, contract, etc.)."""
        ...

    def _extract_concepts(self, text: str) -> List[str]:
        """Use YAKE or KeyBERT to get top‑N key phrases."""
        ...

    async def _extract_entities(self, text: str) -> List[Entity]:
        """Call Ollama LLM with a JSON‑structured NER prompt, parse response."""
        ...
```

---

## Interaction with Other Components

- **PrometheusReader** supplies `raw_text`.
- **MnemosyneExtractor** consumes `StructuredDocumentInfo` to generate insights.
- **DaedalusOrchestrator** uses the concepts and entities to enrich the LLM prompt.
- **KnowledgeGraph** may be updated with newly discovered entities via `EntityResolver`.
- **Themis** can factor document type confidence into overall answer confidence.

---

## Configuration (`config.yaml`)

```yaml
agents:
  hypatia:
    enabled: true
    concept_extractor:
      method: "keybert"
      top_n: 10
    entity_extractor:
      llm:
        temperature: 0.2
        max_tokens: 256
```

---

## Error Handling & Logging

- Logs each stage with `loguru` (`🔎 Hypatia`).
- If the LLM entity extraction fails, falls back to spaCy NER.
- Critical failures raise `SemanticAnalysisError` which is caught by Daedalus and results in a generic "analysis unavailable" message.

---

## Testing Strategy

1. **Unit Tests** for `_classify_type` with sample excerpts.
2. **Concept Extraction Tests** using a known document and verifying top concepts.
3. **Mock LLM Entity Extraction** to ensure JSON parsing works.
4. **Integration Test**: Run full Daedalus pipeline on a PDF and assert that `StructuredDocumentInfo` contains expected fields.

---

## Data Class

```python
@dataclass
class StructuredDocumentInfo:
    document_type: str
    concepts: List[str]
    entities: List[Entity]
```

---

*Hypatia turns raw text into a rich semantic representation, enabling downstream agents to reason about the document’s meaning and context.*
