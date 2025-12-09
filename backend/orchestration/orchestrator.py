
# backend/orchestration/orchestrator.py
"""
Zeus - The Conductor
====================
Enhanced Orchestrator with Greek Mythology Architecture

Main entry point that routes queries:
- Document-attached queries → DAEDALUS (The Architect)
- Non-document queries → ATHENA (The Strategist) → Specialized Agents

Agent Routing Flow:
==================
USER QUERY
    │
    ▼
┌──────────────────────────────────────────────────┐
│     ZEUS (The Conductor) - Main Orchestrator     │
└──────────────────────────────────────────────────┘
    │
    ├─── Has attached documents? ───────────────────────┐
    │              │                                     │
    │              NO                                   YES
    │              │                                     │
    │              ▼                                     ▼
    │   ┌─────────────────────┐          ┌──────────────────────────────┐
    │   │ ATHENA (Strategist) │          │ DAEDALUS (The Architect)     │
    │   │ Classify Intent     │          │ Document Orchestrator        │
    │   └─────────────────────┘          └──────────────────────────────┘
    │              │                                     │
    │              ▼                                     ▼
    │   Route to Specialized Agent:      Document Pipeline:
    │   - ARISTOTLE (Analysis)           - PROMETHEUS (Extract)
    │   - SOCRATES (Clarification)       - HYPATIA (Analyze)
    │   - DIOGENES (Quality Check)       - MNEMOSYNE (Insights)
    │   - HERMES (Explanation)           
    │   - THOTH (Summarization)          
    │              │                                     │
    └──────────────┴─────────────────────────────────────┘
                                    │
                                    ▼
                                RESPONSE
"""

import asyncio
from typing import Dict, Any, List, TypedDict, Optional
from datetime import datetime
from loguru import logger
import queue

# LangGraph imports
try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning("LangGraph not available, using simplified orchestration")

# Local imports
from backend.agents import (
    QueryClassifier, QueryIntent,
    ClarificationAgent, AnalysisAgent,
    SummarizationAgent, ExplanationAgent,
    CriticAgent
)
from backend.agents.document_agents import DaedalusOrchestrator
from backend.streaming_steps import emit_step
from backend.memory import MemoryManager
from backend.utils.llm_utils import call_ollama_with_retry


class WorkflowState(TypedDict):
    """State for the workflow graph"""
    user_id: str
    session_id: str
    query: str
    intent: Optional[str]
    confidence: float
    filters: Optional[Dict]
    entities: List[str]
    results: List[Dict[str, Any]]
    search_time: float
    clarification_questions: List[str]
    comparison_result: Optional[Dict]
    summary: Optional[str]
    explanations: List[str]
    insights: List[str]
    quality_evaluation: Optional[Dict]
    should_reformulate: bool
    response_message: str
    suggestions: List[str]
    session_context: Optional[Dict]
    user_preferences: Optional[Dict]
    conversation_history: Optional[List[Dict[str, Any]]]  # NEW: Previous messages
    next_action: str
    error: Optional[str]
    steps: List[Dict[str, Any]]


