# Custom Workflows for PEU

## Overview

This document adapts the earlier custom workflow ideas to the PEU learning environment. The focus is on practical workflows that support Pyramid work, Codex productivity, and BI judgment rather than generic automation.

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
description: Analyze a repository or logic chain for PEU readiness
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

This aligns directly with the Codex productivity track in PEU.

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

## Practical PEU Use Cases

These workflows are especially useful for:

- preparing a repository analysis brief
- validating a KPI or metric lineage
- drafting a reviewer handoff
- documenting a deployment or QC check
- organizing the next step for a future session
