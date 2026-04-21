---
name: mdm-supplier-standardizer
description: Normalizes supplier and business partner names for consistent master data. Handles legal entity suffix standardization (LLC, L.L.C., Limited, Ltd, FZE, FZCO), case normalization, trading name vs legal name separation, and common abbreviation expansion. Returns a standardized record with a log of changes applied.
version: 1.0.0
metadata:
  hermes:
    tags: [mdm, data-quality, standardization, suppliers]
    category: mdm
---

# MDM Supplier Standardizer

## When to Use

Activate this skill when:

- The user asks to "clean up", "standardize", "normalize", or "fix formatting" on a supplier record.
- The user pastes a single supplier record or a batch and asks for the canonical version.
- A record is being loaded into the master data platform for the first time and must conform to naming standards.
- The `mdm-duplicate-resolver` skill has identified two records as a match and the surviving record needs its name cleaned up before retention.

Do **not** use this skill for:

- Matching two records against each other (use `/mdm-duplicate-resolver`).
- Validating addresses (use `/mdm-location-validator`).
- Deciding which source system's value wins in a golden record (use `/mdm-golden-record-composer`).

## Procedure

Apply the following transformations in order. Track every change for the output log.

### Step 1 — Whitespace cleanup

- Strip leading and trailing whitespace.
- Collapse any sequence of multiple spaces into a single space.
- Remove non-printing characters (tabs, non-breaking spaces, zero-width spaces).

### Step 2 — Case normalization

- Target **Title Case** for the canonical `legal_name`.
- Preserve all-upper acronyms: `LLC`, `FZE`, `FZCO`, `DMCC`, `UAE`, `USA`, `UK`, `DIFC`.
- Preserve brand tokens that are canonically lower-case (rare in suppliers; verify before applying).
- Example: `DUBAI TRADING L.L.C.` → `Dubai Trading LLC`.

### Step 3 — Legal entity suffix standardization

Apply the canonical form table:

| Variants found | Canonical form |
|---|---|
| `L.L.C.`, `LLC`, `L.L.C`, `llc`, `Limited Liability Company` | `LLC` |
| `Ltd.`, `Ltd`, `LTD`, `Limited` | `Ltd` |
| `FZE`, `F.Z.E.`, `Free Zone Establishment` | `FZE` |
| `FZCO`, `Free Zone Company`, `FZ-LLC`, `FZ LLC` | `FZCO` |
| `DMCC`, `D.M.C.C.` | `DMCC` |
| `Inc.`, `Inc`, `INC`, `Incorporated` | `Inc` |
| `Corp.`, `Corp`, `Corporation` | `Corp` |
| `Co.`, `Co`, `Company` (at end of name, in legal context) | `Company` |
| `&` (in legal name) | `and` |

Place the canonical suffix at the **end** of the legal name, separated by a single space. Never embed it mid-name.

### Step 4 — Trading name extraction

If the `trading_name` field is empty but the legal name contains a DBA pattern (`"X trading as Y"`, `"X dba Y"`, `"X t/a Y"`), split:

- `legal_name` = the formal entity on the left.
- `trading_name` = the DBA name on the right.

If the legal name and trading name are identical after standardization, leave the trading name populated — it is still meaningful metadata that this entity has no separate trading name.

### Step 5 — Abbreviation expansion (optional, policy-driven)

If the governance policy is "expand abbreviations in legal names":

- `Co` → `Company` (only when standalone, not in `Co-op`).
- `Corp` → `Corporation`.
- `Intl` → `International`.

If the policy is "preserve abbreviations as entered on the trade license", skip this step. The default in this skill pack is **preserve**, since trade license naming is legally authoritative.

### Step 6 — Output

Return the standardized record plus a change log:

```
INPUT:
  legal_name: "  DUBAI TRADING L.L.C.  "
  trading_name: "DUBAI TRADING"

OUTPUT:
  legal_name: "Dubai Trading LLC"
  trading_name: "Dubai Trading"

CHANGES:
  - legal_name: trimmed whitespace (leading + trailing)
  - legal_name: case normalized (UPPER → Title Case), acronyms preserved
  - legal_name: suffix standardized (L.L.C. → LLC)
  - trading_name: case normalized (UPPER → Title Case)
```

## Pitfalls

- **Do not standardize the trading name against the legal name's suffix rules.** Trading names are marketing-driven and often intentionally omit suffixes. "Dubai Trading" is a valid trading name even when the legal entity is "Dubai Trading LLC".
- **Arabic-transliterated names are not safe to "clean up".** Do not alter spacing or hyphenation in names like "Al-Futtaim" or "Bin Hendi". Preserve exactly as entered unless the user explicitly authorizes romanization changes.
- **Case normalization breaks brand styling.** Some luxury or fashion suppliers have intentional casing ("eBay", "iHerb", "YOOX"). Before applying Title Case, check if the supplier has a registered brand style. If unsure, flag for steward review rather than force.
- **Suffix position matters legally.** UAE trade licenses place the suffix at the end. Placing it mid-name ("Dubai LLC Trading") makes the record non-compliant with trade license reconciliation processes. Always end-position.
- **Abbreviation expansion can cause false duplicates downstream.** If one record has "Trading Co" expanded to "Trading Company" and another record remains "Trading Co", they'll no longer match on normalized name. Apply expansion policy consistently across the entire dataset or not at all.

## Verification

After standardizing, verify:

- Does the output round-trip against the trade license copy (if available)?
- Does the normalized form match the entity's own self-presentation (website, invoice header)?
- Has every change been logged with a reason a steward can audit?
- Has the original input been preserved in the source-record audit trail before overwriting?

If any answer is "no", do not persist the change. Return it as a proposed change for human approval.
