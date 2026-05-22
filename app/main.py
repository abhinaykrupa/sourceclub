"""
SourceClub Operations POC — Streamlit application.

Four tabs:
  1. Leadership Dashboard — exec-facing view (CEO / Marketing / Sales)
  2. Savings Analysis — upload supplier purchase history → matched report + PDF + email
  3. Stripe ↔ HubSpot Sync — mock dashboard showing the multi-location data spine
  4. 90-Day Roadmap — prioritized project queue with rationale
"""

import io
from pathlib import Path

import pandas as pd
import streamlit as st

from engine.adapters import ADAPTERS, auto_detect
from engine.matcher import match_invoice
from sync.sync_engine import (
    build_company_billing_snapshot,
    build_location_detail,
    get_unmapped_stripe_customers,
)
from views import dashboard as dashboard_view
from app_helpers.email_drafter import draft_outreach_email
from app_helpers.pdf_generator import generate_savings_pdf

# ---------- Config ----------

st.set_page_config(
    page_title="SourceClub Ops POC",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ROOT = Path(__file__).parent.parent
CATALOG_PATH = ROOT / "sample_data" / "sourceclub_catalog.csv"
SAMPLE_DIR = ROOT / "sample_data"

# ---------- Global styling ----------
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
    /* ---- Typography baseline ---- */
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-feature-settings: 'cv11', 'ss01';
        -webkit-font-smoothing: antialiased;
    }

    /* ---- Page background — soft healthcare gradient ---- */
    .stApp {
        background:
            radial-gradient(ellipse at top right, rgba(14, 165, 161, 0.045) 0%, transparent 50%),
            radial-gradient(ellipse at bottom left, rgba(16, 185, 129, 0.035) 0%, transparent 50%),
            #FAFCFC;
    }

    /* ---- Container ---- */
    .block-container {
        padding-top: 2.5rem !important;
        padding-bottom: 3rem;
        max-width: 1320px;
    }

    /* ---- Hero header section ---- */
    .sc-hero {
        background: linear-gradient(135deg, #0F766E 0%, #0EA5A1 50%, #14B8A6 100%);
        border-radius: 16px;
        padding: 28px 32px;
        margin-bottom: 22px;
        color: white;
        box-shadow:
            0 4px 24px rgba(15, 118, 110, 0.18),
            0 1px 2px rgba(15, 23, 42, 0.04);
        position: relative;
        overflow: hidden;
    }
    .sc-hero::before {
        content: "";
        position: absolute;
        top: -40%;
        right: -10%;
        width: 380px;
        height: 380px;
        background: radial-gradient(circle, rgba(255,255,255,0.12) 0%, transparent 70%);
        pointer-events: none;
    }
    .sc-hero::after {
        content: "";
        position: absolute;
        bottom: -30%;
        left: 15%;
        width: 200px;
        height: 200px;
        background: radial-gradient(circle, rgba(94,234,212,0.18) 0%, transparent 70%);
        pointer-events: none;
    }
    .sc-hero-row { display: flex; align-items: center; gap: 18px; position: relative; z-index: 1; }
    .sc-hero-text { flex: 1; }
    .sc-wordmark {
        font-family: 'Inter', sans-serif;
        font-size: 2.05rem;
        font-weight: 800;
        line-height: 1.15;
        letter-spacing: -0.025em;
        color: white;
        padding-top: 4px;
        margin: 0;
    }
    .sc-subtitle {
        font-size: 0.85rem;
        font-weight: 500;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: rgba(255,255,255,0.78);
        margin-top: 4px;
    }
    .sc-pill {
        display: inline-flex; align-items: center; gap: 6px;
        background: rgba(255,255,255,0.16);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255,255,255,0.22);
        padding: 5px 12px; border-radius: 999px;
        font-size: 0.72rem; font-weight: 600;
        color: white;
        letter-spacing: 0.04em;
    }
    .sc-pill-dot {
        width: 7px; height: 7px; border-radius: 50%;
        background: #6EE7B7; box-shadow: 0 0 8px #6EE7B7;
    }
    .sc-tagline {
        color: #475569;
        font-size: 0.95rem;
        line-height: 1.55;
        max-width: 920px;
        margin-bottom: 14px;
    }
    .sc-tagline b { color: #0F172A; font-weight: 700; }

    /* ---- Metric cards: accent stripe + better hierarchy ---- */
    [data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px 18px 18px 18px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04), 0 1px 2px rgba(15, 23, 42, 0.03);
        position: relative;
        overflow: hidden;
        transition: box-shadow 0.18s ease, transform 0.18s ease;
    }
    [data-testid="stMetric"]::before {
        content: "";
        position: absolute; top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #0EA5A1 0%, #10B981 100%);
    }
    [data-testid="stMetric"]:hover {
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08), 0 1px 2px rgba(15, 23, 42, 0.04);
        transform: translateY(-1px);
    }
    [data-testid="stMetricLabel"] > div {
        color: #64748B; font-size: 0.78rem; font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.06em;
    }
    [data-testid="stMetricValue"] {
        color: #0F172A; font-size: 1.85rem; font-weight: 800;
        letter-spacing: -0.02em; line-height: 1.2;
    }
    [data-testid="stMetricDelta"] { font-size: 0.78rem; font-weight: 600; }

    /* ---- Tab list ---- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        border-bottom: 1px solid #E2E8F0;
        padding-bottom: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 12px 22px 14px 22px;
        background: transparent;
        border-radius: 10px 10px 0 0;
        font-weight: 600;
        font-size: 0.92rem;
        color: #64748B;
        transition: all 0.15s ease;
        margin-bottom: -1px;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #0F766E;
        background: rgba(14, 165, 161, 0.05);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(180deg, #F0FDFA 0%, #FFFFFF 100%) !important;
        color: #0F766E !important;
        border-bottom: 2px solid #0EA5A1 !important;
    }

    /* ---- Section headers (h2 / h3) ---- */
    h2, .stMarkdown h2 {
        color: #0F172A; font-weight: 800;
        letter-spacing: -0.02em;
        margin-top: 1.3rem; margin-bottom: 0.5rem;
    }
    h3, .stMarkdown h3 { color: #0F172A; font-weight: 700; letter-spacing: -0.01em; }
    .stSubheader, .stMarkdown h2 + p { color: #475569; }

    /* ---- Expanders ---- */
    .streamlit-expanderHeader, [data-testid="stExpander"] summary {
        font-size: 0.93rem;
        font-weight: 600;
    }
    [data-testid="stExpander"] {
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        background: #FFFFFF;
    }

    /* ---- DataFrames ---- */
    [data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #E2E8F0;
    }

    /* ---- Buttons ---- */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.9rem;
        padding: 8px 16px;
        border: 1px solid #E2E8F0;
        background: #FFFFFF;
        color: #0F172A;
        transition: all 0.15s ease;
    }
    .stButton > button:hover {
        border-color: #0EA5A1;
        color: #0F766E;
        box-shadow: 0 2px 6px rgba(14, 165, 161, 0.12);
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0F766E 0%, #0EA5A1 100%);
        color: white;
        border: none;
    }
    .stDownloadButton > button {
        background: linear-gradient(135deg, #0F766E 0%, #0EA5A1 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 9px 16px;
        box-shadow: 0 1px 3px rgba(15, 118, 110, 0.25);
    }
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #134E4A 0%, #0F766E 100%);
        box-shadow: 0 3px 8px rgba(15, 118, 110, 0.32);
        transform: translateY(-1px);
    }

    /* ---- Captions ---- */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #64748B; font-size: 0.82rem;
    }

    /* ---- File uploader ---- */
    [data-testid="stFileUploader"] section {
        border: 2px dashed #CBD5E1;
        background: #F8FAFC;
        border-radius: 10px;
        padding: 18px;
        transition: all 0.15s ease;
    }
    [data-testid="stFileUploader"] section:hover {
        border-color: #0EA5A1;
        background: #F0FDFA;
    }

    /* ---- Code blocks (architecture diagrams) ---- */
    code, pre {
        font-family: 'JetBrains Mono', 'Menlo', monospace !important;
        font-size: 0.8rem !important;
    }
    pre {
        background: #0F172A !important;
        color: #E2E8F0 !important;
        border-radius: 8px !important;
        padding: 16px !important;
    }

    /* ---- Subtle horizontal rule ---- */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, #CBD5E1 50%, transparent 100%);
        margin: 1.4rem 0;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_catalog() -> pd.DataFrame:
    return pd.read_csv(CATALOG_PATH)


