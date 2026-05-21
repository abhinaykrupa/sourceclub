"""
3-stage matching engine.
Stage 1: Deterministic (exact SKU/mfg SKU)
Stage 2: Semantic retrieval (fuzzy description similarity — simulates vector search)
Stage 3: LLM Judge (mocked with rule-based scoring — production uses Claude Haiku)

UOM/pack-size normalization runs alongside Stage 3 — flagging the #1 mismatch class
the team called out in training videos ("box vs case").
"""

import difflib
import re
import pandas as pd
from typing import Optional


STOPWORDS = {"dental", "the", "and", "of", "with", "for", "per", "pk", "bx", "box",
             "case", "bag", "each", "ea", "cs", "kit", "set", "non", "sterile"}

UOM_ALIASES = {
    "bx": "box", "box": "box", "boxes": "box",
    "cs": "case", "case": "case", "cases": "case",
    "bg": "bag", "bag": "bag", "bags": "bag",
    "pk": "pack", "pack": "pack", "packs": "pack",
    "ea": "each", "each": "each",
    "rl": "roll", "roll": "roll",
    "syr": "syringe", "syringe": "syringe",
    "cart": "cartridge", "cartridge": "cartridge", "cartridges": "cartridge",
    "carp": "cartridge",  # dental anesthetic carpules == cartridges
}


def _tokenize(text: str) -> set:
    tokens = re.sub(r"[^a-z0-9/]", " ", str(text).lower()).split()
    return {t for t in tokens if t not in STOPWORDS and len(t) > 1}


def _fuzzy_score(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, str(a).lower(), str(b).lower()).ratio()


def _token_overlap(a: str, b: str) -> float:
    ta, tb = _tokenize(a), _tokenize(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


def _combined_score(prospect_desc: str, catalog_desc: str) -> float:
    fuzzy = _fuzzy_score(prospect_desc, catalog_desc)
    token = _token_overlap(prospect_desc, catalog_desc)
    return 0.5 * fuzzy + 0.5 * token


def extract_pack_info(text: str) -> dict:
    """
    Parse pack size and UOM hints from a free-text description.
    e.g. "Nitrile Gloves Med PF 100/bx" -> {pack_size: 100, uom: 'box'}
         "Cotton Rolls 2000/case"        -> {pack_size: 2000, uom: 'case'}
         "Composite A2 4g Syringe"       -> {pack_size: None, uom: 'syringe'}
    """
    text_l = str(text).lower()
    info = {"pack_size": None, "uom": None}

    # "100/bx", "2000/cs", "50 / box"
    m = re.search(r"(\d{2,5})\s*/\s*([a-z]+)", text_l)
    if m:
        info["pack_size"] = int(m.group(1))
        info["uom"] = UOM_ALIASES.get(m.group(2), m.group(2))
        return info

    # "Box of 100", "Case of 2000"
    m = re.search(r"\b(box|case|bag|pack)\s+of\s+(\d{2,5})", text_l)
    if m:
        info["uom"] = UOM_ALIASES.get(m.group(1), m.group(1))
        info["pack_size"] = int(m.group(2))
        return info

    # "100 ct", "50 count", "200 per box"
    m = re.search(r"(\d{2,5})\s*(?:ct|count|per)\b", text_l)
    if m:
        info["pack_size"] = int(m.group(1))

    # Bare UOM mention
    for alias, canonical in UOM_ALIASES.items():
        if re.search(rf"\b{alias}\b", text_l):
            info["uom"] = canonical
            break

    return info


def check_uom_alignment(prospect_row: pd.Series, catalog_row: pd.Series) -> tuple[str, str]:
    """
    Returns ('aligned' | 'mismatch' | 'unknown', human-readable note).
    """
    prospect_info = extract_pack_info(prospect_row.get("raw_description", ""))

    # Some adapters carry an explicit UOM field
    explicit_uom = str(prospect_row.get("uom_raw", "")).lower().strip()
    if explicit_uom and not prospect_info["uom"]:
        prospect_info["uom"] = UOM_ALIASES.get(explicit_uom, explicit_uom)

    cat_uom = str(catalog_row.get("unit_of_measure", "")).lower().strip()
    cat_pack = str(catalog_row.get("pack_size", "")).strip()
    try:
        cat_pack_num = int(re.sub(r"[^0-9]", "", cat_pack)) if cat_pack else None
    except Exception:
        cat_pack_num = None

    p_uom = prospect_info["uom"]
    p_pack = prospect_info["pack_size"]

    if p_uom is None and p_pack is None:
        return "unknown", "UOM/pack-size could not be parsed from description"

    notes = []
    aligned = True

    if p_uom and cat_uom:
        if p_uom != cat_uom:
            aligned = False
            notes.append(f"UOM differs: prospect={p_uom}, SC={cat_uom}")
        else:
            notes.append(f"UOM aligned ({p_uom})")

    if p_pack and cat_pack_num:
        if p_pack != cat_pack_num:
            aligned = False
            notes.append(f"Pack size differs: prospect={p_pack}, SC={cat_pack_num}")
        else:
            notes.append(f"Pack size aligned ({p_pack})")

    return ("aligned" if aligned else "mismatch"), "; ".join(notes)


def stage1_deterministic(row: pd.Series, catalog: pd.DataFrame) -> Optional[pd.Series]:
    """Exact match on supplier SKU or manufacturer SKU."""
    p_sku = str(row.get("supplier_sku", "")).strip()
    p_mfg = str(row.get("manufacturer_sku", "")).strip()

    for _, cat_row in catalog.iterrows():
        if p_mfg and p_mfg.lower() not in ("", "nan") and p_mfg == str(cat_row.get("mfg_sku", "")).strip():
            return cat_row
        if p_sku and p_sku.lower() not in ("", "nan") and p_sku == str(cat_row.get("sc_sku", "")).strip():
            return cat_row
    return None


def stage2_candidates(row: pd.Series, catalog: pd.DataFrame, top_k: int = 5) -> list:
    """Return top-k catalog candidates by description similarity."""
    desc = str(row.get("raw_description", ""))
    scored = []
    for _, cat_row in catalog.iterrows():
        score = _combined_score(desc, str(cat_row.get("description", "")))
        scored.append((score, cat_row))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_k]


