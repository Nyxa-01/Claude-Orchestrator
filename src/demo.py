"""Quick CLI smoke test — runs the full orchestrator pipeline against the real API.

Usage:
    python -m src.demo
"""

from src.config import validate_config
from src.orchestrator.factory import build_orchestrator


if __name__ == "__main__":
    validate_config()

    orchestrator = build_orchestrator()

    goal = "Write a 3-section beginner's guide to multi-agent AI systems."
    print(f"\nRunning orchestrator for goal:\n  {goal}\n")
    print("=" * 60)

    result = orchestrator.handle_request(goal)

    print("\nSTEPS RUN:")
    for step in result["steps"]:
        print(f"  [{step['step']}] agent={step['agent']}  meta={step['metadata']}")

    print("\nFINAL ANSWER:")
    print("-" * 60)
    print(result["final_answer"])
    print("-" * 60)
    print(f"\nrequest_id: {result['request_id']}")
