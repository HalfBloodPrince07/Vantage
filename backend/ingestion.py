# backend/ingestion.py - Enhanced Document Processing & Embedding Pipeline

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import hashlib
import asyncio
import gc
from datetime import datetime
from loguru import logger
import httpx
import base64
import re
import json
import time

# Session logging
from backend.utils.session_logger import create_ingestion_logger, SessionLogger

# File processors
from pypdf import PdfReader
from docx import Document
import pandas as pd

# Sentence tokenization
import nltk
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)
from nltk.tokenize import sent_tokenize

# Local embeddings (stable alternative to Ollama)
from sentence_transformers import SentenceTransformer
import torch


class IngestionPipeline:
    """
    Enhanced document ingestion pipeline with:
    - Improved chunking strategies
    - Better prompts for summarization
    - Keyword extraction
    - Entity extraction
    - Local embeddings via sentence-transformers (more stable than Ollama)
    """
    
    def __init__(self, config: Dict[str, Any], opensearch_client, status_callback=None):
        self.config = config
        self.opensearch = opensearch_client
        self.ollama_url = config['ollama']['base_url']
        # Unified model for both text and vision tasks
        self.unified_model = config['ollama']['unified_model']['name']
        
        # Summary settings (no chunking)
        summary_config = config['ingestion'].get('summary', {})
        self.max_summary_length = summary_config.get('max_length', 2000)
        self.max_content_length = summary_config.get('max_content_length', 50000)

        # HTTP client for Ollama (still used for summarization)
        self.client = httpx.AsyncClient(timeout=120.0)

        # Status callback for real-time updates
        self.status_callback = status_callback

        # Initialize local embedding model (much more stable than Ollama)
        logger.info("Loading local embedding model (sentence-transformers)...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.embedding_model = SentenceTransformer(
            'nomic-ai/nomic-embed-text-v1.5',
            trust_remote_code=True,
            device=device
        )
        self.embedding_dimension = self.embedding_model.get_sentence_embedding_dimension()
        self._embedding_lock = asyncio.Lock()  # Thread-safe lock for concurrent access
        logger.info(f"Local embedding model loaded on {device} (dim: {self.embedding_dimension})")

        # Failed files tracker
        self.failed_files_path = Path("logs/failed_ingestion.json")
        self._failed_files_lock = asyncio.Lock()

        logger.info("Enhanced ingestion pipeline initialized")

    async def process_directory(self, directory: Path, task_id: str):
        """Process all files in directory"""
        logger.info(f"Processing directory: {directory}")
        supported_exts = self.config['watcher']['supported_extensions']
        files = []

        for ext in supported_exts:
            files.extend(directory.rglob(f"*{ext}"))

        total_files = len(files)
        logger.info(f"Found {total_files} files to process")

        # Notify status callback
        if self.status_callback:
            await self.status_callback({
                "task_id": task_id,
                "status": "started",
                "message": f"Found {total_files} files to process",
                "total_files": total_files,
                "processed": 0
            })

        batch_size = self.config['watcher']['batch_size']
        for i in range(0, total_files, batch_size):
            batch = files[i:i + batch_size]
            await self._process_batch(batch, task_id, i, total_files)
            logger.info(f"Processed batch {i//batch_size + 1}/{(total_files-1)//batch_size + 1}")

        # Notify completion
        if self.status_callback:
            await self.status_callback({
                "task_id": task_id,
                "status": "completed",
                "message": f"✓ Successfully processed {total_files} files",
                "total_files": total_files,
                "processed": total_files
            })

    async def _process_batch(self, files: List[Path], task_id: str = None, offset: int = 0, total_files: int = 0):
        """Process batch of files concurrently"""
        tasks = [self.process_file(file_path) for file_path in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for idx, (file_path, result) in enumerate(zip(files, results)):
            current_count = offset + idx + 1

            if isinstance(result, Exception):
                logger.error(f"Failed to process {file_path}: {result}")
                if self.status_callback and task_id:
                    await self.status_callback({
                        "task_id": task_id,
                        "status": "processing",
                        "message": f"Error processing: {file_path.name}",
                        "current_file": file_path.name,
                        "processed": current_count,
                        "total_files": total_files
                    })
            elif self.status_callback and task_id:
                # Notify progress for each file (including skipped ones)
                status_msg = f"Skipped: {file_path.name}" if result.get("status") == "skipped" else f"Processed: {file_path.name}"
                await self.status_callback({
                    "task_id": task_id,
                    "status": "processing",
                    "message": status_msg,
                    "current_file": file_path.name,
                    "processed": current_count,
                    "total_files": total_files
                })

    async def process_file(self, file_path: Path) -> Dict[str, Any]:
        """Process a single file - creates ONE document entry with detailed summary + full content"""
        start_time = datetime.now()

        try:
            # Calculate unique document ID
            doc_id = hashlib.md5(str(file_path.absolute()).encode()).hexdigest()

            # Check if document already exists (skip logic)
            if await self.opensearch.document_exists(doc_id):
                logger.info(f"✓ Skipping existing file: {file_path.name}")
                return {"status": "skipped", "id": doc_id}

            # Initialize session logger for this document
            session_log = create_ingestion_logger(file_path.name)
            session_log.log_step("start", "started", {
                "file_path": str(file_path),
                "file_size": file_path.stat().st_size,
                "doc_id": doc_id
            })
            
            logger.info(f"⚙️  Processing file: {file_path.name} (type: {file_path.suffix})")
            file_stats = file_path.stat()

            # 1. Extract content
            step_start = time.time()
            logger.debug(f"  [1/4] Extracting content from {file_path.name}")
            content = await self._extract_content(file_path)
            full_text = content.get('content', '')
            content_type = content.get('type', 'text')  # text, image, spreadsheet
            page_count = content.get('page_count', 0)
            session_log.log_step("extract_content", "completed", {
                "content_type": content_type,
                "content_length": len(full_text),
                "page_count": page_count
            }, duration_ms=(time.time() - step_start) * 1000)
            logger.debug(f"  ✓ Extracted {len(full_text)} characters (type: {content_type})")

            # 2. Generate DETAILED summary with entities and keywords
            step_start = time.time()
            logger.debug(f"  [2/4] Generating detailed summary for {file_path.name}")
            summary_data = await self._generate_detailed_summary(content, file_path, session_log)
            detailed_summary = summary_data['summary']
            keywords = summary_data.get('keywords', '')
            # Structured entities (dict) for hierarchical graph
            entities_structured = summary_data.get('entities', {})
            # Flat list for OpenSearch keyword field
            entities_flat = summary_data.get('entities_flat', [])
            # If entities is somehow a list (legacy), use it directly
            if isinstance(entities_structured, list):
                entities_flat = entities_structured
                entities_structured = {}
            relationships = summary_data.get('relationships', [])
            topics = summary_data.get('topics', [])
            session_log.log_step("generate_summary", "completed", {
                "summary_length": len(detailed_summary),
                "keywords_count": len(keywords.split(',')) if keywords else 0,
                "entities_count": len(entities_flat),
                "relationships_count": len(relationships),
                "topics_count": len(topics)
            }, duration_ms=(time.time() - step_start) * 1000)
            logger.debug(f"  ✓ Detailed summary generated (length: {len(detailed_summary)}, {len(relationships)} relationships)")

            # 3. Determine document type
            step_start = time.time()
            logger.debug(f"  [3/4] Classifying document type for {file_path.name}")
            doc_type = self._classify_document(file_path, content)
            is_image = content_type == 'image'
            session_log.log_step("classify_document", "completed", {
                "doc_type": doc_type,
                "is_image": is_image
            }, duration_ms=(time.time() - step_start) * 1000)
            logger.debug(f"  ✓ Document type: {doc_type}")

            # 4. Generate embedding from detailed summary
            step_start = time.time()
            logger.debug(f"  [4/4] Generating embedding for {file_path.name}")
            embedding = await self.generate_embedding(detailed_summary)
            
            # Check embedding validity
            is_zero_vector = all(v == 0.0 for v in embedding)
            if is_zero_vector:
                logger.warning(f"  ⚠ Zero vector embedding for {file_path.name}")
            session_log.log_step("generate_embedding", "completed", {
                "embedding_dim": len(embedding),
                "is_zero_vector": is_zero_vector
            }, duration_ms=(time.time() - step_start) * 1000)

            # Create SINGLE document entry with all metadata
            document = {
                # Identity
                "id": doc_id,
                "filename": file_path.name,
                "file_path": str(file_path.absolute()),
                
                # Type metadata
                "file_type": file_path.suffix.lower(),
                "content_type": content_type,
                "document_type": doc_type,
                "is_image": is_image,
                
                # Content (summary for search, full for LLM context)
                "detailed_summary": detailed_summary,
                "full_content": full_text[:self.max_content_length] if full_text else detailed_summary,
                
                # Extracted metadata
                "keywords": keywords,
                "entities": entities_flat,  # Flat list for OpenSearch keyword field
                "entities_structured": json.dumps(entities_structured) if entities_structured else "{}",  # JSON for hierarchical graph
                "topics": topics,
                
                # Embedding (of detailed summary)
                "vector_embedding": embedding,
                
                # Statistics
                "word_count": len(full_text.split()) if full_text else len(detailed_summary.split()),
                "page_count": page_count,
                "file_size_bytes": file_stats.st_size,
                
                # Timestamps
                "created_at": datetime.now().isoformat(),
                "last_modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat()
            }

            # Index document in OpenSearch
            await self.opensearch.index_document(document)

            # === NEW: Index entities/relationships in Knowledge Graph ===
            if entities_flat or relationships:
                await self._index_to_knowledge_graph(
                    doc_id=doc_id, 
                    filename=file_path.name,
                    entities=entities_flat,
                    relationships=relationships,
                    content=detailed_summary
                )

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"✓ Successfully indexed: {file_path.name} (took {elapsed:.2f}s)")

            # Log final result to session
            session_log.log_result({
                "status": "success",
                "doc_id": doc_id,
                "filename": file_path.name,
                "summary_length": len(detailed_summary),
                "entities_count": len(entities_flat),
                "elapsed_seconds": elapsed
            })

            # Free memory
            del document
            del embedding
            del full_text
            gc.collect()

            return {
                "status": "success",
                "id": doc_id,
                "detailed_summary": detailed_summary
            }

        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(f"✗ Error processing {file_path.name} after {elapsed:.2f}s: {type(e).__name__}: {e}")
            # Log error if session_log was created
            if 'session_log' in locals():
                session_log.log_error(e, "process_file")
            raise

    def _classify_document(self, file_path: Path, content: Dict) -> str:
        """Classify document type based on content and filename"""
        filename_lower = file_path.name.lower()
        suffix = file_path.suffix.lower()
        
        # Image types
        if suffix in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            if 'screenshot' in filename_lower:
                return 'screenshot'
            elif 'diagram' in filename_lower or 'chart' in filename_lower:
                return 'diagram'
            return 'image'
        
        # Document types based on filename patterns
        if 'invoice' in filename_lower:
            return 'invoice'
        elif 'receipt' in filename_lower:
            return 'receipt'
        elif 'report' in filename_lower:
            return 'report'
        elif 'contract' in filename_lower or 'agreement' in filename_lower:
            return 'contract'
        elif 'resume' in filename_lower or 'cv' in filename_lower:
            return 'resume'
        elif 'presentation' in filename_lower:
            return 'presentation'
        
        # Spreadsheet types
        if suffix in ['.xlsx', '.csv']:
            return 'spreadsheet'
        
        # Default based on extension
        if suffix == '.pdf':
            return 'pdf_document'
        elif suffix == '.docx':
            return 'word_document'
        elif suffix in ['.txt', '.md']:
            return 'text_document'
        
        return 'document'

    async def _extract_content(self, file_path: Path) -> Dict[str, Any]:
        """Extract content based on file type"""
        suffix = file_path.suffix.lower()
        
        if suffix in ['.txt', '.md']:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            return {"type": "text", "content": text}
                
        elif suffix == '.pdf':
            try:
                reader = PdfReader(file_path)
                text_parts = []
                max_pages = 100
                total_pages = len(reader.pages)
                
                for i, page in enumerate(reader.pages):
                    if i >= max_pages:
                        logger.warning(f"PDF has {total_pages} pages, limiting to {max_pages}")
                        text_parts.append(f"\n\n[... {total_pages - max_pages} more pages truncated ...]\n\n")
                        break
                    
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"\n\n--- Page {i+1} ---\n\n{page_text}")
                    
                    del page_text
                
                text = "".join(text_parts)
                del text_parts
                gc.collect()
                
                return {"type": "text", "content": text.strip(), "page_count": min(total_pages, max_pages)}
            except Exception as e:
                logger.warning(f"PDF extraction failed: {e}")
                return {"type": "text", "content": f"PDF file: {file_path.name}"}
                
        elif suffix == '.docx':
            try:
                doc = Document(file_path)
                paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
                text = "\n".join(paragraphs)
                return {"type": "text", "content": text}
            except Exception as e:
                logger.warning(f"DOCX extraction failed: {e}")
                return {"type": "text", "content": f"DOCX file: {file_path.name}"}
                
        elif suffix in ['.xlsx', '.csv']:
            try:
                if suffix == '.xlsx':
                    df = pd.read_excel(file_path)
                else:
                    df = pd.read_csv(file_path)
                    
                text = f"Spreadsheet: {file_path.name}\n"
                text += f"Shape: {len(df)} rows × {len(df.columns)} columns\n"
                text += f"Columns: {', '.join(str(c) for c in df.columns)}\n\n"
                text += "Sample data:\n"
                text += df.head(20).to_string()
                return {"type": "spreadsheet", "content": text, "dataframe": df}
            except Exception as e:
                logger.warning(f"Spreadsheet extraction failed: {e}")
                return {"type": "text", "content": f"Spreadsheet file: {file_path.name}"}
                
        elif suffix in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            return {"type": "image", "path": str(file_path)}
            
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

    async def _generate_detailed_summary(
        self,
        content: Dict[str, Any],
        file_path: Path,
        session_log: Optional[SessionLogger] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive detailed summary with keywords, entities, and topics"""
        
        if content['type'] == 'image':
            return await self._process_image_detailed(content, file_path, session_log=session_log)
        elif content['type'] == 'spreadsheet':
            return await self._process_spreadsheet_detailed(content, file_path, session_log=session_log)
        else:
            return await self._process_text_detailed(content, file_path, session_log=session_log)
    
    async def _process_text_detailed(self, content: Dict, file_path: Path, session_log: Optional[SessionLogger] = None) -> Dict[str, Any]:
        """Process text document with comprehensive detailed summarization"""
        text = content.get('content', '')
        
        # Handle empty or very short content
        if len(text.strip()) < 50:
            return {
                "summary": f"Document: {file_path.name}",
                "keywords": file_path.stem.replace('_', ' ').replace('-', ' '),
                "entities": [],
                "topics": []
            }
        
        # Use more content for better summarization (up to 8000 chars)
        max_length = 10000
        truncated = text[:max_length] + ("..." if len(text) > max_length else "")
        
        prompt = f"""You are an expert document analyst. Create a COMPREHENSIVE summary of this document.

Your summary should be detailed and thorough (5-10 paragraphs), covering:

## Executive Summary
What is this document? What is its main purpose?

## Key Content
Describe the main sections, topics, and content in detail.

## Important Information
- Key facts, figures, statistics, and data points
- Important dates, deadlines, or timeframes
- Specific amounts, quantities, or measurements

---
DOCUMENT CONTENT:
{truncated}
---

Respond in this EXACT format:

SUMMARY:
[Your comprehensive multi-paragraph summary - be detailed and thorough, 5-10 paragraphs]

KEYWORDS: [keyword1, keyword2, keyword3, keyword4, keyword5, ...]

ENTITIES_STRUCTURED:
PERSON: [name1, name2]
SKILLS: [skill1, skill2, skill3, ...]
COMPANIES: [company1, company2, ...]
EDUCATION: [university1, degree1, ...]
LOCATIONS: [location1, location2, ...]
DATES: [date1, date2, ...]
PROJECTS: [project1, project2, ...]
TECHNOLOGIES: [tech1, tech2, ...]

RELATIONSHIPS:
[Entity1 | relationship_type | Entity2]
[Entity3 | relationship_type | Entity4]

TOPICS: [topic1, topic2, topic3, ...]"""

        try:
            llm_start = time.time()
            response = await self.client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.unified_model,
                    "prompt": prompt,
                    "stream": False,
                    "think": True,  # Enable chain-of-thought for better extraction
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 4000  # Much longer for detailed summaries
                    }
                },
                timeout=180.0  # Longer timeout for detailed summaries
            )
            result = response.json()
            response_text = result.get('response', '')
            thinking_content = result.get('thinking', '')
            llm_duration = (time.time() - llm_start) * 1000
            
            # Log LLM call with thinking
            if session_log:
                session_log.log_llm_call(
                    step_name="text_summarization",
                    prompt=prompt,
                    response=response_text,
                    thinking=thinking_content,
                    model=self.unified_model,
                    duration_ms=llm_duration
                )
            
            # Parse structured response
            parsed = self._parse_detailed_response(response_text)
            
            # Fallback if parsing fails
            if not parsed['summary']:
                parsed['summary'] = text[:2000]
            
            return parsed
            
        except Exception as e:
            logger.error(f"Text summarization failed: {e}")
            # Track failed file
            await self._track_failed_file(file_path.name, "text_summarization", str(e))
            return {
                "summary": text[:2000],
                "keywords": file_path.stem.replace('_', ' ').replace('-', ' '),
                "entities": [],
                "topics": []
            }
    
    async def _process_spreadsheet_detailed(self, content: Dict, file_path: Path, session_log: Optional[SessionLogger] = None) -> Dict[str, Any]:
        """Process spreadsheet with detailed analysis"""
        text = content.get('content', '')
        df = content.get('dataframe')
        
        # Build comprehensive description
        description = f"Spreadsheet: {file_path.name}\n"
        if df is not None:
            description += f"Shape: {len(df)} rows × {len(df.columns)} columns\n"
            description += f"Columns: {', '.join(str(c) for c in df.columns)}\n\n"
            
            # Add column analysis
            description += "Column Analysis:\n"
            for col in df.columns:
                non_null = df[col].notna().sum()
                dtype = str(df[col].dtype)
                description += f"- {col}: {dtype}, {non_null} values\n"
            
            description += f"\nSample Data:\n{df.head(10).to_string()}\n"
        
        prompt = f"""Analyze this spreadsheet and provide a detailed summary:

{description}

Respond in this EXACT format:

SUMMARY:
[Describe what this spreadsheet contains, its purpose, the data structure, key columns, and any patterns or insights you can identify. Be comprehensive - 3-5 paragraphs.]

KEYWORDS: [keyword1, keyword2, keyword3, ...]

ENTITIES: [any specific names, dates, or identifiers found in the data]

TOPICS: [data themes and subject areas]"""

        try:
            response = await self.client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.unified_model,
                    "prompt": prompt,
                    "stream": False,
                    "think": True,  # Enable reasoning for spreadsheet analysis
                    "options": {"temperature": 0.3, "num_predict": 2500}
                },
                timeout=120.0
            )
            result = response.json()
            response_text = result.get('response', '')
            
            parsed = self._parse_detailed_response(response_text)
            if not parsed['summary']:
                parsed['summary'] = description
            
            return parsed
            
        except Exception as e:
            logger.error(f"Spreadsheet analysis failed: {e}")
            return {
                "summary": description,
                "keywords": file_path.stem.replace('_', ' '),
                "entities": [],
                "topics": ["spreadsheet", "data"]
            }
    
    async def _process_image_detailed(self, content: Dict, file_path: Path, session_log: Optional[SessionLogger] = None, max_retries: int = 5) -> Dict[str, Any]:
        """Process image with comprehensive detailed description - OPTIMIZED"""
        
        for attempt in range(max_retries):
            try:
                with open(content['path'], 'rb') as f:
                    image_data = f.read()
                
                if len(image_data) == 0:
                    break
                
                # Resize large images for faster processing
                try:
                    from PIL import Image
                    import io
                    img = Image.open(io.BytesIO(image_data))
                    max_dim = 1024
                    if max(img.size) > max_dim:
                        ratio = max_dim / max(img.size)
                        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                        img = img.resize(new_size, Image.Resampling.LANCZOS)
                        buffer = io.BytesIO()
                        img.save(buffer, format='JPEG', quality=85)
                        image_data = buffer.getvalue()
                        logger.debug(f"Resized image to {new_size} for faster processing")
                except Exception as resize_err:
                    logger.warning(f"Image resize failed, using original: {resize_err}")
                
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                
                prompt = """Analyze this image COMPREHENSIVELY and provide a VERY DETAILED description.

Your description should cover ALL of the following in detail:

1. **Main Subject**: What is the primary focus? Describe it thoroughly.
2. **All Visible Elements**: List and describe EVERY object, person, element visible
3. **Text Content**: Transcribe ALL visible text EXACTLY as it appears
4. **Visual Details**: Colors, composition, style, quality, lighting
5. **Context & Purpose**: What is this image about? What is it used for?
6. **Identifiable Information**: Logos, brands, dates, names, locations

Provide a COMPREHENSIVE description (minimum 3-5 detailed paragraphs) that captures everything someone might want to search for in this image.

Respond in this format:
SUMMARY:
[Your very detailed multi-paragraph description]

KEYWORDS: [keyword1, keyword2, keyword3, ...]

TOPICS: [topic1, topic2, topic3, ...]"""

                response = await self.client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.unified_model,
                        "prompt": prompt,
                        "images": [image_base64],
                        "stream": False,
                        # NOTE: think=False for images - thinking mode adds latency without benefit for vision
                        "options": {"temperature": 0.3, "num_predict": 1500}
                    },
                    timeout=90.0  # Reduced from 180s
                )
                
                response.raise_for_status()
                result = response.json()
                
                if 'response' not in result:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    break
                
                summary = result.get('response', '').strip()
                if not summary or len(summary) < 20:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    summary = f"Image file: {file_path.name}"
                
                # Parse if formatted, otherwise use as-is
                if 'SUMMARY:' in summary:
                    parsed = self._parse_detailed_response(summary)
                    if parsed['summary']:
                        return parsed
                
                # Extract keywords from description
                keywords = await self._extract_keywords(summary)
                
                return {
                    "summary": summary,
                    "keywords": keywords,
                    "entities": [],
                    "topics": ["image"]
                }
                
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}/{max_retries}: Image processing failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
        
        # Fallback - track as failed and return basic info
        await self._track_failed_file(file_path.name, "image_processing", "All retries failed")
        return {
            "summary": f"Image file: {file_path.name}. Unable to generate detailed description.",
            "keywords": file_path.stem.replace('_', ' ').replace('-', ' '),
            "entities": [],
            "topics": ["image"]
        }
    
    def _parse_detailed_response(self, response: str) -> Dict[str, Any]:
        """Parse the detailed summary response with topics and relationships"""
        result = {
            "summary": "",
            "keywords": "",
            "entities": {},  # Now a dict with categories
            "entities_flat": [],  # Flat list for backward compatibility
            "relationships": [],
            "topics": []
        }
        
        # Extract summary (everything between SUMMARY: and KEYWORDS:)
        summary_match = re.search(r'SUMMARY:\s*(.+?)(?=KEYWORDS:|$)', response, re.DOTALL | re.IGNORECASE)
        if summary_match:
            result['summary'] = summary_match.group(1).strip()
        
        # Extract keywords
        keywords_match = re.search(r'KEYWORDS:\s*(.+?)(?=ENTITIES|RELATIONSHIPS:|TOPICS:|$)', response, re.DOTALL | re.IGNORECASE)
        if keywords_match:
            keywords_text = keywords_match.group(1).strip()
            keywords_text = re.sub(r'[\[\]]', '', keywords_text)
            result['keywords'] = keywords_text
        
        # Extract structured entities (new format)
        entity_categories = ['PERSON', 'SKILLS', 'COMPANIES', 'EDUCATION', 'LOCATIONS', 'DATES', 'PROJECTS', 'TECHNOLOGIES']
        entities_structured = {}
        
        # Look for ENTITIES_STRUCTURED: section
        entities_section = re.search(r'ENTITIES_STRUCTURED:\s*(.+?)(?=RELATIONSHIPS:|TOPICS:|$)', response, re.DOTALL | re.IGNORECASE)
        if entities_section:
            section_text = entities_section.group(1)
            for category in entity_categories:
                # Try multiple patterns: with brackets, without brackets, or with line breaks
                patterns = [
                    rf'{category}:\s*\[([^\]]*)\]',  # PERSON: [item1, item2]
                    rf'{category}:\s*([^\n]+)',       # PERSON: item1, item2 (no brackets)
                ]
                for pattern in patterns:
                    cat_match = re.search(pattern, section_text, re.IGNORECASE)
                    if cat_match:
                        items_text = cat_match.group(1).strip()
                        # Remove any remaining brackets
                        items_text = re.sub(r'[\[\]]', '', items_text)
                        items = [item.strip().strip('"\'') for item in items_text.split(',') if item.strip() and item.strip() not in ['...', '..', 'etc']]
                        if items:
                            entities_structured[category.lower()] = items[:15]
                            result['entities_flat'].extend(items[:15])
                        break
        
        # Fallback: try old ENTITIES: format if structured not found
        if not entities_structured:
            entities_match = re.search(r'ENTITIES:\s*(.+?)(?=RELATIONSHIPS:|TOPICS:|$)', response, re.DOTALL | re.IGNORECASE)
            if entities_match:
                entities_text = entities_match.group(1).strip()
                entities_text = re.sub(r'[\[\]]', '', entities_text)
                entities = [e.strip() for e in entities_text.split(',') if e.strip()]
                result['entities_flat'] = entities[:30]
                # Auto-categorize based on simple heuristics
                entities_structured = self._auto_categorize_entities(entities[:30])
        
        result['entities'] = entities_structured
        
        # Extract relationships (format: Entity1 | relationship_type | Entity2)
        relationships_match = re.search(r'RELATIONSHIPS:\s*(.+?)(?=TOPICS:|$)', response, re.DOTALL | re.IGNORECASE)
        if relationships_match:
            relationships_text = relationships_match.group(1).strip()
            for line in relationships_text.split('\n'):
                line = line.strip()
                if '|' in line:
                    parts = [p.strip().strip('[]') for p in line.split('|')]
                    if len(parts) >= 3:
                        result['relationships'].append({
                            "source": parts[0],
                            "type": parts[1].lower().replace(' ', '_'),
                            "target": parts[2]
                        })
            result['relationships'] = result['relationships'][:15]
        
        # Extract topics
        topics_match = re.search(r'TOPICS:\s*(.+?)$', response, re.DOTALL | re.IGNORECASE)
        if topics_match:
            topics_text = topics_match.group(1).strip()
            topics_text = re.sub(r'[\[\]]', '', topics_text)
            topics = [t.strip().lower() for t in topics_text.split(',') if t.strip()]
            result['topics'] = topics[:10]
        
        return result
    
    async def _track_failed_file(self, filename: str, failure_type: str, error_message: str):
        """Track failed ingestion files in a JSON file"""
        try:
            async with self._failed_files_lock:
                # Load existing failures or create new
                failures = []
                if self.failed_files_path.exists():
                    try:
                        with open(self.failed_files_path, 'r') as f:
                            failures = json.load(f)
                    except (json.JSONDecodeError, IOError):
                        failures = []
                
                # Add new failure
                failure_entry = {
                    "filename": filename,
                    "type": failure_type,
                    "error": error_message[:200] if error_message else "Unknown error",
                    "timestamp": datetime.now().isoformat()
                }
                
                # Avoid duplicates (same filename and type)
                failures = [f for f in failures if not (f.get("filename") == filename and f.get("type") == failure_type)]
                failures.append(failure_entry)
                
                # Save to file
                self.failed_files_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.failed_files_path, 'w') as f:
                    json.dump(failures, f, indent=2)
                
                logger.warning(f"📋 Tracked failed file: {filename} ({failure_type})")
        except Exception as e:
            logger.error(f"Failed to track failed file: {e}")
    
    def _auto_categorize_entities(self, entities: List[str]) -> Dict[str, List[str]]:
        """Auto-categorize flat entity list using simple heuristics"""
        categorized = {
            'persons': [],
            'skills': [],
            'companies': [],
            'education': [],
            'locations': [],
            'other': []
        }
        
        # Simple keyword-based categorization
        skill_keywords = ['python', 'java', 'javascript', 'react', 'sql', 'aws', 'docker', 'kubernetes', 
                         'machine learning', 'ai', 'ml', 'api', 'html', 'css', 'node', 'fastapi', 'django']
        edu_keywords = ['university', 'college', 'institute', 'school', 'degree', 'bachelor', 'master', 'phd']
        company_suffixes = ['inc', 'llc', 'ltd', 'corp', 'company', 'technologies', 'solutions', 'services']
        
        for entity in entities:
            entity_lower = entity.lower()
            
            if any(skill in entity_lower for skill in skill_keywords):
                categorized['skills'].append(entity)
            elif any(edu in entity_lower for edu in edu_keywords):
                categorized['education'].append(entity)
            elif any(suffix in entity_lower for suffix in company_suffixes):
                categorized['companies'].append(entity)
            elif len(entity.split()) <= 3 and entity[0].isupper():
                # Likely a person name (2-3 words, capitalized)
                categorized['persons'].append(entity)
            else:
                categorized['other'].append(entity)
        
        # Remove empty categories
        return {k: v for k, v in categorized.items() if v}

    async def _process_image(self, content: Dict, file_path: Path, max_retries: int = 3) -> Dict[str, Any]:
        """Process image with enhanced captioning prompt and retry logic"""

        for attempt in range(max_retries):
            try:
                # Read and encode image
                logger.debug(f"Attempt {attempt + 1}/{max_retries}: Reading image {file_path.name}")
                with open(content['path'], 'rb') as f:
                    image_data = f.read()

                if len(image_data) == 0:
                    logger.error(f"Image file is empty: {file_path.name}")
                    break

                image_base64 = base64.b64encode(image_data).decode('utf-8')
                logger.debug(f"Image encoded to base64, size: {len(image_base64)} chars")

                prompt = """Analyze this image comprehensively and provide a detailed description.

Your description should include:
1. **Main Subject**: What is the primary focus of this image?
2. **Objects & Elements**: List all visible objects, people, or elements
3. **Text Content**: If there's any text visible, transcribe it exactly
4. **Visual Style**: Colors, composition, quality (photo, screenshot, diagram, etc.)
5. **Context Clues**: What does this image appear to be about or used for?
6. **Notable Details**: Any logos, brands, dates, or identifiable information

Provide a comprehensive description (3-5 sentences) that would help someone find this image through a text search. Be specific and detailed."""

                logger.debug(f"Sending image to Ollama model: {self.unified_model}")
                response = await self.client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.unified_model,
                        "prompt": prompt,
                        "images": [image_base64],
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "num_predict": 1500
                        }
                    },
                    timeout=120.0  # Longer timeout for vision models
                )

                response.raise_for_status()
                result = response.json()

                # Validate response
                if 'response' not in result:
                    logger.warning(f"Attempt {attempt + 1}/{max_retries}: No 'response' field in Ollama result")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        break

                summary = result.get('response', '').strip()

                # Check if we got a meaningful response
                if not summary or len(summary) < 10:
                    logger.warning(f"Attempt {attempt + 1}/{max_retries}: Received empty or too short caption: '{summary}'")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        summary = f"Image file: {file_path.name}"

                logger.info(f"Successfully generated image caption for {file_path.name} (length: {len(summary)})")

                # Extract keywords from image description
                keywords = await self._extract_keywords(summary)

                return {
                    "summary": summary,
                    "keywords": keywords,
                    "entities": []
                }

            except httpx.HTTPStatusError as e:
                logger.error(f"Attempt {attempt + 1}/{max_retries}: HTTP error during image captioning: {e.response.status_code}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
            except httpx.TimeoutException:
                logger.error(f"Attempt {attempt + 1}/{max_retries}: Timeout during image captioning")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    continue
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}/{max_retries}: Image captioning failed: {type(e).__name__}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue

        # All retries failed - return fallback
        logger.warning(f"Using fallback description for image: {file_path.name}")
        return {
            "summary": f"Image file: {file_path.name}. Unable to generate detailed description.",
            "keywords": file_path.stem.replace('_', ' ').replace('-', ' '),
            "entities": []
        }

    async def _process_text(self, content: Dict, file_path: Path) -> Dict[str, Any]:
        """Process text document with enhanced summarization"""
        text = content.get('content', '')
        
        # Handle empty or very short content
        if len(text.strip()) < 50:
            return {
                "summary": f"Document: {file_path.name}",
                "keywords": file_path.stem.replace('_', ' ').replace('-', ' '),
                "entities": []
            }
        
        # Truncate for prompt
        max_length = 7000
        truncated = text[:max_length] + ("..." if len(text) > max_length else "")
        
        prompt = f"""You are a document analysis assistant. Analyze this document and provide:

1. **Summary**: A concise 5-7 sentence summary capturing the document's main purpose and key information.

2. **Keywords**: 5-10 important keywords or phrases that would help find this document in a search.

3. **Entities**: Any important names, organizations, dates, locations, or other specific entities mentioned.

---
DOCUMENT CONTENT:
{truncated}
---

Respond in this exact format:
SUMMARY: [Your 5-7 sentence summary]
KEYWORDS: [keyword1, keyword2, keyword3, ...]
ENTITIES: [entity1, entity2, entity3, ...]"""

        try:
            response = await self.client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.unified_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 1000
                    }
                }
            )
            result = response.json()
            response_text = result.get('response', '')
            
            # Parse structured response
            parsed = self._parse_summary_response(response_text)
            
            # Fallback if parsing fails
            if not parsed['summary']:
                parsed['summary'] = text[:500]
            
            return parsed
            
        except Exception as e:
            logger.error(f"Text summarization failed: {e}")
            return {
                "summary": text[:900],
                "keywords": file_path.stem.replace('_', ' ').replace('-', ' '),
                "entities": []
            }

    def _parse_summary_response(self, response: str) -> Dict[str, Any]:
        """Parse the structured summary response"""
        result = {
            "summary": "",
            "keywords": "",
            "entities": []
        }
        
        # Extract summary
        summary_match = re.search(r'SUMMARY:\s*(.+?)(?=KEYWORDS:|ENTITIES:|$)', response, re.DOTALL | re.IGNORECASE)
        if summary_match:
            result['summary'] = summary_match.group(1).strip()
        
        # Extract keywords
        keywords_match = re.search(r'KEYWORDS:\s*(.+?)(?=ENTITIES:|$)', response, re.DOTALL | re.IGNORECASE)
        if keywords_match:
            keywords_text = keywords_match.group(1).strip()
            # Clean up brackets and format
            keywords_text = re.sub(r'[\[\]]', '', keywords_text)
            result['keywords'] = keywords_text
        
        # Extract entities
        entities_match = re.search(r'ENTITIES:\s*(.+?)$', response, re.DOTALL | re.IGNORECASE)
        if entities_match:
            entities_text = entities_match.group(1).strip()
            entities_text = re.sub(r'[\[\]]', '', entities_text)
            entities = [e.strip() for e in entities_text.split(',') if e.strip()]
            result['entities'] = entities[:20]  # Limit to 20 entities
        
        return result

    async def _extract_keywords(self, text: str) -> str:
        """Extract keywords from text using simple NLP"""
        # Simple keyword extraction - remove common words
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'shall', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'what', 'which', 'who', 'when', 'where', 'why', 'how', 'all',
            'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some',
            'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
            'too', 'very', 'just', 'and', 'but', 'if', 'or', 'because', 'as',
            'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against',
            'between', 'into', 'through', 'during', 'before', 'after', 'above',
            'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off',
            'over', 'under', 'again', 'further', 'then', 'once', 'image', 'shows',
            'appears', 'visible', 'contains', 'includes', 'features'
        }
        
        # Extract words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter and count
        word_counts = {}
        for word in words:
            if word not in stop_words:
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Get top keywords
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, _ in sorted_words[:15]]
        
        return ', '.join(keywords)

    async def generate_embedding(self, text: str, max_retries: int = 3) -> List[float]:
        """
        Generate embedding using local sentence-transformers model.
        Much more stable than Ollama - no HTTP calls, no connection issues.
        """
        # Clean and validate input text
        text = text.strip()
        if not text:
            logger.warning("Empty text provided for embedding. Using zero vector.")
            return [0.0] * self.embedding_dimension

        # Truncate to model's max sequence length
        max_chars = 8000  # nomic-embed supports ~8k tokens
        if len(text) > max_chars:
            text = text[:max_chars]

        try:
            # Use lock to prevent concurrent GPU access
            async with self._embedding_lock:
                # Generate embedding locally (runs on GPU if available)
                # Run in thread pool to not block async event loop
                loop = asyncio.get_event_loop()
                embedding = await loop.run_in_executor(
                    None,
                    lambda: self.embedding_model.encode(
                        text,
                        convert_to_numpy=True,
                        normalize_embeddings=True
                    ).tolist()
                )
            
            # Validate dimension
            expected_dim = self.config['models']['embedding']['dimension']
            if len(embedding) != expected_dim:
                logger.warning(f"Embedding dimension mismatch: got {len(embedding)}, expected {expected_dim}")
                if len(embedding) < expected_dim:
                    embedding.extend([0.0] * (expected_dim - len(embedding)))
                else:
                    embedding = embedding[:expected_dim]
            
            return embedding

        except Exception as e:
            logger.error(f"Local embedding generation failed: {type(e).__name__}: {e}")
            return [0.0] * self.embedding_dimension

    async def expand_query(self, query: str) -> List[str]:
        """Expand query with related terms for better recall"""
        prompt = f"""Given this search query, generate 2-3 alternative phrasings or related search terms that might help find relevant documents.

Query: "{query}"

Return only the alternative queries, one per line, without numbering or explanation."""

        try:
            response = await self.client.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.5,
                        "num_predict": 100
                    }
                }
            )
            result = response.json()
            expansions = result.get('response', '').strip().split('\n')
            expansions = [e.strip() for e in expansions if e.strip() and len(e.strip()) > 3]
            return expansions[:3]
        except Exception as e:
            logger.error(f"Query expansion failed: {e}")
            return []

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    async def _index_to_knowledge_graph(
        self, 
        doc_id: str, 
        filename: str, 
        entities: List[str], 
        relationships: List[Dict[str, str]],
        content: str
    ):
        """
        Index entities and relationships into the Knowledge Graph.
        """
        try:
            from backend.graph import KnowledgeGraph
            
            # Get or create global knowledge graph
            if not hasattr(self, '_knowledge_graph'):
                self._knowledge_graph = KnowledgeGraph()
            
            kg = self._knowledge_graph
            
            # Track entity IDs for relationship linking
            entity_id_map = {}
            
            # Add entities
            for entity_name in entities[:20]:  # Limit to 20 entities per doc
                entity_name = entity_name.strip()
                if not entity_name or len(entity_name) < 2:
                    continue
                    
                # Infer entity type from name patterns
                entity_type = self._infer_entity_type(entity_name)
                entity_id = hashlib.md5(f"{entity_name.lower()}_{entity_type}".encode()).hexdigest()[:16]
                entity_id_map[entity_name.lower()] = entity_id
                
                kg.add_entity(
                    entity_id=entity_id,
                    name=entity_name,
                    entity_type=entity_type.upper(),
                    properties={"source_doc": doc_id, "filename": filename},
                    document_id=doc_id
                )
            
            # Add relationships extracted by LLM
            rel_count = 0
            for rel in relationships[:15]:  # Limit relationships
                source_name = rel.get('source', '').lower()
                target_name = rel.get('target', '').lower()
                rel_type = rel.get('type', 'related_to').upper()
                
                # Get or create entity IDs
                source_id = entity_id_map.get(source_name)
                target_id = entity_id_map.get(target_name)
                
                # If either entity wasn't in our list, create them on-demand
                if not source_id:
                    source_id = hashlib.md5(f"{source_name}_concept".encode()).hexdigest()[:16]
                    kg.add_entity(entity_id=source_id, name=rel['source'], entity_type='CONCEPT', document_id=doc_id)
                    entity_id_map[source_name] = source_id
                    
                if not target_id:
                    target_id = hashlib.md5(f"{target_name}_concept".encode()).hexdigest()[:16]
                    kg.add_entity(entity_id=target_id, name=rel['target'], entity_type='CONCEPT', document_id=doc_id)
                    entity_id_map[target_name] = target_id
                
                # Add the relationship edge
                if kg.add_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    relationship_type=rel_type,
                    weight=1.0,
                    document_id=doc_id
                ):
                    rel_count += 1
            
            # Log success
            logger.debug(f"🌐 Indexed {len(entities)} entities, {rel_count} relationships from {filename}")
            
        except Exception as e:
            logger.warning(f"Knowledge graph indexing failed for {filename}: {e}")
    
    def _infer_entity_type(self, entity_name: str) -> str:
        """Infer entity type from name patterns"""
        name_lower = entity_name.lower()
        
        # Organization patterns
        org_suffixes = ['inc', 'corp', 'llc', 'ltd', 'company', 'co', 'group', 'foundation']
        if any(suf in name_lower for suf in org_suffixes):
            return 'organization'
        
        # Location patterns (simple heuristics)
        if any(kw in name_lower for kw in ['city', 'state', 'country', 'street', 'avenue', 'road']):
            return 'location'
        
        # Date patterns
        if any(kw in name_lower for kw in ['january', 'february', 'march', 'april', 'may', 'june',
                                           'july', 'august', 'september', 'october', 'november', 'december']):
            return 'date'
        
        # Monetary patterns
        if '$' in entity_name or '€' in entity_name or any(kw in name_lower for kw in ['dollar', 'euro', 'usd']):
            return 'monetary'
        
        # Person pattern (has space, likely a name)
        parts = entity_name.split()
        if 2 <= len(parts) <= 4 and all(p[0].isupper() for p in parts if p):
            return 'person'
        
        # Default to concept
        return 'concept'