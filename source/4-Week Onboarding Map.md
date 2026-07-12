# 4-Week Onboarding Map — MUE (Multifaceted User Education)

> **A sleek, category-driven learning process** — 8 subject-material categories across 4 weeks.
> Every day is tagged by category, each week has a clear theme, and all learning compounds toward the Codex Gate.

```
Week 1                  Week 2                  Week 3                  Week 4
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   🏗️ Foundation  │  │   🔗 Data Layer  │  │   ⚡ Operations  │  │   📦 Contribution│
│   Establish the   │→│   Validate the    │→│   Automate & QC  │→│   Deliver & Hand  │
│   learning frame  │  │   data foundation│  │   the model      │  │   off to review   │
└──────────────────┘  └──────────────────┘  └──────────────────┘  └──────────────────┘
```

**Category Legend — every daily task is tagged:**

| Tag | Category | Focus |
|-----|----------|-------|
| 🤖 AI | AI & Copilot | Chat modes, prompts, instructions, context |
| ⚡ Codex | Codex Productivity | Workflow orientation, handoff fluency, AI acceleration |
| 🏗️ Pyr | Pyramid Platform | Model logic, deployment, QC, security, artifacts |
| 📊 BI | BI Judgment | Business reasoning, metrics, grain, validation |
| 🔗 Data | Data & Lineage | Source-to-model lineage, rollups, snapshots, dependencies |
| 📦 Del | Delivery & Handoff | Change isolation, review packages, assets, handoff |
| 🧠 Ret | Retention & Readiness | Scorecards, proof tasks, gates, readiness checks |
| 💬 Team | Team Communication & Task Management | Standups, status updates, task tracking, feedback, blockers |

---

## Purpose

> **Overarching Goal:** Become a confident, operationally reliable **Business Intelligence (BI) team contributor** who can analyze data, validate logic, deploy models, communicate and collaborate with the team, and hand off work cleanly — using Pyramid, Codex, BI judgment, and team collaboration skills.

This map condenses the 60-day `Pyramid, Codex, and BI Judgment Daily Execution Guide` into a **maximum 28-working-day program** while preserving all six proof tasks, the eight learning categories, and the evidence-backed readiness gates. It is the single source of truth for scheduling. Every week builds directly toward the BI team contributor outcome.

> **Rule:** This program must not exceed 28 working days (Monday–Friday only; weekends are excluded). If you need more time, open an issue with rationale and get explicit team sign-off per `CONTRIBUTING.md`.

> **Weekend exclusion:** Day count increments only on weekdays. A day-number of N always corresponds to the N‑th working day since the cycle started. See `source/scripts/create_daily_note.py` — it refuses to create notes on Saturday or Sunday.

### Note on Cognitive Load Across Proficiency Levels

The MUE curriculum offers **4 proficiency levels** (🌱 Foundation → 🌿 Development → 🌳 Operational → 🏆 Mastery), each with its own independent 28-working-day cycle. The same 8 categories repeat across all levels, but the **cognitive demand escalates significantly**:

| Level | Bloom's Tier | Typical Task | Cognitive Load |
|-------|-------------|--------------|----------------|
| **🌱 L1 Foundation** | Remember & Understand | *Identify, describe, follow guided steps* | Low — vocabulary building with maximum scaffolding |
| **🌿 L2 Development** | Apply | *Practice, implement, execute under guidance* | Moderate — structured tasks with clear success criteria |
| **🌳 L3 Operational** | Analyze & Evaluate | *Compare, detect, assess, validate independently* | High — requires quality judgment and self-correction |
| **🏆 L4 Mastery** | Create & Evaluate | *Design, automate, optimize, mentor others* | Very high — system-level thinking, strategy, teaching |

This means **28 working days at L4 is not the same workload as 28 working days at L1**. Learners at higher levels are expected to:
- Work with greater independence (less step-by-step guidance)
- Produce higher-quality artifacts (validation evidence, reusable assets)
- Demonstrate judgment, not just compliance

