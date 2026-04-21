# Tech Memory — MDM Steward Agent

Technical decisions, architectural rationale, patterns used, and known gotchas. Written for future-me and Claude.

---

## Architecture at a glance

- **Skill pack, not a fork.** The project is a directory of `SKILL.md` files plus one Python helper script. Hermes Agent loads them via its `external_dirs` configuration. No framework code is modified or duplicated.
- **agentskills.io compliant.** SKILL.md frontmatter and structure follow the open standard so the pack can be loaded by any compliant agent, not just Hermes.
- **Plain Markdown + one Python file.** The only non-Markdown artefact is `run_dq_audit.py`. Deliberate choice — keeps the pack inspectable, diffable, and portable.
- **Synthetic data bundled.** `datasets/nexora_*.csv` ship with the pack so the audit script works out of the box without any external connections.

## Decisions and why

### Skill pack pattern vs. forking Hermes

**Chosen:** Skill pack loaded via `external_dirs`.
**Rejected:** Forking Hermes and adding MDM skills into the bundled skills directory.

**Rationale.** Hermes is at v0.8 and evolving. A fork means carrying merge conflicts every time upstream changes. The `external_dirs` mechanism is documented as a first-class extension point — skills loaded this way are "read-only" to Hermes (it never writes back to the external directory), which means upgrades don't stomp the skill pack. Survives framework churn.

### agentskills.io standard compliance

**Chosen:** Follow the `agentskills.io` frontmatter format exactly.
**Rejected:** A Hermes-specific skill schema that uses proprietary extensions.

**Rationale.** The value of the playbooks is independent of the agent framework executing them. If a user wants to port this pack to another agent in a year, the standard-compliant frontmatter means the port is trivial — re-read the procedures, keep the Markdown. Hermes-specific metadata (tags, category) is namespaced under `metadata.hermes.*` so it is safely ignorable by other agents.

### Python over bash for the DQ audit

**Chosen:** One Python script using pandas.
**Rejected:** A bash pipeline using `awk` / `csvkit`.

**Rationale.** The audit produces structured output (completeness percentages, duplicate candidates with paired record IDs, emirate violations with severity). Bash can do it, but the resulting script would be harder to read and harder to extend. Pandas is in the Hermes sandbox by default — no install overhead for most users. Type hints and docstrings make the script self-documenting.

### Synthetic dataset rather than referencing any real data

**Chosen:** Fictitious Nexora Retail with five fictitious sub-brands.
**Rejected:** Using any real brand names; using public datasets like Open Corporates.

**Rationale.** A legal/IP boundary. This is a public repository. Real brand names would raise questions. Public data registries carry their own licensing complications. A fully synthetic dataset is safe, portable, and tunable — MDM pain points can be seeded deliberately to stress-test the skills.

### Six seed skills (not fewer, not more)

**Chosen:** duplicate-resolver, supplier-standardizer, location-validator, golden-record-composer, dq-audit, steward-briefing.
**Rejected:** A single "MDM steward" omnibus skill. Rejected also: a larger pack of 15+ skills covering every MDM edge case.

**Rationale.** Six is a catalog — it shows the pack is structured and reusable, not a demo. One omnibus skill violates the progressive-disclosure principle that skills are built on; Hermes only loads the skills it needs per task, and a monolith defeats that. Fifteen skills is bloat for a v0.1 release — each additional skill is maintenance debt without clear marginal value.

### PO Box, emirate, and country handled as separate concerns

**Chosen:** `mdm-location-validator` handles all three inside one skill.
**Rejected:** A separate skill per field type.

**Rationale.** The three are interdependent in Gulf addresses. A PO Box number is scoped to an emirate's postal system, a country normalization may change the authoritative emirate name. Splitting across skills would force the agent to invoke two or three skills sequentially on every address, producing a confusing call graph. One skill, multiple steps, clear output.

### Provenance map is non-negotiable in golden record composition

