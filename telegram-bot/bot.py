"""
HERMES MDM Steward Telegram Bot — main entry point.

Provides a Telegram interface to the HERMES MDM Steward skill library.
Each skill is exposed as a slash command; natural language is routed
automatically by the intent classifier.

Run with:
    python bot.py

Requirements: see requirements.txt
Secrets: see .env (never commit this file)
"""

import asyncio
import logging
import sys
from collections import defaultdict

import anthropic
from telegram import BotCommand, Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import config
from agents import (
    AGENT_REGISTRY,
    AgentID,
    ConversationState,
    HermesAgent,
)
from router import classify_intent

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# ── State store ────────────────────────────────────────────────────────────────
# user_id → ConversationState. Lives in memory; resets on restart.
_sessions: dict[int, ConversationState] = defaultdict(ConversationState)


def get_session(user_id: int) -> ConversationState:
    return _sessions[user_id]


# ── Access control ─────────────────────────────────────────────────────────────

def is_authorised(update: Update) -> bool:
    """Return True only if the sender is in the admin whitelist."""
    if not config.ADMIN_USER_IDS:
        logger.warning("ADMIN_USER_IDS is empty — all users are permitted.")
        return True
    user_id = update.effective_user.id if update.effective_user else None
    return user_id in config.ADMIN_USER_IDS


# ── Helpers ────────────────────────────────────────────────────────────────────

def _chunk_message(text: str, max_len: int = config.TELEGRAM_MAX_MESSAGE_LEN) -> list[str]:
    """Split a long message into chunks that respect Telegram's character limit."""
    if len(text) <= max_len:
        return [text]
    chunks: list[str] = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    return chunks


async def send_reply(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
) -> None:
    """Send a reply, splitting into multiple messages if needed."""
    chunks = _chunk_message(text)
    for i, chunk in enumerate(chunks):
        if i > 0:
            await asyncio.sleep(0.3)
        try:
            await update.message.reply_text(chunk, parse_mode=None)
        except Exception as exc:
            logger.error("Failed to send message chunk %d: %s", i, exc)


async def typing_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show a 'typing…' indicator while the agent is working."""
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING,
    )


# ── Shared agent invocation ────────────────────────────────────────────────────

async def invoke_active_agent(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_message: str,
) -> None:
    """Send user_message to the session's active agent and reply."""
    user_id = update.effective_user.id
    state = get_session(user_id)
    agent: HermesAgent = context.bot_data["agent"]

    await typing_action(update, context)
    reply = await agent.run(state, user_message)
    await send_reply(update, context, reply)


