# Prometheus (Content Extraction) Architecture

**File:** `backend/agents/document_agents/prometheus_reader.py`

---

## Purpose

Prometheus is the **first stage** in the document processing pipeline. It extracts raw textual content, tables, and images from various file formats (PDF, DOCX, XLSX, plain text, images) and normalises them for downstream semantic analysis.

---

## High‑Level ASCII Diagram

```
+-------------------+      +----------------------+      +-------------------+
|   Input File      | ---> |   Format Detector   | ---> |   Extractor      |
+-------------------+      +----------------------+      +-------------------+
        |                         |                         |
        | .pdf                    | .docx                   |
        v                         v                         v
+-------------------+      +----------------------+      +-------------------+
|   PDF Parser      |      |   DOCX Parser       |      |   Image OCR       |
|   (pypdf + OCR)  |      |   (python-docx)     |      |   (Ollama Vision) |
+-------------------+      +----------------------+      +-------------------+
        |                         |                         |
        +-----------+-------------+-------------+-----------+
                    |                           |
                    v                           v
               +-------------------------------+
               |   Normalised Content Object   |
               |   { raw_text, tables, images }|
               +-------------------------------+
```

---

## Core Methods

```python
class PrometheusReader:
    async def extract(self, file_paths: List[str], file_contents: Optional[List[bytes]] = None) -> List[ExtractedContent]:
        """Extract content for each file. Returns a list of `ExtractedContent` dataclasses."""
        ...

    def _detect_format(self, path: str) -> str:
        """Return file type identifier (pdf, docx, xlsx, txt, image)."""
        ...

    async def _extract_pdf(self, path: str) -> ExtractedContent:
        """Use pypdf to read text, then OCR for scanned pages via pytesseract."""
        ...

    async def _extract_docx(self, path: str) -> ExtractedContent:
        """Read paragraphs and tables using python-docx."""
        ...

    async def _extract_image(self, path: str) -> ExtractedContent:
        """Send image to Ollama vision model and capture description as text."""
        ...
```

---

## Interaction with Other Components

- **DaedalusOrchestrator** calls `PrometheusReader.extract` for each attached document.
- **HypatiaAnalyzer** receives `extracted.raw_text` for semantic analysis.
- **MnemosyneExtractor** may also use `extracted.tables` for structured insight extraction.
- **KnowledgeGraph** is updated with any entities discovered during extraction (e.g., named entities in OCR text).

---

## Configuration (`config.yaml`)

```yaml
agents:
  prometheus:
    enabled: true
    ocr:
      language: eng
      timeout_seconds: 30
    vision_model: "qwen3-vl:8b"
```

---

## Error Handling & Logging

- Each extraction step logs with `loguru` (`🔥 Prometheus`).
- If OCR fails, the raw image bytes are stored and a warning emitted.
- Unsupported formats raise `UnsupportedFileTypeError` which is caught by Daedalus and results in a graceful fallback message to the user.

---

## Testing Strategy

1. **Unit Tests** for `_detect_format` with a variety of filenames.
2. **Mock PDF Extraction** using a small sample PDF to verify text extraction and OCR fallback.
3. **Image Extraction Test** – Provide a PNG and assert that the returned `raw_text` contains a description.
4. **Integration Test** – Run the full Daedalus pipeline on a mixed‑type zip and verify that each file yields an `ExtractedContent` instance.

---

## Data Class

```python
@dataclass
class ExtractedContent:
    filename: str
    raw_text: str
    tables: List[Dict] = field(default_factory=list)
    images: List[bytes] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None
```

---

*Prometheus transforms raw user files into a uniform textual representation, enabling the downstream agents to reason over heterogeneous document types.*
