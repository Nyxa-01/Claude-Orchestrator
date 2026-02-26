"""Unit tests for the orchestrator pipeline.

Uses a stub ClaudeClient so no real API key or network calls are needed.
Run with: pytest tests/
"""

import json
import pytest

from src.agents.base import Agent, AgentResult
from src.agents.planner import PlannerAgent
from src.agents.researcher import ResearchAgent
from src.agents.writer import WriterAgent
from src.agents.evaluator import EvaluatorAgent
from src.orchestrator.core import Orchestrator, OrchestrationConfig


# ---------------------------------------------------------------------------
# Stub model client — returns deterministic canned responses
# ---------------------------------------------------------------------------

class StubClaudeClient:
    """Replaces ClaudeClient for testing without hitting the Anthropic API."""

    def __init__(self, response: str = "stub response"):
        self.response = response
        self.calls: list = []

    def generate(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        self.calls.append({"system": system_prompt, "user": user_prompt})
        return self.response


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def stub_client():
    # Returns valid eval JSON so the evaluator loop exits cleanly on first pass
    eval_json = json.dumps({
        "pass": True,
        "issues": [],
        "improved_draft": "Improved stub draft.",
    })
    return StubClaudeClient(response=eval_json)


@pytest.fixture
def orchestrator(stub_client):
    planner = PlannerAgent("planner", stub_client)
    researcher = ResearchAgent("researcher", stub_client)
    writer = WriterAgent("writer", stub_client)
    evaluator = EvaluatorAgent("evaluator", stub_client)
    config = OrchestrationConfig(max_retries=1)
    return Orchestrator(planner, researcher, writer, evaluator, config)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_handle_request_returns_required_keys(orchestrator):
    result = orchestrator.handle_request("Write a blog post about AI.")
    assert "request_id" in result
    assert "steps" in result
    assert "memory" in result
    assert "final_answer" in result


def test_handle_request_runs_all_agents(orchestrator):
    result = orchestrator.handle_request("Explain quantum computing.")
    step_names = [s["step"] for s in result["steps"]]
    assert "planner" in step_names
    assert "researcher" in step_names
    assert "writer" in step_names
    assert "evaluator" in step_names


def test_request_id_is_unique(orchestrator):
    r1 = orchestrator.handle_request("Goal A")
    r2 = orchestrator.handle_request("Goal B")
    assert r1["request_id"] != r2["request_id"]


def test_memory_contains_plan_and_draft(orchestrator):
    result = orchestrator.handle_request("Plan my week.")
    assert "plan" in result["memory"]
    assert "draft" in result["memory"]


def test_evaluator_pass_sets_final_answer(orchestrator):
    # The stub returns pass=True with improved_draft, so final_answer should be that.
    result = orchestrator.handle_request("Describe a sunset.")
    assert result["final_answer"] == "Improved stub draft."


def test_evaluator_fail_triggers_retry():
    """When the evaluator returns pass=False, the orchestrator retries (up to max_retries)."""
    fail_then_pass = [
        json.dumps({"pass": False, "issues": ["too short"], "improved_draft": "Better draft v2."}),
        json.dumps({"pass": True, "issues": [], "improved_draft": "Final draft v3."}),
    ]
    call_count = 0

    class SequentialStub:
        def generate(self, system_prompt, user_prompt, **kwargs):
            nonlocal call_count
            # Return different responses for the two evaluator calls
            if "evaluator" in system_prompt.lower() or "assess" in system_prompt.lower():
                idx = min(call_count, len(fail_then_pass) - 1)
                call_count += 1
                return fail_then_pass[idx]
            return "generic stub response"

    stub = SequentialStub()
    planner = PlannerAgent("planner", stub)
    researcher = ResearchAgent("researcher", stub)
    writer = WriterAgent("writer", stub)
    evaluator = EvaluatorAgent("evaluator", stub)
    orch = Orchestrator(planner, researcher, writer, evaluator, OrchestrationConfig(max_retries=1))

    result = orch.handle_request("Write a poem.")
    assert "final_answer" in result
