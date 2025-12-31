# backend/memory/agentic_memory/system.py
"""
Unified Agentic Memory System - Main integration point
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from .note import AgenticNote, NoteType, Modality, SourceType
from .opensearch_memory import AgenticMemoryStore
from .note_generator import NoteGenerator
from .evolution import MemoryEvolution
from .consolidation import MemoryConsolidator
from .chains import MemoryChain
from .multimodal import MultiModalMemory, CrossModalSearch
from .proactive import MemoryProactiveSuggester
from .nl_interface import MemoryNLInterface
from .metrics import MemoryMetrics
from .tuning import ThresholdTuner
from .pruning import MemoryPruner
from .reorganizer import MemoryReorganizer


class AgenticMemorySystem:
    def __init__(
        self,
        opensearch_client,
        embedding_model,
        config: Dict[str, Any]
    ):
        self.config = config.get("agentic_memory", {})
        self.enabled = self.config.get("enabled", True)
        
        index_name = self.config.get("index_name", "vantage_memories")
        self.store = AgenticMemoryStore(opensearch_client, index_name)
        self.embedding_model = embedding_model
        
        llm_model = self.config.get("generation", {}).get("model", "qwen3-vl:8b")
        
        self.generator = NoteGenerator(llm_model)
        self.evolution = MemoryEvolution(
            self.store, embedding_model,
            similarity_threshold=self.config.get("evolution", {}).get("similarity_threshold", 0.7),
            max_links=self.config.get("evolution", {}).get("max_links_per_note", 10),
            llm_model=llm_model
        )
        self.consolidator = MemoryConsolidator(
            self.store, embedding_model,
            min_cluster_size=self.config.get("consolidation", {}).get("min_cluster_size", 3),
            llm_model=llm_model
        )
        self.chains = MemoryChain(self.store, embedding_model, llm_model)
        self.multimodal = MultiModalMemory(self.store, embedding_model)
        self.cross_modal = CrossModalSearch(self.store, embedding_model)
        self.proactive = MemoryProactiveSuggester(
            self.store, embedding_model,
            suggestion_threshold=self.config.get("proactive", {}).get("suggestion_threshold", 0.6),
            max_suggestions=self.config.get("proactive", {}).get("max_suggestions", 5)
        )
        self.nl_interface = MemoryNLInterface(self.store, embedding_model, llm_model)
        self.metrics = MemoryMetrics(self.store)
        self.tuner = ThresholdTuner(
            initial_threshold=self.config.get("evolution", {}).get("similarity_threshold", 0.7)
        )
        self.pruner = MemoryPruner(
            self.store,
            max_notes=self.config.get("pruning", {}).get("max_notes", 10000),
            decay_rate=self.config.get("pruning", {}).get("decay_rate", 0.01),
            prune_after_days=self.config.get("pruning", {}).get("prune_after_days", 30)
        )
        self.reorganizer = MemoryReorganizer(self.store, self.evolution)

    async def initialize(self) -> bool:
        if not self.enabled:
            logger.info("Agentic memory is disabled")
            return False
        return await self.store.create_index()

    async def add_note(
        self,
        content: str,
        user_id: str,
        note_type: str = "insight",
        session_id: Optional[str] = None,
        **kwargs
    ) -> AgenticNote:
        attrs = await self.generator.generate_note_attributes(content)
        confidence = await self.generator.assess_confidence(content, kwargs.get("source_type", "user_input"))
        
        note = AgenticNote(
            content=content,
            user_id=user_id,
            context=attrs.get("context", ""),
            keywords=attrs.get("keywords", []),
            tags=attrs.get("tags", []),
            importance=attrs.get("importance", 0.5),
            confidence=confidence,
            session_id=session_id,
            note_type=NoteType(note_type) if isinstance(note_type, str) else note_type,
            **kwargs
        )
        
        note.embedding = self.embedding_model.encode(content).tolist()
        note = await self.evolution.evolve_note(note)
        await self.store.store_note(note)
        
        logger.info(f"Added agentic note: {note.id} ({note.note_type.value})")
        return note

    async def search(
        self,
        query: str,
        user_id: str,
        k: int = 5,
        use_chain: bool = False
    ) -> List[Dict[str, Any]]:
        import time
        start = time.perf_counter()
        
        if use_chain:
            chain = await self.chains.build_reasoning_chain(query, user_id, max_hops=3)
            results = [n.to_dict() for n in chain]
        else:
            query_embedding = self.embedding_model.encode(query).tolist()
            results = await self.store.search_by_vector(query_embedding, user_id, k)
        
        latency = (time.perf_counter() - start) * 1000
        self.metrics.log_search_performance(query, len(results), latency)
        
        for r in results:
            note = await self.store.get_note(r.get("id"))
            if note:
                note.increment_access()
                await self.store.update_note(note)
        
        return results

    async def process_command(self, command: str, user_id: str) -> Dict[str, Any]:
        return await self.nl_interface.process_command(command, user_id)

    async def get_graph_data(self, user_id: str) -> Dict[str, Any]:
        notes = await self.store.get_user_notes(user_id, limit=200)
        
        nodes = [n.to_dict() for n in notes]
        edges = []
        
        for note in notes:
            for link_id in note.links:
                edges.append({
                    "source": note.id,
                    "target": link_id,
                    "strength": 0.5
                })
        
        return {"nodes": nodes, "edges": edges}

    async def get_stats(self, user_id: str = None) -> Dict[str, Any]:
        return await self.metrics.get_stats(user_id)

    async def get_insights(self, user_id: str, recent_queries: List[str] = None) -> Dict[str, Any]:
        gaps = await self.proactive.detect_knowledge_gaps(recent_queries or [], user_id)
        stale = await self.proactive.find_stale_clusters(user_id)
        hot = await self.proactive.get_hot_topics(user_id)
        
        return {
            "gaps": gaps,
            "staleClusters": [[n.to_dict() for n in c] for c in stale],
            "hotTopics": hot
        }

    async def run_maintenance(self, user_id: str) -> Dict[str, Any]:
        self.evolution.threshold = self.tuner.get_optimal_threshold()
        prune_result = await self.pruner.run_full_maintenance(user_id)
        reorg_result = await self.reorganizer.re_evolve_recent(user_id)
        
        if self.config.get("consolidation", {}).get("enabled", True):
            consolidated = await self.consolidator.run_consolidation(user_id)
            prune_result["consolidated"] = len(consolidated)
        
        return {**prune_result, **reorg_result}
