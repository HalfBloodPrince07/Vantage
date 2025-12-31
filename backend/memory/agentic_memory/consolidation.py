# backend/memory/agentic_memory/consolidation.py
"""
MemoryConsolidator: Cluster and summarize related memories
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger
import numpy as np
import json

from backend.utils.llm_utils import call_ollama_with_retry
from .note import AgenticNote, NoteType, Modality, SourceType
from .opensearch_memory import AgenticMemoryStore


class MemoryConsolidator:
    def __init__(
        self,
        store: AgenticMemoryStore,
        embedding_model,
        min_cluster_size: int = 3,
        llm_model: str = "qwen3-vl:8b"
    ):
        self.store = store
        self.embedding_model = embedding_model
        self.min_cluster_size = min_cluster_size
        self.llm_model = llm_model

    async def find_clusters(
        self,
        user_id: str,
        similarity_threshold: float = 0.75
    ) -> List[List[AgenticNote]]:
        notes = await self.store.get_user_notes(user_id, limit=500)
        notes_with_embeddings = [n for n in notes if n.embedding]
        
        if len(notes_with_embeddings) < self.min_cluster_size:
            return []
        
        embeddings = np.array([n.embedding for n in notes_with_embeddings])
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normalized = embeddings / (norms + 1e-10)
        similarity_matrix = np.dot(normalized, normalized.T)
        
        visited = set()
        clusters = []
        
        for i, note in enumerate(notes_with_embeddings):
            if i in visited:
                continue
            
            cluster = [note]
            visited.add(i)
            
            for j in range(len(notes_with_embeddings)):
                if j not in visited and similarity_matrix[i, j] >= similarity_threshold:
                    cluster.append(notes_with_embeddings[j])
                    visited.add(j)
            
            if len(cluster) >= self.min_cluster_size:
                clusters.append(cluster)
        
        return clusters

    async def consolidate_cluster(
        self,
        notes: List[AgenticNote]
    ) -> Optional[AgenticNote]:
        if len(notes) < 2:
            return None
        
        combined_content = "\n---\n".join([n.content[:500] for n in notes])
        
        prompt = f"""Summarize these related memories into a single comprehensive note.

Memories:
{combined_content}

Create a consolidated summary that captures the key information from all memories.
Keep it concise but comprehensive (2-4 sentences):"""

        try:
            summary = await call_ollama_with_retry(
                base_url="http://localhost:11434",
                model=self.llm_model,
                prompt=prompt,
                think=False
            )
            
            all_keywords = set()
            all_tags = set()
            for note in notes:
                all_keywords.update(note.keywords)
                all_tags.update(note.tags)
            
            consolidated = AgenticNote(
                content=summary.strip(),
                user_id=notes[0].user_id,
                context=f"Consolidated from {len(notes)} related memories",
                keywords=list(all_keywords)[:10],
                tags=list(all_tags)[:5],
                links=[n.id for n in notes],
                importance=max(n.importance for n in notes),
                confidence=sum(n.confidence for n in notes) / len(notes),
                note_type=NoteType.CONSOLIDATED
            )
            
            consolidated.embedding = await self._get_embedding(summary)
            
            return consolidated
        except Exception as e:
            logger.error(f"Failed to consolidate cluster: {e}")
            return None

    async def _get_embedding(self, text: str) -> List[float]:
        try:
            return self.embedding_model.encode(text).tolist()
        except Exception as e:
            logger.error(f"Failed to get embedding: {e}")
            return [0.0] * 768

    async def run_consolidation(
        self,
        user_id: str,
        similarity_threshold: float = 0.75
    ) -> List[AgenticNote]:
        clusters = await self.find_clusters(user_id, similarity_threshold)
        consolidated_notes = []
        
        for cluster in clusters:
            consolidated = await self.consolidate_cluster(cluster)
            if consolidated:
                await self.store.store_note(consolidated)
                consolidated_notes.append(consolidated)
                logger.info(f"Created consolidated note from {len(cluster)} memories")
        
        return consolidated_notes
