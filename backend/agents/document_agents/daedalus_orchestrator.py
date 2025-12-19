"""
Daedalus (The Architect)
========================
Master craftsman and architect - orchestrates the document processing pipeline.

Responsibilities:
- Coordinate between Prometheus, Hypatia, and Mnemosyne
- Manage document processing workflow
- Cache processed documents for efficiency
- Handle multi-document queries
- Synthesize information across multiple documents
- Route user questions to appropriate extracted knowledge
- Maintain conversation context about documents

Input: User query + Attached document IDs/paths
Output: Complete processed response with citations

IMPORTANT: This orchestrator is SEPARATE from Zeus (main orchestrator).
Daedalus ONLY activates when user has attached documents and asks 
questions specifically about those documents.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from loguru import logger
import asyncio
from pathlib import Path
from datetime import datetime

from .prometheus_reader import PrometheusReader, ExtractedContent
from .hypatia_analyzer import HypatiaAnalyzer, SemanticAnalysis
from .mnemosyne_extractor import MnemosyneExtractor, DocumentInsights
from backend.utils.llm_utils import call_ollama_with_retry


@dataclass
class ProcessedDocument:
    """Fully processed document with all agent outputs"""
    document_id: str
    filename: str
    extracted: ExtractedContent
    analysis: SemanticAnalysis
    insights: DocumentInsights
    processed_at: str
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "document_id": self.document_id,
            "filename": self.filename,
            "extracted": self.extracted.to_dict(),
            "analysis": self.analysis.to_dict(),
            "insights": self.insights.to_dict(),
            "processed_at": self.processed_at
        }


@dataclass
class DocumentQueryResponse:
    """Response to a document-specific query"""
    answer: str
    sources: List[Dict[str, Any]]  # [{filename, page, excerpt}]
    confidence: float
    agents_used: List[str]
    thinking_steps: List[Dict[str, str]]
    
    def to_dict(self):
        """Convert to dictionary"""
        return asdict(self)


class DaedalusOrchestrator:
    """
    Daedalus (The Architect) - Document Processing Orchestrator
    
    Like the master architect of the Labyrinth, I design and coordinate
    the complex workflow of document understanding.
    
    ACTIVATION CONDITION:
    - User has attached one or more documents to the conversation
    - User's query is specifically about the attached documents
    - Query contains references like "this document", "the file", "attached", etc.
    """
    
    AGENT_NAME = "Daedalus"
    AGENT_TITLE = "The Architect"
    AGENT_DESCRIPTION = "Master architect - I coordinate document understanding"
    
    # Keywords that indicate document-specific queries
    DOCUMENT_QUERY_INDICATORS = [
        "this document", "this file", "the document", "the file",
        "attached", "uploaded", "this pdf", "this image",
        "in here", "from this", "what does it say",
        "summarize this", "explain this document", "summarize the",
        "what is this about", "content of this",
        "in the document", "from the document",
        "attached document", "the attached"
    ]
    
    def __init__(self, config: Dict[str, Any], opensearch_client=None):
        self.name = f"{self.AGENT_NAME} ({self.AGENT_TITLE})"
        self.config = config
        self.opensearch_client = opensearch_client
        
        # Initialize sub-agents
        self.prometheus = PrometheusReader(config)
        self.hypatia = HypatiaAnalyzer(config)
        self.mnemosyne = MnemosyneExtractor(config)
        
        # Document cache
        self._processed_cache: Dict[str, ProcessedDocument] = {}
        
        logger.info(f"🏛️ {self.name} initialized with sub-agents: "
                   f"Prometheus, Hypatia, Mnemosyne")
    
    def should_activate(self, query: str, attached_documents: List[str]) -> bool:
        """
        Determine if Daedalus should handle this query.
        
        SIMPLIFIED: Always activate if documents are attached.
        Zeus handles the routing decision - if documents are attached,
        Daedalus is the right choice for processing.
        
        Returns True if:
        - User has attached documents (regardless of query content)
        """
        if not attached_documents:
            return False
        
        # Always activate when documents are attached
        # Zeus has already decided to route here
        logger.info(f"🏛️ Daedalus activating for query with {len(attached_documents)} attached document(s)")
        return True

    
    async def process_query(
        self,
        query: str,
        attached_documents: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict]] = None
    ) -> DocumentQueryResponse:
        """
        Main entry point for document-specific queries.
        
        Args:
            query: User's question
            attached_documents: List of {id, path, filename, content?}
            conversation_history: Previous conversation turns
            
        Returns:
            DocumentQueryResponse with answer and sources
        """
        thinking_steps = []
        agents_used = [self.name]
        
        # Step 1: Process all attached documents
        thinking_steps.append({
            "agent": self.name,
            "step": "Analyzing attached documents...",
            "detail": f"Processing {len(attached_documents)} document(s)"
        })
        
        processed_docs = await self._process_documents(attached_documents)
        agents_used.extend([
            "Prometheus (The Illuminator)", 
            "Hypatia (The Scholar)", 
            "Mnemosyne (The Keeper)"
        ])
        
        # Step 2: Build context from all documents
        thinking_steps.append({
            "agent": "Hypatia (The Scholar)",
            "step": "Building semantic understanding...",
            "detail": "Analyzing structure and meaning"
        })
        
        combined_context = self._build_combined_context(processed_docs)
        
        # Step 3: Answer the query
        thinking_steps.append({
            "agent": "Mnemosyne (The Keeper)",
            "step": "Searching for relevant information...",
            "detail": "Extracting insights to answer your question"
        })
        
        answer, sources, confidence = await self._answer_query(
            query, processed_docs, combined_context, conversation_history
        )
        
        return DocumentQueryResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            agents_used=agents_used,
            thinking_steps=thinking_steps
        )
    
    async def _process_documents(
        self, 
        documents: List[Dict[str, Any]]
    ) -> List[ProcessedDocument]:
        """Process documents through the full pipeline"""
        processed = []
        
        for doc in documents:
            doc_id = doc.get('id') or doc.get('path') or doc.get('filename')
            
            # Check cache first
            if doc_id in self._processed_cache:
                logger.info(f"🏛️ Using cached analysis for {doc_id}")
                processed.append(self._processed_cache[doc_id])
                continue
            
            try:
                # Extract with Prometheus
                file_path = doc.get('path') or doc.get('file_path')
                file_content = doc.get('content')  # For uploaded files
                
                logger.info(f"🔥 Prometheus extracting from {file_path}")
                extracted_list = await self.prometheus.extract(
                    [file_path], 
                    [file_content] if file_content else None
                )
                extracted = extracted_list[0]
                
                if not extracted.success:
                    logger.warning(f"Failed to extract {file_path}: {extracted.error}")
                    continue
                
                # Analyze with Hypatia
                logger.info(f"📚 Hypatia analyzing {extracted.filename}")
                analysis = await self.hypatia.analyze({
                    'raw_text': extracted.raw_text,
                    'filename': extracted.filename,
                    'content': extracted.content
                })
                
                # Extract insights with Mnemosyne
                logger.info(f"🧠 Mnemosyne extracting insights from {extracted.filename}")
                insights = await self.mnemosyne.extract_insights(
                    {'raw_text': extracted.raw_text, 'filename': extracted.filename},
                    analysis.to_dict()
                )
                
                # Create processed document
                proc_doc = ProcessedDocument(
                    document_id=doc_id,
                    filename=extracted.filename,
                    extracted=extracted,
                    analysis=analysis,
                    insights=insights,
                    processed_at=datetime.utcnow().isoformat()
                )
                
                # Cache it
                self._processed_cache[doc_id] = proc_doc
                processed.append(proc_doc)
                
                logger.info(f"🏛️ Successfully processed {extracted.filename}")
                
            except Exception as e:
                logger.error(f"🏛️ Error processing document {doc.get('filename', 'unknown')}: {e}")
                continue
        
        return processed
    
    def _build_combined_context(self, docs: List[ProcessedDocument]) -> str:
        """Build combined context from multiple documents"""
        if not docs:
            return ""
        
        context_parts = []
        
        for i, doc in enumerate(docs, 1):
            context_parts.append(f"""
