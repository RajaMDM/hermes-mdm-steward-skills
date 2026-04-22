---
name: mdm-location-validator
description: Validates and standardizes address records for GCC master data — UAE, Saudi Arabia, Kuwait, Qatar, Bahrain, and Oman. Handles per-country administrative-level naming (emirate / region / governorate), PO Box vs postal-code conventions, country naming, and geo-coordinate sanity checks against bounded country boxes.
version: 2.0.0
metadata:
  hermes:
    tags: [mdm, data-quality, address, location, gcc, uae, ksa, kuwait, qatar, bahrain, oman]
    category: mdm
---

# MDM Location Validator

## When to Use

Activate this skill when:

- The user presents a location or address record and asks for validation or standardization.
- The user mentions "PO Box", "emirate", "region", "governorate", "address cleanup", "location master", or names a GCC country.
- A store, warehouse, or office location is being onboarded into the master data platform.
- Geo-coordinates need a sanity check against the stated administrative level.

Do **not** use this skill for:

- Address validation outside the GCC (different postal conventions and reference tables apply).
- Supplier legal name cleanup (use `/mdm-supplier-standardizer`).
- Duplicate detection (use `/mdm-duplicate-resolver`, which consumes this skill's output as an input signal).

## Core principle

Every GCC country has its own administrative-level naming and postal conventions. **Identify the country first, then apply that country's specific rules.** Do not carry UAE assumptions (emirate, PO Box) into Saudi Arabia (region, 5-digit postal code) or Qatar (zone + street + building, no postal code).

## Procedure

### Step 1 — Country normalization

Canonical form for GCC countries:

| Variants found | Canonical |
|---|---|
| `UAE`, `U.A.E.`, `United Arab Emirates`, `Emirates` | `United Arab Emirates` |
| `KSA`, `Saudi Arabia`, `Kingdom of Saudi Arabia`, `Saudi`, `K.S.A.` | `Saudi Arabia` |
| `Kuwait`, `State of Kuwait`, `KWT` | `Kuwait` |
| `Qatar`, `State of Qatar`, `QAT` | `Qatar` |
| `Bahrain`, `Kingdom of Bahrain`, `BHR` | `Bahrain` |
| `Oman`, `Sultanate of Oman`, `OMN` | `Oman` |

Decide once per dataset whether the canonical form is the long or short version, and apply it everywhere. Mixing both is the most common master data sin in GCC address fields. **This skill recommends the long form** (e.g., `United Arab Emirates`, `Kingdom of Saudi Arabia`) because long forms are unambiguous across language variants.

Once country is established, route to the country-specific block below.

### Step 2A — United Arab Emirates

**Administrative level:** Emirate (seven).

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

**Postal convention:** PO Box. Format as `PO Box <number>` (canonical, see Step 3). UAE does not use street-level postal codes.

### Step 2B — Saudi Arabia

**Administrative level:** Region (13). Regions are further divided into governorates and cities.

| Variants found | Canonical | First postcode digit |
|---|---|---|
| `Riyadh`, `Ar Riyad`, `Al Riyadh` | `Riyadh` | 1 |
| `Makkah`, `Mecca`, `Makkah al Mukarramah`, `Holy Mecca` | `Makkah` | 2 |
| `Madinah`, `Medina`, `Al Madinah al Munawwarah` | `Madinah` | 4 |
| `Eastern Province`, `Ash Sharqiyah`, `Eastern Region` | `Eastern Province` | 3 |
| `Qassim`, `Al Qassim`, `Al-Qassim` | `Qassim` | 5 |
| `Hail`, `Hail Region`, `Ha'il` | `Hail` | 5 |
| `Tabuk`, `Tabouk` | `Tabuk` | 7 |
| `Asir`, `Aseer`, `Asir Region` | `Asir` | 6 |
| `Jazan`, `Jizan` | `Jazan` | 8 |
| `Najran` | `Najran` | 6 |
| `Al Bahah`, `Al-Baha`, `Al Baha` | `Al Bahah` | 6 |
| `Northern Borders`, `Al Hudud ash Shamaliyah` | `Northern Borders` | 7 |
| `Al Jawf`, `Al-Jouf`, `Al Jowf` | `Al Jawf` | 7 |

**Critical distinction:** In Saudi Arabia, **Riyadh is a city within the Riyadh region, not the same thing**. If the source column expects a region, do not accept "Riyadh city" — distinguish `region: Riyadh` from `city: Riyadh`. Same applies to Makkah (city in Makkah region), Madinah (city in Madinah region), and Dammam (city in Eastern Province).

**Postal convention:** 5-digit numeric postal code via Saudi Post (SPL). Format: `XXXXX`. The first digit encodes the region (see table above). An extended 9-digit format (`XXXXX-YYYY`) identifies specific buildings via the National Address system — preserve the extended form if present. PO Boxes also exist but are secondary to the postal code for building-level delivery.

### Step 2C — Kuwait

**Administrative level:** Governorate (six).

| Variants found | Canonical |
|---|---|
| `Al Asimah`, `Capital`, `Kuwait City Governorate`, `Al-Asimah` | `Al Asimah` |
| `Hawalli`, `Hawally` | `Hawalli` |
| `Farwaniyah`, `Al Farwaniyah`, `Al-Farwaniyah` | `Al Farwaniyah` |
| `Mubarak Al Kabeer`, `Mubarak Al-Kabeer` | `Mubarak Al Kabeer` |
| `Ahmadi`, `Al Ahmadi`, `Al-Ahmadi` | `Al Ahmadi` |
| `Jahra`, `Al Jahra`, `Al-Jahra` | `Al Jahra` |

**Postal convention:** 5-digit numeric postal code. The first two digits encode the governorate. PO Boxes are widely used — each range of 100 boxes within an area has its own code (e.g., PO Boxes 1–100 in Salmiya share one postal code).

**Address structure:** Blocks, streets, buildings (not street numbers in the Western sense). A complete Kuwait address is typically: Block, Street, Building, Area, Governorate, Postal Code.

### Step 2D — Qatar

**Administrative level:** Municipality (eight).

| Variants found | Canonical |
|---|---|
| `Doha`, `Ad Dawhah`, `Ad-Dawhah` | `Doha` |
| `Al Rayyan`, `Al-Rayyan`, `Ar Rayyan` | `Al Rayyan` |
| `Al Wakrah`, `Al-Wakrah` | `Al Wakrah` |
| `Al Khor`, `Al-Khor`, `Al Khawr` | `Al Khor` |
| `Al Daayen`, `Al-Daayen`, `Ad Dayin` | `Al Daayen` |
| `Umm Salal`, `Umm-Salal` | `Umm Salal` |
| `Al Shamal`, `Al-Shamal`, `Ash Shamal`, `Madinat ash Shamal` | `Al Shamal` |
| `Al Shahaniya`, `Al-Shahaniya`, `Ash Shahaniyah` | `Al Shahaniya` |

**Postal convention:** Qatar **does not use postal codes** in the civilian addressing system. Addresses use **zone number + street number + building number** — three numeric identifiers. Example: `Zone 63, Street 250, Building 15`. Store these as separate fields where the schema supports it; if collapsed into a single text field, preserve the three-number structure.

**PO Box:** Qatar Post supports PO Boxes; format as `PO Box <number>` (canonical). PO Boxes are commonly used for business addresses.

### Step 2E — Bahrain

**Administrative level:** Governorate (four).

| Variants found | Canonical |
|---|---|
| `Capital`, `Al Asimah`, `Al-Asimah`, `Capital Governorate` | `Capital` |
| `Muharraq`, `Al Muharraq`, `Al-Muharraq` | `Muharraq` |
| `Northern`, `Al Shamaliyah`, `Ash Shamaliyah`, `Northern Governorate` | `Northern` |
| `Southern`, `Al Janubiyah`, `Al-Janubiyah`, `Southern Governorate` | `Southern` |

**Postal convention:** 3- or 4-digit numeric postal code. Addresses use **block number + road number + building number** — similar to Kuwait's structure. PO Boxes exist and are commonly used for business addresses.

**Historic note:** Bahrain previously had five governorates (including `Central`); `Central` was merged and no longer exists. If you see `Central` on a record, flag it — the record is either historic or incorrect.

### Step 2F — Oman

**Administrative level:** Governorate (11, locally called "muhafazah").

| Variants found | Canonical |
|---|---|
| `Muscat`, `Masqat`, `Masqaţ` | `Muscat` |
| `Dhofar`, `Zufar`, `Dhofar Governorate` | `Dhofar` |
| `Musandam`, `Musandam Governorate` | `Musandam` |
| `Al Buraymi`, `Al-Buraymi`, `Buraimi` | `Al Buraymi` |
| `Ad Dakhiliyah`, `Al Dakhiliyah`, `Al-Dakhiliyah`, `Interior` | `Ad Dakhiliyah` |
| `Al Batinah North`, `North Al Batinah`, `Shamal al Batinah` | `Al Batinah North` |
| `Al Batinah South`, `South Al Batinah`, `Janub al Batinah` | `Al Batinah South` |
| `Ash Sharqiyah North`, `North Ash Sharqiyah` | `Ash Sharqiyah North` |
| `Ash Sharqiyah South`, `South Ash Sharqiyah` | `Ash Sharqiyah South` |
| `Adh Dhahirah`, `Ad Dhahirah`, `Al-Dhahirah`, `Az Zahirah` | `Adh Dhahirah` |
| `Al Wusta`, `Al-Wusta`, `Wusta`, `Central` | `Al Wusta` |

**Postal convention:** 3-digit numeric postal code via Oman Post. PO Boxes are commonly used and include a separate PO Box number alongside the postal code of the branch.

### Step 3 — PO Box formatting (UAE, Qatar, Bahrain, Oman, and legacy KSA records)

For countries that use PO Box primarily (UAE) or as a common alternative (Qatar, Bahrain, Oman, Kuwait), apply the canonical form: `PO Box <number>` with a single space, no punctuation.

Variants to normalize:

- `P.O. Box`, `P.O Box`, `POBox`, `POB`, `Post Box` → `PO Box`
- Strip any text content, retain only the box number.
- A PO Box is a positive integer. If the captured value is non-numeric (for example "Free Zone" or "N/A"), blank the field rather than keeping junk.

**Critical:** A PO Box number is scoped to a specific branch's postal system. PO Box `12345` in Dubai is a different physical location from PO Box `12345` in Sharjah, and from PO Box `12345` in Doha. Never match records on PO Box alone — always require matching country + administrative level (emirate / region / governorate / municipality).

### Step 4 — Postal code formatting (KSA, Kuwait, Bahrain, Oman)

For countries that use postal codes:

- Saudi Arabia: 5-digit numeric, optional 4-digit extension (`XXXXX` or `XXXXX-YYYY`).
- Kuwait: 5-digit numeric.
- Bahrain: 3- or 4-digit numeric.
- Oman: 3-digit numeric.

Zero-pad shorter entries to the country's expected length. Strip any text prefix (e.g., "Postcode:", "Zip:"). If the captured value is non-numeric, blank the field.

### Step 5 — Address line discipline

Enforce a two-line structure where possible:

- `address_line_1`: building / unit / floor / block-street-building triple (Qatar/Bahrain/Kuwait) — the specific physical location.
- `address_line_2`: larger landmark (mall, tower, community, compound).

Common mistake to fix: the whole address crammed into `address_line_2` with `address_line_1` empty. Re-split where the data allows, or flag for steward review where it doesn't.

### Step 6 — Area normalization

Each country has named sub-regions, communities, and districts that carry operational meaning:

- **UAE:** `Jumeirah` vs `JBR`, `Downtown` vs `DIFC`, `Al Wasl`, `Al Barsha`, `Al Quoz` — preserve exact spelling including the `Al`.
- **KSA:** `Al Olaya`, `Al Malqa`, `Al Rawdah`, `King Abdullah Financial District` — preserve.
- **Kuwait:** `Salmiya`, `Jabriya`, `Mishref`, `Fahaheel`, `Jleeb Al-Shuyoukh` — preserve.
- **Qatar:** `Al Dafna`, `Pearl-Qatar`, `Lusail`, `West Bay` — preserve.
- **Bahrain:** `Manama`, `Muharraq`, `Juffair`, `Seef`, `Amwaj Islands` — preserve.
- **Oman:** `Ruwi`, `Qurum`, `Al Khuwair`, `Madinat Qaboos` — preserve.

If the `area` field is missing but can be inferred from the landmark (e.g., `Dubai Mall` → `Downtown`, `Mall of the Emirates` → `Al Barsha`, `Villaggio Mall` → `Aspire Zone`), propose the inferred value but do not auto-populate without steward approval.

### Step 7 — Geo-coordinate sanity check

If latitude and longitude are populated, check against each country's approximate bounding box:

| Country | Latitude range | Longitude range |
|---|---|---|
| United Arab Emirates | 22.5 to 26.5 | 51.0 to 56.5 |
| Saudi Arabia | 16.0 to 33.0 | 34.5 to 56.0 |
| Kuwait | 28.5 to 30.5 | 46.5 to 49.0 |
| Qatar | 24.5 to 26.5 | 50.5 to 52.0 |
| Bahrain | 25.5 to 27.0 | 50.0 to 51.0 |
| Oman | 16.5 to 27.0 | 51.5 to 60.0 |

- If coordinates fall outside the stated country's bounding box, flag as a data quality defect.
- If coordinates fall inside the box but do not match the stated administrative level's approximate centre (±50 km for UAE/Kuwait/Qatar/Bahrain; ±200 km for KSA/Oman given their size), flag for human review.

Missing coordinates are a less severe defect but should still be logged — they block downstream spatial analytics.

### Step 8 — Output

```
INPUT:
  address_line_1: ""
  address_line_2: "Kingdom Centre, Al Olaya"
  po_box: ""
  postal_code: "11564"
  area: "Al Olaya"
  region: "Riyadh"
  country: "KSA"
  latitude: 24.7114
  longitude: 46.6745

OUTPUT:
  address_line_1: "Kingdom Centre"
  address_line_2: ""
  po_box: ""
  postal_code: "11564"
  area: "Al Olaya"
  region: "Riyadh"
  country: "Kingdom of Saudi Arabia"
  latitude: 24.7114
  longitude: 46.6745

CHANGES:
  - country: canonical long form applied (KSA → Kingdom of Saudi Arabia)
  - address_line_1 / line_2: re-split (line_2 → line_1, area extracted)
  - postal_code: validated (5 digits, first digit "1" consistent with Riyadh region)
  - coordinates validated: (24.7114, 46.6745) falls within KSA bounding box, consistent with Riyadh region centre

FLAGS:
  - None. Record is clean.
```

## Pitfalls

- **Geo-coordinates override stated administrative level when they conflict.** If the emirate/region/governorate/municipality field disagrees with verified coordinates, trust the coordinates and flag the text field. Never trust the text over verified coordinates.
- **"City vs region/governorate" distinction matters in KSA and Oman** but not in UAE. "Dubai" is simultaneously an emirate and the name of its largest city — the same convention does not apply to Riyadh (city in Riyadh region) or Makkah (city in Makkah region). Do not blindly copy UAE habits into Saudi records.
- **Qatar has no postal code field.** Forcing a 5-digit value into a Qatar postal code column is invalid. If the schema has a postal code column that applies to all GCC countries, leave it blank for Qatar and populate the zone/street/building fields instead.
- **Free zones and economic cities have their own PO Box / postal ranges** that don't follow the standard pattern. JAFZA (Dubai), KAEC (KSA), Lusail (Qatar), NEOM (KSA). Do not flag these as invalid just because they're larger or structured differently.
- **Arabic address transliteration is not one-to-one.** "Al-Olaya" / "Al Olaya" / "Al Ulaya" are the same district. "Al-Futtaim" / "Al Futtaim" / "Alfuttaim" are the same group. Do not force one canonical romanization; record what the trade license or utility bill shows, and match across variants using a separate phonetic or fuzzy-match skill.
- **Missing geo-coordinates are genuinely common.** Many smaller suppliers and older store records never captured lat/long. Flag but do not block.
- **Country-specific administrative-level column naming varies.** Your MDM schema might call the field `emirate` (UAE-first design), `region` (KSA-first), or `governorate` (Kuwait-first). A truly GCC-wide schema uses a generic `admin_level_1` column and records the country-specific label separately. If the schema you're auditing uses a country-specific name, flag records from other countries as structurally misfiled.

## Verification

- Does the administrative-level value match the country? (UAE → emirate, KSA → region, Kuwait/Bahrain/Oman → governorate, Qatar → municipality)
- Does the postal code or PO Box follow the country's convention?
- Do the coordinates (if present) fall within the country's bounding box and near the stated administrative level's centre?
- Is the area field populated with a recognizable community, not a synonym of the administrative level itself?
- Has the original input been preserved in the audit trail?
