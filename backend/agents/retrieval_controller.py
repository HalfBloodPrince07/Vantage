"""
RetrievalController (Sisyphus) - The Persistent One
Controls retrieval loops with quality-based correction and query reformulation.

Implements Corrective RAG (CRAG) pattern:
1. Retrieve documents
2. Evaluate quality with Diogenes
3. If quality is low, reformulate query and retry
4. Max iterations prevent infinite loops
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from loguru import logger
import asyncio


@dataclass
class RetrievalAttempt:
    """Record of a single retrieval attempt"""
    iteration: int
    query: str
    results: List[Dict[str, Any]]
    quality_score: float
    issues: List[str]
    reformulation_applied: bool
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CorrectedResults:
    """Final results after correction loop"""
    final_results: List[Dict[str, Any]]
    final_query: str
    original_query: str
    total_iterations: int
    attempts: List[RetrievalAttempt]
    final_quality: float
    was_reformulated: bool
    improvement_percentage: float


class RetrievalController:
    """
    Sisyphus - The Persistent - Controls retrieval loops with correction.
    
    Implements the CRAG (Corrective RAG) pattern:
    - Evaluates retrieval quality after each attempt
    - Reformulates query if quality is below threshold
    - Retries up to max_iterations times
    - Tracks improvement across iterations
    """
    
    AGENT_NAME = "Sisyphus"
    AGENT_ICON = "🔄"
    
    def __init__(
        self, 
        config: Dict[str, Any],
        critic_agent = None,
        search_function = None,
        max_iterations: int = 3,
        quality_threshold: float = 0.6
    ):
        self.config = config
        self.critic = critic_agent
        self.search_function = search_function
        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold
        
        # LLM settings for reformulation
        self.ollama_url = config.get('ollama', {}).get('base_url', 'http://localhost:11434')
        self.model = config.get('ollama', {}).get('unified_model', {}).get('name', 'qwen3-vl:8b')
        
        logger.info(f"🔄 {self.AGENT_NAME} initialized (max_iterations={max_iterations}, threshold={quality_threshold})")
    
    async def retrieve_with_correction(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        step_callback = None
    ) -> CorrectedResults:
        """
        Main entry point - retrieve with quality-based correction loop.
        
        Args:
            query: Original user query
            filters: Optional search filters
            user_id: User ID for personalization
            step_callback: Optional callback for logging steps
            
        Returns:
            CorrectedResults with final results and attempt history
        """
        original_query = query
        current_query = query
        attempts: List[RetrievalAttempt] = []
        best_results = []
        best_quality = 0.0
        
        for iteration in range(1, self.max_iterations + 1):
            if step_callback:
                step_callback(
                    f"{self.AGENT_ICON} {self.AGENT_NAME}",
                    f"Iteration {iteration}/{self.max_iterations}",
                    f"Searching with: '{current_query[:50]}...'"
                )
            
            # Step 1: Perform retrieval
            try:
                results = await self.search_function(
                    query=current_query,
                    filters=filters,
                    user_id=user_id
                )
                if results is None:
                    results = []
            except Exception as e:
                logger.error(f"Search failed in iteration {iteration}: {e}")
                results = []
            
            # Step 2: Evaluate quality with Diogenes
            quality_score, issues = await self._evaluate_quality(current_query, results)
            
            # Track attempt
            attempt = RetrievalAttempt(
                iteration=iteration,
                query=current_query,
                results=results,
                quality_score=quality_score,
                issues=issues,
                reformulation_applied=(iteration > 1)
            )
            attempts.append(attempt)
            
            # Track best results
            if quality_score > best_quality:
                best_quality = quality_score
                best_results = results
            
            if step_callback:
                step_callback(
                    f"{self.AGENT_ICON} {self.AGENT_NAME}",
                    f"Quality: {quality_score:.0%}",
                    f"Found {len(results)} results"
                )
            
            # Step 3: Check if quality is acceptable
            if quality_score >= self.quality_threshold:
                logger.info(f"✓ Quality threshold met at iteration {iteration}")
                break
            
            # Step 4: Reformulate if more iterations available
            if iteration < self.max_iterations:
                if step_callback:
                    step_callback(
                        f"{self.AGENT_ICON} {self.AGENT_NAME}",
                        "Reformulating Query",
                        f"Issues: {', '.join(issues[:2])}"
                    )
                
                reformulated = await self._reformulate_query(
                    original_query=original_query,
                    current_query=current_query,
                    issues=issues,
                    results=results
                )
                
                if reformulated and reformulated != current_query:
                    current_query = reformulated
                    logger.info(f"Query reformulated: '{reformulated[:50]}...'")
                else:
                    logger.info("No useful reformulation found, keeping current query")
        
        # Calculate improvement
        initial_quality = attempts[0].quality_score if attempts else 0
        improvement = ((best_quality - initial_quality) / max(initial_quality, 0.01)) * 100
        
        return CorrectedResults(
            final_results=best_results,
            final_query=current_query,
            original_query=original_query,
            total_iterations=len(attempts),
            attempts=attempts,
            final_quality=best_quality,
            was_reformulated=(current_query != original_query),
            improvement_percentage=max(0, improvement)
        )
    
    async def _evaluate_quality(
        self, 
        query: str, 
        results: List[Dict[str, Any]]
    ) -> Tuple[float, List[str]]:
        """
        Evaluate retrieval quality using Diogenes (critic agent).
        
        Returns:
            Tuple of (quality_score, list_of_issues)
        """
        issues = []
        
        if not results:
            return 0.0, ["No results found"]
        
        # Use critic agent if available
        if self.critic:
            try:
                evaluation = await self.critic.evaluate_retrieval_quality(
                    query=query,
                    results=results
                )
                return evaluation.get("score", 0.5), evaluation.get("issues", [])
            except Exception as e:
                logger.warning(f"Critic evaluation failed: {e}")
        
        # Fallback: heuristic quality scoring
        quality = 0.3  # Base score
        
        # Factor 1: Number of results
        if len(results) >= 5:
            quality += 0.2
        elif len(results) >= 2:
            quality += 0.1
        else:
            issues.append("Too few results")
        
        # Factor 2: Score distribution
        scores = [r.get('score', 0) for r in results if r.get('score')]
        if scores:
            avg_score = sum(scores) / len(scores)
            if avg_score >= 0.7:
                quality += 0.3
            elif avg_score >= 0.5:
                quality += 0.15
            else:
                issues.append("Low relevance scores")
        
        # Factor 3: Query terms in results
        query_terms = set(query.lower().split())
        matches = 0
        for r in results[:5]:
            content = (r.get('detailed_summary', '') or r.get('content_summary', '') + r.get('filename', '')).lower()
            if any(term in content for term in query_terms):
                matches += 1
        
        if matches >= 3:
            quality += 0.2
        elif matches >= 1:
            quality += 0.1
        else:
            issues.append("Query terms not well matched")
        
        return min(quality, 1.0), issues
    
    async def _reformulate_query(
        self,
        original_query: str,
        current_query: str,
        issues: List[str],
        results: List[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Reformulate query based on issues and current results.
        """
        # Get context from existing results
        result_context = ""
        if results:
            top_terms = set()
            for r in results[:3]:
                keywords = r.get('keywords', '')
                if keywords:
                    top_terms.update(keywords.split(',')[:3])
            if top_terms:
                result_context = f"\nTerms from partial matches: {', '.join(list(top_terms)[:5])}"
        
        prompt = f"""You are a search query optimizer. The user's search didn't return good results.

Original query: "{original_query}"
Current query: "{current_query}"
Issues: {', '.join(issues)}
{result_context}

Generate a SINGLE improved search query that:
1. Keeps the original intent
2. Addresses the issues
3. Uses different keywords or phrasing
4. Is concise (under 15 words)

Return ONLY the new query, nothing else."""

        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.7, "num_predict": 50}
                    }
                )
                
                result = response.json()
                reformulated = result.get('response', '').strip()
                
                # Clean up response
                reformulated = reformulated.strip('"\'')
                if reformulated and len(reformulated) < 200:
                    return reformulated
                    
        except Exception as e:
            logger.error(f"Query reformulation failed: {e}")
        
        # Fallback: simple expansion
        return self._simple_reformulation(original_query, issues)
    
    def _simple_reformulation(self, query: str, issues: List[str]) -> str:
        """Simple rule-based reformulation fallback."""
        words = query.split()
        
        # Strategy 1: If too specific, broaden
        if "Too few results" in issues and len(words) > 3:
            return " ".join(words[:3])
        
        # Strategy 2: Add synonyms for common terms
        synonyms = {
            "find": "search locate",
            "show": "display list",
            "get": "retrieve fetch",
            "about": "regarding concerning",
        }
        
        for word in words:
            if word.lower() in synonyms:
                return query.replace(word, synonyms[word.lower()].split()[0])
        
        return query
    
    def should_use_correction(self, query: str, initial_results: List[Dict]) -> bool:
        """
        Determine if correction loop should be used.
        
        Returns True if:
        - Few results found
        - Low average score
        - Query looks complex
        """
        if not initial_results:
            return True
        
        if len(initial_results) < 3:
            return True
        
        scores = [r.get('score', 0) for r in initial_results]
        if scores and sum(scores) / len(scores) < 0.5:
            return True
        
        # Complex queries benefit from correction
        if len(query.split()) > 8 or '?' in query:
            return True
        
        return False
