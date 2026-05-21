# SourceClub Case Study: Head of AI Powered Operations & Systems
**Candidate:** Abhi
**Date:** May 21, 2026

---

## Executive Summary
SourceClub is an AI-forward operator in the dental GPO space. My approach to these assignments is centered on **shipping pragmatic, reliable systems** that create a trustworthy data layer and unblock revenue. I prioritize reducing manual bottlenecks (Savings Analysis) and building a durable data spine (Stripe/HubSpot) to enable a lean team of 7 to operate at scale.

---

## Assignment 1 — “Savings Analysis” Automation

### The Strategy: Pragmatic Human-in-the-Loop Matching
Matching product data across disparate suppliers is a semantic reasoning problem, not just a data cleaning one. I propose a 3-stage matching pipeline that prioritizes speed and precision.

#### 1. The Architecture
| Layer | Description | Tools |
|---|---|---|
| **Intake** | Accept PDF/CSV exports; identify source supplier; normalize headers. | Make.com, Python, Claude (OCR) |
| **Canonicalization** | Standardize SKU, Mfg, UOM, Pack Size, and Unit Price. | Python (Pandas), Regex |
| **Match Engine** | 3-stage logic (Deterministic -> Semantic -> LLM Judge). | pgvector, Claude 3.5 Haiku |
| **Human Review** | Route low-confidence/high-spend mismatches to a queue. | Retool or Notion DB |
| **Output** | Generate savings report + audit trail for prospect. | HubSpot, PDF Generator |

#### 2. The 3-Stage Match Logic
1.  **Deterministic:** Exact match on Supplier SKU or Manufacturer SKU.
2.  **Semantic Retrieval:** Use Vector Embeddings (pgvector) to pull the top 5 catalog candidates based on description similarity.
3.  **LLM Judge:** A fast LLM (Claude Haiku) adjudicates the top candidates, forcing a structured JSON output that accounts for UOM differences (e.g., "box" vs "case").

#### 3. Confidence Policy
- **High Confidence (>90%):** Auto-accept into report.
- **Medium Confidence:** Include but flag for "Review Suggested."
- **Low Confidence / High Spend:** Force human review in the Retool/Notion queue.

**POC Reference:** See `case_study/assignment_1/savings_analysis_poc_v2.py` for a functional 3-stage pipeline demonstration.

---

## Assignment 2 — Systems Architecture: Stripe ↔ HubSpot

### The Challenge: Many-Locations-to-One-Company
Stripe bills per location (subscription), while HubSpot tracks the parent entity (company). Native integrations fail here because they lack the canonical mapping required for multi-location groups.

### The Recommendation: Custom Sync + Durable Mapping Logic
I recommend building a **Custom Sync Service** with a dedicated mapping table to act as the "Data Spine."

#### 1. The Data Model
- **HubSpot Company:** Parent dental group.
- **HubSpot Locations (Custom Object):** Individual practice records.
- **Stripe Customer:** Parent bill-to entity.
- **Stripe Subscription:** One subscription = One location membership.

#### 2. Implementation Plan
1.  **Mapping Table:** Build a canonical SQL table (or Airtable/Notion) mapping `Stripe_Sub_ID` ↔ `HubSpot_Location_ID` ↔ `HubSpot_Company_ID`.
2.  **Webhooks:** Deploy a service (AWS Lambda or specialized Make.com scenario) to listen for Stripe `subscription.updated` and `invoice.paid` events.
3.  **HubSpot Write:** Push a normalized billing snapshot into HubSpot Company properties:
    - `Active Subscription Count`
    - `Total MRR / ARR`
    - `Billing Health Status` (Green/Yellow/Red)
    - `Last Paid Date`

#### 3. Why this wins
This approach handles the multi-location reality of SourceClub’s members and creates the "trustworthy data layer" needed for the automated dashboards and health scoring mentioned in the project queue.

---

## Assignment 3 — Prioritizing the 90-Day Roadmap

I prioritize projects based on **dependencies and revenue leverage**, not just urgency.

| Order | Project | Strategic Rationale |
|---|---|---|
| **1** | **Automate Savings Analysis (2.1)** | **P0.** The single biggest revenue bottleneck. Automating this doubles sales throughput immediately. |
| **2** | **Stripe ↔ HubSpot Name Matching (1.1)** | **P0.** Foundational. You cannot scale billing or success without a clean connection between money (Stripe) and people (HubSpot). |
| **3** | **Consolidate CS into HubSpot (3.1)** | **P1.** Operational Control. Moving off fragmented email/slack into a ticketing queue allows for team measurement and prevents churn. |
| **4** | **Post-Onboarding Drip Campaign (3.8)** | **P1.** Quick Win. Improves activation and "Time to Value" for new members. |
| **5** | **ZenOne Data Integration (1.2)** | **P2.** Strategic Backbone. Unlocks true customer health scoring and lifecycle automation in Phase 2. |

---

## Appendix

### Assumptions
- SourceClub is willing to use intermediate tools (Make/Retool) to speed up implementation before moving to fully custom code.
- The "Master Catalog" of pricing is accessible via API or regular CSV export.

### Open Questions
- What is the current "Match Rate" for the manual process? (Goal: exceed this with AI).
- How are "Multi-Location" groups currently identified in HubSpot—is there a shared domain or unique parent ID?
