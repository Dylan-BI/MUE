# 4-Week Onboarding Map — MUE (Multifaceted User Education)

## Purpose

This map condenses the 60-day `Pyramid, Codex, and BI Judgment Daily Execution Guide` into a **maximum 4-week (28-day) program** while preserving all six proof tasks, the three learning tracks, and the evidence-backed readiness gates. It is the single source of truth for scheduling.

> **Rule:** This program must not exceed 28 calendar days. If you need more time, open an issue with rationale and get explicit team sign-off per `CONTRIBUTING.md`.

---

## How the 60-Day Guide Maps to 28 Days

The original 60-day guide has three phases:
| Phase | Original Days | Condensed to Week |
|---|---|---|
| Foundation | Days 1–5 | **Week 1** (Days 1–5) |
| Operational | Days 6–30 | **Weeks 2–3** (Days 6–19) |
| Contribution | Days 31–60 | **Week 4** (Days 20–28) |

---

## Three Learning Tracks (Run in Parallel Each Week)

Every day advances one primary track. Rotate across tracks to build all three simultaneously.

| Track | Focus |
|---|---|
| **Pyramid Operations** | Platform mechanics, model logic, deployment, QC, security, reviewer handoff |
| **Codex Productivity** | Prompt discipline, context synthesis, handoff fluency, targeted AI use |
| **BI Judgment** | Tool-agnostic business reasoning, metric definition, validation evidence, trusted delivery |

---

## Week 1 — Foundation (Days 1–5)

**Goal:** Establish the three-track frame, Copilot habits, and baseline readiness.

| Day | Execution Guide Day | Track | Today's Focus | Evidence Artifact | Retention Check |
|---|---|---|---|---|---|
| 1 | Day 1 | Codex Productivity | Learn Ask/Edit/Agent/Plan modes, prompt structure, context limits | One-page readiness note explaining modes, prompt structure, and context-window limits | — |
| 2 | Day 2 | Codex Productivity | Build 3 reusable prompts (repo analysis, model validation, deployment/QC review) | Three working prompts + revision log (first failure + fix) | Re-read Day 1 note; explain one mode change from memory |
| 3 | Day 3 | BI Judgment | Narrow-scope review behavior, change isolation | Clean review draft: purpose, audience, focus, reviewer questions | Explain prompt structure without looking |
| 4 | Day 4 | Pyramid Operations | Trace model lineage (source → transformation → snapshot → rollup → QC) | One-page dependency map naming each layer | Trace lineage from memory; identify risk layer |
| 5 | Day 5 | Pyramid Operations | Build operations checklist (connections, migration, security, access, rerun) | v1 deployment + handoff checklist + **Week 1 Scorecard** | Name 3 data quality risks without notes |

**Week 1 Scorecard Areas:** Prompt discipline, repo/workspace analysis, change isolation, validation order, deployment awareness, reviewer handoff, reusability

> **Gate:** If 2+ areas score **Fail**, repeat Week 1 before moving to Week 2.

---

## Week 2 — Data Foundation & Model Layer (Days 6–12)

**Goal:** Validate source-to-model foundation. Complete Proof Tasks 1 and 3.

| Day | Execution Guide Day | Track | Today's Focus | Evidence Artifact | Retention Check |
|---|---|---|---|---|---|
| 6 | Day 6 | BI Judgment | Inventory source inputs, target outputs, reporting grain | Source-to-output inventory | From Week 1: name all 4 Copilot modes + when to use each |
| 7 | Day 7 | BI Judgment | Identify row ownership, deduplication logic, history preservation | Row ownership + deduplication note | Recall which layer owns row sets |
| 8 | Day 8 | BI Judgment | Identify aggregation boundaries, double-counting risks | Aggregation boundary note | Explain 3 prompts created in Week 1 |
| 9 | **Day 9 (PT1)** | Codex Productivity | **Proof Task 1:** Repository Analysis Brief (business purpose, dependency order, key I/O, risks, safe change point) | Completed PT1 brief | Re-state dependency order from Day 4 map |
| 10 | Days 10–11 | Pyramid Operations | Close data-foundation layer + validate hierarchy structure | Week 2 scorecard + hierarchy validation note | Explain grain, hierarchy levels, goal evaluation point |
| 11 | Day 12 | Pyramid Operations | Validate measure/service logic, active/inactive rows, cancellations | Active-row logic note | State what each model layer owns in one sentence |
| 12 | Days 13–14 | Codex Productivity | Validate time/target logic + list/parameter/level behavior | Time logic note + list/parameter note | **Week 2 Scorecard** + name top 3 data risks from memory |

