# 🏗️ Pyramid Platform — Training Reference

> **Category:** 🏗️ Pyramid Platform  
> **Weeks Active:** 2–4  
> **Focus:** Model logic, deployment sequencing, QC, security, artifact movement, reviewer access

---

## Table of Contents

1. [Platform Overview](#1-platform-overview)
2. [Model Layer Architecture](#2-model-layer-architecture)
3. [Visual Surface Decision Rules](#3-visual-surface-decision-rules)
4. [Model & Formula Decision Rules](#4-model--formula-decision-rules)
5. [Deployment Sequencing](#5-deployment-sequencing)
6. [QC & Validation](#6-qc--validation)
7. [Artifact Migration](#7-artifact-migration)
8. [Security & Access Policy](#8-security--access-policy)
9. [Reviewer Path Setup](#9-reviewer-path-setup)
10. [Operating Principles](#10-operating-principles)

---

## 1. Platform Overview

Pyramid is a BI platform that provides a complete analytics environment: model design, metric definition, visual reporting, deployment management, and reviewer-ready content delivery.

In the MUE curriculum, Pyramid serves as one of three complementary tracks:

| Track | Role |
|-------|------|
| **🏗️ Pyramid** | Platform-specific BI context — mechanics of model, deployment, and delivery |
| **⚡ Codex** | Workflow process — context synthesis, handoff fluency, bounded automation |
| **🧠 BI Judgment** | Tool-agnostic analytical thinking — business questions, metrics, validation |

Pyramid training is not a prerequisite for Codex productivity or BI judgment. It provides the operational context where those skills are exercised.

---

## 2. Model Layer Architecture

A Pyramid model has distinct layers, each with a specific purpose and ownership:

```
┌─────────────────────────────────────────────────────┐
│                   PRESENTATION                       │
│  Dashboards · Reports · KPIs · Visual Surfaces      │
├─────────────────────────────────────────────────────┤
│                    ROLLUP                            │
│  Summaries · Aggregations · Weighted Totals         │
├─────────────────────────────────────────────────────┤
│                   SNAPSHOT                           │
│  Point-in-time state · Current vs. Previous         │
├─────────────────────────────────────────────────────┤
│                TRANSFORMATION                        │
│  Business logic · Row filters · Active/inactive      │
├─────────────────────────────────────────────────────┤
│                   SOURCE                             │
│  Raw data · Input tables · Load queries             │
└─────────────────────────────────────────────────────┘
```

### Key Model Elements

| Element | Purpose | Example |
|---------|---------|---------|
| **Data Point** | A single numeric value at a specific intersection | Revenue for Product A in Q1 |
| **Measure** | A named calculation or aggregation | `Total Sales = SUM(LineTotal)` |
| **Member** | An individual item in a hierarchy | Region = "West" |
| **Standard List** | A flat set of values | Status: Active, Inactive, Cancelled |
| **Range List** | A set of value ranges | Revenue bands: $0-$1K, $1K-$10K, $10K+ |
| **Model Attribute** | A property or descriptor of a dimension | Customer Segment, Product Category |
| **Parameter** | A user-controllable input | Date range selector, Filter value |
| **Level** | A position in a hierarchy | Year → Quarter → Month → Day |

### Dependency Order

When tracing a metric, always start at the lowest dependency layer and work upward:

1. **Source conditions** — What raw data enters the model?
2. **Transformation logic** — How are rows filtered, joined, and derived?
3. **Snapshot behavior** — What point-in-time state is captured?
4. **Rollup rules** — How are granular values aggregated to summaries?
5. **Presentation layer** — How is the final output displayed?

**Rule:** An upstream defect contaminates every downstream rollup. Always validate from the bottom up.

---

## 3. Visual Surface Decision Rules

Choose the right visual based on the business question:

### Detail & Validation
- Use **Matrix Grid**, **Tabular Grid**, or **Raw Results** when detail validation matters more than presentation.

### Ranking & Comparison
- Use **Column Chart**, **Bar Chart**, **Stacked variants**, **Tornado Chart**, or **Matrix Grid** for ranking and categorical comparison.

### Time Behavior
- Use **Line Chart**, **Spline Chart**, **Step Line Chart**, **Lollipop Chart**, **Area Chart**, or **Demand Forecast** for time-series analysis.

### Contribution to Change
- Use **Waterfall** or **IBCS Waterfall** when the business question is about contribution to change.

### Target vs. Actual
- Use **Bullet Chart**, **Gauges**, **KPIs**, **IBCS Column Chart**, or **IBCS Line Chart** for target-versus-actual communication.

### Hierarchical Composition
- Use **Tree Map Chart**, **Hierarchical Tree Map**, **Circle Packing**, **Hierarchical Circle Packing**, or **Sunburst Chart** for hierarchical composition.

### Stage Progression & Flow
- Use **Sankey Chart**, **Funnel Chart**, or **Pyramid Chart** for stage progression or flow.

### Spread, Outliers & Relationships
- Use **Box and Whisker**, **Scatter Chart**, **Scatter Line Chart**, **Bubble Chart**, or **Open High Low Close Chart** for spread, outliers, or relationships.

### Geo Concentration
- Use **Bubble Map Chart**, **Shape Map**, **Geo Heat Map**, **Layered Map**, or **Heat Grid** for geographic patterns.

### Simple Part-to-Whole
- Use **Pie Chart** or **Doughnut Chart** only when category count is small and the part-to-whole story is simple.

---

## 4. Model & Formula Decision Rules

When working with model logic, follow a structured diagnostic:

### 1. Identify the Owning Element Block
Determine which element type owns the behavior:
- **Data Point** — A specific value
- **Measure** — A calculated aggregate
- **Member** — A dimension value
- **Standard List** — A fixed set of options
- **Range List** — A set of value bands
- **Model Attribute** — A descriptive property
- **Parameter** — A user-controllable input
- **Level** — A hierarchy position

### 2. Identify the Aggregation Behavior
- Aggregate, Average, Count, Maximum, Median, Minimum
- Multiply, Sum, Variance, Standard Deviation
- Correlation-style logic

### 3. Identify the Time Behavior
- Current Period, Full Month, Full Week, Full Year
- Month To Date, Quarter To Date, Week To Date, Year To Date
- Parallel Periods
- Semantic time functions

### 4. Identify the Function Category
- Operators, Date-time functions, Financial functions, Formatting
- Geo logic, Identity logic, Logical functions, Math functions
- Statistical functions, String functions, Aggregate functions
- Hierarchical functions, List functions, Member functions

### 5. Parameter Design
If the issue is driven by user input, define:
- **Scope**: Model or Global
- **Type**: Text, Number, or Binary
- **Behavior**: Discrete List, Free Input, or Continuous

### 6. KPI Style Selection
If the output is KPI-based, choose the appropriate style:
- Signs, Squares, Cylinder, Data Bars, Text
- Reverse Signs, Circles, Dial, Bullet, Arcs

---

## 5. Deployment Sequencing

Deployments follow a repeatable sequence. Validate each step before proceeding to the next.

### Preflight Checklist

| Step | Check | Evidence |
|------|-------|----------|
| 1 | Connection validation — all source connections reachable | Connection test log |
| 2 | Model dependencies — correct build order | Dependency map |
| 3 | Access control — roles and permissions defined | Access notes |
| 4 | Reviewer path — preview URL or entrypoint identified | Reviewer path note |
| 5 | Rollback plan — documented undo sequence | Rollback runbook |

### Deployment Sequence

1. **Preflight validation** — Run checks against target environment
2. **Connection setup** — Verify all required connections exist before content migration
3. **Model deployment** — Deploy models in correct dependency order (source → transformation → snapshot → rollup)
4. **Reporting artifact migration** — Move dashboards, reports, and KPIs
5. **Security setup** — Apply intended access policy
6. **Post-deploy QC** — Run sanity checks, compare expected vs. actual outcomes
7. **Preview entrypoint** — Verify the exact URL a reviewer should open

### Deployment Rehearsal (PT5)

Proof Task 5 requires:
- A draft deployment sequence
- A dry run executing that sequence
- A recorded outcome with any issues flagged
- An updated runbook another developer could follow

---

## 6. QC & Validation

### QC Evidence Pack (PT4)

A complete QC evidence pack includes:

1. **What was checked** — The specific metrics, logic, or outputs validated
2. **Expected outcome** — What should happen under correct logic
3. **Actual outcome** — What the system produced
4. **Classification** — Whether anomalies are:
   - **Source data issue** — Input data is wrong
   - **Transformation logic error** — Business rule misapplied
   - **Snapshot timing issue** — Wrong point-in-time captured
   - **Rollup miscalculation** — Aggregation is incorrect
   - **Presentation limitation** — Display doesn't match intent
5. **Evidence** — Screenshots, logs, or query results

### QC Execution Principles

- Validate from the lowest dependency layer upward
- Test current vs. previous snapshot behavior
- Validate area-level outputs before validating summaries
- Trace at least one KPI end-to-end from source conditions to final rollup
- Record anomalies with expected and actual outcomes

### Error Classification

| Error Type | Example | Owning Layer |
|------------|---------|--------------|
| Source data | Wrong input values | Source |
| Logic error | Incorrect WHERE clause | Transformation |
| Snapshot issue | Wrong date range captured | Snapshot |
| Rollup error | Double-counting in summary | Rollup |
| Presentation | Wrong chart type obscures data | Presentation |

---

## 7. Artifact Migration

Moving content between environments (dev → test → prod) requires:

### Migration Checklist

| Artifact Type | Check |
|---------------|-------|
| **Model files** | Correct version, dependency order maintained |
| **Reporting content** | Dashboards linked to correct model version |
| **Connections** | All environment-specific connections updated |
| **Parameters** | Environment-appropriate defaults set |
| **Security** | Role assignments migrated or re-mapped |

### Content Movement (Wk4)

By Week 4, the learner should be able to:
- Validate artifact movement between environments
- Build a reviewer path with explicit entrypoint
- Produce a delivery packet that includes:
  - Environment target
  - Artifact list
  - QC summary
  - Access notes
  - Reviewer entrypoint (preview URL)

---

## 8. Security & Access Policy

### Access Policy Design

| Principle | Practice |
|-----------|----------|
| **Least privilege** | Grant minimum access needed for the role |
| **Role-based** | Define roles (Viewer, Editor, Admin) with clear boundaries |
| **Reviewer access** | Provide read-only access with explicit entrypoint |
| **Audit trail** | Document who has access and why |

### Common Access Patterns

- **Reviewers** — Read-only access to preview content, no write access
- **Contributors** — Write access to assigned content only
- **Deployers** — Full access to deployment pipeline

---

## 9. Reviewer Path Setup

A reviewer-ready delivery means the reviewer does not need to hunt for the right build or asset.

### Reviewer Path Requirements

| Requirement | Detail |
|-------------|--------|
| **Explicit entrypoint** | A direct URL or path to the content being reviewed |
| **Environment target** | Which environment the reviewer should use |
| **Access granted** | Reviewer has the correct role assigned |
| **Context** | What the reviewer is looking at and why |
| **Expected outcome** | What a passing review looks like |

### Handoff to Reviewer

The delivery packet should include:
- Environment target (e.g., `https://pyramid-dev.company.com/review/123`)
- Artifact list (models, reports, dashboards included)
- QC summary (what passed validation)
- Access notes (reviewer role assigned)
- Review entrypoint (exact preview URL)

---

## 10. Operating Principles

1. **Learn the manual workflow first** — Understand the deployment sequence before automating it.
2. **Validate from the lowest dependency layer upward** — Start at source data, end at presentation.
3. **Keep changes narrow enough for fast review** — A reviewable change slice is one metric or one model, not the entire platform.
4. **Treat deployment, access, and reviewer handoff as part of delivery** — Deployment is not complete until a reviewer can see the result.
5. **Leave behind reusable checklists and runbooks** — The next deployment should be faster than the first.
6. **Distinguish platform mechanics from business reasoning** — A Pyramid error is not necessarily a BI error.
7. **Produce QC evidence with a clear review entrypoint** — A reviewer should know exactly where to look and what to expect.
8. **Know the owning layer for any metric or defect** — Source, transformation, snapshot, rollup, or presentation.
