# backend/agents/confidence_scorer.py
"""
ConfidenceScorer (Themis)
=========================
Themis - The Just - Uncertainty quantification agent.

Provides confidence-aware responses with:
- Answer confidence scoring
- Evidence strength assessment
- Alternative interpretation generation
- Follow-up question suggestions
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from loguru import logger

from backend.utils.llm_utils import call_ollama_json


@dataclass
class EvidenceStrength:
    """Assessment of evidence supporting an answer"""
    level: str  # strong, moderate, weak, none
    score: float  # 0.0-1.0
    supporting_sources: int
    contradicting_sources: int
    explanation: str


@dataclass
class ConfidenceAwareResponse:
    """A response with full confidence metadata"""
    answer: str
    confidence: float  # 0.0-1.0
    evidence_strength: EvidenceStrength
    alternative_interpretations: List[str]
    suggested_followups: List[str]
    uncertainty_reasons: List[str]
    sources_used: int


class ConfidenceScorer:
    """
    Themis - The Just
    
    The goddess of justice and order - I weigh evidence and quantify certainty.
    
    Responsibilities:
    - Score confidence in generated answers
    - Assess strength of evidence
    - Suggest alternative interpretations when uncertain
    - Generate follow-up questions for clarification
    """
    
    AGENT_NAME = "Themis"
    AGENT_TITLE = "The Just"
    AGENT_DESCRIPTION = "The goddess of justice - I weigh evidence and certainty"
    AGENT_ICON = "⚖️"
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = f"{self.AGENT_NAME} ({self.AGENT_TITLE})"
        self.ollama_url = config['ollama']['base_url']
        self.model = config['ollama']['unified_model']['name']
        
        logger.info(f"⚖️ {self.name} initialized for confidence scoring")
    
    async def score_answer_confidence(
        self,
        answer: str,
        query: str,
        sources: List[Dict[str, Any]],
        retrieval_quality: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Score confidence in an answer (0.0-1.0).
        
        Args:
            answer: The generated answer
            query: Original query
            sources: Source documents used
            retrieval_quality: Optional quality metrics from CriticAgent
            
        Returns:
            Confidence score 0.0-1.0
        """
        base_score = 0.5
        
        # Factor 1: Number of sources
        sources_score = min(len(sources) / 5.0, 1.0) * 0.2
        
        # Factor 2: Top source quality
        if sources:
            top_score = sources[0].get('score', 0.5)
            source_quality_score = min(top_score, 1.0) * 0.2
        else:
            source_quality_score = 0
        
        # Factor 3: Answer length (too short = uncertain, too long = verbose)
        answer_len = len(answer)
        if answer_len < 50:
            length_score = 0.1
        elif answer_len > 2000:
            length_score = 0.1
        else:
            length_score = 0.15
        
        # Factor 4: Retrieval quality from CriticAgent
        if retrieval_quality:
            quality_score = retrieval_quality.get('quality_score', 0.5) * 0.2
        else:
            quality_score = 0.1
        
        # Factor 5: Certainty phrases in answer
        uncertainty_phrases = [
            "i'm not sure", "might be", "possibly", "perhaps",
            "unclear", "couldn't find", "no information"
        ]
        certainty_phrases = [
            "clearly", "definitely", "the document states",
            "according to", "specifically"
        ]
        
        answer_lower = answer.lower()
        uncertainty_count = sum(1 for p in uncertainty_phrases if p in answer_lower)
        certainty_count = sum(1 for p in certainty_phrases if p in answer_lower)
        
        phrase_score = 0.15
        if uncertainty_count > certainty_count:
            phrase_score = 0.05
        elif certainty_count > uncertainty_count:
            phrase_score = 0.2
        
        total = base_score + sources_score + source_quality_score + length_score + quality_score + phrase_score
        
        return round(min(max(total, 0.0), 1.0), 2)
    
    async def assess_evidence_strength(
        self,
        answer: str,
        query: str,
        sources: List[Dict[str, Any]]
    ) -> EvidenceStrength:
        """
        Assess the strength of evidence supporting an answer.
        
        Args:
            answer: The answer to assess
            query: Original query
            sources: Source documents
            
        Returns:
            EvidenceStrength assessment
        """
        if not sources:
            return EvidenceStrength(
                level="none",
                score=0.0,
                supporting_sources=0,
                contradicting_sources=0,
                explanation="No source documents available to verify the answer."
            )
        
        # Simple heuristic assessment
        supporting = 0
        contradicting = 0
        
        # Check each source for relevance
        for source in sources:
            score = source.get('score', 0)
            if score >= 0.5:
                supporting += 1
            elif score < 0.2:
                # Low scoring sources might indicate poor relevance
                pass
        
        # Determine level
        if supporting >= 3:
            level = "strong"
            score = 0.8 + (supporting - 3) * 0.05
        elif supporting >= 2:
            level = "moderate"
            score = 0.6
        elif supporting >= 1:
            level = "weak"
            score = 0.4
        else:
            level = "none"
            score = 0.1
        
        return EvidenceStrength(
            level=level,
            score=round(min(score, 1.0), 2),
            supporting_sources=supporting,
            contradicting_sources=contradicting,
            explanation=f"{supporting} source(s) support this answer with relevant content."
        )
    
    async def generate_alternatives(
        self,
        query: str,
        answer: str
    ) -> List[str]:
        """
        Generate alternative interpretations of the query/answer.
        
        Useful when confidence is low.
        """
        prompt = f"""The user asked: "{query}"

The answer provided was: "{answer[:500]}"

If this answer might not be exactly what the user was looking for, 
suggest 2-3 alternative interpretations of their question.

Return JSON:
{{
    "alternatives": [
        "Alternative interpretation 1",
        "Alternative interpretation 2"
    ]
}}

Only suggest alternatives if the question could reasonably be interpreted differently.
If the question is clear and unambiguous, return empty list."""

        try:
            fallback = {"alternatives": []}
            
            result = await call_ollama_json(
                base_url=self.ollama_url,
                model=self.model,
                prompt=prompt,
                max_retries=2,
                timeout=self.config['ollama'].get('timeout', 120.0),
                temperature=0.4,
                fallback_data=fallback,
                model_type="text",
                config=self.config
            )
            
            return result.get('alternatives', [])[:3]
            
        except Exception as e:
            logger.error(f"Alternative generation failed: {e}")
            return []
    
    async def suggest_followups(
        self,
        query: str,
        answer: str,
        sources: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate suggested follow-up questions.
        
        Based on what was asked and what information is available.
        """
        # Extract topics from sources
        source_topics = []
        for source in sources[:3]:
            filename = source.get('filename', '')
            summary = (source.get('detailed_summary', '') or source.get('content_summary', ''))[:100]
            source_topics.append(f"{filename}: {summary}")
        
        prompt = f"""Based on this interaction, suggest helpful follow-up questions.

User asked: "{query}"
Answer given: "{answer[:300]}"
Available sources: {', '.join(source_topics) or 'various documents'}

Suggest 2-3 natural follow-up questions the user might want to ask.
Focus on:
- Diving deeper into topics mentioned
- Related information in the sources
- Clarifications that might help

Return JSON:
{{
    "followups": [
        "Suggested follow-up question 1?",
        "Suggested follow-up question 2?"
    ]
}}"""

        try:
            fallback = {"followups": []}
            
            result = await call_ollama_json(
                base_url=self.ollama_url,
                model=self.model,
                prompt=prompt,
                max_retries=2,
                timeout=self.config['ollama'].get('timeout', 120.0),
                temperature=0.5,
                fallback_data=fallback,
                model_type="text",
                config=self.config
            )
            
            return result.get('followups', [])[:3]
            
        except Exception as e:
            logger.error(f"Follow-up generation failed: {e}")
            return []
    
    async def create_confidence_aware_response(
        self,
        answer: str,
        query: str,
        sources: List[Dict[str, Any]],
        retrieval_quality: Optional[Dict[str, Any]] = None
    ) -> ConfidenceAwareResponse:
        """
        Create a full confidence-aware response with all metadata.
        
        Args:
            answer: The generated answer
            query: Original query
            sources: Source documents
            retrieval_quality: Optional quality metrics
            
        Returns:
            ConfidenceAwareResponse with full confidence metadata
        """
        # Score confidence
        confidence = await self.score_answer_confidence(
            answer, query, sources, retrieval_quality
        )
        
        # Assess evidence
        evidence = await self.assess_evidence_strength(answer, query, sources)
        
        # Generate alternatives if confidence is low
        alternatives = []
        if confidence < 0.6:
            alternatives = await self.generate_alternatives(query, answer)
        
        # Generate follow-ups
        followups = await self.suggest_followups(query, answer, sources)
        
        # Identify uncertainty reasons
        uncertainty_reasons = []
        if len(sources) < 2:
            uncertainty_reasons.append("Limited source documents available")
        if confidence < 0.5:
            uncertainty_reasons.append("Answer may be incomplete or uncertain")
        if evidence.level in ["weak", "none"]:
            uncertainty_reasons.append("Evidence for this answer is limited")
        
        return ConfidenceAwareResponse(
            answer=answer,
            confidence=confidence,
            evidence_strength=evidence,
            alternative_interpretations=alternatives,
            suggested_followups=followups,
            uncertainty_reasons=uncertainty_reasons,
            sources_used=len(sources)
        )
    
    def get_agent_info(self) -> Dict[str, str]:
        """Return agent information for UI display"""
        return {
            "name": self.AGENT_NAME,
            "title": self.AGENT_TITLE,
            "full_name": self.name,
            "description": self.AGENT_DESCRIPTION,
            "icon": self.AGENT_ICON,
            "role": "confidence_scorer"
        }
