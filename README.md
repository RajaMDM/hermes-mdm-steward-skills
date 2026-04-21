# MDM Steward Agent

> A portable, open-standard skill pack that turns a generic LLM into an on-call Master Data Management steward.

Built for [Hermes Agent](https://github.com/NousResearch/hermes-agent) (Nous Research) via the [agentskills.io](https://agentskills.io) open standard. Not a fork. Not a framework. A loadable skill directory that plugs into Hermes — or any agentskills.io-compatible agent — and immediately gives it operational MDM resolution playbooks.

Author: **Raja Shahnawaz Soni** — Enterprise Data Management leader, Dubai. License: MIT.

---

## Why this exists

Most enterprise MDM programmes have the same problem: **resolution knowledge lives in stewards' heads**. When a duplicate supplier record surfaces, or a Gulf address fails validation, or a survivorship decision needs a tie-break, the answer is a judgement call that took years to earn and five minutes to make. It never gets written down. When the steward leaves, or the programme scales to new brands, the knowledge walks out the door.

This skill pack is an experiment in the opposite pattern: **write the playbooks down as skills, let the agent execute them, and let the agent accumulate new ones as stewards teach it**.

Each skill here is a real MDM resolution pattern encoded as a SKILL.md file. The agent loads them on-demand, applies them to dirty records, and — because Hermes has a learning loop — improves the skill when a steward corrects it. Over time, the skill pack is the programme's living operational memory.

## What's in the pack

Six seed skills, covering the core MDM steward workflow:

| Skill | Handles |
|---|---|
| `/mdm-duplicate-resolver` | Match/merge exceptions — deciding whether two supplier or customer records are the same entity |
| `/mdm-supplier-standardizer` | Legal-entity suffix normalization (LLC / L.L.C. / Limited / Ltd), abbreviation expansion, tradename vs legal name |
| `/mdm-location-validator` | Gulf address standardization — PO Box handling, Emirate naming, building/area conventions |
| `/mdm-golden-record-composer` | Survivorship rules when assembling the golden record from multiple source systems |
| `/mdm-dq-audit` | Scheduled nightly data quality audit against Core MDM, with summary generation |
| `/mdm-steward-briefing` | Morning briefing template — exceptions awaiting action, SLA breaches, trending issues |

Plus:

- **Synthetic `Nexora Retail` dataset** — fictitious parent brand with five sub-brands (Verdant Grocers, Luxora Beauty, StrideSport, Kindle & Loom, Petalia Fashion). Realistic MDM pain: name variants, address quirks, missing fields, duplicate candidates. Safe to fork, share, and demo.
- **Three scenario walkthroughs** — end-to-end examples of the agent resolving real problems using the skill pack.

## How to use it

See [INSTALL.md](INSTALL.md) for wiring this into Hermes Agent via `external_dirs`.

Once installed, every skill is available as a slash command in your Hermes CLI or any connected messaging gateway:

```
/mdm-duplicate-resolver I have two supplier records, one says "Dubai Trading LLC" 
the other "DUBAI TRADING L.L.C." — same entity?

/mdm-dq-audit run the nightly audit against datasets/nexora_suppliers_dirty.csv 
and email me the summary
```

## What this demonstrates

This project is a proof-of-practice, not a product. It shows three things:

1. **Operational MDM knowledge can be codified as portable skills.** The agentskills.io standard means these playbooks aren't locked to one agent framework.
2. **A learning-loop agent is a natural fit for steward work** — the pattern of "resolve exception → capture decision → reuse next time" is exactly what Hermes' skill-creation loop was built for.
3. **Data residency and air-gapped deployment are achievable** without sacrificing agent capability — Hermes runs local, skills are plain Markdown, and the synthetic dataset means the whole thing can be demoed without a live MDM connection.

## Body of work

This skill pack sits alongside:

- [BrainDrop](https://rajamdm.github.io/braindrop) — CBSE study companion with seven AI engines
- **The MDM Lab by Raja Shahnawaz Soni** — data literacy platform on Cloudflare Workers
- **SYNAPTIQ** — six-stage enterprise architecture learning system
- **QualIQ** — AI-powered data quality learning platform
- **NumerX** — Google OPAL-based mathematics tutor

Philosophy: *Anyone can describe a system. I'd rather hand you a working one and say — here, try it.*

## Honest limitations

- **Not production-hardened.** Seed skills are starting points. Real deployments need your own governance policies, your own survivorship rules, your own regional quirks.
- **Local-only by default.** Email gateway requires your machine to be on. Move to a VPS if you want 24/7 on-call.
- **Hermes is at v0.8** (public release Feb 2026). Framework behaviour may shift. Skills follow the agentskills.io standard, so they survive framework churn better than a fork would — but verify against current Hermes docs before assuming anything.
- **No connection to real MDM platforms.** The DQ audit script reads the synthetic CSV. Wiring it to Informatica IDMC / Microsoft Master Data Services / any real Core MDM is left as an exercise — each needs its own credentials and integration pattern.

## License

MIT. Use it, fork it, adapt it. Attribution appreciated.

---

*Raja Shahnawaz Soni — [LinkedIn](https://linkedin.com/in/raja-shahnawaz/) — Dubai*
