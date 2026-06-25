# Module 3 - Pyramid Operational Readiness Plan

## Overview

This module lays out a practical improvement path for becoming an experienced Pyramid contributor who can operate inside a mature BI team. The plan is intentionally broader than dashboard building. In this workspace, Pyramid work sits inside a larger delivery model that includes prompt discipline, repository analysis, change isolation, source validation, deployment sequencing, QC, security awareness, and reviewer handoff.

The goal is to become operationally reliable before using Codex as a force multiplier. That means learning the workflow well enough to explain it, validate it, and hand it off cleanly without depending on AI to invent the missing logic.

## Target Outcome

By the end of this plan, you should be able to:

- explain the dependency order from source loads to reporting outputs
- create reliable prompts for analysis, validation, and review tasks
- validate model logic before trusting front-end numbers
- move Pyramid artifacts through an environment with the right connections, access, and reviewer path
- provide QC evidence with a direct review entrypoint
- use Codex to speed up proven workflows instead of replacing understanding

## Operating Principles

1. Learn the manual workflow first.
2. Use AI to compress repetitive work, not to define business truth.
3. Validate from the lowest dependency layer upward.
4. Keep changes narrow enough for fast review.
5. Treat deployment, access, and reviewer handoff as part of delivery.
6. Leave behind reusable prompts, checklists, or runbooks.

## Day-By-Day Plan

The first five working days should build a stable foundation.

| Day | Focus | Work To Perform | Evidence Of Completion |
|---|---|---|---|
| 1 | AI operating discipline | Learn when to use Ask, Edit, Agent, and Plan modes. Practice writing prompts with persona, objective, constraints, context, format, and quality bar. Write down the limits of context windows and why prompt bloat causes drift. | A one-page note that explains mode choice, prompt structure, and context limits in your own words. |
| 2 | Reusable prompt setup | Create three reusable prompt templates: one for repository analysis, one for SQL or model validation, and one for deployment or QC review. Test each prompt on real material and revise them after failures. | Three working prompts plus a short note describing what failed in the first version and what you changed. |
| 3 | Review discipline | Practice isolating one narrow change. Use a document or a small change slice, stage only that scope, and write a review request that states purpose, audience, review focus, and questions for reviewers. | A clean change set with a focused commit message and a draft review description. |
| 4 | Model lineage understanding | Trace the current BI model from source-load logic through hierarchy and service modeling into snapshot logic and rollups. Do not start in the front end. Start where the data is shaped. | A one-page dependency map that names the load layer, transformation layer, snapshot layer, area rollup, market rollup, total rollup, and QC layer. |
| 5 | Pyramid operations baseline | Build a deployment checklist that covers connection setup, model migration, reporting artifact migration, security setup, reviewer access, rerun steps, and direct preview entrypoints. Include fonts, themes, or manual configuration items if they are not versioned. | A checklist that another developer could follow without a meeting. |

## Week-By-Week Plan

After the first week, the next month should focus on repeated operational reps.

### Week 2: Validate The Data Foundation

Focus on source-load logic, deduplication, grain, and row ownership.

Tasks:

- inspect the source-load SQL and identify where current row sets are defined
- confirm which layer owns deduplication and which layer preserves business history
- confirm the reporting grain used by the final reporting tables
- identify where parent-level double counting could occur if aggregation is handled incorrectly

Pass criteria:

- you can explain why an upstream defect contaminates every downstream rollup
- you can name the top three data quality risks without opening the front end
- you can state which tables or views own row selection, deduplication, and aggregation

### Week 3: Validate The Core Model Layer

Focus on the hierarchy, service model, base logic, and goal logic.

Tasks:

- validate the area hierarchy and confirm the business grain used for goal evaluation
- validate the entity or service model and identify the logic for active rows, cancellations, and deleted rows
- validate the base penetration logic and ensure metric definitions are consistent
- validate the goal curve or target layer and confirm how lifecycle position affects expected outcomes

Pass criteria:

- you can state what each layer owns in one sentence
- you can tell another developer where to look first when a metric is wrong
- you can explain why goals must be evaluated at the lowest operational grain before rollup

### Week 4: Validate Snapshot And Rollup Logic

Focus on current versus previous logic and the transition from granular outputs to summaries.

Tasks:

- test current and previous snapshot behavior and confirm the correct date logic
- validate area-level outputs before validating market or total summaries
- trace at least one KPI end to end from source conditions to final rollup
- run sanity checks and record any anomalies with expected and actual outcomes

Pass criteria:

- you can trace one KPI from raw business rules to final summary output
- you can explain a discrepancy without immediately blaming Pyramid
- you can identify whether an error belongs to source data, transformation logic, snapshot logic, rollup logic, or presentation

### Week 5: Rehearse Deployment Operations

Focus on moving from local understanding to repeatable delivery.

Tasks:

- run or shadow preflight validation
- provision roles or confirm access assumptions
- deploy the model in the correct sequence
- run post-deploy QC and record the outcome
- apply the intended access policy and confirm who should and should not receive access

Pass criteria:

- you can describe the deployment sequence from memory
- you produce a dry-run log or checklist with evidence of each step
- another developer could follow your runbook with minimal questions

### Week 6: Rehearse Pyramid-Facing Delivery

Focus on the last mile: artifact movement, reviewer readiness, and consumable handoff.

Tasks:

- confirm required connections exist before content migration
- migrate or document the movement of models and reporting artifacts
- validate security expectations for reviewers
- verify the exact entrypoint or preview URL that a reviewer should open
- ensure the reviewer does not need to hunt for the right build or asset

