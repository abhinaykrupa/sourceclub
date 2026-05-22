# Strategic Addendum — Beyond the Three Assignments

**Author:** Abhi
**Context:** What I'd put on the table in the first leadership meeting after joining. Less "case study answer," more "here's how I'd think about growing this business as Head of AI / functional CTO."
**Audience:** SourceClub CEO + VP of Growth (the people I'd interview with next).

---

## Why this doc exists

The three case-study assignments are tactical. Reading them is necessary; treating them as the whole picture is wrong. The job description explicitly says this role owns "systems, automations, data, and AI workflows that let a team this size run like a much bigger one" — that's a CTO-with-AI-bent description, not a build-the-savings-analysis-tool description.

So this doc answers: **if I had the keys to the technology and data layer on day one, what would I push for in the first six quarters?**

It's organized around three growth levers:
1. **Acquire more members faster** (revenue growth)
2. **Make each member worth more, longer** (LTV expansion + retention)
3. **Run the company on less per dollar of revenue** (operating leverage)

Plus a fourth section on **defensive moats** because at a $2.5M-ARR startup, the next competitor is always 12 months behind you.

---

## What I learned from the website that re-frames everything

Quoting the SourceClub homepage directly:

- **"90% of practices who see their numbers join"** ← The savings analysis IS the close, not a step toward it.
- **"3x ROI guaranteed, or Source Club tells you not to join"** ← They actively *disqualify* prospects when the math doesn't work. That's incredibly disciplined and rare.
- **"$97K avg annual savings per practice"** ← The unit economics for a member are enormous.
- **"Supply costs 7-12% → 3-4% of revenue"** ← This is the headline metric, not dollars.
- **"Cancel anytime. No contracts."** ← Retention has to be earned every month.
- **"One login. All suppliers."** ← They already have a multi-supplier ordering platform.

These five facts should drive every technology investment. Specifically:

1. The single highest-leverage AI investment is **getting more prospects to the "see their numbers" moment**, because conversion from there is already 90%.
2. The single highest-leverage retention investment is **continuously proving the math** to existing members, because they can cancel any time.
3. The SourceClub business model is fundamentally a **data-and-leverage flywheel** (more members → more buying power → deeper discounts → better savings analyses → more members). Everything that grows the data side compounds.

---

## Lever 1 — Acquire more members faster

The current funnel:
```
Prospect aware → discovery call → uploads purchase history → SA delivered → 90% close
```

The bottleneck isn't conversion. It's **getting prospects to upload their purchase history.** That's the gate.

### 1.1 Self-Serve Savings Analysis (the single biggest lever)
**Concept:** A landing page where a prospect uploads their supplier export and gets an instant savings analysis with one click. No sales rep. No discovery call. No friction.

**Why it works for SourceClub specifically:**
- Conversion from SA → close is already 90%.
- The bottleneck today is *human availability* on the sales side.
- Self-serve removes the bottleneck entirely.
- 24/7 lead capture. Inbound from Google Ads, content marketing, partner referrals all funnel here.

**What it requires:**
- Existing matching engine (we've built the POC).
- A "soft" disclaimer about confidence/accuracy.
- Email gate so we capture leads.
- Auto-email follow-up if savings >3x ROI: "Your SA shows $X savings. Book a 15-min call to start."
- A different flow if savings <3x: "Honest finding — we'd save you $X, which isn't worth our membership fee for your practice size. Here's free advice on category Y where you're already optimal."

**Quantified upside (conservative):**
- Today: 20-40 SAs/month at 90% conversion = 18-36 new members/month.
- With self-serve: 100-200 SAs/month (most don't convert because volume includes tire-kickers) at 30% conversion = 30-60 new members/month.
- **Net effect: ~doubling acquisition rate without adding sales headcount.**

**Effort:** 4-6 weeks (the matching engine already exists; needs landing page, email gating, follow-up automation).

### 1.2 Prospect Auto-Enrichment + AI Discovery Brief
**Concept:** When a prospect fills the form, an AI agent does the prep work the sales rep would do manually: pulls practice size from public sources, identifies likely current supplier from the export, drafts a personalized opening for the rep.

**Why now:** rep prep time per discovery call is probably 15-30 minutes. Eliminate it.

**Effort:** 1-2 weeks. Built on top of the SA pipeline.

### 1.3 Referral-Driven Acquisition Engine
**Concept:** At 90% conversion on SAs, the cheapest customer is a referral (their friend will also probably convert at 90%). Build a structured referral program with member-facing incentives:
- "Refer a practice → if they join, you get $500 credit toward your membership."
- AI-drafted "intro to your colleague" templates so members don't have to think.
- Track referrals in HubSpot, attribute revenue, pay out automatically.

**Effort:** 2 weeks. Mostly HubSpot workflow + email + tracking.

### 1.4 Conference / Trade-Show Lead Capture
**Concept:** Reps at dental conferences (Greater NY Dental, ADA, Chicago Midwinter) collect business cards / scan badges. Tonight, the system AI-enriches each lead, queues them for self-serve SA the next morning, and the rep gets a pre-drafted follow-up email per lead.

**Effort:** 1 week (mostly integrations).

---

## Lever 2 — Make each member worth more, longer

Cancel-anytime + no contracts = retention is the most fragile and most valuable part of the model.

### 2.1 Continuous Savings Proof (Monthly "Member Statement")
**Concept:** Every month, automated email/in-app statement: "This month you spent $X. Without SourceClub, you would have spent $Y. We saved you $Z. Year-to-date: $A saved. Your ROI: B.Cx."

**Why this matters:** The value prop fades from memory two months after onboarding. A monthly reminder makes the savings *visible* — defends against cancellation.

**Tech needed:** Already-existing app.sourceclub.com order data + comparison to "would-have" pricing from supplier portals. Mostly ETL + email templating.

**Effort:** 2 weeks. **Probably the single highest-ROI retention project.**

### 2.2 Catalog Compliance Monitor (not "drift monitor")
**Concept refined from earlier:** Their prices are *contractually locked* for 6 months with 2 adjustment windows. So this isn't really drift monitoring — it's **contract compliance monitoring**. Daily check: did any supplier invoice come in with a price >locked rate? If yes, auto-file a price-match claim, alert SC ops.

**Why it matters:** Supplier billing systems make mistakes. Without monitoring, every uncaught error is a broken promise to the member and a chip away at trust.

**Effort:** 1 week. Built on top of supplier API integrations.

### 2.3 Member Health Score with Auto-Intervention
**Concept:** Beyond a passive "score," tie it to automated nudges:
- Spend dropped 25% MoM → CS rep gets alert + AI-drafted check-in email
- Order frequency dropped → "missing something?" outreach
- Logged into app.sourceclub.com less than once/month → AI-drafted re-engagement email with a relevant cross-sell

**Effort:** 2-3 weeks (depends on existing CS workflow).

### 2.4 Cross-Sell into Adjacent Spend Categories
**Concept:** Use member spend data to identify what they're *not* buying through SC but probably could. Examples:
- They buy gloves through SC but anesthetics from Patterson direct → SC has Patterson pricing too, surface it.
- They buy through SC but at lower volumes than peer practices → maybe they don't know about bulk discounts.
- They buy generics — and they're equally good — but a peer practice just switched to a branded alternative at 2x cost → wrong direction, alert.

**Effort:** 2-3 weeks (needs ZenOne integration first).

### 2.5 Equipment Financing as Membership Add-On
**Concept:** Members buy big-ticket equipment (chairs $8K, cone-beam X-ray $50K, autoclaves $4K) periodically. Today they finance through CareCredit or vendor financing at 15-22% APR. Partner with a B2B lender and offer SC members financing at 9-12% APR. Take 1-2% spread.

**Revenue impact:** At 500 members, ~50 equipment purchases/year averaging $15K each = $750K in financed volume. 1.5% spread = $11K/yr. Small in dollars but builds stickiness — once a member finances through SC, switching cost is materially higher.

**Effort:** Mostly business development (find a lender partner), not engineering. Tech is ~1 week (a portal page + lender API integration).

### 2.6 Practice Sale-Prep Service
**Concept:** Practices considering sale to a DSO get evaluated on supply efficiency. SC has the data to prove "this practice has industry-best supply costs (3.5% of revenue vs 8% peer median) — worth $X more at sale." Charge a flat $5K advisory fee or take % of sale uplift.

**Why this is brilliant for SC:** the only competitor narrative is "but DSOs will buy you." This service makes SC part of *that* exit, not threatened by it. Some members leave to DSO regardless — SC takes a cut on the way out.

**Effort:** Mostly product positioning + business development. Tech: ~1 week to package the data into a sellable report.

---

## Lever 3 — Run the company on less per dollar of revenue

A 7-person team at $2.5M ARR = $357K rev/employee. Healthy but optimizable.

### 3.1 AI-Powered Supplier Negotiation Prep
**Concept:** Before quarterly supplier negotiations, an AI agent analyzes:
- Aggregate spend across all 500 members for each supplier
- Categories where SC is over-/under-indexed vs market benchmarks
- Where prices are out of pattern vs known cost basis
- Where competing suppliers offer better terms

Outputs: a structured brief for the human negotiator. "Talk to Henry Schein about category X — we're buying $Y/yr at a margin Z above industry, here's the asking price we should anchor to."

**Why this matters:** Better supplier deals = deeper discounts for members = stronger value prop = higher conversion + retention. The flywheel compounds.

**Effort:** 3-4 weeks. Needs ZenOne + supplier data + market benchmark data.

### 3.2 Self-Serve Member Onboarding
**Concept:** Today the team does Day 1 / 30 / 60 / 90 calls. Convert the call cadence into:
- Day 1: automated video walkthrough + interactive product tour
- Day 30: AI-drafted personalized check-in email with member's actual savings data
- Day 60: AI-drafted optimization suggestions based on their spend pattern
- Day 90: only call schedule on demand or if health score flags

Reserve human calls for accounts >$10K MRR or showing risk signals.

**Effort:** 3-4 weeks. Saves ~10 hrs/week of CS time = 0.25 FTE = $25-35K/yr at SC's cost structure.

### 3.3 AI-First Internal Knowledge System
**Concept:** Repurposed from NEW-9 but elevated. Everything the team needs to do their job, indexed and queryable:
- SOPs, supplier contracts, member notes
- Past savings analyses (for reference / training the matching engine)
- Sales call recordings (Gong/Fathom transcripts), surfaceable
- Negotiation memory ("when was the last Patterson conversation about gloves? What did they offer?")

This is the company brain. Critical at scale, transformative even at 7 people.

**Effort:** 1-2 weeks for v1; ongoing for content curation.

### 3.4 Replace Tools, Don't Add Them
**Concept:** Audit the SaaS stack. A 7-person team probably has 15-25 SaaS subscriptions. Many are vestigial. AI lets you collapse some (e.g., a smart workspace might replace Notion + Loom + Slack-search + ChatGPT-Team). Saves 20-30% of SaaS spend.

**Effort:** 1 week of audit, then ongoing.

---

## Lever 4 — Defensive moats (because someone will copy this)

The SourceClub model is replicable. What makes it defensible long-term?

### 4.1 Data Network Effect
**Concept:** Every SA run, every member's spend pattern, every successful catalog match becomes training data for matching, pricing intelligence, and benchmarking. The more members, the better the system gets. Make this *visible* in marketing: "Our matching engine has been trained on $200M+ of supply purchases" (eventually).

**Tech implication:** Every matching decision becomes a labeled training example for future ML. The reviewer queue feedback loop is the highest-leverage data acquisition mechanism in the company.

### 4.2 Multi-Year Supplier Contracts (lock in the leverage)
**Concept:** Today's supplier deals presumably renew annually. Push for 2-3 year exclusive pricing arrangements with key suppliers in exchange for guaranteed volume. Locks in the discount, locks out the next-aspiring-GPO.

**This is business development, not technology**, but I'd push for it as part of the AI strategy because the supplier negotiation prep (3.1) gives us the data to argue for longer terms.

### 4.3 Member-Created Content / Network
**Concept:** Encourage members to share procurement playbooks, equipment reviews, vendor experiences. Build a private member-only community. The community becomes a switching cost — leaving SC means losing access to the peer network.

**Effort:** Discourse community setup (1 week) + ongoing community management.

### 4.4 Adjacent Service Lock-In
**Concept:** As SC layers in financing (2.5), sale-prep (2.6), insurance brokerage, payroll (potential), etc. — each service deepens the integration. A member with 3 SC services is materially less likely to leave than a member with 1.

---

## Lever 5 — AI-native opportunities (the truly innovative ones)

These are the bets I'd make as Head of AI specifically.

### 5.1 Conversational SA Agent (Voice or Chat)
**Concept:** Practice owner calls a phone number or chats with an AI agent: "I want to know if you can save us money." Agent walks them through getting the export, processes it in real-time, walks through results conversationally, books a call if there's >3x ROI.

**Why this is differentiated:** Most prospects are office managers, not the dentist. They'd rather have a 5-min conversation than fill a form and wait. The AI can answer "what's a savings analysis?" in real-time.

**Tech:** OpenAI Realtime API or Vapi.ai voice agent + matching engine + Twilio. ~6-8 weeks for a polished v1.

### 5.2 AI Marketing Engine (Lookalike Member Acquisition)
**Concept:** Take your top 50 happiest highest-savings members. Use their public attributes (practice size, specialty, geography, supplier mix) to build a lookalike model. Buy ads / outbound to lookalike practices. AI personalizes the outreach.

**Why this is differentiated:** Conversion economics already strong; better targeting = even higher conversion.

**Effort:** 3-4 weeks.

### 5.3 "Procurement Co-Pilot" in app.sourceclub.com
**Concept:** Inside the member-facing app, a chat assistant that knows the member's spend history, the catalog, and current promotions. "What's my best price for nitrile gloves medium right now?" "Should I switch suppliers for anesthetics?" "What did I spend on burs last quarter?"

**Why this matters:** Increases member engagement with the app → higher perceived value → harder to cancel.

**Effort:** 3-4 weeks once internal knowledge system (3.3) is in place.

### 5.4 Supplier-Side Intelligence Product
**Concept (the wildcard):** SC has visibility into 500+ practices' aggregate spend. That data is valuable to suppliers (Schein, Patterson, Benco) for forecasting, category management, new-product testing. Could SC monetize anonymized aggregate insights *to suppliers* — without violating member trust?

This is delicate. Done wrong, it's a betrayal. Done right, it's a second revenue stream that funds even deeper discounts. I'd explore carefully with member transparency baked in.

---

## What I'd push for in the first board meeting

If I were in this role and presenting a 12-month plan to leadership, I'd open with five claims:

1. **The matching engine is the second-most-important asset in the company.** First is the supplier deals. Treat the matching engine like supplier-deal infrastructure: invest in it, defend it, productize it.

2. **Self-serve SA is the single biggest acquisition lever** because conversion is already 90%; the bottleneck is *getting prospects to upload*. Ship that in Q1.

3. **Monthly member statements are the single biggest retention lever** because cancellation is frictionless. The value prop must be visible monthly. Ship that in Q1.

4. **AI doesn't replace the team. It makes us look like 25 people instead of 7.** Every AI project below is framed in FTE-equivalents and dollars, not "AI capability." That's how AI gets funded at small companies.

5. **The data flywheel is the moat.** Every SA, every order, every reviewer correction becomes training data. Build the systems that capture and act on this from day one.

---

## Six-quarter roadmap (the version I'd actually pitch)

**Q1: Foundation + first acquisition lever**
- Automated SA pipeline (existing POC → production)
- Stripe ↔ HubSpot sync + canonical mapping
- Self-Serve Savings Analysis landing page **← acquisition unlock**
- Monthly Member Statement automation **← retention unlock**

**Q2: Data spine + member experience**
- ZenOne / app.sourceclub.com data integration
- Customer health score + auto-intervention
- Cross-sell recommender
- Catalog Compliance Monitor

**Q3: Supplier-side leverage**
- AI-powered supplier negotiation prep
- Supplier API integrations (real-time data)
- Multi-year supplier contract push (business, not tech)
- Member referral program

**Q4: Adjacent services**
- Equipment financing partnership
- Practice sale-prep service
- Conference/trade-show lead capture engine

**Q5: AI-native differentiation**
- Conversational SA agent (voice + chat)
- Procurement co-pilot inside member app
- AI marketing engine (lookalike acquisition)

**Q6: Defensive moats**
- Member community / network features
- Supplier-side intelligence product (carefully)
- Brand campaigns leveraging the data moat ("trained on $X of supply purchases")

**By Q6 / 18 months in**, SourceClub should be at ~1,500 members, ~$7-9M ARR, with a defensible moat that takes a competitor 2+ years to replicate.

---

## What I'd NOT do (to be explicit)

These get pitched at every fast-growing SaaS company and they're usually wrong:

- ❌ **Build a marketplace.** SC isn't a marketplace; it's a buying group. The model works because of negotiation leverage, not matching buyers and sellers. Don't drift into marketplace dynamics.
- ❌ **Vertical-specific dental SaaS** (practice management, charting, scheduling). Crowded market, distracts from core, capital-intensive.
- ❌ **Buy a competitor.** Too small to absorb integration debt. Build organically.
- ❌ **International expansion before US dominance.** Different supplier landscapes, different regulations, different sales motion. Defer to Year 3.
- ❌ **Hire a sales team of 10.** With 90% conversion on SAs, what you need is more SAs, not more closers. Add 1-2 more reps to handle SA-call volume, then automate the rest.
- ❌ **Raise a $20M Series A.** Burn the bridge of profitability. SC at $2.5M ARR with a 7-person team is presumably profitable or close. Stay capital-efficient until the data moat is undeniable.

---

---

## The 10x bet — $2.5M → $25M ARR in 12 months

**Premise.** Going from $2.5M to $25M in 12 months is hypergrowth. Most SaaS tops out at 3-5x/year. 10x requires *all three* of: dramatically more leads, dramatically higher ACV per member, and at least one distribution channel we don't have today. Anything less, and the math doesn't compute.

**Market grounding** (sourced):
- US dental services: **$174.2B market**; ~202K practicing dentists; ~82K **independent** practices (our TAM).
- Average dental practice revenue: **$700K-$1M**, supply spend **6-8% of revenue = $42-80K/yr**.
- SourceClub claim: drops supply to 3-4% = **$14-32K saved per practice**, dwarfing the membership fee.
- **At 5% capture of independent TAM (~4,100 members), we'd already be at ~$20M ARR.** The market is there.

### The 12-month math

| Component | New members | Avg ACV | ARR contribution |
|---|---|---|---|
| Today's baseline | 500 | $5K | $2.5M |
| Self-serve SA + paid ads (Bet 1) | +840 | $5K | +$4.2M |
| Enterprise multi-location tier (Bet 2) | +200 (groups of 3-50) | $20K | +$4M |
| State dental association partnerships (Bet 3) | +800 | $5K | +$4M |
| Embedded SA in PMS software (Bet 4) | +400 | $5K | +$2M |
| Member referral bounties (Bet 7) | +450 | $5K | +$2.25M |
| Adjacent services ACV expansion (Bet 6) | (existing base) | +$2.5K/member | +$6M |
| **Year-end** | **3,190 members** | **~$7.7K** | **~$25M** ✅ |

This is aggressive but mathematically coherent. Below are the seven bets that, executed simultaneously, get us there. **Each one is engineering-led** — that's why this is the Head of AI / CTO roadmap, not a sales roadmap.

### Bet 1 — Self-Serve SA Landing Page + Paid Acquisition Engine ($500K-$1M ad spend)
- **What:** A standalone landing page where any prospect uploads a supplier file → instant SA → email-gated results → if 3x ROI, AI-drafted email + Calendly booking. Behind it, a $50K/qtr paid-media engine targeting "dental supply cost reduction" keywords on Google, LinkedIn, and dental industry trade publications.
- **Why this is #1:** 90% close on SAs today. The bottleneck is *getting prospects to upload.* Self-serve removes the human-availability gate; paid ads multiplies inbound 10x.
- **Engineering:** Existing matching engine + new landing page + email automation + Stripe Checkout for self-serve trial. **~4-6 weeks.**
- **Year-1 outcome:** 200+ inbound SAs/month → 60-80 closes/month → 840 new members.

### Bet 2 — Enterprise Multi-Location Tier ($20K avg ACV)
- **What:** A new pricing tier for groups with 3-50 locations: central procurement dashboard, role-based access, consolidated billing, dedicated success engineer, custom catalog negotiations. Pricing $1,500-$5,000/mo per group.
- **Why now:** Current $299/mo per location doesn't scale economically for 10-50 location groups, and they're the highest-leverage members (one sale = many locations). Multi-location groups also typically aren't ready for DSO acquisition yet — they're the SourceClub-perfect persona.
- **Engineering:** Multi-location dashboard, role-based access, consolidated billing logic, custom contract terms. **~6-8 weeks.**
- **Year-1 outcome:** 100-200 enterprise groups at $20K avg ACV = $2-4M ARR from this tier alone.

### Bet 3 — State Dental Association Partnerships (distribution unlock)
- **What:** Partner with 5-7 strategic state dental associations (CA, TX, FL, NY, IL — biggest by membership). Association co-markets to its members; SC offers exclusive member discount; revenue share with the association.
- **Why this 10x's distribution:** State associations have 2,000-8,000 dentist members each who *already trust them*. Trust transfer is the single highest-conversion channel after referrals. Cold outbound converts 1-3%; association-endorsed converts 15-30%.
- **Engineering:** Co-branded landing pages per partnership, partnership-attribution analytics, automated revenue-share reporting. **~3-4 weeks** + business development (3-6 months for first partnership to close).
- **Year-1 outcome:** 5 partnerships × ~25,000 reachable members × 3% conversion = 3,750 prospects → ~600-800 closes.

### Bet 4 — Embedded SA in Practice Management Software (product-led discovery)
- **What:** Integrations with Dentrix Ascend, Open Dental, Eaglesoft (top 3 PMS by market share). SC appears as a button/widget inside the software dentists use 6+ hours/day. "Show me my SourceClub savings" runs an in-context SA on their existing order history.
- **Why this is a moat:** PMS partnerships are sticky and hard to replicate. Even if competitors build a similar product, getting into the same PMS app stores takes years. First-mover advantage matters.
- **Engineering:** API integrations with each PMS (REST/OAuth), embedded UI components, joint-customer data agreements. **~6-10 weeks per integration; can run in parallel.**
- **Year-1 outcome:** 50,000+ discovery moments per integration × 1-2% conversion = 500-1,000 members per integration.

### Bet 5 — AI Sales Agent (Voice + Chat) — fully autonomous SA funnel
- **What:** Practice owner calls a phone number or chats. Voice/chat AI agent walks them through the SA process, processes their file in real-time, walks through results conversationally, books a call if 3x ROI, politely declines if not.
- **Why this is the bottleneck-shattering bet:** With Bets 1-4 generating 10x lead volume, the human sales team becomes the bottleneck again. The AI agent runs 24/7, never gets tired, scales infinitely. Critical for Year 2 trajectory; should ship by month 6.
- **Engineering:** Voice agent (OpenAI Realtime API or Vapi.ai) + matching engine + Twilio + conversational follow-up logic. **~8-10 weeks for a polished v1.**
- **Year-1 outcome:** Handles 70-80% of SA throughput; lets human reps focus on enterprise (Bet 2).

### Bet 6 — Adjacent-Services Marketplace (ACV expansion)
- **What:** Beyond supplies — equipment financing (1-2% spread), insurance brokerage (E&O, cyber, malpractice — 10-15% commission), lab services aggregation (5-10% margin on volume), compliance/HR-as-a-service ($100-300/mo per practice). Each is a separate revenue line layered on the existing member base.
- **Why this hits ACV math:** Existing members are warm — getting an existing happy customer to add a $200/mo service is 10x easier than acquiring a new member. Even $2.5K/year/member ACV expansion × 3,000 members = $7.5M ARR from existing base.
- **Engineering:** Marketplace UI in app.sourceclub.com, partner-vendor integrations (financing APIs, insurance brokerage APIs), unified billing. **~8-12 weeks** for the platform; each service launches independently.
- **Year-1 outcome:** $6-8M ACV expansion from existing + new member base.

### Bet 7 — Member Referral Bounties (compounding growth)
- **What:** $2,000 bounty per referred member who joins (paid as membership credit OR cash, member's choice). At 90% close on referred SAs, the math: $2K acquisition cost on $5K ARR = 40% CAC. Highly efficient.
- **Why now:** Every existing happy member knows 5-15 other dental practice owners (study groups, dental schools, state associations). A formal bounty makes referrals 5x more likely than passive word-of-mouth.
- **Engineering:** Referral attribution, automated bounty payouts via Stripe, AI-drafted intro emails members can send. **~2-3 weeks.**
- **Year-1 outcome:** 30% of existing 500 members refer 1 colleague = 150 referrals × 90% close = 135 + compounds as base grows = ~450 total referral-driven members.

### What this costs / requires

- **Marketing budget:** $500K-$1M (paid ads for Bet 1 + content marketing + conferences)
- **Hires:** +1 enterprise account exec, +1 partnerships lead, +1 senior AI engineer, +1 customer success manager = 4 new headcount. Brings team to ~11-12.
- **Capital:** Could be done from cash flow if profitable today; ~$2-3M Series A unlocks faster execution.
- **Timeline:** Bets 1, 7 ship Q1. Bet 2, 3 start Q1, close throughout year. Bet 4, 5, 6 ship Q2-Q3.

### The risks I'd flag to the CEO honestly

- **Conversion will drop as we scale to colder leads.** Bet 1 brings in tire-kickers. Net conversion likely 30-50% on inbound vs 90% on hand-curated discovery calls today. Math still works if blended stays above 25%.
- **Enterprise sales cycles are 6-12 months.** Bet 2 won't materialize until H2.
- **PMS integrations take longer than projected.** Always do. Plan for 12 weeks each, not 6.
- **AI Sales Agent (Bet 5) is the highest technical-risk item.** Voice agents are still finicky. Build a chat-only fallback first.
- **State association partnerships require trust building.** First one takes 6+ months; subsequent ones get easier as we have proof points.

### What I'd tell the board

> "The dental supply market is $174B. We're at $2.5M ARR. Even capturing 0.1% of independent practices puts us at $20M+. The blocker isn't market size; it's the speed at which we can build the acquisition machine. These seven bets, run in parallel, can get us to $25M by month 12 with $3M of investment. They can also get us to $10M with $1M and a slower hiring plan. Choose your risk tolerance; the upside math is the same."

That's the 10x conversation. Doable, hard, defensible.

---

## Closing

The case study assignments are tactical. The job is strategic. This document is what I'd put in the next 1:1 with the CEO 30 days in. I built it for two reasons:

1. To show I'd think this way *unprompted*, not just answer what's asked.
2. To put concrete bets on the table that we can argue about — because half of these will be wrong, and the conversation about which half is the actual job.

— Abhi
