# backend/agents/critic_agent.py
"""
Critic Agent - Self-RAG and Quality Control
============================================
Diogenes - The Critic

Extended with Self-RAG (Corrective RAG) capabilities:
- Retrieval quality evaluation with detailed scoring
- Query reformulation suggestions
- Hallucination detection
- Confidence-aware feedback
- Retrieval loop control
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import httpx
from loguru import logger
import json
from backend.utils.llm_utils import call_ollama_json, call_ollama_with_retry


@dataclass
class RetrievalQuality:
    """Assessment of retrieval quality"""
    overall_score: float  # 0.0-1.0
    relevance_score: float
    coverage_score: float  # How well results cover the query
    diversity_score: float  # Variety in results
    confidence: float
    issues: List[str]
    is_sufficient: bool  # Whether results are good enough
    

@dataclass
class ReformulationSuggestion:
    """Suggested query reformulation"""
    original_query: str
    reformulated_query: str
    strategy: str  # expand, narrow, rephrase, add_context
    expected_improvement: str
    confidence: float


class CriticAgent:
    """
    Diogenes - The Critic
    
    The cynic philosopher - I question everything and evaluate quality.
    
    Extended with Self-RAG capabilities:
    - Evaluate retrieval quality and decide if reformulation needed
    - Suggest query reformulations
    - Detect hallucinations in generated answers
    - Control retrieval loops
    """
    AGENT_NAME = "Diogenes"
    AGENT_TITLE = "The Critic"
    AGENT_DESCRIPTION = "The cynic - I evaluate and control retrieval quality"
    AGENT_ICON = "🔎"

    def __init__(self, config: Dict[str, Any]):
        self.name = f"{self.AGENT_NAME} ({self.AGENT_TITLE})"
        self.config = config
        self.ollama_url = config['ollama']['base_url']
        self.model = config['ollama']['unified_model']['name']
        
        # Self-RAG thresholds
        self.min_quality_threshold = 0.5  # Minimum quality to accept results
        self.reformulation_threshold = 0.4  # Below this, definitely reformulate
        self.max_retrieval_iterations = 3  # Maximum reformulation attempts
        
        logger.info(f"🔎 {self.name} initialized with Self-RAG capabilities")

    async def evaluate_retrieval_quality(
        self,
        query: str,
        results: List[Dict[str, Any]],
        iteration: int = 1
    ) -> RetrievalQuality:
        """
        Evaluate the quality of retrieval results (Self-RAG core).
        
        Args:
            query: Original user query
            results: Retrieved documents
            iteration: Current retrieval iteration (for loop control)
            
        Returns:
            RetrievalQuality assessment
        """
        if not results:
            return RetrievalQuality(
                overall_score=0.0,
                relevance_score=0.0,
                coverage_score=0.0,
                diversity_score=0.0,
                confidence=1.0,
                issues=["No results retrieved"],
                is_sufficient=False
            )
        
        # Quick heuristic checks
        issues = []
        
        # Check result scores
        top_score = results[0].get('score', 0) if results else 0
        avg_score = sum(r.get('score', 0) for r in results) / len(results) if results else 0
        
        if top_score < 0.3:
            issues.append("Top result has low relevance score")
        if avg_score < 0.2:
            issues.append("Overall result quality is poor")
        if len(results) < 2:
            issues.append("Very few results found")
        
        # Check for diversity (different file types, sources)
        file_types = set(r.get('file_type', '') for r in results)
        diversity_score = min(len(file_types) / 3.0, 1.0)
        
        # Build prompt for LLM evaluation
        results_summary = []
        for i, r in enumerate(results[:5], 1):
            summary = (r.get('detailed_summary', '') or r.get('content_summary', '') or r.get('text', ''))[:150]
            results_summary.append(
                f"{i}. {r.get('filename', 'unknown')} (score: {r.get('score', 0):.2f})\n   {summary}"
            )
        
        prompt = f"""Evaluate retrieval quality for this search:

QUERY: "{query}"
ITERATION: {iteration} of {self.max_retrieval_iterations}

RESULTS:
{chr(10).join(results_summary)}

Evaluate these aspects (0.0-1.0):
1. RELEVANCE: Do results actually answer what was asked?
2. COVERAGE: Do results cover all aspects of the query?
3. CONFIDENCE: How confident are you in this assessment?

Also determine:
- Is this result set SUFFICIENT to answer the query? (true/false)
- What ISSUES exist with the results? (list specific problems)

