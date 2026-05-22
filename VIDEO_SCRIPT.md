# Assignment 4 — Video Walkthrough Script (3–5 min)

**Goal:** Walk through Assignments 1, 2, 3 — what I decided and *why* — screen-sharing the working app. Lead with the working thing. Emphasize reasoning. Stop under 5 minutes.

**Setup before recording:**
- App already loaded on the Leadership Dashboard
- Browser zoomed so text is readable
- Have the "Auburn Dental (Benco)" sample pre-selected OR ready to pick in one click
- Close other tabs / notifications
- Loom or QuickTime, screen + small webcam bubble

**Timing target:** ~4 minutes. Leaves buffer under the 5-min cap.

---

## [0:00–0:25] Open — hook + frame (25 sec)

> "Hi, I'm Abhi. Over the last few hours I built a working prototype that covers all three assignments — so instead of talking through slides, I'll show you the actual thing running and explain the decisions behind it.
>
> Quick framing: I treated this as one problem, not three. SourceClub's whole engine is *get a prospect to see their savings number* — because 90% of practices who see it join. So everything I built points at making that engine faster and the data behind it trustworthy."

*(This signals you read their site, understood the business, and you ship working things.)*

---

## [0:25–2:00] Assignment 1 — Savings Analysis (the big one, ~95 sec)

**[SCREEN: Savings Analysis tab. Pick the Benco sample file.]**

> "Assignment 1 — automating the savings analysis. This is the founder's biggest time sink today: about 10 minutes a file, 20–40 times a month.
>
> I'm dropping in a sample Benco purchase history. Watch what happens —"

**[SCREEN: it auto-detects supplier, parses, runs. Point at the summary metrics.]**

> "It auto-detected the supplier, parsed that supplier's specific format, and ran a matching engine. $12,600 in current spend, $5,100 in identified savings — about 40%.
>
> Here's the key decision: **the matching is three stages, not one.**"

**[SCREEN: expand the 'Pipeline architecture' section briefly, or just talk over the results.]**

> "Stage one is deterministic — exact SKU matches, no AI needed, handles the easy 30-40%. Stage two is semantic search for the fuzzy ones. Stage three is where an LLM adjudicates the hard cases. I deliberately *don't* lead with AI — most line items don't need it, and using it everywhere is slower and noisier.
>
> The piece I'm proudest of: **unit-of-measure checking.** The hardest part of this whole problem is 'box of 100' versus 'case of 10 boxes' — same product, totally different unit price. That's its own check, and any mismatch gets forced to a human."

**[SCREEN: scroll to the review queue. Expand one item.]**

> "Which brings up the most important design choice — **human-in-the-loop is the spec, not a fallback.** High-confidence matches auto-accept. Anything uncertain, or high-dollar, or with a unit mismatch routes here to a review queue. That mirrors their '3x ROI guaranteed or we tell you not to join' — the system has to be honest about what it's unsure of."

**[SCREEN: click 'Generate PDF' and 'Draft AI email'.]**

> "And because the savings analysis *is* the sale, I didn't stop at a table on screen. One click generates a branded PDF the rep sends the prospect, and another drafts the follow-up email personalized to their savings. That's the full loop — file in, closed-deal-ready output out."

*(If short on time, cut the PDF/email demo to a single sentence.)*

---

## [2:00–2:45] Assignment 2 — Stripe ↔ HubSpot (~45 sec)

**[SCREEN: switch to the Sync tab.]**

> "Assignment 2 — connecting Stripe billing to HubSpot. The problem is one company has many locations, each its own Stripe subscription, and the names don't line up. So nobody can open a company in HubSpot and see billing health.
>
> I looked at three options — native integration, middleware like Zapier, or a custom sync. I picked **custom sync with a canonical mapping table**, and here's the why that matters most:"

**[SCREEN: point at the company rollup table, then the Sunrise Orthodontics drill-down.]**

> "Native integrations dump data onto deals, not the company, and can't roll up multi-location MRR. But the real reason is this mapping table isn't just for billing — it's the same data spine the customer health score and the ordering-data integration both need later. You build it once here and it pays off three more times. That's the difference between solving a ticket and building infrastructure."

---

## [2:45–3:30] Assignment 3 — Roadmap (~45 sec)

**[SCREEN: switch to the 90-Day Roadmap tab.]**

> "Assignment 3 — prioritizing the project queue. My one principle: **sequence by dependency and revenue leverage, not by urgency labels.**
>
> Savings analysis automation is first — it's the revenue bottleneck. Stripe-HubSpot sync second, because it's the data spine everything downstream needs. Then customer service consolidation, a quick onboarding win, and the ZenOne data integration that unlocks all of Q2.
>
> The part I'd point to as judgment: I explicitly say what *not* to do first. The unified dashboard and the customer health score get pitched a lot — but they're garbage-in until the data spine underneath them is clean. Doing them early builds a number nobody trusts."

**[SCREEN: scroll to the proposed projects table with $ impact.]**

> "I also added ten projects of my own with dollar estimates, sized to their actual scale — about 500 members, $2.5M in revenue — so the numbers are defensible, not inflated."

---

## [3:30–4:00] Close — strategic teaser + sign-off (~30 sec)

> "That covers the three assignments. I'll flag one thing beyond the ask: I also wrote up how I'd think about *growing* this 10x as the Head of AI — self-serve savings analysis, an enterprise tier, association partnerships. That's in the repo as a strategic addendum if you want to see how I think about the bigger picture.
>
> Everything here is a working prototype on real-shaped data — the LLM calls are mocked but the architecture is API-ready, and I documented exactly what production would take. Thanks for the time, I really enjoyed this one. Happy to go deeper on any piece."

---

## One-glance cheat sheet (if you'd rather riff than read)

| Time | Section | Hit these points |
|---|---|---|
| 0:00 | Hook | Working demo not slides · "SA is the close — 90% who see numbers join" |
| 0:25 | **A1** | Drop Benco file → it runs · 3-stage (det → semantic → LLM) · **UOM checking** · human-in-loop is the spec · PDF + email = full loop |
| 2:00 | **A2** | 3 options → custom sync + canonical map · **the map is the data spine 3 other projects reuse** |
| 2:45 | **A3** | Dependency not urgency · top 5 · **what NOT to do first** (dashboard/health score = garbage-in) · 10 own ideas with $ |
| 3:30 | Close | Teaser: 10x strategic addendum · mocked LLM but API-ready · thanks |

## Things to deliberately NOT do in the video
- ❌ Don't read the architecture diagrams line by line — point and summarize
- ❌ Don't spend more than 30 sec on the strategic extras — the ask is the 3 assignments
- ❌ Don't apologize for mocked LLM — frame it as a deliberate, documented choice
- ❌ Don't go over 5:00 — they explicitly capped it. Aim for 4:00.