**Proof Tasks Due This Week:**
- ✅ Proof Task 1 (Day 9)
- ✅ Proof Task 3 (Day 12 — Metric Lineage Walkthrough)

> **Gate:** If Proof Tasks 1 or 3 are incomplete, do not advance to Week 3.

---

## Week 3 — Snapshots, Rollups, QC & Deployment (Days 13–19)

**Goal:** Validate snapshot/rollup logic, run QC, rehearse deployment. Complete Proof Tasks 4 and 5.

| Day | Execution Guide Day | Track | Today's Focus | Evidence Artifact | Retention Check |
|---|---|---|---|---|---|
| 13 | Days 15–16 | BI Judgment | **Proof Task 3** Metric Lineage Walkthrough (counting grain, active-row rules, period definitions, calc point, rollup path) + validate snapshot behavior | PT3 walkthrough + snapshot validation note | From Week 2: explain why upstream defect contaminates all downstream rollups |
| 14 | Day 17 | BI Judgment | Validate rollup behavior (lowest grain → summaries, weighted/summed/derived totals) | Rollup behavior note | Explain where double-counting could happen |
| 15 | Day 18 | Codex Productivity | Start **Proof Task 4:** QC plan (what to check, expected outcomes, anomaly classification) | QC evidence template (first pass) | Recall 3 prompts from Week 1; test one on current work |
| 16 | **Day 19 (PT4)** | Codex Productivity | Complete **Proof Task 4:** Run checks, separate defects from limitations | Completed PT4 QC evidence pack | Name 3 data quality risks w/o notes |
| 17 | Days 21–22 | Pyramid Operations | Map deployment preflight + access/reviewer boundaries | Preflight checklist + access note | State deployment sequence from memory |
| 18 | **Days 23–24 (PT5)** | Pyramid Operations | **Proof Task 5:** Deployment rehearsal (draft sequence → dry run → record) | Completed PT5 deployment rehearsal record | Explain whether an error is source, transform, snapshot, rollup, or presentation |
| 19 | Day 25 | Pyramid Operations | Close deployment-operations layer | **Week 3 Scorecard** + deployment closeout | Name all 6 proof tasks from memory |

**Proof Tasks Due This Week:**
- ✅ Proof Task 4 (Day 16)
- ✅ Proof Task 5 (Day 18)
- ⬜ Proof Task 3 should be complete (started Day 13)

> **Gate:** If 2+ scorecard areas score **Fail**, repeat this layer in Week 4 instead of expanding scope.

---

## Week 4 — Contribution & Handoff (Days 20–28)

**Goal:** Complete remaining proof tasks, deliver a reviewable change slice, create a reusable team asset, and pass the Codex Gate.

