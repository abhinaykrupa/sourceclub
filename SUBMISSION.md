# SourceClub Case Study — Final Submission

**Candidate:** Abhi
**Role:** Head of AI Powered Operations, Systems & RevOps
**Submitted:** May 21, 2026

**🔗 Live demo:** `https://<your-app>.streamlit.app`  (TODO: replace after Streamlit Cloud deploy)
**💻 Code:** `https://github.com/abhinaykrupa/sourceclub`
**🎥 Video walkthrough:** `<Loom link>` (3–5 min)
**🔒 Security review:** [`SECURITY_REVIEW.md`](./SECURITY_REVIEW.md) — what's safe in the POC, what's required for real data
**🏗️ Production architecture:** [`PRODUCTION_ARCHITECTURE.md`](./PRODUCTION_ARCHITECTURE.md) — vendor picks, cost model, scaling plan, 6-8 week build path
**🎯 Strategic addendum:** [`STRATEGIC_ADDENDUM.md`](./STRATEGIC_ADDENDUM.md) — six-quarter growth thesis I'd bring to the first board meeting (unprompted; not part of the three assignments)

---

## TL;DR

Three deliverables, one repo, one demo URL. Built for the **CEO, Head of Marketing, and Head of Sales/Revenue** — not just a back-office analyst — so the app opens on a **Leadership Dashboard** with three persona-targeted sections before drilling into the individual workflows.

