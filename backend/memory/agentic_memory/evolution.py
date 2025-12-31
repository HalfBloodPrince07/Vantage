# backend/memory/agentic_memory/evolution.py
"""
Memory Evolution - Linking and enrichment of agentic memories
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from loguru import logger

from .note import AgenticNote, VerificationStatus
from .opensearch_memory import AgenticMemoryStore
from backend.utils.llm_utils import call_ollama_with_retry


class MemoryEvolution:
    def __init__(
        self,
        store: AgenticMemoryStore,
        embedding_model,
        similarity_threshold: float = 0.7,
        max_links: int = 10,
        llm_model: str = "qwen3-vl:8b"
    ):
        self.store = store
        self.embedding_model = embedding_model
        self.threshold = similarity_threshold
        self.max_links = max_links
        self.llm_model = llm_model

    async def evolve_note(self, note: AgenticNote) -> AgenticNote:
        if note.embedding is None:
            note.embedding = await self._get_embedding(note.content)
        
        similar_notes = await self.store.search_by_vector(
            embedding=note.embedding,
            user_id=note.user_id,
            k=self.max_links + 5
        )
        
        for match in similar_notes:
            if match["id"] == note.id:
                continue
            if match["score"] >= self.threshold and len(note.links) < self.max_links:
                note.add_link(match["id"])
                await self._add_bidirectional_link(match["id"], note.id)
        
        if note.links:
            contradictions = await self._detect_contradictions(note, similar_notes[:3])
            for contra_id in contradictions:
                note.mark_contradicts(contra_id)
        
        if note.links and len(note.context) < 50:
            note.context = await self._enrich_context(note, similar_notes[:3])
        
        note.updated_at = datetime.utcnow().isoformat()
        return note

    async def _get_embedding(self, text: str) -> List[float]:
        try:
            return self.embedding_model.encode(text).tolist()
        except Exception as e:
            logger.error(f"Failed to get embedding: {e}")
            return [0.0] * 768

    async def _add_bidirectional_link(self, target_id: str, source_id: str) -> None:
        target_note = await self.store.get_note(target_id)
        if target_note and source_id not in target_note.links:
            target_note.add_link(source_id)
            await self.store.update_note(target_note)

    async def _detect_contradictions(
        self,
        note: AgenticNote,
        similar_notes: List[Dict]
    ) -> List[str]:
        if not similar_notes:
            return []
        
        similar_content = "\n".join([
            f"[{n['id'][:8]}]: {n.get('content', '')[:200]}"
            for n in similar_notes
        ])
        
        prompt = f"""Compare this new memory with existing memories and identify contradictions.

New memory: {note.content[:500]}

Existing memories:
{similar_content}

If any existing memory contradicts the new one, respond with just the IDs (first 8 chars) separated by commas.
If no contradictions, respond with "none".

Response:"""

        try:
            response = await call_ollama_with_retry(
                base_url="http://localhost:11434",
                model=self.llm_model,
                prompt=prompt,
                think=False
            )
            if "none" in response.lower():
                return []
            
            ids = [id.strip() for id in response.split(",") if len(id.strip()) >= 8]
            contradicting_ids = []
            for sim_note in similar_notes:
                if sim_note["id"][:8] in ids:
                    contradicting_ids.append(sim_note["id"])
            return contradicting_ids
        except Exception as e:
            logger.warning(f"Contradiction detection failed: {e}")
            return []

    async def _enrich_context(
        self,
        note: AgenticNote,
        related_notes: List[Dict]
    ) -> str:
        if not related_notes:
            return note.context
        
        related_content = "\n".join([
            f"- {n.get('context', n.get('content', '')[:100])}"
            for n in related_notes
        ])
        
        prompt = f"""Generate a brief context description for this memory, considering its related memories.

Memory: {note.content[:300]}

Related memories:
{related_content}

Write a 1-2 sentence context description that captures how this memory fits with related ones:"""

        try:
            response = await call_ollama_with_retry(
                base_url="http://localhost:11434",
                model=self.llm_model,
                prompt=prompt,
                think=False
            )
            return response.strip()[:500]
        except Exception as e:
            logger.warning(f"Context enrichment failed: {e}")
            return note.context

    async def create_causal_link(
        self,
        from_note_id: str,
        to_note_id: str
    ) -> bool:
        from_note = await self.store.get_note(from_note_id)
        if from_note:
            from_note.add_causal_link(to_note_id)
            await self.store.update_note(from_note)
            return True
        return False

    async def find_related_chain(
        self,
        note: AgenticNote,
        max_depth: int = 3
    ) -> List[AgenticNote]:
        chain = [note]
        visited = {note.id}
        current = note
        
        for _ in range(max_depth):
            if not current.links:
                break
            
            linked_notes = await self.store.get_linked_notes(current.id)
            unvisited = [n for n in linked_notes if n.id not in visited]
            
            if not unvisited:
                break
            
            best = max(unvisited, key=lambda n: n.importance)
            chain.append(best)
            visited.add(best.id)
            current = best
        
        return chain
