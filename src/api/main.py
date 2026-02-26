"""FastAPI application exposing the orchestrator as an HTTP API.

Start with:
    uvicorn src.api.main:app --reload

Endpoints:
    POST /orchestrate   — run the full agent pipeline
    GET  /health        — liveness check
"""

from functools import lru_cache
from fastapi import FastAPI
from pydantic import BaseModel, Field

from src.config import validate_config
from src.orchestrator.factory import build_orchestrator
from src.orchestrator.core import Orchestrator


app = FastAPI(
    title="Claude Orchestrator",
    description="Multi-agent orchestration powered by Anthropic Claude.",
    version="1.0.0",
)


# --- Request / Response models ---

class OrchestrateRequest(BaseModel):
    user_goal: str = Field(..., min_length=1, max_length=2000)


class OrchestrateResponse(BaseModel):
    request_id: str
    final_answer: str
    steps: list


# --- Singleton orchestrator (built once on first request) ---

@lru_cache(maxsize=1)
def get_orchestrator() -> Orchestrator:
    validate_config()
    return build_orchestrator()


# --- Endpoints ---

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/orchestrate", response_model=OrchestrateResponse)
def orchestrate(request: OrchestrateRequest) -> OrchestrateResponse:
    """Run the full Planner → Researcher → Writer → Evaluator pipeline."""
    orchestrator = get_orchestrator()
    result = orchestrator.handle_request(request.user_goal)
    return OrchestrateResponse(
        request_id=result["request_id"],
        final_answer=result["final_answer"],
        steps=result["steps"],
    )
