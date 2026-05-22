# Production Architecture — SourceClub Operations Platform

**Author:** Abhi
**Context:** What it takes to move the POC from "runs on Streamlit Cloud with mock data" → "production system processing real prospect and member data at ~500 members today, ~2,000 in 18 months."
**Audience:** SourceClub CEO + technical founder; reader who'd evaluate this as if hiring me.

---

## TL;DR

The POC is the right *shape* — adapters → matching engine → leadership dashboard → salesperson actions. To make it production-ready, you need to add the **data spine** (database + auth + audit log), the **AI spine** (real LLM calls with cost guardrails + prompt-injection defense), and the **operational spine** (CI/CD + observability + on-call). Everything else is bells.

**Estimated effort to v1 production:** ~6–8 engineer-weeks for one mid/senior backend engineer + me overseeing the AI choices. Infra cost at launch: **~$650/month all-in** (compute + DB + LLM + monitoring). Scales sub-linearly with member growth.

**The cost case writes itself.** Founder time today on SAs alone = $40K/yr at modest valuation. Cost to run the platform = $8K/yr. Even ignoring all the second-order revenue lift, payback is <3 months.

---

## 1. Current state → production gap

| Layer | POC today | Production v1 | Effort |
|---|---|---|---|
| Frontend | Streamlit on Streamlit Cloud | Same Streamlit app, deployed on AWS App Runner or Render (custom domain, SSO) | 2 days |
| Auth | None | Google Workspace SSO via Streamlit Auth or Auth0 | 2 days |
| Database | None (all in-memory) | Postgres (RDS or Supabase) with row-level security per tenant | 3 days |
| File storage | In-memory only | S3 with per-tenant prefixes, lifecycle rules | 1 day |
| Matching: deterministic + UOM | Real (pandas) | Same code, runs in worker process | 0 |
| Matching: semantic (Stage 2) | difflib | pgvector + sentence-transformers embeddings | 3 days |
| Matching: LLM judge (Stage 3) | Mocked | Claude Haiku via Anthropic API | 2 days |
| Email drafter | Template | Claude Sonnet with prospect context | 1 day |
| PDF generator | reportlab (local) | Same code, output to S3 with signed URLs | 1 day |
| Stripe sync | Mock | Real webhooks + canonical mapping in Postgres | 5 days |
| HubSpot writer | Mock | Real API client + retry/backoff + rate-limit handling | 3 days |
| Background work | None (synchronous) | Job queue (Celery + Redis, or SQS + Lambda) | 3 days |
| Audit log | None | Append-only events table + queryable UI | 2 days |
| Monitoring | streamlit log | Sentry + Datadog + UptimeRobot | 1 day |
| CI/CD | git push → manual deploy | GitHub Actions → containerized → auto-deploy staging, gated prod | 2 days |
| Reviewer queue | In-session buttons | Retool dashboard on the canonical DB | 3 days |

**Total ~30 working days** for one engineer. With me overseeing AI/data architecture and pair-programming on the harder pieces, **6–8 calendar weeks** is realistic.

---

## 2. System architecture (production v1)

```
                                  ┌─────────────────────┐
                                  │   GOOGLE WORKSPACE  │
                                  │       (SSO)         │
                                  └──────────┬──────────┘
                                             │
                          ┌──────────────────┴──────────────────┐
                          │                                     │
                          ▼                                     ▼
                ┌─────────────────┐               ┌─────────────────┐
                │  STREAMLIT APP  │               │     RETOOL      │
                │  (sales + ops)  │               │ (reviewer queue,│
                │                 │               │  internal admin)│
                │ on AWS App      │               │                 │
                │ Runner          │               │                 │
                └────────┬────────┘               └────────┬────────┘
                         │                                 │
                         │ HTTP + auth headers             │ direct DB
                         ▼                                 ▼
            ┌─────────────────────────────────────────────────────┐
            │              POSTGRES (RDS Multi-AZ)                │
            │   prospects · members · matches · audit_log · etc.  │
            │   pgvector for catalog embeddings                   │
            │   Row-level security (per tenant)                   │
            └──────────────────┬──────────────────────────────────┘
                               │
       ┌───────────────────────┼──────────────────────┐
       │                       │                      │
       ▼                       ▼                      ▼
┌────────────┐         ┌──────────────┐      ┌──────────────────┐
│  S3        │         │  REDIS       │      │  ANTHROPIC API   │
│  (files +  │         │ (queue +     │      │  Haiku (Stage 3) │
│   PDFs)    │         │  cache)      │      │  Sonnet (emails) │
└────────────┘         └──────┬───────┘      └──────────────────┘
                              │                       ▲
                              ▼                       │
                     ┌─────────────────┐              │
                     │  WORKERS        │──────────────┘
                     │  (Celery)       │
                     │  - SA matching  │
                     │  - PDF gen      │
                     │  - LLM calls    │
                     │  - Stripe sync  │
                     └────────┬────────┘
                              │
                ┌─────────────┼─────────────────┐
                │             │                 │
                ▼             ▼                 ▼
        ┌──────────┐  ┌──────────────┐  ┌──────────────┐
        │  STRIPE  │  │  HUBSPOT     │  │  ZENONE      │
        │ (webhook │  │  (API write) │  │  (data pull) │
        │ ingress) │  │              │  │              │
        └──────────┘  └──────────────┘  └──────────────┘

      ┌─────────────────────────────────────────────────────┐
      │  OBSERVABILITY                                      │
      │   Sentry (errors) · Datadog (metrics+logs)          │
      │   UptimeRobot (external pings)                      │
      │   PagerDuty → Slack (alerts)                        │
      └─────────────────────────────────────────────────────┘
```

