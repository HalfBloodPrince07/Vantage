# backend/agents/query_classifier.py
"""
Query Classification & Intent Router

Classifies queries into:
- Document Search: Needs to search indexed documents
- General Knowledge: Can be answered directly by LLM
- System/Meta: Questions about the system
- Comparison: Comparing multiple documents
- Summarization: Multi-document summarization
- Clarification Needed: Ambiguous queries
"""

from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import re
import httpx
from loguru import logger
import json
from backend.utils.llm_utils import call_ollama_json


class QueryIntent(Enum):
    """Query intent types"""
    DOCUMENT_SEARCH = "document_search"
    GENERAL_KNOWLEDGE = "general_knowledge"
    SYSTEM_META = "system_meta"
    COMPARISON = "comparison"
    SUMMARIZATION = "summarization"
    ANALYSIS = "analysis"
    CLARIFICATION_NEEDED = "clarification_needed"


@dataclass
class ClassificationResult:
    """Result of query classification"""
    intent: QueryIntent
    confidence: float
    sub_intent: Optional[str] = None
    entities: List[str] = None
    filters: Optional[Dict] = None
    clarification_questions: List[str] = None
    reasoning: str = ""

    def __post_init__(self):
        if self.entities is None:
            self.entities = []
        if self.clarification_questions is None:
            self.clarification_questions = []


