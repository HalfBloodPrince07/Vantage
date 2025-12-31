# backend/memory/agentic_memory/tuning.py
"""
Adaptive Threshold Tuning - Learn optimal parameters from feedback
"""

from typing import List, Tuple, Dict, Any
from datetime import datetime, timedelta
from loguru import logger


class ThresholdTuner:
    def __init__(
        self,
        initial_threshold: float = 0.7,
        min_feedback: int = 50
    ):
        self.current_threshold = initial_threshold
        self.min_feedback = min_feedback
        self.link_feedback: List[Tuple[str, bool, datetime]] = []
        self.search_feedback: List[Tuple[str, float, bool]] = []

    def record_link_quality(self, link_id: str, was_useful: bool) -> None:
        self.link_feedback.append((link_id, was_useful, datetime.utcnow()))
        if len(self.link_feedback) > 1000:
            self.link_feedback = self.link_feedback[-500:]

    def record_search_feedback(
        self,
        query: str,
        relevance_score: float,
        was_helpful: bool
    ) -> None:
        self.search_feedback.append((query, relevance_score, was_helpful))
        if len(self.search_feedback) > 1000:
            self.search_feedback = self.search_feedback[-500:]

    def get_optimal_threshold(self) -> float:
        if len(self.link_feedback) < self.min_feedback:
            return self.current_threshold
        
        recent = self.link_feedback[-100:]
        useful_count = sum(1 for _, useful, _ in recent if useful)
        success_rate = useful_count / len(recent)
        
        if success_rate < 0.6:
            new_threshold = min(0.85, self.current_threshold + 0.03)
        elif success_rate > 0.8:
            new_threshold = max(0.5, self.current_threshold - 0.03)
        else:
            new_threshold = self.current_threshold
        
        if abs(new_threshold - self.current_threshold) > 0.01:
            logger.info(f"Threshold tuned: {self.current_threshold:.2f} -> {new_threshold:.2f} (success rate: {success_rate:.2%})")
            self.current_threshold = new_threshold
        
        return self.current_threshold

    def get_stats(self) -> Dict[str, Any]:
        total_link_feedback = len(self.link_feedback)
        recent_link = self.link_feedback[-100:] if self.link_feedback else []
        link_success = sum(1 for _, u, _ in recent_link if u) / len(recent_link) if recent_link else 0
        
        total_search_feedback = len(self.search_feedback)
        recent_search = self.search_feedback[-100:] if self.search_feedback else []
        search_success = sum(1 for _, _, h in recent_search if h) / len(recent_search) if recent_search else 0
        
        return {
            "current_threshold": self.current_threshold,
            "total_link_feedback": total_link_feedback,
            "link_success_rate": round(link_success, 3),
            "total_search_feedback": total_search_feedback,
            "search_success_rate": round(search_success, 3)
        }

    def reset(self, initial_threshold: float = 0.7) -> None:
        self.current_threshold = initial_threshold
        self.link_feedback.clear()
        self.search_feedback.clear()
        logger.info("Threshold tuner reset")
