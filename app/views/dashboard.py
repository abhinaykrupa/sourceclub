"""
Leadership Dashboard — the first view a SourceClub exec opens.

Three persona-targeted sections on one page:
  • CEO view: pipeline health, savings delivered, throughput
  • Head of Marketing view: ICP signals, objections, case-study fodder
  • Head of Sales/Revenue view: deal-level pipeline + AI-drafted nudges
"""

from collections import Counter
from datetime import date
import pandas as pd
import streamlit as st

# plotly imported lazily inside render() — saves ~2s on cold start when user
# hasn't opened the dashboard tab yet

from sync.pipeline_data import (
    build_pipeline,
    segment_savings_summary,
    common_objections,
    ready_to_nudge,
)
from app_helpers.email_drafter import draft_outreach_email


# ---- Theme-aware palette ----
def _theme():
    """Return color tokens based on current theme."""
    is_dark = st.session_state.get("theme", "dark") == "dark"
    if is_dark:
        return {
            "teal": "#14B8A6",
            "sage": "#34D399",
            "slate": "#F8FAFC",
            "text_muted": "#94A3B8",
            "card_bg": "#111A2C",
            "card_border": "#1E293B",
            "soft_bg": "#0F172A",
            "amber": "#FBBF24",
            "rose": "#FB7185",
            "indigo": "#818CF8",
            "chart_bg": "#0B1220",
            "chart_paper": "#111A2C",
            "grid": "#1E293B",
        }
    return {
        "teal": "#0EA5A1",
        "sage": "#10B981",
        "slate": "#0F172A",
        "text_muted": "#64748B",
        "card_bg": "#FFFFFF",
        "card_border": "#E2E8F0",
        "soft_bg": "#F0F9F8",
        "amber": "#F59E0B",
        "rose": "#E11D48",
        "indigo": "#6366F1",
        "chart_bg": "#FFFFFF",
        "chart_paper": "#FFFFFF",
        "grid": "#E2E8F0",
    }


# Module-level fallbacks (used outside render)
TEAL = "#0EA5A1"
SAGE = "#10B981"
SLATE = "#0F172A"
LIGHT_BG = "#F0F9F8"
AMBER = "#F59E0B"
ROSE = "#E11D48"
INDIGO = "#6366F1"


