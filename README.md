# SourceClub Operations POC

Case study deliverable for the **Head of AI Powered Operations, Systems & RevOps** role.

A lean, runnable prototype built to be used by the **CEO, Head of Marketing, and Head of Sales/Revenue** — not just an analyst. Covers all three assignments:

1. **Savings Analysis Automation** — upload a prospect's supplier purchase history, get a matched savings report + branded PDF + AI-drafted follow-up email
2. **Stripe ↔ HubSpot Sync** — mock multi-location billing rollup demonstrating the canonical mapping table approach
3. **90-Day Roadmap** — prioritized project queue with dollar impact estimates, plus 10 proposed additions worth ~$1.1M/yr in aggregate

Plus a **Leadership Dashboard** (first tab) with three persona-targeted sections so each executive lands on the data they care about.

📄 **Full written submission:** [`SUBMISSION.md`](./SUBMISSION.md)
🎯 **Strategic addendum** (six-quarter growth thesis, unprompted): [`STRATEGIC_ADDENDUM.md`](./STRATEGIC_ADDENDUM.md)
🔒 **Security review:** [`SECURITY_REVIEW.md`](./SECURITY_REVIEW.md)
🏗️ **Production architecture:** [`PRODUCTION_ARCHITECTURE.md`](./PRODUCTION_ARCHITECTURE.md)
✉️ **Submission email draft:** [`SUBMISSION_EMAIL.md`](./SUBMISSION_EMAIL.md)

---

## Quick start (local)

Requires Python 3.10+.

```bash
git clone https://github.com/abhinaykrupa/sourceclub.git
cd sourceclub
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run app/main.py
```

The app opens at `http://localhost:8501`. Land on the **Leadership Dashboard**, then click into **Savings Analysis** and pick any sample file from the dropdown.

---

## What's inside

```
app/
  main.py                       Streamlit UI — four tabs (Dashboard, SA, Sync, Roadmap)
  views/
    dashboard.py                Leadership Dashboard (CEO / Marketing / Sales sections)
  engine/
    matcher.py                  3-stage matching engine + UOM/pack-size normalizer
    adapters/
      benco.py                  Benco purchase-history parser
      henry_schein.py           Henry Schein detailed-items report parser
      darby.py                  Darby order history parser
      base86.py                 Base86 export parser
      patterson.py              Patterson (handles messy real-world export)
      auto_detect.py            Supplier auto-detection
  sync/
    mock_data.py                Mock Stripe customers/subs + HubSpot companies/locations
    sync_engine.py              Canonical mapping + per-company billing rollup
    pipeline_data.py            Mock 45-prospect sales pipeline for the dashboard
  app_helpers/
    email_drafter.py            AI-drafted follow-up email generator (mocked LLM)
    pdf_generator.py            Branded PDF savings report (reportlab)
sample_data/
  sourceclub_catalog.csv        ~40-item SourceClub pricing catalog
  auburn_dental_benco.csv       Sample Benco export
  demit_dental_henry_schein.csv Sample Henry Schein export
  quincy_smiles_darby.csv       Sample Darby export
  auburn_dental_base86.csv      Sample Base86 export
  harbor_view_patterson_messy.csv  Sample Patterson — intentionally messy
.streamlit/config.toml          Healthcare blue/green theme (teal + sage)
SUBMISSION.md                   Full written deliverable for the recruiter
```

---

## Demo flow (90 seconds)

1. Open the app → **Tab 0: Leadership Dashboard**
   - See the three persona sections: CEO KPIs at top, Marketing in the middle, Sales at bottom
   - Pipeline by stage, savings by stage, per-rep throughput, ready-to-nudge list
   - In the Sales section, expand a "ready to nudge" prospect and click "🤖 Draft follow-up email"
2. Switch to **Tab 1: Savings Analysis**
   - From the sample dropdown, pick **"Auburn Dental (Benco)"**
   - Watch: file parsed → 3-stage matching → savings summary
   - Click **📄 Generate Branded PDF Report** → downloads a 2-page branded PDF
   - Click **🤖 Draft AI Follow-up Email** → personalized email appears
   - Try **"Patterson (messy real-world export)"** to see the engine handle chaos
3. **Tab 2** — pick "Sunrise Orthodontics" to see a multi-location billing rollup with health states
4. **Tab 3** — roadmap with dollar impact estimates per project

---

## Things to know

**The LLM calls are mocked.** Stage 3 (the LLM Judge) and the email drafter both use rule-based logic that mimics what Claude Haiku/Sonnet would return. The architecture is built so swapping in a real Anthropic API call is a one-function change. Mocked behavior is clearly labeled in the UI.

**The Stripe/HubSpot data is mocked.** Both platforms are simulated with realistic multi-location data. Production replaces these with API calls.

**The pipeline data (45 prospects in the dashboard) is fabricated** for demo purposes — deterministic so the dashboard looks identical each run.

**No API keys required.** The demo runs entirely offline.

**Scope:** POC, not production code. Demonstrates the pipeline shape and matching logic on representative data. See `SUBMISSION.md` for the production architecture and the production swap-in points.

---

## Tech choices and why

| Choice | Why |
|---|---|
| **Streamlit** | Fastest path to a runnable demo. Pure Python. Recruiter can install + run in 2 minutes. |
| **Plotly for charts** | Looks like a real product, not a hackathon. Works inside Streamlit without effort. |
| **reportlab for PDFs** | Pure Python, no system deps. Generates a real branded PDF the salesperson would actually send. |
| **Mocked LLM** | POC runs with zero setup. Architecture is API-ready — swap one function. Production prompt is in the code as a docstring. |
| **pandas only for matching** | No vector DB needed for the POC. Deterministic + fuzzy + token-overlap gets 70–85% match rate on this data, which is the right ballpark for human-in-the-loop. |
| **CSV samples (not Excel)** | Recruiters open CSVs in any tool. Easier to inspect than `.xlsx`. |
| **Healthcare-modern theme** | Teal + sage palette (à la One Medical / Forward). Signals "considered" without crossing into gimmicky. |

---

## Production-readiness gaps (intentionally out of POC scope)

Documented in detail in `SUBMISSION.md`. Short list:

- Real vector store (pgvector) for Stage 2 instead of fuzzy matching
- Real LLM API calls for Stage 3 + email drafter (Claude Haiku + Sonnet)
- Authentication, multi-tenant data isolation, audit log per matching decision
- Background job queue (Celery / RQ) for batch ingestion
- Stripe webhook handler + idempotent processing
- HubSpot API writer for custom properties
- Catalog versioning so historical reports remain reproducible
- Persistent review queue (POC buttons are illustrative — no state)