**Recommendation for reviewers:** When assessing at L3 or L4, evaluate the *quality and autonomy* of the work, not just completion. A Level 4 learner who still needs daily step-by-step guidance may need to consolidate at L3 before advancing.

---

## How the 60-Day Guide Maps to 28 Working Days

The original 60-day guide has three phases, now mapped to four themed weeks with explicit category coverage:

| Phase | Original Days | Week | Theme | Primary Categories |
|---|---|---|---|---|
| Foundation | Days 1–5 | **Week 1** | 🏗️ Foundation | 🤖 AI · 📊 BI · 🏗️ Pyr |
| Operational | Days 6–30 | **Weeks 2–3** | 🔗 Data → ⚡ Operations | 🔗 Data · 📊 BI · ⚡ Codex · 🏗️ Pyr |
| Contribution | Days 31–60 | **Week 4** | 📦 Contribution | 📦 Del · ⚡ Codex · 🧠 Ret |

---

## Learning Journey — Category Coverage Heatmap

```
Category                    Wk1      Wk2      Wk3      Wk4
───────────────────────  ───────  ───────  ───────  ───────
🤖 AI & Copilot           ██████   ████     ████     ████
⚡ Codex Productivity     ██████   ████     ██████   ██████
🏗️ Pyramid Platform      ████     ██████   ██████   ██████
📊 BI Judgment            ████     ██████   ██████   ██████
🔗 Data & Lineage         ████     ██████   ██       
📦 Delivery & Handoff     ██                ████     ██████
🧠 Retention & Readiness  ██       ██       ██       ██████
💬 Team Comm & Task Mgmt  ████     ██       ██       ██████
```

---

## 📖 Academic Layer Reference

This curriculum now includes a **BI Academic Framework** that adds BI theory, formal assessment design, and industry standards alignment to each proficiency level. See `source/BI Academic Framework.md` for the full reference.

**Quick map by level:**
| Level | Academic Focus | Key Concepts |
|-------|---------------|--------------|
| 🌱 L1 Foundation | Theoretical vocabulary + team norms | DIKW pyramid, descriptive vs. diagnostic analytics, what is a data model, why visualisation matters, team communication channels, standup format |
| 🌿 L2 Development | Guided application of theory + task tracking | Analytics maturity (4 types), ETL/ELT, dimensional modelling basics, grain as a threshold concept, breaking down work, GitHub Issues |
| 🌳 L3 Operational | Independent analysis with rigour + feedback | Kimball lifecycle, data governance, star schemas, validation chain methodology, row ownership, giving/receiving feedback, blocker escalation |
| 🏆 L4 Mastery | Strategic integration & transfer + team leadership | BI maturity models, industry standards (DMBOK/TDWI/SFIA), far-transfer assessment, portfolio capstone, mentoring, task prioritisation across team |

---

## Week 1 — 🏗️ Foundation (Days 1–5)

**Theme:** Establish the learning frame — AI habits, BI reasoning, and Pyramid awareness.
**Categories:** 🤖 AI & Copilot · 📊 BI Judgment · 🏗️ Pyramid Platform · 🧠 Retention
**🎓 Academic concepts this week:** DIKW pyramid (name the four layers), descriptive vs. diagnostic analytics, what is a data model, why visualisation matters