**Design principles:**
1. **Postgres is the single source of truth.** Everything joinable lives in one DB. No microservices for a 7-person team. Adopt the canonical mapping table from Assignment 2 here.
2. **Workers do the heavy lifting**, not the web frontend. Matching runs are async — the user clicks "run analysis" and gets a notification when done (15–30 sec). Keeps the UI snappy and lets us batch LLM calls.
3. **All external APIs are webhook-in + queue-out.** No synchronous external calls in user request paths. Insulates against vendor outages.
4. **One vendor per category.** Don't mix Sentry + Bugsnag + Rollbar. Don't mix Datadog + New Relic. Discipline matters when the team is 7 people.

---

## 3. Data architecture

### 3.1 Schema (Postgres, simplified)

```sql
-- Identity & tenant
CREATE TABLE tenants (id UUID PRIMARY KEY, name TEXT, created_at TIMESTAMPTZ);
CREATE TABLE users (id UUID PRIMARY KEY, tenant_id UUID, email TEXT, role TEXT);

-- Canonical mapping (the data spine from Assignment 2)
CREATE TABLE hubspot_companies (id TEXT PRIMARY KEY, tenant_id UUID, name TEXT, domain TEXT, owner TEXT);
CREATE TABLE hubspot_locations (id TEXT PRIMARY KEY, hs_company_id TEXT, tenant_id UUID, name TEXT);
CREATE TABLE stripe_customers (id TEXT PRIMARY KEY, tenant_id UUID, name TEXT, email TEXT);
CREATE TABLE stripe_subscriptions (id TEXT PRIMARY KEY, stripe_customer_id TEXT, tenant_id UUID,
                                    status TEXT, mrr_cents INT, plan TEXT, current_period_end DATE);
CREATE TABLE canonical_map (
  stripe_sub_id TEXT PRIMARY KEY,
  stripe_customer_id TEXT NOT NULL,
  hs_location_id TEXT NOT NULL,
  hs_company_id TEXT NOT NULL,
  tenant_id UUID NOT NULL,
  confidence FLOAT,
  resolved_by TEXT,
  resolved_at TIMESTAMPTZ
);

-- Savings analysis
CREATE TABLE catalog_items (
  sc_sku TEXT PRIMARY KEY, tenant_id UUID,
  description TEXT, manufacturer TEXT, mfg_sku TEXT,
  unit_of_measure TEXT, pack_size INT, unit_price_cents INT,
  description_embedding VECTOR(384),  -- pgvector
  version INT, active BOOLEAN, valid_from DATE, valid_to DATE
);
CREATE TABLE sa_runs (
  id UUID PRIMARY KEY, tenant_id UUID,
  prospect_company TEXT, supplier TEXT,
  uploaded_by UUID, uploaded_at TIMESTAMPTZ,
  status TEXT,  -- 'pending', 'processing', 'complete', 'failed'
  total_spend_cents BIGINT, total_savings_cents BIGINT,
  match_count INT, review_count INT, no_match_count INT
);
CREATE TABLE sa_line_items (
  id UUID PRIMARY KEY, sa_run_id UUID,
  raw_description TEXT, supplier_sku TEXT, manufacturer_sku TEXT,
  quantity NUMERIC, unit_price_cents INT, annual_spend_cents BIGINT,
  matched_sc_sku TEXT, match_method TEXT, confidence FLOAT,
  uom_status TEXT, rationale TEXT, status TEXT,
  reviewer_action TEXT, reviewer_id UUID, reviewed_at TIMESTAMPTZ
);

-- Audit log (append-only, immutable)
CREATE TABLE audit_log (
  id BIGSERIAL PRIMARY KEY,
  tenant_id UUID, user_id UUID,
  event_type TEXT, entity_type TEXT, entity_id TEXT,
  payload JSONB,
  ip_address INET, user_agent TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_audit_tenant_time ON audit_log(tenant_id, created_at DESC);
```