| Day | Execution Guide Day | Track | Today's Focus | Evidence Artifact | Retention Check |
|---|---|---|---|---|---|
| 20 | Days 26–27 | Pyramid Operations | Validate content movement + build reviewer handoff path | Content-movement checklist + handoff draft | From Week 3: trace one KPI end-to-end from memory |
| 21 | **Day 28–29 (PT2+6)** | Codex Productivity | **Proof Task 2:** Review workflow dry run + **Proof Task 6:** Reviewer handoff test | Completed PT2 review package + PT6 handoff test | Pass Codex Gate check (all 6 gates) |
| 22 | Days 31–33 | BI Judgment | Select one narrow change slice, establish baseline, identify owning surface | Change-slice charter + baseline note + owning-surface note | State where business logic lives for this change |
| 23 | Days 34–36 | Pyramid Operations | Draft smallest fix path, run first validation cycle, repair | Fix-path draft + validation record + iteration note | Reproduce deployment sequence from memory |
| 24 | Days 37–40 | Codex Productivity | Record before/after, prepare review package, stress-test, close slice | Before/after note + review package + closed contribution package + **Week 4 Scorecard** | All 6 proof tasks complete? If not, list missing |
| 25 | Days 41–44 | BI Judgment | Practice surface recommendation, validate parameter/list/hierarchy, build reviewer explanation, final handoff rehearsal | Surface recommendation + reviewer-facing summary + final handoff rehearsal | Explain whether an issue is source, transform, snapshot, rollup, or presentation |
| 26 | Days 46–50 | Codex Productivity | Create one reusable team asset (charter → draft → test → revise) | Asset charter + draft v1 + test note + v2 + **Week 5 Scorecard** | Asset addresses real team problem |
| 27 | Days 51–55 | Pyramid Operations | Add Pyramid specificity, example use case, review as outsider, tighten language, publish | Surface-aware revision + example + assumption gap list + v3 + final asset | Asset is consumable by another developer without translation |
| 28 | **Days 56–60 (condensed)** | All Tracks | Bounded Codex test + manual-vs-Codex comparison + final readiness summary + final gate decision | Codex comparison note + final readiness statement + **Final Readiness Package** | **Final Codex Gate + closeout** |

**Proof Tasks Due This Week:**
- ✅ Proof Task 2 (Day 21)
- ✅ Proof Task 6 (Day 21)
- ✅ One reusable team asset (Days 26–27)

---

## Evidence-Backed Results & Reporting

### Daily Evidence Standard

Every day **must** produce at least one evidence artifact saved to `notes/` or `evidence/`:

| Artifact Type | Examples |
|---|---|
| Note | Readiness note, dependency map, logic note, boundary note |
| Prompt | Reusable prompt template + revision log |
| Checklist | Deployment checklist, preflight checklist, QC checklist |
| Validation Record | Expected vs. actual outcome, anomaly classification |
| Review Draft | Scope note, review request, reviewer questions |
| Handoff | Handoff draft, handoff package, reviewer-facing summary |
| Proof Task | Completed PT1–PT6 with all required sections |
| Reusable Asset | Prompt library, QC template, deployment checklist, troubleshooting guide |

### Weekly Reporting Standard

At the end of each week, produce:
1. **Weekly Scorecard** (`Pass` / `Partial` / `Fail` for all 7 areas)
2. **Proof Task Progress** — which tasks are complete, which remain
3. **Readiness Classification** — Foundational / Developing / Operational / Ready For Codex Acceleration
4. **Retention Summary** — what was retained from prior weeks
5. **Next Week Focus** — which track needs the most attention

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

### 2. Weekly Cross-Track Review
At the end of each week, answer these questions in your scorecard:
- What concept from **Week 1** am I still using daily?
- What concept from **Week 2** am I still using daily?
- What concept from **Week 3** am I still using daily?
- Which track (Pyramid / Codex / BI Judgment) did I advance most this week?
- Which track needs the most attention next week?

### 3. Cumulative Proof Task Checklist
Track completion across all 6 proof tasks. Revisit any failed proof task before attempting the Codex Gate.

| Proof Task | Week Due | Status | Notes |
|---|---|---|---|
| PT1: Repository Analysis Brief | Week 2 | ⬜ | |
| PT2: Review Workflow Dry Run | Week 4 | ⬜ | |
| PT3: Metric Lineage Walkthrough | Week 2–3 | ⬜ | |
| PT4: QC Evidence Pack | Week 3 | ⬜ | |
| PT5: Deployment Rehearsal | Week 3 | ⬜ | |
| PT6: Reviewer Handoff Test | Week 4 | ⬜ | |

---

## Standard Equipped Team Contributor Definition