| Day | Exec Day | Tags | Today's Focus | Evidence Artifact | Retention Check |
|-----|----------|------|---------------|-------------------|-----------------|
| 1 | 1 | 🤖 AI 💬 Team | **AI Modes & Prompts + Team Norms:** Learn Ask/Edit/Agent/Plan modes, prompt structure, context limits. Learn team communication channels, standup format, and how to ask for help effectively | Readiness note explaining modes, prompt structure, context-window limits, team channels, standup structure | — |
| 2 | 2 | 🤖 AI ⚡ Codex | **Prompt Crafting + Codex Loop Intro:** Build 3 reusable prompts (repo analysis, model validation, deployment/QC). **Codex Exercise 1: Handoff Reading** — extract 5 facts from any handoff in <60s | Three working prompts + revision log (first failure + fix) + Handoff Reading exercise result | Re-read Day 1; explain one mode change from memory |
| 3 | 3 | 📊 BI 📦 Del 💬 Team | **Change Isolation + First Standup:** Narrow-scope review behavior, isolate a reviewable change slice. Give your first 30-second standup update on your change slice | Clean review draft: purpose, audience, focus, reviewer questions + standup note | Explain prompt structure without looking |
| 4 | 4 | 🏗️ Pyr 🔗 Data | **Model Lineage:** Trace source → transformation → snapshot → rollup → QC | One-page dependency map naming each layer | Trace lineage from memory; identify risk layer |
| 5 | 5 | 🏗️ Pyr 📦 Del 🧠 Ret 💬 Team | **Operations Checklist + Task Tracking:** Build deployment, migration, security, access, rerun checklist. Set up task tracking for your work items (GitHub Issues or project board) | v1 deployment + handoff checklist + task board snapshot + **Week 1 Scorecard** | Name 3 data quality risks without notes |

**Week 1 Scorecard Areas:** Prompt discipline, repo/workspace analysis, change isolation, validation order, deployment awareness, reviewer handoff, reusability, Codex handoff fluency, Codex bounded use

> **Gate:** If 2+ areas score **Fail**, repeat Week 1 before moving to Week 2.

---

## Week 2 — 🔗 Data Foundation & Model Layer (Days 6–12)

**Theme:** Validate source-to-model data foundation. Complete Proof Tasks 1 and 3.
**Categories:** 🔗 Data & Lineage · 📊 BI Judgment · ⚡ Codex Productivity · 🏗️ Pyramid Platform
**🎓 Academic concepts this week:** Analytics maturity (descriptive→diagnostic→predictive→prescriptive), ETL/ELT pipeline, dimensional modelling basics (facts vs. dimensions), grain as a threshold concept

| Day | Exec Day | Tags | Today's Focus | Evidence Artifact | Retention Check |
|-----|----------|------|---------------|-------------------|-----------------|
| 6 | 6 | 📊 BI 🔗 Data 💬 Team | **Source-to-Output Inventory + Status Update:** Map source inputs, target outputs, reporting grain. Communicate your findings as a brief status update to a peer | Source-to-output inventory + status update note | Name all 4 Copilot modes + when to use each |
| 7 | 7 | 🔗 Data 📊 BI | **Row Ownership & Deduplication:** Identify who owns row selection, dedup logic, history | Row ownership + deduplication note | Recall which layer owns row sets |
| 8 | 8 | 🔗 Data 📊 BI | **Aggregation Boundaries:** Identify double-counting risks, grain boundaries | Aggregation boundary note | Explain 3 prompts from Week 1 |
| 9 | 9 | ⚡ Codex 🧠 Ret 💬 Team | **📌 PT1: Repository Analysis Brief:** Business purpose, dependency order, key I/O, risks, safe change point. **Codex Exercise 2: Context Pull** — use Pattern 1 to pull context, evaluate scope, refine. Share a one-paragraph finding with your team | Completed PT1 brief + Context Pull exercise with before/after prompt comparison + team update note | Re-state dependency order from Day 4 map |
| 10 | 10–11 | 🏗️ Pyr 🔗 Data | **Hierarchy & Structure:** Close data-foundation layer, validate hierarchy | Week 2 scorecard + hierarchy validation note | Explain grain, hierarchy levels, goal evaluation point |
| 11 | 12 | 🏗️ Pyr 📊 BI | **Measure & Service Logic:** Validate active/inactive rows, cancellations | Active-row logic note | State what each model layer owns in one sentence |
| 12 | 13–14 | ⚡ Codex 🔗 Data 🧠 Ret | **Time Logic & Parameters:** Validate time/target logic, list/parameter/level behavior. **Codex Exercise 3: State Summary** — draft 3-sentence state summary using Pattern 2, test on peer | Time logic note + list/parameter note + State Summary exercise result + **Week 2 Scorecard** | Name top 3 data risks from memory |

