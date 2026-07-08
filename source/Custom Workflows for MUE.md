# Custom Workflows for MUE

## Overview

This document adapts the earlier custom workflow ideas to the MUE learning environment. The focus is on practical workflows that support Pyramid work, Codex productivity, and BI judgment rather than generic Copilot use cases.

## Workflow 1: Repository Orientation and Analysis

### Purpose

Help a learner quickly understand a repository, a logic chain, or an unfamiliar BI workflow before making changes.

### Recommended prompt pattern

Use a prompt that asks for:

- business purpose
- dependency order
- key inputs and outputs
- likely risk areas
- safe first change or validation point

### Suggested prompt file

Create a prompt file such as `.vscode/copilot-prompts/repo-analysis.md` with guidance like:

```yaml
---
name: repo-analysis
description: Analyze a repository or logic chain for MUE readiness
---

# Repository Analysis

Explain the business purpose, dependency order, key inputs and outputs, and the safest place to begin analysis or change.
```

### When to use it

Use this workflow when:

- onboarding to a new repository
- tracing a metric or logic chain
- preparing for a review or handoff
- understanding where the next action should happen

## Workflow 2: Review and Validation Workflow

### Purpose

Use Copilot to support targeted review and validation rather than to define the business answer alone.

### Recommended steps

1. Identify the metric, report, or change being reviewed
2. Ask for the validation criteria and likely failure points
3. Review the evidence and compare it to expected behavior
4. Record the findings in a short review note or handoff

### Suggested prompt file

Create a prompt file such as `.vscode/copilot-prompts/validation-review.md`:

```yaml
---
name: validation-review
description: Review logic, validation evidence, and handoff readiness
---

# Validation Review

Summarize the current state, expected behavior, likely risk areas, and next action.
```

## Workflow 3: Handoff and Next-Step Workflow

### Purpose

Turn completed work into a useful handoff note for the next person or future session.

### Recommended output

A good handoff should include:

- current state
- what was completed
- what remains open
- next action
- any relevant context or reviewer note

This aligns directly with the Codex productivity track in MUE.

## Workflow 4: Daily Learning Workflow

### Purpose

Use Copilot to support a short-cycle learning routine with explicit outcomes.

### Daily pattern

Each session should answer:

- What are we learning today?
- What should be possible by tomorrow?
- What evidence shows progress?
- What is the next narrow action?

This helps keep learning practical and measurable.

## Workflow 5: Codex Handoff Fluency Workflow

### Purpose

Build automatic handoff reading and creation skills — the core Codex productivity metric.

### Recommended routine

**Reading (start of session):**
1. Open the most recent handoff note
2. Extract the 5 facts mentally: Current State, Completed, Remains, Next Action, Context
3. Verify against the actual note
4. If any fact is missing, flag it as a context gap

**Creation (end of session):**
1. Use the 5-section handoff template
2. Write Current State in one sentence
3. List Completed and Remains as bullets
4. Name one Next Action
5. Add Context (files, decisions, rationale)

### Performance expectation

Reading: <60 seconds per handoff. Creation: <2 minutes per session handoff.

## Workflow 6: Bounded Codex Workflow

### Purpose

Use Codex within explicit boundaries — accelerate execution without ceding business-logic decisions.

### Recommended steps

1. **Define the boundary:** Before prompting, decide what Codex should and should not do
2. **Write a bounded prompt:** Use "Do" and "Do NOT" clauses explicitly
3. **Execute:** Run the prompt within the bounds
4. **Validate:** Check that Codex respected the bounds
5. **Refine:** If bounds were breached, strengthen constraints
6. **Record:** Note which constraint patterns work for which task types

### Example bounded prompt

```
I need to validate the active-row filter logic in this model.
Do:
- Check whether the WHERE clause matches the expected business rule
- Highlight any rows that would be incorrectly included or excluded
Do NOT:
- Change the filter logic
- Suggest alternative business rules
If you cannot validate within these bounds, say "Out of scope" and explain why.
```

### When to use

Use this workflow when:
- validating logic without changing it
- reviewing evidence before forming a conclusion
- asking Codex to find inconsistencies without suggesting fixes
- checking work without letting Codex redefine the approach

## Workflow 7: Manual-vs-Codex Comparison Workflow

### Purpose

Build judgment about when Codex adds value and when it introduces risk.

### Recommended routine

1. Pick a defined, repeatable task
2. Do it manually — time yourself, note accuracy
3. Do it with Codex — time yourself, note accuracy
4. Compare across four dimensions: time, accuracy, understanding gained, risk of wrong answer
5. Write a one-paragraph decision: when will you use Codex for this task?

### Suggested comparison tasks

- Trace a KPI from source conditions to final rollup
- Validate a deployment preflight checklist
- Draft a handoff from raw session notes
- Review a change slice for completeness
- Classify a defect as data-quality vs. logic vs. presentation

## Practical MUE Use Cases

These workflows are especially useful for:

- preparing a repository analysis brief
- validating a KPI or metric lineage
- drafting a reviewer handoff
- documenting a deployment or QC check
- organizing the next step for a future session
- building handoff fluency (Workflow 5)
- keeping Codex within bounds (Workflow 6)
- evaluating when Codex helps vs. harms (Workflow 7)
