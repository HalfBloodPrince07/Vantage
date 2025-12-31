# Proteus (Adaptive Retriever) Architecture

**File:** `backend/agents/adaptive_retriever.py`

---

## Purpose

Proteus selects the **optimal retrieval strategy** (precise, semantic, exploratory, temporal, or hybrid) based on the characteristics of the user query. It balances speed, relevance, and coverage.

---

## High‑Level Flow (ASCII Diagram)

```
+-------------------+      +----------------------+      +-------------------+
|   User Query      | ---> |   Feature Extract   | ---> |   Strategy Picker |
+-------------------+      +----------------------+      +-------------------+
        |                         |                         |
        | (keywords, length,     | (heuristic scoring)    |
        |  dates, entities)       |                         |
        v                         v                         v
+-------------------+      +----------------------+      +-------------------+
|   Rule‑Based      |      |   Score Calculation |      |   Return Strategy |
|   Checks         |      |   (weights)         |      +-------------------+
+-------------------+      +----------------------+                     |
        |                         |                                 |
        | (fallback)              | (fallback)                      |
        v                         v                                 v
+-------------------+      +----------------------+      +-------------------+
|   LLM Prompt      | ---> |   LLM Strategy Gen  | ---> |   Final Strategy  |
+-------------------+      +----------------------+      +-------------------+
```

1. **Feature Extraction** – Token count, presence of dates, file‑type mentions, entity count.
2. **Rule‑Based Checks** – Quick matches for obvious cases (e.g., "exact file name" → PRECISE).
3. **Heuristic Scoring** – Weighted sum of features produces a score for each strategy.
4. **LLM Fallback** – If confidence < 0.6, a short prompt asks the LLM to suggest a strategy.
5. **Output** – Returns a `RetrievalStrategy` enum and a parameter dict.

---

## Key Methods

```python
class AdaptiveRetriever:
    def classify_strategy(self, query: str) -> Tuple[RetrievalStrategy, Dict[str, Any]]:
        """Return the chosen strategy and its configuration."""
        features = self._extract_features(query)
        strategy, score = self._rule_based_strategy(features)
        if score < 0.6:
            strategy, score = self._llm_strategy(query)
        return strategy, self._strategy_params(strategy)

    def _extract_features(self, query: str) -> Dict[str, Any]:
        """Calculate length, keyword flags, date patterns, entity count."""
        ...

    def _rule_based_strategy(self, feats: Dict) -> Tuple[RetrievalStrategy, float]:
        """Apply ordered heuristics to pick a strategy."""
        ...

    async def _llm_strategy(self, query: str) -> Tuple[RetrievalStrategy, float]:
        """Prompt Ollama to suggest a strategy when heuristics are unsure."""
        ...
```

---

## Interaction with Other Components

- **Zeus** calls `Proteus.classify_strategy` after intent classification.
- **Apollo** may be invoked if the chosen strategy is `EXPLORATORY`.
- **Themis** uses the returned strategy to adjust confidence weighting.
- **Odysseus** receives the strategy when planning multi‑hop queries.

---

## Configuration (`config.yaml`)

```yaml
agents:
  adaptive_retriever:
    enabled: true
    thresholds:
      precise: 0.8
      semantic: 0.6
      exploratory: 0.5
    llm:
      temperature: 0.3
      max_tokens: 256
```

---

## Error Handling & Logging

- Logs each decision step with `loguru` at `INFO`.
- If LLM call fails, defaults to `HYBRID` strategy.
- Exceptions are caught; a warning is emitted and a safe fallback is returned.

---

## Testing Strategy

1. **Unit Tests** for `_extract_features` with varied queries.
2. **Rule‑Based Tests** ensuring deterministic strategy selection for known patterns.
3. **Mock LLM** to verify fallback path.
4. **Integration Test**: End‑to‑end `/search` with a temporal query, assert `TEMPORAL` strategy is used.

---

## Key Classes & Enums

```python
class RetrievalStrategy(Enum):
    PRECISE = "precise"
    SEMANTIC = "semantic"
    EXPLORATORY = "exploratory"
    TEMPORAL = "temporal"
    HYBRID = "hybrid"
```

---

*Proteus ensures Vantage selects the most appropriate retrieval approach for each user request, balancing relevance and performance.*