def stage3_llm_judge(row: pd.Series, candidates: list) -> tuple[Optional[pd.Series], float, str]:
    """
    Mocked LLM judge. Production: Claude Haiku with structured JSON output.

    Generates a rationale string that mimics what a real LLM would return:
    description alignment, manufacturer alignment, UOM/pack-size verification.
    """
    if not candidates:
        return None, 0.0, "✗ No candidates retrieved"

    best_score, best_match = candidates[0]
    parts = []

    # Description signal
    if best_score >= 0.75:
        parts.append(f"✓ Strong description match ({best_score:.2f})")
    elif best_score >= 0.55:
        parts.append(f"~ Partial description match ({best_score:.2f})")
    else:
        parts.append(f"✗ Weak description similarity ({best_score:.2f})")

    # Manufacturer signal
    p_mfg = str(row.get("manufacturer_name", "")).lower().strip()
    c_mfg = str(best_match.get("manufacturer", "")).lower().strip()
    if p_mfg and c_mfg:
        if p_mfg == c_mfg or p_mfg in c_mfg or c_mfg in p_mfg:
            parts.append(f"✓ Manufacturer match ({best_match.get('manufacturer')})")
            best_score = min(best_score + 0.15, 1.0)
        else:
            parts.append(f"⚠ Manufacturer differs: {row.get('manufacturer_name')} vs {best_match.get('manufacturer')}")

    # UOM / pack-size signal
    uom_status, uom_note = check_uom_alignment(row, best_match)
    if uom_status == "aligned":
        parts.append(f"✓ {uom_note}")
        best_score = min(best_score + 0.05, 1.0)
    elif uom_status == "mismatch":
        parts.append(f"⚠ {uom_note}")
        best_score = max(best_score - 0.15, 0.0)
    else:
        parts.append(f"? {uom_note}")

    rationale = " | ".join(parts)

    if best_score >= 0.55:
        return best_match, best_score, rationale
    else:
        return None, best_score, rationale + " — below match threshold"


def classify_status(confidence: float, annual_spend: float, method: str, uom_status: str = None) -> str:
    if method == "Deterministic":
        return "AUTO-ACCEPT"
    if uom_status == "mismatch":
        return "FORCE-REVIEW"  # UOM mismatches always go to human
    if confidence >= 0.85:
        return "AUTO-ACCEPT"
    if confidence >= 0.60:
        if annual_spend >= 500:
            return "FORCE-REVIEW"
        return "REVIEW-SUGGESTED"
    return "NO-MATCH"


def match_invoice(invoice_df: pd.DataFrame, catalog: pd.DataFrame) -> pd.DataFrame:
    results = []

    for _, row in invoice_df.iterrows():
        match = stage1_deterministic(row, catalog)
        uom_status = None

        if match is not None:
            method = "Deterministic"
            confidence = 1.0
            uom_status, uom_note = check_uom_alignment(row, match)
            rationale = f"✓ Exact SKU match | {uom_note}"
        else:
            candidates = stage2_candidates(row, catalog)
            match, confidence, rationale = stage3_llm_judge(row, candidates)
            method = "Semantic+Judge" if match is not None else "No Match"
            if match is not None:
                uom_status, _ = check_uom_alignment(row, match)

        annual_spend = float(row.get("annual_spend", 0) or 0)
        status = classify_status(confidence, annual_spend, method, uom_status)

        sc_price = float(match["unit_price"]) if match is not None else None
        current_price = float(row.get("unit_price", 0) or 0)
        qty = float(row.get("quantity", 0) or 0)

        if sc_price is not None and current_price > 0:
            unit_savings = current_price - sc_price
            total_savings = unit_savings * qty
            savings_pct = (unit_savings / current_price * 100) if current_price > 0 else 0
        else:
            unit_savings = None
            total_savings = None
            savings_pct = None

        results.append({
            "customer_name": row.get("customer_name", ""),
            "supplier_name": row.get("supplier_name", ""),
            "supplier_sku": row.get("supplier_sku", ""),
            "raw_description": row.get("raw_description", ""),
            "manufacturer_sku": row.get("manufacturer_sku", ""),
            "quantity": qty,
            "current_unit_price": current_price,
            "annual_spend": annual_spend,
            "sc_sku": match["sc_sku"] if match is not None else None,
            "sc_description": match["description"] if match is not None else None,
            "sc_unit_price": sc_price,
            "unit_savings": unit_savings,
            "total_savings": total_savings,
            "savings_pct": round(savings_pct, 1) if savings_pct is not None else None,
            "match_method": method,
            "confidence": round(confidence, 3),
            "rationale": rationale,
            "status": status,
        })

    return pd.DataFrame(results)
