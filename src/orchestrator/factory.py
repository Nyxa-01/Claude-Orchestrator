"""Factory function for building a fully-wired Orchestrator.

Both demo.py and api/main.py import this so orchestrator construction logic
lives in exactly one place.
"""

from src.models import get_main_client, get_cheap_client
from src.agents import PlannerAgent, ResearchAgent, WriterAgent, EvaluatorAgent
from src.orchestrator.core import Orchestrator, OrchestrationConfig


def build_orchestrator(max_retries: int = 1) -> Orchestrator:
    """Create and return a fully-configured Orchestrator instance.

    Uses cheap/fast model for planner and researcher (cost efficiency) and
    the main model for writer and evaluator (output quality).
    """
    cheap = get_cheap_client()
    main = get_main_client()

    planner = PlannerAgent("planner", cheap)
    researcher = ResearchAgent("researcher", cheap)
    writer = WriterAgent("writer", main)
    evaluator = EvaluatorAgent("evaluator", main)

    config = OrchestrationConfig(max_retries=max_retries)
    return Orchestrator(planner, researcher, writer, evaluator, config)
