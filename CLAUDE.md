# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Case study deliverable for **SourceClub — Head of AI Powered Operations, Systems & RevOps**. A Streamlit POC + written submission covering three assignments: savings analysis automation, Stripe↔HubSpot multi-location sync, and a 90-day project roadmap.

## Source of truth for the original ask

**Always consult `assignments.md` first** when scope, intent, or requirements are in question. It contains:
- The recruiter email (from Cristina Duarte) and case-study brief
- All 4 assignment descriptions verbatim from Notion
- The SourceClub project queue (used in Assignment 3)
- Summaries extracted from the training Loom videos (manual workflow per supplier)
- Suggestions from other LLMs (Gemini, Perplexity) — used as input, not gospel

Do not confuse `assignments.md` (the brief) with `requirements.txt` (Python deps).

## Running the app

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run app/main.py
```

Opens at `http://localhost:8501`. Tab 1 has a sample-file dropdown — pick any of the 4 to see the pipeline run.

## Project layout

```
app/
  main.py                  Streamlit UI — 3 tabs
  engine/
    matcher.py             3-stage matching engine + UOM/pack-size normalization
    adapters/              Per-supplier parsers: benco, henry_schein, darby, base86, auto_detect
  sync/
    mock_data.py           Mock Stripe customers/subs + HubSpot companies/locations
    sync_engine.py         Canonical mapping + per-company billing rollup
sample_data/
  sourceclub_catalog.csv   ~40 negotiated-price items
  *_<supplier>.csv         4 sample supplier exports (Auburn/Benco, Demit/Schein, Quincy/Darby, Auburn/Base86)
SUBMISSION.md              Full written deliverable (what gets emailed to recruiter)
README.md                  Recruiter-facing install + demo guide
assignments.md             ⚠️ Original brief — read this first for any scope question
```

The earlier Gemini-generated `case_study/` drafts were removed during cleanup. The canonical deliverables in the repo root are:
- `SUBMISSION.md` — what the recruiter reads
- `SUBMISSION_EMAIL.md` — the email draft to send
- `SECURITY_REVIEW.md` — security analysis of the POC + production gates
- `PRODUCTION_ARCHITECTURE.md` — the "what does v1 production look like" doc

## Architecture notes

**3-stage matching engine** (in `app/engine/matcher.py`):
| Stage | Function | Production equivalent |
|---|---|---|
| Deterministic | `stage1_deterministic` | Exact SKU / Mfg SKU lookup (same as POC) |
| Semantic | `stage2_candidates` | pgvector + sentence-transformers embeddings (POC uses difflib + token overlap) |
| LLM Judge | `stage3_llm_judge` | Claude Haiku with structured JSON output (POC uses rule-based mock) |
| Cross-cut | `check_uom_alignment` | Same — regex-based UOM/pack-size parser (real logic, not mocked) |

**LLM and external APIs are all mocked.** The mocks are explicit and clearly labeled. Production swap-in points:
- `stage3_llm_judge` → real Claude Haiku call
- `app/sync/mock_data.py` → real Stripe + HubSpot API reads

## Important constraints

- **No API keys required.** Demo runs fully offline. Don't add Anthropic/OpenAI SDK calls without explicit user instruction.
- **Recruiter is the audience.** Code quality matters less than the UI demo and the written submission reading well. Prioritize clarity in `SUBMISSION.md` and visual polish in `app/main.py` over engineering elegance elsewhere.
- **Stay terse.** User prefers concise, unhedged responses (see `/Volumes/ag/.claude/CLAUDE.md` for global preferences).
