"""
Configuration for the HERMES MDM Steward Telegram bot.
Loads all settings from environment variables via .env.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Resolve .env relative to this file so it loads correctly regardless of cwd.
_here = Path(__file__).parent
load_dotenv(_here / ".env", override=True)


def _require(key: str) -> str:
    """Return an env var or raise a clear error at startup."""
    value = os.getenv(key)
    if not value:
        raise RuntimeError(
            f"Required environment variable '{key}' is not set. "
            f"Check your telegram-bot/.env file."
        )
    return value


# ── Core secrets ──────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN: str = _require("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY: str = _require("ANTHROPIC_API_KEY")

# ── Access control ─────────────────────────────────────────────────────────────
# Comma-separated list of Telegram user IDs allowed to interact with the bot.
ADMIN_USER_IDS: set[int] = {
    int(uid.strip())
    for uid in os.getenv("ADMIN_USER_IDS", "").split(",")
    if uid.strip()
}

# ── Model settings ─────────────────────────────────────────────────────────────
# Agent model — used for all skill invocations.
CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

# Router model — faster/cheaper, only classifies intent.
CLAUDE_ROUTER_MODEL: str = os.getenv("CLAUDE_ROUTER_MODEL", "claude-haiku-4-5-20251001")

# ── Conversation settings ──────────────────────────────────────────────────────
# Max messages kept per user session before oldest are trimmed.
MAX_CONTEXT_MESSAGES: int = int(os.getenv("MAX_CONTEXT_MESSAGES", "20"))

# Max characters in a single Telegram message (API hard limit: 4096).
TELEGRAM_MAX_MESSAGE_LEN: int = 4000

# ── HERMES repo path ───────────────────────────────────────────────────────────
HERMES_REPO_PATH: Path = Path(
    os.getenv(
        "HERMES_REPO_PATH",
        str(Path.home() / "Documents" / "hermes-mdm-steward-skills"),
    )
).expanduser()
