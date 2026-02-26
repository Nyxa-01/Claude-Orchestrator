import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")

# Default to latest capable models; override via .env
CLAUDE_MAIN_MODEL: str = os.environ.get("CLAUDE_MAIN_MODEL", "claude-sonnet-4-6")
CLAUDE_CHEAP_MODEL: str = os.environ.get("CLAUDE_CHEAP_MODEL", "claude-haiku-4-5-20251001")


def validate_config() -> None:
    """Raise RuntimeError if required configuration values are missing.

    Call this at application startup (demo.py, api/main.py) before any
    Anthropic client is constructed.
    """
    if not ANTHROPIC_API_KEY:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. "
            "Add it to your .env file or export it as an environment variable."
        )