def status_badge(status: str) -> str:
    colors = {
        "AUTO-ACCEPT": "🟢",
        "REVIEW-SUGGESTED": "🟡",
        "FORCE-REVIEW": "🟠",
        "NO-MATCH": "🔴",
    }
    return f"{colors.get(status, '⚪')} {status}"


# ---------- App header ----------

SC_LOGO_SVG = """
<svg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg" style="flex-shrink:0;">
  <defs>
    <linearGradient id="sclogo" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.95"/>
      <stop offset="100%" stop-color="#E6FFFA" stop-opacity="0.9"/>
    </linearGradient>
  </defs>
  <rect x="2" y="2" width="56" height="56" rx="14"
        fill="rgba(255,255,255,0.12)"
        stroke="rgba(255,255,255,0.32)" stroke-width="1.5"/>
  <!-- stylized tooth/shield -->
  <path d="M30 14 C23 14 18 18 18 25 C18 30 20.5 34 23 40 C24.5 43.5 26 46 30 46 C34 46 35.5 43.5 37 40 C39.5 34 42 30 42 25 C42 18 37 14 30 14 Z"
        fill="url(#sclogo)"/>
  <!-- inner highlight stroke -->
  <path d="M30 20 C26 20 23 22.5 23 26 C23 29 25 32 26.5 35.5"
        stroke="rgba(15,118,110,0.42)" stroke-width="2" stroke-linecap="round" fill="none"/>
  <!-- accent dot suggesting "savings" / value -->
  <circle cx="36" cy="22" r="2.5" fill="#5EEAD4"/>
</svg>
"""

