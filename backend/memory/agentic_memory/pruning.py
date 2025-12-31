# backend/memory/agentic_memory/pruning.py
"""
Memory Pruning - Decay and cleanup of old/unused memories
"""

from typing import List, Optional
from datetime import datetime, timedelta
from loguru import logger

from .note import AgenticNote
from .opensearch_memory import AgenticMemoryStore


class MemoryPruner:
    def __init__(
        self,
        store: AgenticMemoryStore,
        max_notes: int = 10000,
        decay_rate: float = 0.01,
        min_importance: float = 0.1,
        prune_after_days: int = 30
    ):
        self.store = store
        self.max_notes = max_notes
        self.decay_rate = decay_rate
        self.min_importance = min_importance
        self.prune_after_days = prune_after_days

    async def apply_decay(self, user_id: str) -> int:
        notes = await self.store.get_user_notes(user_id, limit=500)
        updated_count = 0
        now = datetime.utcnow()
        
        for note in notes:
            try:
                updated_at = datetime.fromisoformat(note.updated_at.replace('Z', '+00:00').replace('+00:00', ''))
            except:
                continue
            
            days_since_access = (now - updated_at).days
            if days_since_access <= 0:
                continue
            
            decay = self.decay_rate * days_since_access
            new_importance = max(self.min_importance, note.importance - decay)
            
            if abs(new_importance - note.importance) > 0.001:
                note.importance = new_importance
                await self.store.update_note(note)
                updated_count += 1
        
        logger.info(f"Applied decay to {updated_count} notes for user {user_id}")
        return updated_count

    async def prune_old_notes(self, user_id: str) -> int:
        cutoff = datetime.utcnow() - timedelta(days=self.prune_after_days)
        cutoff_str = cutoff.isoformat()
        
        candidates = await self.store.get_notes_by_importance(
            user_id=user_id,
            max_importance=0.3,
            limit=200
        )
        
        pruned = 0
        for note in candidates:
            if note.updated_at >= cutoff_str:
                continue
            if len(note.links) >= 3:
                continue
            if note.note_type.value == "consolidated":
                continue
            
            await self.store.delete_note(note.id)
            pruned += 1
            logger.debug(f"Pruned low-importance note: {note.id}")
        
        logger.info(f"Pruned {pruned} old/low-importance notes for user {user_id}")
        return pruned

    async def enforce_limit(self, user_id: str) -> int:
        count = await self.store.count_notes(user_id)
        if count <= self.max_notes:
            return 0
        
        excess = count - self.max_notes
        
        low_importance = await self.store.get_notes_by_importance(
            user_id=user_id,
            max_importance=0.5,
            limit=excess + 50
        )
        
        pruned = 0
        for note in low_importance:
            if pruned >= excess:
                break
            if len(note.links) < 2 and note.access_count < 3:
                await self.store.delete_note(note.id)
                pruned += 1
        
        logger.info(f"Enforced limit: pruned {pruned} notes (was {count}, limit {self.max_notes})")
        return pruned

    async def run_full_maintenance(self, user_id: str) -> dict:
        decay_count = await self.apply_decay(user_id)
        prune_count = await self.prune_old_notes(user_id)
        limit_count = await self.enforce_limit(user_id)
        
        return {
            "decayed": decay_count,
            "pruned": prune_count,
            "limit_enforced": limit_count
        }
