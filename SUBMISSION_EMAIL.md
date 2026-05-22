# Submission email draft

Per the case-study brief — goes to **both** addresses, includes all required items.

---

**To:** jpuhl@sourceclub.io, cduarte@sourceclub.io
**Subject:** SourceClub Case Study — Abhi (Head of AI Powered Operations, Systems & RevOps)

---

Hi Jake and Cristina,

Thank you for the case study — it was a genuinely interesting problem to work through. I treated it as one strategic problem (member acquisition economics and operating leverage at a 7-person team) and built around that lens rather than three disconnected exercises. A summary of what I'm submitting is below.

**Deliverables**

- **Written submission** (architecture, options, roadmap with $ impact, "My First 30 Days" plan): `https://github.com/abhinaykrupa/sourceclub/blob/main/SUBMISSION.md`
- **Working POC** (Streamlit app you can drive end-to-end):
  - Live demo: `https://<your-app>.streamlit.app`
  - Source: `https://github.com/abhinaykrupa/sourceclub`
  - README has local-install instructions if the live demo is down for any reason
- **Video walkthrough** (3–5 min, screen-share through the three assignments + reasoning): `<Loom link>`

**Quick navigation in the demo**

The app opens on a **Leadership Dashboard** with sections for CEO, Marketing, and Sales — that's the fastest way to see the shape of the work. From there:

- **Tab 1 — Savings Analysis:** pick any of the 5 sample files from the dropdown to drive the matching pipeline. Try "Auburn Dental (Benco)" for the clean path, then "Patterson (messy real-world export)" to see the engine handle chaos. The PDF and AI email buttons show end-to-end value.
- **Tab 2 — Stripe ↔ HubSpot Sync:** pick "Sunrise Orthodontics" in the drill-down for the multi-location case.
- **Tab 3 — 90-Day Roadmap:** prioritization, plus 10 net-new projects I'd add with dollar-impact estimates.

**Required items**

- **PayPal / Venmo for the $50:** `<your @venmo or paypal email>` *(replace before sending)*
- **Time spent:** ~`<X>` hours
- **Comments / feedback:** *(optional — see below for what I'd add)*

**A few notes on choices I made**

- **Mocked LLM calls intentionally.** The POC runs with zero setup so you can drive it without any API keys. The Stage-3 LLM judge and the email drafter are rule-based mocks that mimic Claude Haiku/Sonnet output. Production prompts are included in the code as docstrings; swapping in real API calls is a one-function change.
- **Supplier adapters over generic AI matching.** The training videos make clear that each supplier exports a different shape. Adapters before matching is what makes the manual workflow today reliable; I kept that structure.
- **Built it for executives, not just analysts.** The Leadership Dashboard tab came after I re-read the brief and assumed the actual users are leadership making bets, not the founder running individual SAs. That changes the product significantly.

**Optional links**

- GitHub: `https://github.com/abhinaykrupa`
- *(Add LinkedIn / portfolio / prior work if you want)*

Looking forward to discussing. Happy to walk through the POC live and answer anything the video doesn't cover.

Best,
Abhi

---

## Pre-send checklist

- [ ] Replace `<your-app>.streamlit.app` with the actual deployed URL (once Streamlit Cloud is live)
- [ ] Replace `<Loom link>` with the recorded video URL
- [ ] Replace `<your @venmo or paypal email>` with your actual payment handle — **this one is required or they can't pay you**
- [ ] Replace `<X>` with hours spent on the case study
- [ ] Add LinkedIn / portfolio links in the "Optional links" section if you want
- [ ] Send to **both** addresses (jpuhl@ AND cduarte@) — the brief is explicit about this
- [ ] Send from your usual address (the one you applied with)
