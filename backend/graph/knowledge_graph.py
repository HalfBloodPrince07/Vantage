# backend/graph/knowledge_graph.py
"""
KnowledgeGraph
==============
NetworkX-based knowledge graph for storing and querying entity relationships.

Features:
- Entity storage with types and properties
- Relationship storage with types and weights
- Multi-hop graph traversal for query expansion
- Persistence to SQLite
"""

import networkx as nx
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import sqlite3
from pathlib import Path
from loguru import logger


@dataclass
class Entity:
    """Represents an entity in the knowledge graph"""
    id: str
    name: str
    entity_type: str  # PERSON, ORGANIZATION, LOCATION, DATE, CONCEPT, DOCUMENT
    properties: Dict[str, Any] = field(default_factory=dict)
    document_ids: List[str] = field(default_factory=list)  # Documents mentioning this entity
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "entity_type": self.entity_type,
            "properties": self.properties,
            "document_ids": self.document_ids,
            "created_at": self.created_at
        }


@dataclass
class Relationship:
    """Represents a relationship between entities"""
    source_id: str
    target_id: str
    relationship_type: str  # WORKS_FOR, LOCATED_IN, MENTIONED_IN, RELATED_TO, etc.
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    document_id: Optional[str] = None  # Document where this relationship was found
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relationship_type": self.relationship_type,
            "weight": self.weight,
            "properties": self.properties,
            "document_id": self.document_id
        }


