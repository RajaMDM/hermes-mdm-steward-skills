# Project History — MDM Steward Agent

A chronological narrative of what was built, why, and how it evolved. Written for non-technical readers.

---

## Origin

In April 2026, Nous Research released Hermes Agent — an open-source AI agent framework with a learning loop, persistent memory, and a messaging gateway. It was two months old when this project began, still at version 0.8, moving fast.

The question that started this project: **what does a twenty-year MDM practitioner pick up a brand-new agent framework for?**

The answer settled on a long-standing problem in every enterprise MDM programme: **resolution knowledge lives in stewards' heads**. When a duplicate supplier appears, or a Gulf address fails validation, or a survivorship decision needs a tie-break, the answer is a judgement call that took years to learn. It rarely gets written down. When stewards leave or new brands onboard, the knowledge walks out the door.

Hermes offered two features that mapped directly to that problem. Its skill system lets you codify resolution patterns as plain-Markdown playbooks. Its learning loop proposes new skills when it sees repeated patterns. Together, they turn operational knowledge into living organisational memory — which is exactly what an MDM programme needs.

## What was built

A public GitHub repository — a **portable skill pack** that plugs into Hermes Agent via its `external_dirs` configuration. Not a fork of Hermes, not a rebuilt framework. A directory of skills, a synthetic dataset for demonstration, and wiring instructions. Anyone who installs Hermes can clone this repo, point Hermes at it, and immediately have an MDM-capable agent.

Six seed skills cover the core steward workflow: duplicate resolution, supplier name standardization, Gulf-region address validation, golden record composition, a scheduled data quality audit, and a morning briefing template. Each skill is a playbook with procedure, pitfalls, and verification steps — written the way a senior steward would hand off knowledge to a junior one.

A synthetic dataset built around a fictitious parent company, **Nexora Retail**, with five sub-brands — Verdant Grocers, Luxora Beauty, StrideSport, Kindle & Loom, and Petalia Fashion. The data is seeded with realistic MDM pain: cross-brand duplicates sharing tax registration numbers, Emirate naming variants, legal-entity suffix inconsistencies, missing geo-coordinates. Safe to fork, share, and demo without exposing any real-world commercial information.

Three scenario walkthroughs showing the skills working together — resolving a cross-brand duplicate, correcting an address variant, and running the scheduled nightly audit with email delivery.

## What it demonstrates

Three things, none of them framework-specific.

**First**, operational MDM knowledge can be codified as portable skills. Because the skill pack follows the [agentskills.io](https://agentskills.io) open standard, the playbooks are not locked to Hermes. If the framework landscape shifts, the skills port.

**Second**, a learning-loop agent is a natural fit for steward work. The pattern of "resolve exception, capture decision, reuse next time" is exactly what Hermes' skill-creation mechanism was built for.

**Third**, data residency and air-gapped deployment are achievable without sacrificing capability. The whole system runs locally. Skills are plain Markdown. The synthetic dataset means the pipeline can be demonstrated without connecting to any real MDM platform.

## Why this matters in context

This is not the first platform in the portfolio. It sits alongside BrainDrop (a study companion for schoolchildren), the Data Alchemist / MDM Lab (a data literacy platform on Cloudflare Workers), SYNAPTIQ (an enterprise architecture learning system), QualIQ (a data quality learning platform), and NumerX (a mathematics tutor).

What this project adds that the others do not: a Python codebase of real weight, a vector-database-adjacent pattern via Hermes' skill retrieval, and a long-running-service architecture via the messaging gateway. It closes a gap the portfolio had — everything before it was either a static web app or a Markdown artefact. This is the first project in the portfolio that would run unattended on a server.

## Known limitations

The machine running Hermes must be on to receive scheduled briefings. A $5 VPS would solve that but is deliberately out of scope for this phase.

Hermes is at version 0.8. The framework is likely to introduce breaking changes. The skill pack follows the agentskills.io standard to minimise exposure, but users should expect to re-verify against current Hermes docs.

The skills encode patterns that work for UAE master data. A GCC-wide deployment would require additions (Saudi region-city distinction, Qatar postal system, Kuwait governorate naming). A global deployment would require substantial extension.

No connection to a real MDM platform is included. Connecting to Informatica IDMC, Microsoft Master Data Services, or any Core MDM is left as an exercise — each needs its own credentials and integration pattern.

## What the project is not

It is not production software. It is a proof of practice — a working demonstration that an MDM programme's operational knowledge can be encoded, versioned, and shared like code. It is MIT licensed, open to fork, and intended to be picked up by others who want to do the same in their own environments.

---

*Author: Raja Shahnawaz Soni — Enterprise Data Management leader, Dubai.*
