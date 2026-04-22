# Changelog — MDM Steward Agent

All notable changes to this project will be documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.0] — 2026-04-21

GCC-wide expansion of the location validator and corrections to the repo's factual claims.

### Changed

- **`mdm-location-validator` expanded from UAE-only to full GCC coverage** — canonical administrative-level tables for Saudi Arabia (13 regions), Kuwait (6 governorates), Qatar (8 municipalities), Bahrain (4 governorates), and Oman (11 governorates) in addition to the existing UAE (7 emirates).
- **Per-country postal conventions** — the skill now distinguishes between PO Box–primary countries (UAE), postal-code-primary countries (KSA 5-digit, Kuwait 5-digit, Bahrain 3-4-digit, Oman 3-digit), and Qatar's zone/street/building triple (no postal code).
- **Per-country geo-coordinate bounding boxes** — coordinate sanity checks now route by country with appropriate tolerances (±50 km for small countries, ±200 km for KSA and Oman).
- **Removed outdated Microsoft Master Data Services reference** from README and documentation. MDS was removed from SQL Server 2025 and is no longer a current integration target. READMEs now refer generically to "your Core MDM platform" with examples of current options (Informatica IDMC, Profisee, Reltio, Ataccama).
- **Corrected Hermes Agent version reference** — v0.10.0 is the tested target (v0.8 reference from initial release was out of date by the time of publication).
- **Nexora Retail location dataset expanded** — added sample records across Saudi Arabia, Kuwait, Qatar, and Bahrain with realistic naming variants, to make the GCC coverage demonstrable rather than just declared.

### Rationale

External review raised two specific concerns: (1) Microsoft MDS no longer exists as a current product and shouldn't be used as an example integration, and (2) the UAE-only scope undersold the practitioner's actual domain, which is GCC-wide. Both fixes land in this release.

---

First public release. Seed skill pack and synthetic dataset for demonstrating the MDM Steward Agent pattern.

### Added

- **Six seed skills** covering the core MDM steward workflow:
  - `mdm-duplicate-resolver` — four-gate decision procedure for match/merge exceptions.
  - `mdm-supplier-standardizer` — legal entity suffix normalization, case cleanup, trading name extraction.
  - `mdm-location-validator` — Gulf-region address standardization with geo-coordinate sanity checks.
  - `mdm-golden-record-composer` — field-level survivorship with full provenance tracking.
  - `mdm-dq-audit` — scheduled audit with a production-ready Python helper script.
  - `mdm-steward-briefing` — concise morning briefing for delivery via messaging gateway.
- **Synthetic Nexora Retail dataset** — three CSV files (suppliers, products, locations) with five fictitious sub-brands. Seeded with realistic MDM pain: cross-brand duplicates, Emirate naming variants, legal entity suffix inconsistency, missing geo-coordinates.
- **Three scenario walkthroughs** showing end-to-end resolution patterns — cross-brand duplicate merge, address variant correction, scheduled nightly audit with email delivery.
- **Standing project documentation set**:
  - `PROJECT_HISTORY.md` — narrative for non-technical readers.
  - `TECH_MEMORY.md` — technical decisions and gotchas.
  - `CHANGELOG.md` — this file.
  - `DEFENSE_BRIEF.md` — talking points for defending technical choices.
  - `ROADMAP.md` — near-term and longer-term direction.
- **Installation guide** (`INSTALL.md`) — wiring the pack into Hermes Agent via `external_dirs`.
- **MIT License.**

### Business impact

- A public proof of practice that MDM resolution knowledge can be codified as portable, versioned skills — rather than living in stewards' heads.
- Demonstrates that a brand-new agent framework (Hermes Agent, released Feb 2026) can be picked up and extended for enterprise master data workloads within weeks of its public release.
- Closes a portfolio gap: first project in the author's body of work to include a Python codebase, long-running-service architecture, and cron-driven automation alongside existing single-file web app projects.

### Known limitations

- Local-only deployment means the host machine must be running for scheduled briefings to fire. A VPS move is on the roadmap.
- Hermes Agent v0.10.0 is the tested target; framework-level breaking changes upstream may require skill pack adjustments.
- No live connection to a real MDM platform is included; the audit operates against CSV files only. Integration with any Core MDM platform (Informatica IDMC, Profisee, Reltio, or equivalent) is left as an exercise per deployment.
