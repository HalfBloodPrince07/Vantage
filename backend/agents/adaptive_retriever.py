# backend/agents/adaptive_retriever.py
"""
AdaptiveRetriever (Proteus)
===========================
Proteus - The Shape-Shifter - Adaptive retrieval strategy selection.

Chooses the best retrieval strategy based on query characteristics:
- Precise: Keyword-heavy search (BM25)
- Semantic: Embedding-based search (vector)
- Exploratory: Graph traversal for related entities
- Temporal: Time-filtered search for recent/dated queries
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from backend.utils.llm_utils import call_ollama_json


class RetrievalStrategy(Enum):
    """Available retrieval strategies"""
    PRECISE = "precise"       # BM25/keyword heavy
    SEMANTIC = "semantic"     # Vector/embedding heavy
    EXPLORATORY = "exploratory"  # Graph traversal
    TEMPORAL = "temporal"     # Time-filtered
    HYBRID = "hybrid"         # Combined approach


@dataclass
class StrategyDecision:
    """Result of strategy selection"""
    primary_strategy: RetrievalStrategy
    secondary_strategy: Optional[RetrievalStrategy]
    confidence: float
    reasoning: str
    weights: Dict[str, float]  # Weight for each strategy in hybrid


class AdaptiveRetriever:
    """
    Proteus - The Shape-Shifter
    
    The shape-shifting god - I adapt my form to best answer your query.
    
    Analyzes queries to determine the optimal retrieval strategy:
    - Precise queries get keyword search
    - Abstract queries get semantic search
    - Entity queries get graph traversal
    - Time-sensitive queries get temporal filtering
    """
    
    AGENT_NAME = "Proteus"
    AGENT_TITLE = "The Shape-Shifter"
    AGENT_DESCRIPTION = "The adaptive god - I choose the best search strategy"
    AGENT_ICON = "🔮"
    
    # Keywords indicating specific strategies
    PRECISE_INDICATORS = [
        "exact", "specific", "called", "named", "titled",
        "file", "document", "pdf", "report", '"'  # Quoted terms
    ]
    
    TEMPORAL_INDICATORS = [
        "recent", "latest", "newest", "last week", "last month",
        "today", "yesterday", "this year", "2023", "2024", "2025",
        "before", "after", "during", "between"
    ]
    
    EXPLORATORY_INDICATORS = [
        "related to", "connected", "similar", "like",
        "associated", "linked", "about the same"
    ]
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = f"{self.AGENT_NAME} ({self.AGENT_TITLE})"
        self.ollama_url = config['ollama']['base_url']
        self.model = config['ollama']['text_model']['name']
        
        logger.info(f"🔮 {self.name} initialized for adaptive retrieval")
    
    def classify_strategy(self, query: str) -> StrategyDecision:
        """
        Classify the optimal retrieval strategy for a query.
        
        Uses heuristics first, then LLM if ambiguous.
        
        Args:
            query: The search query
            
        Returns:
            StrategyDecision with recommended strategy
        """
        query_lower = query.lower()
        
        # Score each strategy
        scores = {
            RetrievalStrategy.PRECISE: 0.0,
            RetrievalStrategy.SEMANTIC: 0.0,
            RetrievalStrategy.EXPLORATORY: 0.0,
            RetrievalStrategy.TEMPORAL: 0.0
        }
        
        # Check for precise indicators
        for indicator in self.PRECISE_INDICATORS:
            if indicator in query_lower:
                scores[RetrievalStrategy.PRECISE] += 1.0
        
        # Check for temporal indicators
        for indicator in self.TEMPORAL_INDICATORS:
            if indicator in query_lower:
                scores[RetrievalStrategy.TEMPORAL] += 1.0
        
        # Check for exploratory indicators
        for indicator in self.EXPLORATORY_INDICATORS:
            if indicator in query_lower:
                scores[RetrievalStrategy.EXPLORATORY] += 1.0
        
        # Semantic is default for abstract queries
        # Short queries with no specific indicators lean semantic
        if len(query.split()) < 4 and max(scores.values()) < 1:
            scores[RetrievalStrategy.SEMANTIC] += 0.5
        
        # Questions lean semantic
        if query.endswith('?'):
            scores[RetrievalStrategy.SEMANTIC] += 0.5
        
        # Normalize scores
        total = sum(scores.values())
        if total > 0:
            for k in scores:
                scores[k] /= total
        else:
            # Default to hybrid
            scores = {s: 0.25 for s in scores}
        
        # Determine primary strategy
        primary = max(scores, key=scores.get)
        confidence = scores[primary]
        
        # Determine secondary strategy
        secondary = None
        remaining = {k: v for k, v in scores.items() if k != primary and v > 0.1}
        if remaining:
            secondary = max(remaining, key=remaining.get)
        
        # Generate reasoning
        reasoning_parts = []
        if scores[RetrievalStrategy.PRECISE] > 0.2:
            reasoning_parts.append("contains specific keywords")
        if scores[RetrievalStrategy.TEMPORAL] > 0.2:
            reasoning_parts.append("has temporal constraints")
        if scores[RetrievalStrategy.EXPLORATORY] > 0.2:
            reasoning_parts.append("seeks related information")
        if scores[RetrievalStrategy.SEMANTIC] > 0.2:
            reasoning_parts.append("requires semantic understanding")
        
        reasoning = f"Query {', '.join(reasoning_parts) or 'is general'}, using {primary.value} strategy."
        
        # Compute weights for hybrid
        weights = {s.value: round(v, 2) for s, v in scores.items()}
        
        return StrategyDecision(
            primary_strategy=primary,
            secondary_strategy=secondary,
            confidence=round(confidence, 2),
            reasoning=reasoning,
            weights=weights
        )
    
    async def classify_strategy_llm(self, query: str) -> StrategyDecision:
        """
        Use LLM to classify strategy for ambiguous queries.
        
        More accurate but slower than heuristics.
        """
        prompt = f"""Analyze this search query and determine the best retrieval strategy.

