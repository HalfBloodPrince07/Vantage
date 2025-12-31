# Odysseus (Reasoning Planner) Architecture

**File:** `backend/agents/reasoning_planner.py`

---

## Purpose

Odysseus handles **complex, multi‑hop queries** by decomposing them into sub‑queries, planning an execution order, and synthesizing a final answer from multiple sources.

---

## High‑Level Flow (ASCII Diagram)

```
+-------------------+      +----------------------+      +-------------------+
|   User Query      | ---> |   Complexity Check  | ---> |   Decompose       |
+-------------------+      +----------------------+      +-------------------+
        |                         |                         |
        | (simple)                | (complex)               |
        v                         v                         v
+-------------------+      +----------------------+      +-------------------+
|   Direct Search   |      |   Generate Sub‑Qs    |      |   Execute Sub‑Qs |
+-------------------+      +----------------------+      +-------------------+
        |                         |                         |
        |                         |                         |
        v                         v                         v
+-------------------+      +----------------------+      +-------------------+
|   Hybrid Search   |      |   LLM Planning       |      |   LLM Answer      |
+-------------------+      +----------------------+      +-------------------+
        |                         |                         |
        +-------------------------+-------------------------+
                              |
                              v
                     +-------------------+
                     |   Synthesize      |
                     +-------------------+
                              |
                              v
                     +-------------------+
                     |   Final Answer    |
                     +-------------------+
```

1. **Complexity Check** – Uses heuristics (keyword patterns, number of question marks, conjunctions) to decide if the query is *simple* or *complex*.
2. **Decompose** – Calls Ollama with a prompt to generate a list of sub‑queries, each with a purpose and priority.
3. **Execute Sub‑Queries** – Each sub‑query is processed through the normal retrieval pipeline (Proteus → Hybrid Search → Rerank).
4. **Synthesize** – The LLM receives the original query, sub‑answers, and optional context, then produces a coherent final answer.

---

## Key Methods

```python
class ReasoningPlanner:
    def detect_complexity(self, query: str) -> str:
        """Return 'simple', 'moderate', or 'complex' based on heuristics."""
        ...

    async def decompose_query(self, query: str) -> List[Dict[str, Any]]:
        """Ask the LLM to return JSON list of sub‑queries.
        Example output:
        [{"id": "sq1", "query": "What is the revenue of Company X?", "purpose": "fetch financials", "priority": 1}, ...]
        """
        ...

    async def execute_subqueries(self, subqs: List[Dict], session_id: Optional[str]) -> List[Dict]:
        """Run each sub‑query through the normal search pipeline and collect answers."""
        ...

    async def synthesize_answer(self, original_query: str, sub_answers: List[Dict]) -> str:
        """Prompt the LLM to combine sub‑answers into a final response."""
        ...
```

---

## Interaction with Other Components

- **Proteus** – Provides the retrieval strategy for each sub‑query.
- **Apollo** – May be invoked if a sub‑query contains entity references.
- **Themis** – Scores confidence of the final synthesized answer.
- **Zeus** – Calls `Odysseus.decompose_query` when the intent is `COMPARISON` or `ANALYSIS` and the complexity is high.
- **Sisyphus** – Can trigger corrective retrieval if any sub‑answer is low confidence.

---

## Configuration (`config.yaml`)

```yaml
agents:
  reasoning_planner:
    enabled: true
    max_subqueries: 5
    llm:
      temperature: 0.3
      max_tokens: 1024
```

---

## Error Handling & Logging

- All steps log with `loguru` at `INFO`.
- If LLM fails to produce valid JSON, Odysseus falls back to a single‑hop approach (treat as simple query).
- Exceptions are caught; a generic error message is returned and the workflow continues with a safe default.

---

## Testing Strategy

1. **Unit Tests** for `detect_complexity` with varied query patterns.
2. **Mock LLM** responses to verify JSON parsing in `decompose_query`.
3. **Integration Tests**: End‑to‑end complex query through `/search` endpoint, assert that multiple sub‑queries are executed and final answer contains combined information.
4. **Performance**: Total time for a 3‑sub‑query plan ≤ 2 seconds (excluding LLM latency).

---

## Key Classes & Data Structures

```python
@dataclass
class SubQuery:
    id: str
    query: str
    purpose: str
    priority: int
    answer: Optional[str] = None
    sources: List[Dict[str, Any]] = field(default_factory=list)
```

---

*Odysseus empowers Vantage to tackle multi‑step reasoning tasks, turning a single natural‑language question into a structured plan of sub‑queries and a coherent final answer.*
