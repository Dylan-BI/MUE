# Pyramid, Codex, and BI Judgment Readiness Plan

## Overview

> **Overarching Goal:** Become a confident, operationally reliable **Business Intelligence (BI) team contributor** who can analyze data, validate logic, deploy models, communicate and collaborate with the team, and hand off work cleanly — using Pyramid, Codex, BI judgment, and team collaboration skills.

This module lays out a practical improvement path for becoming a reliable **BI team contributor** who can operate inside a mature analytics organization. The plan is intentionally broader than dashboard building. In this workspace, Pyramid work sits inside a larger delivery model that includes prompt discipline, repository analysis, change isolation, source validation, deployment sequencing, QC, security awareness, and reviewer handoff.

This plan is organized across three complementary tracks, reinforced by a fourth cross-cutting skill:
- Pyramid training for platform-specific modeling, deployment, and reviewer-ready delivery.
- Codex productivity training for workflow orientation, context synthesis, handoff fluency, and targeted follow-up.
- BI judgment training for tool-agnostic reasoning about business questions, metrics, grain, validation evidence, and trusted delivery.
- 💬 Team communication and task management — practised in parallel with all three tracks, covering standups, status updates, task tracking, feedback, blocker escalation, and collaborative workflows.

This plan is intended to be used as a four-week learning cycle. In week 1, the learner establishes the frame and the Copilot habits. In week 2, the learner practices reusable workflows. In week 3, the learner applies the readiness model in a more structured way. In week 4, the learner uses daily execution and reflection to build fluency.

### Four-Week Structure With Day-By-Day Goals

- Week 1: Learn the structure, the three tracks, and the basic Copilot habits. Each day should produce one small artifact such as a note, prompt, handoff draft, or summary.
- Week 2: Practice repository orientation, review behavior, and handoff drafting. Each day should answer: what did I learn, what should I be able to do tomorrow, and what evidence did I produce?
- Week 3: Apply the readiness model to a real or sample work item. Each day should include one concrete validation or review activity and one short report of findings.
- Week 4: Convert the plan into a repeatable daily rhythm. Each day should close with a short report that captures the outcome, the next action, and the evidence that supports the result.

### Daily and Weekly Reporting Standard

Each day should end with a short report covering:
- What I learned today
- What I should be able to do tomorrow
- What evidence I produced
- What remains open

Each week should end with a short review covering:
- What improved this week
- What still needs more practice
- Which track advanced the most
- What the next week should focus on

### How to use the tracks

- Use Pyramid training when the work is about Pyramid platform mechanics, artifact movement, model logic, deployment, or reviewer access.
- Use Codex productivity training when the work is about pulling context, summarizing current state, identifying next steps, creating handoffs, or asking targeted clarification questions.
- Use BI judgment training when the work is about defining business questions, choosing the right metric, understanding grain and exclusions, selecting the right output, or producing evidence a reviewer needs.

Each day should be tagged with the primary track it advances, and each unit should use short-cycle outcomes.

The goal is to become operationally reliable before using Codex as a force multiplier. That means learning the workflow well enough to explain it, validate it, and hand it off cleanly without depending on AI to invent the missing logic.

## Target Outcome — BI Team Contributor

**By the end of this plan, you should be a reliable BI team contributor who can:**

- explain the dependency order from source loads to reporting outputs
- create reliable prompts for analysis, validation, and review tasks
- validate model logic before trusting front-end numbers
- move Pyramid artifacts through an environment with the right connections, access, and reviewer path
- provide QC evidence with a direct review entrypoint
- use Codex to speed up proven workflows instead of replacing understanding
- orient work quickly with Codex, summarize current state, identify next actions, and hand off progress clearly
- apply BI judgment to decide what business question is being answered, what metrics are appropriate, and what evidence a reviewer needs to trust the output
- **communicate effectively with the team:** give clear standup updates, escalate blockers promptly, share findings with peers, and participate in team discussions
- **manage tasks within a team context:** break work into assignable units, track progress on a shared board, prioritise across competing demands, and incorporate feedback constructively

## How This Plan Is Structured

Each learning unit is intentionally short and outcome-focused. Use this format across daily and weekly work:

- Today we are learning this.
- By tomorrow, the learner should be able to do this.
- This is the acceptance criteria.
- This week the goal is this.
- This week the acceptance criteria is this.
- At this point in time, the acceptance criteria will be measured.

Each day should also be tagged with the primary track it advances: Pyramid operations, Codex productivity, or BI judgment.

## Operating Principles

1. Learn the manual workflow first.
2. Use AI to compress repetitive work, not to define business truth.
3. Validate from the lowest dependency layer upward.
4. Keep changes narrow enough for fast review.
5. Treat deployment, access, and reviewer handoff as part of delivery.
6. Leave behind reusable prompts, checklists, or runbooks.
7. Treat Pyramid as one useful platform context, Codex as a bounded accelerator, and BI judgment as the core decision layer.
8. Learn to separate platform mechanics from business reasoning.
9. **Communicate early and often.** Share progress, blockers, and findings with your team before they ask. A 30-second standup update saves an hour of context recovery.
10. **Track your work in the open.** Use task tracking tools (GitHub Issues, project boards) so your team knows what you're working on and what's coming next.
11. **Treat feedback as data, not criticism.** When receiving feedback, listen first, ask clarifying questions, then decide what to act on. When giving feedback, be specific and actionable.

## Day-By-Day Plan

The first five working days should build a stable foundation.

| Day | Track | Today we are learning | Tomorrow you should be able to do | Acceptance criteria | Measurement point |
|---|---|---|---|---|---|
| 1 | Codex productivity | Learn when to use Ask, Edit, Agent, and Plan modes, and how to write structured prompts. | Write a baseline note explaining mode choice, prompt structure, context limits, and why prompt bloat causes drift. | A one-page readiness note exists and explains each mode, prompt structure, and context limits in your own words. | End of day |
| 2 | Codex productivity | Build reusable prompts for repository analysis, model validation, and deployment or QC review. | Create and test three working prompt templates on real material. | Three reusable prompts exist with notes describing the first failure and the revision made. | End of day |
| 3 | BI judgment | Practice narrow-scope review behavior and change isolation. | Isolate one reviewable change slice and draft a focused review request. | A clean review draft includes purpose, audience, review focus, and reviewer questions. | End of day |
| 4 | Pyramid operations | Trace the BI model lineage from source load through transformation, snapshot, and rollup logic. | Create a dependency map that starts at the data source and ends at QC. | A one-page map names load, transformation, snapshot, rollup, and QC layers. | End of day |
| 5 | Pyramid operations | Build an operations checklist for deployment, migration, security, and reviewer access. | Produce a deployment and handoff checklist another developer can follow. | The checklist covers connection setup, model migration, reporting artifact migration, security setup, reviewer access, rerun steps, and preview entrypoints. | End of day |

## Week-By-Week Plan

After the first week, the next month should focus on repeated operational reps.

### Week 2: Validate The Data Foundation

This week the goal is to confirm the source and row-level foundation for reporting.

This week the acceptance criteria is that you can name the ownership of row selection, deduplication, and aggregation without opening the front end.

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

This week the goal is to verify the business model structure and active-row logic behind the metrics.

This week the acceptance criteria is that you can explain who owns each model layer and where active/inactive row decisions are made.

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

This week the goal is to confirm the behavior of current and previous snapshots and the transition from granular outputs to summaries.

This week the acceptance criteria is that you can explain whether an issue belongs to source data, transformation logic, snapshot logic, rollup logic, or presentation.

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