### 3.2 Row-level security

```sql
ALTER TABLE sa_runs ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON sa_runs
  USING (tenant_id = current_setting('app.current_tenant')::UUID);
```

Set `app.current_tenant` per session — even a bug in app code can't leak data across tenants.

### 3.3 What lives where

| Data class | Store | Why |
|---|---|---|
| Structured records | Postgres | Single source of truth, joinable, supports RLS |
| Catalog embeddings | Postgres (pgvector) | Same DB as the items — no sync drift |
| Uploaded files (CSV/XLSX) | S3 (per-tenant prefix) | Cheap, durable, lifecycle rules |
| Generated PDFs | S3 (signed URLs, 7-day expiry) | Same |
| LLM prompt/response cache | Redis | Hot data, cheap, evictable |
| Job queue | Redis (Celery broker) | Standard, well-understood |
| Audit log | Postgres → archived to S3 monthly | Queryable + retained long-term |
| Logs (app + access) | Datadog | Centralized + searchable |

---

## 4. AI / LLM architecture

### 4.1 Model routing (production)

| Use case | Model | Why this choice | Cost per call |
|---|---|---|---|
| **Stage 3 LLM Judge** (per line item) | Claude Haiku | Fast, cheap, structured JSON, doesn't need deep reasoning | ~$0.003 |
| **Email drafter** (per prospect) | Claude Sonnet | Quality matters — this email goes to a paying prospect | ~$0.05 |
| **Internal knowledge search** (NEW-9) | Claude Haiku | Volume + retrieval-augmented, doesn't need maximal reasoning | ~$0.005/query |
| **Win/loss analysis** (NEW-7) | Claude Sonnet (monthly batch) | Synthesis quality matters | ~$2/run |
| **OCR / PDF extraction** (future supplier uploads) | Claude Sonnet | Multimodal, handles complex tables | ~$0.10/page |
| **Quote bot** (NEW-6) | Claude Haiku | Latency-sensitive, conversational, single-turn | ~$0.005/query |

**Cost model for matching at 500 members + ~30 SAs/mo:**
- 30 SAs × 30 line items × ~50% reach Stage 3 = 450 Haiku calls/mo
- 450 × $0.003 = **$1.35/mo for Stage 3**
- 30 emails × $0.05 = **$1.50/mo for email drafter**
- **Total LLM cost at current volume: ~$3/mo.** Essentially free.

At 5,000 members + 300 SAs/mo: ~$30/mo. Still negligible.

### 4.2 Cost optimization techniques (built in from day 1)

| Technique | Mechanism | Savings |
|---|---|---|
| **Prompt caching** (Anthropic feature) | Reuse the catalog candidate list across calls within a session | 50–70% on Stage 3 |
| **Model cascade** | Try Haiku first; only escalate to Sonnet on low-confidence | 60–80% on hard cases |
| **Batch processing** | Run nightly catalog drift check as a single batch call vs per-item | 30% |
| **Embedding cache** | Cache embeddings for SKUs already seen | Massive on repeat suppliers |
| **Confidence floor** | Skip LLM entirely when deterministic match is high-confidence | Already in POC design |

### 4.3 Safety architecture

| Risk | Mitigation |
|---|---|
| **Prompt injection** via uploaded files | Wrap prospect data in `<prospect_data>...</prospect_data>` delimiters. Instruct LLM to treat contents as data only. |
| **PII leakage** to Anthropic | Strip contact names, emails, phone numbers, account IDs before sending. Only send `(description, mfg, qty, price)` tuples to Stage 3. |
| **Output validation** | Force structured JSON output. Validate against Pydantic schema. Reject and fall back if invalid. |
| **Hallucinated SKUs** | LLM proposes a `sc_sku`; we verify it exists in our catalog before accepting. |
| **Cost runaway** | Per-tenant daily spend cap. Alert at 80%, hard-stop at 100%. |
| **Vendor outage** | Circuit-breaker on Anthropic. On outage: queue requests, fall back to "review queue" with `LLM unavailable` status, retry async. |

