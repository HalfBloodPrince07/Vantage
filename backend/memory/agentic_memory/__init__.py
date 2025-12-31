# backend/memory/agentic_memory/__init__.py
"""
Enhanced Agentic Memory (A-mem) System
Implements intelligent, self-evolving memory with consolidation, multi-modal support,
and proactive suggestions.
"""

from .note import AgenticNote, NoteType, Modality, SourceType, VerificationStatus
from .opensearch_memory import AgenticMemoryStore
from .note_generator import NoteGenerator
from .evolution import MemoryEvolution
from .system import AgenticMemorySystem

__all__ = [
    "AgenticNote",
    "NoteType",
    "Modality",
    "SourceType",
    "VerificationStatus",
    "AgenticMemoryStore",
    "NoteGenerator",
    "MemoryEvolution",
    "AgenticMemorySystem",
]

