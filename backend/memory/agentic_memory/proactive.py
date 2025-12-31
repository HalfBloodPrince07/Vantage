# backend/memory/agentic_memory/proactive.py
"""
Proactive Memory Suggestions - Surface relevant underutilized memories
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

from .note import AgenticNote
from .opensearch_memory import AgenticMemoryStore


class MemoryProactiveSuggester:
    def __init__(
        self,
        store: AgenticMemoryStore,
        embedding_model,
        suggestion_threshold: float = 0.6,
        max_suggestions: int = 5
    ):
        self.store = store
        self.embedding_model = embedding_model
        self.threshold = suggestion_threshold
        self.max_suggestions = max_suggestions

    async def suggest_relevant_memories(
        self,
        current_context: str,
        user_id: str
    ) -> List[AgenticNote]:
        context_embedding = self.embedding_model.encode(current_context).tolist()
        
        results = await self.store.search_by_vector(
            embedding=context_embedding,
            user_id=user_id,
            k=20
        )
        
        suggestions = []
        for result in results:
            if result["score"] >= self.threshold:
                importance = result.get("importance", 0.5)
                access_count = result.get("access_count", 0)
                
                if importance > 0.5 and access_count < 5:
                    note = await self.store.get_note(result["id"])
                    if note:
                        suggestions.append(note)
                        if len(suggestions) >= self.max_suggestions:
                            break
        
        return suggestions

    async def detect_knowledge_gaps(
        self,
        recent_queries: List[str],
        user_id: str
    ) -> List[Dict[str, Any]]:
        gaps = []
        
        for query in recent_queries:
            query_embedding = self.embedding_model.encode(query).tolist()
            results = await self.store.search_by_vector(
                embedding=query_embedding,
                user_id=user_id,
                k=3
            )
            
            if not results or results[0]["score"] < 0.5:
                gaps.append({
                    "query": query,
                    "coverage": results[0]["score"] if results else 0,
                    "suggestion": f"Consider adding memories about: {query}"
                })
        
        return gaps

    async def find_stale_clusters(
        self,
        user_id: str,
        stale_days: int = 30
    ) -> List[List[AgenticNote]]:
        cutoff = datetime.utcnow() - timedelta(days=stale_days)
        cutoff_str = cutoff.isoformat()
        
        notes = await self.store.get_user_notes(user_id, limit=200)
        
        stale_notes = [
            n for n in notes
            if n.updated_at < cutoff_str and n.access_count < 3
        ]
        
        clusters = []
        visited = set()
        
        for note in stale_notes:
            if note.id in visited:
                continue
            
            cluster = [note]
            visited.add(note.id)
            
            for link_id in note.links:
                if link_id not in visited:
                    linked = await self.store.get_note(link_id)
                    if linked and linked.updated_at < cutoff_str:
                        cluster.append(linked)
                        visited.add(link_id)
            
            if len(cluster) >= 2:
                clusters.append(cluster)
        
        return clusters

    async def get_hot_topics(
        self,
        user_id: str,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        cutoff = datetime.utcnow() - timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        
        notes = await self.store.get_user_notes(user_id, limit=100)
        recent = [n for n in notes if n.updated_at >= cutoff_str]
        
        tag_counts = {}
        keyword_counts = {}
        
        for note in recent:
            for tag in note.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            for kw in note.keywords:
                keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
        
        hot_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        hot_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return [
            {"type": "tag", "topic": t[0], "count": t[1]} for t in hot_tags
        ] + [
            {"type": "keyword", "topic": k[0], "count": k[1]} for k in hot_keywords
        ]
