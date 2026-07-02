# Copilot Reference for MUE

## Overview

This guide brings the core Copilot concepts from the earlier AI workflow modules into the MUE learning context. The goal is not to treat Copilot as a replacement for business understanding, but as a tool that can accelerate learning and handoff workflows when used within a clear frame.

Use this document alongside the readiness plan when you want a quick reminder of how Copilot features should be used in real training and delivery work.

## How This Fits the MUE Plan

The MUE plan is organized around three tracks:

- Pyramid training for platform-specific understanding and delivery
- Codex productivity for workflow orientation, context synthesis, and handoffs
- BI judgment for business reasoning, metric understanding, and reviewer trust

Copilot is most useful when it supports those tracks without replacing the learner's own judgment.

## Chat Modes

Use the right mode for the task:

- Ask Mode: best for learning, explaining concepts, and asking targeted questions
- Edit Mode: best for small, explicit changes to a file or snippet
- Agent Mode: best for multi-step tasks that require several file or workspace actions
- Plan Mode: best for mapping a workflow before acting on it

### MUE guidance

- Use Ask Mode first when you are learning a model, a metric, or a workflow
- Use Edit Mode when you need a narrowly-scoped change
- Use Plan Mode before a larger review, deployment, or analysis task
- Use Agent Mode only after the workflow is well understood and the scope is clear

## Custom Instructions

Custom instructions help Copilot apply the same standards every time. They are useful for keeping work aligned with MUE expectations such as:

- explain the business purpose before the technical detail
- validate logic before trusting the output
- keep changes narrow and reviewable
- leave behind a handoff note or evidence record

### Recommended setup

Create instruction files in:

- .github/instructions/ for team-wide guidance
- .vscode/instructions/ for local or project-specific guidance

Example guidance:

```yaml
---
applyTo: '**'
---

# MUE Working Standards
- Explain the business question before the technical detail.
- Validate the logic before trusting the output.
- Keep changes narrow and reviewable.
- Leave behind a handoff note or evidence artifact.
```

## Prompt Files

Prompt files are useful for repeated MUE workflows such as:

- repository analysis
- validation review
- handoff drafting
- deployment readiness review

A simple prompt file can save time and improve consistency across sessions.

### Suggested prompt files

- repo-analysis.md for understanding a workspace or logic chain
- validation-review.md for checking numbers, dependencies, and assumptions
- handoff-draft.md for turning a completed task into a useful next-step note

## Tools and Extensions

Useful tools in this context include:

- GitHub Copilot Chat
- GitHub PR and review support
- terminal and workspace integration
- database or data-inspection extensions when relevant

Use tools to accelerate repeatable tasks, not to shortcut understanding.

## Context Management

Good context leads to better answers. In MUE work, include:

- the relevant file or selection
- the business question being asked
- the current work state or handoff note
- any known constraints, review expectations, or acceptance criteria

Use targeted context such as:

- #file for a specific file
- #selection for a scoped section
- #codebase when you need broader repository orientation

## Practical MUE Checklist

Before using Copilot on a real task, confirm:

1. What business question is being answered?
2. What track is this task advancing: Pyramid, Codex productivity, or BI judgment?
3. What evidence or artifact should be produced by the end of the task?
4. What does the learner need to understand without relying on Copilot?

## Quick Start

A good MUE workflow is:

1. Start with Ask Mode to frame the question and gather context
2. Use Plan Mode if the task is larger or involves multiple steps
3. Use Edit Mode for narrow changes
4. Record the answer, decision, or handoff artifact before closing the session
