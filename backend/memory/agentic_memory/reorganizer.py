# backend/memory/agentic_memory/reorganizer.py
"""
Memory Reorganizer - Periodic re-evolution of memories
"""

from typing import List
from datetime import datetime
from loguru import logger

from .note import AgenticNote
from .opensearch_memory import AgenticMemoryStore
from .evolution import MemoryEvolution


class MemoryReorganizer:
    def __init__(
        self,
        store: AgenticMemoryStore,
        evolution: MemoryEvolution,
        batch_size: int = 100
    ):
        self.store = store
        self.evolution = evolution
        self.batch_size = batch_size

    async def re_evolve_all(self, user_id: str) -> dict:
        total_notes = 0
        new_links_created = 0
        offset = 0
        
        while True:
            notes = await self.store.get_user_notes(
                user_id=user_id,
                limit=self.batch_size,
                offset=offset
            )
            
            if not notes:
                break
            
            for note in notes:
                original_link_count = len(note.links)
                evolved = await self.evolution.evolve_note(note)
                new_links = len(evolved.links) - original_link_count
                
                if new_links > 0:
                    await self.store.update_note(evolved)
                    new_links_created += new_links
                    logger.debug(f"Re-evolved note {note.id}: +{new_links} links")
                
                total_notes += 1
            
            offset += self.batch_size
        
        logger.info(f"Re-evolution complete: {total_notes} notes, {new_links_created} new links")
        return {
            "notes_processed": total_notes,
            "new_links_created": new_links_created
        }

    async def re_evolve_recent(
        self,
        user_id: str,
        days: int = 7
    ) -> dict:
        cutoff = datetime.utcnow().isoformat()
        notes = await self.store.get_user_notes(user_id, limit=200)
        
        recent = [n for n in notes if n.created_at >= cutoff or n.updated_at >= cutoff]
        
        new_links = 0
        for note in recent:
            original = len(note.links)
            evolved = await self.evolution.evolve_note(note)
            added = len(evolved.links) - original
            if added > 0:
                await self.store.update_note(evolved)
                new_links += added
        
        return {
            "notes_processed": len(recent),
            "new_links_created": new_links
        }

    async def find_orphan_notes(self, user_id: str) -> List[AgenticNote]:
        notes = await self.store.get_user_notes(user_id, limit=500)
        return [n for n in notes if not n.links and n.access_count < 2]

    async def connect_orphans(self, user_id: str) -> int:
        orphans = await self.find_orphan_notes(user_id)
        connected = 0
        
        for orphan in orphans:
            evolved = await self.evolution.evolve_note(orphan)
            if evolved.links:
                await self.store.update_note(evolved)
                connected += 1
        
        logger.info(f"Connected {connected} orphan notes for user {user_id}")
        return connected
