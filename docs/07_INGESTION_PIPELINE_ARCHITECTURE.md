# VANTAGE - Document Ingestion Pipeline Architecture (Deep Dive)

## Table of Contents
- [Ingestion Pipeline Overview](#ingestion-pipeline-overview)
- [File Discovery & Validation](#file-discovery--validation)
- [Content Extraction by File Type](#content-extraction-by-file-type)
- [LLM-Based Summarization](#llm-based-summarization)
- [Embedding Generation](#embedding-generation)
- [Knowledge Graph Extraction](#knowledge-graph-extraction)
- [OpenSearch Indexing](#opensearch-indexing)
- [File Watcher Integration](#file-watcher-integration)
- [Error Handling & Recovery](#error-handling--recovery)

---

## Ingestion Pipeline Overview

The document ingestion pipeline is responsible for processing documents from local directories, extracting content, generating summaries and embeddings, and indexing them in OpenSearch for hybrid search.

```
┌─────────────────────────────────────────────────────────────────────┐
│                   INGESTION PIPELINE OVERVIEW                        │
└─────────────────────────────────────────────────────────────────────┘

USER INPUT: Select directory "/path/to/documents"
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 1: FILE DISCOVERY                                             │
│   • Scan directory recursively                                       │
│   • Filter by supported extensions                                   │
│   • Collect file metadata (path, size, modified time)                │
│   Output: List of files to process                                   │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 2: CONTENT EXTRACTION (Per File)                              │
│   • PDF → PyPDF + Qwen OCR fallback                                 │
│   • DOCX → python-docx                                               │
│   • TXT/MD → Direct read                                             │
│   • XLSX/CSV → pandas                                                │
│   • Images → Qwen3-VL vision OCR                                     │
│   Output: Raw text content                                           │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 3: TEXT PROCESSING                                            │
│   • Truncate to 50K chars                                            │
│   • Clean whitespace                                                 │
│   • Normalize unicode                                                │
│   Output: Cleaned full_content                                       │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 4: LLM SUMMARIZATION (Ollama qwen3-vl:8b)                     │
│   • Generate detailed 3-5 sentence summary                           │
│   • Extract keywords, entities, topics                               │
│   • Classify document type                                           │
│   Output: detailed_summary, keywords, entities, topics, doc_type    │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 5: EMBEDDING GENERATION (Sentence-Transformers)               │
│   • Model: nomic-embed-text (768 dims)                               │
│   • Input: detailed_summary (not full content)                       │
│   • L2 normalization                                                 │
│   Output: 768-dimensional vector                                     │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 6: KNOWLEDGE GRAPH EXTRACTION                                 │
│   • Extract entities from summary                                    │
│   • Identify entity types                                            │
│   • Extract relationships                                            │
│   • Add to NetworkX graph                                            │
│   Output: Graph nodes and edges                                      │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 7: OPENSEARCH INDEXING                                        │
│   • Upsert document (update if exists)                               │
│   • Index: full_content, summary, embedding, metadata                │
│   • Bulk indexing for efficiency                                     │
│   Output: Indexed document                                           │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STAGE 8: PROGRESS STREAMING (SSE)                                   │
│   • Stream updates to frontend                                       │
│   • Update: current file, progress %, stage                          │
│   Output: Real-time progress events                                  │
└─────────────────────────────────────────────────────────────────────┘
    │
    ▼
COMPLETION: All documents indexed, ready for search
```

---

## File Discovery & Validation

**File**: `backend/ingestion.py` (IngestionPipeline class)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FILE DISCOVERY PROCESS                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Input: directory_path = "/Users/john/Documents/Research"            │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ STEP 1: VALIDATE DIRECTORY                                      │ │
│  │                                                                  │ │
│  │ if not os.path.exists(directory_path):                          │ │
│  │     raise DirectoryNotFoundError                                │ │
│  │                                                                  │ │
│  │ if not os.path.isdir(directory_path):                           │ │
│  │     raise NotADirectoryError                                    │ │
│  │                                                                  │ │
│  │ if not os.access(directory_path, os.R_OK):                      │ │
│  │     raise PermissionError("Cannot read directory")              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ STEP 2: SCAN DIRECTORY                                          │ │
│  │                                                                  │ │
│  │ Supported Extensions (from config.yaml):                         │ │
│  │   Documents: .pdf, .docx, .txt, .md                             │ │
│  │   Spreadsheets: .xlsx, .csv                                      │ │
│  │   Images: .png, .jpg, .jpeg, .gif, .bmp                         │ │
│  │                                                                  │ │
│  │ Recursive Scan:                                                  │ │
│  │   for root, dirs, files in os.walk(directory_path):             │ │
│  │       for filename in files:                                    │ │
│  │           file_path = os.path.join(root, filename)              │ │
│  │           ext = os.path.splitext(filename)[1].lower()           │ │
│  │                                                                  │ │
│  │           # Filter criteria                                      │ │
│  │           if ext in supported_extensions:                       │ │
│  │               if not filename.startswith('.'):  # Skip hidden   │ │
│  │                   if os.path.getsize(file_path) < 100*1024*1024:│ │
│  │                       files_to_process.append(file_path)        │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ STEP 3: COLLECT METADATA                                        │ │
│  │                                                                  │ │
│  │ For each file:                                                   │ │
│  │   metadata = {                                                   │ │
│  │       "file_path": "/Users/john/Documents/Research/paper.pdf",  │ │
│  │       "filename": "paper.pdf",                                   │ │
│  │       "file_type": "pdf",                                        │ │
│  │       "file_size": 2048576,  # bytes                            │ │
│  │       "modified_time": datetime.fromtimestamp(                  │ │
│  │           os.path.getmtime(file_path)                           │ │
│  │       ),                                                         │ │
│  │       "created_time": datetime.fromtimestamp(                   │ │
│  │           os.path.getctime(file_path)                           │ │
│  │       )                                                          │ │
│  │   }                                                              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ STEP 4: CHECK FOR ALREADY INDEXED                              │ │
│  │                                                                  │ │
│  │ Generate doc_id from file_path:                                 │ │
│  │   doc_id = hashlib.sha256(file_path.encode()).hexdigest()      │ │
│  │                                                                  │ │
│  │ Check OpenSearch:                                                │ │
│  │   if opensearch.exists(index="locallens_index", id=doc_id):    │ │
│  │       # Check if file modified since last index                │ │
│  │       existing_doc = opensearch.get(id=doc_id)                 │ │
│  │       if existing_doc['updated_at'] >= file_modified_time:     │ │
│  │           skip_file()  # Already indexed, up to date           │ │
│  │       else:                                                      │ │
│  │           reindex_file()  # Modified, needs reindexing         │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  Output:                                                             │
│    files_to_process = [                                             │
│      {                                                               │
│        "file_path": "/Users/john/Documents/Research/paper1.pdf",    │
│        "metadata": {...}                                             │
│      },                                                              │
│      {                                                               │
│        "file_path": "/Users/john/Documents/Research/paper2.docx",   │
│        "metadata": {...}                                             │
│      },                                                              │
│      ...                                                             │
│    ]                                                                 │
│                                                                       │
│  Total files: 47 (3 PDFs, 12 DOCXs, 15 TXTs, 10 Images, 7 CSVs)     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Content Extraction by File Type

### PDF Extraction

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PDF EXTRACTION                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Library: PyPDF (pypdf)                                              │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ PRIMARY METHOD: Text Extraction                                 │ │
│  │                                                                  │ │
│  │ import pypdf                                                     │ │
│  │                                                                  │ │
│  │ def extract_pdf_text(file_path):                                │ │
│  │     with open(file_path, 'rb') as f:                            │ │
│  │         pdf_reader = pypdf.PdfReader(f)                         │ │
│  │         text = ""                                                │ │
│  │         for page in pdf_reader.pages:                           │ │
│  │             text += page.extract_text()                         │ │
│  │                                                                  │ │
│  │     # Extract metadata                                           │ │
│  │     metadata = {                                                 │ │
│  │         "page_count": len(pdf_reader.pages),                    │ │
│  │         "author": pdf_reader.metadata.get('/Author', 'Unknown'),│ │
│  │         "title": pdf_reader.metadata.get('/Title', ''),         │ │
│  │         "creator": pdf_reader.metadata.get('/Creator', '')      │ │
│  │     }                                                            │ │
│  │                                                                  │ │
│  │     return text, metadata                                        │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ FALLBACK METHOD: OCR with Qwen3-VL                             │ │
│  │                                                                  │ │
│  │ If text extraction fails or returns < 100 chars:                │ │
│  │                                                                  │ │
│  │ 1. Convert PDF pages to images (pdf2image):                     │ │
│  │    images = convert_from_path(file_path)                        │ │
│  │                                                                  │ │
│  │ 2. OCR each page with Qwen3-VL vision model:                    │ │
│  │    for img in images:                                           │ │
│  │        # Save image to temp file                                │ │
│  │        img_path = save_temp_image(img)                          │ │
│  │                                                                  │ │
│  │        # Call Qwen3-VL with vision                              │ │
│  │        response = ollama.generate(                              │ │
│  │            model="qwen3-vl:8b",                                 │ │
│  │            prompt="Extract all text from this image",           │ │
│  │            images=[img_path]                                    │ │
│  │        )                                                         │ │
│  │        text += response['response']                             │ │
│  │                                                                  │ │
│  │ 3. Return OCR'd text                                            │ │
│  │                                                                  │ │
│  │ Note: OCR is much slower (5-30s per page) but more accurate     │ │
│  │       for scanned PDFs or PDFs with embedded images             │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  Example Output:                                                     │
│    text = "Abstract\nThis paper explores deep learning..."          │
│    metadata = {                                                      │
│      "page_count": 12,                                               │
│      "author": "John Smith",                                         │
│      "title": "Deep Learning for NLP"                                │
│    }                                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

### DOCX Extraction

```
┌─────────────────────────────────────────────────────────────────────┐
│                       DOCX EXTRACTION                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Library: python-docx                                                │
│                                                                       │
│  import docx                                                         │
│                                                                       │
│  def extract_docx_text(file_path):                                  │
│      doc = docx.Document(file_path)                                 │
│      text = ""                                                       │
│                                                                       │
│      # Extract paragraphs                                            │
│      for para in doc.paragraphs:                                    │
│          text += para.text + "\n"                                    │
│                                                                       │
│      # Extract tables                                                │
│      for table in doc.tables:                                       │
│          for row in table.rows:                                     │
│              for cell in row.cells:                                 │
│                  text += cell.text + " "                            │
│          text += "\n"                                                │
│                                                                       │
│      # Extract metadata                                              │
│      core_props = doc.core_properties                               │
│      metadata = {                                                    │
│          "author": core_props.author,                                │
│          "title": core_props.title,                                  │
│          "created": core_props.created,                              │
│          "modified": core_props.modified                             │
│      }                                                               │
│                                                                       │
│      return text, metadata                                           │
│                                                                       │
│  Example Output:                                                     │
│    text = "Chapter 1: Introduction\nThis document discusses..."      │
│    metadata = {                                                      │
│      "author": "Jane Doe",                                           │
│      "title": "Research Notes"                                       │
│    }                                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

### Image Extraction (OCR + Vision)

```
┌─────────────────────────────────────────────────────────────────────┐
│                     IMAGE EXTRACTION (Vision OCR)                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Library: Qwen3-VL (Ollama)                                          │
│                                                                       │
│  def extract_image_content(file_path):                              │
│      # Call Qwen3-VL with vision capability                         │
│      response = ollama.generate(                                    │
│          model="qwen3-vl:8b",                                       │
│          prompt="""                                                  │
│              Analyze this image and provide:                         │
│              1. All visible text (OCR)                               │
│              2. A detailed description of the image                  │
│              3. Key visual elements                                  │
│          """,                                                        │
│          images=[file_path],                                        │
│          temperature=0.3                                             │
│      )                                                               │
│                                                                       │
│      content = response['response']                                 │
│                                                                       │
│      # Also store image path for later retrieval                    │
│      metadata = {                                                    │
│          "image_path": file_path,                                    │
│          "has_text": "OCR:" in content,                             │
│          "has_visual_description": true                              │
│      }                                                               │
│                                                                       │
│      return content, metadata                                        │
│                                                                       │
│  Example Output:                                                     │
│    content = """                                                     │
│      OCR Text: "Figure 3: Neural Network Architecture"              │
│      Visual Description: The image shows a diagram of a neural      │
│      network with 3 layers: input layer (10 nodes), hidden layer    │
│      (5 nodes), and output layer (2 nodes). Arrows connect all      │
│      nodes between layers.                                           │
│      Key Elements: Neural network diagram, 3 layers, blue nodes     │
│    """                                                               │
└─────────────────────────────────────────────────────────────────────┘
```

### Text File Extraction

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TEXT FILE EXTRACTION (.txt, .md)                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  def extract_text_file(file_path):                                  │
│      # Try multiple encodings                                        │
│      encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']           │
│                                                                       │
│      for encoding in encodings:                                     │
│          try:                                                        │
│              with open(file_path, 'r', encoding=encoding) as f:     │
│                  text = f.read()                                    │
│              return text, {"encoding": encoding}                    │
│          except UnicodeDecodeError:                                 │
│              continue                                                │
│                                                                       │
│      raise UnicodeDecodeError("Unable to decode file")              │
└─────────────────────────────────────────────────────────────────────┘
```

### Spreadsheet Extraction

```
┌─────────────────────────────────────────────────────────────────────┐
│                  SPREADSHEET EXTRACTION (.xlsx, .csv)                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Library: pandas                                                     │
│                                                                       │
│  def extract_spreadsheet(file_path):                                │
│      if file_path.endswith('.csv'):                                 │
│          df = pd.read_csv(file_path)                                │
│      else:  # .xlsx                                                  │
│          df = pd.read_excel(file_path)                              │
│                                                                       │
│      # Convert to text representation                                │
│      text = f"Column Headers: {', '.join(df.columns)}\n\n"          │
│      text += df.to_string(index=False)                              │
│                                                                       │
│      metadata = {                                                    │
│          "rows": len(df),                                            │
│          "columns": len(df.columns),                                 │
│          "column_names": list(df.columns)                            │
│      }                                                               │
│                                                                       │
│      return text, metadata                                           │
│                                                                       │
│  Example Output:                                                     │
│    text = """                                                        │
│      Column Headers: Name, Age, Department                           │
│                                                                       │
│      John Smith    35    Engineering                                 │
│      Jane Doe      28    Marketing                                   │
│      ...                                                             │
│    """                                                               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## LLM-Based Summarization

```
┌─────────────────────────────────────────────────────────────────────┐
│                   LLM SUMMARIZATION (Ollama qwen3-vl:8b)             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Input: full_content (cleaned, up to 50K chars)                      │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ PROMPT CONSTRUCTION                                             │ │
│  │                                                                  │ │
│  │ system_prompt = """                                              │ │
│  │   You are a document analysis assistant. Analyze the following   │ │
│  │   document and provide structured information.                   │ │
│  │ """                                                              │ │
│  │                                                                  │ │
│  │ user_prompt = f"""                                               │ │
│  │   Analyze the following document and provide:                    │ │
│  │                                                                  │ │
│  │   1. A detailed 3-5 sentence summary capturing the main points   │ │
│  │   2. 5-10 key topics (comma-separated)                           │ │
│  │   3. Named entities (people, organizations, locations)           │ │
│  │   4. 5-10 important keywords                                     │ │
│  │   5. Document type classification (one of: research_paper,       │ │
│  │      technical_doc, meeting_notes, report, tutorial, article,    │ │
│  │      code, data, other)                                          │ │
│  │                                                                  │ │
│  │   Respond in JSON format:                                        │ │
│  │   {{                                                              │ │
│  │     "summary": "...",                                            │ │
│  │     "topics": ["topic1", "topic2", ...],                         │ │
│  │     "entities": ["entity1", "entity2", ...],                     │ │
│  │     "keywords": ["keyword1", "keyword2", ...],                   │ │
│  │     "document_type": "research_paper"                            │ │
│  │   }}                                                             │ │
│  │                                                                  │ │
│  │   Document content:                                              │ │
│  │   {full_content}                                                 │ │
│  │ """                                                              │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ LLM CALL                                                        │ │
│  │                                                                  │ │
│  │ response = ollama.generate(                                     │ │
│  │     model="qwen3-vl:8b",                                        │ │
│  │     system=system_prompt,                                       │ │
│  │     prompt=user_prompt,                                         │ │
│  │     temperature=0.3,  # Low for deterministic outputs           │ │
│  │     max_tokens=500,   # Enough for summary + metadata           │ │
│  │     timeout=30        # 30 second timeout                       │ │
│  │ )                                                                │ │
│  │                                                                  │ │
│  │ Time: 2-8 seconds (depending on content length)                 │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ RESPONSE PARSING                                                │ │
│  │                                                                  │ │
│  │ import json                                                      │ │
│  │                                                                  │ │
│  │ try:                                                             │ │
│  │     result = json.loads(response['response'])                   │ │
│  │ except json.JSONDecodeError:                                    │ │
│  │     # Fallback: Extract JSON from response                      │ │
│  │     # Sometimes LLM adds extra text around JSON                 │ │
│  │     json_match = re.search(r'\{.*\}', response['response'],     │ │
│  │                            re.DOTALL)                            │ │
│  │     if json_match:                                              │ │
│  │         result = json.loads(json_match.group())                 │ │
│  │     else:                                                        │ │
│  │         # Manual extraction fallback                            │ │
│  │         result = extract_manually(response['response'])         │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  Example Output:                                                     │
│    {                                                                 │
│      "summary": "This research paper explores the application of    │
│                  transformer models to natural language processing   │
│                  tasks. The authors demonstrate that attention       │
│                  mechanisms significantly improve performance on     │
│                  tasks like machine translation and question         │
│                  answering.",                                        │
│      "topics": ["transformers", "natural language processing",       │
│                 "attention mechanism", "machine translation",        │
│                 "neural networks"],                                  │
│      "entities": ["BERT", "GPT", "Google", "Stanford University"],   │
│      "keywords": ["transformer", "attention", "NLP", "BERT",         │
│                   "neural network", "encoder", "decoder"],           │
│      "document_type": "research_paper"                               │
│    }                                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Embedding Generation

```
┌─────────────────────────────────────────────────────────────────────┐
│               EMBEDDING GENERATION (Sentence-Transformers)           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Model: nomic-embed-text                                             │
│  Dimensions: 768                                                     │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ MODEL INITIALIZATION (Once at startup)                          │ │
│  │                                                                  │ │
│  │ from sentence_transformers import SentenceTransformer            │ │
│  │                                                                  │ │
│  │ embedding_model = SentenceTransformer('nomic-embed-text')       │ │
│  │                                                                  │ │
│  │ # Move to GPU if available                                      │ │
│  │ device = 'cuda' if torch.cuda.is_available() else 'cpu'         │ │
│  │ embedding_model = embedding_model.to(device)                    │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ EMBEDDING GENERATION (Per Document)                            │ │
│  │                                                                  │ │
│  │ Input: detailed_summary (NOT full_content)                      │ │
│  │   "This research paper explores the application of transformer  │ │
│  │    models to natural language processing tasks..."              │ │
│  │                                                                  │ │
│  │ Rationale for using summary instead of full content:            │ │
│  │   • Summaries are more semantically dense                       │ │
│  │   • Better query-document alignment                             │ │
│  │   • Faster embedding generation                                 │ │
│  │   • Full content still indexed for BM25 search                  │ │
│  │                                                                  │ │
│  │ Generate Embedding:                                              │ │
│  │   embedding = embedding_model.encode(                           │ │
│  │       detailed_summary,                                          │ │
│  │       normalize_embeddings=True,  # L2 normalization            │ │
│  │       show_progress_bar=False                                   │ │
│  │   )                                                              │ │
│  │                                                                  │ │
│  │ Output: numpy array of shape (768,)                             │ │
│  │   [0.123, -0.456, 0.789, ..., 0.321]                            │ │
│  │                                                                  │ │
│  │ Time: 100-500ms (depends on GPU vs CPU)                         │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ BATCH PROCESSING (For Multiple Documents)                      │ │
│  │                                                                  │ │
│  │ For efficiency, process documents in batches:                   │ │
│  │                                                                  │ │
│  │ summaries = [doc1_summary, doc2_summary, ..., doc10_summary]    │ │
│  │ embeddings = embedding_model.encode(                            │ │
│  │     summaries,                                                   │ │
│  │     batch_size=16,                                              │ │
│  │     normalize_embeddings=True                                   │ │
│  │ )                                                                │ │
│  │                                                                  │ │
│  │ Output: numpy array of shape (10, 768)                          │ │
│  │                                                                  │ │
│  │ Time: ~50-100ms per document (batch processing)                 │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Knowledge Graph Extraction

```
┌─────────────────────────────────────────────────────────────────────┐
│                   KNOWLEDGE GRAPH EXTRACTION                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Input: summary, entities (from LLM), full_content                   │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ ENTITY EXTRACTION                                               │ │
│  │                                                                  │ │
│  │ Entities from LLM:                                               │ │
│  │   ["BERT", "GPT", "Google", "Stanford University"]               │ │
│  │                                                                  │ │
│  │ For each entity:                                                 │ │
│  │   1. Classify entity type (using heuristics or LLM)             │ │
│  │      • Contains "University", "Inc", "Corp" → ORGANIZATION      │ │
│  │      • Capitalized, short → PERSON or CONCEPT                   │ │
│  │      • Country, city names → LOCATION                           │ │
│  │                                                                  │ │
│  │   2. Create entity node in graph:                               │ │
│  │      graph.add_node(                                            │ │
│  │          entity_id="ent_bert",                                  │ │
│  │          name="BERT",                                            │ │
│  │          type="CONCEPT",                                         │ │
│  │          mentioned_in=[doc_id],                                 │ │
│  │          first_seen=datetime.now()                              │ │
│  │      )                                                           │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ RELATIONSHIP EXTRACTION                                         │ │
│  │                                                                  │ │
│  │ Method 1: Co-occurrence in same sentence                        │ │
│  │   • If "BERT" and "Google" appear in same sentence:            │ │
│  │     graph.add_edge("ent_bert", "ent_google", type="CO_OCCURS") │ │
│  │                                                                  │ │
│  │ Method 2: LLM-based relationship extraction (optional)          │ │
│  │   • Prompt: "What is the relationship between BERT and Google?" │ │
│  │   • Response: "BERT was developed by Google"                    │ │
│  │   • graph.add_edge("ent_bert", "ent_google",                   │ │
│  │                    type="CREATED_BY")                           │ │
│  │                                                                  │ │
│  │ Method 3: Document-Entity relationship                          │ │
│  │   • Always create edge from document to mentioned entities:     │ │
│  │     graph.add_edge("doc_id", "ent_bert", type="MENTIONS")      │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ GRAPH UPDATE                                                    │ │
│  │                                                                  │ │
│  │ If entity already exists:                                        │ │
│  │   • Update mentioned_in list                                    │ │
│  │   • Increment mention_count                                     │ │
│  │   • Update last_seen timestamp                                  │ │
│  │                                                                  │ │
│  │ If relationship already exists:                                  │ │
│  │   • Increment strength (co-occurrence count)                    │ │
│  │   • Add document to relationship metadata                       │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ PERSISTENCE                                                     │ │
│  │                                                                  │ │
│  │ Save to SQLite (locallens_graph.db):                            │ │
│  │                                                                  │ │
│  │ INSERT INTO entities (id, name, type, metadata)                 │ │
│  │ VALUES ('ent_bert', 'BERT', 'CONCEPT', '{"mention_count": 5}') │ │
│  │                                                                  │ │
│  │ INSERT INTO relationships (source_id, target_id, type, strength)│ │
│  │ VALUES ('ent_bert', 'ent_google', 'CREATED_BY', 1.0)            │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  Example Graph Structure:                                            │
│                                                                       │
│    [BERT] ──CREATED_BY──> [Google]                                  │
│      │                                                               │
│      │──RELATED_TO──> [Transformers]                                │
│      │                                                               │
│      │──CO_OCCURS──> [GPT]                                          │
│      │                                                               │
│      │<──MENTIONS── [doc_research_paper.pdf]                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## OpenSearch Indexing

```
┌─────────────────────────────────────────────────────────────────────┐
│                      OPENSEARCH INDEXING                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Input: All processed document data                                  │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ DOCUMENT STRUCTURE                                              │ │
│  │                                                                  │ │
│  │ document = {                                                     │ │
│  │     "id": "sha256_hash_of_filepath",                             │ │
│  │     "filename": "research_paper.pdf",                            │ │
│  │     "file_path": "/Users/john/Documents/research_paper.pdf",     │ │
│  │     "file_type": "pdf",                                          │ │
│  │     "file_size": 2048576,                                        │ │
│  │     "document_type": "research_paper",                           │ │
│  │     "detailed_summary": "This research paper explores...",       │ │
│  │     "full_content": "Abstract\nIntroduction\n...",               │ │
│  │     "keywords": ["transformer", "attention", "NLP"],             │ │
│  │     "entities": ["BERT", "GPT", "Google"],                       │ │
│  │     "topics": ["transformers", "NLP", "attention mechanism"],    │ │
│  │     "vector_embedding": [0.123, -0.456, ..., 0.321],  # 768 dims │ │
│  │     "created_at": "2025-01-15T10:30:00Z",                        │ │
│  │     "updated_at": "2025-01-15T10:30:00Z",                        │ │
│  │     "page_count": 12,  # PDF-specific                            │ │
│  │     "author": "John Smith",  # From metadata                     │ │
│  │ }                                                                │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ INDEXING OPERATION                                              │ │
│  │                                                                  │ │
│  │ Upsert (Update or Insert):                                       │ │
│  │   opensearch.index(                                             │ │
│  │       index="locallens_index",                                  │ │
│  │       id=document['id'],                                        │ │
│  │       body=document,                                            │ │
│  │       refresh=False  # Don't refresh immediately (performance)  │ │
│  │   )                                                              │ │
│  │                                                                  │ │
│  │ If document ID exists → Update                                  │ │
│  │ If document ID is new → Insert                                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ BULK INDEXING (For Multiple Documents)                         │ │
│  │                                                                  │ │
│  │ For efficiency, batch index documents:                          │ │
│  │                                                                  │ │
│  │ from opensearchpy import helpers                                │ │
│  │                                                                  │ │
│  │ actions = [                                                      │ │
│  │     {                                                            │ │
│  │         "_op_type": "index",                                    │ │
│  │         "_index": "locallens_index",                            │ │
│  │         "_id": doc['id'],                                       │ │
│  │         "_source": doc                                          │ │
│  │     }                                                            │ │
│  │     for doc in documents                                        │ │
│  │ ]                                                                │ │
│  │                                                                  │ │
│  │ success, failed = helpers.bulk(                                 │ │
│  │     opensearch,                                                  │ │
│  │     actions,                                                     │ │
│  │     chunk_size=10,  # Index 10 docs at a time                   │ │
│  │     raise_on_error=False                                        │ │
│  │ )                                                                │ │
│  │                                                                  │ │
│  │ Time: ~50-200ms per batch of 10 documents                       │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ REFRESH INDEX                                                   │ │
│  │                                                                  │ │
│  │ After all documents indexed:                                     │ │
│  │   opensearch.indices.refresh(index="locallens_index")           │ │
│  │                                                                  │ │
│  │ This makes documents immediately searchable                      │ │
│  │ Time: 100-500ms (depends on index size)                         │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## File Watcher Integration

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FILE WATCHER INTEGRATION                          │
└─────────────────────────────────────────────────────────────────────┘

When indexing completes with watch_mode=True:
  ↓
Start FileWatcher for the directory:
  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ File Modified: /Users/john/Documents/research_paper.pdf             │
│   ↓                                                                  │
│ FileSystemEvent triggered                                            │
│   ↓                                                                  │
│ Debounce timer (3 seconds)                                           │
│   ↓ (Wait for more events)                                           │
│ Timer expires                                                         │
│   ↓                                                                  │
│ Queue reindexing:                                                    │
│   reindex_file("/Users/john/Documents/research_paper.pdf")           │
│   ↓                                                                  │
│ Run full ingestion pipeline (Steps 2-7):                            │
│   • Extract content                                                  │
│   • Generate summary                                                 │
│   • Generate embedding                                               │
│   • Update graph                                                     │
│   • Upsert in OpenSearch                                             │
│   ↓                                                                  │
│ Notify frontend (SSE):                                               │
│   event: document_updated                                            │
│   data: {"file": "research_paper.pdf", "status": "reindexed"}        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Error Handling & Recovery

```
┌─────────────────────────────────────────────────────────────────────┐
│                   ERROR HANDLING & RECOVERY                          │
└─────────────────────────────────────────────────────────────────────┘

Common Errors and Handling:

┌─────────────────────────────────────────────────────────────────────┐
│ ERROR: File Not Readable (PermissionError)                          │
│   • Log error with file path                                         │
│   • Skip file                                                        │
│   • Notify user via SSE                                              │
│   • Continue with next file                                          │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ ERROR: PDF Extraction Failed (PyPDF error)                          │
│   • Try OCR fallback with Qwen3-VL                                  │
│   • If OCR fails → Skip file, log error                             │
│   • Continue with next file                                          │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ ERROR: Ollama Timeout (LLM summarization)                           │
│   • Retry up to 2 times with exponential backoff                    │
│   • If still fails → Use fallback summary (first 500 chars)         │
│   • Mark document as "partial_index"                                │
│   • Continue with next file                                          │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ ERROR: OpenSearch Connection Failed                                 │
│   • Retry 3 times with exponential backoff (1s, 2s, 4s)             │
│   • If still fails → Store documents in local queue                 │
│   • Notify user: "Indexing paused, will retry"                      │
│   • Retry queue every 30 seconds                                    │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ ERROR: Out of Memory (Large file)                                   │
│   • Skip file                                                        │
│   • Log warning with file size                                      │
│   • Suggest increasing file size limit in config                    │
│   • Continue with next file                                          │
└─────────────────────────────────────────────────────────────────────┘

Progress Tracking:
  • Total files: 100
  • Successful: 92
  • Failed: 5 (logged in ingestion_YYYYMMDD_HHMMSS.log)
  • Skipped: 3 (already indexed, up to date)

Final Report:
  "Indexed 92/100 documents successfully. 5 failed (see logs). 3 skipped."
```

---

**Document Version**: 1.0
**Last Updated**: 2025-12-31
**Related Docs**: `02_BACKEND_ARCHITECTURE.md`, `06_DATA_FLOW_AND_REQUEST_LIFECYCLE.md`
