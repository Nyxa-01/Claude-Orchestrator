# Contributing to Claude Orchestrator

Thanks for your interest in contributing!

## Getting started

### Prerequisites

- Python 3.11+
- An Anthropic API key

### Local setup

```bash
git clone <repo-url>
cd Claude_Orchestrator

python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

pip install -r requirements.txt
cp .env.example .env
# add your ANTHROPIC_API_KEY to .env
```

## Project structure

- `src/config.py`: environment variables and `validate_config()` startup check.
- `src/models.py`: Claude client wrapper; call `get_main_client()` / `get_cheap_client()` for lazy singletons.
- `src/agents/`: planner, researcher, writer, evaluator agents.
- `src/orchestrator/core.py`: orchestrator, state, config.
- `src/orchestrator/factory.py`: `build_orchestrator()` — single wiring point used by CLI and API.
- `src/api/main.py`: FastAPI app exposing `/orchestrate`.
- `src/demo.py`: CLI demo script.
- `tests/`: orchestrator, API endpoint, and individual agent tests.

## Workflow

1. Open an issue or comment on an existing one before large changes.
2. Create a feature branch from `main`:
   ```bash
   git checkout -b feat/my-feature
   ```
3. Make changes with small, focused commits.
4. Run tests:
   ```bash
   pytest
   ```
5. Push your branch and open a Pull Request.

## Coding guidelines

- Use type hints on new public functions.
- Keep orchestrator logic declarative and easy to follow (planner → researcher → writer → evaluator).
- Keep configuration out of code where possible (use `config.py` and env vars).
- To add a new orchestration entry point, import `build_orchestrator()` from `src/orchestrator/factory.py` — do not duplicate client/agent construction.
- Avoid adding new direct Claude calls; go through the model client in `models.py` using `get_main_client()` or `get_cheap_client()`. Never instantiate `ClaudeClient` or `Anthropic` directly at module level.

## Testing

- All PRs should pass `pytest` locally.
- When adding new agents or steps, include at least one test that exercises them via `Orchestrator.handle_request`.

## Security and API keys

- Never commit `.env` or real API keys.
- `.env.example` is the only environment file that should be tracked.
- If you suspect a key was exposed, rotate it immediately and update `.env`.

## Contact

<!-- How people can reach you - GitHub issues, email, Discord, etc. -->
