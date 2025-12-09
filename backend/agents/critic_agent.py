# backend/agents/critic_agent.py
"""
Critic Agent - Self-reflection and Quality Control

Implements the critic pattern for quality assurance
"""

from typing import Dict, Any, List, Optional
import httpx
from loguru import logger
import json
from backend.utils.llm_utils import call_ollama_json


class CriticAgent:
    """
    Agent that evaluates and critiques search results

    Checks for:
    - Relevance
    - Completeness
    - Hallucination detection
    - Quality assessment
    """
    AGENT_NAME = "Diogenes"
    AGENT_TITLE = "The Critic"
    AGENT_DESCRIPTION = "The cynic - I evaluate the quality of your results"

    def __init__(self, config: Dict[str, Any]):
        self.name = f"{self.AGENT_NAME} ({self.AGENT_TITLE})"
        self.config = config
        self.ollama_url = config['ollama']['base_url']
        self.model = config['ollama']['text_model']['name']

    async def evaluate_results(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate quality of search results

        Args:
            query: Original query
            results: Search results to evaluate

        Returns:
            Quality assessment with score and recommendations
        """
        if not results:
            return {
                "quality_score": 0.0,
                "completeness": 0.0,
                "relevance": 0.0,
                "recommendations": ["No results found. Try broadening your search terms."],
                "should_reformulate": True
            }

        # Prepare results summary for evaluation
        results_summary = []
        for i, r in enumerate(results[:5], 1):
            results_summary.append(
                f"{i}. {r.get('filename', 'unknown')} (score: {r.get('score', 0):.2f})"
            )

        prompt = f"""Evaluate these search results for query: "{query}"

Results:
{chr(10).join(results_summary)}

Return JSON:
{{
    "quality_score": 0.0-1.0,
    "relevance_score": 0.0-1.0,
    "completeness_score": 0.0-1.0,
    "strengths": ["strength1"],
    "weaknesses": ["weakness1"],
    "recommendations": ["rec1"],
    "should_reformulate": true/false
}}

IMPORTANT: Return ONLY the raw JSON. Do not use markdown code blocks (```json)."""

        try:
            # Default fallback for evaluation
            fallback_data = {
                "quality_score": 0.7,
                "relevance_score": 0.7,
                "completeness_score": 0.6,
                "strengths": [],
                "weaknesses": [],
                "recommendations": [],
                "should_reformulate": False
            }
            
            evaluation = await call_ollama_json(
                base_url=self.ollama_url,
                model=self.model,
                prompt=prompt,
                max_retries=2,
                timeout=self.config['ollama'].get('timeout', 120.0),
                temperature=0.2,
                fallback_data=fallback_data,
                model_type="text",
                config=self.config
            )

            return {
                "agent": self.name,
                "quality_score": float(evaluation.get('quality_score', 0.5)),
                "relevance": float(evaluation.get('relevance_score', 0.5)),
                "completeness": float(evaluation.get('completeness_score', 0.5)),
                "strengths": evaluation.get('strengths', []),
                "weaknesses": evaluation.get('weaknesses', []),
                "recommendations": evaluation.get('recommendations', []),
                "should_reformulate": evaluation.get('should_reformulate', False)
            }

        except Exception as e:
            logger.error(f"Result evaluation failed: {e}")
            return {
                "agent": self.name,
                "quality_score": 0.7,  # Assume decent quality
                "relevance": 0.7,
                "completeness": 0.6,
                "recommendations": []
            }

    async def detect_hallucination(
        self,
        query: str,
        response_text: str,
        source_documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect if response contains hallucinated information

        Args:
            query: Original query
            response_text: Generated response
            source_documents: Source documents used

        Returns:
            Hallucination detection results
        """
        # Extract source summaries
        source_summaries = [
            doc.get('content_summary', '')[:200]
            for doc in source_documents[:3]
        ]

        prompt = f"""Check for hallucinations in this response:
Query: "{query}"
Response: "{response_text}"
Sources:
{chr(10).join(f"{i+1}. {s}" for i, s in enumerate(source_summaries))}

Return JSON:
{{
    "has_hallucination": true/false,
    "confidence": 0.0-1.0,
    "unsupported_claims": [],
    "supported_claims": []
}}"""

        try:
            async with httpx.AsyncClient(timeout=self.config['ollama'].get('timeout', 120.0)) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        # "format": "json", # Disabled for Qwen compatibility
                        "options": {"temperature": 0.1}
                    }
                )
                result = response.json()

                # Validate response is not empty
                response_text = result.get('response', '').strip()
                if not response_text:
                    logger.warning("Empty LLM response for hallucination detection")
                    return {
                        "has_hallucination": False,
                        "confidence": 0.5,
                        "unsupported_claims": []
                    }

                try:
                    return json.loads(response_text)
                except json.JSONDecodeError as json_err:
                    logger.warning(f"LLM response not valid JSON for hallucination detection: {json_err}")
                    return {
                        "agent": self.name,
                        "has_hallucination": False,
                        "confidence": 0.5,
                        "unsupported_claims": []
                    }

        except Exception as e:
            logger.error(f"Hallucination detection failed: {e}")
            return {
                "has_hallucination": False,
                "confidence": 0.5,
                "unsupported_claims": []
            }

    def calculate_confidence_score(
        self,
        results: List[Dict[str, Any]],
        evaluation: Dict[str, Any]
    ) -> float:
        """
        Calculate overall confidence score for results

        Combines multiple signals:
        - Number of results
        - Quality scores
        - Top result score
        """
        if not results:
            return 0.0

        # Factors
        num_results_score = min(len(results) / 5.0, 1.0)  # Max at 5 results
        quality_score = evaluation.get('quality_score', 0.5)
        top_score = results[0].get('score', 0) if results else 0

        # Weighted combination
        confidence = (
            num_results_score * 0.2 +
            quality_score * 0.4 +
            min(top_score, 1.0) * 0.4
        )

        return round(confidence, 2)

    async def suggest_improvements(
        self,
        query: str,
        results: List[Dict[str, Any]],
        evaluation: Dict[str, Any]
    ) -> List[str]:
        """
        Suggest improvements to search query or strategy

        Args:
            query: Original query
            results: Current results
            evaluation: Quality evaluation

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        # Based on evaluation
        if evaluation.get('should_reformulate'):
            suggestions.append("Try rephrasing your query with different keywords")

        if evaluation.get('relevance', 1.0) < 0.5:
            suggestions.append("Results may not match your intent. Be more specific")

        if len(results) == 0:
            suggestions.extend([
                "Try broader search terms",
                "Check if documents are indexed",
                "Use different keywords"
            ])

        elif len(results) < 3:
            suggestions.append("Limited results found. Try expanding your search")

        # Add evaluation recommendations
        suggestions.extend(evaluation.get('recommendations', []))

        return suggestions[:5]  # Top 5 suggestions
