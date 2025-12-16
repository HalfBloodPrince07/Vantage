# backend/ranking/personalized_ranker.py
"""
PersonalizedRanker
==================
Learn from user feedback to personalize search result ranking.

Features:
- User preference learning from feedback
- Topic affinity tracking
- File type preference weighting
- Personalized re-ranking of results
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from loguru import logger
import sqlite3
import json


@dataclass
class UserPreferences:
    """Learned user preferences"""
    user_id: str
    file_type_weights: Dict[str, float]  # pdf: 1.2, doc: 0.9, etc.
    topic_affinities: Dict[str, float]  # topic: affinity score
    avg_preferred_score: float  # Average score of docs user found helpful
    preferred_sources: List[str]  # Folders/sources user prefers
    updated_at: str


class PersonalizedRanker:
    """
    Learns from user feedback to personalize search rankings.
    
    Uses implicit signals:
    - Explicit feedback (helpful/not helpful buttons)
    - Document opens
    - Document attachments
    - Click patterns
    """
    
    def __init__(self, db_path: str = "data/feedback.db"):
        self.db_path = db_path
        self._preferences_cache: Dict[str, UserPreferences] = {}
        
        logger.info("📊 PersonalizedRanker initialized")
    
    def load_user_preferences(self, user_id: str) -> UserPreferences:
        """
        Load learned preferences for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            UserPreferences object
        """
        # Check cache first
        if user_id in self._preferences_cache:
            return self._preferences_cache[user_id]
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get feedback history for this user
            cursor.execute("""
                SELECT document_id, feedback_score, query
                FROM feedback 
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 100
            """, (user_id,))
            
            feedback_rows = cursor.fetchall()
            
            # Calculate file type preferences from helpful documents
            file_type_weights: Dict[str, float] = {}
            topic_counts: Dict[str, int] = {}
            helpful_scores = []
            
            for doc_id, feedback_score, query in feedback_rows:
                is_helpful = feedback_score > 0  # Convert to boolean
                # Get document info
                cursor.execute("""
                    SELECT file_type, file_path
                    FROM documents
                    WHERE id = ?
                """, (doc_id,))
                doc_row = cursor.fetchone()
                
                if doc_row:
                    file_type = doc_row[0] or 'unknown'
                    
                    # Update file type weights
                    if file_type not in file_type_weights:
                        file_type_weights[file_type] = 1.0
                    
                    if is_helpful:
                        file_type_weights[file_type] += 0.1
                    else:
                        file_type_weights[file_type] -= 0.05
                    
                    # Track topics from queries
                    if query and is_helpful:
                        words = query.lower().split()
                        for word in words:
                            if len(word) > 4:
                                topic_counts[word] = topic_counts.get(word, 0) + 1
            
            conn.close()
            
            # Normalize file type weights
            if file_type_weights:
                min_weight = min(file_type_weights.values())
                max_weight = max(file_type_weights.values())
                if max_weight > min_weight:
                    for ft in file_type_weights:
                        file_type_weights[ft] = 0.8 + (file_type_weights[ft] - min_weight) / (max_weight - min_weight) * 0.4
            
            # Convert topic counts to affinities
            topic_affinities = {}
            if topic_counts:
                max_count = max(topic_counts.values())
                for topic, count in topic_counts.items():
                    if count >= 2:  # Only topics mentioned multiple times
                        topic_affinities[topic] = count / max_count
            
            preferences = UserPreferences(
                user_id=user_id,
                file_type_weights=file_type_weights,
                topic_affinities=dict(sorted(topic_affinities.items(), key=lambda x: x[1], reverse=True)[:20]),
                avg_preferred_score=0.7,  # Default
                preferred_sources=[],
                updated_at=datetime.utcnow().isoformat()
            )
            
            # Cache it
            self._preferences_cache[user_id] = preferences
            
            return preferences
            
        except Exception as e:
            logger.error(f"Failed to load user preferences: {e}")
            return UserPreferences(
                user_id=user_id,
                file_type_weights={},
                topic_affinities={},
                avg_preferred_score=0.5,
                preferred_sources=[],
                updated_at=datetime.utcnow().isoformat()
            )
    
    def rerank(
        self,
        results: List[Dict[str, Any]],
        user_id: str,
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Re-rank search results based on user preferences.
        
        Args:
            results: Original search results
            user_id: User to personalize for
            query: Optional query for context
            
        Returns:
            Re-ranked results
        """
        if not results or not user_id:
            return results
        
        prefs = self.load_user_preferences(user_id)
        
        # Score and re-rank
        scored_results = []
        for result in results:
            base_score = result.get('score', 0.5)
            personalization_boost = 0.0
            
            # File type preference
            file_type = result.get('file_type', '').lower()
            if file_type in prefs.file_type_weights:
                type_weight = prefs.file_type_weights[file_type]
                personalization_boost += (type_weight - 1.0) * 0.1
            
            # Topic affinity
            if query:
                query_words = set(query.lower().split())
                for topic, affinity in prefs.topic_affinities.items():
                    if topic in query_words:
                        personalization_boost += affinity * 0.05
            
            # Document summary topic match
            summary = (result.get('detailed_summary', '') or result.get('content_summary', '')).lower()
            for topic, affinity in list(prefs.topic_affinities.items())[:10]:
                if topic in summary:
                    personalization_boost += affinity * 0.02
            
            # Calculate final score
            personalized_score = base_score + personalization_boost
            
            result['original_score'] = base_score
            result['score'] = round(min(max(personalized_score, 0), 1), 4)
            result['personalization_boost'] = round(personalization_boost, 4)
            
            scored_results.append(result)
        
        # Sort by new score
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        
        logger.debug(f"📊 Re-ranked {len(results)} results for user {user_id}")
        return scored_results
    
    def update_from_feedback(
        self,
        user_id: str,
        document_id: str,
        is_helpful: bool,
        query: str
    ):
        """
        Update preferences based on explicit feedback.
        
        Called when user clicks helpful/not helpful.
        """
        # Invalidate cache so next load picks up new feedback
        if user_id in self._preferences_cache:
            del self._preferences_cache[user_id]
        
        logger.info(f"📊 Preference update triggered for user {user_id}")
    
    def get_topic_affinities(self, user_id: str) -> Dict[str, float]:
        """Get user's topic affinities for display/debugging"""
        prefs = self.load_user_preferences(user_id)
        return prefs.topic_affinities
    
    def get_recommendations(
        self,
        user_id: str,
        available_docs: List[Dict[str, Any]],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get proactive document recommendations based on preferences.
        
        Suggests documents user might find interesting based on patterns.
        """
        prefs = self.load_user_preferences(user_id)
        
        if not prefs.topic_affinities and not prefs.file_type_weights:
            return []  # Not enough data to recommend
        
        scored_docs = []
        for doc in available_docs:
            score = 0.0
            
            # File type preference
            file_type = doc.get('file_type', '').lower()
            if file_type in prefs.file_type_weights:
                score += prefs.file_type_weights[file_type] - 1.0
            
            # Topic presence
            summary = (doc.get('detailed_summary', '') or doc.get('content_summary', '')).lower()
            for topic, affinity in prefs.topic_affinities.items():
                if topic in summary:
                    score += affinity * 0.5
            
            if score > 0:
                doc['recommendation_score'] = round(score, 3)
                scored_docs.append(doc)
        
        scored_docs.sort(key=lambda x: x.get('recommendation_score', 0), reverse=True)
        return scored_docs[:limit]
    
    def clear_user_preferences(self, user_id: str):
        """Clear cached preferences for a user"""
        if user_id in self._preferences_cache:
            del self._preferences_cache[user_id]
        logger.info(f"📊 Cleared preferences cache for user {user_id}")
