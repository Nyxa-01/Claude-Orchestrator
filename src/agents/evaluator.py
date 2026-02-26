from typing import Any, Dict
from src.agents.base import Agent, AgentResult


class EvaluatorAgent(Agent):
    """Evaluates the draft for correctness, safety, and completeness.

    Reads memory["draft"].
    Writes raw JSON string to memory["evaluation"].

    Returns STRICT JSON with keys:
        pass (bool)         — whether the draft is acceptable as-is
        issues (list[str])  — problems found; empty list if pass is true
        improved_draft (str) — a corrected/improved version of the draft
    """

    def run(self, task: str, memory: Dict[str, Any]) -> AgentResult:
        system = (
            "You are a strict quality-control evaluator agent. "
            "Assess the provided draft against the original user goal for: "
            "accuracy, completeness, clarity, and safety. "
            "Return ONLY valid JSON with exactly these keys: "
            '"pass" (boolean), "issues" (array of strings), '
            '"improved_draft" (string with a corrected/improved version). '
            "No markdown fences, no extra keys, no explanation outside the JSON object."
        )
        user = (
            f"User goal: {task}\n\n"
            f"Draft to evaluate:\n{memory.get('draft', '(no draft)')}"
        )

        review_json = self.model.generate(system, user, max_tokens=2000)
        memory["evaluation"] = review_json

        return AgentResult(content=review_json, metadata={"type": "evaluation"})