QUERY: "{query}"

STRATEGIES:
1. PRECISE: Best for queries looking for specific files/documents by name, exact terms, or keywords
2. SEMANTIC: Best for conceptual questions, understanding meaning, abstract topics
3. EXPLORATORY: Best for finding related entities, similar documents, connections
4. TEMPORAL: Best for time-sensitive queries (recent, last week, before date X)

Which strategy is best? Consider:
- Is the user looking for something specific or exploring?
- Are there time constraints?
- Is this about relationships between things?

Return JSON:
{{
    "primary_strategy": "PRECISE|SEMANTIC|EXPLORATORY|TEMPORAL",
    "secondary_strategy": "...|null",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}"""

        try:
            fallback = {
                "primary_strategy": "SEMANTIC",
                "secondary_strategy": None,
                "confidence": 0.5,
                "reasoning": "Default to semantic search"
            }
            
            result = await call_ollama_json(
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
            
            primary_str = result.get('primary_strategy', 'SEMANTIC').upper()
            primary = RetrievalStrategy[primary_str] if primary_str in RetrievalStrategy.__members__ else RetrievalStrategy.SEMANTIC
            
            secondary = None
            secondary_str = result.get('secondary_strategy')
            if secondary_str and secondary_str.upper() in RetrievalStrategy.__members__:
                secondary = RetrievalStrategy[secondary_str.upper()]
            
            return StrategyDecision(
                primary_strategy=primary,
                secondary_strategy=secondary,
                confidence=float(result.get('confidence', 0.5)),
                reasoning=result.get('reasoning', ''),
                weights={primary.value: 1.0}
            )
            
        except Exception as e:
            logger.error(f"LLM strategy classification failed: {e}")
            return self.classify_strategy(query)  # Fallback to heuristics
    
    def get_strategy_params(self, strategy: RetrievalStrategy) -> Dict[str, Any]:
        """
        Get search parameters for a given strategy.
        
        Returns:
            Dict with search parameters
        """
        params = {
            RetrievalStrategy.PRECISE: {
                "use_bm25": True,
                "use_vector": False,
                "bm25_weight": 1.0,
                "vector_weight": 0.0,
                "min_score": 0.5
            },
            RetrievalStrategy.SEMANTIC: {
                "use_bm25": True,
                "use_vector": True,
                "bm25_weight": 0.3,
                "vector_weight": 0.7,
                "min_score": 0.3
            },
            RetrievalStrategy.EXPLORATORY: {
                "use_bm25": True,
                "use_vector": True,
                "use_graph": True,
                "bm25_weight": 0.2,
                "vector_weight": 0.5,
                "graph_weight": 0.3,
                "expand_hops": 2,
                "min_score": 0.2
            },
            RetrievalStrategy.TEMPORAL: {
                "use_bm25": True,
                "use_vector": True,
                "bm25_weight": 0.4,
                "vector_weight": 0.4,
                "time_weight": 0.2,
                "prefer_recent": True,
                "min_score": 0.3
            },
            RetrievalStrategy.HYBRID: {
                "use_bm25": True,
                "use_vector": True,
                "bm25_weight": 0.5,
                "vector_weight": 0.5,
                "min_score": 0.3
            }
        }
        
        return params.get(strategy, params[RetrievalStrategy.HYBRID])
    
    def get_agent_info(self) -> Dict[str, str]:
        """Return agent information for UI display"""
        return {
            "name": self.AGENT_NAME,
            "title": self.AGENT_TITLE,
            "full_name": self.name,
            "description": self.AGENT_DESCRIPTION,
            "icon": self.AGENT_ICON,
            "role": "adaptive_retriever"
        }
