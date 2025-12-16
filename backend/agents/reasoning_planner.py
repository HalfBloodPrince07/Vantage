# backend/agents/reasoning_planner.py
"""
ReasoningPlanner (Odysseus)
===========================
Odysseus - The Strategist - Multi-hop reasoning agent.

Handles complex queries requiring multiple retrieval steps:
- Query decomposition into sub-queries
- Planning retrieval steps
- Synthesizing answers from multiple sources
- ReAct-style reasoning loop
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

from backend.utils.llm_utils import call_ollama_json, call_ollama_with_retry


@dataclass
class SubQuery:
    """A sub-query decomposed from the main query"""
    id: str
    query: str
    purpose: str  # What this sub-query is meant to find
    dependencies: List[str]  # IDs of sub-queries this depends on
    priority: int  # Execution order (lower = first)
    estimated_type: str  # document_search, comparison, aggregation, etc.


@dataclass
class RetrievalStep:
    """A step in the retrieval plan"""
    step_id: int
    action: str  # retrieve, synthesize, compare, filter
    sub_query_id: str
    expected_output: str
    completed: bool = False
    result: Optional[Any] = None


@dataclass
class RetrievalPlan:
    """Complete plan for multi-hop retrieval"""
    original_query: str
    complexity: str  # simple, moderate, complex
    sub_queries: List[SubQuery]
    steps: List[RetrievalStep]
    requires_synthesis: bool


@dataclass
class SynthesizedAnswer:
    """Answer synthesized from multiple sub-answers"""
    answer: str
    sub_answers: List[Dict[str, Any]]
    confidence: float
    reasoning_trace: List[str]


class ReasoningPlanner:
    """
    Odysseus - The Strategist
    
    The cunning hero - I devise plans to answer complex questions
    that require multiple retrieval steps.
    
    Responsibilities:
    - Detect if a query needs multi-hop reasoning
    - Decompose complex queries into sub-queries
    - Plan and execute retrieval steps
    - Synthesize final answer from sub-answers
    """
    
    AGENT_NAME = "Odysseus"
    AGENT_TITLE = "The Strategist"
    AGENT_DESCRIPTION = "The cunning hero - I devise plans for complex questions"
    AGENT_ICON = "🧭"
    
    # Query patterns that suggest multi-hop reasoning
    COMPLEX_PATTERNS = [
        "compare", "versus", "vs", "difference between",
        "relationship between", "how does", "why did",
        "combine", "summarize all", "across all",
        "first...then", "before...after"
    ]
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = f"{self.AGENT_NAME} ({self.AGENT_TITLE})"
        self.ollama_url = config['ollama']['base_url']
        self.model = config['ollama']['text_model']['name']
        
        logger.info(f"🧭 {self.name} initialized for multi-hop reasoning")
    
    def detect_complexity(self, query: str) -> str:
        """
        Detect if query requires multi-hop reasoning.
        
        Returns:
            'simple', 'moderate', or 'complex'
        """
        query_lower = query.lower()
        
        # Check for complex patterns
        complex_indicators = sum(1 for pattern in self.COMPLEX_PATTERNS if pattern in query_lower)
        
        # Check for multiple question marks or clauses
        question_marks = query.count('?')
        and_count = query_lower.count(' and ')
        
        # Complexity scoring
        complexity_score = complex_indicators + question_marks + and_count
        
        if complexity_score >= 3:
            return "complex"
        elif complexity_score >= 1:
            return "moderate"
        else:
            return "simple"
    
    async def decompose_query(self, query: str) -> List[SubQuery]:
        """
        Decompose a complex query into sub-queries.
        
        Args:
            query: The complex query to decompose
            
        Returns:
            List of SubQuery objects
        """
        prompt = f"""Analyze this complex query and break it down into simpler sub-queries.

QUERY: "{query}"

Identify what information needs to be retrieved to fully answer this. Each sub-query should:
1. Be simple and focused on ONE piece of information
2. Have a clear purpose
3. Indicate dependencies on other sub-queries (if any)

Return JSON:
{{
    "sub_queries": [
        {{
            "id": "sq1",
            "query": "the simplified sub-query",
            "purpose": "what this finds",
            "dependencies": [],
            "priority": 1,
            "type": "document_search|comparison|aggregation|filter"
        }}
    ],
    "requires_synthesis": true
}}

