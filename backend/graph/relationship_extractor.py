# backend/graph/relationship_extractor.py
"""
RelationshipExtractor
=====================
LLM-based extraction of relationships between entities.

Extracts relationships like:
- WORKS_FOR: person -> organization
- LOCATED_IN: entity -> location
- MENTIONED_IN: entity -> document
- RELATED_TO: generic relationship
- PART_OF: entity -> larger entity
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json
from loguru import logger

from backend.utils.llm_utils import call_ollama_json


@dataclass
class ExtractedRelationship:
    """A relationship extracted from text"""
    source_entity: str
    source_type: str
    target_entity: str
    target_type: str
    relationship_type: str
    confidence: float
    evidence: str  # Text snippet supporting this relationship
    

class RelationshipExtractor:
    """
    LLM-based relationship extraction between entities.
    
    Uses structured prompts to identify relationships
    between entities mentioned in text.
    """
    
    AGENT_NAME = "Hephaestus"
    AGENT_TITLE = "The Smith"
    AGENT_DESCRIPTION = "God of craftsmanship - I forge connections between entities"
    
    # Relationship types we extract
    RELATIONSHIP_TYPES = [
        "WORKS_FOR",      # person -> organization
        "WORKS_WITH",     # person -> person
        "LOCATED_IN",     # entity -> location
        "PART_OF",        # entity -> larger entity
        "OWNS",           # entity -> asset
        "CREATED_BY",     # artifact -> creator
        "MENTIONS",       # document -> entity
        "OCCURRED_ON",    # event -> date
        "RELATED_TO",     # generic fallback
    ]
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ollama_url = config['ollama']['base_url']
        self.model = config['ollama']['text_model']['name']
        
        logger.info(f"🔧 {self.AGENT_NAME} ({self.AGENT_TITLE}) initialized")
    
    async def extract_relationships(
        self,
        text: str,
        entities: List[Dict[str, Any]],
        document_id: Optional[str] = None
    ) -> List[ExtractedRelationship]:
        """
        Extract relationships between entities from text.
        
        Args:
            text: Source text to analyze
            entities: List of entities found in the text
            document_id: Optional document ID for context
            
        Returns:
            List of extracted relationships
        """
        if len(entities) < 2:
            return []  # Need at least 2 entities for relationships
        
        # Format entities for the prompt
        entity_list = "\n".join([
            f"- {e.get('name', 'Unknown')} ({e.get('entity_type', 'UNKNOWN')})"
            for e in entities[:15]  # Limit to avoid token overflow
        ])
        
        # Truncate text if too long
        text_preview = text[:3000] if len(text) > 3000 else text
        
        prompt = f"""Analyze the following text and extract relationships between the listed entities.

ENTITIES FOUND:
{entity_list}

TEXT:
{text_preview}

RELATIONSHIP TYPES TO IDENTIFY:
- WORKS_FOR: person works for an organization
- WORKS_WITH: person collaborates with another person
- LOCATED_IN: entity is located in a place
- PART_OF: entity is part of a larger entity
- OWNS: entity owns an asset or organization
- CREATED_BY: something was created by someone
- OCCURRED_ON: event happened on a date
- RELATED_TO: generic relationship (use sparingly)

For each relationship you can identify, provide:
1. Source entity (exactly as listed above)
2. Target entity (exactly as listed above)  
3. Relationship type (from the list above)
4. Confidence (0.0-1.0)
5. Evidence (brief quote from text supporting this)

Return a JSON array of relationships:
{{
    "relationships": [
        {{
            "source": "Entity Name",
            "source_type": "ENTITY_TYPE",
            "target": "Entity Name", 
            "target_type": "ENTITY_TYPE",
            "relationship": "RELATIONSHIP_TYPE",
            "confidence": 0.85,
            "evidence": "brief supporting quote"
        }}
    ]
}}

Only include relationships you are confident about (confidence >= 0.6).
If no clear relationships exist, return {{"relationships": []}}"""

        try:
            fallback = {"relationships": []}
            
            result = await call_ollama_json(
                base_url=self.ollama_url,
                model=self.model,
                prompt=prompt,
                max_retries=2,
                timeout=self.config['ollama'].get('timeout', 120.0),
                temperature=0.2,
                fallback_data=fallback,
                model_type="text",
                config=self.config
            )
            
            relationships = []
            for rel in result.get('relationships', []):
                try:
                    extracted = ExtractedRelationship(
                        source_entity=rel.get('source', ''),
                        source_type=rel.get('source_type', 'UNKNOWN'),
                        target_entity=rel.get('target', ''),
                        target_type=rel.get('target_type', 'UNKNOWN'),
                        relationship_type=rel.get('relationship', 'RELATED_TO'),
                        confidence=float(rel.get('confidence', 0.5)),
                        evidence=rel.get('evidence', '')
                    )
                    
                    # Validate relationship type
                    if extracted.relationship_type not in self.RELATIONSHIP_TYPES:
                        extracted.relationship_type = 'RELATED_TO'
                    
                    if extracted.confidence >= 0.6:
                        relationships.append(extracted)
                        
                except Exception as e:
                    logger.warning(f"Failed to parse relationship: {e}")
                    continue
            
            logger.info(f"🔧 Extracted {len(relationships)} relationships from text")
            return relationships
            
        except Exception as e:
            logger.error(f"Relationship extraction failed: {e}")
            return []
    
    async def infer_implicit_relationships(
        self,
        entities: List[Dict[str, Any]]
    ) -> List[ExtractedRelationship]:
        """
        Infer implicit relationships based on entity co-occurrence.
        
        If entities appear in the same document, they may be related.
        """
        relationships = []
        
        # Group entities by document
        doc_entities: Dict[str, List[Dict]] = {}
        for entity in entities:
            for doc_id in entity.get('document_ids', []):
                if doc_id not in doc_entities:
                    doc_entities[doc_id] = []
                doc_entities[doc_id].append(entity)
        
        # Create CO_OCCURS_WITH relationships for entities in same document
        for doc_id, doc_ents in doc_entities.items():
            for i, ent1 in enumerate(doc_ents):
                for ent2 in doc_ents[i+1:]:
                    relationships.append(ExtractedRelationship(
                        source_entity=ent1.get('name', ''),
                        source_type=ent1.get('entity_type', 'UNKNOWN'),
                        target_entity=ent2.get('name', ''),
                        target_type=ent2.get('entity_type', 'UNKNOWN'),
                        relationship_type='RELATED_TO',
                        confidence=0.5,  # Lower confidence for implicit
                        evidence=f"Co-occur in document {doc_id}"
                    ))
        
        return relationships
    
    def get_agent_info(self) -> Dict[str, str]:
        """Return agent information for UI display"""
        return {
            "name": self.AGENT_NAME,
            "title": self.AGENT_TITLE,
            "full_name": f"{self.AGENT_NAME} ({self.AGENT_TITLE})",
            "description": self.AGENT_DESCRIPTION,
            "icon": "🔧",
            "role": "relationship_extractor"
        }
