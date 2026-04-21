# Roadmap — MDM Steward Agent

Where the project is heading, what is currently blocked and why, and what triggers the next phase.

---

## Current phase — v0.1 "Seed Pack"

**Status:** Released 2026-04-21.

The seed release establishes the skill pack pattern, a working DQ audit, and three end-to-end scenario walkthroughs against a synthetic dataset. It is intentionally lean.

## Near-term (next 30 days)

### 1. Move hosting from local to a $5 VPS

**What triggers it:** validation from two or more external users that the pattern is useful and the limits of local-only are a real blocker.

**What it requires:**

- A VPS provider account (Hetzner, DigitalOcean, or similar).
- Hermes installed on the VPS with the email gateway configured to forward SMTP through a sender domain.
- The skill pack cloned onto the VPS.
- A systemd unit or equivalent to keep Hermes running across reboots.

**Cost:** ~$5–10 per month, plus a sender domain if not already owned.

**Trade-off:** Running on a VPS means the agent is always on and briefings fire reliably — but it also means the machine is exposed to the public internet and needs basic hardening (SSH key only, fail2ban, automated security updates).

**Not started. Blocked by:** waiting for the v0.1 release to stabilise and gather usage signal.

### 2. Add GCC-wide variant tables to `mdm-location-validator`

**What it requires:**

- Canonical emirate and region tables for Saudi Arabia, Kuwait, Qatar, Bahrain, Oman.
- Country-specific postal conventions (KSA uses a five-digit postal code rather than PO Box for many addresses; Qatar and Kuwait have different structures).
- A tenant-configurable way to select which GCC country's rules apply to a dataset.

**Trigger:** first user asking for non-UAE support, or the author's own need for it in a GCC-wide dataset.

### 3. Add a fuzzy-match skill for Gate 2 of the duplicate resolver

Current Gate 2 uses exact-match-after-normalization. Real-world Arabic transliteration variants (Al-Futtaim vs Alfuttaim vs Al Futtaim) are best handled with a phonetic or edit-distance match.

**What it requires:**

- A decision on the matching algorithm — Jaro-Winkler for latin transliteration, Soundex-Arabic or equivalent for Arabic-origin names.
- A threshold-based confidence score that feeds into the Gate 2 output.
- A supporting Python script (similar to `run_dq_audit.py`) that the skill calls via `execute_code`.

**Trigger:** first case where the exact-match Gate 2 misses a genuine duplicate and the miss becomes visible in an audit.

## Medium-term (60–90 days)

### 4. Reference integration with one Core MDM platform

Pick one platform and build a reference nightly-export pipeline that:

- Exports supplier, product, and location tables to CSV.
- Runs the DQ audit over the exported files.
- Pushes exception records back to the platform's exception queue.

**Likely candidate:** Microsoft Master Data Services, given the author's active Power Platform practice and the Microsoft stack available in Core MDM.

**What it requires:**

- Platform access (or a local developer instance).
- A documented export procedure (stored procedures, SSIS package, or Power Automate flow — depending on the user's pattern).
- A thin Python wrapper that calls the platform's API to push exception records.

**Trigger:** a concrete use case from a practitioner who already has Core MDM running and wants to demo the skill pack end-to-end against real data.

### 5. Web dashboard for the agent's skill-creation activity

Hermes has a web dashboard feature. A companion dashboard specific to the MDM pack would show:

- Skills invoked in the last 7 days, ranked by frequency.
- Agent-proposed new skills awaiting approval.
- Audit history and trend charts (completeness, duplicate candidate count over time).

**What it requires:** Hermes' web dashboard extension API, plus a small React frontend.

**Trigger:** user feedback that the CLI + messaging gateway combination is insufficient for governance oversight.

## Longer-term (90+ days)

### 6. Multi-tenant pack

Extend the pack to support running multiple tenants from a single Hermes instance, each with their own source-system trust hierarchy, canonical emirate / country forms, and exception queue routing.

**What it requires:** a tenant configuration layer, likely as a YAML file per tenant loaded by the skills at invocation time.

**Trigger:** demand from a consultancy or multi-client deployment scenario.

### 7. Formal skill publishing to the Hermes Skills Hub

The Hermes Skills Hub (`agentskills.io`) accepts community skill submissions. Publishing the MDM pack formally would:

- Make it discoverable to users who do not know about this repo.
- Subject it to the Skills Hub security scanner.
- Give it an install command: `hermes skills install hermes-mdm-steward-skills/…`.

**What it requires:** compliance with the Skills Hub submission requirements and passing the security scan.

**Trigger:** v1.0 readiness — the pack is stable, the skills are hardened, and the author is confident supporting it publicly.

## What is explicitly out of scope

- **Training or fine-tuning a custom model.** The pack is model-agnostic and relies on the user's configured LLM provider (Nous Portal, Anthropic, OpenAI, local Ollama, or any other). Model selection is a user decision, not a pack decision.
- **Becoming a commercial product.** This is an open-source demonstration. Any commercial extension is a separate conversation with a separate licence.
- **Support for every MDM domain.** The pack focuses on supplier, product, and location domains. Customer MDM, employee MDM, and reference data management are different problems with different skill requirements. If demand emerges, those are separate packs, not extensions of this one.

## Triggers that would pause or stop development

- **Hermes Agent stops being actively maintained.** Unlikely given Nous Research's current trajectory, but if the framework goes dormant, the pack's value declines. In that case, port to whichever framework the community has moved to while preserving the agentskills.io-compliant skills.
- **A better abstraction emerges.** If the agent-skills-with-messaging-gateway pattern is superseded by something genuinely better (not just newer), follow the better pattern.

---

*This roadmap is deliberately modest. The seed pack's purpose is to establish a pattern, not to become a product. Each roadmap item is optional and gated on real demand.*