Return JSON:
{{
    "relevance_score": 0.0-1.0,
    "coverage_score": 0.0-1.0,
    "confidence": 0.0-1.0,
    "is_sufficient": true/false,
    "issues": ["issue1", "issue2"]
}}"""

        try:
            fallback = {
                "relevance_score": 0.6,
                "coverage_score": 0.5,
                "confidence": 0.5,
                "is_sufficient": len(results) >= 2 and top_score > 0.3,
                "issues": issues
            }
            
            evaluation = await call_ollama_json(
                base_url=self.ollama_url,
                model=self.model,
                prompt=prompt,
                max_retries=2,
                timeout=self.config['ollama'].get('timeout', 120.0),
                temperature=0.2,
                fallback_data=fallback,
                model_type="text",
                config=self.config
            )
            
            relevance = float(evaluation.get('relevance_score', 0.5))
            coverage = float(evaluation.get('coverage_score', 0.5))
            overall = (relevance * 0.5 + coverage * 0.3 + diversity_score * 0.2)
            
            return RetrievalQuality(
                overall_score=overall,
                relevance_score=relevance,
                coverage_score=coverage,
                diversity_score=diversity_score,
                confidence=float(evaluation.get('confidence', 0.5)),
                issues=issues + evaluation.get('issues', []),
                is_sufficient=evaluation.get('is_sufficient', overall >= self.min_quality_threshold)
            )
            
        except Exception as e:
            logger.error(f"Retrieval quality evaluation failed: {e}")
            overall = (top_score * 0.5 + avg_score * 0.3 + diversity_score * 0.2)
            return RetrievalQuality(
                overall_score=overall,
                relevance_score=top_score,
                coverage_score=avg_score,
                diversity_score=diversity_score,
                confidence=0.4,
                issues=issues,
                is_sufficient=overall >= self.min_quality_threshold
            )

    def should_reformulate(self, quality: RetrievalQuality, iteration: int = 1) -> bool:
        """
        Decide if query should be reformulated based on quality.
        
        Args:
            quality: RetrievalQuality assessment
            iteration: Current iteration number
            
        Returns:
            True if reformulation is recommended
        """
        # Don't reformulate if we've hit max iterations
        if iteration >= self.max_retrieval_iterations:
            logger.info(f"🔎 Max iterations ({self.max_retrieval_iterations}) reached, accepting results")
            return False
        
        # Definitely reformulate if quality is very low
        if quality.overall_score < self.reformulation_threshold:
            logger.info(f"🔎 Quality score {quality.overall_score:.2f} below threshold, recommending reformulation")
            return True
        
        # Don't reformulate if quality is sufficient
        if quality.is_sufficient:
            return False
        
        # Reformulate if relevance is specifically low
        if quality.relevance_score < 0.4:
            return True
        
        return False

    async def suggest_reformulation(
        self,
        query: str,
        quality: RetrievalQuality,
        previous_results: List[Dict[str, Any]]
    ) -> ReformulationSuggestion:
        """
        Suggest how to reformulate the query for better results.
        
        Args:
            query: Original query
            quality: Quality assessment of current results
            previous_results: Results that were deemed insufficient
            
        Returns:
            ReformulationSuggestion with new query
        """
        issues_str = ", ".join(quality.issues[:3]) if quality.issues else "low relevance"
        
        prompt = f"""The search query didn't get good results. Suggest a better query.

ORIGINAL QUERY: "{query}"
ISSUES: {issues_str}

Suggest ONE reformulated query that might get better results.
Choose a strategy:
- EXPAND: Add related terms to broaden search
- NARROW: Be more specific to focus results  
- REPHRASE: Use different words for same meaning
- ADD_CONTEXT: Add context that might be in documents