**Proof Tasks Due This Week:**
- ✅ **PT1: Repository Analysis Brief** (Day 9) — ⚡ Codex category
- ✅ **PT3: Metric Lineage Walkthrough** (Day 12) — 📊 BI / 🔗 Data categories

> **Gate:** If Proof Tasks 1 or 3 are incomplete, do not advance to Week 3.

---

## Week 3 — ⚡ Snapshots, Rollups, QC & Deployment (Days 13–19)

**Theme:** Validate snapshot/rollup logic, run QC, rehearse deployment. Complete Proof Tasks 3–5.
**Categories:** 🏗️ Pyramid Platform · ⚡ Codex Productivity · 📊 BI Judgment · 📦 Delivery & Handoff
**🎓 Academic concepts this week:** Kimball lifecycle, data governance & quality dimensions (DMBOK), star schemas, validation chain methodology, row ownership threshold concept

| Day | Exec Day | Tags | Today's Focus | Evidence Artifact | Retention Check |
|-----|----------|------|---------------|-------------------|-----------------|
| 13 | 15–16 | 📊 BI 🔗 Data | **📌 PT3: Metric Lineage Walkthrough:** Counting grain, active-row rules, period definitions, calc point, rollup path + snapshot validation | PT3 walkthrough + snapshot validation note | Explain why upstream defect contaminates downstream rollups |
| 14 | 17 | 📊 BI 🔗 Data | **Rollup Behavior:** Validate lowest grain → summaries, weighted/summed/derived totals | Rollup behavior note | Explain where double-counting could happen |
| 15 | 18 | ⚡ Codex 📦 Del 💬 Team | **📌 Start PT4: QC Plan + Codex Validation Practice:** What to check, expected outcomes, anomaly classification. Use Pattern 4 (Validation Check) to classify gaps. Escalate any anomalies to a peer for discussion | QC evidence template (first pass) + Validation Check prompt result + anomaly escalation note | Recall 3 prompts from Week 1; test one on current work |
| 16 | 19 | ⚡ Codex 🧠 Ret | **📌 Complete PT4: QC Evidence Pack + Handoff Draft:** Run checks, separate defects from limitations. Use Pattern 3 (Handoff Draft) to record findings | Completed PT4 QC evidence pack + Handoff Draft exercise result | Name 3 data quality risks without notes |
| 17 | 21–22 | 🏗️ Pyr 📦 Del 💬 Team | **Deployment Preflight + Task Breakdown:** Map deployment sequence + access/reviewer boundaries. Break deployment into assignable tasks and share with team | Preflight checklist + access note + task breakdown | State deployment sequence from memory |
| 18 | 23–24 | 🏗️ Pyr 🧠 Ret | **📌 PT5: Deployment Rehearsal:** Draft sequence → dry run → record | Completed PT5 deployment rehearsal record | Explain whether error is source/transform/snapshot/rollup/presentation |
| 19 | 25 | 🏗️ Pyr 📦 Del 🧠 Ret 💬 Team | **Close Operations Layer + Team Sync:** Finalize deployment, QC, and handoff readiness. Give a summary update of what was completed to your team | **Week 3 Scorecard** + deployment closeout + team sync note | Name all 6 proof tasks from memory |

**Proof Tasks Due This Week:**
- ✅ **PT3: Metric Lineage Walkthrough** (Day 13) — 📊 BI / 🔗 Data
- ✅ **PT4: QC Evidence Pack** (Day 16) — ⚡ Codex
- ✅ **PT5: Deployment Rehearsal** (Day 18) — 🏗️ Pyr

> **Gate:** If 2+ scorecard areas score **Fail**, repeat this layer in Week 4 instead of expanding scope.

---

## Week 4 — 📦 Contribution & Handoff (Days 20–28)

