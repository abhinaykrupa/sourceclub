import pandas as pd
import io


COLUMN_MAP = {
    "Item #": "supplier_sku",
    "Description": "raw_description",
    "Manufacturer": "manufacturer_name",
    "Mfg Item #": "manufacturer_sku",
    "Qty Ordered": "quantity",
    "Unit Price": "unit_price",
    "Extended Price": "annual_spend",
}


def parse(file_bytes: bytes, filename: str) -> pd.DataFrame:
    raw = pd.read_csv(
        io.BytesIO(file_bytes),
        skiprows=3,
        skip_blank_lines=True,
    )
    raw = raw.dropna(subset=["Item #"])
    raw = raw[raw["Item #"].astype(str).str.startswith("BEN")]
    raw = raw.rename(columns=COLUMN_MAP)
    raw["supplier_name"] = "Benco"
    raw["customer_name"] = _extract_customer(file_bytes)
    raw["report_period"] = "2025 Annual"
    keep = list(COLUMN_MAP.values()) + ["supplier_name", "customer_name", "report_period"]
    raw = raw[[c for c in keep if c in raw.columns]]
    raw["quantity"] = pd.to_numeric(raw["quantity"], errors="coerce").fillna(0)
    raw["unit_price"] = pd.to_numeric(raw["unit_price"].astype(str).str.replace("$", "").str.strip(), errors="coerce").fillna(0)
    raw["annual_spend"] = pd.to_numeric(raw["annual_spend"].astype(str).str.replace("$", "").str.strip(), errors="coerce").fillna(0)
    return raw.reset_index(drop=True)


def _extract_customer(file_bytes: bytes) -> str:
    try:
        first_line = file_bytes.decode("utf-8", errors="ignore").split("\n")[0]
        return first_line.split("-")[0].strip()
    except Exception:
        return "Unknown"
