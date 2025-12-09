"""
Document Processing Agents
===========================

Specialized agents for document understanding and chatting:
- Prometheus (The Illuminator): Extracts text from documents
- Hypatia (The Scholar): Semantic analysis and categorization
- Mnemosyne (The Keeper): Key insights extraction
- Daedalus (The Architect): Document processing orchestrator
"""

from .prometheus_reader import PrometheusReader
from .hypatia_analyzer import HypatiaAnalyzer
from .mnemosyne_extractor import MnemosyneExtractor
from .daedalus_orchestrator import DaedalusOrchestrator

__all__ = [
    "PrometheusReader",
    "HypatiaAnalyzer", 
    "MnemosyneExtractor",
    "DaedalusOrchestrator"
]
