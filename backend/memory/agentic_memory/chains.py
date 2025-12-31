# backend/memory/agentic_memory/chains.py
"""
MemoryChain: Multi-hop reasoning across linked memories
"""

from typing import List, Dict, Any, Optional
from loguru import logger
import json

from backend.utils.llm_utils import call_ollama_with_retry
from .note import AgenticNote
from .opensearch_memory import AgenticMemoryStore


class MemoryChain:
    def __init__(
        self,
        store: AgenticMemoryStore,
        embedding_model,
        llm_model: str = "qwen3-vl:8b"
    ):
        self.store = store
        self.embedding_model = embedding_model
        self.llm_model = llm_model

    async def build_reasoning_chain(
        self,
        query: str,
        user_id: str,
        max_hops: int = 3
    ) -> List[AgenticNote]:
        query_embedding = self.embedding_model.encode(query).tolist()
        
        results = await self.store.search_by_vector(
            embedding=query_embedding,
            user_id=user_id,
            k=3
        )
        
        if not results:
            return []
        
        start_note = await self.store.get_note(results[0]["id"])
        if not start_note:
            return []
        
        chain = [start_note]
        visited = {start_note.id}
        current = start_note
        
        for _ in range(max_hops):
            next_note = await self._find_best_next_hop(current, query, visited)
            if next_note is None:
                break
            
            chain.append(next_note)
            visited.add(next_note.id)
            current = next_note
        
        return chain

    async def _find_best_next_hop(
        self,
        current: AgenticNote,
        query: str,
        visited: set
    ) -> Optional[AgenticNote]:
        linked_notes = await self.store.get_linked_notes(current.id)
        unvisited = [n for n in linked_notes if n.id not in visited]
        
        if not unvisited:
            return None
        
        best_note = None
        best_score = -1
        
        for note in unvisited:
            relevance = await self._score_relevance(note, query)
            combined_score = 0.7 * relevance + 0.3 * note.importance
            if combined_score > best_score:
                best_score = combined_score
                best_note = note
        
        return best_note if best_score > 0.3 else None

    async def _score_relevance(self, note: AgenticNote, query: str) -> float:
        query_words = set(query.lower().split())
        content_words = set(note.content.lower().split())
        keyword_set = set(kw.lower() for kw in note.keywords)
        
        overlap = len(query_words & (content_words | keyword_set))
        return min(1.0, overlap / max(len(query_words), 1))

    async def get_causal_path(
        self,
        start_id: str,
        end_id: str
    ) -> List[AgenticNote]:
        start = await self.store.get_note(start_id)
        if not start:
            return []
        
        path = [start]
        visited = {start_id}
        current = start
        
        for _ in range(10):
            if current.id == end_id:
                return path
            
            if not current.causal_links:
                break
            
            found_next = False
            for link_id in current.causal_links:
                if link_id not in visited:
                    next_note = await self.store.get_note(link_id)
                    if next_note:
                        path.append(next_note)
                        visited.add(link_id)
                        current = next_note
                        found_next = True
                        break
            
            if not found_next:
                break
        
        if path[-1].id == end_id:
            return path
        return []

    async def synthesize_chain_answer(
        self,
        chain: List[AgenticNote],
        query: str
    ) -> str:
        if not chain:
            return "No relevant memories found."
        
        chain_content = "\n".join([
            f"[{i+1}] {n.content[:300]}"
            for i, n in enumerate(chain)
        ])
        
        prompt = f"""Based on this chain of related memories, answer the question.

Question: {query}

Memory Chain:
{chain_content}

Synthesize an answer using information from the memory chain:"""

        try:
            response = await call_ollama_with_retry(
                base_url="http://localhost:11434",
                model=self.llm_model,
                prompt=prompt,
                think=True
            )
            return response.strip()
        except Exception as e:
            logger.error(f"Failed to synthesize answer: {e}")
            return chain[0].content
