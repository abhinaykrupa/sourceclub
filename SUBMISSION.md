# SourceClub Case Study — Final Submission

**Candidate:** Abhi
**Role:** Head of AI Powered Operations, Systems & RevOps
**Submitted:** May 21, 2026

---

## TL;DR

Three deliverables, one repo, one demo URL.

- **Assignment 1:** Working POC that auto-detects supplier (Benco / Henry Schein / Darby / Base86), parses the file, runs a 3-stage matching engine with UOM/pack-size verification, and produces a savings report with a human review queue.
- **Assignment 2:** Recommended **custom sync + canonical mapping table** over native or middleware-only options. Mocked end-to-end in the POC, showing per-company billing rollup and per-location drill-down.
- **Assignment 3:** Prioritized the existing queue by **dependency, not urgency** (savings analysis → Stripe sync → CS consolidation → drip → ZenOne). Added 10 net-new projects I'd push into the backlog.

The whole thing runs locally with `pip install` + `streamlit run`. See `README.md` for install steps.

---

## Assignment 1 — Savings Analysis Automation

### What I built

A working pipeline you can drive end-to-end in the UI:

```
Upload → Auto-detect Supplier → Adapter (per-supplier parser) → Canonical Schema
   ↓
3-Stage Matching Engine (per line item):
   Stage 1: Deterministic — exact match on Mfg SKU / Supplier SKU
   Stage 2: Semantic Retrieval — top-K candidates by description similarity
   Stage 3: LLM Judge — adjudicates candidates, generates rationale, scores confidence
   Cross-cut: UOM/Pack-size Normalizer — flags "box vs case" style mismatches
   ↓
Confidence Router:
   ≥ 0.85 → Auto-Accept → Savings Report
   0.60–0.85 → Review Queue (human approves/overrides)
   UOM mismatch → Force Review (regardless of confidence)
   High $ + medium conf → Force Review
   < 0.60 → No-Match bucket (feeds catalog gap analysis for procurement)
   ↓
Output: Savings Report + Audit CSV
```

### Why this design

**Three stages instead of one** because the failure modes are different:
- Stage 1 catches the easy ~30–40% (clean SKU matches) at zero LLM cost.
- Stage 2 narrows the candidate space — an LLM judging 500 catalog items per line is wasteful and noisy.
- Stage 3 is where reasoning happens (UOM normalization, manufacturer disambiguation).

**Supplier adapters before matching** because the training videos make it clear: every supplier (Benco, Henry Schein, Darby, Base86) exports a different shape. Without adapters, you're trying to match across schemas, which is where the manual VLOOKUP pain comes from today.

**UOM/pack-size detection as its own concern.** This was the single most-called-out failure mode in the videos. "Box of 100" vs "case of 10 boxes" matters more than fuzzy description scoring. I parse pack hints from descriptions (`100/bx`, `2000/cs`, `box of 50`) and from explicit UOM columns (Darby has one), then compare against catalog metadata. Mismatches force human review — even when description and manufacturer both align — because the unit-economics math breaks otherwise.

**Human-in-the-loop is the spec, not a fallback.** The training material talks about 5–7 hrs/mo of manual work. Replacing 100% of that requires perfect matching; replacing 80% requires good matching with a review path. The right target is the latter — the queue UI in Tab 1 shows what reviewer experience looks like.

### What's mocked vs production-ready

| Component | POC | Production |
|---|---|---|
| Supplier adapters | ✅ Production-shaped (per-supplier modules) | Same code, expanded for edge cases + more suppliers |
| Stage 1 deterministic | ✅ Real | Same |
| Stage 2 semantic | difflib + token overlap | **pgvector** with `sentence-transformers/all-MiniLM-L6-v2` embeddings |
| Stage 3 LLM judge | Rule-based mock with rationale generation | **Claude Haiku** with structured JSON output (forces matched_sku, confidence, uom_alignment, rationale fields) |
| UOM normalization | ✅ Real (regex + alias table) | Same + learned synonyms from reviewer corrections |
| Review queue | Approve/Reject buttons (no persistence) | **Retool** front-end on the canonical DB |
| Catalog | CSV, ~40 items | Postgres table, versioned per analysis run |

**Production stage-3 prompt sketch** (Claude Haiku):

```
You are matching dental supply line items from a prospect to SourceClub's pricing catalog.

PROSPECT LINE:
  Description: {raw_description}
  Manufacturer: {manufacturer_name}  Mfg SKU: {manufacturer_sku}
  Quantity: {quantity}  Unit price: ${unit_price}

TOP 5 CATALOG CANDIDATES (from vector retrieval):
  {numbered_candidates_with_full_metadata}

Return JSON only:
{
  "best_match_sc_sku": string | null,
  "confidence": 0.0–1.0,
  "uom_alignment": "aligned" | "mismatch" | "unknown",
  "rationale": "1–2 sentence explanation"
}
```

