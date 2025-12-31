# Themis (Confidence Scorer) Architecture

**File:** `backend/agents/confidence_scorer.py`

---

## Purpose

Themis evaluates the **confidence** of a generated answer, assesses the strength of supporting evidence, and produces a rich `ConfidenceAwareResponse` that includes alternative interpretations, follow‑up suggestions, and uncertainty reasons.

---

## High‑Level ASCII Diagram

```
+-------------------+      +----------------------+      +-------------------+
|   Generated Answer| ---> |   Confidence Scorer  | ---> |   ConfidenceAware |
|   (from LLM)     |      |   (Themis)          |      |   Response        |
+-------------------+      +----------------------+      +-------------------+
        |                         |                         |
        | 1. Score confidence    | 2. Assess evidence      |
        | 2. Generate alternatives| 3. Suggest follow‑ups   |
        v                         v                         v
+-------------------+      +----------------------+      +-------------------+
|   Score Answer    |      |   Evidence Strength |      |   Follow‑up List  |
+-------------------+      +----------------------+      +-------------------+
```

---

## Core Steps

1. **Score Answer Confidence** – `score_answer_confidence` combines:
   - Number of sources (max 0.2)
   - Top source quality (max 0.2)
   - Answer length (max 0.15)
   - Retrieval quality from the Critic agent (max 0.2)
   - Presence of certainty/uncertainty phrases (max 0.15)
   - Base score 0.5 → final score clamped to 0‑1.
2. **Assess Evidence Strength** – `assess_evidence_strength` counts supporting vs contradictory sources and maps to levels *strong*, *moderate*, *weak*, *none*.
3. **Generate Alternatives** – If confidence < 0.6, `generate_alternatives` prompts the LLM to propose 2‑3 alternative interpretations of the query/answer.
4. **Suggest Follow‑ups** – `suggest_followups` builds a prompt from the answer and top sources to obtain helpful next‑question suggestions.
5. **Assemble Response** – `create_confidence_aware_response` bundles answer, confidence, evidence, alternatives, follow‑ups, uncertainty reasons, and source count into a `ConfidenceAwareResponse` dataclass.

---

## Important Methods (Signature)

```python
class ConfidenceScorer:
    async def score_answer_confidence(
        self, answer: str, query: str, sources: List[Dict], retrieval_quality: Optional[Dict] = None
    ) -> float:
        ...

    async def assess_evidence_strength(
        self, answer: str, query: str, sources: List[Dict]
    ) -> EvidenceStrength:
        ...

    async def generate_alternatives(self, query: str, answer: str) -> List[str]:
        ...

    async def suggest_followups(self, query: str, answer: str, sources: List[Dict]) -> List[str]:
        ...

    async def create_confidence_aware_response(
        self, answer: str, query: str, sources: List[Dict], retrieval_quality: Optional[Dict] = None
    ) -> ConfidenceAwareResponse:
        ...
```

---

## Interaction with Other Components

- **Zeus** calls `create_confidence_aware_response` after answer generation.
- **Diogenes (Critic)** supplies `retrieval_quality` (e.g., `quality_score`).
- **Odysseus** may receive the confidence score to decide whether to re‑plan.
- **The UI** displays `confidence`, `evidence_strength.level`, `alternative_interpretations`, and `suggested_followups`.

---

## Configuration (`config.yaml`)

```yaml
agents:
  confidence_scorer:
    enabled: true
    confidence_threshold: 0.6   # Below this triggers alternatives/follow‑ups
    llm:
      temperature: 0.4
      max_tokens: 512
```

---

## Error Handling & Logging

- All steps log at `INFO` with timestamps.
- If any LLM call fails, the method returns sensible defaults (e.g., empty alternatives, confidence = 0.5).
- Exceptions are caught and reported to the orchestrator; the workflow continues with a degraded response.

---

## Testing Strategy

1. **Unit Tests** for each scoring factor (source count, length, phrase detection).
2. **Mock LLM** for alternatives and follow‑ups to verify JSON parsing.
3. **Integration Test**: End‑to‑end `/search` request, assert `confidence` field present and within 0‑1.
4. **Edge Cases**: No sources, very short answer, contradictory sources.

---

## Key Data Classes

```python
@dataclass
class EvidenceStrength:
    level: str          # strong | moderate | weak | none
    score: float        # 0‑1
    supporting_sources: int
    contradicting_sources: int
    explanation: str

@dataclass
class ConfidenceAwareResponse:
    answer: str
    confidence: float
    evidence_strength: EvidenceStrength
    alternative_interpretations: List[str]
    suggested_followups: List[str]
    uncertainty_reasons: List[str]
    sources_used: int
```

---

*Themis provides transparent confidence metrics, helping users trust the AI’s answers and guiding follow‑up interactions.*