**Theme:** Deliver a reviewable change slice, create a reusable asset, and pass the Codex Gate — communicating effectively with your team throughout.
**Categories:** 📦 Delivery & Handoff · ⚡ Codex Productivity · 🏗️ Pyramid Platform · 📊 BI Judgment · 🧠 Retention & Readiness · 💬 Team Communication & Task Management
**🎓 Academic concepts this week:** BI maturity models (TDWI/Gartner), industry standards alignment (DMBOK/TDWI/SFIA), far-transfer assessment, portfolio capstone, bounded Codex as metacognition, task prioritisation across team, giving/receiving feedback

| Day | Exec Day | Tags | Today's Focus | Evidence Artifact | Retention Check |
|-----|----------|------|---------------|-------------------|-----------------|
| 20 | 26–27 | 🏗️ Pyr 📦 Del 💬 Team | **Content Movement & Handoff Path + Task Board:** Validate artifact movement, build reviewer path. Update your task board with current status and next steps | Content-movement checklist + handoff draft + task board update | Trace one KPI end-to-end from memory |
| 21 | 28–29 | ⚡ Codex 📦 Del 🧠 Ret | **📌 PT2: Review Dry Run + PT6: Handoff Test + Codex Exercise 4:** Complete both proof tasks. Use Pattern 6 (Change Impact) to scope review package, then Pattern 3 to draft handoff | PT2 review package + PT6 handoff test + Change Impact prompt result | Pass Codex Gate check (all 6 gates) |
| 22 | 31–33 | 📊 BI 📦 Del 💬 Team | **Change Slice + Feedback Practice:** Select narrow change, establish baseline, identify owning surface. Share your change slice with a peer and practise receiving feedback | Change-slice charter + baseline note + owning-surface note + feedback reception note | State where business logic lives for this change |
| 23 | 34–36 | 🏗️ Pyr ⚡ Codex | **Fix Path & Validate + Bounded Codex Practice:** Draft smallest fix, run validation cycle, repair. **Codex Exercise 6: Bounded Codex Simulation** — write bounded prompt with 2+ "Do NOT" constraints, test, refine | Fix-path draft + validation record + iteration note + Bounded Codex exercise result | Reproduce deployment sequence from memory |
| 24 | 37–40 | ⚡ Codex 📦 Del 🧠 Ret 💬 Team | **Review Package + Handoff Mastery + Status Update:** Record before/after, prepare review package, stress-test, close slice. Use Pattern 3 to draft handoff, grade against Quality Rubric. Give a final status update to your team | Before/after note + review package + closed contribution + handoff graded against rubric + **Week 4 Scorecard** + status update note | All 6 PTs complete? If not, list missing |
| 25 | 41–44 | 📊 BI 📦 Del 💬 Team | **Handoff Rehearsal + Peer Review:** Practice surface recommendation, validate parameters, build reviewer explanation. Walk through your handoff with a peer and incorporate their input | Surface recommendation + reviewer summary + final handoff rehearsal + peer feedback log | Explain whether issue is source/transform/snapshot/rollup/presentation |
| 26 | 46–50 | ⚡ Codex 📦 Del 💬 Team | **📌 Reusable Asset (v1) — Codex Prompt Library:** Charter → draft → test → revise. Create a reusable Codex prompt template (Pattern 1–7) as your asset. Share draft with a teammate for early feedback | Asset charter + draft v1 + test note + v2 + prompt pattern as asset + early feedback note | Asset addresses real team problem |
| 27 | 51–55 | 🏗️ Pyr 📦 Del 💬 Team | **📌 Reusable Asset (v2) + Team Handoff:** Add platform specificity, example use case, external review, publish. Hand off the completed asset to a teammate with a brief walkthrough | Surface-aware revision + example + gap list + v3 + final asset + team handoff record | Asset is consumable by another developer without translation |
| 28 | 56–60 | 🧠 Ret 🤖 AI ⚡ Codex 💬 Team | **📌 Codex Gate & Closeout + Final Team Communication:** Bounded Codex test, **Exercise 5: Manual-vs-Codex Comparison**, final readiness summary, gate decision. Run full Comparison Template for one defined task. Share your readiness conclusion with your team and discuss next steps | Codex comparison note + final readiness statement + **Final Readiness Package** + all 5 Codex exercises completed + team closeout note | **Final Codex Gate + closeout** |