### What I'd do next with more time

1. **Real embeddings + pgvector.** Replace the difflib stage with a proper vector store. Embed once at catalog ingest, query at match time. ~2 days.
2. **Reviewer feedback loop.** Every approve/reject in the queue writes a labeled pair (`prospect_desc → sc_sku`) into a "matching memory" table. Use it to bias future Stage-2 retrieval. The system gets smarter per analysis run.
3. **Supplier API integrations.** Skip the manual export step entirely for Benco and Henry Schein (they both have REST APIs). One less click in the workflow, real-time data, no analyst touching the supplier portal.
4. **Catalog drift monitor.** Daily diff supplier prices vs SC negotiated rates. Alert when any item shifts >5%. Protects the integrity of every report we've already sent.
5. **Self-serve prospect portal.** Today the salesperson runs the analysis; eventually the prospect uploads their own file and sees the savings report inside a branded landing page. Drops sales-cycle time materially.

### Demo

Open the app → **Tab 1** → pick **"Demit Dental (Henry Schein)"** from the sample dropdown. ~$33K annual spend, ~30 items, you'll see roughly half auto-matched, several routed to review queue (including UOM mismatches), and 2–3 unmatched items going to the catalog-gap bucket.

---

## Assignment 2 — Stripe ↔ HubSpot Sync

### The problem

Stripe bills per location (one subscription = one practice). HubSpot organizes around the Company (parent dental group). Today: nobody on the team can open a Company in HubSpot and see its billing health without manually cross-referencing Stripe. That blocks:

- Sales seeing if a prospect's existing locations are paying on time
- CS knowing which Companies have past-due locations (early churn signal)
- Finance pulling a clean MRR/ARR view sliced by Company

### Three options I considered

| Option | Cost | Pros | Cons | Verdict |
|---|---|---|---|---|
| **Native Stripe-HubSpot integration** | $0 (included) | Zero setup | Syncs to Deals/Invoices, not the Company record. No multi-location rollup. Can't aggregate MRR across subs. | ❌ |
| **Middleware only (Make / Zapier)** | $30–50/mo | Visual, fast to MVP, low-code | Brittle for backfills + audits. Mapping logic spread across scenarios — hard to debug. Per-task pricing scales linearly with volume. | ⚠️ Stopgap only |
| **Custom sync + canonical mapping table** | ~1 dev-week build, ~$0 ongoing infra | Owns the data spine. Auditable. Handles multi-location reality natively. Same spine serves customer health score (3.5) and ZenOne integration (1.2) downstream. | More upfront work. Maintenance is on us. | ✅ **Pick this** |

### The chosen design

**Three layers:**

```
┌─────────────────────────────────────────────────────────┐
│  STRIPE                                                 │
│   • customer.created, customer.updated                  │
│   • subscription.created, .updated, .canceled           │
│   • invoice.paid, invoice.payment_failed                │
└────────────────┬────────────────────────────────────────┘
                 │ webhooks (real-time)
                 ▼
┌─────────────────────────────────────────────────────────┐
│  SYNC SERVICE                                           │
│   • Webhook handler (idempotent)                        │
│   • Canonical mapping table:                            │
│       stripe_sub_id ↔ stripe_customer_id                │
│       ↔ hs_location_id ↔ hs_company_id                  │
│   • Aggregator: per-Company billing rollup              │
│   • Exception queue: unmapped customers                 │
└────────────────┬────────────────────────────────────────┘
                 │ HubSpot API (writes custom properties)
                 ▼
┌─────────────────────────────────────────────────────────┐
│  HUBSPOT                                                │
│   Company custom properties (updated near-real-time):   │
│     • billing_status (Healthy / At Risk / Churned)      │
│     • total_mrr, total_arr                              │
│     • active_subscription_count                         │
│     • past_due_count                                    │
│     • last_invoice_paid_date                            │
│   Location object: per-location subscription detail     │
└─────────────────────────────────────────────────────────┘
```

**The canonical mapping table is the asset.** Everything else (webhooks, aggregator, writer) is plumbing. Once that table exists, the same join logic powers:
- This billing dashboard (Assignment 2)
- The customer health score (Project 3.5)
- The ZenOne ordering data join (Project 1.2)
- Any future "give me MRR by Company" SQL query

### Implementation steps

