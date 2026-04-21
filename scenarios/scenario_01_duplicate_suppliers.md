# Scenario 01 — Resolving duplicate suppliers across brands

**Setup.** A steward is reviewing yesterday's DQ audit output. Five supplier duplicate candidates were flagged — all matched on shared TRN. The steward picks the first one: `NX-SUP-00142` and `NX-SUP-00189`.

This scenario walks through how the agent uses the skill pack to resolve it end-to-end.

---

## The records

From `nexora_suppliers_dirty.csv`:

```
Record A: NX-SUP-00142
  legal_name:      Dubai Trading LLC
  trading_name:    Dubai Trading
  trn:             100123456700003
  country:         UAE
  po_box:          12345
  emirate:         Dubai
  phone:           +971-4-1234567
  email:           info@dubaitrading.ae
  brand_used_by:   Verdant Grocers
  created_date:    2019-03-15
  status:          Active

Record B: NX-SUP-00189
  legal_name:      DUBAI TRADING L.L.C.
  trading_name:    DUBAI TRADING
  trn:             100123456700003
  country:         United Arab Emirates
  po_box:          12345
  emirate:         DXB
  phone:           971412345678
  email:           sales@dubaitrading.ae
  brand_used_by:   Luxora Beauty
  created_date:    2021-07-02
  status:          Active
```

## Steward prompt

```
/mdm-duplicate-resolver

I have two supplier records from the Nexora master data. Are they the same
entity? Walk me through the decision.

[paste both records as above]
```

## Expected agent response (using `/mdm-duplicate-resolver`)

```
DECISION: MATCH
CONFIDENCE: High
REASONING:
  - Gate 1 (Deterministic identifier): Both records share TRN 100123456700003.
    TRN is entity-unique in the UAE system — this alone establishes a match
    at high confidence.
  - Gate 2 (Normalized name): "DUBAI TRADING L.L.C." and "Dubai Trading LLC"
    normalize to identical canonical forms (uppercase, suffix standardized).
    Confirms Gate 1.
  - Gate 3 (Address corroboration): Same PO Box (12345), same phone number
    after stripping punctuation. Multiple strong positive signals.
  - Gate 4 (Status): Both records are Active. No lifecycle concerns.

RECOMMENDED ACTION: merge

SURVIVING RECORD: NX-SUP-00142

RATIONALE FOR SURVIVAL:
  - Earlier created_date (2019 vs 2021) — has accumulated more downstream
    links.
  - Sourced from Verdant Grocers onboarding, which maps to the ERP system
    in this tenant's source trust hierarchy.

NEXT STEP: Invoke /mdm-golden-record-composer to produce the consolidated
golden record and provenance map.
```

## Follow-up prompt — compose the golden record

```
/mdm-golden-record-composer

Confirmed match. Compose the golden record with NX-SUP-00142 as the surviving
ID. Both records are Active.
```

## Expected agent response (using `/mdm-golden-record-composer`)

```
GOLDEN RECORD:
  surviving_record_id: NX-SUP-00142
  legal_name:       "Dubai Trading LLC"       [from NX-SUP-00142, rule: source-trust-ERP]
  trading_name:     "Dubai Trading"           [from NX-SUP-00142, rule: source-trust-ERP]
  trn:              "100123456700003"         [matches across both sources]
  po_box:           "PO Box 12345"            [formatted via mdm-location-validator]
  emirate:          "Dubai"                   [NX-SUP-00142 — NX-SUP-00189 had "DXB" variant]
  country:          "United Arab Emirates"    [from NX-SUP-00189, applying canonical form]
  phone_primary:    "+971-4-1234567"          [from NX-SUP-00142, rule: source-trust-ERP]
  phone_secondary:  "+971-4-1234567"          [from NX-SUP-00189 after normalization — identical]
  email_primary:    "info@dubaitrading.ae"    [from NX-SUP-00142]
  email_secondary:  "sales@dubaitrading.ae"   [from NX-SUP-00189, retained as multi-valued]
  brand_used_by:    [Verdant Grocers, Luxora Beauty]  [union across sources]
  status:           "Active"                  [no restrictive status to propagate]
  created_date:     2019-03-15                [earliest non-null, from NX-SUP-00142]
  last_modified:    2021-07-02                [most recent, from NX-SUP-00189]

CROSS-REFERENCES:
  - NX-SUP-00142 (surviving)
  - NX-SUP-00189 (merged, retired)

NOTES:
  - Phone numbers from both sources resolve to the same E.164 value after
    normalization. Secondary phone line retained but deduplicated on output.
  - Email addresses are genuinely distinct (info@ vs sales@) — multi-valued
    retention.
  - Cross-brand relationship retained. Verdant and Luxora both transact
    with this supplier.
```

## What this scenario demonstrates

1. **The skill pack's skills chain cleanly** — one decision flows into the next without manual glue.
2. **Cross-brand duplicates are resolved without losing the brand relationship** — the golden record remembers both Verdant and Luxora as consumers.
3. **Provenance is preserved per field** — for audit, dispute, and future re-derivation of the golden record.
4. **Format inconsistency is fixed by a dedicated skill**, not ad-hoc in the composer — each skill has one job.

## What a steward would do next

- Review the proposed golden record in the MDM platform's review UI.
- Approve or amend.
- Trigger the downstream cross-reference update so that any transaction previously pointing to `NX-SUP-00189` now resolves to `NX-SUP-00142`.

## If this resolution pattern repeats

After the steward confirms this class of resolution a few times, Hermes' skill-creation loop will offer to capture "cross-brand same-TRN supplier merge" as a derived skill — so the next similar case can be handled with less back-and-forth. That is the learning loop in action.
