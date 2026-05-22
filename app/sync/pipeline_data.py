"""
Mock sales pipeline data — 45 prospects in various stages.
In production this is read from HubSpot via the API.

Used by the Leadership Dashboard to render exec-facing views.
"""

from datetime import date, timedelta
import random

# Deterministic so the dashboard looks identical each run
random.seed(42)

REPS = ["Jake P.", "Sarah M.", "Maria L."]
SOURCES = ["Inbound — Web", "Outbound", "Referral", "Conference", "Partner"]
SPECIALTIES = ["General", "Pediatric", "Ortho", "Endo", "Perio", "Oral Surgery", "Cosmetic"]
STATES = ["CA", "TX", "NY", "FL", "IL", "OH", "PA", "GA", "WA", "MA", "AZ", "CO"]

STAGES = [
    "SA Requested",        # Prospect agreed to share purchase history
    "SA In Progress",      # Founder/analyst running the analysis
    "SA Delivered",        # Report sent to prospect
    "Proposal Sent",       # Pricing/agreement out
    "Negotiating",         # Active back-and-forth
    "Closed Won",          # Signed
    "Closed Lost",         # Lost
    "Stalled",             # No response 14+ days
]

# Distribution of stages (mid-funnel heavy, realistic)
STAGE_DISTRIBUTION = [
    ("SA Requested",   8),
    ("SA In Progress", 5),
    ("SA Delivered",   10),
    ("Proposal Sent",  7),
    ("Negotiating",    4),
    ("Closed Won",     6),
    ("Closed Lost",    3),
    ("Stalled",        2),
]


_PRACTICE_NAMES = [
    "Auburn Dental Group", "Demit Dental", "Quincy Smiles", "Bright Smiles Dental",
    "Coastal Family Dentistry", "Heritage Dental Associates", "Lakeside Smiles",
    "Premier Dental Care", "Sunset Dental Group", "Mountain View Dental",
    "Riverside Family Dental", "Oakwood Dental Arts", "Cedar Park Dentistry",
    "Willow Creek Dental", "Pine Valley Smiles", "Maple Street Dental",
    "Aspen Dental Studio", "Cypress Dental Group", "Magnolia Family Dentistry",
    "Bayview Dental Associates", "Hilltop Smiles", "Greenway Dental",
    "Crescent Dental Care", "Highland Park Dentistry", "Westshore Dental Group",
    "Sunnyside Pediatric Dental", "Briarcliff Family Dental", "Eastlake Smiles",
    "Crossroads Dental", "Parkside Dental Studio", "Beacon Hill Dentistry",
    "Foxhollow Dental", "Stonebridge Family Dental", "Larkspur Smiles",
    "Meridian Dental Group", "Northshore Dental Arts", "Trailhead Family Dentistry",
    "Vista Dental Associates", "Whispering Pines Dental", "Brookside Smiles",
    "Copper Ridge Dentistry", "Driftwood Dental", "Emerald Bay Dental Studio",
    "Falcon Crest Dental", "Glenwood Family Dental",
]


def _stages_list() -> list:
    """Flatten the stage distribution into a list of stage labels."""
    result = []
    for stage, count in STAGE_DISTRIBUTION:
        result.extend([stage] * count)
    return result


def _days_ago(n: int) -> str:
    return (date.today() - timedelta(days=n)).isoformat()


def build_pipeline():
    """
    Generate a mock sales pipeline of ~45 prospects with realistic distributions.
    Each row represents one prospect (one HubSpot company) with one in-flight
    savings analysis or recent outcome.
    """
    stages = _stages_list()
    random.shuffle(stages)

    rows = []
    for idx, name in enumerate(_PRACTICE_NAMES):
        stage = stages[idx % len(stages)]
        rep = REPS[idx % len(REPS)]
        source = SOURCES[idx % len(SOURCES)]
        specialty = SPECIALTIES[idx % len(SPECIALTIES)]
        state = STATES[idx % len(STATES)]
        locations = random.choices([1, 1, 1, 2, 2, 3, 4, 5, 8], k=1)[0]

        # Practice scale → annual supply spend
        # Single-location practice spends roughly $40-80K/yr on supplies
        # Multi-location scales sub-linearly (some shared inventory)
        base_spend = random.randint(40000, 80000)
        annual_spend = int(base_spend * (1 + 0.7 * (locations - 1)))
        identified_savings = int(annual_spend * random.uniform(0.18, 0.42))

        # Stage-dependent values
        days_in_stage = random.randint(1, 30)
        if stage == "Closed Won":
            outcome_savings = identified_savings
            mrr = 299 * locations
        elif stage == "Closed Lost":
            outcome_savings = 0
            mrr = 0
        else:
            outcome_savings = None
            mrr = None

        # SA date: when the analysis was run (or scheduled)
        if stage in ("SA Requested", "SA In Progress"):
            sa_date = None
        else:
            sa_date = _days_ago(days_in_stage + random.randint(0, 14))

        # Common objections — synthesized from review queue / sales conversations
        objection = None
        if stage in ("Closed Lost", "Stalled", "Negotiating"):
            objection = random.choice([
                "Already locked into 12-month supplier contract",
                "Price difference too small to justify switching",
                "Concerns about product availability/lead time",
                "Need to discuss with practice partners",
                "Worried about supplier exclusivity",
            ])

        rows.append({
            "company": name,
            "state": state,
            "specialty": specialty,
            "locations": locations,
            "rep": rep,
            "source": source,
            "stage": stage,
            "sa_date": sa_date or "—",
            "days_in_stage": days_in_stage,
            "annual_supply_spend": annual_spend,
            "identified_savings": identified_savings if stage not in ("SA Requested", "SA In Progress") else None,
            "savings_pct": round(identified_savings / annual_spend * 100, 1) if stage not in ("SA Requested", "SA In Progress") else None,
            "potential_mrr": 299 * locations,
            "outcome_savings": outcome_savings,
            "outcome_mrr": mrr,
            "objection": objection,
        })

    return rows


def segment_savings_summary(pipeline_rows: list) -> list:
    """Aggregate savings opportunity by specialty — used for the marketing view."""
    from collections import defaultdict
    by_spec = defaultdict(lambda: {"count": 0, "total_savings": 0, "total_spend": 0})
    for r in pipeline_rows:
        if r["identified_savings"]:
            by_spec[r["specialty"]]["count"] += 1
            by_spec[r["specialty"]]["total_savings"] += r["identified_savings"]
            by_spec[r["specialty"]]["total_spend"] += r["annual_supply_spend"]
    result = []
    for spec, vals in by_spec.items():
        pct = (vals["total_savings"] / vals["total_spend"] * 100) if vals["total_spend"] else 0
        result.append({
            "specialty": spec,
            "prospects_analyzed": vals["count"],
            "avg_savings_per_prospect": int(vals["total_savings"] / vals["count"]) if vals["count"] else 0,
            "avg_savings_pct": round(pct, 1),
        })
    return sorted(result, key=lambda x: x["avg_savings_per_prospect"], reverse=True)


def common_objections(pipeline_rows: list) -> list:
    """Count distinct objections — used for the marketing view."""
    from collections import Counter
    c = Counter(r["objection"] for r in pipeline_rows if r["objection"])
    return [{"objection": o, "frequency": n} for o, n in c.most_common()]


def ready_to_nudge(pipeline_rows: list) -> list:
    """Prospects whose SA was delivered but who haven't moved in 7+ days."""
    return [r for r in pipeline_rows
            if r["stage"] == "SA Delivered" and r["days_in_stage"] >= 7]
