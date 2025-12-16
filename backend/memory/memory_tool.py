# backend/memory/memory_tool.py
"""
MemoryTool - Agent-Callable Memory Interface
=============================================
Enables agents to explicitly query and update memory during task execution.

This transforms passive memory into an active tool that agents can use:
- Search past interactions for relevant context
- Store discovered insights for future use
- Update user preferences
- Track query patterns
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json
from loguru import logger


@dataclass
class Memory:
    """A memory entry"""
    id: str
    content: str
    memory_type: str  # insight, preference, fact, query_pattern
    importance: float  # 0.0-1.0
    created_at: str
    last_accessed: str
    access_count: int
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class UserContext:
    """Aggregated context about a user"""
    user_id: str
    preferences: Dict[str, Any]
    recent_queries: List[str]
    frequent_topics: List[str]
    interaction_count: int
    avg_session_length: float
    last_seen: str


class MemoryTool:
    """
    Agent-callable memory interface.
    
    Allows agents to:
    - Search memories by semantic similarity
    - Store new insights discovered during processing
    - Get aggregated user context
    - Update memory importance based on usage
    """
    
    def __init__(self, memory_manager):
        """
        Initialize with a MemoryManager instance.
        
        Args:
            memory_manager: The main MemoryManager from backend/memory/
        """
        self.memory = memory_manager
        self._insight_cache: Dict[str, Memory] = {}
        
        logger.info("🧠 MemoryTool initialized for agent access")
    
    async def search_memory(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        memory_types: Optional[List[str]] = None,
        limit: int = 5
    ) -> List[Memory]:
        """
        Search memories for relevant past interactions.
        
        Called by agents when they need context from past conversations.
        
        Args:
            query: What to search for
            user_id: Optional user filter
            session_id: Optional session filter
            memory_types: Filter by types (insight, preference, fact, query_pattern)
            limit: Max results
            
        Returns:
            List of relevant Memory objects
        """
        try:
            # Get session context with recent queries
            context = await self.memory.get_context(session_id) if session_id else {}
            
            # Search through recent queries for matches
            recent_queries = context.get('recent_queries', [])
            relevant_memories = []
            
            query_lower = query.lower()
            
            # Simple keyword matching (could be enhanced with embeddings)
            for past_query in recent_queries:
                if any(term in past_query.lower() for term in query_lower.split()):
                    relevant_memories.append(Memory(
                        id=f"query_{len(relevant_memories)}",
                        content=past_query,
                        memory_type="query_pattern",
                        importance=0.6,
                        created_at=datetime.utcnow().isoformat(),
                        last_accessed=datetime.utcnow().isoformat(),
                        access_count=1,
                        metadata={"source": "session_context"}
                    ))
            
            # Add cached insights
            for insight_id, insight in self._insight_cache.items():
                if memory_types is None or insight.memory_type in memory_types:
                    if query_lower in insight.content.lower():
                        insight.access_count += 1
                        insight.last_accessed = datetime.utcnow().isoformat()
                        relevant_memories.append(insight)
            
            logger.info(f"🧠 MemoryTool.search_memory found {len(relevant_memories)} relevant memories")
            return relevant_memories[:limit]
            
        except Exception as e:
            logger.error(f"MemoryTool search failed: {e}")
            return []
    
    async def store_insight(
        self,
        insight: str,
        importance: float = 0.5,
        insight_type: str = "insight",
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Memory:
        """
        Store a discovered insight for future use.
        
        Called by agents when they discover something worth remembering.
        
        Args:
            insight: The insight text to store
            importance: How important is this (0.0-1.0)
            insight_type: Type of insight (insight, fact, preference, observation)
            user_id: Optional user association
            metadata: Additional data about the insight
            
        Returns:
            The created Memory object
        """
        memory_id = f"insight_{datetime.utcnow().timestamp()}"
        
        memory = Memory(
            id=memory_id,
            content=insight,
            memory_type=insight_type,
            importance=min(max(importance, 0.0), 1.0),
            created_at=datetime.utcnow().isoformat(),
            last_accessed=datetime.utcnow().isoformat(),
            access_count=0,
            metadata={
                "user_id": user_id,
                **(metadata or {})
            }
        )
        
        self._insight_cache[memory_id] = memory
        
        logger.info(f"🧠 MemoryTool stored insight: '{insight[:50]}...' (importance: {importance:.2f})")
        return memory
    
    async def get_user_context(self, user_id: str) -> UserContext:
        """
        Get aggregated context about a user.
        
        Called by agents to understand user patterns and preferences.
        
        Args:
            user_id: User identifier
            
        Returns:
            UserContext with preferences, patterns, and stats
        """
        try:
            # Get preferences from memory manager
            prefs = await self.memory.get_user_preferences(user_id)
            
            # Build context
            context = UserContext(
                user_id=user_id,
                preferences=prefs or {},
                recent_queries=[],  # Would come from session data
                frequent_topics=prefs.get('preferred_file_types', []) if prefs else [],
                interaction_count=prefs.get('total_searches', 0) if prefs else 0,
                avg_session_length=0.0,
                last_seen=datetime.utcnow().isoformat()
            )
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to get user context: {e}")
            return UserContext(
                user_id=user_id,
                preferences={},
                recent_queries=[],
                frequent_topics=[],
                interaction_count=0,
                avg_session_length=0.0,
                last_seen=datetime.utcnow().isoformat()
            )
    
    async def update_memory(
        self,
        memory_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update an existing memory entry.
        
        Args:
            memory_id: ID of memory to update
            updates: Fields to update
            
        Returns:
            True if updated successfully
        """
        if memory_id in self._insight_cache:
            memory = self._insight_cache[memory_id]
            
            if 'content' in updates:
                memory.content = updates['content']
            if 'importance' in updates:
                memory.importance = updates['importance']
            if 'metadata' in updates:
                memory.metadata.update(updates['metadata'])
            
            memory.last_accessed = datetime.utcnow().isoformat()
            
            logger.info(f"🧠 MemoryTool updated memory {memory_id}")
            return True
        
        return False
    
    async def forget_memory(self, memory_id: str) -> bool:
        """
        Remove a memory entry.
        
        Args:
            memory_id: ID of memory to remove
            
        Returns:
            True if removed
        """
        if memory_id in self._insight_cache:
            del self._insight_cache[memory_id]
            logger.info(f"🧠 MemoryTool forgot memory {memory_id}")
            return True
        return False
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about stored memories"""
        if not self._insight_cache:
            return {"total_memories": 0, "by_type": {}}
        
        by_type = {}
        total_importance = 0.0
        
        for memory in self._insight_cache.values():
            by_type[memory.memory_type] = by_type.get(memory.memory_type, 0) + 1
            total_importance += memory.importance
        
        return {
            "total_memories": len(self._insight_cache),
            "by_type": by_type,
            "avg_importance": total_importance / len(self._insight_cache) if self._insight_cache else 0
        }