class KnowledgeGraph:
    """
    NetworkX-based knowledge graph for entity relationships.
    
    Supports:
    - Adding/updating entities and relationships
    - Multi-hop traversal for query expansion
    - Persistence to SQLite database
    """
    
    def __init__(self, db_path: str = "locallens_graph.db"):
        self.db_path = db_path
        self.graph = nx.DiGraph()  # Directed graph for relationships
        self._entity_index: Dict[str, Entity] = {}  # id -> Entity
        self._name_index: Dict[str, Set[str]] = {}  # normalized_name -> entity_ids
        
        self._init_db()
        self._load_from_db()
        
        logger.info(f"🌐 KnowledgeGraph initialized with {len(self._entity_index)} entities")
    
    def _init_db(self):
        """Initialize SQLite database for persistence"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                properties TEXT,
                document_ids TEXT,
                created_at TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                properties TEXT,
                document_id TEXT,
                FOREIGN KEY (source_id) REFERENCES entities(id),
                FOREIGN KEY (target_id) REFERENCES entities(id)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_entity_type ON entities(entity_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_entity_name ON entities(name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_rel_source ON relationships(source_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_rel_target ON relationships(target_id)
        """)
        
        conn.commit()
        conn.close()
    
    def _load_from_db(self):
        """Load graph from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Load entities
        cursor.execute("SELECT * FROM entities")
        for row in cursor.fetchall():
            entity = Entity(
                id=row[0],
                name=row[1],
                entity_type=row[2],
                properties=json.loads(row[3]) if row[3] else {},
                document_ids=json.loads(row[4]) if row[4] else [],
                created_at=row[5]
            )
            self._entity_index[entity.id] = entity
            self.graph.add_node(entity.id, **entity.to_dict())
            
            # Build name index
            normalized = self._normalize_name(entity.name)
            if normalized not in self._name_index:
                self._name_index[normalized] = set()
            self._name_index[normalized].add(entity.id)
        
        # Load relationships
        cursor.execute("SELECT source_id, target_id, relationship_type, weight, properties, document_id FROM relationships")
        for row in cursor.fetchall():
            self.graph.add_edge(
                row[0], row[1],
                relationship_type=row[2],
                weight=row[3],
                properties=json.loads(row[4]) if row[4] else {},
                document_id=row[5]
            )
        
        conn.close()
        logger.info(f"🌐 Loaded {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges from database")
    
    def _normalize_name(self, name: str) -> str:
        """Normalize entity name for matching"""
        return name.lower().strip()
    
    def add_entity(
        self,
        entity_id: str,
        name: str,
        entity_type: str,
        properties: Optional[Dict[str, Any]] = None,
        document_id: Optional[str] = None
    ) -> Entity:
        """Add or update an entity in the graph"""
        
        if entity_id in self._entity_index:
            # Update existing entity
            entity = self._entity_index[entity_id]
            if document_id and document_id not in entity.document_ids:
                entity.document_ids.append(document_id)
            if properties:
                entity.properties.update(properties)
            self.graph.nodes[entity_id].update(entity.to_dict())
        else:
            # Create new entity
            entity = Entity(
                id=entity_id,
                name=name,
                entity_type=entity_type,
                properties=properties or {},
                document_ids=[document_id] if document_id else []
            )
            self._entity_index[entity_id] = entity
            self.graph.add_node(entity_id, **entity.to_dict())
            
            # Update name index
            normalized = self._normalize_name(name)
            if normalized not in self._name_index:
                self._name_index[normalized] = set()
            self._name_index[normalized].add(entity_id)
        
        # Persist to database
        self._save_entity(entity)
        
        return entity
    
    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        weight: float = 1.0,
        properties: Optional[Dict[str, Any]] = None,
        document_id: Optional[str] = None
    ) -> bool:
        """Add a relationship between entities"""
        
        if source_id not in self._entity_index or target_id not in self._entity_index:
            logger.warning(f"Cannot add relationship: entity not found ({source_id} -> {target_id})")
            return False
        
        # Check if relationship already exists
        if self.graph.has_edge(source_id, target_id):
            # Update weight (increase connection strength)
            current_weight = self.graph[source_id][target_id].get('weight', 1.0)
            self.graph[source_id][target_id]['weight'] = current_weight + weight
        else:
            # Add new edge
            self.graph.add_edge(
                source_id, target_id,
                relationship_type=relationship_type,
                weight=weight,
                properties=properties or {},
                document_id=document_id
            )
        
        # Persist to database
        self._save_relationship(source_id, target_id, relationship_type, weight, properties, document_id)
        
        return True
    
    def _save_entity(self, entity: Entity):
        """Save entity to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO entities (id, name, entity_type, properties, document_ids, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            entity.id,
            entity.name,
            entity.entity_type,
            json.dumps(entity.properties),
            json.dumps(entity.document_ids),
            entity.created_at
        ))
        
        conn.commit()
        conn.close()
    
    def _save_relationship(
        self, source_id: str, target_id: str, rel_type: str,
        weight: float, properties: Optional[Dict], document_id: Optional[str]
    ):
        """Save relationship to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO relationships (source_id, target_id, relationship_type, weight, properties, document_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            source_id, target_id, rel_type, weight,
            json.dumps(properties) if properties else None,
            document_id
        ))
        
        conn.commit()
        conn.close()
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID"""
        return self._entity_index.get(entity_id)
    
    def find_entities_by_name(self, name: str) -> List[Entity]:
        """Find entities by name (case-insensitive)"""
        normalized = self._normalize_name(name)
        entity_ids = self._name_index.get(normalized, set())
        return [self._entity_index[eid] for eid in entity_ids if eid in self._entity_index]
    
    def find_entities_by_type(self, entity_type: str) -> List[Entity]:
        """Find all entities of a given type"""
        return [e for e in self._entity_index.values() if e.entity_type == entity_type]
    
    def get_related_entities(
        self,
        entity_id: str,
        hops: int = 2,
        relationship_types: Optional[List[str]] = None
    ) -> List[Tuple[Entity, int, str]]:
        """
        Get entities related to the given entity within N hops.
        
        Returns:
            List of (entity, distance, relationship_type)
        """
        if entity_id not in self._entity_index:
            return []
        
        related = []
        visited = {entity_id}
        current_level = [entity_id]
        
        for distance in range(1, hops + 1):
            next_level = []
            for node in current_level:
                # Get both outgoing and incoming edges
                for neighbor in self.graph.successors(node):
                    if neighbor not in visited:
                        edge_data = self.graph[node][neighbor]
                        rel_type = edge_data.get('relationship_type', 'RELATED_TO')
                        
                        if relationship_types is None or rel_type in relationship_types:
                            related.append((self._entity_index[neighbor], distance, rel_type))
                            visited.add(neighbor)
                            next_level.append(neighbor)
                
                for neighbor in self.graph.predecessors(node):
                    if neighbor not in visited:
                        edge_data = self.graph[neighbor][node]
                        rel_type = edge_data.get('relationship_type', 'RELATED_TO')
                        
                        if relationship_types is None or rel_type in relationship_types:
                            related.append((self._entity_index[neighbor], distance, rel_type))
                            visited.add(neighbor)
                            next_level.append(neighbor)
            
            current_level = next_level
        
        return related
    
    def expand_query_entities(
        self,
        entities: List[str],
        hops: int = 1,
        max_expansion: int = 10
    ) -> List[str]:
        """
        Expand a list of entity names to include related entities.
        
        Args:
            entities: List of entity names from the query
            hops: Number of hops to traverse
            max_expansion: Maximum number of entities to add
            
        Returns:
            Expanded list of entity names
        """
        expanded = set(entities)
        
        for entity_name in entities:
            # Find matching entities
            matching = self.find_entities_by_name(entity_name)
            
            for entity in matching:
                # Get related entities
                related = self.get_related_entities(entity.id, hops=hops)
                
                for rel_entity, distance, rel_type in related:
                    if len(expanded) >= len(entities) + max_expansion:
                        break
                    expanded.add(rel_entity.name)
        
        return list(expanded)
    
    def get_entity_context(self, entity_id: str) -> Dict[str, Any]:
        """Get full context for an entity including all relationships"""
        entity = self.get_entity(entity_id)
        if not entity:
            return {}
        
        # Get all relationships
        outgoing = []
        for neighbor in self.graph.successors(entity_id):
            edge_data = self.graph[entity_id][neighbor]
            neighbor_entity = self._entity_index.get(neighbor)
            if neighbor_entity:
                outgoing.append({
                    "target": neighbor_entity.name,
                    "target_type": neighbor_entity.entity_type,
                    "relationship": edge_data.get('relationship_type'),
                    "weight": edge_data.get('weight', 1.0)
                })
        
        incoming = []
        for neighbor in self.graph.predecessors(entity_id):
            edge_data = self.graph[neighbor][entity_id]
            neighbor_entity = self._entity_index.get(neighbor)
            if neighbor_entity:
                incoming.append({
                    "source": neighbor_entity.name,
                    "source_type": neighbor_entity.entity_type,
                    "relationship": edge_data.get('relationship_type'),
                    "weight": edge_data.get('weight', 1.0)
                })
        
        return {
            "entity": entity.to_dict(),
            "outgoing_relationships": outgoing,
            "incoming_relationships": incoming,
            "total_connections": len(outgoing) + len(incoming)
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics"""
        return {
            "total_entities": len(self._entity_index),
            "total_relationships": self.graph.number_of_edges(),
            "entity_types": {
                etype: len([e for e in self._entity_index.values() if e.entity_type == etype])
                for etype in set(e.entity_type for e in self._entity_index.values())
            }
        }
