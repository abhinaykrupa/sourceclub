"""
Simulates the Stripe → HubSpot sync engine.
Production: this runs as a webhook handler + nightly batch job.
"""

import pandas as pd
from .mock_data import (
    STRIPE_CUSTOMERS, STRIPE_SUBSCRIPTIONS,
    HUBSPOT_COMPANIES, HUBSPOT_LOCATIONS, MAPPING_TABLE
)


def build_company_billing_snapshot() -> pd.DataFrame:
    """
    Aggregate Stripe subscriptions up to the HubSpot Company level.
    This is what gets written to HubSpot custom properties in production.
    """
    subs = pd.DataFrame(STRIPE_SUBSCRIPTIONS)
    mapping = pd.DataFrame(MAPPING_TABLE)
    companies = pd.DataFrame(HUBSPOT_COMPANIES)
    locations = pd.DataFrame(HUBSPOT_LOCATIONS)

    merged = mapping.merge(subs, on="stripe_sub_id", suffixes=("", "_stripe"))
    merged = merged.merge(
        locations[["hs_location_id", "name"]].rename(columns={"name": "location_name"}),
        on="hs_location_id"
    )

    grouped = merged.groupby("hs_company_id").agg(
        total_locations=("hs_location_id", "count"),
        active_subscriptions=("status", lambda x: (x == "active").sum()),
        past_due_count=("past_due", "sum"),
        canceled_count=("status", lambda x: (x == "canceled").sum()),
        total_mrr=("mrr", "sum"),
    ).reset_index()

    grouped["total_arr"] = grouped["total_mrr"] * 12
    grouped["billing_health"] = grouped.apply(_health_status, axis=1)

    result = companies.merge(grouped, on="hs_company_id", how="left")
    result = result.fillna(0)
    return result


def build_location_detail(hs_company_id: str) -> pd.DataFrame:
    """Return per-location billing breakdown for a given company."""
    subs = pd.DataFrame(STRIPE_SUBSCRIPTIONS)
    mapping = pd.DataFrame(MAPPING_TABLE)
    locations = pd.DataFrame(HUBSPOT_LOCATIONS)

    filtered = mapping[mapping["hs_company_id"] == hs_company_id]
    merged = filtered.merge(subs, on="stripe_sub_id")
    merged = merged.merge(
        locations[["hs_location_id", "name"]].rename(columns={"name": "location_name"}),
        on="hs_location_id"
    )
    return merged[["location_name", "stripe_sub_id", "status", "mrr", "plan", "current_period_end", "past_due"]].reset_index(drop=True)


def get_unmapped_stripe_customers() -> list:
    """Find Stripe customers not yet in the mapping table — these go to exception queue."""
    mapped_customers = {m["stripe_customer_id"] for m in MAPPING_TABLE}
    return [c for c in STRIPE_CUSTOMERS if c["stripe_customer_id"] not in mapped_customers]


def _health_status(row) -> str:
    if row["past_due_count"] > 0:
        return "🔴 At Risk"
    if row["canceled_count"] > 0 and row["active_subscriptions"] > 0:
        return "🟡 Partial"
    if row["active_subscriptions"] == 0:
        return "⚫ Churned"
    return "🟢 Healthy"