Keep sub-queries to a maximum of 4. If the query is simple, return just 1 sub-query."""

        try:
            fallback = {
                "sub_queries": [
                    {
                        "id": "sq1",
                        "query": query,
                        "purpose": "Find relevant information",
                        "dependencies": [],
                        "priority": 1,
                        "type": "document_search"
                    }
                ],
                "requires_synthesis": False
            }
            
            result = await call_ollama_json(
                base_url=self.ollama_url,
                model=self.model,
                prompt=prompt,
                max_retries=2,
                timeout=self.config['ollama'].get('timeout', 120.0),
                temperature=0.3,
                fallback_data=fallback,
                model_type="text",
                config=self.config
            )
            
            sub_queries = []
            for sq in result.get('sub_queries', []):
                sub_queries.append(SubQuery(
                    id=sq.get('id', f"sq{len(sub_queries)+1}"),
                    query=sq.get('query', query),
                    purpose=sq.get('purpose', ''),
                    dependencies=sq.get('dependencies', []),
                    priority=sq.get('priority', len(sub_queries) + 1),
                    estimated_type=sq.get('type', 'document_search')
                ))
            
            logger.info(f"🧭 Decomposed query into {len(sub_queries)} sub-queries")
            return sub_queries
            
        except Exception as e:
            logger.error(f"Query decomposition failed: {e}")
            return [SubQuery(
                id="sq1",
                query=query,
                purpose="Main query",
                dependencies=[],
                priority=1,
                estimated_type="document_search"
            )]
    
    async def plan_retrieval(
        self,
        query: str,
        sub_queries: List[SubQuery]
    ) -> RetrievalPlan:
        """
        Create a retrieval plan from sub-queries.
        
        Args:
            query: Original query
            sub_queries: Decomposed sub-queries
            
        Returns:
            RetrievalPlan with ordered steps
        """
        # Sort sub-queries by priority and dependencies
        sorted_queries = sorted(sub_queries, key=lambda sq: sq.priority)
        
        steps = []
        for i, sq in enumerate(sorted_queries):
            steps.append(RetrievalStep(
                step_id=i + 1,
                action="retrieve",
                sub_query_id=sq.id,
                expected_output=sq.purpose
            ))
        
        # Add synthesis step if needed
        requires_synthesis = len(sub_queries) > 1
        if requires_synthesis:
            steps.append(RetrievalStep(
                step_id=len(steps) + 1,
                action="synthesize",
                sub_query_id="all",
                expected_output="Combined answer from all sub-queries"
            ))
        
        complexity = self.detect_complexity(query)
        
        return RetrievalPlan(
            original_query=query,
            complexity=complexity,
            sub_queries=sub_queries,
            steps=steps,
            requires_synthesis=requires_synthesis
        )
    
    async def synthesize_answers(
        self,
        original_query: str,
        sub_answers: List[Dict[str, Any]]
    ) -> SynthesizedAnswer:
        """
        Synthesize a final answer from multiple sub-answers.
        
        Args:
            original_query: The original complex query
            sub_answers: Answers to each sub-query
            
        Returns:
            SynthesizedAnswer combining all information
        """
        if not sub_answers:
            return SynthesizedAnswer(
                answer="I couldn't find enough information to answer your question.",
                sub_answers=[],
                confidence=0.0,
                reasoning_trace=["No sub-answers available"]
            )
        
        # Format sub-answers for synthesis
        sub_answer_text = []
        for i, sa in enumerate(sub_answers, 1):
            query = sa.get('query', '')
            answer = sa.get('answer', '')
            sources = sa.get('sources', [])
            sub_answer_text.append(
                f"Sub-query {i}: {query}\n"
                f"Answer: {answer}\n"
                f"Sources: {len(sources)} documents"
            )
        
        prompt = f"""Synthesize a comprehensive answer from these sub-answers.

ORIGINAL QUESTION: "{original_query}"

SUB-ANSWERS:
{chr(10).join(sub_answer_text)}

