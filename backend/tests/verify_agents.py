import sys
import os
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from backend.agents.query_classifier import QueryClassifier
from backend.agents.analysis_agent import AnalysisAgent
from backend.agents.clarification_agent import ClarificationAgent
from backend.agents.critic_agent import CriticAgent
from backend.agents.explanation_agent import ExplanationAgent
from backend.agents.summarization_agent import SummarizationAgent
from backend.orchestration.orchestrator import EnhancedOrchestrator

def verify_agents():
    config = {
        "ollama": {
            "base_url": "http://localhost:11434",
            "text_model": {"name": "qwen2.5-coder:7b"},
            "timeout": 120.0
        }
    }

    agents = [
        (QueryClassifier, "Athena"),
        (AnalysisAgent, "Aristotle"),
        (ClarificationAgent, "Socrates"),
        (CriticAgent, "Diogenes"),
        (ExplanationAgent, "Hermes"),
        (SummarizationAgent, "Thoth")
    ]

    print("Verifying Agent Initialization...")
    for agent_cls, expected_name in agents:
        try:
            agent = agent_cls(config)
            print(f"✅ {agent_cls.__name__} initialized. Name: {agent.name}")
            if expected_name not in agent.name:
                print(f"❌ Name mismatch! Expected {expected_name} in {agent.name}")
        except Exception as e:
            print(f"❌ Failed to initialize {agent_cls.__name__}: {e}")

    print("\nVerifying Orchestrator...")
    try:
        # Mock dependencies
        memory = {}
        search = lambda x: []
        orch = EnhancedOrchestrator(config, memory, search)
        print(f"✅ Orchestrator initialized. Name: {orch.name}")
        if "Zeus" not in orch.name:
            print(f"❌ Name mismatch! Expected Zeus in {orch.name}")
    except Exception as e:
        print(f"❌ Failed to initialize Orchestrator: {e}")

if __name__ == "__main__":
    verify_agents()
