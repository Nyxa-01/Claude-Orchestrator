from typing import Any, Dict
from src.agents.base import Agent, AgentResult


class ResearchAgent(Agent):
    """Produces structured markdown bullet notes relevant to the user goal.

    Reads from memory["plan"] and memory["context"] (if present).
    Appends notes to memory["research_notes"] (list).

    Future extension: swap or augment `_fetch_context` with real tool calls
    (web search, vector DB, RAG pipeline). The agent interface stays unchanged.
    """

    def run(self, task: str, memory: Dict[str, Any]) -> AgentResult:
        context = self._fetch_context(task, memory)

        system = (
            "You are a research agent. Produce thorough, structured notes in markdown "
            "bullet format covering all relevant aspects of the user goal. "
            "Be specific and factual. Your notes will be used by a writer agent next."
        )
        user = (
            f"User goal: {task}\n\n"
            f"Plan to follow:\n{memory.get('plan', '(no plan provided)')}\n\n"
            f"Additional context:\n{context}"
        )

        notes = self.model.generate(system, user, max_tokens=1500)
        memory.setdefault("research_notes", []).append(notes)

        return AgentResult(content=notes, metadata={"type": "research"})

    def _fetch_context(self, task: str, memory: Dict[str, Any]) -> str:
        # TODO: plug in real tools here (web search, DB queries, RAG retrieval)
        return memory.get("context", "(no additional context)")
