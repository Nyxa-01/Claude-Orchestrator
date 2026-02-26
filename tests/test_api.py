"""API endpoint tests using FastAPI TestClient.

No real Anthropic API calls are made — the orchestrator singleton is
replaced with a stub by patching src.api.main.get_orchestrator.
"""

import json
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from src.api.main import app
from src.orchestrator.core import Orchestrator, OrchestrationConfig
from src.agents.planner import PlannerAgent
from src.agents.researcher import ResearchAgent
from src.agents.writer import WriterAgent
from src.agents.evaluator import EvaluatorAgent


# ---------------------------------------------------------------------------
# Stub client that simulates a passing evaluator
# ---------------------------------------------------------------------------

class _StubClient:
    def generate(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        return json.dumps({"pass": True, "issues": [], "improved_draft": "API stub answer."})


def _make_stub_orchestrator() -> Orchestrator:
    stub = _StubClient()
    planner = PlannerAgent("planner", stub)
    researcher = ResearchAgent("researcher", stub)
    writer = WriterAgent("writer", stub)
    evaluator = EvaluatorAgent("evaluator", stub)
    return Orchestrator(planner, researcher, writer, evaluator, OrchestrationConfig(max_retries=0))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def patch_orchestrator():
    """Patch get_orchestrator so no real API calls happen in any test."""
    stub = _make_stub_orchestrator()
    with patch("src.api.main.get_orchestrator", return_value=stub):
        yield


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_orchestrate_valid_goal_returns_expected_keys(client):
    response = client.post("/orchestrate", json={"user_goal": "Explain neural networks."})
    assert response.status_code == 200
    body = response.json()
    assert "request_id" in body
    assert "final_answer" in body
    assert "steps" in body


def test_orchestrate_empty_goal_returns_422(client):
    response = client.post("/orchestrate", json={"user_goal": ""})
    assert response.status_code == 422


def test_orchestrate_missing_goal_field_returns_422(client):
    response = client.post("/orchestrate", json={})
    assert response.status_code == 422


def test_orchestrate_goal_too_long_returns_422(client):
    response = client.post("/orchestrate", json={"user_goal": "x" * 2001})
    assert response.status_code == 422


def test_orchestrate_steps_is_list(client):
    response = client.post("/orchestrate", json={"user_goal": "Summarise Python."})
    assert response.status_code == 200
    assert isinstance(response.json()["steps"], list)
