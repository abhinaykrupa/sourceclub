# Security Review — SourceClub Operations POC

**Scope:** the Streamlit POC in this repo, as currently structured.
**Audience:** SourceClub leadership + whoever's responsible for moving this from POC → production.
**Verdict:** **acceptable for a public POC with mock data**, **not acceptable for processing real prospect/member data without the changes in §4.**

---

## 1. POC threat model (what this code is exposed to today)

| Surface | Exposure | Risk if compromised |
|---|---|---|
| Public Streamlit Cloud URL | Anyone with the link | Mock data only — low. No PII, no money, no API keys. |
| File upload (CSV) | Arbitrary content from any visitor | Possible memory exhaustion, CSV-injection downstream, parser crashes |
| GitHub repo | Public source | Code is the demo — intentional. No secrets committed. |
| User browser → app | Standard HTTP traffic | Streamlit Cloud handles TLS termination |

**Bottom line for the POC:** the only sensitive thing here is *Abhi's reputation with the recruiter*. There is no live PII, no money flow, no API keys. The acceptable risk surface is small.

---

## 2. Findings — POC code

### 2.1 `unsafe_allow_html=True` usage
**Files:** `app/main.py` (hero, styling), `app/views/dashboard.py` (section headers, page header)
**Risk:** XSS if user-controlled data were interpolated into the HTML.
**Status:** ✅ **Safe.** All interpolated values are either (a) hardcoded strings from `pipeline_data.py`, (b) deterministic computed values (dates, sums), or (c) controlled by our own theme tokens. **No CSV-uploaded content is rendered via unsafe HTML.** Uploaded data is shown via `st.dataframe()`, `st.text()`, `st.text_area()` — all of which auto-escape.
**Production action:** if a future feature needs to render uploaded-data fields as HTML (e.g., a markdown-rendered email preview), wrap with `html.escape()` or a sanitizer first.

### 2.2 CSV ingestion
**File:** `app/engine/adapters/*.py`
**Risks:**
- **Memory exhaustion:** `pandas.read_csv()` loads entire file into memory. Malicious 1GB file = OOM.
- **CSV injection downstream:** if a cell contains `=cmd|'/k calc'!A1`, opening the *exported audit CSV* in Excel could execute commands. The POC doesn't pre-strip these.
- **Pathological column counts:** `skipinitialspace=True` is set; parsing is otherwise standard.
**Status:** ⚠️ **Acceptable for POC, not for production.**
**POC mitigations already in place:** Streamlit's file uploader has a default upload size limit (~200MB). Adapters parse a known schema and reject unexpected files at the supplier filter step.
**Production action:** (a) enforce a 5–10 MB upload cap, (b) strip leading `=`, `+`, `-`, `@` from cell values before exporting CSVs, (c) cap row count at the adapter level (e.g., reject >50K rows), (d) wrap `read_csv` in a `try/except` that returns a user-friendly error instead of stack trace.

### 2.3 PDF generation (reportlab)
**File:** `app/app_helpers/pdf_generator.py`
**Risk:** customer_name and supplier_name are interpolated into the PDF via `Paragraph()`.
**Status:** ✅ **Safe.** ReportLab's `Paragraph` parses a constrained XML subset; it does not execute scripts. Long strings get truncated visually but not executed.
**Production action:** none required.

### 2.4 No code execution surface
**Status:** ✅ **Confirmed safe.** Audit (`grep -rn 'eval\|exec\|subprocess\|os.system\|shell=True'`) shows no use of dynamic Python execution, no shell commands, no SQL (no database), no file writes outside intended paths.

### 2.5 No secrets in code
**Status:** ✅ **Confirmed.** No API keys, tokens, passwords, or credentials committed. The `.gitignore` excludes `.env`, `.streamlit/secrets.toml`, `.claude/settings.local.json`. Verified via inspection.

### 2.6 Streamlit session isolation
**Status:** ✅ **Adequate for POC.** Streamlit's `session_state` is per-browser-session and not shared between users. Uploaded files are processed in-memory and discarded when the session ends.
**Caveat:** *do not assume this is a multi-tenant safe pattern.* For production with real PII, move to a proper auth + database per-tenant model.

---

## 3. Findings — Dependency hygiene

`requirements.txt` pins minimum versions but does not lock exact ones. The 4 direct dependencies (streamlit, pandas, plotly, reportlab) are well-maintained, widely-used packages with active security teams.

**POC action:** run `pip-audit` or `pip list --outdated` before each demo refresh.

**Production action:**
- Lock with `pip-tools` (`requirements.in` + compiled `requirements.txt`)
- Run `pip-audit` in CI on every PR
- Subscribe to Dependabot for transitive vulns
- Run `safety check` for known CVE database hits

---

## 4. What MUST change before processing real prospect/member data

The POC was designed to run on mock data. Real PII (prospect purchase histories include practice name, supplier identifiers, spend levels) and member billing data require these gates before going live:

### 4.1 Authentication & authorization
- **Auth:** OAuth/SSO via Google Workspace (most dental practices already use it) or Microsoft 365. Use Streamlit's built-in auth, Auth0, or Clerk.
- **Authorization:** role-based — Sales rep sees only their pipeline; CS sees only their accounts; CEO sees all. Implement at the data layer, not just the UI.
- **Session timeout:** 30 min idle, hard cap 8 hrs.
- **Audit log:** every login, every data access, every export. Stored separately from the app DB. Retention 1 year minimum.

