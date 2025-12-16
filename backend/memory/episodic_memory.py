# backend/memory/episodic_memory.py
"""
EpisodicMemory - Complete Interaction Episode Storage
=====================================================
Stores complete interaction episodes rather than just individual turns.

An episode includes:
- The full query-response cycle
- Context at time of query
- Results retrieved
- User feedback (if any)
- Outcome metrics
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import sqlite3
from loguru import logger


@dataclass
class Episode:
    """A complete interaction episode"""
    id: str
    user_id: str
    session_id: str
    timestamp: str
    
    # Query information
    query: str
    intent: str
    entities: List[str]
    
    # Response information
    response: str
    results_count: int
    top_result_score: float
    
    # Context
    attached_documents: List[str]
    conversation_history_length: int
    
    # Outcome
    success: bool  # Did user find what they wanted?
    feedback: Optional[str]  # User feedback if any
    duration_ms: int  # How long the query took
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EpisodeSummary:
    """Summary of multiple episodes"""
    user_id: str
    total_episodes: int
    success_rate: float
    common_intents: Dict[str, int]
    avg_results_count: float
    avg_duration_ms: float
    period_start: str
    period_end: str


class EpisodicMemory:
    """
    Stores and retrieves complete interaction episodes.
    
    Unlike turn-by-turn memory, episodic memory captures the full
    context of each interaction for better pattern learning.
    """
    
    def __init__(self, db_path: str = "locallens_episodes.db"):
        self.db_path = db_path
        self._init_db()
        logger.info(f"📓 EpisodicMemory initialized at {db_path}")
    
    def _init_db(self):
        """Initialize SQLite database for episodes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                query TEXT NOT NULL,
                intent TEXT,
                entities TEXT,
                response TEXT,
                results_count INTEGER,
                top_result_score REAL,
                attached_documents TEXT,
                conversation_history_length INTEGER,
                success INTEGER,
                feedback TEXT,
                duration_ms INTEGER
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user ON episodes(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session ON episodes(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON episodes(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_intent ON episodes(intent)")
        
        conn.commit()
        conn.close()
    
    def store_episode(self, episode: Episode) -> bool:
        """
        Store a complete episode.
        
        Args:
            episode: The Episode to store
            
        Returns:
            True if stored successfully
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO episodes
                (id, user_id, session_id, timestamp, query, intent, entities,
                 response, results_count, top_result_score, attached_documents,
                 conversation_history_length, success, feedback, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                episode.id,
                episode.user_id,
                episode.session_id,
                episode.timestamp,
                episode.query,
                episode.intent,
                json.dumps(episode.entities),
                episode.response,
                episode.results_count,
                episode.top_result_score,
                json.dumps(episode.attached_documents),
                episode.conversation_history_length,
                1 if episode.success else 0,
                episode.feedback,
                episode.duration_ms
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"📓 Stored episode {episode.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store episode: {e}")
            return False
    
    def retrieve_similar_episodes(
        self,
        query: str,
        user_id: Optional[str] = None,
        intent: Optional[str] = None,
        limit: int = 5
    ) -> List[Episode]:
        """
        Retrieve episodes similar to the given query.
        
        Args:
            query: Query to match against
            user_id: Optional user filter
            intent: Optional intent filter
            limit: Max episodes to return
            
        Returns:
            List of similar Episode objects
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build query with filters
            sql = "SELECT * FROM episodes WHERE 1=1"
            params = []
            
            if user_id:
                sql += " AND user_id = ?"
                params.append(user_id)
            
            if intent:
                sql += " AND intent = ?"
                params.append(intent)
            
            # Simple text matching (could be enhanced with FTS or embeddings)
            sql += " AND query LIKE ?"
            params.append(f"%{query}%")
            
            sql += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()
            
            episodes = []
            for row in rows:
                episodes.append(Episode(
                    id=row[0],
                    user_id=row[1],
                    session_id=row[2],
                    timestamp=row[3],
                    query=row[4],
                    intent=row[5] or "",
                    entities=json.loads(row[6]) if row[6] else [],
                    response=row[7] or "",
                    results_count=row[8] or 0,
                    top_result_score=row[9] or 0.0,
                    attached_documents=json.loads(row[10]) if row[10] else [],
                    conversation_history_length=row[11] or 0,
                    success=bool(row[12]),
                    feedback=row[13],
                    duration_ms=row[14] or 0
                ))
            
            return episodes
            
        except Exception as e:
            logger.error(f"Failed to retrieve episodes: {e}")
            return []
    
    def get_user_episodes(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Episode]:
        """Get recent episodes for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM episodes
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (user_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [self._row_to_episode(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get user episodes: {e}")
            return []
    
    def _row_to_episode(self, row) -> Episode:
        """Convert database row to Episode"""
        return Episode(
            id=row[0],
            user_id=row[1],
            session_id=row[2],
            timestamp=row[3],
            query=row[4],
            intent=row[5] or "",
            entities=json.loads(row[6]) if row[6] else [],
            response=row[7] or "",
            results_count=row[8] or 0,
            top_result_score=row[9] or 0.0,
            attached_documents=json.loads(row[10]) if row[10] else [],
            conversation_history_length=row[11] or 0,
            success=bool(row[12]),
            feedback=row[13],
            duration_ms=row[14] or 0
        )
    
    def summarize_episodes(
        self,
        user_id: str,
        days: int = 30
    ) -> EpisodeSummary:
        """
        Generate summary of user's episodes.
        
        Args:
            user_id: User to summarize
            days: Look back period
            
        Returns:
            EpisodeSummary with statistics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(success) as successes,
                    AVG(results_count) as avg_results,
                    AVG(duration_ms) as avg_duration,
                    MIN(timestamp) as first,
                    MAX(timestamp) as last
                FROM episodes
                WHERE user_id = ?
                AND datetime(timestamp) >= datetime('now', ?)
            """, (user_id, f'-{days} days'))
            
            row = cursor.fetchone()
            
            # Get intent distribution
            cursor.execute("""
                SELECT intent, COUNT(*) as cnt
                FROM episodes
                WHERE user_id = ?
                AND datetime(timestamp) >= datetime('now', ?)
                GROUP BY intent
                ORDER BY cnt DESC
            """, (user_id, f'-{days} days'))
            
            intents = {r[0]: r[1] for r in cursor.fetchall() if r[0]}
            conn.close()
            
            total = row[0] or 0
            successes = row[1] or 0
            
            return EpisodeSummary(
                user_id=user_id,
                total_episodes=total,
                success_rate=successes / total if total > 0 else 0.0,
                common_intents=intents,
                avg_results_count=row[2] or 0.0,
                avg_duration_ms=row[3] or 0.0,
                period_start=row[4] or "",
                period_end=row[5] or ""
            )
            
        except Exception as e:
            logger.error(f"Failed to summarize episodes: {e}")
            return EpisodeSummary(
                user_id=user_id,
                total_episodes=0,
                success_rate=0.0,
                common_intents={},
                avg_results_count=0.0,
                avg_duration_ms=0.0,
                period_start="",
                period_end=""
            )
    
    def update_episode_feedback(
        self,
        episode_id: str,
        success: bool,
        feedback: Optional[str] = None
    ) -> bool:
        """
        Update episode with user feedback.
        
        Args:
            episode_id: Episode to update
            success: Whether query was successful
            feedback: Optional text feedback
            
        Returns:
            True if updated
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE episodes
                SET success = ?, feedback = ?
                WHERE id = ?
            """, (1 if success else 0, feedback, episode_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to update episode feedback: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get overall episodic memory statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM episodes")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM episodes")
            users = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(success) FROM episodes")
            success_rate = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                "total_episodes": total,
                "unique_users": users,
                "overall_success_rate": round(success_rate, 3)
            }
            
        except Exception as e:
            logger.error(f"Failed to get episode stats: {e}")
            return {"total_episodes": 0, "unique_users": 0, "overall_success_rate": 0}
