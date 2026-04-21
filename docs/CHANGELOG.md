# Changelog — MDM Steward Agent

All notable changes to this project will be documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] — 2026-04-21

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
- Hermes Agent v0.8 is the tested target; framework-level breaking changes upstream may require skill pack adjustments.
- No live connection to a real MDM platform is included; the audit operates against CSV files only. Integration with Core MDM platforms (Informatica IDMC, Microsoft MDS) is left as an exercise per deployment.