**Important business context I anchored on** (from SourceClub's public site):
- **"90% of practices who see their numbers join"** — the savings analysis isn't a step toward the close, it *is* the close.
- **"3x ROI guaranteed, or Source Club tells you not to join"** — they actively *disqualify* prospects when the math doesn't work.
- **"$97K avg annual savings per practice"**, **supply costs go from 7-12% → 3-4% of revenue**.
- **"Cancel anytime. No contracts"** — retention is fragile; value must be continuously visible.
- They already have a member-facing app (`app.sourceclub.com`) — my work *complements* that, not replaces it.

These five facts drive every recommendation below.

- **Assignment 1.** Working POC that auto-detects supplier (Benco / Henry Schein / Darby / Base86 / Patterson), parses the file, runs a 3-stage matching engine with UOM/pack-size verification, and produces (a) an interactive savings report, (b) a **branded PDF** for the prospect, and (c) an **AI-drafted follow-up email**.
- **Assignment 2.** Recommended **custom sync + canonical mapping table** over native or middleware-only options. Mocked end-to-end in the POC including multi-location billing rollups and an exception queue for unmapped customers.
- **Assignment 3.** Prioritized the existing queue by **dependency, not urgency**. Added **10 net-new projects** with explicit **dollar impact estimates** totaling **~$1.1M in annual value** if all shipped, plus a day-by-day **First 30 Days** plan.

Runs locally with `pip install` + `streamlit run` (~2 min). All LLM calls and external APIs are mocked and clearly labeled; production swap-in points are documented inline.

---

## My AI Thesis for SourceClub

Three claims that shape every decision in this submission:

**1. AI doesn't replace the team. It makes each person look like five.**
Every project below is framed in headcount-equivalents and dollars, not "AI capabilities." Savings analysis automation = 0.4 FTE freed = $40K/yr saved. AI quote bot = 1 CS hire avoided. That's how AI gets funded inside a 7-person company.

**2. The data spine matters more than the AI.**
ZenOne integration, Stripe-HubSpot mapping, supplier APIs — these are unsexy but compound. AI on bad data is expensive nonsense. **My first 30 days are 60% data plumbing.** Most "head of AI" candidates skip this and ship LLM features into a void.

**3. AI in the sales motion, not just back-office ops.**
Most Head of AI hires get put on operations. The real revenue lever at SourceClub is **AI-augmented sales** — auto-drafted follow-up emails after each savings analysis, AI-prepared discovery briefs from a domain, AI-generated objection responses. That's why the POC's "salesperson actions" (PDF generation + email drafter) sit alongside the matching engine, not buried in an internal tool.

---

## Who uses this tool

The Leadership Dashboard tab (the first thing you see) is designed for three executives:

| Persona | What they need | Where to look |
|---|---|---|
| **CEO** | Is the savings-analysis function working at scale? Pipeline health, revenue delivered, throughput. | Top section: KPI strip + pipeline-by-stage and savings-by-stage charts. Open Monday morning. |
| **Head of Marketing** | What does our ICP actually look like? Where do prospects object? What content do I have for case studies? | Middle section: savings-by-specialty table, objections chart, on-demand anonymized case-study generator. |
| **Head of Sales / Revenue** | Where is each deal? Who's ready for a nudge? What should the rep say? | Bottom section: filterable pipeline table, per-rep throughput, "ready to nudge" list with one-click AI email drafting. |

The other tabs (Savings Analysis / Sync / Roadmap) are operator views — the founder running an SA, the engineer wiring the sync, me explaining the roadmap.

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
Salesperson actions:
   📄 Generate Branded PDF Savings Report  → emailable deliverable for prospect
   🤖 Draft AI Follow-up Email             → personalized to savings amount & specialty
   📊 Export Audit CSV                     → full line-item trail for finance/legal
```

### Five supplier adapters (matches the videos)

| Supplier | Sample file | Demo behavior |
|---|---|---|
| **Benco** | Auburn Dental | Clean SKU matches — 32 auto-accept, 2 catalog gaps. The happy path. |
| **Henry Schein** | Demit Dental | Similar — 35 auto, 3 catalog gaps. Shows multi-supplier coverage. |
| **Darby** | Quincy Smiles | 13 auto, 11 review — UOM mismatches force human review. |
| **Base86** | Auburn Dental Group | 3 auto, 18 review — no mfg SKUs in file, so LLM judge earns its keep. |
| **Patterson (messy)** | Harbor View Dental | Real-world chaos: $-prefixed prices, embedded commas, blank rows, footer rows, mixed UOM formats. Adapter strips it all. |

### Why this design

**Three stages instead of one** because the failure modes are different:
- Stage 1 catches the easy ~30–40% (clean SKU matches) at zero LLM cost.
- Stage 2 narrows the candidate space — an LLM judging 500 catalog items per line is wasteful and noisy.
- Stage 3 is where reasoning happens (UOM normalization, manufacturer disambiguation).

**Supplier adapters before matching** because the training videos make it clear: every supplier exports a different shape. Without adapters, you're matching across schemas — which is where the manual VLOOKUP pain comes from today.

**UOM/pack-size detection as its own concern.** This was the single most-called-out failure mode in the videos. "Box of 100" vs "case of 10 boxes" matters more than fuzzy description scoring. The matcher parses pack hints from descriptions and explicit UOM columns, then compares against catalog metadata. Mismatches force human review even when description and manufacturer align — the unit-economics math breaks otherwise.

**Human-in-the-loop is the spec, not a fallback.** The training material talks about 5–7 hrs/mo of manual work. Replacing 100% requires perfect matching; replacing 80% requires good matching with a clean review path. The right target is the latter.

**End-to-end means END-to-end.** Most candidates would stop at "savings report rendered on screen." But the actual revenue moment is the salesperson clicking send. So the POC ends with the PDF + the AI-drafted follow-up email, not the dataframe.

### What's mocked vs production-ready

| Component | POC | Production |
|---|---|---|
| Supplier adapters | ✅ Production-shaped (per-supplier modules) | Same code, expanded for edge cases + more suppliers |
| Stage 1 deterministic | ✅ Real | Same |
| Stage 2 semantic | difflib + token overlap | **pgvector** with `sentence-transformers/all-MiniLM-L6-v2` embeddings |
| Stage 3 LLM judge | Rule-based mock with rationale generation | **Claude Haiku** with structured JSON output |
| UOM normalization | ✅ Real (regex + alias table) | Same + learned synonyms from reviewer corrections |
| Email drafting | Rule-based template | **Claude Sonnet** with prospect context (template included in code as production prompt) |
| PDF generation | ✅ Real (reportlab) | Same — branded template |
| Review queue | Approve/Reject buttons (no persistence) | **Retool** front-end on the canonical DB |
| Catalog | CSV, ~40 items | Postgres table, versioned per analysis run |

**Production Stage-3 prompt sketch** (Claude Haiku):

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

1. **Real embeddings + pgvector.** Replace difflib with a proper vector store. Embed once at catalog ingest, query at match time. ~2 days.
2. **Reviewer feedback loop.** Every approve/reject in the queue writes a labeled pair into a "matching memory" table. Future Stage-2 retrieval biases on it. System gets smarter per analysis.
3. **Supplier API integrations** (Benco + Henry Schein). Skip the manual export entirely. Real-time data. See NEW-1 below.
4. **Catalog drift monitor.** Daily diff supplier prices vs SC rates. Alert when any item moves >5%. Protects every report we've sent.
5. **Self-serve prospect portal.** Eventually the prospect uploads their own file inside a branded landing page. Drops sales-cycle time materially.

---

## Assignment 2 — Stripe ↔ HubSpot Sync

### The problem

Stripe bills per location (one subscription = one practice). HubSpot organizes around the Company (parent dental group). Today nobody on the team can open a Company in HubSpot and see its billing health without manually cross-referencing Stripe. That blocks:

- Sales seeing if a prospect's existing locations are paying on time
- CS knowing which Companies have past-due locations (early churn signal)
- Finance pulling a clean MRR/ARR view sliced by Company

### Three options I considered

| Option | Cost | Pros | Cons | Verdict |
|---|---|---|---|---|
| **Native Stripe-HubSpot integration** | $0 (included) | Zero setup | Syncs to Deals/Invoices, not the Company record. No multi-location rollup. Can't aggregate MRR across subs. | ❌ |
| **Middleware only (Make / Zapier)** | $30–50/mo | Visual, fast to MVP, low-code | Brittle for backfills + audits. Mapping logic spread across scenarios. Per-task pricing scales with volume. | ⚠️ Stopgap only |
| **Custom sync + canonical mapping table** | ~1 dev-week build, ~$0 ongoing | Owns the data spine. Auditable. Handles multi-location reality natively. Same spine serves customer health score (3.5) and ZenOne integration (1.2) downstream. | More upfront work. Maintenance on us. | ✅ **Pick this** |

### The chosen design

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

1. Build the mapping table in Postgres. Backfill by fuzzy-matching Stripe customer names against HubSpot Company names, then human-reconcile unmatched.
2. Stand up a small Python service (FastAPI on Render or AWS Lambda + API Gateway). Endpoint: `POST /stripe-webhook`.
3. Wire Stripe webhooks for `subscription.*`, `invoice.*`, `customer.updated`.
4. On each event: look up mapping → recompute the affected Company's rollup → push to HubSpot custom properties via API.
5. Nightly reconciliation job: scan for drift, flag new unmapped customers to the exception queue.
6. Build a simple Retool view of the exception queue so CS/Ops can resolve unmapped customers in minutes.

**Cost:** one engineer-week to build, then maintenance only. Infrastructure ~$0 (free tier handles this volume). The middleware-only option costs more per year and gives less control.

### Why this wins long term

1. **It fits the actual data model.** Native integrations can't express "company has many locations, each with one subscription, each with many invoices." A custom build can.
2. **Same spine three other projects need.** Pays for itself once, used four times.
3. **Auditability.** Finance asks "why does Company X show MRR of $897?" → traceable through the mapping table. With middleware, the answer is "open five scenarios and read logs."

See **Tab 2** for the working mock — pick "Sunrise Orthodontics" in the drill-down to see a real multi-location case (2 active + 1 canceled location, partial health status).

---

## Assignment 3 — Prioritizing the 90-Day Roadmap

### Sequencing thesis

Sequence by **dependency and revenue leverage**, not just urgency labels. The first three projects build the spine; everything else is cheaper once the spine exists.

### Top 5 (from the existing queue)

| # | Project | Effort | Why this position |
|---|---|---|---|
| 1 | **2.1 Automate Savings Analysis** | 3–4 wk | The single biggest revenue bottleneck. 5–7 hrs/mo of founder time. Doubles sales throughput. Explicitly flagged highest priority. |
| 2 | **1.1 Stripe ↔ HubSpot Sync** | 1–2 wk | Foundational data spine. Unblocks billing visibility, CS dashboards, customer health score. Can run in parallel with #1. |
| 3 | **3.1 Consolidate CS into HubSpot** | 2–3 wk | No ticketing system today. Service requests scattered across email/phone/SMS. Moving to HubSpot ticketing gives measurability and prevents churn from dropped requests. Needs #2's plumbing. |
| 4 | **3.8 Post-Onboarding Drip Campaign** | 1 wk | Quick win. Improves activation in the critical first-two-weeks window. Reuses HubSpot foundation from #2. |
| 5 | **1.2 ZenOne Data Integration** | 3–4 wk | Backbone for Q2. Customer health score (3.5), 45/90-day check-ins (3.6), missed-savings alerts all depend on this. |

### Why not these first

- **1.3 Unified Business Dashboard.** Garbage-in until #2 (billing) and #5 (ordering) are clean. Building a dashboard on incomplete data trains the team to distrust the dashboard.
- **3.5 Customer Health Score.** Depends on ZenOne data (#5). Doing the score before the pipe = a number nobody trusts. Sequencing trap.
- **4.1 Company AI Audit & Enablement.** Broad and unfocused before core revenue/service workflows stabilize. Better in days 90–180.
- **2.4 PandaDoc Automation.** Moderate impact but low frequency relative to #1.

### 10 projects I'd add to the backlog — with dollar impact

These come from thinking about SourceClub's flywheel: every member buys monthly (recurring data source), every prospect needs an SA (recurring opportunity). Two engines that get faster with automation.

**Sizing context.** Numbers below are calibrated to ~500 members, ~$2.5M ARR, 4–7 employees. SourceClub makes flat membership fees — **not** a % of supplier GMV — so I separate "SourceClub revenue impact" from "member value delivered" (which drives retention indirectly).

| ID | Project | Effort | Annual $ Impact | Mechanism |
|---|---|---|---|---|
| **NEW-1** | Supplier API Integrations (Benco, Henry Schein) | 4–6 wk | **+$50K ARR** | Faster SA turnaround → ~10 extra closes/yr × ~$5K avg ACV. Eliminates analyst time too (~$15K labor saved); main value is sales velocity. |
| **NEW-2** | Catalog Compliance Monitor | 1 wk | **+$15K retained ARR** | SC prices are *contractually locked* for 6 months. This auto-files price-match claims when a supplier invoice exceeds the locked rate — protects trust + recovers refunds. Prevents ~3 trust-driven churns/yr × $5K ACV. |
| **NEW-3** | Member Spend Forecast + Drop Alert | 2 wk | **+$25K retained ARR** | Catches 5 at-risk members 60 days earlier → saves 5 × $5K = $25K of would-be churn. |
| **NEW-4** | Cross-Sell Recommender | 2–3 wk | **+$15K retained ARR** (member-value play) | Members feel more value → measurable in NPS + renewal rates. Indirect revenue, not direct margin. |
| **NEW-5** | Prospect Auto-Enrichment | 1–2 wk | **+$35K (sales hours saved + cycle compression)** | Saves ~8 hrs/wk × $90/hr loaded × 50 wks = $36K. Also shaves days off sales cycle = +1-2 deals/yr. |
| **NEW-6** | AI Quote Bot for Members | 3 wk | **+$30K retention + member experience** | Reduces "I forgot to order" churn driver; small but compounding LTV impact. |
| **NEW-7** | Win/Loss Auto-Analysis | 1 wk | **+$10K (positioning lift)** | At current SA volume, 2pp conversion lift = ~1-2 extra deals/yr. Real value is messaging that compounds over time. |
| **NEW-8** | Intelligent Order Routing (layer on existing "One login, all suppliers") | 4 wk | **+$30K retained ARR** | SC already has multi-supplier ordering. This adds *intelligence* on top — auto-recommends the cheapest in-stock supplier per item per order. Drives member-perceived value → retention + referrals. |
| **NEW-9** | Internal AI Knowledge Search | 1–2 wk | **+$60K (FTE-equivalent)** | 5 hrs/wk × 6 people × $90/hr loaded × 50 wks = $135K theoretical; halve for adoption reality. |
| **NEW-10** | Onboarding Time-to-First-Order Tracker | 1 wk | **+$20K retained ARR** | Catches 5 stalled onboardings/yr before they early-churn × $4K avg ARR each. |

**Aggregate annual $ impact: ~$290K/yr** (roughly 12% of current ARR) if all 10 ship in year one. **These are defensible-directionally estimates, not point-precise** — used as inputs to prioritization, not promises to the board. Most projects in this list cost <2 engineer-weeks; ROI is strong even at half of these estimates.

**Why this is the right way to think about it.** Most "AI roadmap" pitches inflate impact to look exciting. At a 7-person company, the test is: *can the engineering investment plausibly return 5–10x in year one?* Most of these clear that bar comfortably even when discounted. The ones that don't (NEW-7) are still worth doing for compounding strategic value, not point ROI.

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

**Thesis:** the first 90 days build *the spine* (Stripe + HubSpot + ZenOne). Everything else becomes 3–5x cheaper to build once that spine exists.

---

## My First 30 Days

Specific, not hand-wavy. Day-by-day, who I'd talk to, what I'd measure, what I'd ship.

**Week 1 — Listen and measure**
- Day 1–2: shadow the founder running 3 savings analyses end-to-end. Time every step. Note where they hesitate.
- Day 2–3: interview each of the 7 team members 30 min — what's broken, what's slow, what's their biggest "if only this just worked" item.
- Day 3–4: read every closed-won and closed-lost deal from the last 90 days in HubSpot. Catalog objections.
- Day 5: baseline metrics — current match rate (manual), avg minutes per SA, conversion rate from SA → close, current pipeline value, current MRR.

**Week 2 — Ship a quick win + start the spine**
- Mon: ship the catalog-gap report (1 day) — surfaces every "we have no equivalent" item from past SAs. Hand to suppliers as quarterly negotiation input.
- Tue–Fri: scaffold the savings analysis automation. Adapters for top 2 suppliers (Benco, Henry Schein). Mocked LLM judge so progress isn't blocked by API access.
- In parallel: start the Stripe ↔ HubSpot mapping table backfill (1 engineer-day of throwaway script work).

**Week 3 — Real LLM in the loop**
- Wire Claude Haiku into Stage 3 of the matcher. Test on 50 SA samples from history. Compare auto-accept rate vs human override rate.
- Build the salesperson PDF generator (1 day). Email drafter (1 day).
- Ship the Stripe-HubSpot custom-property writer. CS team starts seeing billing health in HubSpot Companies.

**Week 4 — First end-to-end test**
- Run 5 live prospect SAs through the new pipeline. Founder still does the final review pass — that's the human-in-loop spec.
- Measure: time per SA, match rate, # of items routed to review.
- Demo to CEO + Sales. Get sign-off to flip the founder out of the SA workflow for week 5.

**By end of day 30:**
- Savings analysis time per prospect: target 10 min → 2 min (founder review only)
- Stripe ↔ HubSpot data spine: live
- 0 dropped CS tickets this week (because we have ticketing now)
- Baselined and dashboarded the metrics that matter

---

## Appendix

### Assumptions I made

- The SourceClub master catalog is accessible as a CSV or via internal API. Modeled with ~40 representative items.
- ZenOne has a queryable API or at least a regular CSV export. (If screen-scrape only, NEW-1 + 1.2 timelines roughly double.)
- Team is open to introducing one new Python service. (If "no new services" is a hard constraint, Stripe sync falls back to Make.com + Google Sheets — same logic, more brittle.)
- Suggested-time labels in the brief are guidance, not gates. I went over for Assignment 1 because the working POC was the highest-impact deliverable.

### Open questions for the team

- Current match rate of the manual process? Want to beat that. (Estimate from videos: ~95% with 10-min review. Target: 85% auto-accept + 15% reviewed, in <2 min total.)
- How is "multi-location group" currently identified in HubSpot? Shared domain? Parent ID? Need to confirm before building the backfill matcher.
- Existing reviewer queue tool the team prefers (Retool, Notion, Airtable)? POC queue UI is illustrative.
- SLA on a savings analysis today? Drives whether webhook sync or nightly batch suffices for the data spine.

### What this took / honest scope

The POC took several focused hours, mostly on matching engine, UOM normalization, leadership dashboard, and the salesperson actions layer. The deliberate trade-off per the brief: a runnable thing on representative data, not a polished design doc.

### How to evaluate

1. Open the deployed URL (or run locally per README).
2. **Tab 0 (Leadership Dashboard)** — first thing you see. Three persona sections, one page.
3. **Tab 1 (Savings Analysis)** — drive each of the 5 sample files. Watch match rate, review queue, no-match bucket. Click "Generate PDF" and "Draft AI Email" to see end-to-end.
4. **Tab 2** — pick "Sunrise Orthodontics" to see the multi-location billing rollup.
5. **Tab 3** — roadmap rationale + dollar impact estimates.

Happy to walk through any of it live.

— Abhi
