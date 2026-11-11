# src/agents/__init__.py
from src.agents.fitness_agent import FitnessAgent
from src.agents.orchestrator import FitnessOrchestrator
from src.agents.watsonx_client import WatsonxClient

__all__ = ["FitnessAgent", "FitnessOrchestrator", "WatsonxClient"]
