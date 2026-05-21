# SourceClub Case Study: Head of AI Powered Operations & Systems
**Candidate:** Abhi
**Date:** May 21, 2026

---

## Assignment 1 — “Savings Analysis” Automation

### The Problem
Matching noisy, non-standardized line items from prospect purchase histories to the SourceClub pricing catalog. Currently a manual process taking 10 minutes per analysis.

### Proposed Architecture
I propose a **"Hybrid AI Pipeline"** that combines Vector Search for speed and LLM-based reasoning for accuracy.

#### 1. Ingestion & Extraction (OCR)
- **Tool:** Claude 3.5 Sonnet / GPT-4o-mini (Base64 PDF/Image input).
- **Process:** Extract structured JSON (Description, SKU, Qty, Unit Price) from invoices. Standard OCR often fails on complex table layouts; LLMs handle this natively.

#### 2. The Matching Engine (Vector + LLM)
- **Vector Search:** The SourceClub catalog is embedded and stored in a vector database (Pinecone or Chroma).
- **Semantic Retrieval:** For each prospect item, we pull the top 5 closest matches.
- **LLM Re-ranking:** A smaller, faster model (Claude 3.5 Haiku) is given the prospect item and the top 5 candidates.
- **Intelligence:** The LLM resolves discrepancies like:
    - `"bx"` vs `"box"` vs `"box of 100"` (Unit of Measure normalization).
    - Brand names vs. Generic equivalents.
    - Manufacturer SKU partial matches.

#### 3. Human-in-the-Loop (HITL)
- **Confidence Scoring:**
    - **Score > 90%:** Auto-approve and add to report.
    - **Score < 90%:** Flag in a **Notion "Savings Review" DB**. The founder or a VA can click "Yes/No" or manually override. This feedback is used to further fine-tune the matching logic.

#### 4. Deliverable
- **Output:** A polished PDF or Google Sheet generated automatically via API (using a template).

### Proof of Concept (POC)
I have built a Python-based POC (`case_study/assignment_1/savings_analysis_poc.py`) that demonstrates the matching logic. 
- It simulates the fuzzy matching process.
- It highlights items that require "Review" (where the LLM would be invoked).
- It calculates instant monthly and annual savings.

### Next Steps with More Time
- **Automatic Unit Conversion:** Build a specific logic layer to handle price normalization (e.g., if prospect buys a case and we sell by the box).
- **Feedback Loop:** Store every confirmed match in a "Matching Memory" (Vector DB) so the system gets smarter with every analysis.

---

## Assignment 2 — Systems Architecture: Connecting Stripe and HubSpot

### The Situation
Stripe (Billing) and HubSpot (CRM) are disconnected. Multi-location practices have multiple subscriptions in Stripe but should map to a single Company in HubSpot.

### Option 1: Native HubSpot-Stripe Integration
- **Pros:** Zero-code, 10-minute setup.
- **Cons:** Rigid mapping. It often syncs data to "Deals" or "Invoices" rather than the "Company" record. Hard to handle the multi-subscription-to-one-company mapping without manual cleanup.

### Option 2: Middleware (Make.com / Zapier) - **RECOMMENDED**
- **Pros:** Extremely flexible. We can build a workflow that:
    1. Triggers on a new Stripe Subscription.
    2. Searches HubSpot for a Company with a matching domain or "Customer ID".
    3. Aggregates data (e.g., sums up total MRR from multiple subscriptions).
    4. Updates custom HubSpot properties like `[Billing] Status`, `[Billing] Annual Revenue`.
- **Cons:** Minimal monthly cost ($30-$50).

### Option 3: Custom Sync Service (AWS Lambda / Node.js)
- **Pros:** Total control. Can handle complex edge cases (e.g., if names differ significantly).
- **Cons:** High maintenance. Requires a developer to fix if the API changes.

### Final Recommendation: Option 2 (Make.com)
**Justification:** 
SourceClub is a lean team of 7. You need **"The simplest thing that works"** and is maintainable without a full-time DevOps engineer. Make.com provides the visual mapping required for complex multi-location logic while remaining low-cost and high-reliability. It turns HubSpot into the "Single Source of Truth" that the sales and success teams need.

---

## Assignment 3 — Prioritizing Upcoming Projects

If I were in the seat for the first 90 days, here is how I would sequence the work to maximize leverage:

### 1. Savings Analysis Automation (P0)
- **Why:** This is the #1 bottleneck for Growth. Automating this doubles the "Sales Capacity" of the founder immediately. It is the core value proposition.

### 2. Stripe-HubSpot Data Sync (P1)
- **Why:** You cannot manage what you cannot measure. Visibility into billing health directly in the CRM allows the Customer Success team to be proactive about churn and the Sales team to see which leads converted.

### 3. Vendor Data/Pricing Sync (P1)
- **Why:** The Savings Analysis is only as accurate as the pricing data. Automating the ingestion of supplier price lists (Benco, Schein, etc.) into the "Master Catalog" ensures we aren't quoting outdated savings.

### 4. Automated Onboarding Pipeline (P2)
- **Why:** Once a member joins, the "Time to Value" (ordering their first discounted item) is critical. Automating the account setup with vendors reduces the manual burden on the CS team.

### 5. AI-Powered Lifecycle Comms (P3)
- **Why:** "Found money" for the members. Using AI to analyze spend patterns and alert members when they are overpaying or missing a discount opportunity increases member stickiness (LTV).

---

## Summary of Deliverables
- **Architecture:** Described above.
- **POC Code:** `case_study/assignment_1/savings_analysis_poc.py`
- **Video Walkthrough:** (To be recorded by the candidate)
