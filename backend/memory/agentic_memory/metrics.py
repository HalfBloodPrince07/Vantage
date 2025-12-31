# backend/memory/agentic_memory/metrics.py
"""
Memory Metrics - Performance monitoring and statistics
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import time
from loguru import logger

from .opensearch_memory import AgenticMemoryStore


class MemoryMetrics:
    def __init__(self, store: AgenticMemoryStore):
        self.store = store
        self._search_latencies: List[float] = []
        self._max_latency_samples = 1000

    async def get_stats(self, user_id: str = None) -> Dict[str, Any]:
        total = await self.store.count_notes(user_id)
        
        notes = await self.store.get_user_notes(user_id or "", limit=500) if user_id else []
        
        type_counts = {}
        total_links = 0
        for note in notes:
            note_type = note.note_type.value if hasattr(note.note_type, 'value') else note.note_type
            type_counts[note_type] = type_counts.get(note_type, 0) + 1
            total_links += len(note.links)
        
        avg_links = total_links / len(notes) if notes else 0
        
        now = datetime.utcnow()
        day_ago = (now - timedelta(days=1)).isoformat()
        recent = [n for n in notes if n.created_at >= day_ago]
        
        return {
            "total_notes": total,
            "notes_by_type": type_counts,
            "avg_links_per_note": round(avg_links, 2),
            "memory_growth_24h": len(recent),
            "search_latency_ms": self.avg_search_latency,
            "latency_p95_ms": self.p95_search_latency,
            "timestamp": now.isoformat()
        }

    def log_search_performance(
        self,
        query: str,
        results_count: int,
        latency_ms: float
    ) -> None:
        self._search_latencies.append(latency_ms)
        if len(self._search_latencies) > self._max_latency_samples:
            self._search_latencies = self._search_latencies[-self._max_latency_samples:]
        
        logger.debug(f"Memory search: '{query[:30]}...' => {results_count} results in {latency_ms:.1f}ms")

    @property
    def avg_search_latency(self) -> float:
        if not self._search_latencies:
            return 0
        return round(sum(self._search_latencies) / len(self._search_latencies), 2)

    @property
    def p95_search_latency(self) -> float:
        if not self._search_latencies:
            return 0
        sorted_latencies = sorted(self._search_latencies)
        idx = int(len(sorted_latencies) * 0.95)
        return round(sorted_latencies[idx], 2)

    async def get_index_size_mb(self) -> float:
        try:
            result = await self.store.client.client.indices.stats(index=self.store.index_name)
            size_bytes = result["indices"][self.store.index_name]["total"]["store"]["size_in_bytes"]
            return round(size_bytes / (1024 * 1024), 2)
        except Exception as e:
            logger.error(f"Failed to get index size: {e}")
            return 0

    def measure_latency(self):
        return LatencyContext(self)


class LatencyContext:
    def __init__(self, metrics: MemoryMetrics):
        self.metrics = metrics
        self.start = None
        self.query = ""
        self.results = 0

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        elapsed = (time.perf_counter() - self.start) * 1000
        self.metrics.log_search_performance(self.query, self.results, elapsed)

    def set_context(self, query: str, results: int):
        self.query = query
        self.results = results
