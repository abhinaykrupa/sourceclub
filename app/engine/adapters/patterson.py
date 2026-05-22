"""
Patterson Dental adapter — designed to handle real-world export mess.

The Patterson export commonly has:
  • Leading/trailing whitespace in column headers and values
  • Mixed UOM formats ("100/BX", "Box of 50", "100ct")
  • $-prefixed prices with embedded commas
  • Embedded commas in quoted descriptions
  • Blank rows between sections
  • TOTAL/footer rows
  • Inconsistent capitalization
"""

import io
import re
import pandas as pd


COLUMN_MAP = {
    "Order Number": "order_number",
    "Product Code": "supplier_sku",
    "Product Description": "raw_description",
    "Qty": "quantity",
    "Pack/UOM": "uom_raw",
    "Unit Cost": "unit_price",
    "Total": "annual_spend",
}


def _clean_money(val) -> float:
    """Parse '$1,234.56' / ' $12.95 ' / '12.95' → 12.95"""
    if pd.isna(val):
        return 0.0
    s = str(val).strip().replace("$", "").replace(",", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _clean_qty(val) -> float:
    if pd.isna(val):
        return 0.0
    s = str(val).strip().replace(",", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse(file_bytes: bytes, filename: str) -> pd.DataFrame:
    raw = pd.read_csv(
        io.BytesIO(file_bytes),
        skiprows=6,
        skip_blank_lines=True,
        skipinitialspace=True,
    )

    # Strip whitespace from column names
    raw.columns = [c.strip() for c in raw.columns]

    # Drop blank rows + TOTAL footer rows
    raw = raw.dropna(subset=["Order Number"])
    raw = raw[~raw["Order Number"].astype(str).str.strip().str.upper().eq("TOTAL")]
    raw = raw[raw["Order Number"].astype(str).str.strip().str.startswith("PTN")]

    # Rename to canonical
    raw = raw.rename(columns=COLUMN_MAP)
    keep_cols = [c for c in COLUMN_MAP.values() if c in raw.columns]
    raw = raw[keep_cols].copy()

    # Strip whitespace from all string columns
    for col in raw.select_dtypes(include="object").columns:
        raw[col] = raw[col].astype(str).str.strip()

    # Clean numerics
    raw["quantity"] = raw["quantity"].apply(_clean_qty)
    raw["unit_price"] = raw["unit_price"].apply(_clean_money)
    raw["annual_spend"] = raw["annual_spend"].apply(_clean_money)

    # Patterson doesn't expose manufacturer info — leave blank
    raw["manufacturer_name"] = ""
    raw["manufacturer_sku"] = ""
    raw["supplier_name"] = "Patterson"
    raw["customer_name"] = _extract_customer(file_bytes)
    raw["report_period"] = "2025 Annual"

    keep_final = ["supplier_sku", "raw_description", "manufacturer_name", "manufacturer_sku",
                  "quantity", "unit_price", "annual_spend", "uom_raw",
                  "supplier_name", "customer_name", "report_period"]
    raw = raw[[c for c in keep_final if c in raw.columns]]

    return raw.reset_index(drop=True)


def _extract_customer(file_bytes: bytes) -> str:
    try:
        lines = file_bytes.decode("utf-8", errors="ignore").split("\n")
        for line in lines[:6]:
            if "Practice:" in line:
                return line.split("Practice:", 1)[-1].strip()
        return "Unknown"
    except Exception:
        return "Unknown"