**Proof Tasks Due This Week:**
- ✅ **PT2: Review Workflow Dry Run** (Day 21) — ⚡ Codex / 📦 Del
- ✅ **PT6: Reviewer Handoff Test** (Day 21) — 📦 Del / 🧠 Ret
- ✅ **One reusable team asset** (Days 26–27) — 📦 Del / ⚡ Codex

---

## Evidence-Backed Results & Reporting

### Daily Evidence Standard

Every day **must** produce at least one evidence artifact saved to `notes/` or `evidence/`:

| Artifact Type | Category Tag | Examples |
|---|---|---|
| Note | 🤖 · 📊 · 🔗 | Readiness note, dependency map, logic note, boundary note |
| Prompt | 🤖 · ⚡ | Reusable prompt template + revision log |
| Checklist | 🏗️ · 📦 | Deployment checklist, preflight checklist, QC checklist |
| Validation Record | 📊 · 🔗 | Expected vs. actual outcome, anomaly classification |
| Review Draft | 📦 · 📊 | Scope note, review request, reviewer questions |
| Handoff | 📦 · ⚡ | Handoff draft, handoff package, reviewer-facing summary |
| Proof Task | 🧠 | Completed PT1–PT6 with all required sections |
| Reusable Asset | 📦 · ⚡ | Prompt library, QC template, deployment checklist, troubleshooting guide |

### Weekly Reporting Standard

At the end of each week, produce:
1. **Weekly Scorecard** (`Pass` / `Moderate` / `Fail` for all 7 areas)
2. **Proof Task Progress** — which tasks are complete, which remain
3. **Readiness Classification** — Foundational / Developing / Operational / Ready For Codex Acceleration
4. **Category Coverage Summary** — which categories advanced most this week
5. **Retention Summary** — what was retained from prior weeks
6. **Next Week Focus** — which category needs the most attention

### Automated Reporting

Use the included scripts:
```bash
# Create a daily note (enforces day ≤ 28)
python3 scripts/create_daily_note.py --date YYYY-MM-DD --day-number N

# Aggregate weekly notes into a report
python3 scripts/aggregate_weekly.py --year YYYY --week WW
```

The GitHub Actions workflow (`.github/workflows/weekly-aggregator.yml`) runs automatically every Sunday.

---

## Retention Learning System

Retention is built into the 4-week map via three mechanisms:

### 1. Daily Retention Checks (built into each day above)
Each day includes a specific recall question from prior material. Answer it in your daily note before starting new work.

### 2. Weekly Cross-Category Review
At the end of each week, answer these questions in your scorecard:
- What concept from **Week 1** am I still using daily?
- What concept from **Week 2** am I still using daily?
- What concept from **Week 3** am I still using daily?
- Which category (AI / Codex / Pyramid / BI / Data / Delivery / Readiness) advanced most this week?
- Which category needs the most attention next week?

### 3. Cumulative Proof Task Checklist
Track completion across all 6 proof tasks. Each PT maps to specific categories:

| Proof Task | Week | Categories | Status | Notes |
|---|---|---|---|---|
| PT1: Repository Analysis Brief | 2 | ⚡ Codex · 🧠 Ret | ⬜ | |
| PT2: Review Workflow Dry Run | 4 | ⚡ Codex · 📦 Del | ⬜ | |
| PT3: Metric Lineage Walkthrough | 2–3 | 📊 BI · 🔗 Data | ⬜ | |
| PT4: QC Evidence Pack | 3 | ⚡ Codex · 🧠 Ret | ⬜ | |
| PT5: Deployment Rehearsal | 3 | 🏗️ Pyr · 🧠 Ret | ⬜ | |
| PT6: Reviewer Handoff Test | 4 | 📦 Del · 🧠 Ret | ⬜ | |

