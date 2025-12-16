# backend/agents/graph_rag_agent.py
"""
GraphRAGAgent (Apollo)
======================
Apollo - The Illuminated One - Graph-enhanced retrieval agent.

Uses knowledge graph to:
- Expand queries with related entities
- Find connected documents via entity relationships
- Provide entity-aware context for answers
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

from backend.graph.knowledge_graph import KnowledgeGraph, Entity
from backend.graph.entity_resolver import EntityResolver
from backend.graph.relationship_extractor import RelationshipExtractor


@dataclass
class GraphExpansion:
    """Result of graph-based query expansion"""
    original_entities: List[str]
    expanded_entities: List[str]
    related_documents: List[str]
    entity_context: Dict[str, Any]
    expansion_path: List[Dict[str, Any]]  # How we got from original to expanded


@dataclass 
class GraphRAGResult:
    """Result of graph-enhanced retrieval"""
    expanded_query: str
    original_query: str
    expansion: GraphExpansion
    graph_context: str  # Formatted context about entities
    confidence: float


class GraphRAGAgent:
    """
    Apollo - The Illuminated One
    
    God of light and knowledge - I illuminate connections between
    entities to enhance retrieval with graph-based context.
    
    Responsibilities:
    - Query expansion via graph traversal
    - Entity-aware document retrieval
    - Building contextual knowledge for answers
    """
    
    AGENT_NAME = "Apollo"
    AGENT_TITLE = "The Illuminated One"
    AGENT_DESCRIPTION = "God of light - I illuminate connections between entities"
    AGENT_ICON = "🌐"
    
    def __init__(
        self,
        config: Dict[str, Any],
        knowledge_graph: Optional[KnowledgeGraph] = None
    ):
        self.config = config
        self.name = f"{self.AGENT_NAME} ({self.AGENT_TITLE})"
        
        # Initialize or use provided knowledge graph
        self.graph = knowledge_graph or KnowledgeGraph()
        self.entity_resolver = EntityResolver()
        self.relationship_extractor = RelationshipExtractor(config)
        
        logger.info(f"🌐 {self.name} initialized with {self.graph.get_stats()['total_entities']} entities")
    
    async def expand_query(
        self,
        query: str,
        extracted_entities: List[str],
        max_hops: int = 2,
        max_expansion: int = 10
    ) -> GraphExpansion:
        """
        Expand query by finding related entities in the knowledge graph.
        
        Args:
            query: Original user query
            extracted_entities: Entities extracted from query by Athena/classifier
            max_hops: Maximum graph traversal depth
            max_expansion: Maximum number of entities to add
            
        Returns:
            GraphExpansion with expanded entities and context
        """
        expansion_path = []
        related_documents = set()
        entity_context = {}
        
        # Find entities in graph
        matched_entities = []
        for entity_name in extracted_entities:
            found = self.graph.find_entities_by_name(entity_name)
            if found:
                matched_entities.extend(found)
                expansion_path.append({
                    "step": "matched",
                    "entity": entity_name,
                    "found_ids": [e.id for e in found]
                })
        
        # Get related entities via graph traversal
        expanded_names = set(extracted_entities)
        
        for entity in matched_entities:
            # Add documents this entity appears in
            related_documents.update(entity.document_ids)
            
            # Get entity context
            context = self.graph.get_entity_context(entity.id)
            entity_context[entity.name] = context
            
            # Traverse graph for related entities
            related = self.graph.get_related_entities(entity.id, hops=max_hops)
            
            for rel_entity, distance, rel_type in related:
                if len(expanded_names) >= len(extracted_entities) + max_expansion:
                    break
                    
                expanded_names.add(rel_entity.name)
                related_documents.update(rel_entity.document_ids)
                
                expansion_path.append({
                    "step": "expanded",
                    "from": entity.name,
                    "to": rel_entity.name,
                    "relationship": rel_type,
                    "distance": distance
                })
        
        # Log expansion
        new_entities = expanded_names - set(extracted_entities)
        if new_entities:
            logger.info(f"🌐 Apollo expanded query with {len(new_entities)} related entities: {list(new_entities)[:5]}")
        
        return GraphExpansion(
            original_entities=extracted_entities,
            expanded_entities=list(expanded_names),
            related_documents=list(related_documents),
            entity_context=entity_context,
            expansion_path=expansion_path
        )
    
    async def enhance_retrieval(
        self,
        query: str,
        extracted_entities: List[str],
        search_results: List[Dict[str, Any]]
    ) -> GraphRAGResult:
        """
        Enhance retrieval results with graph context.
        
        Args:
            query: Original query
            extracted_entities: Entities from query
            search_results: Results from vector/BM25 search
            
        Returns:
            GraphRAGResult with enhanced context
        """
        # Expand query via graph
        expansion = await self.expand_query(query, extracted_entities)
        
        # Build expanded query string
        if expansion.expanded_entities != expansion.original_entities:
            additional = [e for e in expansion.expanded_entities if e not in expansion.original_entities]
            expanded_query = f"{query} (related: {', '.join(additional[:5])})"
        else:
            expanded_query = query
        
        # Build graph context string for LLM
        graph_context = self._format_graph_context(expansion)
        
        # Calculate confidence based on graph coverage
        confidence = self._calculate_confidence(expansion, search_results)
        
        return GraphRAGResult(
            expanded_query=expanded_query,
            original_query=query,
            expansion=expansion,
            graph_context=graph_context,
            confidence=confidence
        )
    
    def _format_graph_context(self, expansion: GraphExpansion) -> str:
        """Format graph context for LLM prompt injection"""
        lines = []
        
        if expansion.entity_context:
            lines.append("**Entity Knowledge Graph Context:**")
            
            for entity_name, context in list(expansion.entity_context.items())[:5]:
                entity = context.get('entity', {})
                lines.append(f"\n• **{entity_name}** ({entity.get('entity_type', 'Unknown')})")
                
                # Add relationships
                outgoing = context.get('outgoing_relationships', [])[:3]
                for rel in outgoing:
                    lines.append(f"  → {rel['relationship']} → {rel['target']}")
                
                incoming = context.get('incoming_relationships', [])[:3]
                for rel in incoming:
                    lines.append(f"  ← {rel['relationship']} ← {rel['source']}")
        
        if expansion.expansion_path:
            expanded = [p for p in expansion.expansion_path if p['step'] == 'expanded']
            if expanded:
                lines.append(f"\n**Related entities discovered:** {len(expanded)}")
        
        return "\n".join(lines) if lines else ""
    
    def _calculate_confidence(
        self,
        expansion: GraphExpansion,
        search_results: List[Dict[str, Any]]
    ) -> float:
        """Calculate confidence based on graph coverage"""
        if not expansion.original_entities:
            return 0.5  # No entities to match
        
        # Check how many entities we found in graph
        matched = len([e for e in expansion.expansion_path if e.get('step') == 'matched'])
        total = len(expansion.original_entities)
        
        graph_coverage = matched / total if total > 0 else 0
        
        # Check if search results include graph-related documents
        result_doc_ids = {r.get('id') for r in search_results if r.get('id')}
        graph_doc_ids = set(expansion.related_documents)
        
        if result_doc_ids and graph_doc_ids:
            doc_overlap = len(result_doc_ids & graph_doc_ids) / len(result_doc_ids)
        else:
            doc_overlap = 0
        
        # Weighted confidence
        confidence = 0.5 + (graph_coverage * 0.3) + (doc_overlap * 0.2)
        return min(confidence, 1.0)
    
    async def index_document_entities(
        self,
        document_id: str,
        entities: List[Dict[str, Any]],
        text: str
    ):
        """
        Index entities and relationships from a document into the graph.
        
        Called during document ingestion to build the knowledge graph.
        """
        # Get existing entities for resolution
        existing = [e.to_dict() for e in self.graph._entity_index.values()]
        
        indexed_entities = []
        
        for entity_data in entities:
            name = entity_data.get('name', '')
            etype = entity_data.get('type', entity_data.get('entity_type', 'UNKNOWN'))
            
            if not name:
                continue
            
            # Try to resolve to existing entity
            resolved = self.entity_resolver.resolve(name, etype, existing)
            
            if resolved:
                # Update existing entity with new document reference
                entity = self.graph.add_entity(
                    entity_id=resolved.canonical_id,
                    name=resolved.canonical_name,
                    entity_type=etype,
                    document_id=document_id
                )
            else:
                # Create new entity
                entity_id = f"{etype.lower()}_{name.lower().replace(' ', '_')}_{document_id[:8]}"
                entity = self.graph.add_entity(
                    entity_id=entity_id,
                    name=name,
                    entity_type=etype,
                    document_id=document_id
                )
                # Add to existing for subsequent resolution
                existing.append(entity.to_dict())
            
            indexed_entities.append(entity)
        
        # Extract and add relationships
        if len(indexed_entities) >= 2:
            entity_dicts = [e.to_dict() for e in indexed_entities]
            relationships = await self.relationship_extractor.extract_relationships(
                text, entity_dicts, document_id
            )
            
            for rel in relationships:
                # Find entity IDs
                source_entities = self.graph.find_entities_by_name(rel.source_entity)
                target_entities = self.graph.find_entities_by_name(rel.target_entity)
                
                if source_entities and target_entities:
                    self.graph.add_relationship(
                        source_id=source_entities[0].id,
                        target_id=target_entities[0].id,
                        relationship_type=rel.relationship_type,
                        weight=rel.confidence,
                        properties={"evidence": rel.evidence},
                        document_id=document_id
                    )
        
        logger.info(f"🌐 Indexed {len(indexed_entities)} entities from document {document_id}")
        return indexed_entities
    
    def get_entity_suggestions(self, partial_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get entity suggestions for autocomplete"""
        partial_lower = partial_name.lower()
        suggestions = []
        
        for entity in self.graph._entity_index.values():
            if partial_lower in entity.name.lower():
                suggestions.append({
                    "name": entity.name,
                    "type": entity.entity_type,
                    "document_count": len(entity.document_ids)
                })
                if len(suggestions) >= limit:
                    break
        
        # Sort by document count (popularity)
        suggestions.sort(key=lambda x: x['document_count'], reverse=True)
        return suggestions
    
    def get_agent_info(self) -> Dict[str, str]:
        """Return agent information for UI display"""
        return {
            "name": self.AGENT_NAME,
            "title": self.AGENT_TITLE,
            "full_name": self.name,
            "description": self.AGENT_DESCRIPTION,
            "icon": self.AGENT_ICON,
            "role": "graph_rag"
        }
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics"""
        return self.graph.get_stats()