Document {i}: {doc.filename}
Type: {doc.analysis.document_type}
Summary: {doc.insights.executive_summary}

Key Points:
{chr(10).join('- ' + p for p in doc.insights.key_points[:5])}

Content Preview:
{doc.extracted.raw_text[:2000]}...
""")
        
        return "\n\n---\n\n".join(context_parts)
    
    async def _answer_query(
        self,
        query: str,
        docs: List[ProcessedDocument],
        context: str,
        history: Optional[List[Dict]]
    ) -> Tuple[str, List[Dict], float]:
        """Generate answer using LLM with document context"""
        
        if not docs:
            return (
                "I couldn't process any of the attached documents. Please check the file format and try again.",
                [],
                0.0
            )
        
        # Build sources for citation
        sources = []
        for doc in docs:
            sources.append({
                "filename": doc.filename,
                "type": doc.analysis.document_type,
                "summary": doc.insights.executive_summary
            })
        
        # Format conversation history if available
        history_context = ""
        if history and len(history) > 0:
            history_lines = []
            for msg in history[-6:]:  # Last 6 messages for context
                role = "User" if msg.get("role") == "user" else "Assistant"
                content = msg.get("content", "")[:300]
                history_lines.append(f"{role}: {content}")
            history_context = "Previous conversation:\n" + "\n".join(history_lines) + "\n\n"
        
        # Create answering prompt
        prompt = f"""You are an expert document analyst. Answer the user's question based ONLY on the attached document(s).