### 4.2 Data protection
- **At rest:** all DB volumes encrypted with KMS-managed keys.
- **In transit:** TLS 1.3 enforced. HSTS header. No HTTP fallback.
- **In processing:** PII fields (practice name, contact emails) flagged in schema, redacted in logs.
- **Backups:** encrypted, geo-replicated, retention policy (e.g., 30 days hot, 1 year cold).
- **Deletion:** documented right-to-delete process. Cascade delete across all systems (DB, S3, vector store, LLM cache, backups).

### 4.3 Multi-tenancy
- The POC has no concept of tenants. Production: every row in every table gets a `tenant_id`. Enforce with Postgres row-level security (RLS) — defense in depth even if app code has a bug.
- Separate per-tenant S3 prefixes for file uploads + generated PDFs.

### 4.4 Input validation hardening
- File upload size cap (5–10 MB).
- File type validation by magic bytes, not extension.
- Row count cap per file (50K).
- CSV-injection prevention on export: strip `=`, `+`, `-`, `@`, `\t`, `\r` from cell values, or quote-wrap suspicious values.
- Rate limit per IP / per session (e.g., 10 uploads/hour).

### 4.5 LLM-specific (when Stage 3 becomes a real Claude call)
- **Prompt injection defense:** prospect file contents flow into LLM prompts. Treat all prospect-supplied text as untrusted. Use a delimiter pattern + explicit instructions to ignore embedded instructions.
- **PII before LLM:** redact contact emails, phone numbers, full addresses before sending to Anthropic. Send the minimum needed (description, SKU, quantity, price).
- **DPA with Anthropic:** sign a Data Processing Agreement. Their default API does not train on inputs but get this in writing.
- **Output validation:** never trust raw LLM output. Parse the JSON, validate against schema, reject if confidence outside [0, 1], fall back to no-match if invalid.
- **Cost guardrails:** per-tenant daily LLM spend cap, alerting on anomalies.

### 4.6 Logging, monitoring, incident response
- **Application logs:** structured JSON, no PII, shipped to centralized logging (Datadog, BetterStack, or self-hosted Loki).
- **Error tracking:** Sentry for exceptions.
- **Uptime monitoring:** UptimeRobot / Better Stack — external pings.
- **Alerts:** PagerDuty (or Slack-based for a 7-person team) on (a) 5xx error rate >1%, (b) latency p99 >5s, (c) auth failures spike, (d) LLM cost overrun.
- **Incident playbook:** documented response for (a) suspected breach, (b) data loss, (c) auth failure spike, (d) LLM cost spike.

### 4.7 CI/CD security
- **No secrets in git** — already enforced by `.gitignore`, double-check with `gitleaks` in CI.
- **Branch protection:** main locked, requires PR review.
- **Pre-merge:** `pip-audit`, `bandit` for Python security linting, `gitleaks` for secret scanning, run the smoke test.
- **Image scanning:** if containerized, scan with Trivy or Snyk before deploy.
- **Deploy pipeline:** GitHub Actions → build container → push to registry → roll out to staging → run smoke tests → approve to prod.

### 4.8 Compliance posture (likely relevant for SourceClub)
- **HIPAA:** SourceClub probably *does not* process PHI directly (dental supply orders ≠ patient records). Confirm with counsel. If any patient-identifying data ever enters the system (e.g., via member-uploaded EHRs or order notes), HIPAA applies — BAA with Anthropic, encrypted-everywhere, audit log retention 6 years.
- **SOC 2 Type II:** likely required by enterprise dental groups within 12 months of meaningful growth. Start the controls work in year one even if formal audit is deferred.
- **GDPR/CCPA:** if any members are international or California-based, applies. Standard right-to-access + right-to-delete flows.
- **PCI:** Stripe handles card data — SourceClub stays out of PCI scope as long as the app never touches card numbers directly (use Stripe Elements / Checkout).

---

## 5. Recommended security roadmap

| Phase | What | Why now |
|---|---|---|
| **Day 1 of production work** | Lock dependencies, add `pip-audit` to CI, add `gitleaks` to CI | Free hygiene, prevents foot-guns |
| **Pre-real-data launch** | Auth (SSO), encrypted DB, multi-tenancy, audit log | Hard prerequisites for processing PII |
| **First 90 days** | Centralized logging, Sentry, uptime monitoring, incident playbook | You don't know what you don't see |
| **Month 4–6** | Penetration test (external vendor), threat model review, security training for the team | Catch what internal review misses |
| **Year 1** | SOC 2 Type II readiness (controls + evidence), security policies documented | Required for enterprise sales |

This is **the realistic security path for a 7-person team** — not the maximalist FAANG version. Spend the first month on the basics (auth, encryption, multi-tenancy, audit log); the rest follows as you grow.

---

## 6. What I'd hand to the team as a one-pager

> **Today's POC** ships on Streamlit Community Cloud with mock data. It is **not** approved for real prospect or member data. To unlock that:
>
> 1. Add SSO (Google Workspace)
> 2. Add per-tenant data isolation (Postgres + RLS)
> 3. Sign DPA with Anthropic + redact PII before any LLM call
> 4. Stand up audit logging
>
> Estimated effort: **2 engineer-weeks for items 1–4** plus 1 week of soak-testing. Until those are in place, all "real" SAs continue to run in the existing manual workflow.

— Abhi