---

## 5. Infrastructure & tooling stack (vendor picks)

**Pragmatic, vendor-consolidated, defensible. Total ~$650/month at launch.**

| Layer | Vendor | Why | Cost/mo |
|---|---|---|---|
| **Compute (app)** | AWS App Runner or Render | Container-based, autoscales, cheap to start | ~$50 |
| **Compute (workers)** | Same | Same instance pool with worker entrypoint | ~$50 |
| **Database** | AWS RDS Postgres (db.t4g.small Multi-AZ) | Managed, pgvector available, predictable cost | ~$120 |
| **Cache + Queue** | AWS ElastiCache Redis (cache.t4g.micro) | Managed, persistent option | ~$25 |
| **File storage** | AWS S3 | Standard, cheap, lifecycle rules | ~$10 (low volume) |
| **DNS + CDN** | Cloudflare | Free tier covers our needs; DDoS protection included | $0 |
| **Auth** | Streamlit-native + Google Workspace SSO | Already in your stack | $0 |
| **Email** | Postmark | Transactional, reliable, $10/mo for 10K emails | ~$10 |
| **Error tracking** | Sentry (developer plan) | Industry standard, generous free tier | $0–26 |
| **Metrics/Logs** | Datadog (Pro 5-host) | All-in-one, expensive but worth it | ~$120 |
| **Uptime monitoring** | UptimeRobot (paid) | Independent external pings | $7 |
| **On-call** | PagerDuty → Slack | 1-user starter | $21 |
| **Anthropic API** | Anthropic direct | LLM provider | ~$10 (current volume) |
| **CI/CD** | GitHub Actions | Free for public repos, 2000 min/mo on private | $0 |
| **Image registry** | GitHub Container Registry | Bundled with Actions | $0 |
| **Secrets** | AWS Secrets Manager | KMS-backed, IAM-scoped | ~$5 |
| **Database backups** | RDS automated + manual cross-region snapshots | Disaster recovery | ~$10 |
| **Pen test (annual)** | Cobalt or HackerOne | $5–8K/yr | ~$500/mo amortized |

**Subtotal infrastructure: ~$650/mo at launch.** Scales to maybe $1,500/mo at 5,000 members (mostly DB + Datadog). Annual security testing adds $6K/yr.

**Vendors I deliberately did NOT pick and why:**
- **Vercel** — great for frontends, but Streamlit deploys better as a container; not Vercel's strength
- **Snowflake / BigQuery** — overkill for 500-5K members. Postgres handles all reporting needs. Revisit at 50K.
- **Pinecone / Weaviate** — pgvector inside Postgres avoids a separate vendor + sync layer
- **DataDog APM only** — too expensive. Use Sentry for errors, Datadog only for metrics/logs.
- **Kubernetes** — explicitly avoiding. 7-person team should not run their own K8s. App Runner / Render is the right primitive.

---

## 6. Deployment & CI/CD

### 6.1 Environments

| Environment | What it is | Who uses it | Auto-deploy? |
|---|---|---|---|
| **dev** | Local Streamlit, SQLite for speed | Engineers | n/a |
| **staging** | Full prod-equivalent stack, anonymized data | Engineers + me for AI testing | Auto on push to `main` |
| **prod** | Real data, real SSO, alerts on | Whole company | Manual approval after staging green |

### 6.2 CI pipeline (GitHub Actions)

```yaml
# .github/workflows/ci.yml — what every PR runs
- lint:           ruff + black
- typecheck:      mypy --strict on app/
- test:           pytest with 80% coverage gate
- security:      bandit + pip-audit + gitleaks
- adapter-tests:  golden-file regression on all 5 sample CSVs
- llm-mock-tests: run pipeline with mocked LLM, verify match rates haven't drifted
- build:          docker build → push to ghcr.io
- deploy-staging: terraform apply to staging (if merged to main)
- smoke-test:     hit staging URL, run synthetic SA, check output
```

### 6.3 Rollout strategy

- **Blue/green for the web app** — App Runner native support
- **Database migrations:** zero-downtime only (additive changes); two-phase deploys for destructive changes
- **Feature flags:** LaunchDarkly is overkill; use a simple `feature_flags` table in Postgres + decorator pattern
- **Canary for risky changes:** route 10% of SAs to new matching logic, compare match rates for 24 hrs, then promote