1. Build the mapping table in Postgres. Backfill from current data (fuzzy match Stripe customer names against HubSpot Company names, then one-time human reconcile of unmatched).
2. Stand up a small Python service (FastAPI on Render or AWS Lambda + API Gateway). Endpoint: `POST /stripe-webhook`.
3. Wire Stripe webhooks for `subscription.*`, `invoice.*`, `customer.updated`.
4. On each event: look up mapping → recompute the affected Company's rollup → push to HubSpot custom properties via API.
5. Nightly reconciliation job: scans for drift between Stripe and the mapping table, flags new unmapped customers to the exception queue.
6. Build a simple Retool view of the exception queue so CS/Ops can resolve unmapped customers in minutes (not the hours it takes today).

**Cost:** one engineer-week to build, then maintenance only. Infrastructure ~$0 (free tier of Render/Lambda handles this volume). The middleware-only option costs more *per year* and gives less control.

### Why this wins long term

Three reasons:

1. **It fits the actual data model.** A custom build can express "company has many locations, each location has one subscription, each subscription has many invoices" cleanly. Native integrations can't.
2. **It's the same spine three other projects need.** Building it once for billing pays for the health score, the ZenOne join, and any future cross-system reporting.
3. **Auditability.** When Finance asks "why does Company X show MRR of $897 when their three subs add to $897?" you can trace it through the mapping table. With middleware, that question requires opening five scenarios and reading logs.

See the POC **Tab 2** for the working mock — pick "Sunrise Orthodontics" in the drill-down to see a real multi-location case (2 active + 1 canceled location, partial health status).

---

## Assignment 3 — Prioritizing the 90-Day Roadmap

### My sequencing thesis

Sequence by **dependency and revenue leverage**, not just by urgency labels. The first three projects are the spine; everything else is cheaper to build once the spine exists. Below is the order I'd execute in, plus 10 net-new projects I'd add to the queue.

### Top 5 (from the existing queue)

| # | Project | Effort | Why this position |
|---|---|---|---|
| 1 | **2.1 Automate Savings Analysis** | 3–4 wk | The single biggest revenue bottleneck. 5–7 hrs/mo of founder time. Doubles sales throughput immediately. Explicitly flagged highest priority by the brief. |
| 2 | **1.1 Stripe ↔ HubSpot Sync** | 1–2 wk | Foundational data spine. Unblocks billing visibility, CS dashboards, and the customer health score. Can run in parallel with #1. |
| 3 | **3.1 Consolidate CS into HubSpot** | 2–3 wk | No ticketing system today. Service requests scattered across email/phone/SMS. Moving to HubSpot ticketing gives measurability and prevents churn from dropped requests. Needs #2's plumbing. |
| 4 | **3.8 Post-Onboarding Drip Campaign** | 1 wk | Quick win. Improves activation in the critical first-two-weeks window. Reuses HubSpot foundation from #2. |
| 5 | **1.2 ZenOne Data Integration** | 3–4 wk | Backbone for Q2. Customer health score (3.5), 45/90-day check-ins (3.6), missed-savings alerts all depend on this. Must come before any of them. |

### Why not these first