Pass criteria:

- you can prepare a complete delivery packet without verbal explanation
- the delivery packet includes environment target, artifact list, QC summary, access notes, and reviewer entrypoint
- the reviewer path is individual and explicit, not shared and ambiguous

## Month-By-Month Plan

The second and third months are where learning turns into contribution.

### Month 2: Own One Narrow Change Slice End To End

Choose one scoped item such as a validation improvement, a metric discrepancy investigation, a checklist improvement, a model clarification, or a handoff improvement. Move it from analysis to review to validation.

Required evidence:

- a short change summary
- the validation steps you ran
- the before and after behavior
- review feedback or reviewer questions
- final disposition of the change

Success standard:

- the work is accepted without bringing unrelated changes into the same review
- the validation evidence is strong enough that someone else can trust the result

### Month 3: Standardize One Reusable Team Asset

Create something that reduces future manual work. Good examples include:

- a prompt library for repository analysis, SQL review, and deployment review
- a QC evidence template
- a deployment checklist with preflight and post-deploy sections
- a reviewer handoff template with access, entrypoint, and expected checks
- a troubleshooting guide for common metric or deployment failures

Required evidence:

- the asset is documented clearly enough for someone else to use
- another team member can follow it without you translating it live
- it reduces repeated explanation, repeated setup errors, or repeated QC omissions

## Specific Proof Tasks Before Moving To Codex

These tasks prove operational efficiency. Complete them before making Codex your primary tool for Pyramid work.

### Proof Task 1: Repository Analysis Brief

Pick one important logic chain and write a concise brief covering:

- business purpose
- dependency order
- key inputs and outputs
- risk areas
- safest place to make a simple change

What it proves: you can orient yourself in a mature repo without guessing.

### Proof Task 2: Review Workflow Dry Run

Take one narrow document or change slice through a clean review workflow. Keep scope tight, write a focused description, and request feedback on specific points.

What it proves: you can isolate work for review instead of mixing unrelated changes.

### Proof Task 3: Metric Lineage Walkthrough

Choose one KPI such as uptake, projected uptake, goal gap, subscriber gap, or a similar operational metric. Trace it from source conditions to transformation logic to snapshot logic to rollup logic.

Your walkthrough should answer:

- what is the counting grain
- what makes a row active or inactive
- how current and previous periods are defined
- where the formula is calculated
- how the value is rolled up
- which layer should be checked first if the number looks wrong

What it proves: you understand the number before surfacing it in Pyramid.

### Proof Task 4: QC Evidence Pack

Run sanity checks and targeted validations. Record:

- what you checked
- what the expected outcome was
- what the actual outcome was
- whether any anomaly is a true defect, a data issue, or an expected limitation
- what action was taken next

What it proves: you can establish trust in the output instead of treating QC as a formality.

### Proof Task 5: Deployment Rehearsal

Perform or shadow a full dry run from preflight through deployment, QC, and access confirmation.

Your record should include:

- environment target
- sequence of steps
- dependencies that had to exist first
- failures or warnings encountered
- final state after deployment

What it proves: you can operate beyond development and support real delivery.

### Proof Task 6: Reviewer Handoff Test

Prepare a reviewer handoff package that contains:

- the exact entrypoint the reviewer should open
- the environment or build being reviewed
- the checks the reviewer is expected to perform
- access notes
- known limitations or watch items

What it proves: your output is consumable by another person without back-and-forth confusion.

## Weekly Scorecard

Score yourself at the end of each week using `Pass`, `Partial`, or `Fail`.

| Area | Pass Standard |
|---|---|
| Prompt discipline | Prompts are structured, concise, tested on real cases, and revised after failure. |
| Repo analysis | You can name the owning layer for a number or defect quickly and correctly. |
| Change isolation | Reviews stay focused on one purpose and do not include unrelated changes. |
| Validation order | You check source and model logic before trusting front-end results. |
| Deployment awareness | You know the sequence for preflight, deploy, QC, and access handling. |
| Reviewer handoff | Reviewers get a direct path, explicit access, and clear expectations. |
| Reusability | Each week leaves behind at least one note, prompt, checklist, or evidence artifact that can be reused. |

If two or more areas score `Fail` in one week, repeat the same layer the following week instead of expanding scope.

## Readiness Gate For Codex

Do not move to Codex as your primary Pyramid tool until all of the following are true:

- you can complete one end-to-end workflow manually or with standard Copilot support
- your prompt templates are stable across several real cases
- you know where business logic lives and where it does not
- you can produce validation evidence without help
- you have delivered one reviewable change slice cleanly
- you have created one reusable team asset

## Best First Uses Of Codex

Once you clear the readiness gate, start with bounded tasks that accelerate existing workflows.

Good first uses:

- generating alternate QC queries for the same metric
- summarizing validation failures into a structured issue list
- drafting release notes, deployment notes, or handoff text
- comparing expected versus actual outputs across multiple checks
- turning repeated troubleshooting steps into a reusable runbook draft

Avoid using Codex first for:

- defining KPI business logic
- inventing migration or security policy
- redesigning deployment flow without manual experience
- masking gaps in metric lineage or data ownership

## Bottom Line

Pyramid readiness in a mature team is not measured by how quickly you can build a visual. It is measured by whether you can understand the model, validate the numbers, move the artifacts safely, and hand the result to a reviewer with confidence. Once that workflow is reliable, Codex becomes a multiplier instead of a crutch.