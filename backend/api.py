# backend/api.py - Enhanced FastAPI Server with Conversational Responses

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, AsyncGenerator
import yaml
from pathlib import Path
import asyncio
import sys
import json
import logging # Required for the InterceptHandler base class
from datetime import datetime
import os
import subprocess
import urllib.parse

# --- LOGGING SETUP START ---
from loguru import logger

# Define a handler to route standard logging (Uvicorn) to Loguru
class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )

# Configure Loguru
logger.remove() # Remove default handler
logger.add(
    sys.stderr, 
    level="INFO", 
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
# --- LOGGING SETUP END ---

# Import local modules
from backend.opensearch_client import OpenSearchClient
from backend.ingestion import IngestionPipeline
from backend.reranker import CrossEncoderReranker
from backend.watcher import FileWatcher
from backend.mcp_tools import MCPToolRegistry
from backend.a2a_agent import (
    SearchAgent,
    IngestionAgent,
    ConversationAgent,
    OrchestratorAgent
)

# NEW: Import enhanced agentic components
from backend.memory import MemoryManager
from backend.agents import (
    QueryClassifier,
    ClarificationAgent,
    AnalysisAgent,
    SummarizationAgent,
    ExplanationAgent,
    CriticAgent
)
from backend.orchestration import EnhancedOrchestrator
from backend.streaming_steps import ensure_step_queue, stream_steps
from backend.memory.conversation_manager import ConversationManager
from backend.feedback import get_feedback_store, FeedbackStore
import uuid

# Load Configuration
with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# Initialize FastAPI
app = FastAPI(
    title="LocalLens API",
    description="Semantic Search with Conversational AI",
    version="2.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global components
opensearch_client: Optional[OpenSearchClient] = None
ingestion_pipeline: Optional[IngestionPipeline] = None
reranker: Optional[CrossEncoderReranker] = None
watcher: Optional[FileWatcher] = None
mcp_registry: Optional[MCPToolRegistry] = None
search_agent: Optional[SearchAgent] = None
ingestion_agent: Optional[IngestionAgent] = None
conversation_agent: Optional[ConversationAgent] = None
orchestrator_agent: Optional[OrchestratorAgent] = None

# NEW: Enhanced agentic components
memory_manager: Optional[MemoryManager] = None
enhanced_orchestrator: Optional[EnhancedOrchestrator] = None
query_classifier: Optional[QueryClassifier] = None

# Status tracking for streaming
status_updates: Dict[str, List[Dict]] = {}
ingestion_status: Dict[str, List[Dict]] = {}


# Request/Response Models
class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    use_hybrid: bool = True
    stream_status: bool = True
    # NEW: Session and user tracking for memory
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    attached_documents: Optional[List[str]] = None


class IndexRequest(BaseModel):
    directory: str
    watch_mode: bool = False


class AttachDocumentsRequest(BaseModel):
    document_ids: List[str]


class FeedbackRequest(BaseModel):
    user_id: str
    query: str
    document_id: str
    is_helpful: bool  # True = thumbs up, False = thumbs down


class SearchResponse(BaseModel):
    status: str
    message: str
    query: str
    intent: str
    results: List[Dict[str, Any]]
    count: int
    search_time: float


# Status Streaming
async def status_callback(update: Dict[str, Any]):
    """Callback for status updates from agents"""
    task_id = update.get('task_id', 'default')
    if task_id not in status_updates:
        status_updates[task_id] = []
    status_updates[task_id].append(update)


async def ingestion_status_callback(update: Dict[str, Any]):
    """Callback for ingestion status updates"""
    task_id = update.get('task_id', 'default')
    if task_id not in ingestion_status:
        ingestion_status[task_id] = []
    ingestion_status[task_id].append(update)
    logger.debug(f"Ingestion status update: {update}")


async def stream_status(task_id: str) -> AsyncGenerator[str, None]:
    """Stream status updates as Server-Sent Events"""
    last_index = 0
    timeout = 30  # 30 second timeout
    start_time = asyncio.get_event_loop().time()
    
    while asyncio.get_event_loop().time() - start_time < timeout:
        if task_id in status_updates:
            updates = status_updates[task_id]
            while last_index < len(updates):
                update = updates[last_index]
                yield f"data: {json.dumps(update)}\n\n"
                last_index += 1
                
                # Check if task is complete
                if update.get('status') in ['completed', 'failed']:
                    return
        
        await asyncio.sleep(0.1)
    
    yield f"data: {json.dumps({'status': 'timeout'})}\n\n"


# Helper Functions for Session Management
def get_or_create_session(request_session_id: Optional[str] = None) -> str:
    """Get existing session or create new one"""
    if request_session_id:
        return request_session_id
    return str(uuid.uuid4())[:16]


def get_user_id(request_user_id: Optional[str] = None) -> str:
    """Get user ID from request or use default"""
    return request_user_id or "anonymous"


# Health Check
@app.get("/health")
async def health_check():
    """System health check"""
    try:
        opensearch_status = await opensearch_client.ping() if opensearch_client else False
        memory_status = "available" if memory_manager else "unavailable"
        orchestrator_status = "available" if enhanced_orchestrator else "unavailable"

        return {
            "status": "healthy" if opensearch_status else "degraded",
            "opensearch": "connected" if opensearch_status else "disconnected",
            "text_model": config['ollama']['text_model']['name'],
            "vision_model": config['ollama']['vision_model']['name'],
            "hybrid_search": config['search']['hybrid']['enabled'],
            "memory_system": memory_status,
            "enhanced_orchestrator": orchestrator_status,
            "version": "2.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


# --- NEW: ENHANCED SEARCH WITH MEMORY & AGENTS ---
@app.post("/search/enhanced")
async def enhanced_search(request: SearchRequest):
    """
    Enhanced search with memory, agents, and orchestration

    This intelligent search endpoint uses:
    - Memory for context and learning
    - Agents for specialized tasks
    - Orchestrator for workflow management
    - Quality control and explanations
    """
    import time
    start_time = time.time()

    try:
        # Get or create session
        session_id = get_or_create_session(request.session_id)
        user_id = get_user_id(request.user_id)

        logger.info(f"🔍 Enhanced search: '{request.query}' (user: {user_id}, session: {session_id})")

        # Use orchestrator if available, otherwise fallback to standard search
        if enhanced_orchestrator and memory_manager:
            # Create step queue for real-time streaming
            ensure_step_queue(session_id)
            
            # Handle conversation management
            conversation_id = request.conversation_id

            # Auto-create conversation if not provided and conversation_manager exists
            if not conversation_id and conversation_manager:
                try:
                    conversation_id = await conversation_manager.create_conversation(
                        user_id=user_id,
                        initial_query=request.query
                    )
                except Exception as e:
                    logger.warning(f"Failed to create conversation: {e}")

            # Get attached documents - prioritize request.attached_documents, then conversation
            attached_doc_ids = []
            if request.attached_documents:
                attached_doc_ids = request.attached_documents
                logger.info(f"📎 Using {len(attached_doc_ids)} documents from request")
            elif conversation_id and conversation_manager:
                try:
                    attached_doc_ids = await conversation_manager.get_attached_documents(conversation_id)
                    if attached_doc_ids:
                        logger.info(f"📎 Restricting search to {len(attached_doc_ids)} attached documents")
                except Exception as e:
                    logger.warning(f"Failed to load attached documents: {e}")
            
            # Load conversation history for context
            conversation_history = []
            if conversation_id and conversation_manager:
                try:
                    messages = await conversation_manager.get_messages(conversation_id, limit=12)
                    # Format as simple role/content pairs, exclude the current message
                    conversation_history = [
                        {"role": m["role"], "content": m["content"]}
                        for m in messages
                        if m["content"] and m["content"] != request.query
                    ]
                    if conversation_history:
                        logger.info(f"🧠 Loaded {len(conversation_history)} messages for context")
                except Exception as e:
                    logger.warning(f"Failed to load conversation history: {e}")
            
            # Save user message
            if conversation_id and conversation_manager:
                try:
                    await conversation_manager.add_message(
                        conversation_id=conversation_id,
                        role="user",
                        content=request.query,
                        query=request.query
                    )
                except Exception as e:
                    logger.warning(f"Failed to save user message: {e}")
            
            result = await enhanced_orchestrator.process_query(
                user_id=user_id,
                session_id=session_id,
                query=request.query,
                conversation_id=conversation_id,
                attached_documents=attached_doc_ids,
                conversation_history=conversation_history
            )

            # Add session info to response
            result["session_id"] = session_id
            result["user_id"] = user_id
            result["conversation_id"] = conversation_id
            result["status"] = result.get("status", "success")
            
            # Ensure confidence is always present (calculate from results if not set)
            if "confidence" not in result or result.get("confidence") is None:
                results = result.get("results", [])
                if results:
                    # Calculate confidence from average result score
                    scores = [r.get("score", 0.5) for r in results]
                    avg_score = sum(scores) / len(scores) if scores else 0.5
                    # Scale to 0.5-0.95 range based on result count and scores
                    result_boost = min(len(results) / 10, 0.2)  # Up to 0.2 for 10+ results
                    result["confidence"] = min(0.95, avg_score * 0.7 + result_boost + 0.1)
                else:
                    result["confidence"] = 0.3  # Low confidence with no results
            
            # Save assistant response
            if conversation_id and conversation_manager:
                try:
                    await conversation_manager.add_message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=result.get("response_message", ""),
                        query=request.query,
                        results=result.get("results", []),
                        thinking_steps=result.get("steps", [])
                    )
                except Exception as e:
                    logger.warning(f"Failed to save assistant message: {e}")
            
            # Emit completion signal for SSE stream
            from backend.streaming_steps import emit_step
            emit_step(session_id, {"type": "complete", "results": result.get("results", [])})

            return result

        else:
            # Fallback to original search
            logger.warning("Enhanced features not available, using standard search")
            return await search(request)

    except Exception as e:
        logger.error(f"Enhanced search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- NEW: SSE ENDPOINT FOR REAL-TIME STEP STREAMING ---
@app.get("/search/enhanced/stream/{session_id}")
async def stream_search_steps(session_id: str):
    """
    Stream orchestrator steps in real-time using Server-Sent Events
    
    Connect to this endpoint BEFORE starting a search to see steps as they happen.
    Each step will be sent as a JSON event.
    """
    import json
    
    async def event_generator():
        """Generate SSE events from the step queue"""
        try:
            async for step in stream_steps(session_id, timeout=300):
                # Send step data directly for UI consumption
                if step.get("type") == "step":
                    # Flatten the step data for easy frontend access
                    step_data = {
                        'type': 'step',
                        'agent': step.get('agent', 'Agent'),
                        'action': step.get('action', ''),
                        'details': step.get('details', ''),
                        'timestamp': step.get('timestamp', '')
                    }
                    yield f"data: {json.dumps(step_data)}\n\n"
                elif step.get("type") == "complete":
                    yield f"data: {json.dumps({'type': 'complete', 'message': 'Search complete'})}\n\n"
                elif step.get("type") == "error":
                    yield f"data: {json.dumps({'type': 'error', 'message': step.get('message')})}\n\n"
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


# --- EXISTING SEARCH ENDPOINT ---
@app.post("/search")
async def search(request: SearchRequest):
    """
    Enhanced semantic search with:
    - Conversational responses
    - Intent detection
    - Hybrid search (Vector + BM25)
    - Query expansion
    """
    import time
    start_time = time.time()
    
    try:
        logger.info(f"🔍 Search query: {request.query}")
        
        # 1. Intent Detection & Filter Building
        filters, intent, intent_desc = await _detect_intent(request.query)
        
        # 2. Generate query embedding
        query_embedding = await ingestion_pipeline.generate_embedding(request.query)
        
        # 3. Perform search (hybrid or vector-only)
        recall_top_k = config['search']['recall_top_k']
        
        if request.use_hybrid and config['search']['hybrid']['enabled']:
            logger.info("📚 Using hybrid search (Vector + BM25)")
            candidates = await opensearch_client.hybrid_search(
                query=request.query,
                query_vector=query_embedding,
                top_k=recall_top_k,
                filters=filters
            )
        else:
            candidates = await opensearch_client.vector_search(
                query_embedding,
                top_k=recall_top_k,
                filters=filters
            )
        
        logger.info(f"Retrieved {len(candidates)} candidates")
        
        # 4. Cross-encoder reranking
        if candidates:
            reranked = await reranker.rerank(
                query=request.query,
                documents=candidates,
                top_k=request.top_k
            )
            
            # 5. Generate conversational response
            response_message = _generate_response_message(
                query=request.query,
                results=reranked,
                intent=intent,
                intent_desc=intent_desc
            )
            
            search_time = time.time() - start_time
            
            return {
                "status": "success",
                "message": response_message,
                "query": request.query,
                "intent": intent,
                "results": reranked,
                "count": len(reranked),
                "search_time": round(search_time, 3)
            }
        else:
            search_time = time.time() - start_time
            
            return {
                "status": "success",
                "message": f"😕 I couldn't find any documents matching '{request.query}'. Try different keywords or check if documents are indexed.",
                "query": request.query,
                "intent": intent,
                "results": [],
                "count": 0,
                "search_time": round(search_time, 3)
            }
            
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _detect_intent(query: str) -> tuple:
    """
    Enhanced intent detection with more categories
    Returns: (filters, intent_type, intent_description)
    """
    q_lower = query.lower()
    
    # File type categories
    IMAGE_EXTS = [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"]
    DOC_EXTS = [".pdf", ".docx", ".doc", ".txt", ".md"]
    SPREADSHEET_EXTS = [".xlsx", ".xls", ".csv"]
    
    # Document type keywords
    INTENT_PATTERNS = {
        "image": {
            "keywords": ["image", "photo", "picture", "pic", "screenshot", "diagram", 
                        "chart", "graph", "visual", "logo", "drawing"],
            "filter": {"terms": {"file_type": IMAGE_EXTS}},
            "desc": "images and visual content"
        },
        "document": {
            "keywords": ["document", "doc", "pdf", "file", "report", "article", 
                        "paper", "memo", "letter", "contract"],
            "filter": {"terms": {"file_type": DOC_EXTS}},
            "desc": "documents and text files"
        },
        "spreadsheet": {
            "keywords": ["spreadsheet", "excel", "csv", "table", "data", "sheet", 
                        "budget", "financial", "numbers"],
            "filter": {"terms": {"file_type": SPREADSHEET_EXTS}},
            "desc": "spreadsheets and data files"
        },
        "invoice": {
            "keywords": ["invoice", "bill", "receipt", "payment", "purchase"],
            "filter": {"term": {"document_type": "invoice"}},
            "desc": "invoices and receipts"
        },
        "report": {
            "keywords": ["report", "summary", "analysis", "review", "assessment"],
            "filter": {"term": {"document_type": "report"}},
            "desc": "reports and analyses"
        },
        "contract": {
            "keywords": ["contract", "agreement", "legal", "terms", "nda"],
            "filter": {"term": {"document_type": "contract"}},
            "desc": "contracts and agreements"
        }
    }
    
    # Check each intent pattern
    for intent_type, pattern in INTENT_PATTERNS.items():
        if any(kw in q_lower for kw in pattern["keywords"]):
            logger.info(f"🎯 Intent Detected: {intent_type.upper()}")
            return pattern["filter"], intent_type, pattern["desc"]
    
    # No specific intent - general search
    return None, "general", "all documents"


def _generate_response_message(
    query: str,
    results: List[Dict],
    intent: str,
    intent_desc: str
) -> str:
    """Generate a natural, conversational response message with personality"""

    count = len(results)

    if count == 0:
        # More empathetic no-results messages
        no_result_messages = [
            f"I've searched through all your {intent_desc}, but I couldn't find anything that matches '{query}'. Would you like to try different keywords?",
            f"Hmm, I didn't find any {intent_desc} related to '{query}'. Maybe try rephrasing your search?",
            f"I looked everywhere in your {intent_desc}, but nothing matched '{query}'. Let's try a broader search term!"
        ]
        import random
        return random.choice(no_result_messages)

    # Extract key topic from query
    topic = _extract_topic(query)

    # Build response based on count and intent - more conversational
    if count == 1:
        return f"Perfect! I found exactly what you're looking for - 1 document about **{topic}**:"
    elif count == 2:
        return f"Great! I found 2 documents that match your query about **{topic}**. Let me show you both:"
    elif count <= 5:
        return f"Nice! I discovered {count} relevant documents about **{topic}**. Here they are, ranked by relevance:"
    else:
        top_doc = results[0]['filename']
        return f"Excellent! I found {count} documents matching your search. The best match appears to be **{top_doc}**. Here are the top results:"


def _extract_topic(query: str) -> str:
    """Extract main topic from query for response"""
    stop_words = {
        'find', 'search', 'show', 'get', 'the', 'a', 'an', 'my', 'about', 
        'for', 'with', 'where', 'is', 'are', 'all', 'any', 'please', 'can',
        'you', 'me', 'i', 'want', 'need', 'looking', 'help', 'documents',
        'files', 'document', 'file'
    }
    
    words = query.lower().split()
    topic_words = [w for w in words if w not in stop_words and len(w) > 2]
    
    if topic_words:
        return ' '.join(topic_words[:4])
    return query


# Streaming Search Endpoint
@app.post("/search/stream")
async def search_stream(request: SearchRequest):
    """
    Search with streaming status updates.
    Returns Server-Sent Events for real-time status.
    """
    task_id = f"search_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    status_updates[task_id] = []
    
    # Start search in background
    asyncio.create_task(_perform_search_with_status(request, task_id))
    
    return StreamingResponse(
        stream_status(task_id),
        media_type="text/event-stream"
    )


async def _perform_search_with_status(request: SearchRequest, task_id: str):
    """Perform search with detailed thinking steps and status updates"""
    try:
        # Step 1: Understanding the query
        status_updates[task_id].append({
            "step": "analyzing",
            "message": "🤔 Let me understand what you're looking for...",
            "progress": 0.05,
            "thinking": "Analyzing query structure and intent"
        })
        await asyncio.sleep(0.2)

        # Step 2: Detect intent
        filters, intent, intent_desc = await _detect_intent(request.query)

        status_updates[task_id].append({
            "step": "intent",
            "message": f"🎯 I see you're looking for {intent_desc}",
            "intent": intent,
            "progress": 0.15,
            "thinking": f"Detected search intent: {intent}"
        })
        await asyncio.sleep(0.2)

        # Step 3: Generate semantic embedding
        status_updates[task_id].append({
            "step": "embedding",
            "message": "🧠 Converting your query into semantic vectors...",
            "progress": 0.25,
            "thinking": "Generating embeddings using nomic-embed-text model"
        })

        query_embedding = await ingestion_pipeline.generate_embedding(request.query)

        status_updates[task_id].append({
            "step": "embedding_done",
            "message": "✓ Query encoded into 768-dimensional vector space",
            "progress": 0.35,
            "thinking": "Embedding generated successfully"
        })
        await asyncio.sleep(0.2)

        # Step 4: Hybrid Search
        status_updates[task_id].append({
            "step": "searching",
            "message": "📚 Searching with hybrid vector + keyword matching...",
            "progress": 0.45,
            "thinking": "Combining semantic similarity and BM25 keyword search"
        })

        candidates = await opensearch_client.hybrid_search(
            query=request.query,
            query_vector=query_embedding,
            top_k=config['search']['recall_top_k'],
            filters=filters
        )

        status_updates[task_id].append({
            "step": "search_done",
            "message": f"✓ Found {len(candidates)} potential matches",
            "progress": 0.60,
            "thinking": f"Retrieved {len(candidates)} candidates from index"
        })
        await asyncio.sleep(0.2)

        # Step 5: Reranking with cross-encoder
        if candidates:
            status_updates[task_id].append({
                "step": "reranking",
                "message": f"⚡ Re-ranking {len(candidates)} results with AI...",
                "progress": 0.75,
                "thinking": "Using cross-encoder model for precise relevance scoring"
            })

            reranked = await reranker.rerank(
                query=request.query,
                documents=candidates,
                top_k=request.top_k
            )

            status_updates[task_id].append({
                "step": "rerank_done",
                "message": f"✓ Ranked top {len(reranked)} most relevant results",
                "progress": 0.90,
                "thinking": f"Reranking complete, top score: {reranked[0]['score']:.3f}"
            })
        else:
            reranked = []

        await asyncio.sleep(0.1)

        # Complete
        response_message = _generate_response_message(
            request.query, reranked, intent, intent_desc
        )
        
        status_updates[task_id].append({
            "step": "completed",
            "message": response_message,
            "status": "completed",
            "results": reranked,
            "count": len(reranked),
            "intent": intent,
            "progress": 1.0
        })
        
    except Exception as e:
        status_updates[task_id].append({
            "step": "error",
            "message": f"❌ Search failed: {str(e)}",
            "status": "failed",
            "error": str(e)
        })


# Indexing Endpoint
@app.post("/index")
async def start_indexing(request: IndexRequest, background_tasks: BackgroundTasks):
    """Start indexing a directory with status feedback"""
    try:
        directory = Path(request.directory)
        if not directory.exists():
            raise HTTPException(status_code=404, detail="Directory not found")

        task_id = f"index_{directory.name}_{int(asyncio.get_event_loop().time())}"

        # Initialize ingestion status for this task
        ingestion_status[task_id] = []

        # Start ingestion in background
        background_tasks.add_task(
            ingestion_pipeline.process_directory,
            directory,
            task_id
        )

        # Start file watcher if requested
        if request.watch_mode:
            global watcher
            watcher = FileWatcher(config, ingestion_pipeline, opensearch_client)
            background_tasks.add_task(watcher.start, directory)

        return {
            "status": "success",
            "message": f"📂 Starting to index {directory.name}. This may take a moment...",
            "task_id": task_id,
            "directory": str(directory),
            "watch_mode": request.watch_mode
        }
    except Exception as e:
        logger.error(f"Indexing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Ingestion Status Stream Endpoint
@app.get("/ingestion/status/{task_id}")
async def stream_ingestion_status(task_id: str):
    """Stream real-time ingestion status updates"""
    async def event_stream():
        last_index = 0
        timeout = 300  # 5 minute timeout
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            if task_id in ingestion_status:
                updates = ingestion_status[task_id]
                while last_index < len(updates):
                    update = updates[last_index]
                    yield f"data: {json.dumps(update)}\n\n"
                    last_index += 1

                    # Check if task is complete
                    if update.get('status') == 'completed':
                        yield f"data: {json.dumps({'status': 'done'})}\n\n"
                        return

            await asyncio.sleep(0.5)

        yield f"data: {json.dumps({'status': 'timeout'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# Get current ingestion status (polling fallback)
@app.get("/ingestion/status")
async def get_ingestion_status():
    """Get current ingestion status for all active tasks"""
    active_tasks = {}
    for task_id, updates in ingestion_status.items():
        if updates:
            latest = updates[-1]
            if latest.get('status') != 'completed':
                active_tasks[task_id] = latest

    return {
        "status": "success",
        "active_tasks": active_tasks,
        "count": len(active_tasks)
    }


# Statistics Endpoint
@app.get("/stats")
async def get_statistics():
    """Get system statistics"""
    try:
        stats = await opensearch_client.get_stats() if opensearch_client else {}
        return {
            "status": "success",
            "total_documents": stats.get("count", 0),
            "total_vectors": stats.get("count", 0),
            "watcher_active": 1 if watcher and watcher.is_running else 0,
            "hybrid_search_enabled": config['search']['hybrid']['enabled'],
            "avg_search_time": 0.15
        }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {"status": "error", "message": str(e), "total_documents": 0}


# Cluster Visualization Endpoint
@app.get("/clusters")
async def get_clusters():
    """Get semantic clusters for visualization"""
    try:
        cluster_data = await opensearch_client.get_cluster_data()
        if not cluster_data:
            return {}
        return {"status": "success", **cluster_data}
    except Exception as e:
        logger.error(f"Cluster error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- HUMAN FEEDBACK LEARNING ENDPOINTS ---

@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """
    Submit user feedback on a search result.
    
    This enables RLHF-style learning:
    - Per-user feedback (only affects your own results)
    - 1-month time decay (older feedback matters less)
    - Used to boost/penalize documents in future searches
    """
    try:
        feedback_store = get_feedback_store()
        success = feedback_store.add_feedback(
            user_id=request.user_id,
            query=request.query,
            document_id=request.document_id,
            is_helpful=request.is_helpful
        )
        
        if success:
            feedback_type = "helpful" if request.is_helpful else "not helpful"
            logger.info(f"👍 Feedback recorded: user={request.user_id}, doc={request.document_id[:8]}, {feedback_type}")
            return {
                "status": "success",
                "message": f"Thanks for your feedback! Marked as {feedback_type}.",
                "feedback_type": feedback_type
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save feedback")
            
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/feedback/stats/{user_id}")
async def get_feedback_stats(user_id: str):
    """Get feedback statistics for a user"""
    try:
        feedback_store = get_feedback_store()
        stats = feedback_store.get_user_feedback_stats(user_id)
        return {
            "status": "success",
            "user_id": user_id,
            **stats
        }
    except Exception as e:
        logger.error(f"Feedback stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/feedback/document/{user_id}/{document_id}")
async def get_document_feedback(user_id: str, document_id: str):
    """Get user's feedback for a specific document"""
    try:
        feedback_store = get_feedback_store()
        feedback = feedback_store.get_document_feedback(user_id, document_id)
        return {
            "status": "success",
            "user_id": user_id,
            "document_id": document_id,
            "feedback": feedback  # 1 (helpful), -1 (not helpful), or None
        }
    except Exception as e:
        logger.error(f"Document feedback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- NEW: MEMORY SYSTEM ENDPOINTS ---

@app.get("/memory/summary")
async def get_memory_summary(user_id: str, session_id: str):
    """Get user memory summary"""
    if not memory_manager:
        raise HTTPException(status_code=503, detail="Memory system not available")

    try:
        summary = await memory_manager.get_memory_summary(
            user_id=user_id,
            session_id=session_id
        )
        return {"status": "success", "summary": summary}

    except Exception as e:
        logger.error(f"Memory summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/preferences")
async def get_user_preferences(user_id: str):
    """Get personalized user preferences"""
    if not memory_manager:
        raise HTTPException(status_code=503, detail="Memory system not available")

    try:
        prefs = await memory_manager.get_user_preferences(user_id)
        return {"status": "success", "preferences": prefs}

    except Exception as e:
        logger.error(f"Preferences error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/memory/session/{session_id}")
async def clear_session(session_id: str):
    """Clear a specific session"""
    if not memory_manager:
        raise HTTPException(status_code=503, detail="Memory system not available")

    try:
        await memory_manager.session_memory.clear_session(session_id)
        return {"status": "success", "message": f"Session {session_id} cleared"}

    except Exception as e:
        logger.error(f"Session clear error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- NEW: KNOWLEDGE GRAPH ENDPOINTS ---

class GraphQueryRequest(BaseModel):
    entity_name: str
    entity_type: Optional[str] = None
    hops: int = 2


@app.get("/graph/stats")
async def get_graph_stats():
    """Get knowledge graph statistics"""
    try:
        if enhanced_orchestrator and enhanced_orchestrator.knowledge_graph:
            stats = enhanced_orchestrator.knowledge_graph.get_stats()
            return {"status": "success", **stats}
        return {"status": "unavailable", "message": "Knowledge graph not initialized"}
    except Exception as e:
        logger.error(f"Graph stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/entities")
async def search_entities(name: str, limit: int = 10):
    """Search for entities by name"""
    try:
        if not enhanced_orchestrator or not enhanced_orchestrator.knowledge_graph:
            raise HTTPException(status_code=503, detail="Knowledge graph not available")
        
        entities = enhanced_orchestrator.knowledge_graph.find_entities_by_name(name)
        result = [e.to_dict() for e in entities[:limit]]
        return {"status": "success", "entities": result, "count": len(result)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Entity search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/graph/expand")
async def expand_entity(request: GraphQueryRequest):
    """Get related entities via graph traversal"""
    try:
        if not enhanced_orchestrator or not enhanced_orchestrator.graph_rag:
            raise HTTPException(status_code=503, detail="Graph RAG not available")
        
        expansion = await enhanced_orchestrator.graph_rag.expand_query(
            query=request.entity_name,
            extracted_entities=[request.entity_name],
            max_hops=request.hops
        )
        
        return {
            "status": "success",
            "original": expansion.original_entities,
            "expanded": expansion.expanded_entities,
            "related_documents": expansion.related_documents[:10],
            "path": expansion.expansion_path
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Graph expansion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/entity/{entity_id}/context")
async def get_entity_context(entity_id: str):
    """Get full context for an entity including relationships"""
    try:
        if not enhanced_orchestrator or not enhanced_orchestrator.knowledge_graph:
            raise HTTPException(status_code=503, detail="Knowledge graph not available")
        
        context = enhanced_orchestrator.knowledge_graph.get_entity_context(entity_id)
        return {"status": "success", **context}
    except Exception as e:
        logger.error(f"Entity context error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- NEW: EPISODIC MEMORY ENDPOINTS ---

@app.get("/memory/episodes/{user_id}")
async def get_user_episodes(user_id: str, limit: int = 20):
    """Get recent interaction episodes for a user"""
    try:
        if not enhanced_orchestrator or not enhanced_orchestrator.episodic_memory:
            raise HTTPException(status_code=503, detail="Episodic memory not available")
        
        episodes = enhanced_orchestrator.episodic_memory.get_user_episodes(user_id, limit)
        return {
            "status": "success",
            "episodes": [e.to_dict() for e in episodes],
            "count": len(episodes)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Episodes fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/episodes/{user_id}/summary")
async def get_episode_summary(user_id: str, days: int = 30):
    """Get summary of user's interaction episodes"""
    try:
        if not enhanced_orchestrator or not enhanced_orchestrator.episodic_memory:
            raise HTTPException(status_code=503, detail="Episodic memory not available")
        
        from dataclasses import asdict
        summary = enhanced_orchestrator.episodic_memory.summarize_episodes(user_id, days)
        return {"status": "success", **asdict(summary)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Episode summary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- NEW: CONFIDENCE SCORING ENDPOINT ---

class ConfidenceRequest(BaseModel):
    answer: str
    query: str
    source_ids: List[str] = []


@app.post("/analyze/confidence")
async def score_confidence(request: ConfidenceRequest):
    """Get confidence score for an answer with evidence assessment"""
    try:
        if not enhanced_orchestrator or not enhanced_orchestrator.confidence_scorer:
            raise HTTPException(status_code=503, detail="Confidence scorer not available")
        
        # Fetch source documents if IDs provided
        sources = []
        if request.source_ids and opensearch_client:
            for doc_id in request.source_ids[:5]:
                try:
                    doc = await opensearch_client.get_document(doc_id)
                    if doc:
                        sources.append(doc)
                except Exception:
                    pass
        
        from dataclasses import asdict
        response = await enhanced_orchestrator.confidence_scorer.create_confidence_aware_response(
            answer=request.answer,
            query=request.query,
            sources=sources
        )
        
        return {
            "status": "success",
            "confidence": response.confidence,
            "evidence_strength": asdict(response.evidence_strength),
            "alternatives": response.alternative_interpretations,
            "followups": response.suggested_followups,
            "uncertainty_reasons": response.uncertainty_reasons
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Confidence scoring error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- NEW: ADAPTIVE RETRIEVAL STRATEGY ENDPOINT ---

@app.post("/search/strategy")
async def get_retrieval_strategy(query: str):
    """Get recommended retrieval strategy for a query"""
    try:
        if not enhanced_orchestrator or not enhanced_orchestrator.adaptive_retriever:
            raise HTTPException(status_code=503, detail="Adaptive retriever not available")
        
        decision = enhanced_orchestrator.adaptive_retriever.classify_strategy(query)
        
        return {
            "status": "success",
            "query": query,
            "primary_strategy": decision.primary_strategy.value,
            "secondary_strategy": decision.secondary_strategy.value if decision.secondary_strategy else None,
            "confidence": decision.confidence,
            "reasoning": decision.reasoning,
            "weights": decision.weights
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Strategy classification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))




@app.get("/documents/{document_id}/preview")
async def preview_document(document_id: str, max_length: int = 500):
    """Preview document content by ID"""
    if not opensearch_client:
        raise HTTPException(status_code=503, detail="Search not available")
    
    try:
        # Get document from OpenSearch
        from opensearchpy import OpenSearch
        
        response = await opensearch_client.client.get(
            index=opensearch_client.index_name,
            id=document_id
        )
        
        if not response or 'found' not in response or not response['found']:
            raise HTTPException(status_code=404, detail="Document not found")
        
        doc = response['_source']
        
        # Extract preview
        content_preview = (doc.get('detailed_summary', '') or doc.get('content_summary', '') or doc.get('text', ''))[:max_length]
        
        return {
            "status": "success",
            "document": {
                "id": document_id,
                "filename": doc.get('filename'),
                "file_type": doc.get('file_type'),
                "content_preview": content_preview,
                "created_at": doc.get('created_at'),
                "file_path": doc.get('file_path')
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document preview error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/{document_id}/entities")
async def get_document_entities(document_id: str):
    """Get entities, keywords, and topics for a document (for knowledge graph display)"""
    if not opensearch_client:
        raise HTTPException(status_code=503, detail="Search not available")
    
    try:
        response = await opensearch_client.client.get(
            index=opensearch_client.index_name,
            id=document_id
        )
        
        if not response or 'found' not in response or not response['found']:
            raise HTTPException(status_code=404, detail="Document not found")
        
        doc = response['_source']
        
        # Extract entity-related data
        entities = doc.get('entities', [])
        keywords = doc.get('keywords', '')
        topics = doc.get('topics', [])
        
        # Parse keywords into list if string
        if isinstance(keywords, str):
            keywords_list = [k.strip() for k in keywords.split(',') if k.strip()]
        else:
            keywords_list = keywords or []
        
        # Build graph data structure for visualization
        nodes = []
        edges = []
        
        # Document as central node
        nodes.append({
            "id": "doc",
            "label": doc.get('filename', 'Document'),
            "type": "document",
            "size": 30
        })
        
        # Add entity nodes
        for i, entity in enumerate(entities[:20]):  # Limit to 20 entities
            entity_name = entity if isinstance(entity, str) else entity.get('name', str(entity))
            nodes.append({
                "id": f"e{i}",
                "label": entity_name,
                "type": "entity",
                "size": 15
            })
            edges.append({
                "source": "doc",
                "target": f"e{i}",
                "type": "contains"
            })
        
        # Add keyword nodes
        for i, keyword in enumerate(keywords_list[:15]):  # Limit to 15 keywords
            nodes.append({
                "id": f"k{i}",
                "label": keyword,
                "type": "keyword",
                "size": 10
            })
            edges.append({
                "source": "doc",
                "target": f"k{i}",
                "type": "keyword"
            })
        
        # Add topic nodes
        for i, topic in enumerate(topics[:10]):  # Limit to 10 topics
            nodes.append({
                "id": f"t{i}",
                "label": topic,
                "type": "topic",
                "size": 12
            })
            edges.append({
                "source": "doc",
                "target": f"t{i}",
                "type": "topic"
            })
        
        return {
            "status": "success",
            "document_id": document_id,
            "filename": doc.get('filename'),
            "entities": entities,
            "keywords": keywords_list,
            "topics": topics,
            "graph": {
                "nodes": nodes,
                "edges": edges
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document entities error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- NEW: SPECIALIZED AGENT ENDPOINTS ---

@app.post("/analyze/compare")
async def compare_documents(doc_ids: List[str]):
    """Compare multiple documents"""
    try:
        # Fetch documents by IDs
        documents = []
        for doc_id in doc_ids:
            # Simple retrieval - in production, add proper document lookup
            # For now, we'll need to search or have a get_by_id method
            pass

        if len(documents) < 2:
            raise HTTPException(status_code=400, detail="Need at least 2 documents to compare")

        # Use analysis agent
        from backend.agents import AnalysisAgent
        analysis_agent = AnalysisAgent(config)

        comparison = await analysis_agent.compare_documents(documents)

        return {
            "status": "success",
            "comparison": comparison,
            "document_count": len(documents)
        }

    except Exception as e:
        logger.error(f"Comparison error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/summarize")
async def summarize_multiple(doc_ids: List[str], summary_type: str = "comprehensive"):
    """Summarize multiple documents"""
    try:
        # Fetch documents (implementation depends on your document storage)
        documents = []
        # Add document retrieval logic here

        if not documents:
            raise HTTPException(status_code=404, detail="No documents found")

        # Use summarization agent
        from backend.agents import SummarizationAgent
        summarization_agent = SummarizationAgent(config)

        summary = await summarization_agent.summarize_documents(
            documents=documents,
            summary_type=summary_type
        )

        return {
            "status": "success",
            "summary": summary,
            "document_count": len(documents),
            "summary_type": summary_type
        }

    except Exception as e:
        logger.error(f"Summarization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# A2A Message Endpoint
@app.post("/a2a/message")
async def handle_a2a_message(message: Dict[str, Any]):
    """Handle incoming A2A messages"""
    try:
        recipient = message.get('recipient', 'orchestrator')
        
        agent_map = {
            'orchestrator': orchestrator_agent,
            'search': search_agent,
            'ingestion': ingestion_agent,
            'conversation': conversation_agent
        }
        
        agent = agent_map.get(recipient)
        if agent:
            return await agent.handle_message(message)
        else:
            return {"error": f"Unknown recipient: {recipient}"}
            
    except Exception as e:
        logger.error(f"A2A message error: {e}")
        return {"error": str(e)}


# --- CONVERSATION MANAGEMENT ENDPOINTS ---

@app.post("/conversations")
async def create_conversation(user_id: str, title: str = None, initial_query: str = None):
    """Create a new conversation"""
    if not conversation_manager:
        raise HTTPException(status_code=503, detail="Conversation manager not available")
    
    try:
        conversation_id = await conversation_manager.create_conversation(
            user_id=user_id,
            title=title,
            initial_query=initial_query
        )
        return {"status": "success", "conversation_id": conversation_id}
    except Exception as e:
        logger.error(f"Create conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations")
async def list_conversations(user_id: str, limit: int = 50, offset: int = 0):
    """List conversations for a user, grouped by date"""
    if not conversation_manager:
        raise HTTPException(status_code=503, detail="Conversation manager not available")
    
    try:
        conversations = await conversation_manager.list_conversations(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        return {"status": "success", "conversations":conversations}
    except Exception as e:
        logger.error(f"List conversations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation details"""
    if not conversation_manager:
        raise HTTPException(status_code=503, detail="Conversation manager not available")
    
    try:
        conversation = await conversation_manager.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return {"status": "success", "conversation": conversation}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/conversations/{conversation_id}")
async def update_conversation(conversation_id: str, title: str = None, is_pinned: bool = None):
    """Update conversation metadata"""
    if not conversation_manager:
        raise HTTPException(status_code=503, detail="Conversation manager not available")
    
    try:
        await conversation_manager.update_conversation(
            conversation_id=conversation_id,
            title=title,
            is_pinned=is_pinned
        )
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Update conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    if not conversation_manager:
        raise HTTPException(status_code=503, detail="Conversation manager not available")
    
    try:
        await conversation_manager.delete_conversation(conversation_id)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Delete conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str, limit: int = 100, offset: int = 0):
    """Get messages for a conversation"""
    if not conversation_manager:
        raise HTTPException(status_code=503, detail="Conversation manager not available")
    
    try:
        messages = await conversation_manager.get_messages(
            conversation_id=conversation_id,
            limit=limit,
            offset=offset
        )
        return {"status": "success", "messages": messages}
    except Exception as e:
        logger.error(f"Get messages error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/conversations/{conversation_id}/documents")
async def attach_documents(conversation_id: str, request: AttachDocumentsRequest):
    """Attach documents to a conversation"""
    if not conversation_manager:
        raise HTTPException(status_code=503, detail="Conversation manager not available")

    try:
        await conversation_manager.attach_documents(conversation_id, request.document_ids)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Attach documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations/{conversation_id}/documents")
async def get_attached_documents(conversation_id: str):
    """Get documents attached to a conversation"""
    if not conversation_manager:
        raise HTTPException(status_code=503, detail="Conversation manager not available")
    
    try:
        doc_ids = await conversation_manager.get_attached_documents(conversation_id)
        return {"status": "success", "document_ids": doc_ids}
    except Exception as e:
        logger.error(f"Get attached documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/conversations/{conversation_id}/documents/{document_id}")
async def detach_document(conversation_id: str, document_id: str):
    """Detach a document from a conversation"""
    if not conversation_manager:
        raise HTTPException(status_code=503, detail="Conversation manager not available")
    
    try:
        await conversation_manager.detach_document(conversation_id, document_id)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Detach document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# MCP Tool Endpoint
@app.post("/mcp/tools/{tool_name}")
async def execute_mcp_tool(tool_name: str, params: Dict[str, Any]):
    """Execute MCP tool"""
    try:
        result = await mcp_registry.execute(tool_name, params)
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"MCP tool error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Startup Event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup with enhanced agentic features"""
    
    # --- LOGURU INTERCEPT CONFIGURATION ---
    # Redirect Uvicorn logs to Loguru
    logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
    logging.getLogger("uvicorn.error").handlers = [InterceptHandler()]
    
    # Optional: Configure the level to show in logs
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    # --------------------------------------

    global opensearch_client, ingestion_pipeline, reranker
    global mcp_registry, search_agent, ingestion_agent
    global conversation_agent, orchestrator_agent
    global memory_manager, enhanced_orchestrator, query_classifier, conversation_manager

    logger.info("🚀 Starting LocalLens API v2.0 with Agentic Features...")

    # === EXISTING COMPONENTS ===
    opensearch_client = OpenSearchClient(config)
    ingestion_pipeline = IngestionPipeline(config, opensearch_client, ingestion_status_callback)
    reranker = CrossEncoderReranker(config)
    mcp_registry = MCPToolRegistry()

    # Initialize existing agents
    search_agent = SearchAgent(config)
    ingestion_agent = IngestionAgent(config)
    conversation_agent = ConversationAgent(config)
    orchestrator_agent = OrchestratorAgent(config)

    # Initialize OpenSearch index
    await opensearch_client.create_index()

    # === NEW: ENHANCED COMPONENTS ===
    logger.info("Initializing enhanced memory and agent systems...")

    # 1. Initialize Memory Manager
    try:
        memory_config = config.get("memory", {})
        memory_manager = MemoryManager(
            redis_url=memory_config.get("session", {}).get("redis_url", "redis://localhost:6379"),
            database_url=memory_config.get("user_profile", {}).get("database_url", "sqlite+aiosqlite:///locallens_memory.db")
        )
        await memory_manager.initialize()
        logger.info("✅ Memory Manager initialized")
    except Exception as e:
        logger.warning(f"Memory Manager initialization failed: {e}. Continuing without memory features.")
        memory_manager = None

    # 2. Initialize Conversation Manager
    try:
        conversation_manager = ConversationManager("locallens_conversations.db")
        await conversation_manager.initialize()
        logger.info("✅ Conversation Manager initialized")
    except Exception as e:
        logger.warning(f"Conversation Manager initialization failed: {e}. Continuing without conversation history.")
        conversation_manager = None

    # 3. Initialize Query Classifier
    query_classifier = QueryClassifier(config)
    logger.info("✅ Query Classifier initialized")

    # 3. Create search function wrapper for orchestrator
    async def search_function(query: str, filters: Optional[Dict] = None, weights: Optional[Dict] = None, attached_documents: Optional[List[str]] = None, user_id: Optional[str] = None):
        """Wrapper function for search to pass to orchestrator"""
        try:
            # If conversation has attached documents, filter by them
            if attached_documents and len(attached_documents) > 0:
                doc_filter = {"terms": {"_id": attached_documents}}
                if filters:
                    # Combine filters
                    filters = {"bool": {"must": [filters, doc_filter]}}
                else:
                    filters = doc_filter
                logger.info(f"Filtering search to {len(attached_documents)} document(s)")
            
            # Generate embedding
            query_embedding = await ingestion_pipeline.generate_embedding(query)

            # Perform hybrid search
            candidates = await opensearch_client.hybrid_search(
                query=query,
                query_vector=query_embedding,
                top_k=config['search']['recall_top_k'],
                filters=filters
            )

            # Rerank with user feedback boosts
            if candidates and len(candidates) > 0:
                results = await reranker.rerank(
                    query=query,
                    documents=candidates,
                    top_k=config['search']['rerank_top_k'],
                    user_id=user_id  # Pass user_id for feedback-based score adjustments
                )
                return results if results else []
            
            return []
        
        except Exception as e:
            logger.error(f"Search function error: {e}")
            return []  # Always return empty list on error, never None

    # 4. Initialize Enhanced Orchestrator
    if memory_manager:
        try:
            enhanced_orchestrator = EnhancedOrchestrator(
                config=config,
                memory_manager=memory_manager,
                search_function=search_function,
                opensearch_client=opensearch_client
            )
            logger.info("✅ Enhanced Orchestrator initialized with LangGraph")
        except Exception as e:
            logger.warning(f"Orchestrator initialization failed: {e}")
            enhanced_orchestrator = None

    # Register MCP tools (existing)
    mcp_registry.register_tool("search_documents", search)
    mcp_registry.register_tool("index_directory", start_indexing)

    logger.info("✅ LocalLens API ready with enhanced agentic features!")


# Shutdown Event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down LocalLens API...")

    if watcher:
        watcher.stop()
    if opensearch_client:
        await opensearch_client.close()
    if ingestion_pipeline:
        await ingestion_pipeline.close()

    # Close agents
    for agent in [search_agent, ingestion_agent, conversation_agent, orchestrator_agent]:
        if agent:
            await agent.close()

    # NEW: Close memory manager
    if memory_manager:
        await memory_manager.close()
        logger.info("Memory Manager closed")

    logger.info("LocalLens API stopped")


if __name__ == "__main__":
    import uvicorn
    # Use standard logging config for uvicorn, but our InterceptHandler will catch it
    uvicorn.run(app, host="0.0.0.0", port=8000)# Add this to backend/api.py - Indexing endpoint

from fastapi import BackgroundTasks
from pathlib import Path

# Add after other endpoints (around line 1300)

@app.post("/index/directory")
async def index_directory(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Index a directory of documents
    
    Request body:
    {
        "directory_path": "/path/to/documents",
        "recursive": true
    }
    """
    try:
        directory_path = request.get("directory_path")
        recursive = request.get("recursive", True)
        
        if not directory_path:
            raise HTTPException(status_code=400, detail="directory_path is required")
        
        path = Path(directory_path)
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"Directory not found: {directory_path}")
        
        if not path.is_dir():
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {directory_path}")
        
        # Generate task ID
        task_id = f"index_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Start indexing in background
        background_tasks.add_task(
            ingestion_pipeline.process_directory,
            path,
            task_id
        )
        
        logger.info(f"Started indexing directory: {directory_path} (task_id: {task_id})")
        
        return {
            "status": "success",
            "message": f"Indexing started for {directory_path}",
            "task_id": task_id,
            "directory": str(directory_path)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start indexing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/index/status/{task_id}")
async def get_index_status(task_id: str):
    """Get status of an indexing task"""
    try:
        if task_id in ingestion_status:
            updates = ingestion_status[task_id]
            if updates:
                latest = updates[-1]
                return {
                    "status": "success",
                    "task_id": task_id,
                    "progress": latest,
                    "all_updates": updates
                }
        
        return {
            "status": "not_found",
            "task_id": task_id,
            "message": "Task not found or completed"
        }
    except Exception as e:
        logger.error(f"Failed to get index status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# File upload endpoint for SettingsPanel
# Add this BEFORE the shutdown event in api.py

from fastapi import File, UploadFile
import tempfile
import shutil

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and index a single file
    """
    try:
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            # Save uploaded file
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = Path(tmp_file.name)
        
        logger.info(f"ðŸ“¤ Uploaded file: {file.filename}")
        
        # Process the file through ingestion pipeline
        result = await ingestion_pipeline.process_file(tmp_path)
        
        # Clean up temp file
        tmp_path.unlink()
        
        if result:
            return {
                "status": "success",
                "message": f"Successfully indexed {file.filename}",
                "filename": file.filename
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to index {file.filename}"
            }
            
    except Exception as e:
        logger.error(f"Upload error for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-batch")
async def upload_batch(files: List[UploadFile] = File(...), background_tasks: BackgroundTasks = None):
    """
    Upload and index multiple files at once
    Returns immediately and processes in background
    """
    try:
        task_id = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize status
        ingestion_status[task_id] = []
        ingestion_status[task_id].append({
            "task_id": task_id,
            "status": "started",
            "message": f"Starting upload of {len(files)} files",
            "total_files": len(files),
            "processed": 0
        })
        
        # Process files in background
        if background_tasks:
            background_tasks.add_task(process_uploaded_files, files, task_id)
        else:
            await process_uploaded_files(files, task_id)
        
        return {
            "status": "success",
            "message": f"Started processing {len(files)} files",
            "task_id": task_id,
            "file_count": len(files)
        }
        
    except Exception as e:
        logger.error(f"Batch upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_uploaded_files(files: List[UploadFile], task_id: str):
    """Process uploaded files and update status"""
    try:
        total = len(files)
        processed = 0
        
        for file in files:
            try:
                # Create temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
                    # Reset file pointer
                    await file.seek(0)
                    # Save uploaded file
                    shutil.copyfileobj(file.file, tmp_file)
                    tmp_path = Path(tmp_file.name)
                
                logger.info(f"ðŸ“¤ Processing uploaded file: {file.filename}")
                
                # Process through ingestion pipeline
                result = await ingestion_pipeline.process_file(tmp_path)
                
                # Clean up temp file
                tmp_path.unlink()
                
                processed += 1
                
                # Update status
                ingestion_status[task_id].append({
                    "task_id": task_id,
                    "status": "indexing",
                    "message": f"Processed {file.filename}",
                    "total_files": total,
                    "processed": processed
                })
                
            except Exception as e:
                logger.error(f"Failed to process {file.filename}: {e}")
                continue
        
        # Mark as complete
        ingestion_status[task_id].append({
            "task_id": task_id,
            "status": "completed",
            "message": f"Successfully processed {processed}/{total} files",
            "total_files": total,
            "processed": processed
        })
        
    except Exception as e:
        logger.error(f"Batch process error: {e}")
        ingestion_status[task_id].append({
            "task_id": task_id,
            "status": "error",
            "message": str(e)
        })

# Authentication endpoints for api.py
# Add these to your backend/api.py file

from backend.auth import UserManager
from fastapi import Header

# Initialize user manager (add this with other global variables)
user_manager = UserManager()

@app.post("/auth/register")
async def register(request: Dict[str, Any]):
    """Register a new user"""
    user_id = request.get("user_id")
    password = request.get("password")
    
    if not user_id or not password:
        raise HTTPException(status_code=400, detail="user_id and password required")
    
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    result = user_manager.register_user(user_id, password)
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@app.post("/auth/login")
async def login(request: Dict[str, Any]):
    """Login and get session token"""
    user_id = request.get("user_id")
    password = request.get("password")
    
    if not user_id or not password:
        raise HTTPException(status_code=400, detail="user_id and password required")
    
    session_token = user_manager.authenticate(user_id, password)
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {
        "status": "success",
        "session_token": session_token,
        "user_id": user_id
    }


@app.post("/auth/logout")
async def logout(request: Dict[str, Any]):
    """Logout user"""
    session_token = request.get("session_token")
    
    if session_token:
        user_manager.logout(session_token)
    
    return {"status": "success", "message": "Logged out"}


@app.get("/auth/verify")
async def verify_session(authorization: Optional[str] = Header(None)):
    """Verify session token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header")
    
    # Extract token from "Bearer <token>"
    token = authorization.replace("Bearer ", "")
    user_id = user_manager.verify_session(token)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    return {
        "status": "success",
        "user_id": user_id
    }


@app.get("/auth/check-user/{user_id}")
async def check_user_exists(user_id: str):
    """Check if user exists"""
    exists = user_manager.user_exists(user_id)
    return {
        "exists": exists,
        "user_id": user_id
    }


@app.post("/auth/change-password")
async def change_password(request: Dict[str, Any], authorization: Optional[str] = Header(None)):
    """Change user password"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.replace("Bearer ", "")
    user_id = user_manager.verify_session(token)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    old_password = request.get("old_password")
    new_password = request.get("new_password")
    
    if not old_password or not new_password:
        raise HTTPException(status_code=400, detail="old_password and new_password required")
    
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    result = user_manager.change_password(user_id, old_password, new_password)
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result
# File Watcher Endpoints
# Add to backend/api.py

@app.post("/watcher/enable")
async def enable_watcher(request: Dict[str, Any], background_tasks: BackgroundTasks):
    """Enable file watcher for a directory"""
    global watcher
    
    try:
        directory_path = request.get("directory_path")
        if not directory_path:
            # If no path provided, try to get from recent indexing
            directory_path = request.get("directory")
        
        if not directory_path:
            raise HTTPException(status_code=400, detail="directory_path required")
        
        path = Path(directory_path)
        if not path.exists() or not path.is_dir():
            raise HTTPException(status_code=404, detail=f"Directory not found: {directory_path}")
        
        # Stop existing watcher if any
        if watcher:
            watcher.stop()
        
        # Create and start new watcher
        watcher = FileWatcher(config, ingestion_pipeline, opensearch_client)
        background_tasks.add_task(watcher.start, path)
        
        logger.info(f"ðŸ“‚ File watcher enabled for: {directory_path}")
        
        return {
            "status": "success",
            "message": f"File watcher enabled for {directory_path}",
            "directory": str(directory_path)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to enable watcher: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/watcher/disable")
async def disable_watcher():
    """Disable file watcher"""
    global watcher
    
    try:
        if watcher:
            watcher.stop()
            watcher = None
            logger.info("ðŸ“‚ File watcher disabled")
            return {"status": "success", "message": "File watcher disabled"}
        else:
            return {"status": "success", "message": "File watcher was not running"}
            
    except Exception as e:
        logger.error(f"Failed to disable watcher: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/watcher/status")
async def get_watcher_status():
    """Get file watcher status"""
    global watcher
    
    is_running = watcher and watcher.is_running if watcher else False
    watched_dir = str(watcher.watched_directory) if watcher and hasattr(watcher, 'watched_directory') else None
    
    return {
        "status": "success",
        "watcher_enabled": is_running,
        "watching_directory": watched_dir
    }


# --- FILE SERVING ENDPOINTS ---
@app.get("/files/serve")
async def serve_file(file_path: str):
    """Serve a file for preview/download (replaces file:// protocol)"""
    try:
        # Decode URL-encoded path
        decoded_path = urllib.parse.unquote(file_path)
        file = Path(decoded_path)
        
        if not file.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if not file.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")
        
        # Determine media type
        import mimetypes
        media_type, _ = mimetypes.guess_type(str(file))
        
        return FileResponse(
            path=str(file),
            media_type=media_type or "application/octet-stream",
            filename=file.name
        )
    
    except Exception as e:
        logger.error(f"File serve error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/files/open")
async def open_file(file_path: str):
    """Open a file with the system's default application"""
    try:
        # Decode URL-encoded path
        decoded_path = urllib.parse.unquote(file_path)
        file = Path(decoded_path)
        
        if not file.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Open file with default application
        import platform
        system = platform.system()
        
        if system == "Windows":
            os.startfile(str(file))
        elif system == "Darwin":  # macOS
            subprocess.run(["open", str(file)])
        else:  # Linux and others
            subprocess.run(["xdg-open", str(file)])
        
        return {"status": "success", "message": f"Opened {file.name}"}
    
    except Exception as e:
        logger.error(f"File open error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