def _section_header(icon: str, title: str, subtitle: str, accent: str = None):
    t = _theme()
    accent = accent or t["teal"]
    st.markdown(
        f"""
<div style="margin-top: 1.8rem; margin-bottom: 0.8rem; padding: 18px 22px; background: linear-gradient(135deg, {t['card_bg']} 0%, {t['soft_bg']} 100%); border-radius: 12px; border: 1px solid {t['card_border']}; border-left: 4px solid {accent}; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);">
<div style="display: flex; align-items: center; gap: 12px;">
<div style="width: 38px; height: 38px; border-radius: 10px; background: linear-gradient(135deg, {accent} 0%, #0F766E 100%); display: flex; align-items: center; justify-content: center; font-size: 1.15rem; color: white; box-shadow: 0 2px 6px rgba(15, 118, 110, 0.35);">{icon}</div>
<div>
<div style="font-size: 1.18rem; font-weight: 800; color: {t['slate']}; letter-spacing: -0.01em;">{title}</div>
<div style="font-size: 0.86rem; color: {t['text_muted']}; margin-top: 1px; font-weight: 500;">{subtitle}</div>
</div>
</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def _kpi_card(label: str, value: str, delta: str = None, delta_color: str = "normal"):
    st.metric(label=label, value=value, delta=delta, delta_color=delta_color)


@st.cache_data
def _cached_pipeline():
    return build_pipeline()


def render():
    import plotly.graph_objects as go  # lazy — only when dashboard tab is rendered
    t = _theme()
    pipeline = _cached_pipeline()
    df = pd.DataFrame(pipeline)

    # ---- Page header ----
    st.markdown(
        f"""
<div style="padding: 14px 22px; margin-bottom: 6px; background: linear-gradient(135deg, {t['soft_bg']} 0%, {t['card_bg']} 100%); border-radius: 12px; border: 1px solid {t['card_border']};">
<div style="display: flex; align-items: center; justify-content: space-between; gap: 16px;">
<div>
<div style="font-size: 1.55rem; font-weight: 800; color: {t['slate']}; letter-spacing: -0.02em; line-height: 1.2;">Leadership Dashboard</div>
<div style="color: {t['text_muted']}; font-size: 0.93rem; margin-top: 4px; max-width: 720px;">Monday-morning view for the <b style="color:{t['slate']};">CEO</b>, <b style="color:{t['slate']};">Head of Marketing</b>, and <b style="color:{t['slate']};">Head of Sales/Revenue</b> — one page, three lenses on the same pipeline.</div>
</div>
<div style="text-align: right; font-size: 0.75rem; color: {t['text_muted']}; letter-spacing: 0.04em;">
<div style="font-weight: 700; color: {t['teal']};">{date.today().strftime('%b %d, %Y')}</div>
<div>45 active prospects</div>
<div style="opacity: 0.7;">Mocked HubSpot pipeline</div>
</div>
</div>
</div>
        """,
        unsafe_allow_html=True,
    )

    # ============================================================
    # CEO VIEW
    # ============================================================
    _section_header("🏢", "CEO View", "Pipeline health, savings delivered, team throughput")

    # --- KPI row ---
    active_pipeline_value = df[df["potential_mrr"] > 0][~df["stage"].isin(["Closed Won", "Closed Lost"])]["identified_savings"].fillna(0).sum()
    closed_won_mtd = df[df["stage"] == "Closed Won"]["outcome_savings"].fillna(0).sum()
    sa_count_mtd = df[~df["stage"].isin(["SA Requested"])].shape[0]
    avg_time_per_sa = 8  # minutes — with automation; was 10 manual
    closed_won_mrr = df[df["stage"] == "Closed Won"]["outcome_mrr"].fillna(0).sum()
    closed_won_count = (df["stage"] == "Closed Won").sum()
    lost_count = (df["stage"] == "Closed Lost").sum()
    conv_rate = closed_won_count / (closed_won_count + lost_count) * 100 if (closed_won_count + lost_count) > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _kpi_card("Active Pipeline Savings", f"${active_pipeline_value/1000:,.0f}K",
                  "Identified, not yet closed", "off")
    with c2:
        _kpi_card("Closed Won MRR (MTD)", f"${closed_won_mrr:,.0f}",
                  f"+{closed_won_count} new members", "normal")
    with c3:
        _kpi_card("SAs Completed (MTD)", f"{sa_count_mtd}",
                  f"Conv rate: {conv_rate:.0f}%", "normal" if conv_rate > 60 else "inverse")
    with c4:
        _kpi_card("Avg Time per SA", f"{avg_time_per_sa} min",
                  "vs 10 min manual (was 5-7 hrs/mo)", "normal")

    # --- Two charts side-by-side ---
    chart_col_l, chart_col_r = st.columns(2)

    with chart_col_l:
        st.markdown("**Pipeline by Stage** — where deals sit today")
        stage_counts = df["stage"].value_counts().reindex([
            "SA Requested", "SA In Progress", "SA Delivered",
            "Proposal Sent", "Negotiating", "Closed Won", "Closed Lost", "Stalled"
        ]).fillna(0)
        fig = go.Figure(go.Bar(
            x=stage_counts.values,
            y=stage_counts.index,
            orientation="h",
            marker_color=[TEAL, TEAL, TEAL, SAGE, SAGE, "#16A34A", ROSE, AMBER],
            text=stage_counts.values,
            textposition="auto",
        ))
        fig.update_layout(
            height=320, margin=dict(l=0, r=0, t=10, b=10),
            xaxis_title="Count", yaxis_title="",
            plot_bgcolor=t["chart_bg"], paper_bgcolor=t["chart_paper"],
            font=dict(family="Inter, sans-serif", size=12, color=t["slate"]),
        )
        st.plotly_chart(fig, use_container_width=True)

    with chart_col_r:
        st.markdown("**Savings Opportunity by Stage** — $ at risk and won")
        savings_by_stage = df.groupby("stage").agg(
            opportunity=("identified_savings", lambda x: x.fillna(0).sum())
        ).reindex([
            "SA Delivered", "Proposal Sent", "Negotiating",
            "Closed Won", "Closed Lost", "Stalled"
        ]).fillna(0)
        fig = go.Figure(go.Bar(
            x=savings_by_stage.index,
            y=savings_by_stage["opportunity"],
            marker_color=[TEAL, SAGE, SAGE, "#16A34A", ROSE, AMBER],
            text=[f"${v/1000:.0f}K" for v in savings_by_stage["opportunity"]],
            textposition="auto",
        ))
        fig.update_layout(
            height=320, margin=dict(l=0, r=0, t=10, b=10),
            xaxis_title="", yaxis_title="$ savings identified",
            plot_bgcolor=t["chart_bg"], paper_bgcolor=t["chart_paper"],
            font=dict(family="Inter, sans-serif", size=12, color=t["slate"]),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ============================================================
    # HEAD OF MARKETING VIEW
    # ============================================================
    _section_header("📣", "Head of Marketing View",
                    "ICP signals, common objections, case-study fodder")

    mkt_col_l, mkt_col_r = st.columns([2, 1])

    with mkt_col_l:
        st.markdown("**Savings Opportunity by Specialty** — which segments are richest?")
        seg = pd.DataFrame(segment_savings_summary(pipeline))
        if not seg.empty:
            display = seg.rename(columns={
                "specialty": "Specialty",
                "prospects_analyzed": "Prospects Analyzed",
                "avg_savings_per_prospect": "Avg Savings / Prospect ($)",
                "avg_savings_pct": "Avg Savings %",
            })
            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Avg Savings / Prospect ($)": st.column_config.NumberColumn(format="$%d"),
                    "Avg Savings %": st.column_config.ProgressColumn(
                        format="%.1f%%", min_value=0, max_value=50
                    ),
                },
            )
            st.caption(
                "💡 **Marketing read:** specialties at the top of this list have the highest savings ratio. "
                "Build ICP-targeted ads and case-study assets around those specialties first."
            )

    with mkt_col_r:
        st.markdown("**Top Objections** — themes from review queue + sales notes")
        obj_list = common_objections(pipeline)
        if obj_list:
            obj_df = pd.DataFrame(obj_list)
            fig = go.Figure(go.Bar(
                x=obj_df["frequency"],
                y=obj_df["objection"],
                orientation="h",
                marker_color=t["amber"],
                text=obj_df["frequency"],
                textposition="auto",
            ))
            fig.update_layout(
                height=300, margin=dict(l=0, r=0, t=10, b=10),
                xaxis_title="# prospects", yaxis_title="",
                plot_bgcolor=t["chart_bg"], paper_bgcolor=t["chart_paper"],
                font=dict(family="Inter, sans-serif", size=11, color=t["slate"]),
            )
            st.plotly_chart(fig, use_container_width=True)

    # --- Case-study generator ---
    st.markdown("**📝 Case-Study Generator** — biggest savings wins this week")
    wins = sorted(
        [r for r in pipeline if r["stage"] == "Closed Won" and r["outcome_savings"]],
        key=lambda x: x["outcome_savings"], reverse=True
    )[:5]
    if wins:
        for win in wins:
            with st.expander(
                f"💰 ${win['outcome_savings']:,} saved · {win['locations']}-location {win['specialty'].lower()} practice in {win['state']}"
            ):
                st.markdown(f"""
**Anonymized case-study draft:**

> A {win['locations']}-location {win['specialty'].lower()} dental group in {win['state']} was spending
> approximately **\\${win['annual_supply_spend']:,}/year** on supplies across multiple distributors.
> After a SourceClub savings analysis, we identified **\\${win['outcome_savings']:,} in annual savings**
> ({win['savings_pct']}% reduction on the exact same product mix).
> They joined SourceClub on **{win['sa_date']}** — annualized MRR contribution: **\\${win['outcome_mrr']:,}/mo**.

*Source: {win['source']} · Rep: {win['rep']}*
                """)

    # ============================================================
    # HEAD OF SALES / REVENUE VIEW
    # ============================================================
    _section_header("💼", "Head of Sales/Revenue View",
                    "Active pipeline, ready-to-nudge prospects, AI-drafted outreach")

    # --- Per-rep throughput ---
    rep_col_l, rep_col_r = st.columns([2, 1])

    with rep_col_l:
        st.markdown("**Active Pipeline** — filter by rep and stage")
        rep_filter = st.multiselect("Rep", options=df["rep"].unique().tolist(),
                                    default=df["rep"].unique().tolist(),
                                    label_visibility="collapsed")
        active = df[df["rep"].isin(rep_filter) &
                    ~df["stage"].isin(["Closed Won", "Closed Lost"])].copy()
        active_display = active[[
            "company", "stage", "rep", "locations", "annual_supply_spend",
            "identified_savings", "savings_pct", "potential_mrr", "days_in_stage"
        ]].rename(columns={
            "company": "Practice",
            "stage": "Stage",
            "rep": "Rep",
            "locations": "Locs",
            "annual_supply_spend": "Annual Spend",
            "identified_savings": "$ Savings",
            "savings_pct": "Save %",
            "potential_mrr": "Potential MRR",
            "days_in_stage": "Days in Stage",
        })
        st.dataframe(
            active_display, use_container_width=True, hide_index=True, height=320,
            column_config={
                "Annual Spend": st.column_config.NumberColumn(format="$%d"),
                "$ Savings": st.column_config.NumberColumn(format="$%d"),
                "Potential MRR": st.column_config.NumberColumn(format="$%d"),
                "Save %": st.column_config.NumberColumn(format="%.1f%%"),
            },
        )

    with rep_col_r:
        st.markdown("**Per-Rep Throughput** — closed-won this period")
        rep_metrics = df[df["stage"] == "Closed Won"].groupby("rep").agg(
            wins=("company", "count"),
            mrr=("outcome_mrr", "sum"),
        ).reset_index()
        if not rep_metrics.empty:
            fig = go.Figure(go.Bar(
                x=rep_metrics["rep"],
                y=rep_metrics["wins"],
                marker_color=t["teal"],
                text=[f"{w} wins<br>${m:,.0f} MRR" for w, m in zip(rep_metrics["wins"], rep_metrics["mrr"])],
                textposition="outside",
            ))
            fig.update_layout(
                height=320, margin=dict(l=0, r=0, t=30, b=10),
                xaxis_title="", yaxis_title="Wins (MTD)",
                plot_bgcolor=t["chart_bg"], paper_bgcolor=t["chart_paper"],
                font=dict(family="Inter, sans-serif", size=12, color=t["slate"]),
            )
            st.plotly_chart(fig, use_container_width=True)

    # --- Ready to nudge ---
    st.markdown("**📨 Ready to Nudge** — SAs delivered, no movement in 7+ days")
    nudge_list = ready_to_nudge(pipeline)
    if not nudge_list:
        st.success("✓ No prospects need a nudge right now.")
    else:
        st.caption(f"{len(nudge_list)} prospects waiting. Click any row to draft a personalized follow-up email.")
        for idx, prospect in enumerate(nudge_list):
            with st.expander(
                f"📬 {prospect['company']} · ${prospect['identified_savings']:,} savings identified · "
                f"{prospect['days_in_stage']} days since SA delivered · Rep: {prospect['rep']}"
            ):
                col_l, col_r = st.columns([1, 1])
                with col_l:
                    st.markdown("**Prospect snapshot**")
                    st.text(f"Practice: {prospect['company']}")
                    st.text(f"Specialty: {prospect['specialty']}")
                    st.text(f"Locations: {prospect['locations']}")
                    st.text(f"State: {prospect['state']}")
                    st.text(f"Source: {prospect['source']}")
                    st.text(f"Annual spend: ${prospect['annual_supply_spend']:,}")
                    st.text(f"Identified savings: ${prospect['identified_savings']:,} ({prospect['savings_pct']}%)")
                with col_r:
                    if st.button("🤖 Draft follow-up email", key=f"draft_{idx}"):
                        email = draft_outreach_email(prospect)
                        st.session_state[f"email_{idx}"] = email
                    if f"email_{idx}" in st.session_state:
                        email = st.session_state[f"email_{idx}"]
                        st.markdown("**Drafted email (review and send):**")
                        st.text_input("Subject", value=email["subject"], key=f"subj_{idx}")
                        st.text_area("Body", value=email["body"], key=f"body_{idx}", height=220)
                        st.caption("💡 Production: this prompt runs through Claude Sonnet for higher-quality personalization. Current version uses a rule-based template clearly labeled as 'simulated.'")
