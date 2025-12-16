# backend/memory/memory_reflector.py
"""
MemoryReflector - Periodic Memory Summarization
================================================
Implements memory reflection for MemGPT-style agentic memory.

Features:
- Periodic summarization of session interactions
- User preference extraction from patterns
- Memory importance scoring based on access patterns
- Session insight extraction
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

from backend.utils.llm_utils import call_ollama_json, call_ollama_with_retry


@dataclass
class SessionSummary:
    """Summary of a session's interactions"""
    session_id: str
    summary: str
    key_topics: List[str]
    user_intents: List[str]
    successful_queries: int
    total_queries: int
    insights: List[str]
    created_at: str


@dataclass
class UserPreferences:
    """Extracted user preferences"""
    user_id: str
    preferred_file_types: List[str]
    common_topics: List[str]
    search_patterns: Dict[str, Any]
    time_preferences: Dict[str, Any]  # When user typically searches
    confidence: float


@dataclass
class ScoredMemory:
    """Memory with computed importance score"""
    memory_id: str
    content: str
    computed_importance: float
    factors: Dict[str, float]  # Breakdown of score factors


class MemoryReflector:
    """
    Implements memory reflection and summarization.
    
    Periodically reflects on interactions to:
    - Summarize what happened in a session
    - Extract user preferences and patterns
    - Score memory importance for forgetting/prioritization
    """
    
    AGENT_NAME = "Mnemosyne"
    AGENT_TITLE = "The Rememberer"
    AGENT_DESCRIPTION = "Titaness of memory - I reflect on and consolidate memories"
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ollama_url = config['ollama']['base_url']
        self.model = config['ollama']['text_model']['name']
        
        # Importance scoring weights
        self.importance_weights = {
            "recency": 0.25,      # How recently accessed
            "frequency": 0.25,    # How often accessed
            "relevance": 0.30,   # Relevance to user's patterns
            "uniqueness": 0.20   # How unique/novel the memory is
        }
        
        logger.info(f"🧠 {self.AGENT_NAME} ({self.AGENT_TITLE}) initialized")
    
    async def reflect_on_session(
        self,
        session_id: str,
        interactions: List[Dict[str, Any]]
    ) -> SessionSummary:
        """
        Reflect on a session and generate summary.
        
        Args:
            session_id: Session identifier
            interactions: List of query/response pairs from the session
            
        Returns:
            SessionSummary with insights
        """
        if not interactions:
            return SessionSummary(
                session_id=session_id,
                summary="No interactions in this session.",
                key_topics=[],
                user_intents=[],
                successful_queries=0,
                total_queries=0,
                insights=[],
                created_at=datetime.utcnow().isoformat()
            )
        
        # Format interactions for LLM
        interaction_text = []
        successful = 0
        for i, interaction in enumerate(interactions[-10:], 1):  # Last 10
            query = interaction.get('query', '')
            response = interaction.get('response', '')[:200]
            results = interaction.get('results', [])
            
            interaction_text.append(f"{i}. Q: {query}\n   A: {response}\n   Results: {len(results)}")
            if results:
                successful += 1
        
        prompt = f"""Analyze this user session and provide a summary.

SESSION ID: {session_id}
INTERACTIONS:
{chr(10).join(interaction_text)}

Provide:
1. A brief summary of what the user was trying to accomplish
2. Key topics they searched for
3. Their apparent intents
4. Insights about their usage patterns

Return JSON:
{{
    "summary": "Brief summary of the session",
    "key_topics": ["topic1", "topic2"],
    "user_intents": ["intent1", "intent2"],
    "insights": ["insight1", "insight2"]
}}"""

        try:
            fallback = {
                "summary": f"Session with {len(interactions)} queries",
                "key_topics": [],
                "user_intents": [],
                "insights": []
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
            
            return SessionSummary(
                session_id=session_id,
                summary=result.get('summary', ''),
                key_topics=result.get('key_topics', []),
                user_intents=result.get('user_intents', []),
                successful_queries=successful,
                total_queries=len(interactions),
                insights=result.get('insights', []),
                created_at=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Session reflection failed: {e}")
            return SessionSummary(
                session_id=session_id,
                summary=f"Session with {len(interactions)} interactions",
                key_topics=[],
                user_intents=[],
                successful_queries=successful,
                total_queries=len(interactions),
                insights=[],
                created_at=datetime.utcnow().isoformat()
            )
    
    async def extract_user_preferences(
        self,
        user_id: str,
        interactions: List[Dict[str, Any]]
    ) -> UserPreferences:
        """
        Extract user preferences from interaction history.
        
        Args:
            user_id: User identifier
            interactions: Historical interactions
            
        Returns:
            UserPreferences with patterns
        """
        if not interactions:
            return UserPreferences(
                user_id=user_id,
                preferred_file_types=[],
                common_topics=[],
                search_patterns={},
                time_preferences={},
                confidence=0.0
            )
        
        # Analyze patterns
        file_types = {}
        topics = {}
        
        for interaction in interactions:
            query = interaction.get('query', '').lower()
            results = interaction.get('results', [])
            
            # Track file types from results
            for result in results:
                ftype = result.get('file_type', 'unknown')
                file_types[ftype] = file_types.get(ftype, 0) + 1
            
            # Simple topic extraction (could be enhanced with NLP)
            words = query.split()
            for word in words:
                if len(word) > 4 and word not in ['where', 'about', 'which', 'search']:
                    topics[word] = topics.get(word, 0) + 1
        
        # Sort by frequency
        preferred_types = sorted(file_types.keys(), key=lambda x: file_types[x], reverse=True)[:5]
        common_topics = sorted(topics.keys(), key=lambda x: topics[x], reverse=True)[:10]
        
        confidence = min(len(interactions) / 50.0, 1.0)  # More data = higher confidence
        
        return UserPreferences(
            user_id=user_id,
            preferred_file_types=preferred_types,
            common_topics=common_topics,
            search_patterns={"avg_query_length": sum(len(i.get('query', '')) for i in interactions) / len(interactions)},
            time_preferences={},  # Would need timestamps
            confidence=confidence
        )
    
    def compute_importance_scores(
        self,
        memories: List[Dict[str, Any]],
        current_context: Optional[Dict[str, Any]] = None
    ) -> List[ScoredMemory]:
        """
        Compute importance scores for memories.
        
        Used for:
        - Deciding what to forget/keep
        - Prioritizing memory retrieval
        - Memory consolidation
        
        Args:
            memories: List of memory entries
            current_context: Optional current context for relevance scoring
            
        Returns:
            List of ScoredMemory with computed scores
        """
        scored = []
        now = datetime.utcnow()
        
        # Get stats for normalization
        max_access = max(m.get('access_count', 1) for m in memories) if memories else 1
        
        for memory in memories:
            factors = {}
            
            # Recency factor (days since last access)
            last_accessed = memory.get('last_accessed', now.isoformat())
            try:
                last_dt = datetime.fromisoformat(last_accessed.replace('Z', '+00:00'))
                days_ago = (now - last_dt.replace(tzinfo=None)).days
                factors['recency'] = max(0, 1 - (days_ago / 30))  # Decay over 30 days
            except:
                factors['recency'] = 0.5
            
            # Frequency factor
            access_count = memory.get('access_count', 0)
            factors['frequency'] = min(access_count / max_access, 1.0) if max_access > 0 else 0
            
            # Base importance from storage
            factors['relevance'] = memory.get('importance', 0.5)
            
            # Uniqueness (inverse of how common this type is)
            factors['uniqueness'] = 0.5  # Would need more data to compute
            
            # Weighted sum
            total = sum(
                factors[k] * self.importance_weights[k]
                for k in self.importance_weights
            )
            
            scored.append(ScoredMemory(
                memory_id=memory.get('id', ''),
                content=memory.get('content', ''),
                computed_importance=round(total, 3),
                factors=factors
            ))
        
        # Sort by importance
        scored.sort(key=lambda x: x.computed_importance, reverse=True)
        
        return scored
    
    async def consolidate_memories(
        self,
        memories: List[Dict[str, Any]],
        max_memories: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Consolidate memories by removing low-importance ones.
        
        Called periodically to prevent memory bloat.
        
        Args:
            memories: All memories
            max_memories: Maximum to keep
            
        Returns:
            Consolidated list of memories
        """
        if len(memories) <= max_memories:
            return memories
        
        scored = self.compute_importance_scores(memories)
        
        # Keep top N by importance
        to_keep = {s.memory_id for s in scored[:max_memories]}
        
        consolidated = [m for m in memories if m.get('id') in to_keep]
        
        logger.info(f"🧠 Consolidated memories: {len(memories)} -> {len(consolidated)}")
        return consolidated
    
    def get_agent_info(self) -> Dict[str, str]:
        """Return agent information for UI display"""
        return {
            "name": self.AGENT_NAME,
            "title": self.AGENT_TITLE,
            "full_name": f"{self.AGENT_NAME} ({self.AGENT_TITLE})",
            "description": self.AGENT_DESCRIPTION,
            "icon": "🧠",
            "role": "memory_reflector"
        }
