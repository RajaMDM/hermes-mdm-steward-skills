# Scenario 02 — Correcting address variants in a location record

**Setup.** A brand onboarding lead has uploaded new store records for Luxora Beauty's Abu Dhabi expansion. The data quality audit has flagged record `NX-LOC-00203` with a critical warning: the emirate field says `DXB` but the geo-coordinates place it on Yas Island in Abu Dhabi.

This scenario walks through how the skill pack resolves the conflict and produces a clean record.

---

## The record

From `nexora_locations_dirty.csv`:

```
Record: NX-LOC-00203
  brand:            Luxora Beauty
  store_name:       Luxora AUH Yas
  address_line_1:   (empty)
  address_line_2:   Yas Mall Ground Floor
  po_box:           127864
  area:             Yas Island
  emirate:          DXB            ← suspicious
  country:          UAE
  latitude:         24.4886
  longitude:        54.6077
  store_type:       Flagship
  opening_date:     2021-10-10
  status:           Active
```

## Steward prompt

```
/mdm-location-validator

Our DQ audit flagged a conflict on NX-LOC-00203. Emirate field says DXB but
the coordinates look wrong. Validate the record and tell me what to change.

[paste the record as above]
```

## Expected agent response (using `/mdm-location-validator`)

```
VALIDATION RESULT: CRITICAL CONFLICT

Step 1 — Country: "UAE" → keep as-is if tenant canonical form is short code;
         switch to "United Arab Emirates" if tenant canonical form is long.
         (This tenant uses long form elsewhere in the dataset — recommend
         long form.)

Step 2 — Emirate normalization:
  Input value: "DXB"
  "DXB" is a variant of "Dubai" in this skill pack's canonical table.
  However — Gate: verify against geo-coordinates before accepting the
  normalization.

Step 6 — Geo-coordinate sanity check:
  Coordinates: (24.4886, 54.6077)
  These coordinates fall within the Abu Dhabi emirate bounding box
  (approx. 22.5–25.3 lat, 51.0–56.0 lon).
  Dubai emirate centre is approximately (25.2, 55.3).
  Distance from stated emirate (Dubai) centre: ~95 km.
  Distance from Abu Dhabi emirate centre: ~36 km.
  The coordinates are consistent with Yas Island in Abu Dhabi.

CONFLICT DIAGNOSIS:
  The emirate field is WRONG. The data entry error likely came from the
  store_name prefix "Luxora AUH Yas" — "AUH" is the IATA code for Abu
  Dhabi. Someone typed "DXB" in the emirate field by mistake, probably a
  reflex default for UAE records.

Step 4 — Address line discipline:
  address_line_1 is empty; address_line_2 holds the whole address.
  Re-split: move "Yas Mall Ground Floor" to address_line_1.

Step 3 — PO Box formatting:
  Raw value "127864" → canonical form "PO Box 127864".

PROPOSED CHANGES:

  address_line_1:  "Yas Mall Ground Floor"            (was empty)
  address_line_2:  ""                                  (was "Yas Mall...")
  po_box:          "PO Box 127864"                     (was "127864")
  emirate:         "Abu Dhabi"                         (was "DXB" — CORRECTED)
  country:         "United Arab Emirates"              (was "UAE")

FLAGS:
  - CRITICAL: emirate correction is not a formatting change — it is a
    factual correction. Source system should be updated to reflect the true
    emirate, and any reports grouped by emirate will reclassify this store.
  - The store's accounting code, tax registration, and local compliance
    filings may depend on the emirate. Verify no downstream systems need
    corresponding updates before persisting.

RECOMMENDED ACTION: Escalate the emirate change to the Luxora Beauty brand
onboarding lead for confirmation. Other formatting changes can proceed
under normal DQ workflow.
```

## What this scenario demonstrates

1. **Geo-coordinates are treated as more authoritative than text fields** when they conflict — and the skill pack flags the conflict rather than silently normalizing a wrong value.
2. **A data quality issue can mask a real-world classification error.** This record wasn't just formatted badly — it was categorizing an Abu Dhabi store as a Dubai store, which would have skewed every emirate-sliced report until someone noticed.
3. **The agent proposes changes but escalates factual corrections** rather than auto-apply. Formatting the PO Box is safe. Reclassifying the emirate is not — it has downstream accounting and compliance implications.
4. **Detective reasoning is explicit.** The agent names the likely root cause ("AUH in the store name, reflex default of DXB in emirate") so the steward can check the rest of the brand's onboarding batch for the same pattern.

## If this pattern repeats

Three records with the same failure mode (emirate field defaulting to DXB regardless of actual location) is a signal that the upstream data entry template has a default value that shouldn't be there. The agent's learning loop would capture this as a cross-cutting observation and surface it during the next `/mdm-steward-briefing`.

## Follow-up a steward might issue

```
Scan the rest of the Luxora Beauty locations in the dataset for the same
pattern — emirate says Dubai but coordinates suggest otherwise. Report
anything that looks like the same entry error.
```

The agent would loop over the location records, apply Gate 6 to each, and return any additional mismatches. This is where persistent memory starts earning its keep — the agent knows this steward cares about the AUH/DXB confusion pattern and can proactively look for it.
