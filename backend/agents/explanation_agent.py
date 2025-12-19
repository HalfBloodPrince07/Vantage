# backend/agents/explanation_agent.py
"""Explanation Agent - Explains search results and reasoning"""

from typing import Dict, Any, List
import httpx
from loguru import logger
import json
from backend.utils.llm_utils import call_ollama_with_retry, call_ollama_json, get_document_content


class ExplanationAgent:
    """Agent specialized in explaining search results and reasoning"""
    AGENT_NAME = "Hermes"
    AGENT_TITLE = "The Messenger"
    AGENT_DESCRIPTION = "The messenger - I explain why results matter"

    def __init__(self, config: Dict[str, Any]):
        self.name = f"{self.AGENT_NAME} ({self.AGENT_TITLE})"
        self.config = config
        self.ollama_url = config['ollama']['base_url']
        self.model = config['ollama']['unified_model']['name']

    async def explain_ranking(
        self,
        query: str,
        document: Dict[str, Any],
        rank: int
    ) -> Dict[str, Any]:
        """
        Explain why a document ranked at specific position

        Args:
            query: Search query
            document: The document
            rank: Ranking position

        Returns:
            Dict with agent info and explanation text
        """
        content = get_document_content(document, max_length=300)
        
        prompt = f"""Explain why this document ranked #{rank} for query "{query}":

Document: {document.get('filename')}
Score: {document.get('score', 0):.3f}
Content: {content}

Explanation (2-3 sentences):"""

        try:
            fallback = f"This document matches your query with a relevance score of {document.get('score', 0):.2f}"
            
            response_text = await call_ollama_with_retry(
                base_url=self.ollama_url,
                model=self.model,
                prompt=prompt,
                max_retries=3,
                timeout=self.config['ollama'].get('timeout', 120.0),
                temperature=0.2,
                fallback_response=fallback,
                model_type="text",
                config=self.config
            )
            
            return {
                "agent": self.name,
                "explanation": response_text
            }

        except Exception as e:
            logger.error(f"Ranking explanation failed: {e}")
            return {
                "agent": self.name,
                "explanation": f"This document matches your query with a relevance score of {document.get('score', 0):.2f}"
            }

    async def highlight_matches(
        self,
        query: str,
        document: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Identify and extract matching sections from document

        Returns:
            Dict with agent info and list of relevant excerpts
        """
        content = get_document_content(document, max_length=1000)

        prompt = f"""Find 2-3 short excerpts from this text that match query "{query}":

{content}

Return JSON:
{{
    "excerpts": ["excerpt 1", "excerpt 2"]
}}"""

        try:
            fallback_data = {"excerpts": []}
            
            data = await call_ollama_json(
                base_url=self.ollama_url,
                model=self.model,
                prompt=prompt,
                max_retries=2,
                timeout=self.config['ollama'].get('timeout', 120.0),
                temperature=0.1,
                fallback_data=fallback_data,
                model_type="text",
                config=self.config
            )
            
            return {
                "agent": self.name,
                "excerpts": data.get('excerpts', [])
            }

        except Exception as e:
            logger.error(f"Match highlighting failed: {e}")
            return {
                "agent": self.name,
                "excerpts": []
            }

    def explain_score_components(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Break down relevance score into components

        Args:
            document: Document with scoring metadata

        Returns:
            Score breakdown
        """
        score = document.get('score', 0)

        # Simplified breakdown (actual would come from search engine)
        return {
            "agent": self.name,
            "total_score": round(score, 3),
            "semantic_similarity": round(score * 0.7, 3),
            "keyword_match": round(score * 0.3, 3),
            "explanation": f"Score of {score:.2f} indicates {'high' if score > 0.7 else 'moderate' if score > 0.4 else 'low'} relevance"
        }