st.markdown(f"""
<div class="sc-hero">
    <div class="sc-hero-row">
        {SC_LOGO_SVG}
        <div class="sc-hero-text">
            <div class="sc-wordmark">SourceClub</div>
            <div class="sc-subtitle">Operations Platform · Case Study POC</div>
        </div>
        <div style="display:flex; flex-direction:column; align-items:flex-end; gap:6px;">
            <div class="sc-pill"><span class="sc-pill-dot"></span> LIVE · MOCK DATA</div>
            <div style="font-size:0.72rem; color:rgba(255,255,255,0.7); letter-spacing:0.04em;">
                Built for CEO · Marketing · Sales
            </div>
        </div>
    </div>
</div>

<div class="sc-tagline">
    Case-study deliverable for the <b>Head of AI Powered Operations, Systems &amp; RevOps</b> role.
    Three lean prototypes — savings-analysis automation, Stripe↔HubSpot multi-location sync, 90-day project roadmap —
    fronted by a <b>leadership dashboard</b> with persona views for the CEO, Head of Marketing, and Head of Sales/Revenue.
</div>
""", unsafe_allow_html=True)

tab_dash, tab_sa, tab_sync, tab_roadmap = st.tabs([
    "  📊  Leadership Dashboard  ",
    "  🔍  Savings Analysis  ",
    "  🔗  Stripe ↔ HubSpot Sync  ",
    "  🗺️  90-Day Roadmap  ",
])

# ============================================================
# TAB 0: LEADERSHIP DASHBOARD
# ============================================================

with tab_dash:
    dashboard_view.render()

# ============================================================
# TAB 1: SAVINGS ANALYSIS
# ============================================================

