# Synthetic Nexora Retail Dataset

Three CSV files covering supplier, product, and location master data for a fictitious multi-brand retail parent company. Safe to fork, share, and demo — no real-world entities are referenced.

## The fictitious brand family

**Nexora Retail** — parent company. Five sub-brands:

| Brand | Vertical | Typical records |
|---|---|---|
| **Verdant Grocers** | Supermarkets | Fresh produce, dry goods, packaged foods |
| **Luxora Beauty** | Beauty & skincare | Cosmetics, serums, fragrance, bath & body |
| **StrideSport** | Athletic wear & gear | Footwear, apparel, accessories |
| **Kindle & Loom** | Home & lifestyle | Candles, home decor, artisan textiles |
| **Petalia Fashion** | Apparel | Women's fashion, abayas, accessories |

## Known MDM pain points in the data (intentional)

This is not clean data. It's been seeded with realistic problems so the skill pack has something meaningful to resolve.

### `nexora_suppliers_dirty.csv`

- **Legal entity suffix variants** — "LLC", "L.L.C.", "Limited", "Ltd." for the same entity
- **Trading name vs legal name confusion** — records where the trading name has been entered in the legal name column
- **Cross-brand duplicates** — same supplier (same TRN) registered twice because different brands onboarded it separately
- **Trailing whitespace** on some `legal_name` values
- **Missing TRN** (tax registration number) on several records
- **Inconsistent phone formats** — hyphens, spaces, leading `+`, no separators
- **Inconsistent country naming** — "UAE" vs "United Arab Emirates"
- **Emirate variants** — "Dubai" vs "DXB" vs "Dubayy"

### `nexora_products_dirty.csv`

- **Near-duplicate products** from cross-brand supplier records (same barcode, different product_id)
- **Unit of measure inconsistency** — "kg" / "KG" / "grams" / "g" / "each" / "pcs"
- **Category naming variants** — "Groceries" / "Grocery" / "groceries"; "Beauty" / "Sports Footwear"
- **Barcode formatting** — leading zeros present on some, missing on others
- **Missing barcodes** on a few rows
- **SKU naming conventions differ by brand** — some use category prefixes, some use descriptive prefixes

### `nexora_locations_dirty.csv`

- **PO Box formatting** — missing on some, inconsistent elsewhere
- **Emirate naming** — "Dubai" / "DXB" mixed in the same column
- **Missing geo coordinates** on several locations
- **Address structure inconsistency** — some have `address_line_1` populated, some push everything into `address_line_2`
- **Country naming** — "UAE" vs "United Arab Emirates" in the same column
- **Store type taxonomy drift** — "Flagship", "Boutique", "Concept Store", "Counter", "Dark Store"

## What this is good for

- Demoing duplicate detection and match/merge decisions
- Testing address standardization for Gulf-region addresses
- Showing golden record survivorship on multi-source data
- Validating UOM normalization logic
- End-to-end scenarios in the `scenarios/` directory

## What this is NOT good for

- Performance testing (dataset is small — ~18 rows per table)
- Claims about real Gulf retail operations
- Training production ML models (too small, synthetic)
- Anything beyond demonstration of the skill pack's patterns

If you need a larger synthetic dataset, the skill pack's DQ audit script is easy to modify — swap the CSV paths and it works against whatever scale you want.
