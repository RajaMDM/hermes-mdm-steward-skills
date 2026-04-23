# Security

## What this document is for

This repository contains a skill pack for Hermes Agent and a Telegram bot that share the same `SKILL.md` files. Both components interact with large language models and external systems. That means they carry the same class of security risks as any agent framework with tool access.

This page is not a formal security audit. It is an honest disclosure of what to be aware of before you fork, deploy, or extend this work.

---

## Threat model

Before reading further, understand the deployment this repo was built for:

- **Single-operator use.** The Telegram bot restricts access to specific Telegram user IDs via `ADMIN_USER_IDS`. The Hermes CLI runs on the operator's own machine.
- **Self-authored skills only.** The six `SKILL.md` files in `skills/` were written by the repository author. No third-party skills are loaded.
- **Local-first, no multi-tenant surface.** There is no web server, no public API, no multi-user session isolation.

If your intended deployment differs from the above — in particular, if you plan to expose the bot to users beyond yourself, load skills from other repositories, or deploy on shared infrastructure — this repo's assumptions do not cover your case, and you need to do your own threat modelling.

---

## Risks this repo inherits from any agent framework

These risks are not specific to this repository. They apply to Hermes Agent, OpenClaw, Claude Code, Cursor, LangChain, or any tool that gives a language model access to your machine or data. They are listed here because someone forking this repo should see them acknowledged, not hidden.

### 1. Prompt injection

Language models follow instructions they see in any text. If the agent reads an email, document, webpage, or message that contains instructions, the model may act on those instructions — even if they contradict yours.

Mitigation in this repo: the skills are designed to produce *draft decisions for human review* rather than autonomous actions. Every output is framed as a recommendation, not an execution.

Mitigation in your deployment: never give the agent permission to act on decisions without human approval when those decisions are based on externally-sourced text. Be especially cautious with email gateways, web scraping, and unfiltered message intake.

### 2. Malicious third-party skills

The Hermes skill system loads any `SKILL.md` file pointed at by the configuration. A skill is not just data — the procedure text becomes part of the model's instructions. A malicious skill can instruct the agent to exfiltrate credentials, send unauthorised messages, or behave deceptively.

In 2026, Cisco's AI security research team published findings on a third-party OpenClaw skill that performed data exfiltration and prompt injection without user awareness. The same class of risk exists for any `agentskills.io`-compliant skill source, including Hermes.

Mitigation in this repo: all six skills are self-authored by the repository owner. None load dynamic content from the network at skill-read time.

Mitigation in your deployment: treat loading a third-party skill pack the same way you would treat running `curl | bash` from the internet. Read the skill. Read the author. Read the git history. If anything looks off, don't load it.

### 3. Credential exposure

Any file containing API keys, tokens, or secrets on the operator's machine is at risk if the machine is compromised.

In this repo:
- `telegram-bot/.env` is **gitignored** and contains the Telegram bot token, Anthropic API key, and admin user IDs.
- `telegram-bot/.env.example` is committed as a template and contains no real credentials.
- The Hermes authentication uses Claude's OAuth flow; the token is stored in `~/.hermes/.env` (outside this repo).

Mitigation if you fork this repo: verify `.gitignore` includes `.env` before committing anything. Verify no real token strings are pasted into your commits (run `git log -p | grep -iE 'sk-|token|key'` before pushing). If a token is accidentally pushed, assume it is compromised and revoke it immediately — do not rely on force-pushing to remove it from history.

### 4. Network egress

When the agent runs, it makes HTTPS requests to external services (Anthropic API, Telegram Bot API, potentially others depending on how you extend it). Any skill that adds web fetching, email reading, or similar capabilities broadens the attack surface.

Mitigation in this repo: the DQ audit script runs on local CSV files only. The Telegram bot connects to Telegram and Anthropic. No other network egress from the provided skills.

Mitigation in your deployment: if you extend with web-fetching or email-integration skills, restrict outbound network access at the firewall level. Use allowlists, not denylists.

### 5. Local file access

The Hermes CLI has read and write access to files in directories the operator points it at. A skill that misbehaves — or one the operator asks to "fix the whole project" — can modify, delete, or encrypt local files.

Mitigation in this repo: the DQ audit script is read-only. The skills do not request file writes beyond what the operator directly invokes.

Mitigation in your deployment: run the Hermes CLI from a bounded working directory. Do not run it from your home directory unless you fully trust every skill loaded. Consider running in a container or a dedicated user account for higher isolation.

---

## Risks specific to this repository's design

### Telegram bot single-user assumption

The `ADMIN_USER_IDS` check in `telegram-bot/config.py` is the only access control. It filters by Telegram user ID on every message. If you want to allow multiple users, you must add:

- Per-user session isolation (currently the bot uses a single in-memory session map keyed by chat ID)
- Rate limiting per user
- Audit logging
- Access revocation workflow

None of these are implemented. Adding users without these controls is not recommended.

### In-memory state

The Telegram bot's conversation state is held in process memory. Restarting the bot clears all sessions. This is deliberate — no chat history is persisted to disk, which reduces the data-breach surface.

Implication: if you want persistence (for context continuity across restarts), you will need to add a database. Doing so changes the threat model — you now have data at rest that must be encrypted, backed up, and access-controlled.

### No input validation on CSV upload

The DQ audit accepts CSV files. Oversized files, malformed CSVs, or files with adversarial content (e.g., formula injection aimed at Excel, deeply nested structures) are not filtered.

Mitigation: only upload CSVs from sources you trust. If exposing the audit to less-trusted users, add file-size limits, schema validation, and reject files that look suspicious before passing them to the skill.

---

## What to do if you find a vulnerability

If you discover a security issue in this repository:

1. **Do not open a public GitHub issue.** Public issues are visible to everyone.
2. **Email the repository owner directly** at raja.cloudmdm@gmail.com with a description of the issue, reproduction steps, and any proposed remediation.
3. **Allow a reasonable window for response** before public disclosure. This is a single-practitioner project; response times may not match those of funded security teams.

I will acknowledge receipt within 5 business days and work with you on remediation and disclosure timing.

---

## What this repo does not provide

- Formal security certification (SOC 2, ISO 27001, FedRAMP — none of these apply)
- Compliance attestations for regulated industries (HIPAA, PCI-DSS, GDPR — none of these are covered)
- Penetration testing results
- A vulnerability disclosure program with bounties
- A dedicated security team

If your organisation requires any of the above, this repository is not the right starting point. Fork it for learning or internal prototyping, but do not deploy it to production without the appropriate controls.

---

## Honest final note

Agent frameworks are powerful because they give a language model access to systems. That same power is what creates the security surface. There is no version of "useful agent" that is also "zero-risk" — the two are in tension by design.

This repository aims to demonstrate a pattern. It was built by a single practitioner to explore how MDM expertise can be encoded as portable skills. It is not infrastructure-grade, it is not enterprise-hardened, and it should not be treated as either.

Use with appropriate caution. Fork with appropriate understanding. Deploy with appropriate controls.

---

*Author: Raja Shahnawaz Soni — [LinkedIn](https://linkedin.com/in/raja-shahnawaz/)*
*Last reviewed: April 23, 2026*