---

## Standard Equipped Team Contributor — Definition by Category

A learner who completes this 4-week program is considered a **Standard Equipped Team Contributor** when ALL of the following criteria are met across all seven categories:

### 🤖 AI & Copilot Readiness
- [ ] Can use Ask, Edit, Agent, and Plan modes appropriately for the task
- [ ] Has 3+ stable, tested prompt templates for analysis, validation, and review
- [ ] Can write and maintain custom instructions and prompt files
- [ ] Understands context-window limits and can prevent prompt drift

### ⚡ Codex Productivity Readiness
- [ ] Can use Codex to pull context, summarize state, identify next steps, and record a handoff
- [ ] Can constrain Codex to proven workflows (does not let AI define business logic)
- [ ] Has completed a manual-vs-Codex comparison and can articulate where AI helps vs. drifts

### 🏗️ Pyramid Platform Readiness
- [ ] Can explain dependency order from source loads to reporting outputs without notes
- [ ] Can identify owning layer (source/transformation/snapshot/rollup/presentation) for any metric or defect
- [ ] Can move Pyramid artifacts through environments with correct connections, access, and reviewer path
- [ ] Can produce QC evidence with a clear review entrypoint

### 📊 BI Judgment Readiness
- [ ] Can articulate the business question before selecting a technical approach
- [ ] Can define metric grain, filters, exclusions, and ownership rules
- [ ] Can choose appropriate output type (dashboard, report, alert, export, handoff, summary)
- [ ] Can produce validation evidence a reviewer needs to trust the result
- [ ] Can distinguish data-quality issue vs. logic error vs. presentation limitation

### 🔗 Data & Lineage Readiness
- [ ] Can trace a KPI from source conditions to final rollup without notes
- [ ] Can identify where double-counting risks exist in a model
- [ ] Can explain why an upstream defect contaminates all downstream rollups

### 📦 Delivery & Handoff Readiness
- [ ] Can prepare a reviewer handoff package consumable without clarification
- [ ] Can scope a change slice, document before/after, and prepare a review package
- [ ] Has created at least one reusable team asset (prompt library, checklist, template, runbook)

### 🧠 Retention & Readiness
- [ ] All 6 proof tasks complete and documented in `evidence/`
- [ ] Weekly scorecards show ≤1 area at **Fail** in final week
- [ ] Codex Gate decision: **Begin bounded Codex use** (or missing gates explicitly documented)
- [ ] Daily notes demonstrate increasing independence (less template reliance, more own analysis)

---

## Codex Gate (Final Checkpoint)

Run this on Day 28. All must be **Yes** to begin bounded Codex use.

| # | Gate | Codex Skill Tested | How to Verify | Status |
|---|------|-------------------|---------------|--------|
| 1 | One end-to-end workflow completed manually or with standard Copilot support | Codex Loop (all 5 steps) | Review handoff evidence for one full workflow cycle | Yes / No |
| 2 | Business-logic ownership understood (you know where logic lives and where it does not) | Bounded Codex — knowing when NOT to use Codex | Ask: "Where does the business logic live for your last change?" Must name the owning layer without guessing | Yes / No |
| 3 | Validation evidence produced without help | Validation Check (Pattern 4) | Review evidence file — must show expected vs. actual comparison, not just Codex output | Yes / No |
| 4 | All 6 proof tasks completed | Cross-category Codex use | PT1–PT6 all present in `evidence/` with required sections | Yes / No |
| 5 | One clean reviewable change slice delivered | Change Impact (Pattern 6) | Change charter includes: before state, after state, owning surface, review path | Yes / No |
| 6 | One reusable team asset created | Prompt pattern creation | Asset is a Codex prompt template, checklist, or workflow doc tested on a real task | Yes / No |
| 7 | **Manual-vs-Codex comparison completed** | Comparison methodology (Exercise 5) | Comparison Template fully filled, decision paragraph written, saved to `evidence/` | Yes / No |
| 8 | **All 6 Codex exercises passed** | Cumulative Codex proficiency | EX1 (Handoff Reading), EX2 (Context Pull), EX3 (State Summary), EX4 (Handoff Creation), EX5 (Manual-vs-Codex), EX6 (Bounded Simulation) all in evidence/ | Yes / No |