with tab_sa:
    st.header("Savings Analysis — Automated Matching Pipeline")
    st.markdown(
        "Upload a prospect's supplier purchase history. The pipeline auto-detects supplier, "
        "parses the file format, runs the 3-stage matching engine, and produces a savings report "
        "with a human review queue, a branded PDF for the prospect, and an AI-drafted follow-up email."
    )

    with st.expander("📐 Pipeline architecture", expanded=False):
        st.markdown("""
```
Upload → Auto-detect Supplier → Supplier Adapter → Canonical Schema
                                                        │
                                                        ▼
                                  ┌──────────────────────────────────┐
                                  │  3-STAGE MATCHING ENGINE          │
                                  │                                   │
                                  │  Stage 1: Deterministic           │
                                  │           (exact SKU / Mfg SKU)   │
                                  │  Stage 2: Semantic Retrieval      │
                                  │           (vector / fuzzy top-K)  │
                                  │  Stage 3: LLM Judge               │
                                  │           (Claude Haiku, mocked)  │
                                  │  Cross-cut: UOM/pack normalizer   │
                                  └──────────────────────────────────┘
                                                        │
                    ┌───────────────────────────────────┼─────────────────────────────────┐
                    ▼                                   ▼                                 ▼
            AUTO-ACCEPT (≥0.85)            REVIEW QUEUE (0.60–0.85,                NO-MATCH (<0.60)
            → Savings Report               UOM mismatch, or high-$$)               → Catalog gap bucket
                                           → Human reviews in app
```
        """)

    # ---- File source ----
    col_left, col_right = st.columns([2, 1])
    with col_left:
        uploaded_file = st.file_uploader(
            "Drop a supplier purchase history CSV",
            type=["csv"],
            help="Supports Benco, Henry Schein, Darby, Base86, and 'Patterson (messy)' export formats."
        )
    with col_right:
        st.markdown("**Or try a sample file:**")
        sample_choice = st.selectbox(
            "Sample file",
            options=["— none —",
                     "Auburn Dental (Benco)",
                     "Demit Dental (Henry Schein)",
                     "Quincy Smiles (Darby)",
                     "Auburn Dental Group (Base86)",
                     "Patterson (messy real-world export)"],
            label_visibility="collapsed",
        )

    sample_map = {
        "Auburn Dental (Benco)": "auburn_dental_benco.csv",
        "Demit Dental (Henry Schein)": "demit_dental_henry_schein.csv",
        "Quincy Smiles (Darby)": "quincy_smiles_darby.csv",
        "Auburn Dental Group (Base86)": "auburn_dental_base86.csv",
        "Patterson (messy real-world export)": "harbor_view_patterson_messy.csv",
    }

    file_bytes = None
    filename = None

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        filename = uploaded_file.name
    elif sample_choice != "— none —":
        sample_path = SAMPLE_DIR / sample_map[sample_choice]
        if sample_path.exists():
            file_bytes = sample_path.read_bytes()
            filename = sample_path.name
        else:
            st.warning(f"Sample file {sample_path.name} not found yet.")

    if file_bytes is None:
        st.info("👆 Upload a file or select a sample to run the analysis.")
    else:
        # ---- Detect supplier ----
        detected = auto_detect.detect(file_bytes, filename)
        c1, c2, c3 = st.columns(3)
        c1.metric("File", filename)
        c2.metric("Detected Supplier", detected)
        c3.metric("Pipeline", "3-stage + UOM check")

        if detected == "Unknown":
            st.error("Could not auto-detect supplier from this file. Add an adapter to support it.")
            st.stop()

        # ---- Parse ----
        adapter_fn = ADAPTERS[detected]
        try:
            normalized = adapter_fn(file_bytes, filename)
        except Exception as e:
            st.error(f"Adapter failed to parse file: {e}")
            st.stop()

        st.success(f"Parsed {len(normalized)} line items from {detected} export")

        with st.expander(f"🔍 View normalized input ({len(normalized)} rows)"):
            st.dataframe(normalized, use_container_width=True)

        # ---- Match ----
        catalog = load_catalog()
        with st.spinner("Running 3-stage matching engine..."):
            results = match_invoice(normalized, catalog)

        # Stash for later actions
        st.session_state["last_results"] = results
        st.session_state["last_customer"] = normalized["customer_name"].iloc[0] if len(normalized) else "Unknown"
        st.session_state["last_supplier"] = detected

        # ---- Summary metrics ----
        total_spend = results["annual_spend"].sum()
        total_savings = results["total_savings"].fillna(0).sum()
        savings_pct = (total_savings / total_spend * 100) if total_spend > 0 else 0
        match_rate = (results["status"].isin(["AUTO-ACCEPT"]).sum() / len(results) * 100) if len(results) > 0 else 0

        st.subheader("📊 Savings Summary")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Current Annual Spend", f"${total_spend:,.0f}")
        m2.metric("Projected SC Spend", f"${total_spend - total_savings:,.0f}")
        m3.metric("Estimated Savings", f"${total_savings:,.0f}", f"{savings_pct:.1f}%")
        m4.metric("Auto-Match Rate", f"{match_rate:.0f}%")

        # ---- Salesperson actions (NEW) ----
        st.markdown("---")
        st.subheader("🚀 Salesperson Actions")
        st.caption("Once the analysis is reviewed, ship it to the prospect.")
        act1, act2, act3 = st.columns(3)

        with act1:
            pdf_bytes = generate_savings_pdf(
                results,
                customer_name=st.session_state["last_customer"],
                supplier_name=detected,
                period="2025 Annual"
            )
            st.download_button(
                "📄 Generate Branded PDF Report",
                data=pdf_bytes,
                file_name=f"sourceclub_savings_report_{st.session_state['last_customer'].replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        with act2:
            if st.button("🤖 Draft AI Follow-up Email", use_container_width=True):
                # Build a prospect dict from the analysis result
                prospect = {
                    "company": st.session_state["last_customer"],
                    "locations": 1,  # POC default; production reads from HubSpot
                    "specialty": "general",
                    "state": "CA",
                    "rep": "Jake P.",
                    "annual_supply_spend": int(total_spend),
                    "identified_savings": int(total_savings),
                    "savings_pct": round(savings_pct, 1),
                    "source": "Inbound — Web",
                }
                st.session_state["sa_email"] = draft_outreach_email(prospect)

        with act3:
            csv_buffer = io.StringIO()
            results.to_csv(csv_buffer, index=False)
            st.download_button(
                "📊 Export Audit CSV",
                data=csv_buffer.getvalue(),
                file_name=f"savings_audit_{filename.replace('.csv', '')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        # Email preview if drafted
        if "sa_email" in st.session_state:
            email = st.session_state["sa_email"]
            with st.expander("📧 Drafted email — review and send", expanded=True):
                st.text_input("Subject", value=email["subject"], key="sa_email_subj")
                st.text_area("Body", value=email["body"], height=300, key="sa_email_body")
                st.caption("💡 Production: real Claude Sonnet call. Current version is rule-based template (clearly labeled).")

        # ---- Match breakdown ----
        st.markdown("---")
        st.subheader("Match Distribution")
        status_counts = results["status"].value_counts().to_dict()
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("🟢 Auto-Accept", status_counts.get("AUTO-ACCEPT", 0))
        b2.metric("🟡 Review Suggested", status_counts.get("REVIEW-SUGGESTED", 0))
        b3.metric("🟠 Force Review", status_counts.get("FORCE-REVIEW", 0))
        b4.metric("🔴 No Match", status_counts.get("NO-MATCH", 0))

        # ---- Auto-accepted section ----
        auto = results[results["status"] == "AUTO-ACCEPT"].copy()
        if len(auto) > 0:
            with st.expander(f"🟢 Auto-Accepted Matches ({len(auto)})", expanded=False):
                st.dataframe(
                    auto[["raw_description", "sc_description", "current_unit_price",
                          "sc_unit_price", "savings_pct", "total_savings",
                          "match_method", "confidence"]]
                    .rename(columns={
                        "raw_description": "Prospect Item",
                        "sc_description": "SC Match",
                        "current_unit_price": "Current $",
                        "sc_unit_price": "SC $",
                        "savings_pct": "Save %",
                        "total_savings": "Annual Savings",
                        "match_method": "Method",
                        "confidence": "Conf",
                    }),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Annual Savings": st.column_config.NumberColumn(format="$%.0f"),
                        "Current $": st.column_config.NumberColumn(format="$%.2f"),
                        "SC $": st.column_config.NumberColumn(format="$%.2f"),
                        "Save %": st.column_config.NumberColumn(format="%.1f%%"),
                    },
                )

        # ---- Review queue (interactive) ----
        review = results[results["status"].isin(["REVIEW-SUGGESTED", "FORCE-REVIEW"])].copy()
        if len(review) > 0:
            st.subheader(f"🟡🟠 Human Review Queue ({len(review)})")
            st.caption(
                "These line items need a human decision before going into the final report. "
                "In production, this becomes a Retool/Notion queue with approve/override actions."
            )
            for idx, row in review.iterrows():
                badge = status_badge(row["status"])
                with st.expander(
                    f"{badge} · {row['raw_description'][:60]} · ${row['annual_spend']:,.0f} annual"
                ):
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        st.markdown("**Prospect Item**")
                        st.text(f"Desc: {row['raw_description']}")
                        st.text(f"SKU:  {row['supplier_sku']}")
                        st.text(f"Mfg:  {row['manufacturer_sku']}")
                        st.text(f"Qty:  {row['quantity']:.0f}")
                        st.text(f"Price: ${row['current_unit_price']:.2f}")
                    with cc2:
                        st.markdown("**Proposed SC Match**")
                        st.text(f"Desc: {row['sc_description']}")
                        st.text(f"SKU:  {row['sc_sku']}")
                        st.text(f"Price: ${row['sc_unit_price']:.2f}")
                        if row["total_savings"]:
                            st.text(f"Savings: ${row['total_savings']:,.0f} annual")
                    st.markdown(f"**Rationale:** {row['rationale']}")
                    st.markdown(f"**Confidence:** `{row['confidence']:.2f}`")
                    ac1, ac2, ac3 = st.columns(3)
                    ac1.button("✅ Approve", key=f"approve_{idx}")
                    ac2.button("❌ Reject", key=f"reject_{idx}")
                    ac3.button("✏️ Override Match", key=f"override_{idx}")

        # ---- No-match section ----
        no_match = results[results["status"] == "NO-MATCH"].copy()
        if len(no_match) > 0:
            with st.expander(f"🔴 No Match — Catalog gap opportunities ({len(no_match)})"):
                st.caption(
                    "These items have no equivalent in the SourceClub catalog. "
                    "Production system feeds these into a 'catalog gap' list for procurement."
                )
                st.dataframe(
                    no_match[["raw_description", "manufacturer_sku", "annual_spend", "rationale"]]
                    .rename(columns={
                        "raw_description": "Prospect Item",
                        "manufacturer_sku": "Mfg SKU",
                        "annual_spend": "Annual Spend",
                        "rationale": "Why",
                    }),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Annual Spend": st.column_config.NumberColumn(format="$%.0f"),
                    },
                )

