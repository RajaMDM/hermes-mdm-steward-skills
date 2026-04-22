# HERMES MDM Steward — Telegram Bot

A Telegram interface to the HERMES MDM Steward skill pack. Six specialist skills
exposed as slash commands; natural language is routed automatically by an intent
classifier (Claude Haiku). Each skill runs as a conversational Claude agent (Sonnet)
derived directly from the skill's `SKILL.md` procedure.

Built by Raja Shahnawaz Soni. Runs locally on macOS Apple Silicon.

---

## Skills

| Command | Skill | What it does |
|---|---|---|
| `/dqaudit` | DQ Audit | Completeness, duplicates, format violations across pasted master data |
| `/dedup` | Duplicate Resolver | Four-gate match/merge decision for supplier and business-partner records |
| `/golden` | Golden Record Composer | Field-level survivorship with full provenance map |
| `/location` | Location Validator | GCC-wide address standardization (UAE, KSA, Kuwait, Qatar, Bahrain, Oman) |
| `/briefing` | Steward Briefing | Concise morning briefing — what needs a decision today |
| `/supplier` | Supplier Standardizer | Legal entity suffix cleanup, case normalization, DBA extraction |

Utility commands: `/start`, `/help`, `/status`, `/reset`

---

## Install

```bash
# 1. Navigate into the repo
cd ~/path/to/hermes-mdm-steward-skills

# 2. Create a virtual environment
python3 -m venv telegram-bot/venv

# 3. Activate it
source telegram-bot/venv/bin/activate

# 4. Install dependencies
pip install -r telegram-bot/requirements.txt

# 5. Verify the .env file has real tokens (never commit it)
cat telegram-bot/.env

# 6. Run the bot
python telegram-bot/bot.py
```

---

## Configuration

All settings live in `telegram-bot/.env` (gitignored). Copy `.env.example` as a template:

```
TELEGRAM_BOT_TOKEN=   — from @BotFather
ANTHROPIC_API_KEY=    — from console.anthropic.com
ADMIN_USER_IDS=       — comma-separated Telegram user IDs (get yours from @userinfobot)
CLAUDE_MODEL=         — default: claude-sonnet-4-6
CLAUDE_ROUTER_MODEL=  — default: claude-haiku-4-5-20251001
MAX_CONTEXT_MESSAGES= — default: 20
```

---

## Architecture

```
bot.py          Main entry point. Telegram handlers, command registration, polling loop.
agents.py       Six AgentID enums + GENERAL. System prompts derived from SKILL.md procedures.
                ConversationState dataclass for per-user message history.
                HermesAgent class that calls the Anthropic API.
router.py       Intent classifier using Claude Haiku. Maps free-text to an AgentID.
config.py       Loads .env with override=True (handles empty shell env vars).
```

**Request flow:**
1. User sends a message or command
2. If a command → activates the corresponding agent, shows welcome message
3. If plain text in GENERAL mode → Haiku classifies intent → auto-routes to specialist if confident
4. If plain text in an active specialist → sent directly to that agent
5. Agent calls Anthropic API with the skill's system prompt + conversation history
6. Reply chunked and sent back to Telegram

**Design decisions:**
- `load_dotenv(override=True)` — prevents empty shell env vars from masking `.env` values
- In-memory session state — simple, no database needed for single-user deployment
- Haiku for routing (fast, cheap), Sonnet for skills (higher quality for complex MDM reasoning)
- Every skill output is framed as a DRAFT for human review — matches the skill pack's core principle
- CSV file uploads auto-route to DQ Audit; other text formats accepted as plain text

---

## Usage patterns

**Duplicate resolution workflow:**
```
/dedup
[paste two supplier records with TRN, name, address, phone]
→ DECISION: MATCH / NO MATCH / HUMAN REVIEW with gate-by-gate reasoning

/golden
[paste the match cluster]
→ golden record with field-by-field provenance
```

**Address cleanup:**
```
/location
[paste an address: country, region/emirate, PO Box or postal code, area]
→ canonical form with change log and flags
```

**Morning briefing:**
```
/briefing
[paste DQ audit numbers + exception queue state]
→ 150–250 word briefing with Attention Today / SLA Watch / Trending / Numbers
```

---

## Security notes

- `.env` is gitignored. Never commit real tokens.
- `ADMIN_USER_IDS` restricts access to specific Telegram accounts.
- No data is persisted — session state is in-memory and resets on restart.
- No beneficiary or personally sensitive data passes through this bot by design — it is a
  structural MDM tool (names, addresses, identifiers), not a case management system.
