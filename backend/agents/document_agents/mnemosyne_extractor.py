"""
Mnemosyne (The Keeper)
======================
Goddess of memory - extracts and preserves key insights.

Responsibilities:
- Extract key facts, figures, and data points
- Generate document summaries at multiple levels
- Create bullet-point highlights
- Extract quotes and important passages
- Identify actionable items and deadlines
- Create Q&A pairs from document content
- Build structured knowledge representation

Input: Extracted text + Semantic analysis from Hypatia
Output: Key insights, summaries, highlights, Q&A pairs
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from loguru import logger
import json
import re

from backend.utils.llm_utils import call_ollama_with_retry


@dataclass
class DocumentInsights:
    """Structured insights extracted from document"""
    executive_summary: str  # 2-3 sentence summary
    detailed_summary: str  # Full paragraph summary
    key_points: List[str]  # Bullet points
    key_facts: List[Dict[str, str]]  # [{fact: str, context: str}]
    important_quotes: List[Dict[str, str]]  # [{quote: str, page: int}]
    action_items: List[str]
    dates_deadlines: List[Dict[str, str]]  # [{date: str, description: str}]
    questions_answers: List[Dict[str, str]]  # Pre-generated Q&A pairs
    numerical_data: List[Dict[str, Any]]  # Extracted numbers/stats
    
    def to_dict(self):
        """Convert to dictionary"""
        return asdict(self)


class MnemosyneExtractor:
    """
    Mnemosyne (The Keeper) - Insights Extraction Agent
    
    Like the goddess of memory, I preserve and organize the most important knowledge.
    """
    
    AGENT_NAME = "Mnemosyne"
    AGENT_TITLE = "The Keeper"
    AGENT_DESCRIPTION = "Goddess of memory - I extract and preserve key insights"
    
    def __init__(self, config: Dict[str, Any]):
        self.name = f"{self.AGENT_NAME} ({self.AGENT_TITLE})"
        self.config = config
        logger.info(f"🧠 {self.name} initialized - Ready to preserve knowledge")
    
    async def extract_insights(
        self, 
        extracted_content: Dict[str, Any],
        semantic_analysis: Dict[str, Any],
        user_query: Optional[str] = None
    ) -> DocumentInsights:
        """
        Extract key insights from document based on analysis.
        
        Args:
            extracted_content: Output from Prometheus
            semantic_analysis: Output from Hypatia
            user_query: Optional user question for focused extraction
            
        Returns:
            DocumentInsights with structured key information
        """
        text = extracted_content.get('raw_text', '')
        filename = extracted_content.get('filename', 'unknown')
        doc_type = semantic_analysis.get('document_type', 'other')
        
        # Build extraction prompt
        extraction_prompt = self._build_extraction_prompt(text, doc_type, semantic_analysis, user_query)
        
        try:
            response = await call_ollama_with_retry(
                base_url=self.config['ollama']['base_url'],
                model=self.config['ollama']['unified_model']['name'],
                prompt=extraction_prompt,
                max_retries=2,
                timeout=self.config['ollama'].get('timeout', 120.0),
                temperature=0.2,  # Very low for factual extraction
                fallback_response=None,
                model_type="text",
                config=self.config,
                think=True  # Enable reasoning for insight extraction
            )
            
            parsed = self._parse_insights_response(response, text)
            logger.info(f"🧠 {self.name}: Extracted {len(parsed.key_points)} key points from {filename}")
            return parsed
            
        except Exception as e:
            logger.error(f"🧠 {self.name}: Insight extraction failed: {e}")
            return self._fallback_insights(text, filename)
    
    def _build_extraction_prompt(
        self, 
        text: str, 
        doc_type: str, 
        semantic_analysis: Dict,
        user_query: Optional[str]
    ) -> str:
        """Build the extraction prompt for LLM"""
        # Truncate if too long
        max_chars = 8000
        truncated = text[:max_chars] + "..." if len(text) > max_chars else text
        
        query_context = f"\n\nUser's specific question: {user_query}" if user_query else ""
        
        prompt = f"""Extract key insights from this {doc_type} document.

Document content:
{truncated}

{query_context}

