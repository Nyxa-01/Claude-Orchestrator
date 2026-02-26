import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.agents.base import AgentResult
from src.agents.planner import PlannerAgent
from src.agents.researcher import ResearchAgent
from src.agents.writer import WriterAgent
from src.agents.evaluator import EvaluatorAgent

logger = logging.getLogger(__name__)


@dataclass
class OrchestrationConfig:
    """Tunable parameters for the orchestration run."""
    max_retries: int = 1  # how many times to re-run writer+evaluator if eval fails


@dataclass
class OrchestrationState:
    """Holds all state for a single orchestration request."""
    request_id: str
    user_goal: str
    memory: Dict[str, Any] = field(default_factory=dict)
    steps_run: List[Dict[str, Any]] = field(default_factory=list)


class Orchestrator:
    """Central coordinator that routes a user goal through a pipeline of agents.

    Pipeline:
        PlannerAgent → ResearchAgent → WriterAgent → EvaluatorAgent (with retries)

    Usage:
        orchestrator = Orchestrator(planner, researcher, writer, evaluator)
        result = orchestrator.handle_request("my goal")
        print(result["final_answer"])
    """

    def __init__(
        self,
        planner: PlannerAgent,
        researcher: ResearchAgent,
        writer: WriterAgent,
        evaluator: EvaluatorAgent,
        config: Optional[OrchestrationConfig] = None,
    ):
        self.planner = planner
        self.researcher = researcher
        self.writer = writer
        self.evaluator = evaluator
        self.config = config or OrchestrationConfig()

    def handle_request(self, user_goal: str) -> Dict[str, Any]:
        """Run the full agent pipeline for a given user goal.

        Returns a dict with:
            request_id   — unique ID for this run
            steps        — list of step metadata dicts
            memory       — the full shared memory after all agents have run
            final_answer — the finished, quality-controlled response
        """
        state = OrchestrationState(
            request_id=str(uuid.uuid4()),
            user_goal=user_goal,
            memory={"created_at": time.time()},
        )

        # Sequential pipeline
        self._run_step("planner", self.planner, state)
        self._run_step("researcher", self.researcher, state)
        self._run_step("writer", self.writer, state)

        final_result = self._evaluate_with_retries(state)

        return {
            "request_id": state.request_id,
            "steps": state.steps_run,
            "memory": state.memory,
            "final_answer": final_result.content,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_step(self, step_name: str, agent: Any, state: OrchestrationState) -> AgentResult:
        result = agent.run(state.user_goal, state.memory)
        state.steps_run.append(
            {
                "step": step_name,
                "agent": agent.name,
                "metadata": result.metadata,
            }
        )
        return result

    def _evaluate_with_retries(self, state: OrchestrationState) -> AgentResult:
        """Run EvaluatorAgent, parse its JSON, and loop if quality fails."""
        attempts = 0
        final_text = state.memory.get("draft", "")

        while attempts <= self.config.max_retries:
            attempts += 1
            self._run_step("evaluator", self.evaluator, state)

            raw_eval = state.memory.get("evaluation", "")
            try:
                # Strip markdown fences if the model wrapped the JSON anyway
                clean = raw_eval.strip()
                if clean.startswith("```"):
                    clean = clean.split("```")[1]
                    if clean.startswith("json"):
                        clean = clean[4:]
                data = json.loads(clean)
            except (json.JSONDecodeError, IndexError):
                # Evaluation wasn't valid JSON — accept current draft and stop
                snippet = raw_eval[:200].replace("\n", " ")
                logger.warning(
                    "request_id=%s evaluator returned non-JSON output (attempt %d); "
                    "falling back to current draft. Output snippet: %r",
                    state.request_id,
                    attempts,
                    snippet,
                )
                break

            improved = data.get("improved_draft", final_text)
            if data.get("pass"):
                final_text = improved
                break
            else:
                logger.info(
                    "request_id=%s evaluator pass=False on attempt %d (issues: %s); "
                    "retrying writer+evaluator.",
                    state.request_id,
                    attempts,
                    data.get("issues", []),
                )
                # Update draft in memory so writer/evaluator see the improved version
                state.memory["draft"] = improved
                final_text = improved
                if attempts > self.config.max_retries:
                    break
                # Re-run writer with the updated context before next eval
                self._run_step("writer", self.writer, state)

        state.memory["final"] = final_text
        return AgentResult(
            content=final_text,
            metadata={"type": "final", "attempts": attempts},
        )
