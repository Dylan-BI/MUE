# GitHub Well-Architected Principles

> **Category:** 🏗️ Pyramid Platform, 📊 BI Judgment  
> **Source:** `github/github-well-architected` framework, DevOps core principles  
> **Weeks:** 2–4

---

## Overview

This guide adapts the [GitHub Well-Architected](https://github.com/github/github-well-architected) framework's **Productivity** and **Collaboration** pillars for the MUE curriculum. These principles apply to any platform — Pyramid, Codex, or custom BI tools — by focusing on the operational patterns that make analytics reliable, reviewable, and repeatable.

---

## 1. Automation First

### Principle

Every manual process that can be automated should be. Automation reduces human error, enforces consistency, and frees reviewers to focus on judgment rather than mechanics.

### Application to Analytics

| Manual Process | Automated Alternative | Tooling |
|----------------|-----------------------|---------|
| Running data extracts | Scheduled extract workflows | GitHub Actions, cron |
| QC checks | Automated validation scripts | Python tests, dbt tests |
| Deployment steps | CI/CD pipelines | GitHub Actions, environments |
| Change documentation | Auto-generated handoff notes | Handoff templates + AI |
| Reviewer access | Role-based access control | GitHub teams, environments |

### MUE Exercise

1. Identify one manual step in your current workflow
2. Write a GitHub Action or script to automate it
3. Include validation (does it work correctly?)
4. Document the automation for others to use

---

## 2. Continuous Integration & Deployment

### Principle

Changes should be validated and deployed through automated pipelines with clear gates. This ensures that every change is tested, reviewed, and traceable.

### Analytics CI/CD Pipeline

```
CODE → COMMIT → CI (lint/test) → REVIEW → STAGING (QC) → PRODUCTION
  │         │           │           │            │            │
  └─Write   └─Push      └─Validate  └─Approve    └─Verify     └─Release
```

### CI/CD Components for Analytics

| Component | Purpose | Example |
|-----------|---------|---------|
| **Lint/Format** | Ensure code consistency | SQLFluff, Black, ESLint |
| **Unit tests** | Validate logic | pytest, Jest |
| **Data tests** | Validate model output | dbt tests, Great Expectations |
| **QC pipeline** | Multi-environment promotion | GitHub Actions environments |
| **Deployment gate** | Require review before production | Environment protection rules |

### Deployment Sequencing (Pyramid-specific)

```
DEV ──→ TEST ──→ UAT ──→ PRODUCTION
 │        │        │          │
 └─Build   └─QC     └─Sign-off └─Monitor
```

Each promotion requires:
- All tests passing
- Reviewer approval
- QC evidence pack
- Rollback plan

---

## 3. QC Execution & Evidence

### Principle

Every change must produce verifiable evidence that it works correctly. QC is not a phase — it's embedded in the workflow.

### QC Evidence Pack Template

```markdown
## QC Evidence Pack — {Change Description}

### What Was Validated
- [ ] Data accuracy — Source vs. target row counts match
- [ ] Business logic — Metric definitions match spec
- [ ] Edge cases — Nulls, duplicates, boundary values handled
- [ ] Performance — Query completes within SLA

### Validation Results
| Check | Expected | Actual | Pass/Fail |
|-------|----------|--------|-----------|
| Row count | 1,234 | 1,234 | ✅ Pass |
| Null rate | <5% | 2.3% | ✅ Pass |
| Response time | <2s | 1.4s | ✅ Pass |

### Artifacts
- {Link to test output}
- {Link to screenshot/dashboard}
- {Link to log file}

### Sign-off
- **Reviewer:** {name}
- **Date:** {date}
- **Status:** {Approved / Changes Needed}
```

### MUE Exercise

For each model change you make:
1. Before: Write down what you expect to happen
2. After: Capture actual results (screenshot, log, output)
3. Compare: Document any differences
4. Sign off: Get reviewer confirmation

---

## 4. Security & Access Policy

### Principle

Access to data, models, and deployment should follow least-privilege principles. Reviewers need visibility; deployers need permissions; end-users need data only.

### Access Model for Analytics

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Viewer  │    │ Contributor│   │ Deployer │    │  Admin   │
│ Read-only│    │ Create/edit│   │ Promote  │    │ Configure│
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

| Role | Access | Review Permissions |
|------|--------|-------------------|
| **Viewer** | Read dashboards, reports | Comment only |
| **Contributor** | Create/edit models, data | Submit for review |
| **Reviewer** | Review changes, approve/reject | Approve pull requests |
| **Deployer** | Promote to production | Deploy after review |
| **Admin** | Configure permissions, settings | Full access |

---

## 5. Reviewer Path & Handoff

### Principle

The path from work completion to reviewer assessment should be clear, documented, and repeatable. Reviewers should not need to hunt for context.

### Standard Review Path

```
1. LEARNER completes work in action/
2. LEARNER files evidence in action/evidence/
3. LEARNER writes handoff note in action/notes/
4. LEARNER runs sync: action/ → review/
5. REVIEWER opens dashboard → Third Party Review
6. REVIEWER reviews changes, leaves comments
7. LEARNER addresses feedback → iterate
8. REVIEWER approves → work is complete
```

### What Reviewers Need

| Need | How MUE Provides It |
|------|---------------------|
| **What changed** | Learner-scoped change tracking (diff) |
| **Why it changed** | Handoff notes with rationale |
| **Evidence** | QC evidence packs, test outputs |
| **Context** | Source criteria reference files |
| **Communication** | Comment/mailto per artifact |
| **Progress** | Dashboard overview, Curriculum Review tab |

---

## 6. Traceability & Versioning

### Principle

Every artifact must be traceable back to its source. Changes must be versioned and reversible.

### Traceability Chain

```
BUSINESS QUESTION
  └─→ METRIC DEFINITION
        └─→ DATA MODEL
              └─→ TRANSFORMATION
                    └─→ OUTPUT (dashboard/report/alert)
                          └─→ QC EVIDENCE
                                └─→ REVIEWER SIGN-OFF
```

### Versioning Requirements

| Artifact | Version Method | Retention |
|----------|----------------|-----------|
| **Code** | Git commit hash | Permanent |
| **Data models** | Git + model version | Permanent |
| **Dashboards** | Git + deployment version | Permanent |
| **Reports** | Date-stamped files | 90 days |
| **QC evidence** | Linked to commit | Until next version |

---

## 7. Business Judgment & Metric Design

### Principle

BI output is only as good as the thinking behind it. Before building anything, answer these questions:

### Business Question Framework

```
1. What decision will this output support?
2. Who is making the decision?
3. What is the metric definition? (numerator/denominator/grain)
4. What filters or exclusions apply?
5. What is the data source and lineage?
6. How will accuracy be validated?
7. Is the output a dashboard, report, alert, or handoff?
```

### Metric Quality Criteria

| Criterion | Question | Red Flag |
|-----------|----------|----------|
| **Relevance** | Does this metric drive a decision? | "It would be interesting to know..." |
| **Precision** | Is the definition unambiguous? | "Total users" without time range |
| **Accuracy** | Can we validate the result? | No source comparison possible |
| **Stability** | Does the definition change? | Metric means different things in different reports |
| **Ownership** | Who is responsible for this metric? | No clear owner |

### MUE Exercise

1. Pick a business question
2. Define the metric: formula, grain, filters, exclusions
3. Trace the lineage: source → transformation → output
4. Validate: run the query, check against source
5. Document: write the metric definition for a reviewer

---

## References

- [GitHub Well-Architected](https://github.com/github/github-well-architected) — Productivity, Collaboration, Security framework
- [GitHub Well-Architected Design Principles](https://github.com/github/github-well-architected/tree/main/content/library/productivity/design-principles.md) — Automation, integration, continuous learning
- [Awesome Copilot DevOps Principles](https://github.com/github/awesome-copilot) — DevOps core principles, observability, pairing
- [CodeQL Coding Standards](https://github.com/github/codeql-coding-standards) — Code review checklist and quality standards