---

## 7. Scaling plan

### 7.1 By customer tier

| Members | DB size | SAs/month | LLM calls/month | Infra cost | What changes |
|---|---|---|---|---|---|
| 500 (today) | <1 GB | 30 | ~500 | $650/mo | Nothing — this is the launch config |
| 1,500 | 5 GB | 90 | 1,500 | $750/mo | Bump DB to db.t4g.medium |
| 5,000 | 20 GB | 300 | 6,000 | $1,500/mo | Bump worker count, add DB read replica |
| 15,000 | 60 GB | 900 | 20,000 | $4,000/mo | Sharded DB by tenant, dedicated worker pool per priority class |
| 50,000+ | 200 GB+ | 3,000+ | 80,000+ | $10K+/mo | Time to revisit microservices? Probably still no. Time to hire a platform engineer? Yes. |

**Key insight:** Postgres scales much further than people think. You can comfortably run 50K members on a single beefy RDS instance with read replicas. **Don't pre-optimize.**

### 7.2 LLM cost scaling

LLM cost scales linearly with SAs, which scales linearly with members. Even at 15K members + 900 SAs/mo, total LLM spend is ~$50/mo. **LLM cost is never a constraint on the business; latency is.**

For latency: with Claude Haiku at ~1.5s p95 per call, a 30-line SA takes ~5s in Stage 3 (parallelized 5-way). That's well within "near-instant" UX target.

---

## 8. Reliability & observability

### 8.1 SLOs

| Metric | SLO | Why |
|---|---|---|
| **App availability** | 99.9% (43 min downtime/mo) | Sales blocked when down; member portal degraded |
| **SA latency p95** | <30 sec end-to-end | Salesperson stays in flow |
| **Stripe webhook processing** | <60 sec | Billing health must reflect reality |
| **HubSpot sync lag** | <5 min | CS team works in HubSpot; staleness causes bad decisions |
| **PDF generation p95** | <5 sec | Salesperson waiting to send the email |

### 8.2 The dashboard exec/oncall watches

| Metric | Threshold | Action |
|---|---|---|
| 5xx error rate | >0.5% sustained 5 min | Page on-call |
| SA failure rate | >5% in any 1-hr window | Page on-call |
| LLM API errors | >10/min | Auto-circuit-break, fall back to review queue |
| Daily LLM spend | >80% of cap | Slack alert; >100% hard-stop |
| Stripe webhook lag | >2 min p95 | Page on-call |
| Queue depth | >100 jobs | Auto-scale workers |
| DB CPU | >70% sustained 10 min | Investigate; bump instance if persistent |

### 8.3 Runbook coverage

Documented runbooks for the top 10 most likely incidents:
1. Anthropic API outage → fall back to review-queue mode
2. Stripe webhook flood (e.g., they re-send historical events) → idempotency check, alert if duplicates >1%
3. HubSpot rate limit hit → back off, queue, alert
4. DB connection pool exhausted → restart workers, investigate
5. Hot row contention (e.g., catalog table) → check long-running queries
6. Mismatched billing rollup → manual reconciliation procedure
7. PDF generation failure for a tenant → fall back to CSV export, log
8. Unmapped Stripe customer → flag to exception queue, slack CS team
9. Stage 3 confidence dropping over time → trigger embeddings refresh
10. Sentry alert flood → known-issue suppression rules

---

## 9. Team & talent plan

### 9.1 What it takes to operate this

| Role | FTE | Year 1 critical work |
|---|---|---|
| **Head of AI** (me) | 1.0 | Architecture, prioritization, AI/LLM choices, vendor management, build oversight |
| **Senior/Mid backend engineer** | 1.0 | Builds 80% of the production code. The technical founder + me overseeing. |
| **Part-time DevOps/SRE** | 0.25 | Set up CI/CD, infra-as-code (Terraform), incident response. Could be contractor at first. |

That's **2.25 FTE in the engineering org** for year 1. Combined with existing CS, sales, and operations folks, total team stays around 8-9 people.

### 9.2 What I'd hire next, and when

| Hire | When | Why |
|---|---|---|
| **CS engineer / RevOps analyst** | Months 4–6 | Owns the canonical mapping + reviewer queue + member health workflows. Becomes the "data backbone" person. |
| **Product designer (contract)** | Months 6–9 | Once we have real users, design the member-facing portal (NEW-6 quote bot UI, prospect-facing SA upload). |
| **Second backend engineer** | Months 9–12 | Doubles throughput. By then we should know which of the NEW-1 through NEW-10 projects to actually build. |

