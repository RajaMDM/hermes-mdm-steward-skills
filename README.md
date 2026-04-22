# hermes-mdm-steward-skills

> Six MDM resolution playbooks as portable Hermes Agent skills. Drop in, point Hermes at them, get an on-call data steward that walks through match/merge decisions, standardizes GCC addresses, composes golden records, and runs scheduled DQ audits.

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

This skill pack is the opposite pattern: **write the playbooks down as structured skills, let the agent execute them, and let the agent accumulate new ones as stewards teach it**. Over time, the pack becomes the programme's living operational memory.

## What's in the pack

Six seed skills. Each is a single `SKILL.md` with procedure, pitfalls, and verification steps — written the way a senior steward hands off knowledge to a junior one.

| Skill | Handles |
|---|---|
| [`mdm-duplicate-resolver`](skills/mdm-duplicate-resolver/SKILL.md) | Four-gate match/merge decision for supplier and business-partner duplicates |
| [`mdm-supplier-standardizer`](skills/mdm-supplier-standardizer/SKILL.md) | Legal-entity suffix normalization (LLC / L.L.C. / Ltd / FZE / FZCO), trading name vs legal name |
| [`mdm-location-validator`](skills/mdm-location-validator/SKILL.md) | GCC-wide address standardization — per-country administrative levels (emirate / region / governorate / municipality), postal conventions, geo-coordinate sanity checks |
| [`mdm-golden-record-composer`](skills/mdm-golden-record-composer/SKILL.md) | Field-level survivorship with full provenance map |
| [`mdm-dq-audit`](skills/mdm-dq-audit/SKILL.md) | Scheduled DQ audit with a production-ready Python helper (`scripts/run_dq_audit.py`) |
| [`mdm-steward-briefing`](skills/mdm-steward-briefing/SKILL.md) | Concise morning briefing for email / Telegram / Slack delivery |

**GCC coverage:** the location validator carries canonical administrative-level tables for all six GCC countries — United Arab Emirates, Saudi Arabia, Kuwait, Qatar, Bahrain, and Oman — with per-country postal conventions (PO Box vs 5-digit postal code vs Qatar's zone/street/building triple), canonical region/governorate names with common variants, and bounding-box coordinate checks per country.

Plus a synthetic **Nexora Retail** dataset (fictitious parent with five sub-brands — Verdant Grocers, Luxora Beauty, StrideSport, Kindle & Loom, Petalia Fashion) seeded with realistic MDM pain: cross-brand duplicates sharing TRN, naming variants across countries, legal-entity suffix inconsistency, near-duplicate products sharing barcode. Three scenario walkthroughs ship with the repo showing the skills working end-to-end.

## Install

```bash
# 1. Clone somewhere outside ~/.hermes/
git clone https://github.com/RajaMDM/hermes-mdm-steward-skills.git ~/.agents/hermes-mdm-steward-skills

# 2. Point Hermes at the skill directory
#    Add to ~/.hermes/config.yaml under the `skills:` section:
#    skills:
#      external_dirs:
#        - ~/.agents/hermes-mdm-steward-skills/skills

# 3. Launch Hermes
hermes
```

Full wiring guide, troubleshooting, and optional email-gateway setup: see [INSTALL.md](INSTALL.md).

## Try it

```bash
# Run the scheduled DQ audit against the bundled synthetic dataset
cd ~/.agents/hermes-mdm-steward-skills
python skills/mdm-dq-audit/scripts/run_dq_audit.py

# Or from inside Hermes chat:
❯ /mdm-duplicate-resolver [paste two records]
❯ /mdm-location-validator [paste a KSA or Kuwait address to normalize]
❯ /mdm-dq-audit run the audit and summarize the top issues
❯ /mdm-golden-record-composer compose the golden record from the match cluster
```

## What this demonstrates

- **Operational MDM knowledge can be codified as portable skills** — the [agentskills.io](https://agentskills.io) open standard means the playbooks port across compatible agents
- **A learning-loop agent is a natural fit for steward work** — resolve, capture, reuse
- **Data residency and air-gapped deployment are achievable** without sacrificing capability — Hermes runs local, skills are plain Markdown, synthetic data means no MDM platform dependency to demo

## Known limitations

- **Not production-hardened.** Seed skills are starting points. Real deployments need tenant-specific governance, survivorship rules, and regional quirks.
- **Hermes is at v0.10.0** (public release Feb 2026). Framework behaviour may shift. Skills follow the agentskills.io standard to minimise exposure, but verify against [current Hermes docs](https://hermes-agent.nousresearch.com/docs) before assuming anything.
- **No connection to your Core MDM platform.** The DQ audit reads CSV. Wiring this pack to your platform of choice — whether Informatica IDMC, Profisee, Reltio, Ataccama, or something custom — is left per-deployment. Each needs its own credentials and integration pattern.
- **GCC-focused.** Administrative-level tables and postal conventions cover UAE, Saudi Arabia, Kuwait, Qatar, Bahrain, and Oman. Extending beyond the GCC is on the roadmap.

## Body of work

This skill pack sits alongside **The MDM Lab by Raja Shahnawaz Soni** — a data literacy platform for practitioners, deployed on Cloudflare Workers.

Philosophy: *Anyone can describe a system. I'd rather hand you a working one and say — here, try it.*

## Documentation

- [`INSTALL.md`](INSTALL.md) — Hermes wiring, troubleshooting
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