# ============================================================
# TAB 2: STRIPE ↔ HUBSPOT SYNC
# ============================================================

with tab_sync:
    st.header("Stripe ↔ HubSpot Sync — Multi-Location Data Spine")
    st.markdown(
        "**The problem:** Stripe bills per location (subscription) but HubSpot tracks the parent company. "
        "Native integrations dump billing data onto Deals or Invoices — not the Company record — and can't "
        "roll up multi-location MRR into a single view."
    )
    st.markdown(
        "**The fix:** A canonical mapping table joining `Stripe Customer ↔ Stripe Subscription ↔ "
        "HubSpot Location ↔ HubSpot Company`. A sync engine reads Stripe webhooks, aggregates per-location "
        "billing into Company-level rollups, and writes them to HubSpot custom properties."
    )

    with st.expander("📐 Sync architecture", expanded=False):
        st.markdown("""
```
   STRIPE                  CANONICAL MAPPING               HUBSPOT
   ──────                  ─────────────────               ───────
   Customer ─┐                                         ┌─ Company
             │   ┌───────────────────────────┐         │   │
   Sub ──────┼──▶│ stripe_sub_id ─────────┐  │         │   ├─ Location
             │   │ stripe_customer_id  ───┼──┼────────▶│   │
   Invoice ──┘   │ hs_company_id ─────────┘  │         │   └─ Location
                 │ hs_location_id ───────────┼─────────┤
                 └───────────────────────────┘         │   Properties:
                            ▲                          │   • MRR / ARR
                            │                          │   • Active subs
                            │                          │   • Past-due flag
   Webhooks ────────────────┘                          │   • Health status
   (subscription.*, invoice.*)
                                                       Exception queue:
                                                       unmapped customers
```
        """)

    # ---- Company-level rollup ----
    st.subheader("Company Billing Health (HubSpot view)")
    snapshot = build_company_billing_snapshot()
    display = snapshot[[
        "name", "owner", "total_locations", "active_subscriptions",
        "past_due_count", "canceled_count", "total_mrr", "total_arr", "billing_health"
    ]].rename(columns={
        "name": "Company",
        "owner": "CS Owner",
        "total_locations": "Locations",
        "active_subscriptions": "Active Subs",
        "past_due_count": "Past Due",
        "canceled_count": "Canceled",
        "total_mrr": "MRR ($)",
        "total_arr": "ARR ($)",
        "billing_health": "Health",
    })
    st.dataframe(
        display, use_container_width=True, hide_index=True,
        column_config={
            "MRR ($)": st.column_config.NumberColumn(format="$%d"),
            "ARR ($)": st.column_config.NumberColumn(format="$%d"),
        },
    )

    # ---- Per-company drill-down ----
    st.subheader("Per-Location Drill-Down")
    selected_company = st.selectbox(
        "Select a company to inspect",
        snapshot["name"].tolist(),
    )
    selected_id = snapshot[snapshot["name"] == selected_company].iloc[0]["hs_company_id"]
    locations = build_location_detail(selected_id)

    if len(locations) > 0:
        st.dataframe(
            locations.rename(columns={
                "location_name": "Location",
                "stripe_sub_id": "Stripe Sub ID",
                "status": "Status",
                "mrr": "MRR ($)",
                "plan": "Plan",
                "current_period_end": "Period End",
                "past_due": "Past Due",
            }),
            use_container_width=True,
            hide_index=True,
            column_config={
                "MRR ($)": st.column_config.NumberColumn(format="$%d"),
            },
        )

    # ---- Exception queue ----
    st.subheader("⚠️ Exception Queue — Unmapped Stripe Customers")
    unmapped = get_unmapped_stripe_customers()
    if unmapped:
        st.dataframe(pd.DataFrame(unmapped), use_container_width=True, hide_index=True)
    else:
        st.success("✓ All Stripe customers are mapped to HubSpot companies.")

    # ---- Recommendation ----
    st.subheader("🏆 Recommended Implementation")
    st.markdown("""
| Option | Cost | Fit | Verdict |
|---|---|---|---|
| Native Stripe-HubSpot integration | $0 (included) | Maps to Deals, not Company. No multi-location rollup logic. | ❌ |
| Middleware only (Make / Zapier) | $30–50/mo | Quick MVP but brittle for backfills, audits, canonical mapping. | ⚠️ |
| **Custom sync service + canonical map** | ~1 dev-week build, ~$0 ongoing infra | Owns the data spine. Webhooks + nightly reconcile. Auditable. | ✅ |

**Why the custom build wins long-term:** the canonical map is the same data spine
the customer health score (3.5) and ZenOne ordering data (1.2) will both need.
Building it once here pays off three more times downstream.
    """)