**Bonus Gate** (accelerated path):

| # | Gate | Codex Skill Tested | How to Verify | Status |
|---|------|-------------------|---------------|--------|
| 9 | Can explain the Bounded Codex rules without notes | Codex safety awareness | Recite "Codex CAN / MUST NOT" rules from memory; name 3 situations where Codex should NOT be used | Yes / No |

**Decision:** ⬜ Stay with standard Copilot workflows / ⬜ Begin bounded Codex use

> **Note:** The Manual-vs-Codex comparison (Gate 7) and Codex exercises (Gate 8) are required for bounded Codex use. If missing, the learner stays on standard Copilot workflows until completed.

---

## Category-Coded Quick Reference

| File | Categories | Purpose |
|---|---|---|
| `source/LEARNING_CATEGORIES.md` | 🧠 💬 | **Master category reference** — all 8 categories defined including team communication |
| `source/4-Week Onboarding Map.md` | 🧠 | **This file** — condensed daily/weekly plan with categories, evidence, and gates |
| `source/Copilot Reference for MUE.md` | 🤖 AI | Copilot modes, custom instructions, prompt files, context management |
| `source/Pyramid Platform Reference.md` | 🏗️ Pyr | **NEW — Comprehensive Pyramid reference:** model architecture, deployment sequencing, QC, security, artifact migration, reviewer path |
| `source/Codex Productivity.md` | ⚡ Codex | **NEW — Comprehensive Codex training:** Codex Loop, handoff fluency, 7 prompt patterns, bounded use, 6 practice exercises, manual-vs-Codex comparison methodology |
| `source/Custom Workflows for MUE.md` | ⚡ Codex · 📦 Del | Four operational workflows (repo analysis, review, handoff, daily learning) + 3 new Codex-specific workflows (handoff fluency, bounded use, comparison) |
| `source/Codex Productivity Training Handoff.md` | ⚡ Codex · 📊 BI | Vision document — three-track rationale and Codex productivity |
| `source/Pyramid, Codex, and BI Judgment Readiness Plan.md` | 🏗️ Pyr · 📊 BI · ⚡ Codex | Full day-by-day and week-by-week readiness plan |
| `source/Pyramid, Codex, and BI Judgment Daily Execution Guide.txt` | 🏗️ Pyr | 60-day execution plan (reference; use this map for scheduling) |
| `source/Pyramid, Codex, and BI Judgment Daily Working Template.txt` | 🧠 | Daily work blocks, checklists, scorecards (use directly) |
| `source/CONTRIBUTING.md` | 🧠 | Contribution rules, evidence layout, 28-day enforcement |
| `source/scripts/create_daily_note.py` | 🧠 | Creates daily note from template (enforces day ≤ 28) |
| `source/scripts/aggregate_weekly.py` | 🧠 | Aggregates weekly notes into action/reports/ |
| `source/scripts/generate_readiness_report.py` | 🧠 | Parses notes → structured readiness reports |
| `action/templates/retention-review.md` | 🧠 | Weekly retention review with category prompts |
| `action/templates/contributor-readiness-check.md` | 🧠 | End-of-program certification checklist by category |
| `action/dashboard/dashboard.html` | 🧠 | Third-party review dashboard with category change tracking |
| `action/dashboard/build_data.py` | 🧠 | Dashboard data builder — tracks per-category changes |
| `review/scripts/sync-from-action.py` | 📦 Del | Syncs action/ output into review/ |
| `.github/workflows/weekly-aggregator.yml` | 🧠 | Auto-generates weekly reports + syncs to review/ |
| `.github/instructions/mue-instructions.yml` | 🤖 AI | Team-wide Copilot working standards |
