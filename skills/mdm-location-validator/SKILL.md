---
name: mdm-location-validator
description: Validates and standardizes address records for Gulf-region master data. Handles PO Box formatting, Emirate naming normalization, area-vs-building disambiguation, country naming, and geo-coordinate sanity checks. Built around the structural quirks of UAE and wider GCC addresses.
version: 1.0.0
metadata:
  hermes:
    tags: [mdm, data-quality, address, location, gulf, uae]
    category: mdm
---

# MDM Location Validator

## When to Use

Activate this skill when:

- The user presents a location or address record and asks for validation or standardization.
- The user mentions "PO Box", "emirate", "address cleanup", "location master", or names a Gulf country.
- A store, warehouse, or office location is being onboarded into the master data platform.
- Geo-coordinates need a sanity check against the stated emirate or city.

Do **not** use this skill for:

- International address validation outside the GCC (different postal conventions apply).
- Supplier legal name cleanup (use `/mdm-supplier-standardizer`).
- Duplicate detection (use `/mdm-duplicate-resolver`, which consumes this skill's output as an input signal).

## Procedure

### Step 1 — Country normalization

Canonical form for the GCC:

| Variants | Canonical |
|---|---|
| `UAE`, `U.A.E.`, `United Arab Emirates`, `Emirates` | `United Arab Emirates` (`UAE` as the ISO-adjacent short code) |
| `KSA`, `Saudi Arabia`, `Kingdom of Saudi Arabia` | `Saudi Arabia` |
| `Kuwait`, `State of Kuwait` | `Kuwait` |
| `Qatar`, `State of Qatar` | `Qatar` |
| `Bahrain`, `Kingdom of Bahrain` | `Bahrain` |
| `Oman`, `Sultanate of Oman` | `Oman` |

Decide once per dataset whether the canonical form is the long or short version, and apply it everywhere. Mixing both is the most common master data sin in GCC address fields.

### Step 2 — Emirate normalization (UAE only)

The seven emirates with common variants seen in master data:

| Variants found | Canonical |
|---|---|
| `Dubai`, `DXB`, `Dubayy`, `dubai` | `Dubai` |
| `Abu Dhabi`, `AUH`, `Abu-Dhabi`, `AbuDhabi` | `Abu Dhabi` |
| `Sharjah`, `SHJ`, `Shariqah` | `Sharjah` |
| `Ajman`, `AJM` | `Ajman` |
| `Ras Al Khaimah`, `RAK`, `Ras al-Khaimah`, `Ras-al-Khaimah` | `Ras Al Khaimah` |
| `Fujairah`, `FUJ`, `Al Fujairah` | `Fujairah` |
| `Umm Al Quwain`, `UAQ`, `Um Al Quwain` | `Umm Al Quwain` |

**Edge case: Al Ain.** Al Ain is a *city* within the Abu Dhabi emirate, not an emirate itself. If you see `emirate: Al Ain`, this is almost certainly a data entry error — the correct `emirate` is `Abu Dhabi` and `Al Ain` belongs in the `area` or `city` field.

### Step 3 — PO Box formatting

Canonical form: `PO Box <number>` with a single space, no punctuation.

Variants to normalize:

- `P.O. Box`, `P.O Box`, `POBox`, `POB`, `Post Box` → `PO Box`
- Strip any text content, retain only the box number.
- A PO Box is a positive integer. If the captured value is non-numeric (for example "Free Zone" or "N/A"), blank the field rather than keeping junk.

**Critical:** In the UAE, a PO Box number is associated with a specific emirate's postal system. PO Box `12345` in Dubai is a different physical location from PO Box `12345` in Sharjah. Never match records on PO Box alone — always require matching emirate.

### Step 4 — Address line discipline

Enforce a two-line structure where possible:

- `address_line_1`: building / unit / floor (the specific physical location).
- `address_line_2`: larger landmark (mall, tower, community).

Common mistake to fix: the whole address crammed into `address_line_2` with `address_line_1` empty. Re-split where the data allows, or flag for steward review where it doesn't.

### Step 5 — Area normalization

Many UAE retail locations sit in named communities rather than formal districts:

- `Jumeirah` vs `Jumeirah Beach Residence` vs `JBR` — keep distinct. JBR is a subset of Jumeirah but stores there are differentiated in reporting.
- `Downtown` vs `Downtown Dubai` vs `DIFC` — distinct areas.
- `Al Wasl`, `Al Barsha`, `Al Quoz` — preserve exact spelling including the `Al`.

If the `area` field is missing but can be inferred from the landmark mall or development name (e.g., `Dubai Mall` → `Downtown`, `Mall of the Emirates` → `Al Barsha`), propose the inferred value but do not auto-populate without steward approval.

### Step 6 — Geo-coordinate sanity check

If latitude and longitude are populated:

- **UAE bounding box:** latitude roughly 22.5 to 26.5, longitude roughly 51.0 to 56.5.
- If the coordinates fall outside this box, flag as a data quality defect.
- If the coordinates fall inside the box but do not match the stated emirate's approximate centre (±50 km), flag for human review.

Missing coordinates are a less severe defect but should still be logged — they block downstream spatial analytics.

### Step 7 — Output

```
INPUT:
  address_line_1: ""
  address_line_2: "Yas Mall Ground Floor"
  po_box: "127864"
  area: "Yas Island"
  emirate: "DXB"
  country: "UAE"
  latitude: 24.4886
  longitude: 54.6077

OUTPUT:
  address_line_1: "Yas Mall Ground Floor"
  address_line_2: ""
  po_box: "PO Box 127864"
  area: "Yas Island"
  emirate: "Abu Dhabi"
  country: "United Arab Emirates"
  latitude: 24.4886
  longitude: 54.6077

CHANGES:
  - address_line_1 / line_2: re-split (line_2 → line_1, line_1 empty)
  - po_box: formatted as "PO Box <number>"
  - emirate: corrected (DXB was incorrect — geo-coordinates confirm Abu Dhabi)
  - country: canonical form applied

FLAGS:
  - CRITICAL: emirate field said "DXB" but coordinates are in Abu Dhabi. Source record has a data entry error. Steward review required before persisting.
```

## Pitfalls

- **Geo-coordinates override stated emirate when they conflict.** In the example above, the record was wrong. Never trust the emirate text over verified coordinates.
- **"Dubai" is both an emirate and a city** — most records treat them as equivalent. That's fine for UAE, but the same convention breaks for Saudi Arabia (Riyadh is a city in Ar Riyad region, not the same thing).
- **JAFZA and other free zones have their own PO Box ranges** that don't follow the standard emirate numbering. Do not flag a JAFZA PO Box as invalid just because it's much larger than standard Dubai boxes.
- **Arabic address transliteration is not one-to-one.** "Al Khaleej Al Tijari" and "Al-Khalej Al-Tejari" are the same street. Do not force one canonical romanization; record what the trade license or utility bill shows.
- **Missing geo-coordinates are genuinely common.** Many smaller suppliers and older store records never captured lat/long. Flag but do not block.

## Verification

- Does the emirate match the postal code / PO Box range where verifiable?
- Do the coordinates (if present) fall within the named emirate's bounding box?
- Is the area field populated with a recognizable community, not a synonym of the emirate itself?
- Has the original input been preserved in the audit trail?
