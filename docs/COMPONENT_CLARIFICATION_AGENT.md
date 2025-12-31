# ClarificationAgent (Socratic Clarifier) Architecture

**File:** `backend/agents/clarification_agent.py`

---

## Purpose

The ClarificationAgent engages the user in a **clarifying dialogue** when the original query is ambiguous or lacks sufficient context. It generates targeted follow‑up questions, collects user responses, and refines the original query before passing it back to the orchestration flow.

---

## High‑Level ASCII Diagram

```
+-------------------+      +----------------------+      +-------------------+
|   Ambiguous Query | ---> |   ClarificationAgent | ---> |   Refined Query   |
+-------------------+      +----------------------+      +-------------------+
        |                         |                         |
        | 1. Detect ambiguity    | 2. Generate follow‑up   |
        |    (low confidence)    |    questions via LLM   |
        v                         v                         v
+-------------------+      +----------------------+      +-------------------+
|   Themis Scorer   |      |   LLM Prompt Builder |      |   Updated Query   |
+-------------------+      +----------------------+      +-------------------+
        |                         |                         |
        | 3. Ask user            | 4. Receive answers      |
        |    clarification       |    (via UI)            |
        v                         v                         v
+-------------------+      +----------------------+      +-------------------+
|   UI (SSE)        |      |   Context Merger     |      |   Zeus Orchestrator |
+-------------------+      +----------------------+      +-------------------+
```

---

## Core Methods

```python
class ClarificationAgent:
    async def maybe_clarify(self, query: str, confidence: float) -> Tuple[bool, str]:
        """Return (needs_clarification, refined_query)."""
        if confidence >= 0.75:
            return False, query
        follow_ups = await self._generate_follow_ups(query)
        answers = await self._collect_user_responses(follow_ups)
        refined = self._merge_context(query, answers)
        return True, refined

    async def _generate_follow_ups(self, query: str) -> List[str]:
        """Prompt LLM to produce 1‑3 clarifying questions."""
        ...

    async def _collect_user_responses(self, questions: List[str]) -> List[str]:
        """Send questions to frontend via SSE and await replies."""
        ...

    def _merge_context(self, original: str, answers: List[str]) -> str:
        """Combine original query with user answers into a richer prompt."""
        ...
```

---

## Interaction with Other Components

- **Themis** provides the confidence score that triggers clarification.
- **Zeus** receives the refined query and continues the normal pipeline.
- **Frontend** displays the clarifying questions using Server‑Sent Events.
- **MemoryManager** stores the clarification interaction in the session memory for audit.

---

## Configuration (`config.yaml`)

```yaml
agents:
  clarification_agent:
    enabled: true
    min_confidence: 0.75   # Below this triggers clarification
    max_questions: 3
    llm:
      temperature: 0.3
      max_tokens: 128
```

---

## Error Handling & Logging

- Logs each step with `loguru` (`❓ Clarification`).
- If the user does not answer within the timeout, falls back to the original query.
- Exceptions raise `ClarificationError` which is caught by Zeus, leading to a generic answer.

---

## Testing Strategy

1. **Unit Tests** for `_merge_context` concatenation logic.
2. **Mock LLM** to verify generation of sensible follow‑up questions.
3. **Integration Test**: Simulate a low‑confidence query, ensure the UI receives questions and the orchestrator receives a refined query.
4. **Performance**: Clarification round‑trip ≤ 5 seconds.

---

*The ClarificationAgent ensures Vantage asks the right questions before committing to an answer, improving relevance and user satisfaction.*
