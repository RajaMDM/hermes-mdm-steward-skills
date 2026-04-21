"""MDM Data Quality Audit Script.

Runs a baseline DQ audit over supplier, product, and location master data files.
Produces a structured markdown summary suitable for delivery via a messaging
gateway (email, Telegram, Slack) or attachment to a steward review.

Usage:
    python run_dq_audit.py \\
        --suppliers path/to/suppliers.csv \\
        --products  path/to/products.csv \\
        --locations path/to/locations.csv \\
        --output    /tmp/dq_audit_summary.md

If paths are omitted, the script falls back to the skill pack's bundled synthetic
dataset (resolved relative to this script's location).

Author: Raja Shahnawaz Soni
License: MIT
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("mdm-dq-audit")


# ---------------------------------------------------------------------------
# Canonical reference values
# ---------------------------------------------------------------------------

CANONICAL_EMIRATES: set[str] = {
    "Dubai",
    "Abu Dhabi",
    "Sharjah",
    "Ajman",
    "Ras Al Khaimah",
    "Fujairah",
    "Umm Al Quwain",
}

EMIRATE_VARIANTS: set[str] = {
    "DXB",
    "Dubayy",
    "AUH",
    "SHJ",
    "AJM",
    "RAK",
    "FUJ",
    "UAQ",
    "Abu-Dhabi",
    "Ras al-Khaimah",
}

CANONICAL_COUNTRY: str = "UAE"
COUNTRY_VARIANTS: set[str] = {"United Arab Emirates", "U.A.E.", "Emirates"}

CRITICAL_SUPPLIER_FIELDS: list[str] = [
    "legal_name",
    "trn",
    "po_box",
    "emirate",
    "phone",
    "email",
]

CRITICAL_PRODUCT_FIELDS: list[str] = [
    "product_name",
    "category",
    "uom",
    "barcode",
    "supplier_id",
]

CRITICAL_LOCATION_FIELDS: list[str] = [
    "store_name",
    "po_box",
    "emirate",
    "latitude",
    "longitude",
]


# ---------------------------------------------------------------------------
# Result containers
# ---------------------------------------------------------------------------


@dataclass
class EntityAudit:
    """Audit results for a single entity type (suppliers/products/locations)."""

    entity_name: str
    record_count: int
    completeness: dict[str, float] = field(default_factory=dict)
    duplicate_candidates: list[tuple[str, str, str]] = field(default_factory=list)
    format_violations: list[dict[str, Any]] = field(default_factory=list)
    cross_brand_overlap: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class AuditSummary:
    """Top-level audit result across all entity types."""

    run_timestamp: datetime
    suppliers: EntityAudit | None = None
    products: EntityAudit | None = None
    locations: EntityAudit | None = None
    top_issues: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _load_csv(path: Path, entity_name: str) -> pd.DataFrame:
    """Load a CSV file into a DataFrame with logging.

    Args:
        path: Path to the CSV file.
        entity_name: Human-readable name for log messages.

    Returns:
        Loaded DataFrame.

    Raises:
        FileNotFoundError: If the file does not exist.
        pd.errors.EmptyDataError: If the file is empty.
    """
    if not path.exists():
        raise FileNotFoundError(f"{entity_name} file not found: {path}")

    logger.info("Loading %s from %s", entity_name, path)
    df = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])
    logger.info("Loaded %d %s records", len(df), entity_name)
    return df


def _completeness(df: pd.DataFrame, fields: list[str]) -> dict[str, float]:
    """Compute completeness percentage per critical field.

    Args:
        df: DataFrame to audit.
        fields: List of field names to check.

    Returns:
        Mapping of field name to percentage (0.0 to 100.0) populated.
    """
    result: dict[str, float] = {}
    total = len(df)
    if total == 0:
        return {f: 0.0 for f in fields}
    for field_name in fields:
        if field_name not in df.columns:
            result[field_name] = 0.0
            continue
        populated = df[field_name].notna().sum()
        result[field_name] = round((populated / total) * 100, 1)
    return result


def _find_duplicate_suppliers(df: pd.DataFrame) -> list[tuple[str, str, str]]:
    """Find supplier records sharing the same TRN (deterministic match).

    Args:
        df: Supplier DataFrame.

    Returns:
        List of (supplier_id_a, supplier_id_b, shared_trn) tuples.
    """
    duplicates: list[tuple[str, str, str]] = []
    if "trn" not in df.columns or "supplier_id" not in df.columns:
        return duplicates

    populated = df[df["trn"].notna()].copy()
    grouped = populated.groupby("trn")
    for trn_value, group in grouped:
        if len(group) < 2:
            continue
        supplier_ids = sorted(group["supplier_id"].tolist())
        for i in range(len(supplier_ids)):
            for j in range(i + 1, len(supplier_ids)):
                duplicates.append((supplier_ids[i], supplier_ids[j], str(trn_value)))
    return duplicates


def _find_duplicate_products(df: pd.DataFrame) -> list[tuple[str, str, str]]:
    """Find product records sharing the same barcode (deterministic match).

    Args:
        df: Product DataFrame.

    Returns:
        List of (product_id_a, product_id_b, shared_barcode) tuples.
    """
    duplicates: list[tuple[str, str, str]] = []
    if "barcode" not in df.columns or "product_id" not in df.columns:
        return duplicates

    populated = df[df["barcode"].notna()].copy()
    # Strip leading zeros for comparison (common formatting inconsistency).
    populated["barcode_normalized"] = populated["barcode"].str.lstrip("0")
    grouped = populated.groupby("barcode_normalized")
    for barcode_value, group in grouped:
        if len(group) < 2:
            continue
        product_ids = sorted(group["product_id"].tolist())
        for i in range(len(product_ids)):
            for j in range(i + 1, len(product_ids)):
                duplicates.append(
                    (product_ids[i], product_ids[j], str(barcode_value))
                )
    return duplicates


def _emirate_violations(df: pd.DataFrame, id_col: str) -> list[dict[str, Any]]:
    """Detect emirate-field values that are non-canonical variants.

    Args:
        df: DataFrame to audit (suppliers or locations).
        id_col: Primary key column name for reporting.

    Returns:
        List of violation dicts with record id and offending value.
    """
    violations: list[dict[str, Any]] = []
    if "emirate" not in df.columns:
        return violations

    for _, row in df.iterrows():
        emirate_value = row.get("emirate")
        if pd.isna(emirate_value):
            continue
        if emirate_value in EMIRATE_VARIANTS:
            violations.append(
                {
                    "record_id": row[id_col],
                    "field": "emirate",
                    "offending_value": emirate_value,
                    "severity": "HIGH",
                }
            )
        elif emirate_value not in CANONICAL_EMIRATES:
            violations.append(
                {
                    "record_id": row[id_col],
                    "field": "emirate",
                    "offending_value": emirate_value,
                    "severity": "MEDIUM",
                }
            )
    return violations


def _country_violations(df: pd.DataFrame, id_col: str) -> list[dict[str, Any]]:
    """Detect country-field values that deviate from the canonical form.

    Args:
        df: DataFrame to audit.
        id_col: Primary key column name.

    Returns:
        List of violation dicts.
    """
    violations: list[dict[str, Any]] = []
    if "country" not in df.columns:
        return violations

    for _, row in df.iterrows():
        country_value = row.get("country")
        if pd.isna(country_value):
            continue
        if country_value in COUNTRY_VARIANTS:
            violations.append(
                {
                    "record_id": row[id_col],
                    "field": "country",
                    "offending_value": country_value,
                    "severity": "LOW",
                }
            )
    return violations


def _cross_brand_overlap(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Identify suppliers used by more than one brand.

    This is informational — multi-brand supplier relationships are normal
    and expected in multi-brand retail. Flagged for visibility, not as a defect.

    Args:
        df: Supplier DataFrame.

    Returns:
        List of overlap dicts.
    """
    overlap: list[dict[str, Any]] = []
    if "trn" not in df.columns or "brand_used_by" not in df.columns:
        return overlap

    populated = df[df["trn"].notna()].copy()
    grouped = populated.groupby("trn")
    for trn_value, group in grouped:
        brands = sorted(set(group["brand_used_by"].dropna().tolist()))
        if len(brands) > 1:
            overlap.append(
                {
                    "trn": str(trn_value),
                    "brands": brands,
                    "record_count": len(group),
                }
            )
    return overlap