### 9.3 What I'd outsource forever

- Email deliverability (Postmark)
- Auth (Google SSO; don't build identity)
- Payment processing (Stripe — already in place)
- Annual pen testing (Cobalt or similar)
- Compliance auditing when SOC 2 time comes (Vanta + auditor)

---

## 10. Phased rollout

### Phase 0 (today): POC
- Streamlit Cloud, mock data, demo only. **You are here.**

### Phase 1: Internal Alpha (weeks 1–4)
- Migrate to AWS App Runner with auth + Postgres + S3
- Real catalog ingest, real adapters
- LLM mocked still — validate the matching pipeline on internal eyes only
- 5 historical SAs replayed against the new system to measure match rate
- **Success criteria:** match rate within 5pp of human baseline, no data leaks between tenants in audit

### Phase 2: Live AI (weeks 5–6)
- Wire Claude Haiku into Stage 3 with cost cap
- A/B against mock judge on the same 5 SAs
- Decide on production prompt
- Email drafter live for 1–2 reps initially
- **Success criteria:** auto-accept rate ≥75%, no LLM cost incidents, reviewer queue manageable (<10 items/SA)

### Phase 3: Stripe ↔ HubSpot live (weeks 6–8)
- Backfill canonical mapping table
- Webhooks live for new events
- Sync dashboard live in HubSpot
- **Success criteria:** all current members mapped, billing health visible in HubSpot, exception queue <5 items

### Phase 4: Rolling expansion (months 3–6)
- Open to all of sales (drops founder out of SA workflow)
- Ship NEW-2 (catalog drift), NEW-5 (auto-enrichment), NEW-9 (knowledge search)
- Start measuring impact vs roadmap projections
- **Success criteria:** SA throughput 2x current, founder time on SAs <1 hr/month, NPS on member-facing features tracked

### Phase 5: Q2 backbone (months 6–9)
- ZenOne integration (#5 from the roadmap)
- Customer health score live
- NEW-3 (spend forecast), NEW-10 (onboarding tracker)
- Start SOC 2 controls work
- Hire CS engineer

---

## 11. Risk register

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Match rate degrades after launch (real data is messier than POC) | High | Medium | Phase 1 replays historical SAs as canary. Reviewer feedback loop captures drift. |
| LLM provider lockout (account suspension, region issue) | Low | High | Anthropic + OpenAI dual-provider abstraction in matcher.py from day 1 |
| Founder bottleneck on SA review during rollout | Medium | Medium | Hire CS engineer earlier; train Sarah/Maria as backup reviewers |
| ZenOne API isn't actually queryable (screen-scrape only) | Medium | High | Phase 4 dependency — re-plan if confirmed. NEW-1 supplier APIs are similar bet. |
| Streamlit doesn't scale past 1K concurrent users | Low (we won't have that traffic) | Low | We're nowhere near this; if needed, swap to FastAPI + React. |
| Data breach / PII leak | Low | Critical | Section 4 of SECURITY_REVIEW.md addresses this; insurance + DPA + incident playbook |
| Anthropic price increases | Medium | Low | Cost is currently ~$3/mo; even 10x increase is immaterial. Cascade design also helps. |
| HubSpot API rate limit becomes binding | Medium | Medium | Queue + backoff handles it; if persistent, consider HubSpot enterprise tier |

---

## 12. What this would cost to do wrong (and right)

**The wrong way:**
- Kubernetes from day 1 ($$$, complexity tax for years)
- Microservices ($$$, distributed-systems debugging for a 7-person team)
- Build our own embeddings model ($$$, doesn't move the needle)
- Build our own auth ($$$, security debt, distraction)
- Self-host everything (no team to oncall)
- Pick a different LLM provider every quarter (no benchmarks improve fast enough to justify the migration tax)

**The right way:**
- Streamlit + Postgres + S3 + one LLM vendor + boring CI/CD
- Buy auth, monitoring, error tracking
- Build the matching logic and the data spine; everything else is buy
- Measure what matters (match rate, latency, cost per SA, reviewer minutes)
- Hire one strong engineer + part-time DevOps before you need a second engineer

This is the architecture a Head of AI worth hiring would push for. Vendor-consolidated, scope-disciplined, cost-aware, defensible at every choice.

— Abhi
