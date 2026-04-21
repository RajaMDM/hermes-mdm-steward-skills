---
name: mdm-dq-audit
description: Runs a scheduled data quality audit against master data files or a Core MDM export. Produces a summary with completeness percentages, duplicate candidates, format violations, and multi-brand overlap detection. Designed to be invoked nightly via Hermes cron and delivered to a steward via the configured messaging gateway.
version: 1.0.0
metadata:
  hermes:
    tags: [mdm, data-quality, audit, scheduled, cron]
    category: mdm
---

# MDM DQ Audit

## When to Use

Activate this skill when:

- The user asks to "run a DQ audit", "run a data quality check", "audit the master data", or "profile the data".
- A scheduled cron job triggers the audit (typically nightly or weekly).
- The user asks for a summary of master data health before a steward meeting or a brand onboarding cutover.

Do **not** use this skill for:

- Resolving individual duplicate records (use `/mdm-duplicate-resolver`).
- Fixing formatting issues in a specific record (use `/mdm-supplier-standardizer` or `/mdm-location-validator`).
- Long-running profiling of very large datasets (this skill is designed for summaries under a few thousand records — scale up via the underlying script, not this skill).

## Procedure

### Step 1 — Locate input data

The audit script expects three CSV files:

- `nexora_suppliers_dirty.csv`
- `nexora_products_dirty.csv`
- `nexora_locations_dirty.csv`

By default these live in the skill pack's `datasets/` directory. For real deployments, point the script at exported CSV files from your Core MDM platform.

If the user has not specified a path, default to the skill pack's bundled synthetic dataset.

### Step 2 — Run the audit script

Invoke the helper script via Hermes' `execute_code` or `terminal` tool:

```bash
python scripts/run_dq_audit.py \
  --suppliers /path/to/nexora_suppliers_dirty.csv \
  --products  /path/to/nexora_products_dirty.csv \
  --locations /path/to/nexora_locations_dirty.csv \
  --output    /tmp/dq_audit_summary.md
```

The script requires `pandas` (installed in the Hermes sandbox by default). If missing, prompt to install via the sandbox's package manager before proceeding.

### Step 3 — Summarize findings

Read the output markdown file and produce a concise summary for delivery:

- Total records per entity type.
- Completeness percentage per critical field.
- Count of duplicate candidates found (based on deterministic IDs).
- Count of format violations (emirate variants, country variants, PO Box issues).
- Count of cross-brand supplier relationships (information, not defect).
- A ranked list of the top three data quality issues by severity.

### Step 4 — Deliver

If invoked via cron with a gateway target (email, Telegram, Slack), deliver the summary via that gateway. If invoked interactively, return the summary inline and offer to save to a file.

Keep the delivered summary under ~500 words. Full detail lives in the generated markdown file — the delivery is a glance, not a deep-dive.

### Example output

```
MDM DAILY DQ AUDIT — 2026-04-21

Suppliers:  18 records | 78% TRN populated | 3 duplicate candidates
Products:   18 records | 88% barcode populated | 6 near-duplicates (same barcode)
Locations:  18 records | 72% geo-coordinates populated | 2 emirate variant violations

Top 3 issues:
  1. CRITICAL: 2 supplier pairs share TRN — confirmed same entity, awaiting merge
  2. HIGH:     Emirate field uses "DXB" on 3 records — should be "Dubai"
  3. MEDIUM:   6 product pairs share barcode across Verdant + Luxora sub-brands

Action: 5 records require steward review. Full details in
/tmp/dq_audit_summary.md
```

## Pitfalls

- **Do not auto-resolve duplicates based on the audit alone.** The audit surfaces candidates; the `/mdm-duplicate-resolver` skill makes the decision. Keep the separation.
- **Completeness percentage can be misleading.** A 95% populated field can still fail the business — if the missing 5% is on the most-transacted suppliers. Always report count alongside percentage.
- **Format violations are not the same as duplicates.** Three records with "DXB" in the emirate column are three format issues, not three duplicates. Report them separately.
- **Cross-brand overlap is information, not a defect.** Many multi-brand retailers legitimately share suppliers. The audit should report overlap without flagging it as a problem unless a tenant-specific rule says otherwise.
- **Do not send the full detail file via messaging gateways.** Telegram, Slack, and email all have length limits. Summarize in the message, attach or link the full file.

## Verification

- Does the summary identify the top issues ranked by business impact, not just by count?
- Is the script runnable with no arguments (should fall back to bundled synthetic data)?
- Are all percentages reported alongside absolute counts?
- If delivery is configured, was the summary delivered and the delivery receipt logged?
