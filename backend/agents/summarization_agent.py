# backend/agents/summarization_agent.py
"""Summarization Agent - Multi-document summarization"""

from typing import Dict, Any, List
import httpx
from loguru import logger
import json
from backend.utils.llm_utils import call_ollama_with_retry, validate_document_content, get_document_content


class SummarizationAgent:
    """Agent specialized in multi-document summarization"""
    AGENT_NAME = "Thoth"
    AGENT_TITLE = "The Scribe"
    AGENT_DESCRIPTION = "The scribe - I summarize knowledge"

    def __init__(self, config: Dict[str, Any]):
        self.name = f"{self.AGENT_NAME} ({self.AGENT_TITLE})"
        self.config = config
        self.ollama_url = config['ollama']['base_url']
        self.model = config['ollama']['unified_model']['name']

    async def summarize_documents(
        self,
        documents: List[Dict[str, Any]],
        summary_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Generate summary of multiple documents

        Args:
            documents: List of documents to summarize
            summary_type: "comprehensive", "brief", or "bullet_points"

        Returns:
            Dict with agent info and generated summary
        """
        if not documents:
            return {
                "agent": self.name,
                "summary": "No documents to summarize."
            }

        # Validate and extract content
        doc_texts = []
        for i, doc in enumerate(documents[:10], 1):
            if not validate_document_content(doc):
                logger.warning(f"Document {doc.get('filename', 'unknown')} has no valid content")
                continue
            
            content = get_document_content(doc, max_length=400)
            doc_texts.append(f"**{doc.get('filename', 'unknown')}**: {content}")
        
        if not doc_texts:
            return {
                "agent": self.name,
                "summary": "Documents have no valid content to summarize."
            }

        combined = "\n\n".join(doc_texts)

        summary_instructions = {
            "comprehensive": "Provide a detailed summary covering all key points",
            "brief": "Provide a concise 2-3 sentence summary",
            "bullet_points": "Provide summary as bullet points"
        }

        instruction = summary_instructions.get(summary_type, summary_instructions["comprehensive"])

        prompt = f"""Summarize these documents ({instruction}):

{combined}

Summary:"""

        try:
            fallback = f"Found {len(doc_texts)} documents: " + ", ".join([doc.get('filename', 'unknown') for doc in documents[:5]])
            
            response_text = await call_ollama_with_retry(
                base_url=self.ollama_url,
                model=self.model,
                prompt=prompt,
                max_retries=3,
                timeout=self.config['ollama'].get('timeout', 120.0),
                temperature=0.3,
                fallback_response=fallback,
                model_type="text",
                config=self.config
            )
            
            return {
                "agent": self.name,
                "summary": response_text
            }

        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return {
                "agent": self.name,
                "summary": f"Error summarizing documents: {str(e)}"
            }

    async def hierarchical_summary(
        self,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate hierarchical summary for large document sets

        Summarizes in tiers for better organization
        """
        if len(documents) <= 5:
            result = await self.summarize_documents(documents)
            return {
                "agent": self.name,
                "summary": result["summary"],
                "tiers": 1
            }

        # For larger sets, create hierarchical structure
        # This is a simplified version
        tier1_result = await self.summarize_documents(documents[:5], "comprehensive")
        tier2_result = await self.summarize_documents(documents[5:10], "comprehensive")
        tier1_summary = tier1_result["summary"]
        tier2_summary = tier2_result["summary"]

        # Combine tier summaries
        combined_prompt = f"""Combine these summaries into a cohesive overview:

Summary 1: {tier1_summary}

Summary 2: {tier2_summary}

Provide a unified summary."""

        try:
            final_summary = await call_ollama_with_retry(
                base_url=self.ollama_url,
                model=self.model,
                prompt=combined_prompt,
                max_retries=2,
                timeout=self.config['ollama'].get('timeout', 120.0),
                temperature=0.2,
                fallback_response=f"Combined summary of: {tier1_summary[:50]}... and {tier2_summary[:50]}...",
                model_type="text",
                config=self.config
            )

            return {
                "agent": self.name,
                "summary": final_summary,
                "tier1": tier1_summary,
                "tier2": tier2_summary,
                "tiers": 2
            }

        except Exception as e:
            logger.error(f"Hierarchical summarization failed: {e}")
            return {
                "agent": self.name,
                "error": str(e)
            }
