# Claude Orchestrator: Claude-Orchestrated Multi-Agent Backend

## Overview

A multi-agent orchestration system powered by Anthropic's Claude. A central
Orchestrator coordinates specialized agents (Planner, Researcher, Writer,
Evaluator) to handle complex user goals. A single endpoint (`/orchestrate`)
coordinates planning, research, drafting, and evaluation to return a
high-quality final answer plus metadata.

## Architecture

- **Core orchestrator** (`src/orchestrator/core.py`): coordinates planner → researcher → writer → evaluator.
- **Orchestrator factory** (`src/orchestrator/factory.py`): `build_orchestrator()` — single place to wire up agents and clients; used by both the CLI and the API.
- **Agents** (`src/agents/...`): specialized Claude personas for each stage.
- **Model client** (`src/models.py`): wraps the Anthropic Python SDK; use `get_main_client()` / `get_cheap_client()` for lazy-initialized singletons.
- **API** (`src/api/main.py`): FastAPI app exposing the orchestration endpoint.
- **Config** (`src/config.py`): environment variables, defaults, and `validate_config()` startup check.
- **Tests** (`tests/`): orchestrator pipeline, API endpoint, individual agent, and config validation tests (22 tests, no real API calls needed).

### High-level flow

1. Client sends a `user_goal` to the API.
2. Orchestrator creates a request state and calls:
   - PlannerAgent → plan
   - ResearchAgent → notes
   - WriterAgent → draft
   - EvaluatorAgent → evaluation & optional repair loop
3. Orchestrator returns `final_answer` and a trace of steps.

## Quickstart

### Requirements

- Python 3.11+
- An Anthropic API key

### Setup

```bash
git clone <repo-url>
cd Claude_Orchestrator

python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

pip install -r requirements.txt
```

Create `.env` from the example:

```bash
cp .env.example .env
```

Edit `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MAIN_MODEL=claude-sonnet-4-6
CLAUDE_CHEAP_MODEL=claude-haiku-4-5-20251001
```

### Run demo (CLI)

```bash
python -m src.demo
```

This runs a sample `user_goal` through the orchestrator and prints the final answer.

### Run API

```bash
uvicorn src.api.main:app --reload
```

Now you can call the endpoint:

```bash
curl -X POST http://localhost:8000/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"user_goal": "Design a weekly creative workflow for my studio"}'
```

Expected JSON response (simplified):

```json
{
  "request_id": "uuid-...",
  "final_answer": "...",
  "steps": [...]
}
```

Interactive API docs available at: `http://localhost:8000/docs`

## Development

### Running tests

```bash
pytest
```

Tests include:

- `test_orchestrator.py` — end-to-end pipeline tests with a stub client.
- `test_api.py` — FastAPI endpoint tests with TestClient (requires `httpx`).
- `test_agents.py` — individual agent and `ClaudeClient.generate` unit tests.
- `test_config.py` — startup validation tests for `validate_config()`.

### Code style

- Type hints on public functions.
- Keep orchestration logic in `src/orchestrator/core.py`.
- Keep Claude-specific logic inside `src/models.py`.

## Project Structure

```
src/
├── config.py           # Environment config + validate_config()
├── models.py           # ClaudeClient wrapper + get_main_client()/get_cheap_client()
├── agents/
│   ├── base.py         # Base Agent class + AgentResult
│   ├── planner.py      # Decomposes goal into steps
│   ├── researcher.py   # Produces structured notes
│   ├── writer.py       # Writes the final draft
│   └── evaluator.py    # Quality checks and improvement
├── orchestrator/
│   ├── core.py         # Orchestrator class
│   └── factory.py      # build_orchestrator() — shared wiring
├── api/
│   └── main.py         # FastAPI endpoints
└── demo.py             # CLI smoke test
tests/
├── test_orchestrator.py  # End-to-end orchestrator pipeline tests
├── test_api.py           # FastAPI endpoint tests (TestClient)
├── test_agents.py        # Individual agent + ClaudeClient unit tests
└── test_config.py        # Config startup validation tests
notes/
└── QC_REPORT.md          # Internal quality-control report
```

## Roadmap

- Add RAG/web-search tooling to `ResearchAgent`.
- Add structured logging/metrics for every pipeline step (evaluator loop now logs warnings and retries; full step telemetry is TODO).
- Add a small web frontend / playground.
- Support multiple providers or model variants (e.g., OpenAI, Gemini).
- Add streaming responses to the `/orchestrate` endpoint.

## License

[MIT](LICENSE)
