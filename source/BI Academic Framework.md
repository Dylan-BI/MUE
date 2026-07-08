# 🎓 BI Academic Framework — Level Integration

> **Category:** 🧠 Retention & Readiness · 📊 BI Judgment  
> **Weeks Active:** 1–4 (cumulative)  
> **Focus:** BI theory, assessment design, industry alignment, transfer learning — mapped to proficiency levels

---

## Table of Contents

1. [How to Use This Document](#1-how-to-use-this-document)
2. [Level 1 — Foundation: Theoretical Vocabulary](#2-level-1--foundation-theoretical-vocabulary)
3. [Level 2 — Development: Guided Application of Theory](#3-level-2--development-guided-application-of-theory)
4. [Level 3 — Operational: Independent Analysis with Academic Rigour](#4-level-3--operational-independent-analysis-with-academic-rigour)
5. [Level 4 — Mastery: Strategic Integration & Transfer](#5-level-4--mastery-strategic-integration--transfer)
6. [Assessment Enhancements](#6-assessment-enhancements)
7. [Industry Standards Alignment Matrix](#7-industry-standards-alignment-matrix)
8. [Threshold Concepts Deep Dive](#8-threshold-concepts-deep-dive)
9. [Academic Quick Reference](#9-academic-quick-reference)

---

## 1. How to Use This Document

This document adds a **BI academic theory layer** to the existing MUE curriculum. It is not a replacement. Each concept below is assigned to the proficiency level where it is most appropriate — L1 gets foundational awareness, L4 gets strategic integration.

### Integration with the 7 Learning Categories

| Academic Concept | Primary Category | Level Introduced |
|---|---|---|
| DIKW Pyramid | 📊 BI Judgment | L1 |
| Analytics types (descriptive/predictive/prescriptive) | 📊 BI Judgment | L1→L2 |
| Dimensional modelling basics | 🏗️ Pyramid Platform | L2 |
| ETL/ELT concepts | 🔗 Data & Lineage | L2 |
| Kimball lifecycle | 🏗️ Pyramid Platform | L2→L3 |
| Data governance & quality dimensions | 🔗 Data & Lineage | L3 |
| Visualisation theory (Tufte, Few, Cairo) | 📊 BI Judgment | L2→L3 |
| Rubric-based assessment | 🧠 Retention & Readiness | L3 |
| BI strategy & maturity models | 📊 BI Judgment | L4 |
| Industry standards (DMBOK, TDWI, SFIA) | All categories | L4 |
| Far-transfer assessment | 📊 Delivery & Handoff | L4 |
| Peer review calibration | 📦 Delivery & Handoff | L3→L4 |

---

## 2. Level 1 — Foundation: Theoretical Vocabulary

*For complete amateurs — learn the vocabulary of BI theory alongside the hands-on skills.*

### 2.1 DIKW Pyramid (Awareness)

Introduce the organising framework for all BI work:

```
         ⬆ Wisdom — "Why should we act?"
         ⬆ Knowledge — "How does it work?"
         ⬆ Information — "What does it mean?"
         ⬆ Data — "What are the raw facts?"
```

**Level 1 expectation:** The learner can name the four layers and give one example of each from their daily work. *Example: "The sales number 1,247 is Data. The context 'Q1 2026 West Region' makes it Information. Understanding that Q1 sales are trending 8% above forecast is Knowledge. Deciding to increase inventory is Wisdom."*

**Connects to:** BI Judgment category, Week 1 — every metric learners encounter can be classified on the DIKW pyramid.

### 2.2 Descriptive vs. Diagnostic Analytics (Awareness)

- **Descriptive:** "What happened?" (dashboards, reports, KPIs)
- **Diagnostic:** "Why did it happen?" (drill-down, root-cause analysis)

**Level 1 expectation:** The learner can classify any report or metric as descriptive or diagnostic. They do not yet need to produce diagnostic analytics — only recognise the difference.

### 2.3 What Is a Data Model? (Basic Concept)

Define a model as: *"A simplified representation of a real business situation, organised so that a computer can calculate answers."*

**Level 1 expectation:** The learner can explain in their own words what a data model is, using a familiar analogy (e.g., a spreadsheet with formulas).

### 2.4 Why Visualisation Matters

Introduce one core principle from **Edward Tufte**: *"Above all else, show the data."* The learner should understand that the goal of a chart is to communicate accurately, not to look impressive.

**Level 1 expectation:** The learner can identify a misleading chart and explain what makes it misleading (e.g., truncated axis, 3D distortion).

### 2.5 What Is a Rubric?

Introduce the concept of a scoring rubric: *"A set of criteria with clear descriptions of what each score level looks like."* The current Pass/Partial/Fail scorecard is a simple rubric. Learners should understand that reviewers use rubrics to score consistently.

**Level 1 expectation:** The learner can explain why rubrics are better than subjective scoring ("because two reviewers will give the same score for the same work").

---

## 3. Level 2 — Development: Guided Application of Theory

*For learners with some experience — apply theoretical concepts to real tasks.*

### 3.1 Analytics Maturity Model

Extend L1 awareness to the full four-type model:

| Type | Question | Example | Week Introduced |
|------|----------|---------|-----------------|
| **Descriptive** | What happened? | "Sales were $1.2M in Q1" | Wk1 (L1) |
| **Diagnostic** | Why did it happen? | "Sales dropped due to a pricing change in March" | Wk2 (L2) |
| **Predictive** | What will happen? | "Q2 sales are forecast at $1.35M based on current trends" | Wk3 (L3) |
| **Prescriptive** | What should we do? | "Increase marketing spend by 10% to capture the forecasted demand" | Wk4 (L4) |

**Level 2 expectation:** The learner can classify any given BI output into one of the four types AND give an example of a predictive question their organisation might ask.

**Connects to:** BI Judgment, all weeks — every validation exercise should include: "What type of analytics is this output?"

### 3.2 ETL/ELT Concepts

Introduce how data moves from source to model:

```
Source → Extract → Transform → Load → Model → Report
         (ETL is transform-before-load)
         (ELT is load-before-transform — modern data stacks)
```

**Level 2 expectation:** The learner can draw the data pipeline for their own work: "The source table is loaded via SQL, transformed in Pyramid's model layer, then reported in a dashboard." They should also know whether their environment uses ETL or ELT.

**Connects to:** Data & Lineage, Week 2 — before tracing lineage, learners should understand the pipeline mechanics.

### 3.3 Dimensional Modelling Basics

Introduce the two core structures:

| Concept | Definition | Example |
|---------|------------|---------|
| **Fact table** | Stores measurements or events | Sales transactions, clicks, log entries |
| **Dimension table** | Stores descriptive attributes | Customer name, product category, date |

**Level 2 expectation:** The learner can identify which tables in a model are facts and which are dimensions. They can explain why dimensions are stored separately from facts (to avoid repetition and enable flexible filtering).

**Connects to:** Pyramid Platform, Week 2 — model lineage exercises should label each layer as fact or dimension.

### 3.4 The Concept of Grain

**This is a threshold concept** — learners who miss it will produce unreliable metrics for their entire career.

Grain is *"the level of detail captured by a single row in a fact table."*

| Grain Statement | What It Means | Risk If Wrong |
|----------------|---------------|---------------|
| "One row per sales transaction" | Each row = one sale | Double-counting if grain is actually per line item |
| "One row per customer per month" | Each row = one customer's monthly activity | Wrong aggregation level for daily metrics |

**Level 2 expectation:** The learner can state the grain of any fact table they work with AND explain what would happen if the grain were misunderstood (e.g., "We would double-count revenue because each order has multiple line items").

**Practice exercise:** Given a sample dataset, ask the learner to write the grain statement and identify risks of misinterpreting it.

### 3.5 Introduction to Visualisation Theory

Add **Stephen Few**'s principle: *"A dashboard is a visual display of the most important information needed to achieve one or more objectives, consolidated and arranged on a single screen so the information can be monitored at a glance."*

**Level 2 expectation:** The learner can evaluate a dashboard against Few's definition — does it fit on one screen? Is the most important information prominent? Can it be read at a glance?

### 3.6 Calibrated Peer Review (Introduction)

Before learners can assess others, they must calibrate their own judgment. In L2, learners:
1. Score a **sample handoff** using the Handoff Quality Rubric
2. Compare their scores against an expert's scores
3. Note where they over- or under-scored

**Level 2 expectation:** The learner completes one calibration exercise and identifies one scoring bias (e.g., "I was too lenient on 'Current State' because the writer used good formatting even though the content was vague").

---

## 4. Level 3 — Operational: Independent Analysis with Academic Rigour

*For confident practitioners — apply academic frameworks independently.*

### 4.1 Kimball Lifecycle

Ralph Kimball's dimensional modelling methodology provides a structured approach to BI development:

```
┌─────────────────────────────────────────────────────────────┐
│                  KIMBALL LIFECYCLE                           │
│                                                              │
│ ① Program Planning → ② Business Requirements → ③ Technical  │
│    Strategy                       │            Strategy      │
│                                   ▼                          │
│                   ④ Dimensional Modelling                    │
│                   ⑤ Physical Design                          │
│                   ⑥ ETL Design & Development                 │
│                   ⑦ BI Application Design                    │
│                   ⑧ Deployment & Maintenance                 │
└─────────────────────────────────────────────────────────────┘
```

**Level 3 expectation:** The learner can map their current week's tasks to the relevant Kimball phase and explain why the phase order matters (e.g., "We should not design the ETL before completing dimensional modelling because the model determines what data we need").

**Connects to:** Pyramid Platform & Delivery & Handoff, Weeks 3-4 — deployment and handoff are Kimball phases ⑦-⑧.

### 4.2 Data Governance & Quality Dimensions

Introduce the **six dimensions of data quality** (from DAMA/DMBOK):

| Dimension | Definition | Example Check |
|-----------|------------|---------------|
| **Accuracy** | Data reflects reality | Compare source count to system of record |
| **Completeness** | All required data is present | Check for NULLs in required fields |
| **Consistency** | Data is coherent across systems | Same customer ID matches same name everywhere |
| **Timeliness** | Data is current enough for the task | Last refresh timestamp is within SLA |
| **Validity** | Data conforms to defined rules | Values are within expected ranges |
| **Uniqueness** | No duplicate records | No duplicate primary keys |

**Level 3 expectation:** The learner can classify any data quality issue they find into one of these six dimensions. This is the formal version of the existing error classification (source/transformation/snapshot/rollup/presentation).

**Practice exercise:** Given a bug report, the learner writes: "This is a Consistency issue — the same customer has two different names in Sales and Support tables."

### 4.3 Dimensional Modelling in Practice: Star Schemas & SCDs

| Concept | Definition | Level 3 Skill |
|---------|------------|---------------|
| **Star schema** | A central fact table connected to dimension tables | Can draw the star schema for their model |
| **Conformed dimension** | A dimension used consistently across multiple fact tables | Can identify shared dimensions (e.g., Date) |
| **Slowly Changing Dimension (SCD)** | How dimension attributes change over time | Can classify as SCD Type 1 (overwrite), Type 2 (add row), or Type 3 (add column) |

**Level 3 expectation:** The learner can produce a star-schema diagram for any model they work with AND identify which dimensions are conformed and which SCD type applies to each.

### 4.4 Validation Methodology: Bottom-Up Verification

Formalise the existing validation practice with academic language:

> **Bottom-up verification principle:** Always validate from the lowest dependency layer to the highest. A defect discovered at the presentation layer could originate in the source, transformation, snapshot, or rollup layer. Without bottom-up verification, you fix symptoms, not causes.

**Level 3 expectation:** Given a metric discrepancy, the learner produces a **validation chain** — a step-by-step log showing they ruled out each lower layer before concluding the error is at the current layer.

**Template for a validation chain:**
```
Validation Chain — Metric "Active Customers"
1. ✅ Source: Raw input counts match system of record
2. ✅ Transformation: Row filters correctly include only active accounts
3. ✅ Snapshot: Point-in-time state matches end-of-month extract
4. ❌ Rollup: Area-level summaries do not sum to total — double-counting in the "Multiple Products" category
5. — Presentation: Not yet validated (blocked by rollup error)
```

### 4.5 Self-Assessment Against the Analytic Rubric

By L3, learners can score themselves using the full 4-level rubric (see Section 6) and justify each score with evidence.

**Level 3 expectation:** The learner produces a weekly self-assessment that includes:
- A score for each of the 7 scorecard areas using the 1–4 scale
- A specific evidence citation for each score (e.g., "Change isolation: 3 — my change charter included before/after but not owning surface")
- A one-paragraph reflection on the gap between self-score and reviewer score

### 4.6 Threshold Concept Deep Dive: Row Ownership

Row ownership is the BI equivalent of "who owns the source of truth." It is a threshold concept because once understood, it transforms how a learner sees all data disputes.

**The core question:** *"Which layer, component, or person defines which rows are included in or excluded from a metric?"*

| Common Row Ownership Patterns | Who Decides | Risk |
|---|---|---|
| Source system defines | IT/operations | Business may not agree with IT's inclusion rules |
| Model transformation defines | BI developer | If undocumented, no one knows why rows are excluded |
| Report filter defines | End user | Every user may get different counts |
| No one defines | — | Metric is unreliable, everyone distrusts it |

**Level 3 expectation:** For any metric they validate, the learner can state: "Row ownership for this metric lives in [layer], defined by [rule]. If we change that rule, the metric value changes by [estimated impact]."

---

## 5. Level 4 — Mastery: Strategic Integration & Transfer

*For expert-ready learners — use academic frameworks to design, teach, and transfer.*

### 5.1 BI Strategy & Maturity Models

| Maturity Model | Stages | Level 4 Application |
|---|---|---|
| **TDWI BI Maturity Model** | Prenatal → Infant → Child → Teenager → Adult → Sage | Assess the current organisation's stage and design a 6-month improvement plan |
| **Gartner BI Maturity Model** | Unaware → Opportunistic → Systematic → Differentiating → Transformational | Evaluate whether current BI investments align with business strategy |

**Level 4 expectation:** The learner produces a one-page BI maturity assessment of their organisation, identifying the current stage and two concrete actions to advance to the next stage.

### 5.2 Industry Standards Alignment

The curriculum should prepare learners for recognised industry certifications and frameworks:

| Framework | Relevance | L4 Application |
|---|---|---|
| **DMBOK** (Data Management Body of Knowledge) | Data governance, quality, lineage | Map one week's work to DMBOK knowledge areas |
| **TDWI BI Framework** | BI program structure, architecture | Evaluate current BI architecture against TDWI reference model |
| **SFIA** (Skills Framework for the Information Age) | Role definitions, skill levels | Map own skill level for "Data Visualisation" (SFIA VISL) and "Data Modelling" (SFIA DTAN) |
| **ACM/AIS IS 2020 Curriculum Guidelines** | Program-level BI education standards | Compare MUE curriculum to IS 2020 BI/analytics competency areas |

**Level 4 expectation:** The learner can produce an **alignment matrix** showing how their completed MUE evidence maps to one industry standard of their choice.

### 5.3 Far-Transfer Assessment Design

Far-transfer tests whether the learner can apply BI judgment outside the specific tools and contexts they trained on.

**Level 4 exercise:** The learner is given an unfamiliar BI scenario (e.g., a Tableau workbook, a Power BI report, or even a non-BI context like a supply-chain dataset) and must:

1. Articulate the business question being answered
2. Identify the grain and metric definition
3. Trace the implied data lineage
4. Flag validation risks
5. Propose a reviewer-ready handoff structure

**Level 4 expectation:** The learner completes one far-transfer exercise and writes a reflection on what skills transferred and what required new learning.

### 5.4 Peer Review Calibration & Mentoring

**Level 4 expectation:** The learner:
- Reviews two handoffs from L2 or L3 learners using the 4-level rubric
- Provides written feedback with evidence citations
- Calibrates their scores against another L4 reviewer
- Writes a one-page mentoring note: "What I look for in a handoff and why"

### 5.5 Portfolio Assessment

Instead of a single Codex Gate score, the L4 learner submits a **portfolio** of their three best artifacts with a reflective narrative:

| Artifact | Chosen Because | Demonstrates |
|---|---|---|
| [Evidence file path] | "This was my hardest validation because..." | Analytical rigour, persistence |
| [Handoff file path] | "This handoff was used by a reviewer who completed the work without asking me questions" | Communication quality, reviewer readiness |
| [Reusable asset] | "This prompt template saved my team 2 hours per deployment" | Value creation, transferability |

**Level 4 expectation:** The portfolio is included in the Day 28 closeout as the capstone assessment alongside the Codex Gate.

### 5.6 Threshold Concept Deep Dive: Bounded Codex as Metacognition

Bounded Codex is the meta-cognitive skill of knowing when *not* to use AI. This is harder than knowing when to use it.

**Academic framing:** This maps to **Flavell's metacognitive model** — the ability to monitor and regulate one's own cognitive processes.

| Metacognitive Skill | Bounded Codex Equivalent |
|---|---|
| **Planning** — What strategy should I use? | Define the boundary before prompting |
| **Monitoring** — Am I on track? | Check that Codex respected the bounds |
| **Evaluating** — Did it work? Did I learn? | Record which constraint patterns work for which task types |

**Level 4 expectation:** The learner produces a **Bounded Codex pattern library** — a curated set of 5+ bounded prompt templates with notes on when each pattern is effective, when it fails, and why.

---

## 6. Assessment Enhancements

### 6.1 Proposed 4-Level Analytic Rubric

Replace Pass/Partial/Fail with a 4-level scale for each of the 7 scorecard areas. This gives reviewers a **shared mental model** and improves inter-rater reliability.

#### Prompt Discipline

| Level | Label | Description |
|-------|-------|-------------|
| **1** | Novice | Prompts are unstructured, missing context, or require significant clarification |
| **2** | Developing | Prompts have structure but occasionally drift or lack necessary constraints |
| **3** | Proficient | Prompts are clear, scoped, and include relevant context; drift is rare |
| **4** | Exemplary | Prompts are reusable templates with explicit bounds, context, and fallback handling; others adopt them |

#### Repo or Workspace Analysis

| Level | Label | Description |
|-------|-------|-------------|
| **1** | Novice | Cannot explain the business purpose or dependency order of the workspace |
| **2** | Developing | Can name files but cannot trace dependencies between them |
| **3** | Proficient | Can produce a dependency map with business purpose, inputs, outputs, and risks |
| **4** | Exemplary | Analysis is reusable as onboarding documentation for new team members |

#### Change Isolation

| Level | Label | Description |
|-------|-------|-------------|
| **1** | Novice | Changes are broad and not reviewable as a single slice |
| **2** | Developing | Change is scoped but missing before/after documentation |
| **3** | Proficient | Change charter includes before/after, owning surface, and review path |
| **4** | Exemplary | Change slice is consumable by a reviewer without verbal explanation; includes impact analysis |

#### Validation Order

| Level | Label | Description |
|-------|-------|-------------|
| **1** | Novice | Validates in random order or starts at presentation layer |
| **2** | Developing | Starts bottom-up but skips layers |
| **3** | Proficient | Produces a validation chain from source to presentation |
| **4** | Exemplary | Validation chain includes error classification (source vs. transform vs. snapshot vs. rollup vs. presentation) |

#### Deployment Awareness

| Level | Label | Description |
|-------|-------|-------------|
| **1** | Novice | Cannot describe the deployment sequence |
| **2** | Developing | Can list steps but not explain why order matters |
| **3** | Proficient | Can execute deployment from memory with a written runbook |
| **4** | Exemplary | Runbook is reusable by another developer; includes rollback plan and environment differences |

#### Reviewer Handoff

| Level | Label | Description |
|-------|-------|-------------|
| **1** | Novice | Handoff is missing key sections or assumes reviewer has context |
| **2** | Developing | All sections present but some are vague or incomplete |
| **3** | Proficient | Handoff passes the Handoff Quality Rubric in all sections |
| **4** | Exemplary | Handoff is consumable by a reviewer who has never seen the work before; includes context, decisions, and rationale |

#### Reusability

| Level | Label | Description |
|-------|-------|-------------|
| **1** | Novice | No reusable assets created |
| **2** | Developing | Asset exists but is specific to one task and not generalised |
| **3** | Proficient | Asset is reusable by others with minimal adaptation |
| **4** | Exemplary | Asset is adopted by the team; includes documentation and version history |

### 6.2 Triangulated Classification

The current classification (Foundational → Developing → Operational → Ready for Codex Acceleration) should draw from **three sources**, not just the scorecard:

| Source | What It Measures | Weight |
|--------|-----------------|--------|
| **Scorecard trend** (last 2 weeks) | Current competency across 7 areas | 40% |
| **Proof task completion rate** | Cumulative progress across all 6 PTs | 30% |
| **Handoff quality trend** (last 3 handoffs vs. rubric) | Communication and reviewer readiness | 30% |

**Rule:** If the three sources disagree (e.g., scorecard says "Operational" but handoff quality is "Developing"), the classification defaults to the lowest source until all three converge.

### 6.3 Competency Profile for Codex Gate

Replace the binary Yes/No Codex Gate with a **competency profile**:

| Area | Level (1–4) | Evidence Required |
|------|-------------|-------------------|
| Handoff reading | | EX1 result |
| Context pull | | EX2 result |
| State summary | | EX3 result |
| Handoff creation | | EX4 result + rubric score |
| Manual-vs-Codex judgment | | EX5 result |
| Bounded Codex | | EX6 result + pattern library |
| Reusable asset creation | | Asset charter + v1 + v2 |

**Gate decision:** The learner is cleared for bounded Codex use when ALL areas are at Level 3 or above. If any area is Level 2 or below, the learner stays on standard Copilot workflows with a specific improvement plan for the weak area.

---

## 7. Industry Standards Alignment Matrix

| MUE Category | DMBOK Knowledge Area | TDWI BI Framework Component | SFIA Skill |
|---|---|---|---|
| 🤖 AI & Copilot | — (emerging) | — | INOV (Innovating) |
| ⚡ Codex Productivity | — (emerging) | — | METL (Metacognitive skills — proposed) |
| 🏗️ Pyramid Platform | Data Modelling & Design | BI Architecture, Data Integration | DTAN (Data Modelling), ITOM (IT Operations) |
| 📊 BI Judgment | — (cross-cutting) | BI Analysis, Performance Management | VISL (Visualisation), METL (Analytical Thinking) |
| 🔗 Data & Lineage | Data Quality, Data Warehousing, Data Integration | Data Integration, Data Management | DGOV (Data Governance), DQAN (Data Quality) |
| 📦 Delivery & Handoff | — (cross-cutting) | BI Delivery, BI Organisational Factors | REQM (Requirements), BPRE (Business Process Improvement) |
| 🧠 Retention & Readiness | — (programme management) | BI Organisational Factors | EVID (Evidence-based practice) |

---

## 8. Threshold Concepts Deep Dive

Threshold concepts are ideas that, once understood, transform how a learner thinks about everything else. They are often troublesome because they require letting go of a prior mental model.

### 8.1 Grain (📊 BI Judgment)

| Aspect | Detail |
|--------|--------|
| **Why it's troublesome** | Learners want grain to be "the level of detail." It is actually a statement about *what one row represents*, which is a subtle but critical distinction. |
| **Common misconception** | "Fine grain = more detail." This is true but misses the point — the real skill is knowing *what question the grain answers*. |
| **Breakthrough question** | "If I have two rows that look identical, are they duplicates or do they represent two different things?" |
| **Check for understanding** | Given a table and a metric, ask: "State the grain. If we changed the grain to [coarser/finer], which rows would be affected and how would the metric change?" |

### 8.2 Row Ownership (🔗 Data & Lineage)

| Aspect | Detail |
|--------|--------|
| **Why it's troublesome** | Learners assume "the data comes from the source system." They do not realise that every transformation, filter, and join is an act of row selection. |
| **Common misconception** | "Row ownership is about who owns the database." No — it's about who or what decides which rows are included or excluded. |
| **Breakthrough question** | "If two people run the same report and get different counts, where would you look first to understand why?" |
| **Check for understanding** | For any metric, ask: "Who owns the rows? What would happen if that rule changed? How would you document the rule so a future developer knows it exists?" |

### 8.3 Bounded Codex (⚡ Codex Productivity)

| Aspect | Detail |
|--------|--------|
| **Why it's troublesome** | It requires metacognition — thinking about one's own thinking. Learners want to use Codex to go faster; bounded Codex asks them to sometimes go slower. |
| **Common misconception** | "If Codex gives a good answer, it was the right question to ask." No — a confident wrong answer is more dangerous than no answer. |
| **Breakthrough question** | "What part of this task am I asking Codex to decide for me — and should I be the one deciding it?" |
| **Check for understanding** | Given a task, ask: "Write a bounded prompt. What did you put in the 'Do NOT' section and why?" |

---

## 9. Academic Quick Reference

### Recommended Reading by Level

| Level | Reading |
|-------|---------|
| **L1** | Tufte, E. — *The Visual Display of Quantitative Information* (Chapter 1 only) |
| **L2** | Few, S. — *Information Dashboard Design* (Chapters 1–3); Kimball, R. — *The Data Warehouse Toolkit* (Chapter 1) |
| **L3** | Kimball, R. — *The Data Warehouse Toolkit* (Chapters 2–4 on dimensional modelling); DAMA — *DMBOK* (Data Quality chapter) |
| **L4** | TDWI BI Maturity Model whitepaper; Gartner — "BI and Analytics Maturity Model"; SFIA Framework documentation |

### Academic Vocabulary by Level

| L1 | L2 | L3 | L4 |
|----|----|----|----|
| Data, Information | Descriptive, Diagnostic | Predictive, Prescriptive | Strategy, Maturity |
| Model | Fact, Dimension | Star schema, SCD | Governance, Stewardship |
| Chart, Visualisation | Grain, ETL/ELT | Validation chain, Rubric | Far-transfer, Portfolio |
| Rubric | Calibration | Bottom-up verification | Alignment, Standards |

---

*This framework is designed to be read alongside the 4-Week Onboarding Map and LEARNING_CATEGORIES.md. Each level above corresponds to the same proficiency level in the curriculum — 🌱 Foundation (L1), 🌿 Development (L2), 🌳 Operational (L3), 🏆 Mastery (L4).*
