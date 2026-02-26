from typing import Any, Dict
from src.agents.base import Agent, AgentResult


class WriterAgent(Agent):
    """Synthesizes the plan and research notes into a coherent final draft.

    Reads from memory["plan"] and memory["research_notes"].
    Writes result to memory["draft"].
    """

    def run(self, task: str, memory: Dict[str, Any]) -> AgentResult:
        research_notes = memory.get("research_notes", [])
        combined_notes = "\n\n---\n\n".join(research_notes) if research_notes else "(none)"

        system = (
            "You are a writer agent. Synthesize the provided plan and research notes "
            "into a clear, well-structured, and complete response to the user goal. "
            "Write for the end user — polished prose, not bullet dumps."
        )
        user = (
            f"User goal: {task}\n\n"
            f"Plan:\n{memory.get('plan', '(no plan)')}\n\n"
            f"Research notes:\n{combined_notes}"
        )

        draft = self.model.generate(system, user, max_tokens=2000)
        memory["draft"] = draft

        return AgentResult(content=draft, metadata={"type": "draft"})