# ---------------------------------------------------------------------------
# Entity-specific audit routines
# ---------------------------------------------------------------------------


def audit_suppliers(df: pd.DataFrame) -> EntityAudit:
    """Run the full audit suite over supplier records."""
    audit = EntityAudit(entity_name="Suppliers", record_count=len(df))
    audit.completeness = _completeness(df, CRITICAL_SUPPLIER_FIELDS)
    audit.duplicate_candidates = _find_duplicate_suppliers(df)
    audit.format_violations = _emirate_violations(df, "supplier_id") + _country_violations(
        df, "supplier_id"
    )
    audit.cross_brand_overlap = _cross_brand_overlap(df)
    return audit


def audit_products(df: pd.DataFrame) -> EntityAudit:
    """Run the full audit suite over product records."""
    audit = EntityAudit(entity_name="Products", record_count=len(df))
    audit.completeness = _completeness(df, CRITICAL_PRODUCT_FIELDS)
    audit.duplicate_candidates = _find_duplicate_products(df)
    audit.format_violations = []  # UOM/category violations omitted from baseline
    audit.cross_brand_overlap = []
    return audit


def audit_locations(df: pd.DataFrame) -> EntityAudit:
    """Run the full audit suite over location records."""
    audit = EntityAudit(entity_name="Locations", record_count=len(df))
    audit.completeness = _completeness(df, CRITICAL_LOCATION_FIELDS)
    audit.duplicate_candidates = []
    audit.format_violations = _emirate_violations(df, "location_id") + _country_violations(
        df, "location_id"
    )
    audit.cross_brand_overlap = []
    return audit


