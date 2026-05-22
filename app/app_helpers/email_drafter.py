"""
AI-drafted prospect follow-up email generator.

MOCKED in the POC. Production replaces draft_outreach_email() with a Claude
Sonnet call using the prompt below. The mock generates output that is
structurally and tonally what the real model would return.
"""


PRODUCTION_PROMPT_TEMPLATE = """
You are a SourceClub sales rep drafting a personalized follow-up email after
delivering a savings analysis to {practice_name}, a {locations}-location {specialty}
practice in {state}.

Their identified annual savings: ${identified_savings:,} ({savings_pct}% of current
${annual_spend:,} supply budget).

Top savings categories: {top_categories}.

Draft a 4-paragraph email with:
- Subject line that hooks on a specific savings number
- Greeting that references the practice's specialty
- One concrete "did you know" insight tied to their savings
- Soft CTA suggesting a 15-minute call
- Tone: confident but not pushy. SOURCE CLUB style: short paragraphs, direct.

Return JSON: {{ "subject": ..., "body": ... }}
""".strip()


def _top_savings_categories(prospect: dict) -> list:
    """
    For the mock, return plausible top categories based on annual spend tier.
    Production: derive from the actual SA result detail.
    """
    spend = prospect.get("annual_supply_spend", 50000)
    if spend > 100000:
        return ["anesthetics", "PPE", "composites"]
    elif spend > 60000:
        return ["PPE", "consumables", "burs"]
    else:
        return ["PPE", "consumables"]


def draft_outreach_email(prospect: dict) -> dict:
    """
    Generate a personalized follow-up email for a prospect.

    Args:
        prospect: dict with keys: company, locations, specialty, state, rep,
                  identified_savings, savings_pct, annual_supply_spend, source

    Returns:
        {"subject": str, "body": str}
    """
    practice = prospect.get("company", "your practice")
    locations = prospect.get("locations", 1)
    specialty = prospect.get("specialty", "general").lower()
    state = prospect.get("state", "")
    rep = prospect.get("rep", "Jake")
    savings = prospect.get("identified_savings", 0)
    pct = prospect.get("savings_pct", 0)
    spend = prospect.get("annual_supply_spend", 0)
    top_cats = _top_savings_categories(prospect)

    location_phrase = "your practice" if locations == 1 else f"all {locations} of your locations"
    specialty_hook = {
        "general": "general-practice supply mix",
        "pediatric": "high-volume preventive and consumable spend that pediatric practices carry",
        "ortho": "ortho-specific brackets, wires, and elastics — a category where independent buying power is rare",
        "endo": "endo files, irrigants, and obturation materials — typically a high-markup category",
        "perio": "perio surgical and maintenance supply categories",
        "oral surgery": "oral-surgery anesthetics and surgical disposables",
        "cosmetic": "cosmetic composites, bonding agents, and lab consumables",
    }.get(specialty, "supply mix")

    if locations == 1:
        social_proof = "Most single-location practices in our network save in the $8K–$25K range; you're solidly in that band."
    elif locations <= 3:
        social_proof = f"Most {locations}-location groups we work with save in the $30K–$70K range — your numbers line up."
    else:
        social_proof = f"For {locations}+ location groups, savings scale meaningfully — yours is a typical upper-band outcome."

    cats_phrase = ", ".join(top_cats[:-1]) + f", and {top_cats[-1]}" if len(top_cats) > 1 else top_cats[0]

    subject = f"Quick follow-up — your ${savings:,} savings analysis"

    body = f"""Hi there,

Wanted to circle back on the savings analysis we put together for {practice} last week.

The short version: we identified **${savings:,} in annual savings** ({pct}% off your current ${spend:,} supply budget), driven mostly by {cats_phrase}. That's on the exact same product mix you're buying today — same manufacturers, same pack sizes — just at SourceClub negotiated pricing.

One thing that stood out for {location_phrase}: you're carrying meaningful spend on {specialty_hook}, which is exactly where our negotiated rates run deepest. {social_proof}

If you want to walk through the line-item breakdown, I'm happy to grab 15 minutes this week or next. No pressure — but the longer we wait, the more savings keep sitting on the table each month.

Happy to send the full audit report ahead of the call if that helps.

Best,
{rep}
SourceClub
"""

    return {"subject": subject, "body": body}