class EnhancedOrchestrator:
    """
    ZEUS - The Conductor
    Enhanced orchestrator using LangGraph for stateful multi-agent workflows.
    """
    AGENT_NAME = "Zeus"
    AGENT_TITLE = "The Conductor"
    AGENT_DESCRIPTION = "King of gods - I coordinate all agents and route your queries"
    AGENT_ICON = "⚡"

    def __init__(
        self,
        config: Dict[str, Any],
        memory_manager: MemoryManager,
        search_function: callable,
        opensearch_client=None
    ):
        self.config = config
        self.memory = memory_manager
        self.search_function = search_function
        self.opensearch_client = opensearch_client
        self.name = f"{self.AGENT_NAME} ({self.AGENT_TITLE})"
        
        # === ATHENA PATH AGENTS ===
        self.classifier = QueryClassifier(config)
        self.clarification_agent = ClarificationAgent(config)
        self.analysis_agent = AnalysisAgent(config)
        self.summarization_agent = SummarizationAgent(config)
        self.explanation_agent = ExplanationAgent(config)
        self.critic_agent = CriticAgent(config)
        
        # === DAEDALUS PATH ===
        self.daedalus = DaedalusOrchestrator(config, opensearch_client)

        if LANGGRAPH_AVAILABLE:
            self.workflow = self._build_langgraph_workflow()
        else:
            self.workflow = None

        logger.info(f"⚡ {self.name} initialized")
        logger.info(f"   ├── Athena Path: Socrates, Aristotle, Thoth, Hermes, Diogenes")
        logger.info(f"   └── Daedalus Path: Prometheus, Hypatia, Mnemosyne")

    def _build_langgraph_workflow(self) -> StateGraph:
        """Build LangGraph workflow for Athena path"""
        workflow = StateGraph(WorkflowState)
        workflow.add_node("classify", self._classify_node)
        workflow.add_node("load_context", self._load_context_node)
        workflow.add_node("document_search", self._document_search_node)
        workflow.add_node("general_answer", self._general_answer_node)
        workflow.add_node("clarify", self._clarify_node)
        workflow.add_node("analyze", self._analyze_node)
        workflow.add_node("summarize", self._summarize_node)
        workflow.add_node("explain", self._explain_node)
        workflow.add_node("quality_check", self._quality_check_node)
        workflow.add_node("generate_response", self._generate_response_node)
        workflow.set_entry_point("load_context")
        workflow.add_edge("load_context", "classify")
        workflow.add_conditional_edges(
            "classify",
            self._route_by_intent,
            {
                "document_search": "document_search",
                "general_knowledge": "general_answer",
                "clarification": "clarify",
                "comparison": "analyze",
                "summarization": "summarize",
                "analysis": "analyze"
            }
        )
        workflow.add_edge("document_search", "explain")
        workflow.add_edge("explain", "quality_check")
        workflow.add_edge("analyze", "quality_check")
        workflow.add_edge("summarize", "quality_check")
        workflow.add_edge("general_answer", "quality_check")
        workflow.add_edge("clarify", "generate_response")
        workflow.add_edge("quality_check", "generate_response")
        workflow.add_edge("generate_response", END)
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)

    async def process_query(
        self,
        user_id: str,
        session_id: str,
        query: str,
        conversation_id: Optional[str] = None,
        attached_documents: Optional[List[str]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for Zeus - The Conductor
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            query: User's query
            conversation_id: ID of the conversation
            attached_documents: List of attached document IDs
            conversation_history: Previous messages in this conversation
        """
        start_time = asyncio.get_event_loop().time()
        steps = []
        
        # Log conversation context
        if conversation_history:
            logger.info(f"🧠 Conversation context: {len(conversation_history)} previous messages")
        
        self._add_step_to_list(steps, session_id, 
                               f"{self.AGENT_ICON} {self.name}", 
                               "Receiving Query", 
                               f"Processing: '{query[:50]}...'")
        
        if attached_documents and len(attached_documents) > 0:
            return await self._route_to_daedalus(
                query=query, user_id=user_id, session_id=session_id,
                conversation_id=conversation_id,
                attached_documents=attached_documents,
                conversation_history=conversation_history,
                start_time=start_time, steps=steps
            )
        
        return await self._route_to_athena(
            query=query, user_id=user_id, session_id=session_id,
            conversation_id=conversation_id,
            conversation_history=conversation_history,
            start_time=start_time, steps=steps
        )


    async def _route_to_daedalus(
        self, query: str, user_id: str, session_id: str,
        conversation_id: Optional[str], attached_documents: List[str],
        conversation_history: Optional[List[Dict[str, Any]]],
        start_time: float, steps: List[Dict]
    ) -> Dict[str, Any]:
        """Route to DAEDALUS - The Architect"""
        self._add_step_to_list(steps, session_id, f"{self.AGENT_ICON} {self.name}",
                               "Routing to Daedalus",
                               f"Documents attached ({len(attached_documents)}) - activating document pipeline")
        
        try:
            documents_data = []
            for doc_id in attached_documents:
                try:
                    if self.opensearch_client:
                        doc = await self.opensearch_client.get_document(doc_id)
                        if doc:
                            documents_data.append({
                                'id': doc_id, 'path': doc.get('file_path'),
                                'filename': doc.get('filename'), 'file_path': doc.get('file_path')
                            })
                except Exception as e:
                    logger.warning(f"Could not fetch document {doc_id}: {e}")
            
            if not documents_data:
                self._add_step_to_list(steps, session_id, f"{self.AGENT_ICON} {self.name}",
                                       "Fallback", "No valid documents found - routing to Athena")
                return await self._route_to_athena(query=query, user_id=user_id, session_id=session_id,
                    conversation_id=conversation_id, conversation_history=conversation_history, start_time=start_time, steps=steps)
            
            self._add_step_to_list(steps, session_id, "🏛️ Daedalus (The Architect)",
                                   "Activating", f"Processing {len(documents_data)} document(s)")
            
            daedalus_response = await self.daedalus.process_query(
                query=query, attached_documents=documents_data, conversation_history=conversation_history
            )
            
            total_time = asyncio.get_event_loop().time() - start_time
            all_steps = steps + daedalus_response.thinking_steps
            
            return {
                "status": "success",
                "response_message": daedalus_response.answer,
                "results": daedalus_response.sources,
                "count": len(daedalus_response.sources),
                "intent": "document_query",
                "confidence": daedalus_response.confidence,
                "agents_used": daedalus_response.agents_used,
                "steps": all_steps,
                "search_time": round(total_time, 2),
                "total_time": round(total_time, 2),
                "document_mode": True,
                "routing_path": "Zeus → Daedalus → Prometheus → Hypatia → Mnemosyne"
            }
        
        except Exception as e:
            logger.error(f"Daedalus processing failed: {e}")
            self._add_step_to_list(steps, session_id, f"{self.AGENT_ICON} {self.name}",
                                   "Error Recovery", "Daedalus failed - routing to Athena")
            return await self._route_to_athena(query=query, user_id=user_id, session_id=session_id,
                conversation_id=conversation_id, conversation_history=conversation_history, start_time=start_time, steps=steps)

    async def _route_to_athena(
        self, query: str, user_id: str, session_id: str,
        conversation_id: Optional[str], conversation_history: Optional[List[Dict[str, Any]]],
        start_time: float, steps: List[Dict]
    ) -> Dict[str, Any]:
        """Route to ATHENA - The Strategist"""
        self._add_step_to_list(steps, session_id, f"{self.AGENT_ICON} {self.name}",
                               "Routing to Athena", "No documents attached - activating intent classification")
        
        initial_state: WorkflowState = {
            "user_id": user_id, "session_id": session_id, "conversation_id": conversation_id,
            "attached_documents": [], "query": query, "intent": None, "confidence": 0.0,
            "filters": None, "entities": [], "results": [], "search_time": 0.0,
            "clarification_questions": [], "comparison_result": None, "summary": None,
            "explanations": [], "insights": [], "quality_evaluation": {},
            "should_reformulate": False, "response_message": "", "suggestions": [],
            "session_context": None, "user_preferences": None, 
            "conversation_history": conversation_history,  # Pass conversation history
            "next_action": "classify", "error": None, "steps": steps
        }

        try:
            if LANGGRAPH_AVAILABLE and self.workflow:
                config = {"configurable": {"thread_id": session_id}}
                result = await self.workflow.ainvoke(initial_state, config)
            else:
                result = await self._simple_workflow(initial_state)

            await self.memory.record_interaction(
                user_id=user_id, session_id=session_id, query=query,
                response=result["response_message"], results=result["results"],
                intent=result.get("intent", "general"), search_time=result["search_time"],
                metadata={"quality_score": (result.get("quality_evaluation") or {}).get("quality_score"),
                         "confidence": result.get("confidence")}
            )

            total_time = asyncio.get_event_loop().time() - start_time
            result["total_time"] = round(total_time, 2)
            result["routing_path"] = self._get_routing_path(result.get("intent", "document_search"))
            if "steps" not in result:
                result["steps"] = initial_state["steps"]
            return result

        except Exception as e:
            logger.error(f"Athena workflow error: {e}")
            return {"status": "error", "error": str(e),
                   "message": "I encountered an error processing your request.", "steps": steps}

    def _get_routing_path(self, intent: str) -> str:
        paths = {
            "document_search": "Zeus → Athena → Search → Hermes → Diogenes",
            "general_knowledge": "Zeus → Athena → LLM → Diogenes",
            "comparison": "Zeus → Athena → Search → Aristotle → Diogenes",
            "analysis": "Zeus → Athena → Search → Aristotle → Diogenes",
            "summarization": "Zeus → Athena → Search → Thoth → Diogenes",
            "clarification_needed": "Zeus → Athena → Socrates",
        }
        return paths.get(intent, "Zeus → Athena → Default")

    def _add_step(self, state: WorkflowState, agent: str, action: str, details: str = ""):
        if "steps" not in state:
            state["steps"] = []
        step = {"agent": agent, "action": action, "details": details, "timestamp": datetime.now().isoformat()}
        state["steps"].append(step)
        if "session_id" in state:
            emit_step(state["session_id"], {"type": "step", "agent": agent, "action": action,
                     "details": details, "timestamp": step["timestamp"]})
        logger.info(f"🤖 [{agent}] {action}: {details}")

    def _add_step_to_list(self, steps: List[Dict], session_id: str, agent: str, action: str, details: str = ""):
        step = {"agent": agent, "action": action, "details": details, "timestamp": datetime.now().isoformat()}
        steps.append(step)
        emit_step(session_id, {"type": "step", "agent": agent, "action": action,
                 "details": details, "timestamp": step["timestamp"]})
        logger.info(f"🤖 [{agent}] {action}: {details}")

    async def _simple_workflow(self, state: WorkflowState) -> WorkflowState:
        state = await self._load_context_node(state)
        state = await self._classify_node(state)
        intent = state.get("intent", "document_search")
        
        if intent == QueryIntent.CLARIFICATION_NEEDED.value:
            state = await self._clarify_node(state)
        elif intent in [QueryIntent.GENERAL_KNOWLEDGE.value, QueryIntent.SYSTEM_META.value]:
            state = await self._general_answer_node(state)
        elif intent in [QueryIntent.COMPARISON.value, QueryIntent.ANALYSIS.value]:
            state = await self._document_search_node(state)
            state = await self._analyze_node(state)
        elif intent == QueryIntent.SUMMARIZATION.value:
            state = await self._document_search_node(state)
            state = await self._summarize_node(state)
        else:
            state = await self._document_search_node(state)
            state = await self._explain_node(state)

        if state["results"]:
            state = await self._quality_check_node(state)
        state = await self._generate_response_node(state)
        return state

    async def _load_context_node(self, state: WorkflowState) -> WorkflowState:
        try:
            self._add_step(state, "🧠 Memory", "Loading Context", "Retrieving session history")
            context = await self.memory.get_context(state["session_id"])
            state["session_context"] = context
            prefs = await self.memory.get_user_preferences(state["user_id"])
            state["user_preferences"] = prefs
        except Exception as e:
            logger.error(f"Context loading failed: {e}")
        return state

    async def _classify_node(self, state: WorkflowState) -> WorkflowState:
        try:
            self._add_step(state, "🦉 Athena (The Strategist)", "Analyzing Intent", f"Query: {state['query']}")
            result = await self.classifier.classify(query=state["query"], context=state.get("session_context"))
            state["intent"] = result["intent"].value
            state["confidence"] = result["confidence"]
            state["filters"] = result["filters"]
            state["entities"] = result["entities"]
            self._add_step(state, "🦉 Athena (The Strategist)", "Intent Detected", 
                          f"{result['intent'].value} (confidence: {result['confidence']:.2f})")
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            state["intent"] = QueryIntent.DOCUMENT_SEARCH.value
        return state

    async def _document_search_node(self, state: WorkflowState) -> WorkflowState:
        try:
            import time
            search_start = time.time()
            self._add_step(state, "🔍 Search Agent", "Searching", "Performing hybrid vector + keyword search")
            prefs = state.get("user_preferences", {})
            results = await self.search_function(
                query=state["query"], 
                filters=state.get("filters"),
                weights=prefs.get("optimal_weights", {}),
                user_id=state.get("user_id")  # Pass user_id for feedback boosts
            )
            if results is None:
                results = []
            state["results"] = results
            state["search_time"] = round(time.time() - search_start, 3)
            self._add_step(state, "🔍 Search Agent", "Results Found", f"{len(results)} documents retrieved")
        except Exception as e:
            logger.error(f"Search failed: {e}")
            state["error"] = str(e)
            state["results"] = []
        return state

    def _format_conversation_history(self, history: Optional[List[Dict[str, Any]]], max_turns: int = 6) -> str:
        """Format conversation history for LLM context"""
        if not history:
            return ""
        recent = history[-max_turns:] if len(history) > max_turns else history
        formatted = []
        for msg in recent:
            role = "User" if msg.get("role") == "user" else "Assistant"
            content = msg.get("content", "")[:500]
            formatted.append(f"{role}: {content}")
        if formatted:
            return "Previous conversation:\n" + "\n".join(formatted) + "\n\n"
        return ""

    async def _general_answer_node(self, state: WorkflowState) -> WorkflowState:
        try:
            history = state.get("conversation_history")
            if history:
                self._add_step(state, "🧠 Memory", "Loading Context", f"Using {len(history)} previous messages")
            self._add_step(state, "💬 LLM", "Generating Answer", "Using general knowledge")
            query = state['query']
            history_context = self._format_conversation_history(history)
            prompt = f"You are a helpful AI assistant.\n{history_context}User: {query}\n\nAssistant:"
            response_text = await call_ollama_with_retry(
                base_url=self.config['ollama']['base_url'],
                model=self.config['ollama']['text_model']['name'],
                prompt=prompt, max_retries=3,
                timeout=self.config['ollama'].get('timeout', 120.0),
                temperature=0.7,
                fallback_response="I'm having trouble right now. Please try again.",
                model_type="text", config=self.config
            )
            state["response_message"] = response_text
            state["results"] = []
        except Exception as e:
            logger.error(f"General answer failed: {e}")
            state["response_message"] = "Hello! I'm here to help you search your documents."
            state["results"] = []
        return state

    async def _clarify_node(self, state: WorkflowState) -> WorkflowState:
        try:
            self._add_step(state, "🤔 Socrates (The Inquirer)", "Generating Questions", "Query was ambiguous")
            result = await self.clarification_agent.generate_clarifying_questions(
                query=state["query"],
                ambiguity_info={"issues": ["ambiguous intent"], "possible_interpretations": []},
                max_questions=3
            )
            state["clarification_questions"] = result["questions"]
            self._add_step(state, "🤔 Socrates (The Inquirer)", "Questions Generated", f"{len(result['questions'])} questions")
            state["response_message"] = "I need some clarification to help you better:"
        except Exception as e:
            logger.error(f"Clarification failed: {e}")
        return state

    async def _analyze_node(self, state: WorkflowState) -> WorkflowState:
        try:
            self._add_step(state, "📊 Aristotle (The Analyst)", "Analyzing Documents", "Comparing and extracting insights")
            results = state.get("results", [])
            if len(results) >= 2:
                comparison = await self.analysis_agent.compare_documents(documents=results[:3])
                state["comparison_result"] = comparison
                self._add_step(state, "📊 Aristotle (The Analyst)", "Comparison Complete", "Compared top documents")
                insights_result = await self.analysis_agent.generate_insights(documents=results, query=state["query"])
                state["insights"] = insights_result["insights"]
                self._add_step(state, "📊 Aristotle (The Analyst)", "Insights Generated", f"{len(state['insights'])} insights")
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
        return state

    async def _summarize_node(self, state: WorkflowState) -> WorkflowState:
        try:
            self._add_step(state, "📜 Thoth (The Scribe)", "Summarizing", "Generating comprehensive summary")
            results = state.get("results", [])
            if results:
                result = await self.summarization_agent.summarize_documents(documents=results, summary_type="comprehensive")
                state["summary"] = result["summary"]
                self._add_step(state, "📜 Thoth (The Scribe)", "Summary Generated", "Created comprehensive summary")
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
        return state

    async def _explain_node(self, state: WorkflowState) -> WorkflowState:
        try:
            self._add_step(state, "📨 Hermes (The Messenger)", "Explaining Results", "Generating relevance explanations")
            results = state.get("results", [])
            explanations = []
            for i, doc in enumerate(results[:3], 1):
                result = await self.explanation_agent.explain_ranking(query=state["query"], document=doc, rank=i)
                explanations.append(result["explanation"])
            state["explanations"] = explanations
            self._add_step(state, "📨 Hermes (The Messenger)", "Explanations Ready", f"Explained top {len(explanations)} results")
        except Exception as e:
            logger.error(f"Explanation failed: {e}")
        return state

    async def _quality_check_node(self, state: WorkflowState) -> WorkflowState:
        try:
            self._add_step(state, "🔎 Diogenes (The Critic)", "Reviewing Quality", "Checking for relevance")
            evaluation = await self.critic_agent.evaluate_results(query=state["query"], results=state.get("results", []))
            state["quality_evaluation"] = evaluation
            state["should_reformulate"] = evaluation.get("should_reformulate", False)
            suggestions = await self.critic_agent.suggest_improvements(
                query=state["query"], results=state.get("results", []), evaluation=evaluation)
            state["suggestions"] = suggestions
            self._add_step(state, "🔎 Diogenes (The Critic)", "Quality Check Complete", 
                          f"Score: {evaluation.get('quality_score', 0):.2f}")
        except Exception as e:
            logger.error(f"Quality check failed: {e}")
        return state

    async def _generate_response_node(self, state: WorkflowState) -> WorkflowState:
        self._add_step(state, f"{self.AGENT_ICON} {self.name}", "Finalizing", "Constructing final response")
        try:
            intent = state.get("intent", "general")
            results = state.get("results", [])
            
            if state.get("clarification_questions"):
                state["response_message"] = "I need some clarification:\n" + "\n".join(f"• {q}" for q in state["clarification_questions"])
                return state
            if state.get("response_message") and intent == "general_knowledge":
                return state
            if state.get("summary"):
                state["response_message"] = f"**Summary of {len(results)} documents:**\n\n{state['summary']}"
                return state
            if state.get("comparison_result"):
                comp = state["comparison_result"]
                msg = f"**Comparison of documents:**\n\n**Similarities:** {', '.join(comp.get('similarities', []))}\n**Differences:** {', '.join(comp.get('differences', []))}"
                state["response_message"] = msg
                return state
            if results:
                count = len(results)
                state["response_message"] = f"I found {count} relevant document{'s' if count != 1 else ''} for your query."
            else:
                state["response_message"] = f"I couldn't find any documents matching '{state['query']}'. Try different keywords."
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            state["response_message"] = "I found some results for your query."
        return state

    def _route_by_intent(self, state: WorkflowState) -> str:
        intent = state.get("intent", "document_search")
        if state.get("confidence", 1.0) < 0.3:
            return "clarification"
        intent_map = {
            QueryIntent.DOCUMENT_SEARCH.value: "document_search",
            QueryIntent.GENERAL_KNOWLEDGE.value: "general_knowledge",
            QueryIntent.SYSTEM_META.value: "general_knowledge",
            QueryIntent.CLARIFICATION_NEEDED.value: "clarification",
            QueryIntent.COMPARISON.value: "analysis",
            QueryIntent.SUMMARIZATION.value: "summarization",
            QueryIntent.ANALYSIS.value: "analysis"
        }
        return intent_map.get(intent, "document_search")