**Chosen:** Every field in the composed golden record carries a provenance entry (source record ID, survivorship rule, timestamp).
**Rejected:** A simplified "winning values only" output.

**Rationale.** Provenance is what separates a golden record from a guess. When a dispute arises ("why does this supplier's legal name say LLC when our ERP says Limited?"), the provenance map produces an immediate answer. Without it, the golden record loses its value the moment anyone questions it. The cost of carrying provenance is negligible; the cost of not having it is existential to the steward function.

## Patterns used

### Progressive disclosure for skills

Each skill's SKILL.md is the Level 1 document the agent loads when it needs to apply the skill. The frontmatter carries the minimal Level 0 metadata (name, description) that drives skill selection without loading the full body. Supporting files live alongside (scripts, references) and are loaded only when needed.

This is Hermes' pattern, not one invented here. Documented at <https://hermes-agent.nousresearch.com/docs/user-guide/features/skills>.

### Gate-based decisions in the duplicate resolver

The duplicate resolver runs four gates in order (deterministic ID, normalized name, address corroboration, status). Each gate can be definitive; the decision stops at the first gate that resolves the question. This is an efficiency and an explainability pattern — the output tells the steward exactly which gate produced the decision, not just the final answer.

### Source trust hierarchy for survivorship

The golden record composer uses an explicit source-system trust hierarchy (ERP > Procurement > CRM by default) rather than a time-based rule alone. This matches how stewardship works in practice — some systems are more authoritative than others regardless of recency.

## Gotchas to remember

- **CSV parsing requires `dtype=str`**. If pandas is allowed to auto-infer, TRN values with leading digits will be parsed as integers and lose the leading zero on countries that have it. Audit script explicitly forces strings.
- **Comma count on CSV rows matters.** One stray comma on the `Quick Import Traders` row in v0.1.0 initial data broke parsing (14 fields on an 12-field schema). Fixed pre-release, but a reminder that hand-authored CSVs need validation.
- **`keep_default_na=False, na_values=[""]`**. pandas by default treats `"NA"`, `"N/A"`, `"null"` as missing. For master data this is wrong — `"N/A"` in a notes field is a real value. The audit explicitly narrows missing-value detection to empty strings only.
- **Emirate "DXB" is a variant of Dubai — except when it isn't.** If geo-coordinates place the record in Abu Dhabi, the skill must trust the coordinates over the text. `mdm-location-validator` Gate 6 handles this; do not simplify it away.
- **TRN sharing does not always mean duplicate.** UAE branch offices of the same parent can share a TRN but operate as distinct procurement entities. The duplicate resolver's Gate 4 explicitly calls this out. Do not remove the escalation logic.
- **Hermes writes to `~/.hermes/skills/` only.** External skills loaded via `external_dirs` are read-only from Hermes' perspective. This is good (prevents accidental framework writes to the skill pack) but means agent-created skills during chat land in the Hermes home directory, not the pack. Users who want to promote an agent-created skill into the pack must copy it manually. Document this in future if it causes friction.

## Past bugs fixed (so they don't get reintroduced)

- **v0.1.0 pre-release:** `nexora_suppliers_dirty.csv` last row had 13 fields against a 12-field schema. Extra comma between trading name and country values. Fixed by removing the extra comma.

## Environment assumptions

- Python 3.10 or higher (uses `from __future__ import annotations` and match-free code).
- pandas (any recent 2.x release).
- Hermes Agent v0.8 or compatible.
- Linux, macOS, or WSL2 — Windows native not supported by Hermes.
- The running user has read access to the skill pack directory and write access to the output directory (`/tmp` by default).

## Things that are deliberately not done

- No async Python. The audit script is synchronous. If it grows to handle millions of rows, that decision gets revisited; for 18-row synthetic data and low-thousands real exports, sync is simpler.
- No database. The pack is file-based. If a persistent exception queue becomes a requirement, the right solution is a proper MDM platform integration, not a SQLite file in the pack.
- No custom installer. Users clone the repo and add a path to a config file. Anything more elaborate is over-engineering for this surface area.
