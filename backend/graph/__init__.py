# backend/graph/__init__.py
"""
Knowledge Graph Module
======================
Graph-based RAG components for entity-aware retrieval.

Components:
- KnowledgeGraph: NetworkX-based entity graph
- EntityResolver: Cross-document entity linking
- RelationshipExtractor: LLM-based relationship extraction
- GraphRAGAgent: Graph-enhanced retrieval agent (Apollo)
"""

from .knowledge_graph import KnowledgeGraph
from .entity_resolver import EntityResolver
from .relationship_extractor import RelationshipExtractor

__all__ = [
    "KnowledgeGraph",
    "EntityResolver", 
    "RelationshipExtractor"
]
