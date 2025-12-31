# Athena (Query Classifier) Architecture

**File:** `backend/agents/query_classifier.py`

---

## Purpose

Athena is responsible for **determining the user's intent** and extracting structured information (entities, filters, and possible clarification questions) from the raw query. It drives the routing decision in Zeus.

---

## High‑Level Flow (ASCII Diagram)

```
+-------------------+      +----------------------+      +-------------------+
|   User Query      | ---> |   Rule‑Based Engine  | ---> |   Intent Result   |
+-------------------+      +----------------------+      +-------------------+
        |                         |
        | (fallback)              | (fallback)
        v                         v
+-------------------+      +----------------------+      +-------------------+
|   LLM Prompt      | ---> |   LLM Classification | ---> |   Intent Result   |
+-------------------+      +----------------------+      +-------------------+
```

1. **Rule‑Based Engine** – Fast pattern matching for common intents (e.g., keywords like "summarize", "compare", file extensions). Returns intent with high confidence if matched.
2. **LLM Fallback** – When rules are inconclusive, a prompt is sent to Ollama (`qwen3-vl:8b`) to classify the intent and extract entities/filters.
3. **Result** – A `ClassificationResult` dataclass containing:
   - `intent: QueryIntent`
   - `confidence: float`
   - `entities: List[str]`
   - `filters: Dict`
   - `clarification_questions: List[str]`

---

## Detailed Steps

1. **Pre‑Processing**
   - Normalise whitespace, lower‑case the query.
   - Detect attached‑document references (e.g., "this document").
2. **Rule‑Based Classification** (`_rule_based_classify`)
   - Checks ordered rule list (exact keywords → intent).
   - If confidence ≥ `config['classifier']['confidence_threshold']` (default 0.85) → short‑circuit.
3. **LLM Classification** (`_llm_classify`)
   - Prompt template includes examples of each intent.
   - Calls `call_ollama_json` with `model_type="json"`.
   - Parses JSON into `ClassificationResult`.
4. **Entity & Filter Extraction** (`_extract_entities_and_filters`)
   - Uses regex for dates, quarters, file‑type filters.
   - Leverages `sentence_transformers` for named‑entity detection if needed.
5. **Clarification Generation** (`_generate_clarifications`)
   - If confidence < 0.7, asks LLM to propose clarification questions.

---

## Inputs & Outputs

| Input | Description |
|-------|-------------|
| `query: str` | Raw user query string |
| `session_context: Optional[Dict]` | Recent conversation history (used for LLM context) |

| Output | Description |
|--------|-------------|
| `ClassificationResult` | Dataclass with intent, confidence, entities, filters, clarification questions |

---

## Interaction with Other Components

- **Zeus** consumes the `ClassificationResult` to decide routing (Athena Path vs Daedalus Path).
- **Proteus** may use extracted entities to influence retrieval strategy.
- **Themis** receives the intent to adjust confidence scoring heuristics.
- **Odysseus** can request the original query and entities for multi‑hop planning.

---

## Configuration (config.yaml)

```yaml
agents:
  classifier:
    enabled: true
    confidence_threshold: 0.85
    use_llm_fallback: true
    llm:
      temperature: 0.2
      max_tokens: 512
```

---

## Error Handling & Logging

- All classification steps log with `loguru` at `INFO` level.
- LLM failures trigger a fallback response: intent = `GENERAL_KNOWLEDGE` with low confidence.
- Exceptions are caught and logged; the system proceeds with a safe default intent.

---

## Testing Strategy

1. Unit tests for each rule pattern.
2. Mock LLM responses to verify JSON parsing.
3. End‑to‑end tests using the FastAPI `/search` endpoint with varied queries.
4. Performance benchmark: rule‑based path < 10 ms, LLM fallback ≤ 300 ms.