# ---------------------------------------------------------------------------
# Summary generation
# ---------------------------------------------------------------------------


def _rank_top_issues(summary: AuditSummary) -> list[str]:
    """Produce a ranked list of the top issues across all entity audits.

    Ranking:
      CRITICAL: duplicate candidates (deterministic ID match)
      HIGH:     emirate variant violations
      MEDIUM:   non-canonical emirate values (not in variant list either)
      LOW:      country field variants, completeness gaps below 80%

    Args:
        summary: Full audit summary.

    Returns:
        List of human-readable issue strings, most severe first, top 5.
    """
    issues: list[tuple[int, str]] = []

    for audit in (summary.suppliers, summary.products, summary.locations):
        if audit is None:
            continue

        if audit.duplicate_candidates:
            count = len(audit.duplicate_candidates)
            issues.append(
                (
                    0,
                    f"CRITICAL: {count} {audit.entity_name.lower()} duplicate candidate"
                    f"{'s' if count != 1 else ''} detected via deterministic ID match",
                )
            )

        high_violations = [
            v for v in audit.format_violations if v["severity"] == "HIGH"
        ]
        if high_violations:
            issues.append(
                (
                    1,
                    f"HIGH: {len(high_violations)} {audit.entity_name.lower()} "
                    f"record{'s' if len(high_violations) != 1 else ''} use "
                    f"non-canonical emirate codes (e.g. DXB instead of Dubai)",
                )
            )

        medium_violations = [
            v for v in audit.format_violations if v["severity"] == "MEDIUM"
        ]
        if medium_violations:
            issues.append(
                (
                    2,
                    f"MEDIUM: {len(medium_violations)} {audit.entity_name.lower()} "
                    f"record{'s' if len(medium_violations) != 1 else ''} use "
                    f"unrecognized emirate values",
                )
            )

        low_completeness = [
            f"{field_name} ({pct}%)"
            for field_name, pct in audit.completeness.items()
            if pct < 80.0
        ]
        if low_completeness:
            issues.append(
                (
                    3,
                    f"LOW: {audit.entity_name} fields below 80% completeness: "
                    f"{', '.join(low_completeness)}",
                )
            )

    issues.sort(key=lambda x: x[0])
    return [issue for _, issue in issues[:5]]


