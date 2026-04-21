---
name: mdm-duplicate-resolver
description: Decides whether two master data records represent the same real-world entity. Handles supplier, customer, and business-partner duplicate detection using deterministic identifiers, name standardization, and address proximity. Returns a match decision with confidence level and reasoning.
version: 1.0.0
metadata:
  hermes:
    tags: [mdm, data-quality, entity-resolution, match-merge]
    category: mdm
---

# MDM Duplicate Resolver

## When to Use

Activate this skill when:

- The user presents two or more records and asks whether they are the same entity.
- The user mentions "duplicate", "match", "merge", "same supplier", "same customer", "dedupe", or "entity resolution".
- The user pastes master data rows and asks for a survivorship decision.
- A scheduled data quality audit flags a potential duplicate pair.

Do **not** use this skill for:

- Deciding golden-record field survivorship (use `/mdm-golden-record-composer`).
- Standardizing a single record's formatting (use `/mdm-supplier-standardizer` or `/mdm-location-validator`).
- Recommending whether to block a new record from being created.

## Procedure

Work through the following gates in order. Stop at the first gate that gives a definitive answer.

### Gate 1 — Deterministic identifier match

Check for shared **unique business identifiers** that should never collide across distinct entities:

- **TRN** (Tax Registration Number — UAE): 15 digits, entity-unique.
- **CR / Trade License Number**: jurisdiction-specific, entity-unique.
- **VAT registration number**: region-specific.
- **DUNS number**: globally unique where present.
- **GTIN / EAN-13 barcode**: product-only, globally unique per SKU.

**Decision:**

- Same TRN or CR → **MATCH** (confidence: high). Proceed to survivorship.
- Same DUNS or VAT → **MATCH** (confidence: high).
- Different deterministic IDs where both are populated → **NO MATCH** (confidence: high). Stop.
- Both missing → continue to Gate 2.

### Gate 2 — Normalized name comparison

Apply normalization before comparing names:

1. Upper-case both names.
2. Strip leading/trailing whitespace and collapse multiple spaces.
3. Remove punctuation (`.` `,` `-` `&` `(` `)`).
4. Normalize legal entity suffixes: `LLC` = `L.L.C.` = `LIMITED LIABILITY COMPANY`; `LTD` = `LIMITED`; `FZE` = `FREE ZONE ESTABLISHMENT`; `FZCO` = `FREE ZONE COMPANY`.
5. Expand common abbreviations: `CO` → `COMPANY`, `CORP` → `CORPORATION`, `&` → `AND`.
6. Remove stop-word suffixes at end: `COMPANY`, `CORPORATION`, `GROUP`, `HOLDINGS`.

**Decision:**

- Normalized names identical → **LIKELY MATCH** (confidence: medium). Continue to Gate 3 for confirmation.
- Normalized names differ by a single token → **POSSIBLE MATCH** (confidence: low). Continue to Gate 3.
- Normalized names substantially different → **NO MATCH** (confidence: high). Stop.

### Gate 3 — Address and contact corroboration

When names suggest a match, confirm with secondary signals:

- **Same PO Box** (after normalizing "PO Box" / "P.O. Box" / "POBox" to a numeric box number): strong positive signal.
- **Same phone number** (after stripping all non-digit characters): strong positive signal.
- **Same email domain**: moderate positive signal.
- **Same emirate/city** (after normalizing "Dubai" = "DXB" = "Dubayy"): weak positive signal; do not match on this alone.

**Decision:**

- Gate 2 likely match + any strong positive in Gate 3 → **MATCH** (confidence: high).
- Gate 2 likely match + only weak positives in Gate 3 → **HUMAN REVIEW REQUIRED** (confidence: low). Do not auto-merge.
- Gate 2 possible match + multiple strong positives in Gate 3 → **LIKELY MATCH** (confidence: medium). Flag for steward review.

### Gate 4 — Status and lifecycle check

Before finalizing any MATCH decision, check status fields:

- If one record is `Inactive` or `Blocked` and the other is `Active`, flag the decision. Merging may reactivate a blocked entity.
- If one is `Pending Review`, surface the reason before merging.

## Output format

Return a structured decision:

```
DECISION: MATCH | NO MATCH | HUMAN REVIEW REQUIRED
CONFIDENCE: High | Medium | Low
REASONING:
  - Gate 1: [result]
  - Gate 2: [result]
  - Gate 3: [result]
  - Gate 4: [result]
RECOMMENDED ACTION: [merge / keep separate / escalate to data steward]
SURVIVING RECORD: [if MATCH, which supplier_id should be retained]
```

## Pitfalls

- **TRN appearing in multiple records does not automatically mean duplicate.** UAE branch offices of the same parent can legitimately share a TRN while operating as distinct entities for procurement. If the records have different addresses and different phone numbers despite same TRN, escalate to human review rather than auto-merging.
- **Name-only matching is unreliable across languages.** Arabic-transliterated names have multiple valid English spellings ("Al-Futtaim" vs "Al Futtaim" vs "Alfuttaim"). Rely on deterministic identifiers where available.
- **Trading name can legitimately differ from legal name.** "Dubai Trading" and "Dubai Trading LLC" may be the same entity operating under a DBA — treat trading-name vs legal-name mismatches as expected, not as red flags.
- **Cross-brand duplicates are the common case, not the edge case.** When the same supplier sells to multiple Nexora brands, each brand often onboards the supplier separately. This is the single largest source of duplicate records in multi-brand retail MDM.
- **Never silently merge Active + Inactive records.** Always escalate. An inactive record may have been blocked for a reason (compliance, dispute, fraud) that isn't in the master data itself.

## Verification

After making a decision, verify by asking:

- Would a data steward with 5 years of MDM experience agree with this decision based on the same evidence?
- Have I stated which gate produced the decision and what signal was decisive?
- If the decision is MATCH, have I named which record should survive and why?
- If the decision is HUMAN REVIEW, have I stated specifically what additional information would resolve the ambiguity?

If any answer is "no", revise the decision before returning it.
