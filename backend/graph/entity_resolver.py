# backend/graph/entity_resolver.py
"""
EntityResolver
==============
Cross-document entity linking and deduplication.

Resolves entities like:
- "John Smith" and "J. Smith" -> same entity
- "Microsoft" and "Microsoft Corporation" -> same entity
- "NYC" and "New York City" -> same entity
"""

from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher
from loguru import logger
import re


@dataclass
class ResolvedEntity:
    """Result of entity resolution"""
    canonical_id: str
    canonical_name: str
    aliases: List[str]
    confidence: float
    

class EntityResolver:
    """
    Resolves and links entities across documents.
    
    Uses:
    - String similarity matching
    - Alias expansion
    - Type-aware matching
    """
    
    # Common abbreviations and aliases
    KNOWN_ALIASES = {
        "usa": ["united states", "united states of america", "america", "u.s.", "u.s.a."],
        "uk": ["united kingdom", "great britain", "britain", "england"],
        "nyc": ["new york city", "new york", "ny"],
        "la": ["los angeles"],
        "sf": ["san francisco"],
        "ai": ["artificial intelligence"],
        "ml": ["machine learning"],
        "dr": ["doctor"],
        "mr": ["mister"],
        "ms": ["miss", "mrs"],
    }
    
    # Title prefixes to strip
    TITLE_PREFIXES = ["dr.", "mr.", "ms.", "mrs.", "prof.", "sir", "lord", "the"]
    
    # Common suffixes for organizations
    ORG_SUFFIXES = ["inc", "inc.", "corp", "corp.", "corporation", "llc", "ltd", "limited", "co", "company"]
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self._alias_map: Dict[str, str] = {}  # alias -> canonical_id
        self._build_alias_map()
    
    def _build_alias_map(self):
        """Build reverse alias lookup"""
        for canonical, aliases in self.KNOWN_ALIASES.items():
            for alias in aliases:
                self._alias_map[alias.lower()] = canonical
    
    def normalize(self, text: str) -> str:
        """Normalize entity text for comparison"""
        text = text.lower().strip()
        
        # Remove titles
        for prefix in self.TITLE_PREFIXES:
            if text.startswith(prefix + " "):
                text = text[len(prefix) + 1:]
        
        # Remove org suffixes
        for suffix in self.ORG_SUFFIXES:
            if text.endswith(" " + suffix):
                text = text[:-len(suffix) - 1]
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def similarity(self, text1: str, text2: str) -> float:
        """Calculate string similarity between two texts"""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def is_abbreviation(self, short: str, long: str) -> bool:
        """Check if short is an abbreviation of long"""
        short = short.lower().replace(".", "")
        long = long.lower()
        
        # Check if initials match
        words = long.split()
        if len(words) >= 2:
            initials = "".join(w[0] for w in words if w)
            if short == initials:
                return True
        
        # Check known aliases
        if short in self._alias_map:
            canonical = self._alias_map[short]
            if canonical in long or self.similarity(canonical, long) > 0.8:
                return True
        
        return False
    
    def resolve(
        self,
        entity_name: str,
        entity_type: str,
        existing_entities: List[Dict[str, Any]]
    ) -> Optional[ResolvedEntity]:
        """
        Resolve an entity against existing entities.
        
        Args:
            entity_name: Name of the entity to resolve
            entity_type: Type of entity (PERSON, ORGANIZATION, etc.)
            existing_entities: List of existing entities to match against
            
        Returns:
            ResolvedEntity if match found, None otherwise
        """
        normalized = self.normalize(entity_name)
        
        best_match = None
        best_score = 0.0
        
        for existing in existing_entities:
            # Only match same types
            if existing.get('entity_type') != entity_type:
                continue
            
            existing_name = existing.get('name', '')
            existing_normalized = self.normalize(existing_name)
            
            # Exact match after normalization
            if normalized == existing_normalized:
                return ResolvedEntity(
                    canonical_id=existing['id'],
                    canonical_name=existing_name,
                    aliases=[entity_name] if entity_name != existing_name else [],
                    confidence=1.0
                )
            
            # Similarity match
            sim = self.similarity(normalized, existing_normalized)
            if sim > best_score and sim >= self.similarity_threshold:
                best_score = sim
                best_match = existing
            
            # Abbreviation check
            if len(normalized) < len(existing_normalized):
                if self.is_abbreviation(normalized, existing_normalized):
                    return ResolvedEntity(
                        canonical_id=existing['id'],
                        canonical_name=existing_name,
                        aliases=[entity_name],
                        confidence=0.9
                    )
            elif len(normalized) > len(existing_normalized):
                if self.is_abbreviation(existing_normalized, normalized):
                    # The new entity is the better canonical name
                    return ResolvedEntity(
                        canonical_id=existing['id'],
                        canonical_name=entity_name,  # Use longer form as canonical
                        aliases=[existing_name],
                        confidence=0.9
                    )
        
        if best_match and best_score >= self.similarity_threshold:
            return ResolvedEntity(
                canonical_id=best_match['id'],
                canonical_name=best_match['name'],
                aliases=[entity_name] if entity_name != best_match['name'] else [],
                confidence=best_score
            )
        
        return None
    
    def extract_person_parts(self, name: str) -> Dict[str, str]:
        """Extract first name, last name, etc. from a person name"""
        parts = name.strip().split()
        
        if len(parts) == 1:
            return {"full": parts[0]}
        elif len(parts) == 2:
            return {"first": parts[0], "last": parts[1], "full": name}
        else:
            return {
                "first": parts[0],
                "middle": " ".join(parts[1:-1]),
                "last": parts[-1],
                "full": name
            }
    
    def match_person_names(self, name1: str, name2: str) -> float:
        """
        Match two person names with special handling.
        
        Handles:
        - "John Smith" vs "J. Smith" -> high match
        - "John Smith" vs "Smith, John" -> high match
        """
        parts1 = self.extract_person_parts(name1)
        parts2 = self.extract_person_parts(name2)
        
        # Check last name match
        last1 = parts1.get('last', parts1.get('full', ''))
        last2 = parts2.get('last', parts2.get('full', ''))
        
        if self.similarity(last1, last2) < 0.8:
            return 0.0  # Last names don't match
        
        # Check first name / initial match
        first1 = parts1.get('first', '')
        first2 = parts2.get('first', '')
        
        if first1 and first2:
            # Both have first names
            if first1[0].lower() == first2[0].lower():
                # First initials match
                if len(first1) == 1 or len(first2) == 1:
                    return 0.85  # Initial match
                else:
                    return self.similarity(first1, first2)
        
        return 0.7  # Last name only match
    
    def find_duplicates(
        self,
        entities: List[Dict[str, Any]],
        threshold: float = 0.85
    ) -> List[Tuple[str, str, float]]:
        """
        Find potential duplicate entities.
        
        Returns:
            List of (entity_id_1, entity_id_2, similarity_score)
        """
        duplicates = []
        
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                if entity1.get('entity_type') != entity2.get('entity_type'):
                    continue
                
                name1 = self.normalize(entity1.get('name', ''))
                name2 = self.normalize(entity2.get('name', ''))
                
                if entity1.get('entity_type') == 'PERSON':
                    score = self.match_person_names(name1, name2)
                else:
                    score = self.similarity(name1, name2)
                
                if score >= threshold:
                    duplicates.append((entity1['id'], entity2['id'], score))
        
        return duplicates
