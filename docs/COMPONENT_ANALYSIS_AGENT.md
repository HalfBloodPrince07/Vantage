# AnalysisAgent (Deep Analysis) Architecture

**File:** `backend/agents/analysis_agent.py`

---

## Purpose

The AnalysisAgent performs **in‑depth analytical reasoning** on retrieved documents. It extracts trends, performs comparative analysis, and generates structured data (tables, charts) that can be incorporated into the final answer.

---

## High‑Level ASCII Diagram

```
+-------------------+      +----------------------+      +-------------------+
|   Retrieved Docs  | ---> |   AnalysisAgent      | ---> |   Structured Data |
+-------------------+      +----------------------+      +-------------------+
        |                         |                         |
        | 1. Identify patterns   | 2. Compute metrics      |
        | 3. Generate tables      | 4. Summarize insights   |
        v                         v                         v
+-------------------+      +----------------------+      +-------------------+
|   Trend Finder    |      |   Comparator         |      |   Table Builder   |
+-------------------+      +----------------------+      +-------------------+
```

---

## Core Methods

```python
class AnalysisAgent:
    async def analyze(self, docs: List[DocumentResult]) -> AnalysisReport:
        """Run trend detection, comparative analysis, and generate tables."""
        trends = self._detect_trends(docs)
        comparisons = self._compare_documents(docs)
        tables = self._build_tables(comparisons)
        summary = self._summarize_findings(trends, tables)
        return AnalysisReport(summary=summary, tables=tables, trends=trends)

    def _detect_trends(self, docs: List[DocumentResult]) -> List[Trend]:
        ...

    def _compare_documents(self, docs: List[DocumentResult]) -> List[Comparison]:
        ...

    def _build_tables(self, comparisons: List[Comparison]) -> List[Table]:
        ...

    def _summarize_findings(self, trends: List[Trend], tables: List[Table]) -> str:
        ...
```

---

## Interaction with Other Components

- **RetrievalController** supplies the `DocumentResult` list.
- **Odysseus** may request analysis for multi‑hop reasoning.
- **Themis** can use the analysis confidence when scoring the final answer.
- **Frontend** displays generated tables via React components.

---

## Configuration (`config.yaml`)

```yaml
agents:
  analysis_agent:
    enabled: true
    max_documents: 10
    llm:
      temperature: 0.2
      max_tokens: 1024
```

---

## Error Handling & Logging

- Logs each stage with `loguru` (`🔎 Analysis`).
- If metric calculation fails, falls back to a simple bullet‑point summary.
- Exceptions raise `AnalysisError` caught by Zeus, leading to a generic answer.

---

## Testing Strategy

1. **Unit Tests** for trend detection on synthetic time‑series data.
2. **Mock LLM** for summary generation.
3. **Integration Test**: End‑to‑end query that triggers analysis, verify tables appear in the response.
4. **Performance**: Analysis ≤ 800 ms for up to 10 documents.

---

## Data Classes

```python
@dataclass
class Trend:
    description: str
    confidence: float

@dataclass
class Comparison:
    doc_a: str
    doc_b: str
    metric: str
    value: float

@dataclass
class Table:
    headers: List[str]
    rows: List[List[Any]]

@dataclass
class AnalysisReport:
    summary: str
    tables: List[Table]
    trends: List[Trend]
```

---

*The AnalysisAgent enriches Vantage’s answers with data‑driven insights, turning raw search results into actionable information.*
