# backend/feedback.py
# Human Feedback Learning System - RLHF-style feedback for search results

import sqlite3
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from loguru import logger
import numpy as np
from contextlib import contextmanager


class FeedbackStore:
    """
    Stores and retrieves user feedback on search results.
    
    Features:
    - Per-user feedback (each user's ratings only affect their own results)
    - 1-month time decay (older feedback matters less)
    - Query similarity matching for applying feedback to similar searches
    """
    
    def __init__(self, db_path: str = "data/feedback.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        logger.info(f"FeedbackStore initialized at {self.db_path}")
    
    def _init_db(self):
        """Initialize the SQLite database with feedback tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Main feedback table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    query TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    feedback_score INTEGER NOT NULL,  -- +1 (helpful) or -1 (not helpful)
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Index for fast lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_feedback_user_query 
                ON feedback(user_id, query)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_feedback_user_doc 
                ON feedback(user_id, document_id)
            ''')
            
            conn.commit()
            logger.debug("Feedback database initialized")
    
    @contextmanager
    def _get_connection(self):
        """Get a database connection with proper cleanup"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def add_feedback(
        self,
        user_id: str,
        query: str,
        document_id: str,
        is_helpful: bool
    ) -> bool:
        """
        Record user feedback on a search result.
        
        Args:
            user_id: The user providing feedback
            query: The search query that produced the result
            document_id: The document being rated
            is_helpful: True for thumbs up, False for thumbs down
        
        Returns:
            True if feedback was recorded successfully
        """
        feedback_score = 1 if is_helpful else -1
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if user already gave feedback for this query-doc pair
                cursor.execute('''
                    SELECT id FROM feedback 
                    WHERE user_id = ? AND query = ? AND document_id = ?
                ''', (user_id, query.lower().strip(), document_id))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing feedback
                    cursor.execute('''
                        UPDATE feedback 
                        SET feedback_score = ?, created_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (feedback_score, existing['id']))
                    logger.debug(f"Updated feedback for user={user_id}, doc={document_id[:8]}")
                else:
                    # Insert new feedback
                    cursor.execute('''
                        INSERT INTO feedback (user_id, query, document_id, feedback_score)
                        VALUES (?, ?, ?, ?)
                    ''', (user_id, query.lower().strip(), document_id, feedback_score))
                    logger.debug(f"Added feedback for user={user_id}, doc={document_id[:8]}, score={feedback_score}")
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to add feedback: {e}")
            return False
    
    def get_feedback_boosts(
        self,
        user_id: str,
        query: str,
        document_ids: List[str],
        decay_days: int = 30
    ) -> Dict[str, float]:
        """
        Get feedback-based score boosts for a list of documents.
        
        Uses time decay: feedback from 30+ days ago has minimal impact.
        
        Args:
            user_id: The user making the search
            query: The current search query
            document_ids: List of document IDs to get boosts for
            decay_days: Number of days for full decay (default 30)
        
        Returns:
            Dict mapping document_id to boost score (-1.0 to +1.0)
        """
        if not document_ids:
            return {}
        
        boosts = {doc_id: 0.0 for doc_id in document_ids}
        cutoff_date = datetime.now() - timedelta(days=decay_days)
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get feedback for these documents from this user
                placeholders = ','.join(['?' for _ in document_ids])
                cursor.execute(f'''
                    SELECT document_id, feedback_score, created_at
                    FROM feedback
                    WHERE user_id = ? 
                    AND document_id IN ({placeholders})
                    AND created_at > ?
                ''', [user_id] + document_ids + [cutoff_date.isoformat()])
                
                for row in cursor.fetchall():
                    doc_id = row['document_id']
                    score = row['feedback_score']
                    created_at = datetime.fromisoformat(row['created_at'])
                    
                    # Calculate time decay (linear decay over decay_days)
                    days_old = (datetime.now() - created_at).days
                    decay_factor = max(0, 1 - (days_old / decay_days))
                    
                    # Apply decayed feedback
                    boosts[doc_id] += score * decay_factor
                
                # Also check for similar queries (exact match for now)
                cursor.execute(f'''
                    SELECT document_id, feedback_score, created_at
                    FROM feedback
                    WHERE user_id = ? 
                    AND query = ?
                    AND document_id IN ({placeholders})
                    AND created_at > ?
                ''', [user_id, query.lower().strip()] + document_ids + [cutoff_date.isoformat()])
                
                for row in cursor.fetchall():
                    doc_id = row['document_id']
                    score = row['feedback_score']
                    created_at = datetime.fromisoformat(row['created_at'])
                    
                    days_old = (datetime.now() - created_at).days
                    decay_factor = max(0, 1 - (days_old / decay_days))
                    
                    # Extra boost for exact query match
                    boosts[doc_id] += score * decay_factor * 0.5
                
        except Exception as e:
            logger.error(f"Failed to get feedback boosts: {e}")
        
        # Normalize boosts to -1.0 to +1.0 range
        max_boost = max(abs(b) for b in boosts.values()) if boosts else 1
        if max_boost > 1:
            boosts = {k: v / max_boost for k, v in boosts.items()}
        
        return boosts
    
    def get_user_feedback_stats(self, user_id: str) -> Dict:
        """Get feedback statistics for a user"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN feedback_score > 0 THEN 1 ELSE 0 END) as positive,
                        SUM(CASE WHEN feedback_score < 0 THEN 1 ELSE 0 END) as negative
                    FROM feedback
                    WHERE user_id = ?
                ''', (user_id,))
                
                row = cursor.fetchone()
                return {
                    "total_feedback": row['total'] or 0,
                    "positive": row['positive'] or 0,
                    "negative": row['negative'] or 0
                }
                
        except Exception as e:
            logger.error(f"Failed to get feedback stats: {e}")
            return {"total_feedback": 0, "positive": 0, "negative": 0}
    
    def get_document_feedback(self, user_id: str, document_id: str) -> Optional[int]:
        """Get user's feedback for a specific document (1, -1, or None)"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT feedback_score FROM feedback
                    WHERE user_id = ? AND document_id = ?
                    ORDER BY created_at DESC LIMIT 1
                ''', (user_id, document_id))
                
                row = cursor.fetchone()
                return row['feedback_score'] if row else None
                
        except Exception as e:
            logger.error(f"Failed to get document feedback: {e}")
            return None
    
    def cleanup_old_feedback(self, days: int = 90):
        """Remove feedback older than specified days"""
        try:
            cutoff = datetime.now() - timedelta(days=days)
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM feedback WHERE created_at < ?
                ''', (cutoff.isoformat(),))
                deleted = cursor.rowcount
                conn.commit()
                logger.info(f"Cleaned up {deleted} old feedback entries")
                return deleted
        except Exception as e:
            logger.error(f"Failed to cleanup feedback: {e}")
            return 0


# Global instance
_feedback_store: Optional[FeedbackStore] = None


def get_feedback_store() -> FeedbackStore:
    """Get or create the global FeedbackStore instance"""
    global _feedback_store
    if _feedback_store is None:
        _feedback_store = FeedbackStore()
    return _feedback_store
