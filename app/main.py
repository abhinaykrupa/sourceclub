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
<style>
    /* Tighter padding */
    .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem; max-width: 1280px; }
    /* Metric tweaks */
    [data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px 18px;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    }
    [data-testid="stMetricLabel"] > div { color: #64748B; font-size: 0.85rem; }
    [data-testid="stMetricValue"] { color: #0F172A; font-size: 1.7rem; font-weight: 700; }
    [data-testid="stMetricDelta"] { font-size: 0.78rem; }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        border-bottom: 2px solid #E2E8F0;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 18px;
        background: transparent;
        border-radius: 8px 8px 0 0;
        font-weight: 600;
        color: #64748B;
    }
    .stTabs [aria-selected="true"] {
        background: #F0F9F8 !important;
        color: #0EA5A1 !important;
    }

    /* Expander styling */
    .streamlit-expanderHeader { font-size: 0.95rem; }

    /* DataFrame */
    [data-testid="stDataFrame"] { border-radius: 6px; overflow: hidden; }

    /* Section headers in non-dashboard tabs */
    h2 { color: #0F172A; font-weight: 700; }
    h3 { color: #0F172A; font-weight: 600; }

    /* Buttons */
    .stButton > button {
        border-radius: 6px;
        font-weight: 600;
    }
    .stDownloadButton > button {
        background: #0EA5A1;
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 600;
    }
    .stDownloadButton > button:hover {
        background: #0F766E;
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

st.markdown("""
<div style="margin-bottom: 4px;">
    <span style="font-size: 1.9rem; font-weight: 800; color: #0F172A;">🦷 SourceClub</span>
    <span style="font-size: 1.1rem; color: #64748B; margin-left: 8px;">Operations POC</span>
</div>
<div style="color: #64748B; font-size: 0.95rem; max-width: 900px; margin-bottom: 14px;">
    Case-study deliverable for the <b>Head of AI Powered Operations, Systems & RevOps</b> role.
    Three lean prototypes — savings-analysis automation, Stripe↔HubSpot multi-location sync,
    90-day project roadmap — wrapped in a leadership dashboard built for CEO, Marketing, and Sales.
</div>
""", unsafe_allow_html=True)

tab_dash, tab_sa, tab_sync, tab_roadmap = st.tabs([
    "📊 Leadership Dashboard",
    "1️⃣ Savings Analysis",
    "2️⃣ Stripe ↔ HubSpot Sync",
    "3️⃣ 90-Day Roadmap",
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
