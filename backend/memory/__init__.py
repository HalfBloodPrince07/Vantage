# backend/memory/__init__.py
"""
Agentic Memory System for LocalLens

This module implements a tiered memory architecture:
- Short-term: Session context (sliding window buffer)
- Long-term: User profiles and patterns
- Procedural: Tool usage learning and optimization
- Agentic: Agent-callable memory tools (MemGPT-style)
- Episodic: Complete interaction episode storage
"""

from .session_memory import SessionMemory
from .user_profile import UserProfileManager
from .procedural_memory import ProceduralMemory
from .memory_manager import MemoryManager
from .memory_tool import MemoryTool, Memory, UserContext
from .memory_reflector import MemoryReflector, SessionSummary, UserPreferences as ReflectedPreferences
from .episodic_memory import EpisodicMemory, Episode, EpisodeSummary

__all__ = [
    # Core memory components
    "SessionMemory",
    "UserProfileManager",
    "ProceduralMemory",
    "MemoryManager",
    # Agentic memory (MemGPT-style)
    "MemoryTool",
    "Memory",
    "UserContext",
    "MemoryReflector",
    "SessionSummary",
    "ReflectedPreferences",
    # Episodic memory
    "EpisodicMemory",
    "Episode",
    "EpisodeSummary"
]