def render_markdown(summary: AuditSummary) -> str:
    """Render the audit summary as a markdown report.

    Args:
        summary: The full audit summary.

    Returns:
        A markdown string suitable for writing to disk or sending via gateway.
    """
    lines: list[str] = []
    lines.append(
        f"# MDM Daily DQ Audit — {summary.run_timestamp.strftime('%Y-%m-%d %H:%M')}"
    )
    lines.append("")
    lines.append("## Summary")
    lines.append("")

    for audit in (summary.suppliers, summary.products, summary.locations):
        if audit is None:
            continue
        lines.append(f"### {audit.entity_name}")
        lines.append(f"- Records: **{audit.record_count}**")
        lines.append("- Completeness:")
        for field_name, pct in audit.completeness.items():
            lines.append(f"  - `{field_name}`: {pct}%")
        lines.append(f"- Duplicate candidates: **{len(audit.duplicate_candidates)}**")
        lines.append(f"- Format violations: **{len(audit.format_violations)}**")
        if audit.cross_brand_overlap:
            lines.append(
                f"- Cross-brand overlaps: **{len(audit.cross_brand_overlap)}** "
                f"(informational)"
            )
        lines.append("")

    lines.append("## Top issues")
    lines.append("")
    if summary.top_issues:
        for i, issue in enumerate(summary.top_issues, start=1):
            lines.append(f"{i}. {issue}")
    else:
        lines.append("_No issues detected at or above the MEDIUM severity threshold._")
    lines.append("")

    if summary.suppliers and summary.suppliers.duplicate_candidates:
        lines.append("## Supplier duplicate candidates (detail)")
        lines.append("")
        lines.append("| Record A | Record B | Shared TRN |")
        lines.append("|---|---|---|")
        for a, b, trn in summary.suppliers.duplicate_candidates:
            lines.append(f"| {a} | {b} | {trn} |")
        lines.append("")

    if summary.products and summary.products.duplicate_candidates:
        lines.append("## Product duplicate candidates (detail)")
        lines.append("")
        lines.append("| Record A | Record B | Shared barcode |")
        lines.append("|---|---|---|")
        for a, b, barcode in summary.products.duplicate_candidates:
            lines.append(f"| {a} | {b} | {barcode} |")
        lines.append("")

    if summary.suppliers and summary.suppliers.cross_brand_overlap:
        lines.append("## Cross-brand supplier overlap (informational)")
        lines.append("")
        lines.append("| TRN | Brands | Record count |")
        lines.append("|---|---|---|")
        for overlap in summary.suppliers.cross_brand_overlap:
            brands_str = ", ".join(overlap["brands"])
            lines.append(
                f"| {overlap['trn']} | {brands_str} | {overlap['record_count']} |"
            )
        lines.append("")

    lines.append("---")
    lines.append("_Generated by the MDM Steward Agent skill pack._")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def _resolve_default(path: str | None, default_name: str) -> Path:
    """Resolve a path argument, falling back to the bundled dataset.

    Args:
        path: User-supplied path or None.
        default_name: Filename in the bundled `datasets/` directory.

    Returns:
        A Path object.
    """
    if path:
        return Path(path).expanduser().resolve()
    script_dir = Path(__file__).resolve().parent
    default = script_dir.parent.parent.parent / "datasets" / default_name
    return default


def main(argv: list[str] | None = None) -> int:
    """Run the DQ audit end-to-end.

    Args:
        argv: Optional argument list (defaults to sys.argv).

    Returns:
        Exit code: 0 on success, non-zero on error.
    """
    parser = argparse.ArgumentParser(description="Run an MDM DQ audit.")
    parser.add_argument("--suppliers", type=str, default=None)
    parser.add_argument("--products", type=str, default=None)
    parser.add_argument("--locations", type=str, default=None)
    parser.add_argument(
        "--output",
        type=str,
        default="/tmp/dq_audit_summary.md",
        help="Path to write the markdown summary.",
    )
    args = parser.parse_args(argv)

    suppliers_path = _resolve_default(args.suppliers, "nexora_suppliers_dirty.csv")
    products_path = _resolve_default(args.products, "nexora_products_dirty.csv")
    locations_path = _resolve_default(args.locations, "nexora_locations_dirty.csv")

    try:
        suppliers_df = _load_csv(suppliers_path, "suppliers")
        products_df = _load_csv(products_path, "products")
        locations_df = _load_csv(locations_path, "locations")
    except (FileNotFoundError, pd.errors.EmptyDataError) as exc:
        logger.error("Failed to load input: %s", exc)
        return 1

    summary = AuditSummary(run_timestamp=datetime.now())
    summary.suppliers = audit_suppliers(suppliers_df)
    summary.products = audit_products(products_df)
    summary.locations = audit_locations(locations_df)
    summary.top_issues = _rank_top_issues(summary)

    markdown = render_markdown(summary)

    output_path = Path(args.output).expanduser().resolve()
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
    except OSError as exc:
        logger.error("Failed to write output: %s", exc)
        return 1

    logger.info("Audit complete. Summary written to %s", output_path)
    print(markdown)
    return 0


if __name__ == "__main__":
    sys.exit(main())
