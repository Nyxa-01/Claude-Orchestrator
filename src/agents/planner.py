from typing import Any, Dict
from src.agents.base import Agent, AgentResult


class PlannerAgent(Agent):
    """Decomposes a user goal into 3-8 executable steps (JSON list of strings).

    Writes to memory["plan"].
    """

    def run(self, task: str, memory: Dict[str, Any]) -> AgentResult:
        system = (
            "You are a planning agent. Your job is to decompose a user goal into "
            "3 to 8 clear, ordered, executable steps. "
            "Return ONLY a JSON array of strings, no explanation or markdown wrapper. "
            'Example: ["Step 1: ...", "Step 2: ...", "Step 3: ..."]'
        )
        user = f"User goal: {task}"

        plan_json = self.model.generate(system, user, max_tokens=800)
        memory["plan"] = plan_json

        return AgentResult(content=plan_json, metadata={"type": "plan"})