- **1.3 Unified Business Dashboard.** Garbage-in until #2 (billing) and #5 (ordering) are clean. Building a dashboard on top of incomplete data trains the team to distrust the dashboard.
- **3.5 Customer Health Score.** Depends on ZenOne data (#5). Doing the score before the pipe = a number nobody trusts. Sequencing trap.
- **4.1 Company AI Audit & Enablement.** Broad and unfocused before core revenue/service workflows stabilize. Better placed in days 90–180.
- **2.4 PandaDoc Automation.** Moderate impact but low frequency relative to #1. Top-3 in Q2, not Q1.

### 10 projects I'd add to the backlog

The existing queue is solid for the obvious wins. These come from thinking about SourceClub's flywheel: every member buys monthly (recurring data source), every prospect needs an SA (recurring opportunity). Two engines that get faster with automation.

| ID | Project | Category | Effort | Why |
|---|---|---|---|---|
| NEW-1 | **Supplier API Integrations** (Benco, Henry Schein direct pulls) | Data | 4–6 wk | Removes the manual export step in savings analysis. Enables real-time price-drift detection. The single biggest follow-on to Project 2.1. |
| NEW-2 | **Catalog Drift Monitor** | Trust | 1 wk | Daily diff: supplier prices vs SC catalog. Alerts when any item moves >5%. Prevents the "we promised $X but the price changed" churn scenario. |
| NEW-3 | **Member Spend Forecast + Drop Alert** | Retention | 2 wk | Forecast monthly spend from ZenOne data. When spend drops >25% MoM, alert CS owner. Earliest churn signal we'll have. |
| NEW-4 | **Cross-Sell Recommender** | Revenue expansion | 2–3 wk | "Members buying X also buy Y, often at 30% markup elsewhere." Surfaces savings the member doesn't know about. LTV up without selling. |
| NEW-5 | **Prospect Auto-Enrichment** | Sales velocity | 1–2 wk | Given a practice domain, auto-pull location count, specialty mix, likely supplier. Shortens discovery from 30 → 15 min. |
| NEW-6 | **AI Quote Bot for Members** | Member experience | 3 wk | Slack/email bot: "What's my best price for nitrile gloves medium?" Returns SC price + current-supplier comparison. Friction down. |
| NEW-7 | **Win/Loss Auto-Analysis** | Sales ops | 1 wk | LLM digests HubSpot closed-won/lost monthly. Surfaces top 3 objections + segments that convert. Feeds back into messaging (2.5). |
| NEW-8 | **Smart Order Routing** | Margin | 4 wk | Given a member order, auto-route to lowest-cost supplier with stock. Needs ZenOne (#5) + supplier APIs (NEW-1) first. |
| NEW-9 | **Internal AI Knowledge Search** | Team velocity | 1–2 wk | All SOPs, member notes, supplier contracts indexed. "When does the Schein contract renew?" answered in 5 sec. Compounds across the team. |
| NEW-10 | **Onboarding Time-to-First-Order Tracker** | Activation | 1 wk | Single metric: contract-signed → first ZenOne order. Drives every onboarding decision. Easy once #5 is in place. |

### 90-day sequencing view

```
Weeks 1–4   ████████ 2.1 Automate Savings Analysis           ← P0, ships standalone
Weeks 2–4   ████ 1.1 Stripe ↔ HubSpot Sync (in parallel)     ← unblocks #3, #5
Weeks 4–6   ████ 3.8 Post-Onboarding Drip                    ← quick win
Weeks 5–8   ████████ 3.1 CS Consolidation into HubSpot       ← needs #2 plumbing
Weeks 8–12  ████████████ 1.2 ZenOne Data Integration         ← Q2 backbone
Weeks 11–13 ████ NEW-2 Catalog Drift Monitor                 ← protects #1
Weeks 12+   .... NEW-1, NEW-3, NEW-8 ...                     ← unlocked once spine exists
```

The thesis is simple: **the first 90 days build the spine** (Stripe + HubSpot + ZenOne). Everything else becomes 3–5x cheaper to build once that spine exists. That's the difference between a queue of 30 disconnected projects and a roadmap.

---

## Appendix

### Assumptions I made

- The SourceClub master catalog is accessible as a CSV or via internal API. I modeled it with 40 representative items covering the main spend categories.
- ZenOne has a queryable API or at least a regular CSV export. (If it's screen-scrape only, NEW-1 + 1.2 timelines roughly double.)
- The team is open to introducing one new Python service. (If "no new services" is a hard constraint, Stripe sync can fall back to a Make.com scenario plus a Google Sheets canonical mapping — same logic, more brittle.)
- Suggested-time labels in the brief (2–3 hrs Assignment 1, 30 min each for 2 and 3) are guidance, not gates. I went over for Assignment 1 because the working POC was the highest-impact deliverable.

### Open questions for the team

- Current match rate of the manual process? I'd want to beat that with the automated pipeline. (My estimate from videos: ~95% with a 10-min review. Target: 85% auto-accept + 15% reviewed, in <2 min total.)
- How is "multi-location group" currently identified in HubSpot? Shared domain? A `parent_company_id` property? Need to confirm before building the backfill matcher.
- Is there an existing reviewer queue tool the team prefers (Retool, Notion, Airtable)? The POC's queue UI is illustrative — the real one should match team workflow.
- What's the SLA on a savings analysis today? (How fresh does the report need to be?) Drives whether webhook sync or nightly batch is enough.

### What this took / honest scope

The POC took several focused hours to build, mostly on the matching engine, UOM normalization, and the Streamlit UI. The deliberate trade-off: a runnable thing on representative data, not a polished design doc. Per the brief, "a rough working thing beats a beautiful description of one."

### How to evaluate

1. Open the deployed URL (or run locally per README).
2. Drive Tab 1 with each of the four sample files. Watch the match rate, the review queue, the no-match bucket.
3. Open Tab 2, pick "Sunrise Orthodontics" — see the multi-location case (3 locations, 1 past-due, 1 canceled).
4. Read Tab 3 for the roadmap rationale.
5. Read this doc for the production architecture and the "what would I do next."

Happy to walk through any of this live. Thanks for the time.

— Abhi