Create a single, coherent answer that:
1. Directly addresses the original question
2. Integrates information from all sub-answers
3. Maintains accuracy (don't add information not in sub-answers)
4. Is well-structured and easy to read

Return JSON:
{{
    "answer": "The synthesized comprehensive answer",
    "confidence": 0.0-1.0,
    "reasoning_trace": ["step1", "step2"]
}}"""

        try:
            fallback = {
                "answer": sub_answers[0].get('answer', 'Unable to synthesize answer.') if sub_answers else '',
                "confidence": 0.5,
                "reasoning_trace": ["Used first sub-answer as fallback"]
            }
            
            result = await call_ollama_json(
                base_url=self.ollama_url,
                model=self.model,
                prompt=prompt,
                max_retries=2,
                timeout=self.config['ollama'].get('timeout', 120.0),
                temperature=0.3,
                fallback_data=fallback,
                model_type="text",
                config=self.config
            )
            
            return SynthesizedAnswer(
                answer=result.get('answer', ''),
                sub_answers=sub_answers,
                confidence=float(result.get('confidence', 0.5)),
                reasoning_trace=result.get('reasoning_trace', [])
            )
            
        except Exception as e:
            logger.error(f"Answer synthesis failed: {e}")
            # Fallback: concatenate sub-answers
            combined = "\n\n".join(
                f"**{sa.get('query', 'Part')}**: {sa.get('answer', '')}"
                for sa in sub_answers
            )
            return SynthesizedAnswer(
                answer=combined,
                sub_answers=sub_answers,
                confidence=0.4,
                reasoning_trace=[f"Synthesis failed: {e}", "Concatenated sub-answers instead"]
            )
    
    async def execute_reasoning_loop(
        self,
        query: str,
        retriever_func,  # Async function to retrieve documents
        max_iterations: int = 5
    ) -> Dict[str, Any]:
        """
        Execute a ReAct-style reasoning loop.
        
        Args:
            query: The complex query
            retriever_func: Async function(query) -> results
            max_iterations: Maximum reasoning steps
            
        Returns:
            Final answer with reasoning trace
        """
        reasoning_trace = []
        sub_answers = []
        
        # Step 1: Analyze complexity
        complexity = self.detect_complexity(query)
        reasoning_trace.append(f"Query complexity: {complexity}")
        
        if complexity == "simple":
            # Skip decomposition for simple queries
            results = await retriever_func(query)
            return {
                "answer": None,  # Let normal flow handle it
                "reasoning_trace": reasoning_trace,
                "used_multi_hop": False
            }
        
        # Step 2: Decompose query
        sub_queries = await self.decompose_query(query)
        reasoning_trace.append(f"Decomposed into {len(sub_queries)} sub-queries")
        
        # Step 3: Execute each sub-query
        for sq in sorted(sub_queries, key=lambda x: x.priority):
            reasoning_trace.append(f"Executing: {sq.query}")
            
            try:
                results = await retriever_func(sq.query)
                
                # Get answer for this sub-query
                answer_text = ""
                if results:
                    # Simple answer from top result
                    top_result = results[0] if results else {}
                    answer_text = (top_result.get('detailed_summary', '') or top_result.get('content_summary', '') or top_result.get('text', ''))[:500]
                
                sub_answers.append({
                    "id": sq.id,
                    "query": sq.query,
                    "answer": answer_text,
                    "sources": results[:3] if results else []
                })
                
                reasoning_trace.append(f"Found {len(results)} results for {sq.id}")
                
            except Exception as e:
                reasoning_trace.append(f"Error on {sq.id}: {e}")
        
        # Step 4: Synthesize if needed
        if len(sub_answers) > 1:
            synthesized = await self.synthesize_answers(query, sub_answers)
            reasoning_trace.extend(synthesized.reasoning_trace)
            
            return {
                "answer": synthesized.answer,
                "sub_answers": sub_answers,
                "confidence": synthesized.confidence,
                "reasoning_trace": reasoning_trace,
                "used_multi_hop": True
            }
        elif sub_answers:
            return {
                "answer": sub_answers[0].get('answer', ''),
                "sub_answers": sub_answers,
                "confidence": 0.6,
                "reasoning_trace": reasoning_trace,
                "used_multi_hop": True
            }
        else:
            return {
                "answer": "I couldn't find enough information to answer your question.",
                "sub_answers": [],
                "confidence": 0.0,
                "reasoning_trace": reasoning_trace,
                "used_multi_hop": True
            }
    
    def get_agent_info(self) -> Dict[str, str]:
        """Return agent information for UI display"""
        return {
            "name": self.AGENT_NAME,
            "title": self.AGENT_TITLE,
            "full_name": self.name,
            "description": self.AGENT_DESCRIPTION,
            "icon": self.AGENT_ICON,
            "role": "reasoning_planner"
        }
