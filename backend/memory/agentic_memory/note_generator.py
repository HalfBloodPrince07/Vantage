# backend/memory/agentic_memory/note_generator.py
"""
LLM-based note attribute generation
"""

from typing import Dict, Any, List, Optional
import json
import re
from loguru import logger

from backend.utils.llm_utils import call_ollama_with_retry


class NoteGenerator:
    def __init__(self, model: str = "qwen3-vl:8b"):
        self.model = model

    async def generate_note_attributes(self, content: str) -> Dict[str, Any]:
        prompt = f"""Analyze this memory content and extract structured attributes.

Content: {content[:2000]}

Respond in valid JSON format only:
{{"context": "1-2 sentence description of what this is about", "keywords": ["keyword1", "keyword2", "keyword3"], "tags": ["tag1", "tag2"], "importance": 0.5}}

Rules:
- context: Brief description of the content's meaning/purpose
- keywords: 3-5 key terms (nouns, concepts)
- tags: 2-3 category tags (e.g., "technical", "personal", "project")
- importance: 0.0-1.0 based on how significant this information seems

JSON only, no explanation:"""

        try:
            response = await call_ollama_with_retry(
                base_url="http://localhost:11434",
                model=self.model,
                prompt=prompt,
                think=False
            )
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    "context": result.get("context", ""),
                    "keywords": result.get("keywords", [])[:5],
                    "tags": result.get("tags", [])[:3],
                    "importance": min(1.0, max(0.0, float(result.get("importance", 0.5))))
                }
        except Exception as e:
            logger.warning(f"Failed to parse LLM response for attributes: {e}")
        
        return self._extract_basic_attributes(content)

    def _extract_basic_attributes(self, content: str) -> Dict[str, Any]:
        words = content.lower().split()
        word_freq = {}
        stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
                     "have", "has", "had", "do", "does", "did", "will", "would", "could",
                     "should", "may", "might", "must", "shall", "can", "need", "i", "you",
                     "he", "she", "it", "we", "they", "this", "that", "these", "those",
                     "and", "or", "but", "if", "then", "else", "when", "where", "how",
                     "what", "which", "who", "whom", "to", "of", "in", "for", "on", "with",
                     "at", "by", "from", "as", "into", "through", "during", "before", "after"}
        
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word)
            if len(clean_word) > 3 and clean_word not in stopwords:
                word_freq[clean_word] = word_freq.get(clean_word, 0) + 1
        
        keywords = sorted(word_freq.keys(), key=lambda x: word_freq[x], reverse=True)[:5]
        
        return {
            "context": content[:100] + "..." if len(content) > 100 else content,
            "keywords": keywords,
            "tags": ["auto-extracted"],
            "importance": 0.5
        }

    async def assess_confidence(
        self,
        content: str,
        source_type: str
    ) -> float:
        confidence_map = {
            "user_input": 0.9,
            "document": 0.85,
            "llm_inference": 0.6,
            "system": 0.95
        }
        base_confidence = confidence_map.get(source_type, 0.7)
        
        if len(content) < 20:
            base_confidence *= 0.8
        elif len(content) > 500:
            base_confidence *= 1.1
        
        return min(1.0, base_confidence)

    async def detect_note_type(self, content: str) -> str:
        content_lower = content.lower()
        
        if any(kw in content_lower for kw in ["question", "how to", "what is", "why does", "?"]):
            return "query"
        elif any(kw in content_lower for kw in ["i learned", "insight", "realized", "discovered"]):
            return "insight"
        elif any(kw in content_lower for kw in ["feedback", "improve", "suggestion", "better"]):
            return "feedback"
        elif any(kw in content_lower for kw in ["def ", "class ", "function", "import ", "```"]):
            return "code"
        else:
            return "insight"
