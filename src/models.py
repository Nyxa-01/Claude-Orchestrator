from typing import Any, Optional
from anthropic import Anthropic
from src.config import ANTHROPIC_API_KEY, CLAUDE_MAIN_MODEL, CLAUDE_CHEAP_MODEL


class ClaudeClient:
    """Thin wrapper around the Anthropic messages API.

    Usage:
        client = ClaudeClient(model="claude-sonnet-4-6")
        response = client.generate(system_prompt="You are...", user_prompt="Do this...")
    """

    def __init__(self, model: str):
        self.model = model
        self._client = Anthropic(api_key=ANTHROPIC_API_KEY)

    def generate(self, system_prompt: str, user_prompt: str, **kwargs: Any) -> str:
        """Call Claude and return the full text response as a string."""
        response = self._client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 2000),
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return "".join(block.text for block in response.content if block.type == "text")


# ---------------------------------------------------------------------------
# Lazy-initialised singletons — constructed on first call, not at import time
# ---------------------------------------------------------------------------

_main_client: Optional[ClaudeClient] = None
_cheap_client: Optional[ClaudeClient] = None


def get_main_client() -> ClaudeClient:
    """Return the singleton main-model client, creating it on first call."""
    global _main_client
    if _main_client is None:
        _main_client = ClaudeClient(model=CLAUDE_MAIN_MODEL)
    return _main_client


def get_cheap_client() -> ClaudeClient:
    """Return the singleton cheap-model client, creating it on first call."""
    global _cheap_client
    if _cheap_client is None:
        _cheap_client = ClaudeClient(model=CLAUDE_CHEAP_MODEL)
    return _cheap_client
