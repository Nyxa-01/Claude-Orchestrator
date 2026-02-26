from dataclasses import dataclass, field
from typing import Any, Dict
from src.models import ClaudeClient


@dataclass
class AgentResult:
    """The output of a single agent run."""
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class Agent:
    """Base class for all specialist agents.

    Each concrete agent receives:
    - task: the original user goal string
    - memory: shared dict that persists across all agents in one orchestration run

    Each agent may read from and write to memory, then return an AgentResult.
    """

    def __init__(self, name: str, model: ClaudeClient):
        self.name = name
        self.model = model

    def run(self, task: str, memory: Dict[str, Any]) -> AgentResult:
        raise NotImplementedError(f"{self.__class__.__name__} must implement run()")