Provide structured insights in JSON format:
{{
    "executive_summary": "2-3 sentence high-level summary",
    "detailed_summary": "Comprehensive paragraph summary",
    "key_points": ["bullet point 1", "bullet point 2", "bullet point 3"],
    "key_facts": [{{"fact": "important fact", "context": "context"}}],
    "important_quotes": [{{"quote": "exact quote", "page": 1}}],
    "action_items": ["action 1", "action 2"],
    "dates_deadlines": [{{"date": "2024-01-01", "description": "deadline description"}}],
    "questions_answers": [{{"question": "What is X?", "answer": "Y is..."}}],
    "numerical_data": [{{"value": 100, "unit": "dollars", "context": "revenue"}}]
}}

Focus on factual, verifiable information. Respond ONLY with valid JSON."""
        
        return prompt
    
    def _parse_insights_response(self, response: str, text: str) -> DocumentInsights:
        """Parse LLM response into DocumentInsights"""
        try:
            # Extract JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(response)
            
            return DocumentInsights(
                executive_summary=data.get('executive_summary', ''),
                detailed_summary=data.get('detailed_summary', ''),
                key_points=data.get('key_points', []),
                key_facts=data.get('key_facts', []),
                important_quotes=data.get('important_quotes', []),
                action_items=data.get('action_items', []),
                dates_deadlines=data.get('dates_deadlines', []),
                questions_answers=data.get('questions_answers', []),
                numerical_data=data.get('numerical_data', [])
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse insights response: {e}")
            return self._fallback_insights(text, "document")
    
    def _fallback_insights(self, text: str, filename: str) -> DocumentInsights:
        """Simple fallback extraction"""
        # Create simple summary from first few sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        executive_summary = '. '.join(sentences[:2]) + '.' if sentences else "Document content available."
        detailed_summary = ' '.join(sentences[:5]) + '.' if len(sentences) > 2 else executive_summary
        
        # Extract key points (simple heuristic: look for numbered lists or bullet points)
        key_points = []
        for line in text.split('\n')[:50]:
            line = line.strip()
            if re.match(r'^[\d\-\*•]', line):
                key_points.append(re.sub(r'^[\d\-\*•]\s*', '', line))
        key_points = key_points[:5]
        
        # Extract dates
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b'
        dates = re.findall(date_pattern, text[:1000])
        dates_deadlines = [{"date": d, "description": "Found in document"} for d in set(dates)][:3]
        
        # Extract numbers
        number_pattern = r'\$?\d+(?:,\d{3})*(?:\.\d{2})?'
        numbers = re.findall(number_pattern, text[:1000])
        numerical_data = [{"value": n, "unit": "", "context": "Found in text"} for n in set(numbers)][:5]
        
        return DocumentInsights(
            executive_summary=executive_summary,
            detailed_summary=detailed_summary,
            key_points=key_points if key_points else ["Document contains information about " + filename],
            key_facts=[],
            important_quotes=[],
            action_items=[],
            dates_deadlines=dates_deadlines,
            questions_answers=[],
            numerical_data=numerical_data
        )
    
    async def answer_question(
        self, 
        question: str,
        extracted_content: Dict[str, Any],
        insights: DocumentInsights
    ) -> str:
        """Answer a specific question using extracted insights and content"""
        text = extracted_content.get('raw_text', '')
        
        # Build context from insights
        context = f"""Document Summary: {insights.executive_summary}

Key Points:
{chr(10).join('- ' + p for p in insights.key_points[:5])}

Document Content (excerpt):
{text[:3000]}...
"""
        
        prompt = f"""Based on the following document information, answer the user's question accurately and concisely.

{context}

Question: {question}

Answer:"""
        
        try:
            response = await call_ollama_with_retry(
                base_url=self.config['ollama']['base_url'],
                model=self.config['ollama']['unified_model']['name'],
                prompt=prompt,
                max_retries=2,
                timeout=self.config['ollama'].get('timeout', 120.0),
                temperature=0.3,
                fallback_response="I found information in the document, but I'm having trouble formulating an answer.",
                model_type="text",
                config=self.config
            )
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Question answering failed: {e}")
            return "I encountered an error while trying to answer your question."
    
    def get_agent_info(self) -> Dict[str, str]:
        """Return agent information for UI display"""
        return {
            "name": self.AGENT_NAME,
            "title": self.AGENT_TITLE,
            "full_name": self.name,
            "description": self.AGENT_DESCRIPTION,
            "icon": "🧠",
            "role": "insights_extractor"
        }