# ── Command handlers ───────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — introduce HERMES MDM and list available agents."""
    if not is_authorised(update):
        await update.message.reply_text("You are not authorised to use this bot.")
        return

    user = update.effective_user
    name = user.first_name if user else "there"

    lines = [
        f"Hello, {name}. I'm HERMES — your AI data steward for enterprise MDM.",
        "",
        "I give you access to these specialist skills:",
        "",
    ]
    for info in AGENT_REGISTRY.values():
        if info.id != AgentID.GENERAL:
            lines.append(f"{info.emoji} {info.command} — {info.description}")

    lines += [
        "",
        "You can also just type naturally — I'll figure out which skill you need.",
        "",
        "Type /help for guidance. Type /reset to start a fresh session.",
    ]
    await update.message.reply_text("\n".join(lines))


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help — activate the general HERMES MDM assistant."""
    if not is_authorised(update):
        await update.message.reply_text("You are not authorised to use this bot.")
        return

    user_id = update.effective_user.id
    state = get_session(user_id)
    state.switch_agent(AgentID.GENERAL)
    agent: HermesAgent = context.bot_data["agent"]

    await typing_action(update, context)
    reply = await agent.run(
        state,
        "Give me a brief overview of all available HERMES MDM skills and how to use this bot.",
    )
    await send_reply(update, context, reply)


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /reset — clear conversation state."""
    if not is_authorised(update):
        await update.message.reply_text("You are not authorised to use this bot.")
        return

    user_id = update.effective_user.id
    get_session(user_id).clear()
    await update.message.reply_text(
        "Session cleared. Back to neutral — all context wiped.\n"
        "Use a command or just type to get started again."
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status — show current session state."""
    if not is_authorised(update):
        await update.message.reply_text("You are not authorised to use this bot.")
        return

    user_id = update.effective_user.id
    state = get_session(user_id)
    info = AGENT_REGISTRY.get(state.active_agent)
    agent_label = f"{info.emoji} {info.display_name}" if info else state.active_agent
    msg_count = len(state.messages)
    await update.message.reply_text(
        f"Active agent: {agent_label}\n"
        f"Messages in context: {msg_count} / {config.MAX_CONTEXT_MESSAGES}\n"
        f"Use /reset to clear context."
    )


async def _activate_agent(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    agent_id: AgentID,
) -> None:
    """Switch to agent_id, send its welcome message, and wait for user input."""
    if not is_authorised(update):
        await update.message.reply_text("You are not authorised to use this bot.")
        return

    user_id = update.effective_user.id
    state = get_session(user_id)

    if state.active_agent != agent_id:
        state.switch_agent(agent_id)

    agent: HermesAgent = context.bot_data["agent"]
    welcome = agent.get_welcome_message(agent_id)
    await update.message.reply_text(welcome)


async def cmd_dqaudit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /dqaudit — activate the DQ Audit agent."""
    args_text = " ".join(context.args) if context.args else ""
    await _activate_agent(update, context, AgentID.DQAUDIT)
    if args_text:
        await invoke_active_agent(update, context, args_text)


async def cmd_dedup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /dedup — activate the Duplicate Resolver agent."""
    args_text = " ".join(context.args) if context.args else ""
    await _activate_agent(update, context, AgentID.DEDUP)
    if args_text:
        await invoke_active_agent(update, context, args_text)


async def cmd_golden(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /golden — activate the Golden Record Composer agent."""
    args_text = " ".join(context.args) if context.args else ""
    await _activate_agent(update, context, AgentID.GOLDEN)
    if args_text:
        await invoke_active_agent(update, context, args_text)


async def cmd_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /location — activate the Location Validator agent."""
    args_text = " ".join(context.args) if context.args else ""
    await _activate_agent(update, context, AgentID.LOCATION)
    if args_text:
        await invoke_active_agent(update, context, args_text)


async def cmd_briefing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /briefing — activate the Steward Briefing agent."""
    args_text = " ".join(context.args) if context.args else ""
    await _activate_agent(update, context, AgentID.BRIEFING)
    if args_text:
        await invoke_active_agent(update, context, args_text)


async def cmd_supplier(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /supplier — activate the Supplier Standardizer agent."""
    args_text = " ".join(context.args) if context.args else ""
    await _activate_agent(update, context, AgentID.SUPPLIER)
    if args_text:
        await invoke_active_agent(update, context, args_text)


# ── Natural language handler ───────────────────────────────────────────────────

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle all non-command text messages.

    If the user is already in an active agent session, route to that agent.
    If they're in GENERAL mode, classify intent first — if a specialist skill
    matches, switch to it automatically.
    """
    if not is_authorised(update):
        await update.message.reply_text("You are not authorised to use this bot.")
        return

    user_id = update.effective_user.id
    state = get_session(user_id)
    user_message = update.message.text or ""

    if not user_message.strip():
        return

    # If already in a specialist agent, continue the conversation.
    if state.active_agent != AgentID.GENERAL:
        await invoke_active_agent(update, context, user_message)
        return

    # In GENERAL mode: classify intent.
    anthropic_client: anthropic.AsyncAnthropic = context.bot_data["anthropic_client"]
    detected_agent = await classify_intent(anthropic_client, user_message)

    if detected_agent != AgentID.GENERAL:
        state.switch_agent(detected_agent)
        info = AGENT_REGISTRY[detected_agent]
        await update.message.reply_text(
            f"Routing you to the {info.emoji} {info.display_name} skill.\n"
            f"(Use /reset any time to go back to neutral.)"
        )
        await invoke_active_agent(update, context, user_message)
    else:
        await invoke_active_agent(update, context, user_message)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle file uploads — CSV / TSV / TXT files pasted as uploads.
    Downloads the file, reads its content, and passes it to the active agent.
    Most useful with the DQ Audit agent.
    """
    if not is_authorised(update):
        await update.message.reply_text("You are not authorised to use this bot.")
        return

    user_id = update.effective_user.id
    state = get_session(user_id)
    doc = update.message.document

    if doc is None:
        return

    filename = doc.file_name or "uploaded_file"
    file_size = doc.file_size or 0

    if file_size > 1_000_000:
        await update.message.reply_text(
            f"File '{filename}' is {file_size // 1000} KB — too large to process directly.\n"
            "Please paste the key data rows as plain text instead."
        )
        return

    allowed_suffixes = {".csv", ".tsv", ".txt"}
    suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if suffix not in allowed_suffixes:
        await update.message.reply_text(
            "I can read .csv, .tsv, and .txt files.\n"
            "For Excel (.xlsx) files, please export as CSV and re-upload, "
            "or paste the data as plain text."
        )
        return

    await typing_action(update, context)

    try:
        tg_file = await context.bot.get_file(doc.file_id)
        file_bytes: bytearray = await tg_file.download_as_bytearray()
        file_text = file_bytes.decode("utf-8", errors="replace")
    except Exception as exc:
        logger.error("File download error: %s", exc)
        await update.message.reply_text(
            "Could not download the file. Please try again or paste the data as text."
        )
        return

    # Auto-switch to DQ Audit agent if in general mode and a CSV is uploaded.
    if state.active_agent == AgentID.GENERAL:
        state.switch_agent(AgentID.DQAUDIT)
        await update.message.reply_text(
            "CSV detected — switching to the DQ Audit skill.\n"
            "I'll treat this file as your master data for auditing."
        )

    caption = update.message.caption or ""
    combined_message = (
        f"[File uploaded: {filename}]\n\n"
        f"{caption}\n\n"
        f"--- FILE CONTENTS ---\n{file_text}"
    ).strip()

    agent: HermesAgent = context.bot_data["agent"]
    reply = await agent.run(state, combined_message)
    await send_reply(update, context, reply)


# ── Bot setup ──────────────────────────────────────────────────────────────────

async def post_init(application: Application) -> None:
    """Register bot commands so Telegram shows the command menu."""
    commands = [
        BotCommand("start", "Introduce HERMES MDM and list skills"),
        BotCommand("help", "Get guidance on which skill to use"),
        BotCommand("dqaudit", "Run a data quality audit on master data"),
        BotCommand("dedup", "Resolve whether two records are the same entity"),
        BotCommand("golden", "Compose a golden record from confirmed duplicates"),
        BotCommand("location", "Validate and standardize a GCC address"),
        BotCommand("briefing", "Generate a steward morning briefing"),
        BotCommand("supplier", "Normalize supplier names and legal entity suffixes"),
        BotCommand("status", "Show current session and active skill"),
        BotCommand("reset", "Clear session context and start fresh"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Bot commands registered.")


def main() -> None:
    """Build the Application and start polling."""
    logger.info("Starting HERMES MDM Steward Telegram Bot...")
    logger.info("Model (agents): %s", config.CLAUDE_MODEL)
    logger.info("Model (router): %s", config.CLAUDE_ROUTER_MODEL)
    logger.info("Admin user IDs: %s", config.ADMIN_USER_IDS or "(unrestricted)")

    anthropic_client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
    agent = HermesAgent(anthropic_client)

    application = (
        Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    application.bot_data["anthropic_client"] = anthropic_client
    application.bot_data["agent"] = agent

    # ── Command handlers ───────────────────────────────────────────────────────
    application.add_handler(CommandHandler("start",    cmd_start))
    application.add_handler(CommandHandler("help",     cmd_help))
    application.add_handler(CommandHandler("reset",    cmd_reset))
    application.add_handler(CommandHandler("status",   cmd_status))
    application.add_handler(CommandHandler("dqaudit",  cmd_dqaudit))
    application.add_handler(CommandHandler("dedup",    cmd_dedup))
    application.add_handler(CommandHandler("golden",   cmd_golden))
    application.add_handler(CommandHandler("location", cmd_location))
    application.add_handler(CommandHandler("briefing", cmd_briefing))
    application.add_handler(CommandHandler("supplier", cmd_supplier))

    # ── Message handlers ───────────────────────────────────────────────────────
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Bot is running. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
