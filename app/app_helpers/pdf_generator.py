"""
Branded PDF savings report generator.

In production, this PDF is what the salesperson sends to the prospect after
running the savings analysis. It's a 2-page report: cover + line-item detail.
"""

import io
from datetime import date

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)


TEAL = colors.HexColor("#0EA5A1")
SAGE = colors.HexColor("#10B981")
SLATE = colors.HexColor("#0F172A")
LIGHT_BG = colors.HexColor("#F0F9F8")
MUTED = colors.HexColor("#64748B")
WHITE = colors.HexColor("#FFFFFF")


def _styles():
    base = getSampleStyleSheet()
    return {
        "title":  ParagraphStyle("title", parent=base["Title"], fontSize=28,
                                 textColor=SLATE, alignment=TA_LEFT,
                                 spaceAfter=4, fontName="Helvetica-Bold"),
        "tag":    ParagraphStyle("tag", parent=base["Normal"], fontSize=10,
                                 textColor=TEAL, alignment=TA_LEFT,
                                 spaceAfter=18, fontName="Helvetica-Bold"),
        "h2":     ParagraphStyle("h2", parent=base["Heading2"], fontSize=14,
                                 textColor=SLATE, spaceAfter=8, spaceBefore=16,
                                 fontName="Helvetica-Bold"),
        "body":   ParagraphStyle("body", parent=base["Normal"], fontSize=10,
                                 textColor=SLATE, leading=14, spaceAfter=6),
        "small":  ParagraphStyle("small", parent=base["Normal"], fontSize=8,
                                 textColor=MUTED, leading=11),
        "metric_label": ParagraphStyle("ml", parent=base["Normal"], fontSize=10,
                                       textColor=MUTED, alignment=TA_CENTER),
        "metric_value": ParagraphStyle("mv", parent=base["Normal"], fontSize=22,
                                       textColor=SLATE, alignment=TA_CENTER,
                                       fontName="Helvetica-Bold", spaceAfter=2),
        "metric_value_green": ParagraphStyle("mvg", parent=base["Normal"], fontSize=22,
                                             textColor=SAGE, alignment=TA_CENTER,
                                             fontName="Helvetica-Bold", spaceAfter=2),
    }


def _brand_header():
    """Returns a Table representing the SourceClub header band."""
    cell = Paragraph(
        '<font name="Helvetica-Bold" color="#FFFFFF" size="16">SourceClub</font>'
        '<font color="#FFFFFF" size="11">  ·  Dental Group Purchasing</font>',
        getSampleStyleSheet()["Normal"]
    )
    t = Table([[cell]], colWidths=[7.0 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), TEAL),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    return t


def _kpi_row(total_spend, projected_spend, total_savings, savings_pct, styles):
    """3-column KPI strip on the cover page."""
    def cell(label, value, style_key):
        return [
            Paragraph(label, styles["metric_label"]),
            Spacer(1, 2),
            Paragraph(value, styles[style_key]),
        ]

    data = [[
        cell("Current Annual Spend",   f"${total_spend:,.0f}",       "metric_value"),
        cell("With SourceClub",        f"${projected_spend:,.0f}",   "metric_value"),
        cell("Estimated Savings",      f"${total_savings:,.0f}",     "metric_value_green"),
    ]]

    t = Table(data, colWidths=[2.33 * inch, 2.33 * inch, 2.33 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 18),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
        ("BOX", (0, 0), (-1, -1), 1, LIGHT_BG),
    ]))

    pct_para = Paragraph(
        f'<para alignment="center"><font color="#0F766E" size="11">'
        f'<b>{savings_pct:.1f}% reduction</b> on the same product mix</font></para>',
        styles["body"]
    )

    return [t, Spacer(1, 6), pct_para]