Return JSON:
{{
    "reformulated_query": "the new query",
    "strategy": "EXPAND|NARROW|REPHRASE|ADD_CONTEXT",
    "expected_improvement": "brief explanation",
    "confidence": 0.0-1.0
}}"""

        try:
            fallback = {
                "reformulated_query": query,
                "strategy": "EXPAND",
                "expected_improvement": "Added broader terms",
                "confidence": 0.5
            }
            
            result = await call_ollama_json(
                base_url=self.ollama_url,
                model=self.model,
                prompt=prompt,
                max_retries=2,
                timeout=self.config['ollama'].get('timeout', 120.0),
                temperature=0.4,
                fallback_data=fallback,
                model_type="text",
                config=self.config
            )
            
            reformulated = result.get('reformulated_query', query)
            
            # Don't return identical query
            if reformulated.lower().strip() == query.lower().strip():
                # Simple fallback: try adding "documents about"
                reformulated = f"documents about {query}"
            
            logger.info(f"🔎 Suggested reformulation: '{query}' -> '{reformulated}'")
            
            return ReformulationSuggestion(
                original_query=query,
                reformulated_query=reformulated,
                strategy=result.get('strategy', 'EXPAND'),
                expected_improvement=result.get('expected_improvement', ''),
                confidence=float(result.get('confidence', 0.5))
            )
            
        except Exception as e:
            logger.error(f"Reformulation suggestion failed: {e}")
            return ReformulationSuggestion(
                original_query=query,
                reformulated_query=f"files related to {query}",
                strategy="EXPAND",
                expected_improvement="Added broader context",
                confidence=0.4
            )

    async def detect_hallucinations(
        self,
        answer: str,
        query: str,
        sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect if the generated answer contains hallucinations.
        
        Args:
            answer: Generated answer text
            query: Original query
            sources: Source documents used
            
        Returns:
            Hallucination detection results
        """
        if not answer or not sources:
            return {
                "has_hallucination": False,
                "confidence": 0.5,
                "unsupported_claims": [],
                "verification_status": "insufficient_data"
            }
        
        # Extract source content
        source_texts = []
        for doc in sources[:3]:
            text = (doc.get('detailed_summary', '') or doc.get('content_summary', '') or doc.get('text', '') or doc.get('raw_text', ''))[:500]
            source_texts.append(f"[{doc.get('filename', 'unknown')}]: {text}")
        
        prompt = f"""Check if this answer is supported by the sources.

QUESTION: "{query}"

ANSWER TO CHECK:
{answer[:1000]}

AVAILABLE SOURCES:
{chr(10).join(source_texts)}

Analyze the answer and identify:
1. Claims that ARE supported by the sources
2. Claims that are NOT supported (potential hallucinations)
3. Overall verdict

Return JSON:
{{
    "has_hallucination": true/false,
    "confidence": 0.0-1.0,
    "supported_claims": ["claim1", "claim2"],
    "unsupported_claims": ["claim1"],
    "verification_status": "verified|partially_verified|unverified"
}}"""

        try:
            fallback = {
                "has_hallucination": False,
                "confidence": 0.5,
                "supported_claims": [],
                "unsupported_claims": [],
                "verification_status": "partially_verified"
            }
            
            result = await call_ollama_json(
                base_url=self.ollama_url,
                model=self.model,
                prompt=prompt,
                max_retries=2,
                timeout=self.config['ollama'].get('timeout', 120.0),
                temperature=0.1,
                fallback_data=fallback,
                model_type="text",
                config=self.config
            )
            
            return {
                "agent": self.name,
                "has_hallucination": result.get('has_hallucination', False),
                "confidence": float(result.get('confidence', 0.5)),
                "supported_claims": result.get('supported_claims', []),
                "unsupported_claims": result.get('unsupported_claims', []),
                "verification_status": result.get('verification_status', 'partially_verified')
            }
            
        except Exception as e:
            logger.error(f"Hallucination detection failed: {e}")
            return {
                "has_hallucination": False,
                "confidence": 0.4,
                "unsupported_claims": [],
                "verification_status": "check_failed"
            }

    async def evaluate_results(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate quality of search results (original interface, now using Self-RAG).
        """
        quality = await self.evaluate_retrieval_quality(query, results)
        
        return {
            "agent": self.name,
            "quality_score": quality.overall_score,
            "relevance": quality.relevance_score,
            "completeness": quality.coverage_score,
            "diversity": quality.diversity_score,
            "confidence": quality.confidence,
            "issues": quality.issues,
            "strengths": [],
            "weaknesses": quality.issues,
            "recommendations": [],
            "should_reformulate": not quality.is_sufficient,
            "is_sufficient": quality.is_sufficient
        }

    def calculate_confidence_score(
        self,
        results: List[Dict[str, Any]],
        evaluation: Dict[str, Any]
    ) -> float:
        """Calculate overall confidence score for results"""
        if not results:
            return 0.0

        num_results_score = min(len(results) / 5.0, 1.0)
        quality_score = evaluation.get('quality_score', 0.5)
        top_score = results[0].get('score', 0) if results else 0

        confidence = (
            num_results_score * 0.2 +
            quality_score * 0.4 +
            min(top_score, 1.0) * 0.4
        )

        return round(confidence, 2)

    async def suggest_improvements(
        self,
        query: str,
        results: List[Dict[str, Any]],
        evaluation: Dict[str, Any]
    ) -> List[str]:
        """Suggest improvements to search query or strategy"""
        suggestions = []

        if evaluation.get('should_reformulate'):
            suggestions.append("Try rephrasing your query with different keywords")

        if evaluation.get('relevance', 1.0) < 0.5:
            suggestions.append("Results may not match your intent. Be more specific")

        if len(results) == 0:
            suggestions.extend([
                "Try broader search terms",
                "Check if documents are indexed",
                "Use different keywords"
            ])
        elif len(results) < 3:
            suggestions.append("Limited results found. Try expanding your search")

        suggestions.extend(evaluation.get('recommendations', []))
        return suggestions[:5]

    def get_agent_info(self) -> Dict[str, str]:
        """Return agent information for UI display"""
        return {
            "name": self.AGENT_NAME,
            "title": self.AGENT_TITLE,
            "full_name": self.name,
            "description": self.AGENT_DESCRIPTION,
            "icon": self.AGENT_ICON,
            "role": "critic_self_rag"
        }

