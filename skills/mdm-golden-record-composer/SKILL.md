---
name: mdm-golden-record-composer
description: Assembles a golden record from multiple source system representations of the same entity. Applies field-level survivorship rules — most recent wins, source system trust hierarchy, completeness rules, and consolidation rules for multi-valued fields. Returns a single consolidated record with full provenance for every field.
version: 1.0.0
metadata:
  hermes:
    tags: [mdm, golden-record, survivorship, consolidation]
    category: mdm
---

# MDM Golden Record Composer

## When to Use

Activate this skill when:

- The `mdm-duplicate-resolver` skill has confirmed a MATCH between two or more records and a single consolidated record must be produced.
- The user asks about "survivorship", "golden record", "consolidation", "winning values", "cross-reference", or "source of truth" for a specific entity.
- A new record is arriving from a source system and must be reconciled against an existing golden record.

Do **not** use this skill for:

- Deciding whether two records are duplicates (use `/mdm-duplicate-resolver` first).
- Cleaning up a single record's formatting (use `/mdm-supplier-standardizer` or `/mdm-location-validator`).
- Producing a merged record without tracking which source contributed which field (provenance is non-negotiable).

## Core principle

A golden record is a **field-by-field assembly**, not a whole-record pick. For each field, decide which source record wins and record why. The surviving record_id is a convention — the winning *values* may come from any of the merged records.

## Procedure

### Step 1 — Gather source records

Enumerate all records in the match cluster. Capture for each:

- `record_id`
- `source_system` (which system of record the data came from)
- `created_date` and `last_modified_date`
- `completeness_score` — the count of populated non-key fields
- `status` (Active, Inactive, Pending Review)

### Step 2 — Decide the surviving record_id

The surviving record_id is the one all downstream cross-references will point to. Choose by:

1. **Prefer Active over Inactive** — an Inactive record ID persisting as the golden record creates downstream confusion.
2. **Prefer the most recent `last_modified_date`** — assumes active stewardship.
3. **Tie-break on oldest `created_date`** — the record that has been around longest has accumulated the most downstream links.

Log which rule broke the tie.

### Step 3 — Apply field-level survivorship rules

Go field by field. Different field types use different rules:

#### Reference identifiers (TRN, CR, VAT, DUNS)

- **Rule:** Most recent non-null value wins.
- **Rationale:** These are externally authoritative. If a later record has a value and an earlier one doesn't, the later one has been verified against the external authority more recently.
- **Exception:** If two records have *different* non-null values for the same reference ID, the MATCH decision was wrong. Escalate back to `mdm-duplicate-resolver`.

#### Legal name, trading name

- **Rule:** Source system trust hierarchy wins. Default hierarchy (override per-tenant):
  1. ERP system (trade license reconciled)
  2. Procurement system
  3. Marketing / CRM system
- **Rationale:** The legal name on a trade license is legally authoritative. Marketing systems hold marketing variants.

#### Address fields

- **Rule:** Most complete record wins as a block. Do **not** mix address fields from different sources — a partial merge produces a nonsense address.
- **Rationale:** `address_line_1` from source A combined with `emirate` from source B can produce a fictitious location.
- Apply `/mdm-location-validator` to the winning address block before persisting.

#### Contact fields (phone, email)

- **Rule:** Retain all distinct values as a multi-valued collection with source provenance.
- **Rationale:** An entity can legitimately have multiple phone numbers and emails. Collapsing to one loses signal.
- Mark one as `primary` using the source trust hierarchy.

#### Status

- **Rule:** Most restrictive status wins.
- `Blocked` beats `Inactive` beats `Active`.
- **Rationale:** If any source system has flagged the entity as blocked, the consolidated record must preserve that signal regardless of what other systems say.

#### Dates (created, first_transaction, opening_date)

- **Rule:** Earliest non-null value wins.
- **Rationale:** The entity's true age is the earliest time any system recognized it.

#### Last-modified dates

- **Rule:** Most recent value wins (this is the golden record's own last-modified timestamp).

#### Brand-used-by or consumption relationships

- **Rule:** Union across all source records, deduplicated.
- **Rationale:** If Verdant Grocers and Luxora Beauty both used the same supplier, the golden record reflects both relationships.

### Step 4 — Generate the provenance map

For every field in the output record, record:

- The source record_id that contributed the winning value.
- The survivorship rule that selected it.
- The timestamp of the source record's last modification.

The provenance map is persisted alongside the golden record — never discarded. Audit, governance reviews, and dispute resolution all depend on it.

### Step 5 — Output

```
GOLDEN RECORD:
  surviving_record_id: NX-SUP-00142
  legal_name: "Dubai Trading LLC"          [from NX-SUP-00142, rule: source-trust-ERP]
  trading_name: "Dubai Trading"            [from NX-SUP-00142, rule: source-trust-ERP]
  trn: "100123456700003"                   [from NX-SUP-00189, rule: most-recent-non-null]
  po_box: "PO Box 12345"                   [from NX-SUP-00142, rule: completeness]
  emirate: "Dubai"                         [from NX-SUP-00142, rule: validated-by-location-validator]
  phone_primary: "+971-4-1234567"          [from NX-SUP-00142, rule: source-trust-ERP]
  phone_secondary: "+971-4-9876543"        [from NX-SUP-00189, rule: multi-valued-retention]
  email_primary: "info@dubaitrading.ae"    [from NX-SUP-00142]
  email_secondary: "sales@dubaitrading.ae" [from NX-SUP-00189]
  brand_used_by: [Verdant Grocers, Luxora Beauty]  [union across sources]
  status: "Active"                         [from NX-SUP-00142, rule: most-restrictive]
  created_date: 2019-03-15                 [from NX-SUP-00142, rule: earliest-non-null]
  last_modified_date: 2021-07-02           [from NX-SUP-00189, rule: most-recent]

CROSS-REFERENCES:
  - NX-SUP-00142 (surviving, ERP source)
  - NX-SUP-00189 (merged, Procurement source, retired)

WARNINGS:
  - Multi-valued phone and email fields retained; review whether business rules require primary-only.
```

## Pitfalls

- **Never silently drop data during merge.** Losing the secondary phone number without logging it means the next steward has no record that it was ever captured. Merge is additive to the audit trail, even when it's consolidating to the golden record.
- **Multi-valued fields must have a persistence model.** If the target MDM platform's schema has only one `phone` column, multi-valued retention requires either a child table or a delimited string. Decide the pattern once per tenant — don't improvise per merge.
- **Source trust hierarchy is tenant-specific and versioned.** What was the authoritative source two years ago may not be today (system migration, acquisitions). Record the version of the hierarchy used at the time the golden record was composed.
- **Merging Active + Blocked must preserve the Blocked status** *and* surface the reason. A consolidated record that quietly becomes Active because two of three sources said Active is a compliance failure waiting to happen.
- **Brand-used-by union can mask stale relationships.** If Luxora Beauty last transacted with this supplier three years ago and has since terminated the relationship, the union retains Luxora in the list. Downstream reporting should filter by active relationships, not infer active status from the union.

## Verification

- Does every field in the output record have a provenance entry pointing to a source record_id and a survivorship rule?
- Is the surviving_record_id `Active` (unless all inputs were inactive)?
- Have conflicting values been surfaced to a steward rather than silently resolved by a rule?
- Has the cross-reference map been persisted so that pointers to retired record_ids can still resolve to the golden record?

If any answer is "no", the golden record is not ready to persist.