{context}

{history_context}User's Question: {query}

Instructions:
1. Answer based solely on the document content provided above
2. Be specific and cite which document you're referencing
3. If the answer isn't in the documents, say so clearly
4. Use bullet points for clarity when appropriate
5. Keep your answer concise but comprehensive
6. If the user refers to previous conversation, use that context to understand their intent

Answer:"""
        
        try:
            answer = await call_ollama_with_retry(
                base_url=self.config['ollama']['base_url'],
                model=self.config['ollama']['unified_model']['name'],
                prompt=prompt,
                max_retries=2,
                timeout=self.config['ollama'].get('timeout', 120.0),
                temperature=0.3,
                fallback_response="I found the documents but I'm having trouble generating an answer. Please try rephrasing your question.",
                model_type="text",
                config=self.config
            )
            
            # Calculate confidence based on answer quality
            confidence = 0.8 if len(answer) > 50 else 0.5
            
            return answer.strip(), sources, confidence
            
        except Exception as e:
            logger.error(f"🏛️ Answer generation failed: {e}")
            return (
                "I encountered an error while analyzing the documents. Please try again.",
                sources,
                0.0
            )
    
    def clear_cache(self, document_id: Optional[str] = None):
        """Clear processed document cache"""
        if document_id:
            self._processed_cache.pop(document_id, None)
            logger.info(f"🏛️ Cleared cache for {document_id}")
        else:
            self._processed_cache.clear()
            logger.info("🏛️ Cleared entire document cache")
    
    def get_agent_info(self) -> Dict[str, str]:
        """Return agent information for UI display"""
        return {
            "name": self.AGENT_NAME,
            "title": self.AGENT_TITLE,
            "full_name": self.name,
            "description": self.AGENT_DESCRIPTION,
            "icon": "🏛️",
            "role": "document_orchestrator"
        }
    
    def get_all_agents_info(self) -> List[Dict[str, str]]:
        """Get info for all document processing agents"""
        return [
            self.get_agent_info(),
            self.prometheus.get_agent_info(),
            self.hypatia.get_agent_info(),
            self.mnemosyne.get_agent_info()
        ]
