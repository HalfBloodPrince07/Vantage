# backend/memory/agentic_memory/note.py
"""
AgenticNote - Core data structure for agentic memories
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class NoteType(str, Enum):
    INSIGHT = "insight"
    QUERY = "query"
    FEEDBACK = "feedback"
    DOCUMENT = "document"
    CONSOLIDATED = "consolidated"
    CODE = "code"
    IMAGE = "image"


class Modality(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    CODE = "code"
    AUDIO = "audio"


class SourceType(str, Enum):
    USER_INPUT = "user_input"
    LLM_INFERENCE = "llm_inference"
    DOCUMENT = "document"
    SYSTEM = "system"


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    CONTRADICTED = "contradicted"


@dataclass
class AgenticNote:
    content: str
    user_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    context: str = ""
    keywords: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    links: List[str] = field(default_factory=list)
    causal_links: List[str] = field(default_factory=list)
    importance: float = 0.5
    confidence: float = 0.8
    access_count: int = 0
    session_id: Optional[str] = None
    episode_id: Optional[str] = None
    note_type: NoteType = NoteType.INSIGHT
    modality: Modality = Modality.TEXT
    source_type: SourceType = SourceType.USER_INPUT
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    contradicts: List[str] = field(default_factory=list)
    version: int = 1
    embedding: Optional[List[float]] = None
    media_embedding: Optional[List[float]] = None
    thumbnail_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "context": self.context,
            "keywords": self.keywords,
            "tags": self.tags,
            "links": self.links,
            "causal_links": self.causal_links,
            "importance": self.importance,
            "confidence": self.confidence,
            "access_count": self.access_count,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "episode_id": self.episode_id,
            "note_type": self.note_type.value if isinstance(self.note_type, NoteType) else self.note_type,
            "modality": self.modality.value if isinstance(self.modality, Modality) else self.modality,
            "source_type": self.source_type.value if isinstance(self.source_type, SourceType) else self.source_type,
            "verification_status": self.verification_status.value if isinstance(self.verification_status, VerificationStatus) else self.verification_status,
            "contradicts": self.contradicts,
            "version": self.version,
            "embedding": self.embedding,
            "media_embedding": self.media_embedding,
            "thumbnail_path": self.thumbnail_path,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgenticNote":
        note_type = data.get("note_type", "insight")
        if isinstance(note_type, str):
            note_type = NoteType(note_type)
        
        modality = data.get("modality", "text")
        if isinstance(modality, str):
            modality = Modality(modality)
        
        source_type = data.get("source_type", "user_input")
        if isinstance(source_type, str):
            source_type = SourceType(source_type)
        
        verification = data.get("verification_status", "unverified")
        if isinstance(verification, str):
            verification = VerificationStatus(verification)
        
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            content=data["content"],
            context=data.get("context", ""),
            keywords=data.get("keywords", []),
            tags=data.get("tags", []),
            links=data.get("links", []),
            causal_links=data.get("causal_links", []),
            importance=data.get("importance", 0.5),
            confidence=data.get("confidence", 0.8),
            access_count=data.get("access_count", 0),
            user_id=data["user_id"],
            session_id=data.get("session_id"),
            episode_id=data.get("episode_id"),
            note_type=note_type,
            modality=modality,
            source_type=source_type,
            verification_status=verification,
            contradicts=data.get("contradicts", []),
            version=data.get("version", 1),
            embedding=data.get("embedding"),
            media_embedding=data.get("media_embedding"),
            thumbnail_path=data.get("thumbnail_path"),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat()),
        )

    def increment_access(self) -> None:
        self.access_count += 1
        self.updated_at = datetime.utcnow().isoformat()

    def add_link(self, note_id: str) -> None:
        if note_id not in self.links:
            self.links.append(note_id)
            self.updated_at = datetime.utcnow().isoformat()

    def add_causal_link(self, note_id: str) -> None:
        if note_id not in self.causal_links:
            self.causal_links.append(note_id)
            self.updated_at = datetime.utcnow().isoformat()

    def mark_contradicts(self, note_id: str) -> None:
        if note_id not in self.contradicts:
            self.contradicts.append(note_id)
            self.verification_status = VerificationStatus.CONTRADICTED
            self.updated_at = datetime.utcnow().isoformat()
