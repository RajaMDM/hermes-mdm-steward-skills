# hermes-mdm-steward-skills

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Hermes Agent](https://img.shields.io/badge/Hermes%20Agent-v0.10%2B-F5A623)](https://github.com/NousResearch/hermes-agent)
[![agentskills.io](https://img.shields.io/badge/skills-agentskills.io-34D399)](https://agentskills.io)

> Six MDM resolution playbooks encoded once as `SKILL.md` files, addressable through two channels — **Hermes Agent CLI** for local steward work, **Telegram bot** for conversational on-call access. Decisions. Standardization. Golden records. DQ audits. Morning briefings.

```
❯ /mdm-duplicate-resolver are supplier NX-SUP-00142 and NX-SUP-00189 the same entity?

[loads skill mdm-duplicate-resolver 0.0s]

DECISION: MATCH
CONFIDENCE: High
REASONING:
  - Gate 1: Shared TRN 100123456700003 — decisive. Branch-office pitfall
    ruled out (same PO Box, same email domain, same emirate).
  - Gate 2: Names normalize identically to DUBAI TRADING LLC — confirms.
  - Gate 3: Same PO Box, same email domain, same emirate — confirms.
  - Gate 4: Both Active — no lifecycle flag.
RECOMMENDED ACTION: Merge. Route through steward for survivorship.
SURVIVING RECORD: NX-SUP-00142 (older, cleaner formatting)
```

![Demo](demo.gif)

Tested live on `claude-opus-4-7` and `claude-sonnet-4-6` via [Hermes Agent](https://github.com/NousResearch/hermes-agent) v0.10.0 on macOS. MIT licensed. Author: **Raja Shahnawaz Soni** — Enterprise Data Management leader, Dubai.

---

## Why this exists

Most enterprise MDM programmes have the same problem: resolution knowledge lives in stewards' heads. When a duplicate supplier surfaces, or a Gulf address fails validation, or a survivorship tie-break is needed, the answer is a judgement call that took years to earn and five minutes to make. It rarely gets written down. When the steward leaves, or the programme scales to new brands, the knowledge walks out the door.

This repo is the opposite pattern: **write the playbooks down as structured skills, let the agent execute them, let the agent accumulate new ones as stewards teach it** — and make those skills accessible through whichever channel the steward is already using. CLI at the desk, Telegram on the phone. One source of truth, two front doors.

## Architecture — two channels, one source of truth

```
                    ┌─────────────────────────┐
                    │    skills/*/SKILL.md    │   ← source of truth
                    │  (6 resolution          │     (authored playbooks)
                    │   playbooks)            │
                    └────────────┬────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
          ┌─────────▼─────────┐     ┌─────────▼─────────┐
          │  Hermes Agent CLI │     │  Telegram Bot     │
          │  (local, keyboard) │     │  (remote, chat)   │
          │                    │     │                   │
          │  /mdm-* slash      │     │  /dedup /golden   │
          │  commands          │     │  /location etc.   │
          │                    │     │                   │
          │  Full skill        │     │  System prompts   │
          │  procedure loaded  │     │  derived from     │
          │  into Opus/Sonnet  │     │  SKILL.md         │
          └────────────────────┘     └───────────────────┘
```

**Channel 1 — Hermes Agent CLI.** The skill pack loads into [Hermes Agent](https://github.com/NousResearch/hermes-agent) via its `external_dirs` config. Every `SKILL.md` becomes a slash command. Hermes loads the full procedure, pitfalls, and verification steps into context before responding. Best for deep steward work at a workstation. See `skills/`.

**Channel 2 — Telegram bot.** A standalone Python service in `telegram-bot/` exposes the same six skills as conversational agents over Telegram. Haiku routes free-text to the right specialist; Sonnet runs the skill. No Hermes dependency — the bot talks directly to the Anthropic API. Best for quick on-call checks from a phone. See [`telegram-bot/README.md`](telegram-bot/README.md).

Both channels derive their behaviour from the same `SKILL.md` files. Edit a skill once; both channels reflect the change.

## The six skills

Each is a single `SKILL.md` with procedure, pitfalls, and verification steps — written the way a senior steward hands off knowledge to a junior one.

| Skill | Handles |
|---|---|
| [`mdm-duplicate-resolver`](skills/mdm-duplicate-resolver/SKILL.md) | Four-gate match/merge decision for supplier and business-partner duplicates |
| [`mdm-supplier-standardizer`](skills/mdm-supplier-standardizer/SKILL.md) | Legal-entity suffix normalization (LLC / L.L.C. / Ltd / FZE / FZCO), trading name vs legal name |
| [`mdm-location-validator`](skills/mdm-location-validator/SKILL.md) | GCC-wide address standardization — UAE, Saudi Arabia, Kuwait, Qatar, Bahrain, Oman. Per-country administrative levels, postal conventions (PO Box vs 5-digit postal code vs Qatar's zone/street/building triple), bounding-box coordinate checks |
| [`mdm-golden-record-composer`](skills/mdm-golden-record-composer/SKILL.md) | Field-level survivorship with full provenance map |
| [`mdm-dq-audit`](skills/mdm-dq-audit/SKILL.md) | Scheduled DQ audit with a production-ready Python helper (`scripts/run_dq_audit.py`) |
| [`mdm-steward-briefing`](skills/mdm-steward-briefing/SKILL.md) | Concise morning briefing for email / Telegram / Slack delivery |

Plus a synthetic **Nexora Retail** dataset (fictitious parent with five sub-brands — Verdant Grocers, Luxora Beauty, StrideSport, Kindle & Loom, Petalia Fashion) seeded with realistic MDM pain: cross-brand duplicates sharing TRN, naming variants across countries, legal-entity suffix inconsistency, near-duplicate products sharing barcode. Three scenario walkthroughs ship with the repo showing the skills working end-to-end.

## Install

### Channel 1 — Hermes Agent (CLI)

```bash
# 1. Clone the repo
git clone https://github.com/RajaMDM/hermes-mdm-steward-skills.git ~/.agents/hermes-mdm-steward-skills

# 2. Point Hermes at the skill directory
#    Add to ~/.hermes/config.yaml under the `skills:` section:
#    skills:
#      external_dirs:
#        - ~/.agents/hermes-mdm-steward-skills/skills

# 3. Launch Hermes
hermes
```

Full Hermes wiring guide, troubleshooting, and optional email-gateway setup: see [INSTALL.md](INSTALL.md).

### Channel 2 — Telegram bot

See [`telegram-bot/README.md`](telegram-bot/README.md) for setup instructions. You'll need a Telegram bot token from [@BotFather](https://t.me/BotFather) and an Anthropic API key. Runs as a standalone Python service — no Hermes required.

## Try it

```bash
# Run the DQ audit against the bundled synthetic dataset
cd ~/.agents/hermes-mdm-steward-skills
python skills/mdm-dq-audit/scripts/run_dq_audit.py
```

From inside Hermes chat (Channel 1):

```
❯ /mdm-duplicate-resolver [paste two records]
❯ /mdm-location-validator [paste a KSA or Kuwait address]
❯ /mdm-dq-audit run the audit and summarize the top issues
❯ /mdm-golden-record-composer compose the golden record from the match cluster
```

From Telegram (Channel 2):

```
/dedup [paste two records]
/location [paste an address]
/dqaudit [attach a CSV — auto-routes]
/briefing [paste audit numbers + queue state]
```

## What this demonstrates

- **Operational MDM knowledge can be codified as portable skills** — the [agentskills.io](https://agentskills.io) open standard means the playbooks port across compatible agents
- **One source of truth, multiple channels** — the same `SKILL.md` drives both a local CLI agent and a remote chat agent. The channel is an implementation detail; the skill is the asset
- **A learning-loop agent is a natural fit for steward work** — resolve, capture, reuse
- **Data residency and air-gapped deployment are achievable** without sacrificing capability — Hermes runs local, skills are plain Markdown, synthetic data means no MDM platform dependency to demo

## Known limitations

- **Not production-hardened.** Seed skills are starting points. Real deployments need tenant-specific governance, survivorship rules, and regional quirks.
- **Hermes is at v0.10.0** (public release Feb 2026). Framework behaviour may shift. Skills follow the agentskills.io standard to minimise exposure, but verify against [current Hermes docs](https://hermes-agent.nousresearch.com/docs) before assuming anything.
- **No connection to your Core MDM platform.** The DQ audit reads CSV. Wiring this pack to your platform of choice — whether Informatica IDMC, Profisee, Reltio, Ataccama, or something custom — is left per-deployment. Each needs its own credentials and integration pattern.
- **GCC-focused.** Administrative-level tables and postal conventions cover UAE, Saudi Arabia, Kuwait, Qatar, Bahrain, and Oman. Extending beyond the GCC is on the roadmap.
- **Telegram bot is single-user by design.** `ADMIN_USER_IDS` restricts access to specific Telegram accounts. Multi-user deployments require additional session isolation and access control.

## Body of work

This skill pack sits alongside **The MDM Lab by Raja Shahnawaz Soni** — a data literacy platform for practitioners, deployed on Cloudflare Workers.

Philosophy: *Anyone can describe a system. I'd rather hand you a working one and say — here, try it.*

## Documentation

- [`INSTALL.md`](INSTALL.md) — Hermes wiring, troubleshooting
- [`telegram-bot/README.md`](telegram-bot/README.md) — Telegram bot setup, architecture, security notes
- [`docs/PROJECT_HISTORY.md`](docs/PROJECT_HISTORY.md) — narrative for non-technical readers
- [`docs/TECH_MEMORY.md`](docs/TECH_MEMORY.md) — technical decisions, gotchas, patterns
- [`docs/DEFENSE_BRIEF.md`](docs/DEFENSE_BRIEF.md) — rationale for every major technical choice
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — what's next, what's blocked
- [`docs/CHANGELOG.md`](docs/CHANGELOG.md) — change history
- [`scenarios/`](scenarios/) — end-to-end walkthroughs

## License

MIT. Fork it, adapt it, ship it. Attribution appreciated.

---

*Raja Shahnawaz Soni — [LinkedIn](https://linkedin.com/in/raja-shahnawaz/) — Dubai*