A learner who completes this 4-week program is considered a **Standard Equipped Team Contributor** when ALL of the following criteria are met:

### Operational Readiness
- [ ] Can explain the dependency order from source loads to reporting outputs without notes
- [ ] Can identify the owning layer (source/transformation/snapshot/rollup/presentation) for any metric or defect
- [ ] Can validate model logic before trusting front-end numbers
- [ ] Can move Pyramid artifacts through environments with correct connections, access, and reviewer path
- [ ] Can produce QC evidence with a clear review entrypoint
- [ ] Can prepare a reviewer handoff package that another person can follow without clarification

### Codex Productivity Readiness
- [ ] Can use Ask, Edit, Agent, and Plan modes appropriately for the task
- [ ] Has 3+ stable, tested prompt templates for analysis, validation, and review
- [ ] Can use Codex to pull context, summarize state, identify next steps, and record a handoff
- [ ] Can constrain Codex to proven workflows (does not let AI define business logic)
- [ ] Has completed a manual-vs-Codex comparison and can articulate where AI helps vs. drifts

### BI Judgment Readiness
- [ ] Can articulate the business question before selecting a technical approach
- [ ] Can define metric grain, filters, exclusions, and ownership rules
- [ ] Can choose the appropriate output type (dashboard, report, alert, export, handoff, summary)
- [ ] Can produce validation evidence that a reviewer needs to trust the result
- [ ] Can distinguish between a data-quality issue, a logic error, and a presentation limitation

### Evidence & Contribution
- [ ] All 6 proof tasks are complete and documented in `evidence/`
- [ ] At least 1 reusable team asset has been created, tested, and published
- [ ] Weekly scorecards show no more than 1 area at **Fail** in the final week
- [ ] The Codex Gate decision is **Begin bounded Codex use** (or missing gates are explicitly documented)

### Retention Verification
- [ ] Can reproduce key concepts from Weeks 1–3 without referencing notes
- [ ] Daily notes demonstrate increasing independence (less reliance on templates, more own analysis)
- [ ] Can trace one KPI end-to-end from source conditions to final rollup from memory

---

## Codex Gate (Final Checkpoint)

Run this on Day 28. All must be **Yes** to begin bounded Codex use.

| Gate | Status |
|---|---|
| One end-to-end workflow completed manually or with standard Copilot support | Yes / No |
| Business-logic ownership understood (you know where logic lives and where it does not) | Yes / No |
| Validation evidence produced without help | Yes / No |
| All 6 proof tasks completed | Yes / No |
| One clean reviewable change slice delivered | Yes / No |
| One reusable team asset created | Yes / No |

**Decision:** Stay with standard Copilot workflows / Begin bounded Codex use

---

## Quick Reference: File Mapping

| File | Purpose |
|---|---|
| `README.md` | Overview, sharing notes, 4-week flow |
| `4-Week Onboarding Map.md` | **This file** — condensed daily/weekly plan with evidence, retention, and contributor definition |
| `Copilot Reference for MUE.md` | Copilot modes, custom instructions, prompt files, context management |
| `Custom Workflows for MUE.md` | Four operational workflows (repo analysis, review, handoff, daily learning) |
| `Codex Productivity Training Handoff.md` | Vision document — three-track rationale |
| `Pyramid, Codex, and BI Judgment Readiness Plan.md` | Full day-by-day and week-by-week readiness plan |
| `Pyramid, Codex, and BI Judgment Daily Execution Guide.txt` | 60-day execution plan (reference; use this map for scheduling) |
| `Pyramid, Codex, and BI Judgment Daily Working Template.txt` | Daily work blocks, checklists, scorecards (use directly) |
| `scripts/create_daily_note.py` | Creates daily note from template (enforces day ≤ 28) |
| `scripts/aggregate_weekly.py` | Aggregates weekly notes into reports/ |
| `.github/workflows/weekly-aggregator.yml` | Auto-generates weekly reports via GitHub Actions |
| `.github/instructions/mue-instructions.yml` | Team-wide Copilot working standards |