class QueryClassifier:
    AGENT_NAME = "Athena"
    AGENT_TITLE = "The Strategist"
    AGENT_DESCRIPTION = "Goddess of wisdom - I classify and understand your intent"

    def __init__(self, config: Dict[str, Any]):
        self.name = f"{self.AGENT_NAME} ({self.AGENT_TITLE})"
        self.config = config
        self.ollama_url = config['ollama']['base_url']
        self.model = config['ollama']['text_model']['name']

        # Document-related keywords (HIGH PRIORITY - check first)
        self.doc_keywords = [
            "find", "search", "show", "show me", "get", "give me", "list",
            "document", "file", "invoice", "contract", "report", 
            "spreadsheet", "image", "images", "photo", "photos", "picture", "pictures",
            "pdf", "where is", "locate", "my", "our", "the"
        ]
        
        # Image-specific keywords (VERY HIGH PRIORITY)
        self.image_keywords = [
            "image", "images", "photo", "photos", "picture", "pictures",
            "screenshot", "screenshots", "pic", "pics", "containing",
            "showing", "with", "of"
        ]

        # General knowledge keywords
        self.general_keywords = [
            "what is", "who is", "how to", "explain", "define", "tell me about",
            "why does", "how does", "when did"
        ]

        # Comparison keywords
        self.comparison_keywords = [
            "compare", "difference", "versus", "vs", "better", "contrast",
            "similarities", "which one"
        ]

        # Summarization keywords
        self.summary_keywords = [
            "summarize", "summary", "overview", "recap", "all documents about",
            "everything about", "compile", "aggregate"
        ]

    async def classify(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Classify query into intent type - ENHANCED with context resolution
        
        Args:
            query: User query
            context: Optional session context for better classification
        
        Returns:
            Dict with agent info and classification result
        """
        # Resolve follow-up references first
        resolved_query, is_followup = self._resolve_followup(query, context)
        
        # Extract entities from the resolved query
        entities = self.extract_entities(resolved_query)
        
        # Try rule-based first (fast path)
        rule_result = self._rule_based_classify(resolved_query, context)
        
        # Add extracted entities if not already present
        if entities and not rule_result.entities:
            rule_result.entities = entities

        # If confidence is high, return immediately
        if rule_result.confidence > 0.8:
            logger.info(f"Rule-based classification: {rule_result.intent.value} (confidence: {rule_result.confidence})")
            return {
                "agent": self.name,
                "intent": rule_result.intent,
                "confidence": rule_result.confidence,
                "filters": rule_result.filters,
                "entities": rule_result.entities or entities,
                "reasoning": rule_result.reasoning,
                "is_followup": is_followup,
                "resolved_query": resolved_query if is_followup else None
            }

        # Otherwise, use LLM for better accuracy
        llm_result = await self._llm_classify(resolved_query, context)

        # Combine results (LLM has final say, but add extracted entities)
        combined_entities = list(set((llm_result.entities or []) + entities))
        
        return {
            "agent": self.name,
            "intent": llm_result.intent,
            "confidence": llm_result.confidence,
            "filters": llm_result.filters,
            "entities": combined_entities,
            "reasoning": llm_result.reasoning,
            "clarification_questions": llm_result.clarification_questions,
            "is_followup": is_followup,
            "resolved_query": resolved_query if is_followup else None
        }

    def _resolve_followup(self, query: str, context: Optional[Dict]) -> tuple:
        """
        Resolve follow-up queries that reference previous queries/results
        
        Returns:
            Tuple of (resolved_query, is_followup)
        """
        if not context:
            return query, False
        
        q_lower = query.lower()
        recent_queries = context.get("recent_queries", [])
        last_query = recent_queries[-1] if recent_queries else None
        
        # Pattern 1: "show more" / "more like that" / "similar"
        if any(phrase in q_lower for phrase in ["show more", "more like", "similar", "like that", "like those"]):
            if last_query:
                logger.info(f"Follow-up detected: expanding previous query")
                return f"{last_query} (more results)", True
        
        # Pattern 2: "but only" / "only the" - adding filter to previous query
        filter_phrases = ["but only", "only the", "just the", "filter by", "filter to"]
        for phrase in filter_phrases:
            if phrase in q_lower and last_query:
                # Extract the filter part and combine with previous query
                filter_part = q_lower.split(phrase)[-1].strip()
                combined = f"{last_query} {filter_part}"
                logger.info(f"Follow-up detected: adding filter to previous query")
                return combined, True
        
        # Pattern 3: Very short queries with pronouns ("that", "it", "those")
        if len(query.split()) <= 3 and any(pron in q_lower for pron in ["that", "it", "those", "this"]):
            if last_query:
                logger.info(f"Follow-up detected: pronoun reference to previous query")
                return last_query, True
        
        # Pattern 4: "what about X" - applying X to previous context
        if q_lower.startswith("what about"):
            if last_query:
                new_term = query[10:].strip()  # After "what about"
                combined = f"{last_query} {new_term}"
                logger.info(f"Follow-up detected: 'what about' pattern")
                return combined, True
        
        return query, False

    def _rule_based_classify(self, query: str, context: Optional[Dict]) -> ClassificationResult:
        """Fast rule-based classification"""
        q_lower = query.lower()

        # Check for system/meta queries
        if any(kw in q_lower for kw in ["how does this work", "how do i", "what can you", "can you help"]):
            return ClassificationResult(
                intent=QueryIntent.SYSTEM_META,
                confidence=0.9,
                reasoning="System help query"
            )
        
        # PRIORITY 1: Check for image/photo searches (HIGHEST PRIORITY)
        # Queries like "show me images", "find photos", "pictures of X"
        if any(kw in q_lower for kw in ["image", "images", "photo", "photos", "picture", "pictures", "screenshot"]):
            if any(action in q_lower for action in ["show", "find", "search", "get", "give", "list", "locate"]):
                # This is clearly a file search: "show me images", "find photos"
                filters = self._extract_filters(query)
                return ClassificationResult(
                    intent=QueryIntent.DOCUMENT_SEARCH,
                    confidence=0.95,
                    filters=filters,
                    reasoning="Image/photo search in local files detected"
                )

        # PRIORITY 2: Check for comparison
        if any(kw in q_lower for kw in self.comparison_keywords):
            return ClassificationResult(
                intent=QueryIntent.COMPARISON,
                confidence=0.85,
                reasoning="Comparison keywords detected"
            )

        # PRIORITY 3: Check for summarization
        if any(kw in q_lower for kw in self.summary_keywords):
            return ClassificationResult(
                intent=QueryIntent.SUMMARIZATION,
                confidence=0.85,
                reasoning="Summarization keywords detected"
            )

        # PRIORITY 4: Check for document search
        # Queries with "my", "our", "the" + file type are local searches
        has_possessive = any(kw in q_lower for kw in ["my", "our", "the"])
        has_doc_keyword = any(kw in q_lower for kw in self.doc_keywords)
        
        if has_doc_keyword and (has_possessive or any(kw in q_lower for kw in ["show", "find", "search", "locate"])):
            # Extract document type filters
            filters = self._extract_filters(query)
            return ClassificationResult(
                intent=QueryIntent.DOCUMENT_SEARCH,
                confidence=0.85,
                filters=filters,
                reasoning="Document search keywords with possessive/action detected"
            )

        # PRIORITY 5: Check for general knowledge (LOWER PRIORITY)
        # Only if it has question words and NO file-related terms
        if any(kw in q_lower for kw in self.general_keywords):
            # BUT if has doc keywords, still classify as doc search
            if has_doc_keyword:
                return ClassificationResult(
                    intent=QueryIntent.DOCUMENT_SEARCH,
                    confidence=0.7,
                    reasoning="Has both general and doc keywords - defaulting to doc search"
                )
            return ClassificationResult(
                intent=QueryIntent.GENERAL_KNOWLEDGE,
                confidence=0.75,
                reasoning="General knowledge question pattern"
            )

        # Default to document search with medium confidence
        return ClassificationResult(
            intent=QueryIntent.DOCUMENT_SEARCH,
            confidence=0.6,
            reasoning="Default to local file search"
        )

    async def _llm_classify(self, query: str, context: Optional[Dict]) -> ClassificationResult:
        """
        LLM-based classification for complex queries

        Uses structured output with Ollama
        """
        context_str = ""
        if context:
            recent_queries = context.get("recent_queries", [])
            if recent_queries:
                context_str = f"\nRecent queries: {', '.join(recent_queries[-3:])}"

        # Enhanced prompt with few-shot examples
        prompt = f"""You are a query classifier for a personal document search system. Classify the user's query.

IMPORTANT: This is a LOCAL document search system, NOT a web search engine. Users search their own files (PDFs, images, documents, etc.).

Query: "{query}"
{context_str}

INTENTS (choose ONE):
1. DOCUMENT_SEARCH - User wants to find/retrieve specific files
   Examples: "find my resume", "show images from vacation", "where is the contract"
   
2. ANALYSIS - User wants to compare documents or extract patterns
   Examples: "compare these reports", "what's different between V1 and V2"
   
3. SUMMARIZATION - User wants a summary of document content
   Examples: "summarize the meeting notes", "give me an overview of this document"
   
4. GENERAL_KNOWLEDGE - User asks a general question NOT about their local files
   Examples: "what is machine learning?", "explain quantum computing"
   
5. COMPARISON - User wants to compare specific documents
   Examples: "compare Q1 vs Q2 reports", "difference between these contracts"
   
6. CLARIFICATION_NEEDED - Query is too vague to understand
   Examples: "show me that thing", "find it"
   
7. SYSTEM_META - User asks about this system's capabilities
   Examples: "what can you do?", "how do I use this?"

KEY SIGNALS:
- "my", "our", "the" + file type → DOCUMENT_SEARCH
- "find", "show", "search", "where", "locate" → DOCUMENT_SEARCH
- Person names + document type → DOCUMENT_SEARCH (e.g., "Aditya's resume")
- "what is X", "explain X" (general topic) → GENERAL_KNOWLEDGE
- "summarize", "overview", "recap" → SUMMARIZATION
- "compare", "difference", "vs" → COMPARISON

Return valid JSON:
{{
  "intent": "INTENT_NAME",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation",
  "entities": ["extracted", "entities"],
  "filters": {{"file_type": [".pdf"], "time_range": "last_month"}},
  "clarification_questions": []
}}"""

        try:
            # Use centralized JSON call with fallback
            fallback_data = {
                "intent": "DOCUMENT_SEARCH",
                "confidence": 0.5,
                "reasoning": "LLM classification failed, using default",
                "entities": [],
                "filters": None,
                "clarification_questions": []
            }
            
            classification = await call_ollama_json(
                base_url=self.ollama_url,
                model=self.model,
                prompt=prompt,
                max_retries=3,
                timeout=self.config['ollama'].get('timeout', 120.0),
                temperature=0.1,
                fallback_data=fallback_data,
                model_type="text",
                config=self.config
            )

            intent_str = classification.get('intent', 'DOCUMENT_SEARCH')
            try:
                intent = QueryIntent[intent_str]
            except KeyError:
                logger.warning(f"Unknown intent: {intent_str}, defaulting to DOCUMENT_SEARCH")
                intent = QueryIntent.DOCUMENT_SEARCH

            return ClassificationResult(
                intent=intent,
                confidence=float(classification.get('confidence', 0.7)),
                entities=classification.get('entities', []),
                filters=classification.get('filters'),
                clarification_questions=classification.get('clarification_questions', []),
                reasoning=classification.get('reasoning', 'LLM classification')
            )

        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            # Fallback to rule-based
            return self._rule_based_classify(query, context)

    def _extract_filters(self, query: str) -> Optional[Dict]:
        """
        Extract document filters from query - ENHANCED
        
        Supports:
        - File types (pdf, image, spreadsheet)
        - Document types (invoice, contract, report)
        - Time filters (relative, absolute, quarters, ranges)
        """
        q_lower = query.lower()
        filters = {}

        # File type filters
        file_type_map = {
            "pdf": [".pdf"],
            "word": [".docx", ".doc"],
            "excel": [".xlsx", ".xls"],
            "spreadsheet": [".xlsx", ".xls", ".csv"],
            "image": [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"],
            "photo": [".png", ".jpg", ".jpeg"],
            "picture": [".png", ".jpg", ".jpeg"],
            "video": [".mp4", ".avi", ".mov", ".mkv"],
            "audio": [".mp3", ".wav", ".flac"],
            "presentation": [".pptx", ".ppt"],
            "text": [".txt", ".md"],
            "code": [".py", ".js", ".ts", ".java", ".cpp", ".c"],
        }

        for keyword, extensions in file_type_map.items():
            if keyword in q_lower:
                filters["file_type"] = extensions
                break

        # Document type filters
        doc_type_map = {
            "invoice": "invoice",
            "contract": "contract",
            "report": "report",
            "receipt": "invoice",
            "agreement": "contract",
            "resume": "resume",
            "cv": "resume",
            "proposal": "proposal",
            "memo": "memo",
            "letter": "letter",
        }

        for keyword, doc_type in doc_type_map.items():
            if keyword in q_lower:
                filters["document_type"] = doc_type
                break

        # Time filters - ENHANCED
        time_filters = self._extract_time_filters(query)
        if time_filters:
            filters.update(time_filters)

        return filters if filters else None

    def _extract_time_filters(self, query: str) -> Optional[Dict]:
        """
        Extract richer time filters from query - NEW METHOD
        
        Supports:
        - Relative: last week, past month, recent
        - Absolute: March 2024, 2024
        - Quarters: Q1 2024, Q2
        - Ranges: from January to March
        """
        q_lower = query.lower()
        time_filter = {}

        # Relative time patterns (highest priority)
        relative_patterns = [
            (r"last\s+(\d+)\s+days?", lambda m: {"relative": f"last_{m.group(1)}_days"}),
            (r"past\s+(\d+)\s+days?", lambda m: {"relative": f"last_{m.group(1)}_days"}),
            (r"last\s+(\d+)\s+weeks?", lambda m: {"relative": f"last_{m.group(1)}_weeks"}),
            (r"past\s+(\d+)\s+weeks?", lambda m: {"relative": f"last_{m.group(1)}_weeks"}),
            (r"last\s+(\d+)\s+months?", lambda m: {"relative": f"last_{m.group(1)}_months"}),
            (r"past\s+(\d+)\s+months?", lambda m: {"relative": f"last_{m.group(1)}_months"}),
            (r"last\s+month", lambda m: {"time_range": "last_month"}),
            (r"this\s+month", lambda m: {"time_range": "this_month"}),
            (r"last\s+week", lambda m: {"time_range": "last_week"}),
            (r"this\s+week", lambda m: {"time_range": "this_week"}),
            (r"today", lambda m: {"time_range": "today"}),
            (r"yesterday", lambda m: {"time_range": "yesterday"}),
            (r"last\s+year", lambda m: {"time_range": "last_year"}),
            (r"this\s+year", lambda m: {"time_range": "this_year"}),
            (r"recent(?:ly)?", lambda m: {"time_range": "last_week"}),
        ]

        for pattern, handler in relative_patterns:
            match = re.search(pattern, q_lower)
            if match:
                return handler(match)

        # Quarter patterns (Q1 2024, Q2, etc.)
        quarter_match = re.search(r"q([1-4])(?:\s+(\d{4}))?", q_lower)
        if quarter_match:
            quarter = quarter_match.group(1)
            year = quarter_match.group(2) or "2024"
            return {"quarter": f"Q{quarter}", "year": year}

        # Month + Year patterns
        months = ["january", "february", "march", "april", "may", "june",
                  "july", "august", "september", "october", "november", "december"]
        for i, month in enumerate(months, 1):
            month_year_match = re.search(rf"{month}\s+(\d{{4}})", q_lower)
            if month_year_match:
                return {"month": i, "year": month_year_match.group(1)}
            if month in q_lower:
                return {"month": i}

        # Year patterns
        year_match = re.search(r"\b(20\d{2})\b", q_lower)
        if year_match:
            return {"year": year_match.group(1)}

        # Range patterns (from X to Y)
        range_match = re.search(r"from\s+(\w+)\s+to\s+(\w+)", q_lower)
        if range_match:
            return {"range_start": range_match.group(1), "range_end": range_match.group(2)}

        return None

    def needs_clarification(self, result: ClassificationResult) -> bool:
        """
        Determine if query needs clarification

        Returns True if:
        - Intent is CLARIFICATION_NEEDED
        - Confidence is very low
        - Has clarification questions
        """
        return (
            result.intent == QueryIntent.CLARIFICATION_NEEDED or
            result.confidence < 0.4 or
            len(result.clarification_questions) > 0
        )

    async def suggest_clarifications(self, query: str) -> List[str]:
        """
        Generate clarification questions for ambiguous query

        Returns:
            List of clarification questions
        """
        prompt = f"""The user asked: "{query}"

This query is ambiguous. Generate 2-3 clarifying questions to better understand what they're looking for.

Questions should be specific and actionable.

Respond in JSON format:
{{
    "questions": ["Question 1?", "Question 2?", "Question 3?"]
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
                        "options": {"temperature": 0.3}
                    }
                )
                result = response.json()

                # Validate response is not empty
                response_text = result.get('response', '').strip()
                if not response_text:
                    logger.warning("Empty LLM response for clarification questions")
                    return [
                        "Are you looking for a specific type of document?",
                        "Do you remember any keywords or dates associated with it?"
                    ]

                try:
                    data = json.loads(response_text)
                    return data.get('questions', [])
                except json.JSONDecodeError:
                    logger.warning("LLM response not valid JSON for clarification questions")
                    return [
                        "Are you looking for a specific type of document?",
                        "Do you remember any keywords or dates associated with it?"
                    ]

        except Exception as e:
            logger.error(f"Clarification generation failed: {e}")
            return [
                "Are you looking for a specific type of document?",
                "Do you remember any keywords or dates associated with it?"
            ]

    def extract_entities(self, query: str) -> List[str]:
        """
        Extract named entities from query - ENHANCED
        
        Extracts:
        - Quoted phrases
        - Capitalized words (names, companies)
        - Possessive references (e.g., "Aditya's" -> "Aditya")
        - Date patterns
        - Topic keywords
        """
        entities = []
        
        # 1. Extract quoted phrases (highest priority)
        quoted = re.findall(r'"([^"]+)"|\'([^\']+)\'', query)
        for match in quoted:
            phrase = match[0] or match[1]
            if phrase:
                entities.append(phrase)
        
        # 2. Extract possessive references (e.g., "Aditya's resume" -> "Aditya")
        possessive_pattern = r"\b([A-Z][a-zA-Z]+)'s\b"
        possessives = re.findall(possessive_pattern, query)
        entities.extend(possessives)
        
        # 3. Extract capitalized multi-word names (e.g., "John Smith", "Acme Corp")
        # Look for 2-3 capitalized words in sequence
        multi_word = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b', query)
        for name in multi_word:
            if name not in ["The", "This", "That", "What", "Where", "When", "Which", "How"]:
                entities.append(name)
        
        # 4. Extract standalone capitalized words (likely names/companies)
        words = query.split()
        skip_words = {"I", "A", "The", "This", "That", "What", "Where", "When", "Which", "How", 
                      "Find", "Show", "Search", "Get", "Give", "List", "All", "My", "Our"}
        for i, word in enumerate(words):
            # Clean word of punctuation
            clean_word = re.sub(r'[^\w]', '', word)
            if clean_word and clean_word[0].isupper() and clean_word not in skip_words:
                # Skip if it's at sentence start and lowercase version is common
                if i == 0:
                    continue
                if clean_word not in entities:
                    entities.append(clean_word)
        
        # 5. Extract dates (YYYY-MM-DD, YYYY, Month YYYY)
        date_patterns = [
            r'\b\d{4}-\d{2}-\d{2}\b',  # 2024-01-15
            r'\b\d{4}\b',  # 2024
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b',  # March 2024
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\b',  # Mar 2024
        ]
        for pattern in date_patterns:
            dates = re.findall(pattern, query, re.IGNORECASE)
            entities.extend(dates)
        
        # 6. Extract topic keywords after common phrases
        topic_patterns = [
            r'about\s+([a-zA-Z\s]+?)(?:\s+(?:in|from|for|by|with)|$)',  # "about machine learning"
            r'related to\s+([a-zA-Z\s]+?)(?:\s+(?:in|from|for|by|with)|$)',  # "related to AI"
            r'containing\s+([a-zA-Z\s]+?)(?:\s+(?:in|from|for|by)|$)',  # "containing project"
        ]
        for pattern in topic_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                topic = match.strip()
                if len(topic) > 2 and topic not in entities:
                    entities.append(topic)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_entities = []
        for entity in entities:
            if entity.lower() not in seen:
                seen.add(entity.lower())
                unique_entities.append(entity)
        
        return unique_entities

    def get_agent_for_intent(self, intent: QueryIntent) -> Dict[str, str]:
        """
        Get the recommended agent for a given intent.
        
        Returns:
            Dict with agent name, title, and icon for UI display
        """
        agent_map = {
            QueryIntent.DOCUMENT_SEARCH: {
                "name": "Search Agent",
                "title": "Document Search",
                "icon": "🔍",
                "next_agent": "Hermes (The Messenger)"
            },
            QueryIntent.GENERAL_KNOWLEDGE: {
                "name": "LLM",
                "title": "General Knowledge",
                "icon": "💬",
                "next_agent": "Diogenes (The Critic)"
            },
            QueryIntent.COMPARISON: {
                "name": "Aristotle",
                "title": "The Analyst",
                "icon": "📊",
                "next_agent": "Diogenes (The Critic)"
            },
            QueryIntent.ANALYSIS: {
                "name": "Aristotle",
                "title": "The Analyst",
                "icon": "📊",
                "next_agent": "Diogenes (The Critic)"
            },
            QueryIntent.SUMMARIZATION: {
                "name": "Thoth",
                "title": "The Scribe",
                "icon": "📜",
                "next_agent": "Diogenes (The Critic)"
            },
            QueryIntent.CLARIFICATION_NEEDED: {
                "name": "Socrates",
                "title": "The Inquirer",
                "icon": "🤔",
                "next_agent": None
            },
            QueryIntent.SYSTEM_META: {
                "name": "LLM",
                "title": "System Help",
                "icon": "❓",
                "next_agent": None
            }
        }
        return agent_map.get(intent, {
            "name": "Search Agent",
            "title": "Default",
            "icon": "🔍",
            "next_agent": "Hermes (The Messenger)"
        })

