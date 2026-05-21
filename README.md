# SourceClub Operations POC

Case study deliverable for the **Head of AI Powered Operations, Systems & RevOps** role.

A lean, runnable prototype covering all three assignments:

1. **Savings Analysis Automation** — upload a prospect's supplier purchase history, get a matched savings report with a human review queue
2. **Stripe ↔ HubSpot Sync** — mock multi-location billing rollup demonstrating the canonical mapping table approach
3. **90-Day Roadmap** — prioritized project queue with rationale, plus 10 proposed additions to the backlog

📄 **Full written submission:** see [`SUBMISSION.md`](./SUBMISSION.md)

---

## Quick start (local)

Requires Python 3.10+.

```bash
git clone <this-repo-url> sourceclub-poc
cd sourceclub-poc
pip install -r requirements.txt
streamlit run app/main.py
```

The app opens at `http://localhost:8501`. Go to **Tab 1**, select a sample file from the dropdown, and you'll see the pipeline run end-to-end.

---

## What's inside

```
app/
  main.py                       Streamlit UI — three tabs
  engine/
    matcher.py                  3-stage matching engine (deterministic → semantic → LLM judge)
    adapters/
      benco.py                  Benco purchase-history parser
      henry_schein.py           Henry Schein detailed-items report parser
      darby.py                  Darby order history parser
      base86.py                 Base86 export parser
      auto_detect.py            Supplier auto-detection from filename/header
  sync/
    mock_data.py                Mock Stripe customers/subs + HubSpot companies/locations
    sync_engine.py              Canonical mapping + per-company billing rollup
sample_data/
  sourceclub_catalog.csv        ~40-item SourceClub pricing catalog (mock negotiated prices)
  auburn_dental_benco.csv       Sample Benco export — Auburn Dental
  demit_dental_henry_schein.csv Sample Henry Schein export — Demit Dental
  quincy_smiles_darby.csv       Sample Darby export — Quincy Smiles
  auburn_dental_base86.csv      Sample Base86 export — Auburn Dental Group
SUBMISSION.md                   Full written deliverable for the recruiter
```

---

## Things to know

**The LLM calls are mocked.** Stage 3 (the LLM Judge) uses rule-based scoring with rationale generation that mimics what Claude Haiku would return. The architecture is built so swapping in a real Anthropic API call is a one-function change in `app/engine/matcher.py::stage3_llm_judge`. Mocked behavior is clearly labeled in the UI.

**The Stripe/HubSpot data is mocked.** Both platforms are simulated with realistic multi-location data in `app/sync/mock_data.py`. Production replaces these with API calls.

**No API keys required.** The demo runs entirely offline.

**Scope:** this is a POC, not production code. It demonstrates the pipeline shape and matching logic on a representative slice of data. See `SUBMISSION.md` for the production architecture and what would change.

---

## Demo flow (90 seconds)

1. Open the app → **Tab 1: Savings Analysis**
2. From the sample dropdown, pick **"Auburn Dental (Benco)"**
3. Watch: file parsed → 3-stage matching runs → savings summary appears
   - 30+ line items, ~$10K+ identified savings
   - Auto-accepted matches in green
   - 2–3 items flagged for human review (UOM mismatches, low confidence)
   - 2 items with no SC catalog equivalent
4. Expand a review-queue row to see the LLM rationale and approve/reject buttons
5. Switch to **Tab 2** to see the Stripe ↔ HubSpot multi-location rollup
6. **Tab 3** lays out the 90-day project sequence + proposed additions

---

## Tech choices and why

| Choice | Why |
|---|---|
| **Streamlit** | Fastest path to a runnable demo. Pure Python. Recruiter can `pip install` and run, or open the deployed URL. |
| **Mocked LLM** | POC must run with zero setup. Architecture is API-ready — swap one function. |
| **pandas only** | No vector DB, no ML libraries needed for the POC. Deterministic + fuzzy + token-overlap gets 70–85% match rate on this data, which is the right ballpark for human-in-the-loop. |
| **CSV samples (not Excel)** | Recruiters open CSVs in any tool. Easier to inspect than `.xlsx`. |
| **3-stage matching mirrors production** | Each stage is an independent function. Stage 3 (`stage3_llm_judge`) is the only one that becomes an API call in prod; everything else stays as-is. |

---

## Production-readiness gaps (intentionally out of scope for POC)

Documented in detail in `SUBMISSION.md`. Short list:

- Real vector store (pgvector) for Stage 2 instead of fuzzy matching
- Real LLM API call for Stage 3 (Claude Haiku with structured JSON output)
- Authentication, multi-tenant data isolation
- Audit log of every matching decision
- Background job queue for batch ingestion (Celery / RQ)
- Stripe webhook handler + idempotent processing
- HubSpot API writer for the custom properties
- Catalog versioning so historical reports remain reproducible
