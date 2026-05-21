import pandas as pd
import io


COLUMN_MAP = {
    "Product Code": "supplier_sku",
    "Product Description": "raw_description",
    "Category": "category",
    "Annual Qty": "quantity",
    "Price Per Unit": "unit_price",
    "Annual Spend": "annual_spend",
    "Supplier": "sub_supplier",
}


def parse(file_bytes: bytes, filename: str) -> pd.DataFrame:
    raw = pd.read_csv(
        io.BytesIO(file_bytes),
        skiprows=5,
        skip_blank_lines=True,
    )
    raw = raw.dropna(subset=["Product Code"])
    raw = raw[raw["Product Code"].astype(str).str.startswith("B86")]
    raw = raw.rename(columns=COLUMN_MAP)
    raw["supplier_name"] = "Base86"
    raw["manufacturer_name"] = ""
    raw["manufacturer_sku"] = ""
    raw["customer_name"] = _extract_customer(file_bytes)
    raw["report_period"] = "2025 Annual"
    keep = ["supplier_sku", "raw_description", "manufacturer_name", "manufacturer_sku",
            "quantity", "unit_price", "annual_spend", "supplier_name", "customer_name", "report_period"]
    raw = raw[[c for c in keep if c in raw.columns]]
    raw["quantity"] = pd.to_numeric(raw["quantity"], errors="coerce").fillna(0)
    raw["unit_price"] = pd.to_numeric(raw["unit_price"].astype(str).str.replace("$", "").str.strip(), errors="coerce").fillna(0)
    raw["annual_spend"] = pd.to_numeric(raw["annual_spend"].astype(str).str.replace("$", "").str.strip(), errors="coerce").fillna(0)
    return raw.reset_index(drop=True)


def _extract_customer(file_bytes: bytes) -> str:
    try:
        lines = file_bytes.decode("utf-8", errors="ignore").split("\n")
        for line in lines[:5]:
            if "Practice:" in line:
                return line.split("Practice:")[-1].strip()
        return "Unknown"
    except Exception:
        return "Unknown"