# ============================================================
# TAB 3: 90-DAY ROADMAP
# ============================================================

with tab_roadmap:
    st.header("90-Day Roadmap — Prioritized Project Queue")
    st.markdown(
        "Sequencing for the first 90 days in the seat. I prioritize by **dependencies and "
        "revenue leverage**, not just urgency. The first three projects unblock the rest."
    )

    st.subheader("Top 5: from the existing queue")
    queue = pd.DataFrame([
        {"Order": "1", "Project": "2.1 Automate Savings Analysis", "Effort": "3–4 weeks", "Impact": "★★★★★",
         "Why first": "#1 revenue bottleneck. 5–7 hrs/mo of founder time. Doubles sales throughput. Explicitly highest priority in the brief."},
        {"Order": "2", "Project": "1.1 Stripe ↔ HubSpot Name Matching", "Effort": "1–2 weeks", "Impact": "★★★★☆",
         "Why first": "Foundational data spine. Unblocks billing visibility, CS dashboards, and the customer health score downstream."},
        {"Order": "3", "Project": "3.1 Consolidate CS into HubSpot", "Effort": "2–3 weeks", "Impact": "★★★★☆",
         "Why first": "Currently no ticketing system. Moving to HubSpot ticketing gives team-level measurability and prevents churn from dropped requests."},
        {"Order": "4", "Project": "3.8 Post-Onboarding Drip Campaign", "Effort": "1 week", "Impact": "★★★☆☆",
         "Why first": "Quick win. Improves activation in the critical first-two-weeks window. Reuses the HubSpot work from #2."},
        {"Order": "5", "Project": "1.2 ZenOne Data Integration", "Effort": "3–4 weeks", "Impact": "★★★★★",
         "Why first": "Backbone for everything in Q2: customer health score (3.5), 45/90-day check-ins (3.6), missed-savings alerts. Must come before any of those."},
    ])
    st.dataframe(queue, use_container_width=True, hide_index=True)

    st.subheader("Why NOT others first")
    st.markdown("""
- **1.3 Unified business dashboard** — premature. Garbage-in until the billing data spine (#2) and ordering data (#5) are clean.
- **3.5 Customer Health Score** — sequencing trap. Depends on ZenOne data (#5). Doing the score before the pipe = a number nobody trusts.
- **4.1 Company AI Audit** — broad and unfocused before the core revenue/service workflows are stabilized. Better in days 90–180.
- **2.4 PandaDoc automation** — moderate impact but low frequency relative to #1.
    """)

    st.divider()
    st.subheader("💡 What's missing from the queue — my proposals")
    st.markdown(
        "The existing queue is solid for the obvious wins. These are higher-leverage additions "
        "that come from thinking about SourceClub's flywheel — every member buys monthly, and "
        "every prospect needs a savings analysis. That's two engines that get faster with automation."
    )

    proposed = pd.DataFrame([
        {"ID": "NEW-1", "Proposed Project": "Supplier API Integrations (Benco, Henry Schein)",
         "Category": "Data", "Effort": "4–6 weeks", "Impact": "★★★★★",
         "Annual $ Impact": "$200K", "Mechanism": "Eliminates manual export step. Enables real-time price-drift detection. Cuts analyst time from 10 min → 0.",
         "Why": "Eliminates the manual export step in savings analysis. Enables real-time price-drift detection."},
        {"ID": "NEW-2", "Proposed Project": "Catalog Drift Monitor",
         "Category": "Trust", "Effort": "1 week", "Impact": "★★★★☆",
         "Annual $ Impact": "$40K retained MRR", "Mechanism": "Prevents 2 churns/yr × $20K ACV × 80% confidence.",
         "Why": "Daily diff of supplier prices vs SC catalog. Alerts when any item moves >5%. Prevents the 'we promised $X' churn scenario."},
        {"ID": "NEW-3", "Proposed Project": "Member Spend Forecast + Drop Alert",
         "Category": "Retention", "Effort": "2 weeks", "Impact": "★★★★☆",
         "Annual $ Impact": "$75K retained MRR", "Mechanism": "Catches 5 churn-risk members/yr × 6mo earlier × $1.25K/mo each.",
         "Why": "Forecast monthly spend per member from ZenOne data. Alert CS owner when spend drops >25% MoM. Earliest churn signal."},
        {"ID": "NEW-4", "Proposed Project": "Cross-Sell Recommender",
         "Category": "Expansion", "Effort": "2–3 weeks", "Impact": "★★★☆☆",
         "Annual $ Impact": "$120K GMV", "Mechanism": "5% of members add 1 cross-sell category × $X avg basket lift.",
         "Why": "Members who buy X also buy Y, often at 30% markup elsewhere. Surfaces savings the member doesn't know about."},
        {"ID": "NEW-5", "Proposed Project": "Prospect Auto-Enrichment",
         "Category": "Sales Velocity", "Effort": "1–2 weeks", "Impact": "★★★☆☆",
         "Annual $ Impact": "$60K (sales hours saved)", "Mechanism": "Saves 15min/discovery × 20 calls/wk × $100/hr loaded rate.",
         "Why": "Given a practice domain, auto-pull location count, specialty mix, likely supplier. Shortens discovery from 30 → 15 min."},
        {"ID": "NEW-6", "Proposed Project": "AI Quote Bot for Members",
         "Category": "Member Experience", "Effort": "3 weeks", "Impact": "★★★☆☆",
         "Annual $ Impact": "$80K GMV + retention", "Mechanism": "Faster order velocity + reduces 'I forgot to order' churn driver.",
         "Why": "Slack/email bot: 'What's my best price for nitrile gloves medium?' Returns SC price + comparison."},
        {"ID": "NEW-7", "Proposed Project": "Win/Loss Auto-Analysis",
         "Category": "Sales Ops", "Effort": "1 week", "Impact": "★★☆☆☆",
         "Annual $ Impact": "$30K (conversion lift)", "Mechanism": "LLM finds 2-3 messaging insights/qtr → 2pp conversion improvement.",
         "Why": "LLM digests HubSpot closed-won/lost notes monthly. Surfaces top 3 objections + segments that convert. Feeds back into messaging."},
        {"ID": "NEW-8", "Proposed Project": "Smart Order Routing",
         "Category": "Margin", "Effort": "4 weeks", "Impact": "★★★★☆",
         "Annual $ Impact": "$400K GMV", "Mechanism": "8% margin lift on $5M routed GMV. Needs ZenOne + supplier APIs first.",
         "Why": "Given a member order, auto-route to lowest-cost supplier with stock. Production-grade lift."},
        {"ID": "NEW-9", "Proposed Project": "Internal AI Knowledge Search",
         "Category": "Team Velocity", "Effort": "1–2 weeks", "Impact": "★★★☆☆",
         "Annual $ Impact": "$70K (FTE-equivalent)", "Mechanism": "Saves ~5hrs/wk across 7-person team × $100/hr loaded.",
         "Why": "All SOPs, member notes, supplier contracts indexed. 'When does the Schein contract renew?' answered in 5 sec."},
        {"ID": "NEW-10", "Proposed Project": "Onboarding Time-to-First-Order Tracker",
         "Category": "Activation", "Effort": "1 week", "Impact": "★★★☆☆",
         "Annual $ Impact": "$50K retained MRR", "Mechanism": "Catches stalled onboardings 2wk earlier → reduces early-stage churn.",
         "Why": "Single metric: contract-signed → first ZenOne order. Drives every onboarding decision."},
    ])
    st.dataframe(proposed, use_container_width=True, hide_index=True)

    total_impact = 200 + 40 + 75 + 120 + 60 + 80 + 30 + 400 + 70 + 50
    st.caption(f"💰 **Aggregate annual $ impact if all 10 projects ship: ~${total_impact}K.** These are first-order estimates — defensible directionally, not point-precise.")

    st.divider()
    st.subheader("📈 Full 90-Day Sequencing View")
    st.markdown("""
```
Weeks 1–4   ████████ 2.1 Automate Savings Analysis           ← P0, ships standalone
Weeks 2–4   ████ 1.1 Stripe ↔ HubSpot Sync (in parallel)     ← unblocks #3, #5
Weeks 4–6   ████ 3.8 Post-Onboarding Drip                    ← quick win
Weeks 5–8   ████████ 3.1 CS Consolidation into HubSpot       ← needs #2 plumbing
Weeks 8–12  ████████████ 1.2 ZenOne Data Integration         ← Q2 backbone
Weeks 11–13 ████ NEW-2 Catalog Drift Monitor                 ← protects #1
Weeks 12+   .... NEW-1, NEW-3, NEW-8 ...                     ← unlocked once data spine is in place
```

**The thesis:** the first 90 days build *the spine* (Stripe + HubSpot + ZenOne).
Everything else in this proposed list becomes 3–5x cheaper to build once that spine exists.
That's the difference between a queue of 30 disconnected projects and a roadmap.
    """)

st.divider()
st.caption(
    "POC built as case-study deliverable · Mocked LLM calls (production uses Claude Haiku/Sonnet) · "
    "Mocked Stripe/HubSpot data (production reads live APIs) · "
    "Persistent state, auth, multi-tenancy intentionally out of POC scope"
)
