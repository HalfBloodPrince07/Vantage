"""
Hypatia (The Scholar)
=====================
Ancient philosopher and mathematician - performs deep semantic analysis.

Responsibilities:
- Analyze document structure and organization
- Identify document type (contract, report, article, etc.)
- Extract semantic sections and hierarchy
- Classify content themes and topics
- Identify key entities (people, places, organizations, dates)
- Detect language and technical domain
- Generate document metadata

Input: Extracted text from Prometheus
Output: Structured semantic analysis with categories, entities, themes
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from loguru import logger
import json
import re

from backend.utils.llm_utils import call_ollama_with_retry


@dataclass
class SemanticAnalysis:
    """Structured semantic analysis result"""
    document_type: str  # contract, report, article, invoice, resume, etc.
    primary_language: str
    topics: List[str]
    entities: Dict[str, List[str]]  # {persons: [], organizations: [], dates: [], locations: []}
    sections: List[Dict[str, Any]]  # [{title: str, content: str, importance: float}]
    key_themes: List[str]
    technical_domain: Optional[str]
    sentiment: Optional[str]
    complexity_score: float  # 0-1
    summary_context: str  # Brief context for other agents
    
    def to_dict(self):
        """Convert to dictionary"""
        return asdict(self)


class HypatiaAnalyzer:
    """
    Hypatia (The Scholar) - Semantic Analysis Agent
    
    Like the great Alexandrian philosopher, I analyze and categorize knowledge.
    """
    
    AGENT_NAME = "Hypatia"
    AGENT_TITLE = "The Scholar"
    AGENT_DESCRIPTION = "Ancient philosopher - I analyze structure, meaning, and context"
    
    DOCUMENT_TYPES = [
        "contract", "legal_document", "report", "article", "research_paper",
        "invoice", "resume", "letter", "email", "manual", "specification",
        "presentation", "spreadsheet_data", "form", "policy", "other"
    ]
    
    def __init__(self, config: Dict[str, Any]):
        self.name = f"{self.AGENT_NAME} ({self.AGENT_TITLE})"
        self.config = config
        logger.info(f"📚 {self.name} initialized - Ready to analyze documents")
    
    async def analyze(
        self, 
        extracted_content: Dict[str, Any], 
        query_context: Optional[str] = None
    ) -> SemanticAnalysis:
        """
        Perform semantic analysis on extracted document content.
        
        Args:
            extracted_content: Output from Prometheus reader
            query_context: Optional user query for focused analysis
            
        Returns:
            SemanticAnalysis object with structured insights
        """
        text = extracted_content.get('raw_text', '')
        filename = extracted_content.get('filename', 'unknown')
        
        # Use LLM for intelligent analysis
        analysis_prompt = self._build_analysis_prompt(text, filename, query_context)
        
        try:
            response = await call_ollama_with_retry(
                base_url=self.config['ollama']['base_url'],
                model=self.config['ollama']['text_model']['name'],
                prompt=analysis_prompt,
                max_retries=2,
                timeout=self.config['ollama'].get('timeout', 120.0),
                temperature=0.3,  # Lower temperature for more analytical output
                fallback_response=None,
                model_type="text",
                config=self.config
            )
            
            parsed = self._parse_analysis_response(response, text, filename)
            logger.info(f"📚 {self.name}: Analyzed {filename} - Type: {parsed.document_type}")
            return parsed
            
        except Exception as e:
            logger.error(f"📚 {self.name}: Analysis failed: {e}")
            return self._fallback_analysis(text, filename)
    
    def _build_analysis_prompt(self, text: str, filename: str, query_context: Optional[str]) -> str:
        """Build the analysis prompt for LLM"""
        # Truncate text if too long
        max_chars = 8000
        truncated = text[:max_chars] + "..." if len(text) > max_chars else text
        
        prompt = f"""Analyze this document and provide structured insights.

Document: {filename}
Content:
{truncated}

{"User's focus: " + query_context if query_context else ""}

Provide analysis in JSON format:
{{
    "document_type": "one of: {', '.join(self.DOCUMENT_TYPES)}",
    "primary_language": "language name",
    "topics": ["topic1", "topic2", "topic3"],
    "entities": {{
        "persons": ["name1", "name2"],
        "organizations": ["org1", "org2"],
        "dates": ["date1", "date2"],
        "locations": ["location1"]
    }},
    "key_themes": ["theme1", "theme2", "theme3"],
    "technical_domain": "domain or null",
    "complexity_score": 0.0-1.0,
    "summary_context": "2-3 sentence context summary"
}}

Respond ONLY with valid JSON, no other text."""
        
        return prompt
    
    def _parse_analysis_response(self, response: str, text: str, filename: str) -> SemanticAnalysis:
        """Parse LLM response into SemanticAnalysis"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                # Try parsing the whole response
                data = json.loads(response)
            
            return SemanticAnalysis(
                document_type=data.get('document_type', 'other'),
                primary_language=data.get('primary_language', 'English'),
                topics=data.get('topics', []),
                entities=data.get('entities', {
                    'persons': [],
                    'organizations': [],
                    'dates': [],
                    'locations': []
                }),
                sections=[],  # Could be enhanced later
                key_themes=data.get('key_themes', []),
                technical_domain=data.get('technical_domain'),
                sentiment=None,  # Could be enhanced later
                complexity_score=float(data.get('complexity_score', 0.5)),
                summary_context=data.get('summary_context', f"Document about {filename}")
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse LLM analysis response: {e}")
            return self._fallback_analysis(text, filename)
    
    def _fallback_analysis(self, text: str, filename: str) -> SemanticAnalysis:
        """Simple rule-based fallback if LLM fails"""
        # Basic document type detection from filename
        filename_lower = filename.lower()
        doc_type = "other"
        
        if 'invoice' in filename_lower or 'bill' in filename_lower:
            doc_type = "invoice"
        elif 'contract' in filename_lower or 'agreement' in filename_lower:
            doc_type = "contract"
        elif 'report' in filename_lower:
            doc_type = "report"
        elif 'resume' in filename_lower or 'cv' in filename_lower:
            doc_type = "resume"
        
        # Extract simple topics from first few lines
        lines = text.split('\n')[:10]
        topics = []
        for line in lines:
            words = line.strip().split()
            if len(words) > 3:
                topics.append(' '.join(words[:5]))
        topics = topics[:3]
        
        # Simple entity extraction
        entities = {
            'persons': [],
            'organizations': [],
            'dates': [],
            'locations': []
        }
        
        # Find dates using regex
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b'
        dates = re.findall(date_pattern, text[:1000])
        entities['dates'] = list(set(dates))[:5]
        
        # Complexity based on text length and vocabulary
        words = text.split()
        unique_words = len(set(w.lower() for w in words))
        complexity = min(1.0, unique_words / max(len(words), 1))
        
        return SemanticAnalysis(
            document_type=doc_type,
            primary_language="English",
            topics=topics,
            entities=entities,
            sections=[],
            key_themes=[],
            technical_domain=None,
            sentiment=None,
            complexity_score=complexity,
            summary_context=f"Document: {filename} ({len(text)} characters)"
        )
    
    def get_agent_info(self) -> Dict[str, str]:
        """Return agent information for UI display"""
        return {
            "name": self.AGENT_NAME,
            "title": self.AGENT_TITLE,
            "full_name": self.name,
            "description": self.AGENT_DESCRIPTION,
            "icon": "📚",
            "role": "semantic_analyzer"
        }
