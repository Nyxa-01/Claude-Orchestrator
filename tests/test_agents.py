"""Unit tests for individual agents.

Uses a stub ClaudeClient so no real API key or network calls are needed.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.agents.planner import PlannerAgent
from src.agents.researcher import ResearchAgent
from src.agents.writer import WriterAgent
from src.agents.evaluator import EvaluatorAgent
from src.models import ClaudeClient


# ---------------------------------------------------------------------------
# Stub client helpers
# ---------------------------------------------------------------------------

class StubClient:
    """Minimal stub that records calls and returns a fixed response."""

    def __init__(self, response: str = "stub"):
        self.response = response
        self.calls: list = []

    def generate(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        self.calls.append({"system": system_prompt, "user": user_prompt})
        return self.response


# ---------------------------------------------------------------------------
# PlannerAgent tests
# ---------------------------------------------------------------------------

def test_planner_writes_to_memory_plan():
    stub = StubClient(response='["step 1", "step 2", "step 3"]')
    agent = PlannerAgent("planner", stub)
    memory: dict = {}
    agent.run("Write a blog post.", memory)
    assert "plan" in memory


def test_planner_result_has_content():
    stub = StubClient(response='["step 1"]')
    agent = PlannerAgent("planner", stub)
    result = agent.run("Goal", {})
    assert result.content != ""


# ---------------------------------------------------------------------------
# WriterAgent tests
# ---------------------------------------------------------------------------

def test_writer_writes_to_memory_draft():
    stub = StubClient(response="Here is the full draft content.")
    agent = WriterAgent("writer", stub)
    memory = {"plan": ["step 1", "step 2"], "research_notes": ["note A"]}
    agent.run("Write something.", memory)
    assert "draft" in memory


def test_writer_draft_contains_stub_response():
    stub = StubClient(response="Draft content here.")
    agent = WriterAgent("writer", stub)
    memory = {"plan": ["plan step"], "research_notes": []}
    result = agent.run("Write something.", memory)
    assert result.content == "Draft content here."


# ---------------------------------------------------------------------------
# ResearchAgent tests
# ---------------------------------------------------------------------------

def test_researcher_appends_to_research_notes():
    stub = StubClient(response="- bullet note one\n- bullet note two")
    agent = ResearchAgent("researcher", stub)
    memory: dict = {}
    agent.run("Research AI.", memory)
    assert "research_notes" in memory
    assert len(memory["research_notes"]) > 0


# ---------------------------------------------------------------------------
# EvaluatorAgent tests
# ---------------------------------------------------------------------------

def test_evaluator_writes_to_memory_evaluation():
    eval_json = json.dumps({"pass": True, "issues": [], "improved_draft": "Better draft."})
    stub = StubClient(response=eval_json)
    agent = EvaluatorAgent("evaluator", stub)
    memory = {"draft": "Some draft text."}
    agent.run("Evaluate.", memory)
    assert "evaluation" in memory


# ---------------------------------------------------------------------------
# ClaudeClient.generate unit test (mocked Anthropic SDK)
# ---------------------------------------------------------------------------

def test_claude_client_generate_joins_text_blocks():
    """Verify ClaudeClient.generate correctly joins multiple text content blocks."""
    import os
    os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

    block1 = MagicMock()
    block1.type = "text"
    block1.text = "Hello, "

    block2 = MagicMock()
    block2.type = "text"
    block2.text = "world."

    mock_response = MagicMock()
    mock_response.content = [block1, block2]

    with patch("src.models.Anthropic") as MockAnthropic:
        mock_sdk = MockAnthropic.return_value
        mock_sdk.messages.create.return_value = mock_response

        client = ClaudeClient(model="claude-test")
        result = client.generate(system_prompt="You are a test.", user_prompt="Say hi.")

    assert result == "Hello, world."


def test_claude_client_generate_skips_non_text_blocks():
    """Non-text blocks (e.g. tool_use) are ignored."""
    import os
    os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "Only text."

    tool_block = MagicMock()
    tool_block.type = "tool_use"

    mock_response = MagicMock()
    mock_response.content = [text_block, tool_block]

    with patch("src.models.Anthropic") as MockAnthropic:
        mock_sdk = MockAnthropic.return_value
        mock_sdk.messages.create.return_value = mock_response

        client = ClaudeClient(model="claude-test")
        result = client.generate(system_prompt="Sys.", user_prompt="User.")

    assert result == "Only text."
