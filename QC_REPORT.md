# QC Report for Claude Orchestrator v0.1.0

## 1. Summary

Claude Orchestrator is a Python backend that coordinates four Claude-backed agents
(Planner, Researcher, Writer, Evaluator) through a sequential pipeline to produce
quality-controlled answers to complex user goals. The codebase is clean and well
structured with clear separation of concerns, good test coverage using stub clients,
and both CLI and HTTP API interfaces. Several repo-level hygiene items (`.gitignore`,
`LICENSE`) are still missing, and the API layer could benefit from additional tests
and input validation.

## 2. Architecture review

- **Orchestrator and state:**
  - `Orchestrator.handle_request` implements a clear sequential pipeline
    (planner → researcher → writer → evaluator) with a retry loop for evaluation
    failures. State is encapsulated in `OrchestrationState` using dataclasses.
    The flow is easy to follow and extend. (`src/orchestrator/core.py`)

- **Agents:**
  - Each agent has a single responsibility, reads/writes well-defined memory keys,
    and delegates model calls to an injected `ClaudeClient`. Prompts are concise
    and role-appropriate. The base class enforces the `run()` contract.
    (`src/agents/base.py`, `src/agents/planner.py`, etc.)

- **API:**
  - FastAPI app exposes `POST /orchestrate` and `GET /health`. The orchestrator is
    instantiated once via `@lru_cache(maxsize=1)`, avoiding per-request construction.
    `OrchestrateResponse` returns `request_id`, `final_answer`, `steps` but omits
    `memory`, keeping the public contract lean. (`src/api/main.py`)

- **Config:**
  - `config.py` loads `.env` via `python-dotenv` and exposes three settings:
    `ANTHROPIC_API_KEY`, `CLAUDE_MAIN_MODEL`, `CLAUDE_CHEAP_MODEL`. Defaults
    are sensible. `.env.example` matches `config.py` expectations. (`src/config.py`)

## 3. Code quality

### 3.1 Strengths

- Clean pipeline architecture with dependency injection (agents receive model clients).
- Good use of dataclasses for `OrchestrationState`, `OrchestrationConfig`, and `AgentResult`.
- Singleton orchestrator pattern in the API avoids re-initialization overhead.
- Tests use a stub client, so the full pipeline can run without API keys or network access.
- Consistent memory key conventions across agents (`plan`, `research_notes`, `draft`, `evaluation`).

### 3.2 Issues / risks

- **ID**: Q-1
- **Severity**: medium
- **Location**: repo root
- **Description**: `.gitignore` is missing. `.venv/`, `.env`, `__pycache__/`, `.pytest_cache/` could be committed by accident.
- **Suggested fix**: Add a standard Python `.gitignore` before the first commit.

---

- **ID**: Q-2
- **Severity**: medium
- **Location**: repo root
- **Description**: `LICENSE` file is missing. README references `[MIT](LICENSE)` but the file does not exist.
- **Suggested fix**: Add an MIT `LICENSE` file.

---

- **ID**: Q-3
- **Severity**: low
- **Location**: `src/config.py:6`
- **Description**: `ANTHROPIC_API_KEY` defaults to an empty string when unset. The client will create an `Anthropic` instance with an empty key and only fail at request time with an opaque API error.
- **Suggested fix**: Raise a clear error at startup if `ANTHROPIC_API_KEY` is empty or unset.

---

- **ID**: Q-4
- **Severity**: low
- **Location**: `src/models.py:30-31`
- **Description**: `main_client` and `cheap_client` are instantiated at module import time. This means importing `src.models` in any context (tests, CLI tools) immediately creates Anthropic SDK instances with the configured API key, even if they won't be used.
- **Suggested fix**: Consider lazy initialization or a factory function. Tests already work around this by injecting stubs, so this is low priority.

---

- **ID**: Q-5
- **Severity**: low
- **Location**: `src/api/main.py:58-67`
- **Description**: No input validation on `user_goal` (empty string, excessively long input). The orchestrator will pass an empty goal through all four agents.
- **Suggested fix**: Add a `min_length=1` and reasonable `max_length` constraint to the Pydantic model.

---

- **ID**: Q-6
- **Severity**: low
- **Location**: `src/orchestrator/core.py:110-118`
- **Description**: JSON parsing of evaluator output silently falls back to the current draft on any parse error. If the model consistently returns malformed JSON, the user gets no signal that evaluation was skipped.
- **Suggested fix**: Log a warning when evaluation JSON fails to parse so operators can detect prompt regression.

---

- **ID**: Q-7
- **Severity**: low
- **Location**: `src/demo.py` and `src/api/main.py`
- **Description**: Both files independently build the same orchestrator with identical wiring (same agents, same config). Minor duplication.
- **Suggested fix**: Extract a shared `build_orchestrator()` factory (e.g., in `src/orchestrator/__init__.py`). Low priority since there are only two call sites.

## 4. Tests and reliability

- **Test coverage summary:**
  - `tests/test_orchestrator.py` covers the core pipeline: return-key validation,
    all-agents-run check, unique request IDs, memory population, evaluator-pass
    flow, and evaluator-fail retry logic. All tests use `StubClaudeClient` with
    no network calls.

- **Gaps:**
  - No tests for the FastAPI endpoints (`/orchestrate`, `/health`). A `TestClient`-based
    test would catch wiring issues.
  - No tests for individual agents in isolation (e.g., verifying `PlannerAgent`
    writes to `memory["plan"]`).
  - No negative-path tests: what happens when the model returns invalid JSON for
    the planner or evaluator, or when `ANTHROPIC_API_KEY` is missing.
  - No tests for `ClaudeClient.generate` (mocking the Anthropic SDK response object).

## 5. DX and documentation

- **README:**
  - Setup instructions are accurate and include venv, install, `.env` configuration,
    CLI demo, and API startup commands. API request/response schema is documented
    with a curl example and sample JSON.

- **CONTRIBUTING:**
  - Contribution workflow, coding guidelines, and security notes are present and clear.

- **Comments & docstrings:**
  - Public classes and methods have docstrings (`Orchestrator`, `Agent`, `ClaudeClient`,
    all agent classes). Internal helpers use inline comments where logic is non-obvious
    (e.g., markdown-fence stripping in the evaluator retry loop).

## 6. Recommended next steps

1. Add `.gitignore` and `LICENSE` (MIT) to the repo root (Q-1, Q-2).
2. Add FastAPI `TestClient` tests for `/orchestrate` and `/health` endpoints.
3. Add startup validation for `ANTHROPIC_API_KEY` in `config.py` (Q-3).
4. Add basic input validation (`min_length`, `max_length`) to `OrchestrateRequest.user_goal` (Q-5).
5. Add logging to the orchestrator and evaluator retry loop so failures are observable (Q-6).

## 7. Sign-off

- QC performed by: Claude (automated QC agent)
- Date: 2026-02-26
- Release candidate: **no** — missing `.gitignore` and `LICENSE` (Q-1, Q-2) must be resolved before public release.