def generate_savings_pdf(results_df, customer_name: str, supplier_name: str, period: str = "Last 12 months") -> bytes:
    """
    Build a branded PDF savings report.

    Args:
        results_df: DataFrame from matcher.match_invoice()
        customer_name, supplier_name, period: report metadata

    Returns:
        PDF bytes ready for st.download_button or file save.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=LETTER,
        leftMargin=0.6 * inch, rightMargin=0.6 * inch,
        topMargin=0.6 * inch, bottomMargin=0.5 * inch,
        title="SourceClub Savings Analysis",
        author="SourceClub",
    )
    s = _styles()

    # Compute totals
    total_spend = float(results_df["annual_spend"].sum())
    total_savings = float(results_df["total_savings"].fillna(0).sum())
    projected_spend = total_spend - total_savings
    savings_pct = (total_savings / total_spend * 100) if total_spend > 0 else 0

    # Top savings items (matched only)
    matched = results_df[results_df["total_savings"].notna() & (results_df["total_savings"] > 0)].copy()
    matched = matched.sort_values("total_savings", ascending=False).head(15)

    # No-match items
    no_match = results_df[results_df["status"] == "NO-MATCH"]

    # Status counts
    n_auto = (results_df["status"] == "AUTO-ACCEPT").sum()
    n_review = results_df["status"].isin(["REVIEW-SUGGESTED", "FORCE-REVIEW"]).sum()
    n_nomatch = (results_df["status"] == "NO-MATCH").sum()

    story = []

    # ---- Header ----
    story.append(_brand_header())
    story.append(Spacer(1, 24))

    # ---- Cover content ----
    story.append(Paragraph("Savings Analysis Report", s["title"]))
    story.append(Paragraph(f"Prepared for {customer_name}", s["tag"]))

    meta_data = [
        [Paragraph(f"<b>Source supplier:</b> {supplier_name}", s["body"]),
         Paragraph(f"<b>Report date:</b> {date.today().isoformat()}", s["body"])],
        [Paragraph(f"<b>Analysis period:</b> {period}", s["body"]),
         Paragraph(f"<b>Items analyzed:</b> {len(results_df)}", s["body"])],
    ]
    meta_table = Table(meta_data, colWidths=[3.5 * inch, 3.5 * inch])
    meta_table.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 18))

    # ---- KPI cards ----
    story.extend(_kpi_row(total_spend, projected_spend, total_savings, savings_pct, s))
    story.append(Spacer(1, 18))

    # ---- Headline narrative ----
    story.append(Paragraph("The opportunity", s["h2"]))
    story.append(Paragraph(
        f"Based on {len(results_df)} line items from your {supplier_name} purchase history, "
        f"SourceClub identified <b>${total_savings:,.0f} in annual savings</b> "
        f"({savings_pct:.1f}% of your current ${total_spend:,.0f} supply budget). "
        f"This is on the same product mix you're buying today — same manufacturers, "
        f"same pack sizes — just at SourceClub negotiated pricing.",
        s["body"]
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"<b>{n_auto}</b> items matched automatically via SKU. "
        f"<b>{n_review}</b> items flagged for analyst review (typically UOM or pack-size verification). "
        f"<b>{n_nomatch}</b> items have no SourceClub equivalent yet — these are catalog-gap "
        f"opportunities we add to our quarterly supplier negotiations.",
        s["body"]
    ))

    # ---- Page 2: line-item detail ----
    story.append(PageBreak())
    story.append(_brand_header())
    story.append(Spacer(1, 18))

    story.append(Paragraph("Top 15 line items by savings", s["h2"]))
    story.append(Paragraph(
        "Ranked by total annual savings. Full line-item audit available on request.",
        s["small"]
    ))
    story.append(Spacer(1, 8))

    # Build table
    header = ["Item", "Current $", "SC $", "Save %", "Annual Save"]
    table_data = [header]
    for _, row in matched.iterrows():
        desc = str(row["raw_description"])[:55]
        cur = float(row["current_unit_price"])
        sc = float(row["sc_unit_price"])
        pct = float(row["savings_pct"] or 0)
        sav = float(row["total_savings"])
        table_data.append([
            desc,
            f"${cur:.2f}",
            f"${sc:.2f}",
            f"{pct:.0f}%",
            f"${sav:,.0f}",
        ])

    line_table = Table(table_data, colWidths=[3.5*inch, 0.8*inch, 0.8*inch, 0.7*inch, 1.0*inch])
    line_table.setStyle(TableStyle([
        # header
        ("BACKGROUND", (0, 0), (-1, 0), TEAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        # body
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("TEXTCOLOR", (0, 1), (-1, -1), SLATE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("LINEBELOW", (0, 0), (-1, 0), 1, TEAL),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(line_table)

    # ---- Catalog gap section ----
    if len(no_match) > 0:
        story.append(Spacer(1, 18))
        story.append(Paragraph("Items not currently in our catalog", s["h2"]))
        story.append(Paragraph(
            f"These {len(no_match)} items don't yet have a SourceClub equivalent. "
            f"We track these as 'catalog gap' opportunities and prioritize them in "
            f"quarterly supplier negotiations.",
            s["small"]
        ))
        story.append(Spacer(1, 6))
        gap_data = [["Item", "Current Annual Spend"]]
        for _, row in no_match.head(5).iterrows():
            gap_data.append([
                str(row["raw_description"])[:60],
                f"${row['annual_spend']:,.0f}",
            ])
        gap_table = Table(gap_data, colWidths=[5.5*inch, 1.3*inch])
        gap_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), MUTED),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(gap_table)

    # ---- Footer / methodology ----
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "<b>How we matched these items.</b> Every line in your purchase history is run "
        "through a 3-stage matching engine: exact SKU match, semantic description match, "
        "and LLM adjudication for ambiguous cases. Unit-of-measure and pack-size are "
        "verified independently. Low-confidence matches and pack-size mismatches are "
        "routed to a SourceClub analyst for human review before this report is sent. "
        "Full per-line audit trail is available on request.",
        s["small"]
    ))

    doc.build(story)
    return buf.getvalue()
