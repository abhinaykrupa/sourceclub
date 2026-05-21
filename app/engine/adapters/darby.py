import pandas as pd
import io


COLUMN_MAP = {
    "Item Code": "supplier_sku",
    "Item Description": "raw_description",
    "Qty Shipped": "quantity",
    "Unit Cost": "unit_price",
    "Extended": "annual_spend",
    "Mfg": "manufacturer_name",
    "UOM": "uom_raw",
}


def parse(file_bytes: bytes, filename: str) -> pd.DataFrame:
    raw = pd.read_csv(
        io.BytesIO(file_bytes),
        skiprows=5,
        skip_blank_lines=True,
    )
    raw = raw.dropna(subset=["Item Code"])
    raw = raw[raw["Item Code"].astype(str).str.startswith("DRB")]
    raw = raw.rename(columns=COLUMN_MAP)
    raw["supplier_name"] = "Darby"
    raw["manufacturer_sku"] = ""  # Darby doesn't expose mfg SKU cleanly
    raw["customer_name"] = _extract_customer(file_bytes)
    raw["report_period"] = "2025 Annual"
    keep = ["supplier_sku", "raw_description", "manufacturer_name", "manufacturer_sku",
            "quantity", "unit_price", "annual_spend", "uom_raw",
            "supplier_name", "customer_name", "report_period"]
    raw = raw[[c for c in keep if c in raw.columns]]
    raw["quantity"] = pd.to_numeric(raw["quantity"], errors="coerce").fillna(0)
    raw["unit_price"] = pd.to_numeric(raw["unit_price"].astype(str).str.replace("$", "").str.strip(), errors="coerce").fillna(0)
    raw["annual_spend"] = pd.to_numeric(raw["annual_spend"].astype(str).str.replace("$", "").str.strip(), errors="coerce").fillna(0)
    return raw.reset_index(drop=True)


def _extract_customer(file_bytes: bytes) -> str:
    try:
        lines = file_bytes.decode("utf-8", errors="ignore").split("\n")
        for line in lines[:5]:
            if "Customer:" in line:
                return line.split("Customer:")[-1].strip()
        return "Unknown"
    except Exception:
        return "Unknown"
