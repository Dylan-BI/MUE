# Agentic Workflow Patterns

> **Category:** ⚡ Codex Productivity  
> **Source:** `github/gh-aw` agentic workflow patterns, `github/spec-kit` SDD workflow model  
> **Weeks:** 1–4

---

## Overview

This guide defines the core workflow patterns that learners must master to work effectively with AI agents (Codex, Copilot, Claude) in real development and BI environments. These patterns are tool-agnostic — they apply whether you're using Codex, Copilot Agent mode, or any other AI coding assistant.

---

## 1. The Codex Loop

The fundamental pattern for AI-assisted work. This is the primary workflow learners practice throughout all 4 weeks.

```
┌─────────────────────────────────────────────────────────┐
│                    CODEX LOOP                            │
│                                                         │
│   PULL → SUMMARIZE → IDENTIFY → EXECUTE → RECORD       │
│    ↑                                        │           │
│    └────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────┘
```

| Step | Action | Output | Time Target |
|------|--------|--------|-------------|
| **Pull** | Gather context: open files, recent commits, issue/PR descriptions, active errors | Context snapshot | <30s |
| **Summarize** | Synthesize what's happening: current state, goal, blockers | Status summary (3 sentences) | <60s |
| **Identify** | Determine the next narrow action based on the summary | Clear next step | <30s |
| **Execute** | Perform the action using AI or manually | Working code/analysis | Varies |
| **Record** | Log what was done, why, and what's next for handoff | Handoff note | <120s |

### Exercise: Complete a Codex Loop <5 min

1. Open any active workspace
2. Pull context: `@workspace What's the current state of this project?`
3. Summarize in 3 sentences
4. Identify the next most impactful single action
5. Execute it (or plan it explicitly)
6. Write a handoff note in `action/notes/`

---

## 2. Handoff Extraction

A handoff is a structured note that lets another person (or your future self) pick up work without re-doing context discovery.

### 5-Fact Extraction

From any handoff note, PR description, or issue, extract these 5 facts in <60s:

| # | Fact | Example |
|---|------|---------|
| 1 | **What was done** | "Added user profile API with GET/PUT endpoints" |
| 2 | **Why it was done** | "Required for onboarding flow, needed by frontend team" |
| 3 | **What's pending** | "Email verification not yet implemented" |
| 4 | **Key decisions** | "Used SQLAlchemy async sessions, no cache layer yet" |
| 5 | **Next step** | "Wire up email service and add integration tests" |

### Handoff Quality Rubric

| Criterion | Pass | Moderate | Fail |
|-----------|------|---------|------|
| **Completeness** | All 5 facts present | 3-4 facts present | <3 facts |
| **Specificity** | References file names, function names | Vague references | No references |
| **Actionability** | Next step is concrete and scoped | Next step is vague | No next step |
| **Timeliness** | Written within 2 hours of work | Written within 1 day | Written >1 day later |

---

## 3. Context Pull (3-Question Method)

Before starting any AI-assisted task, answer these 3 questions:

1. **Where are we?** — What is the current state? (branch, file, error, commit)
2. **Where are we going?** — What is the specific goal? (acceptance criteria)
3. **What's in the way?** — What blockers or unknowns exist?

### Context Pull Prompt Templates

```
# Quick context pull
@workspace Summarize the state of {feature/file}. What's done, what's pending?

# Deep context pull
@workspace Find all references to {concept} and explain how they connect.
List each file with its role.

# Error context pull
I'm seeing {error}. What files are involved in this code path?
What could cause this?
```

---

## 4. Bounded Prompt Design

Effective AI work requires clear boundaries. Every prompt should have:

```
╔══════════════════════════════════════════════╗
║            BOUNDED PROMPT                    ║
║                                              ║
║  SCOPE:  "Only modify files in src/api/"     ║
║  TASK:   "Add input validation"              ║
║  STYLE:  "Follow existing error patterns"    ║
║  LIMIT:  "Don't touch database schema"       ║
╚══════════════════════════════════════════════╝
```

### Bounding Dimensions

| Dimension | Question to Answer |
|-----------|-------------------|
| **File scope** | Which files/directories are in bounds? Out of bounds? |
| **Task scope** | What exactly should be done? What should NOT be done? |
| **Style scope** | What conventions/must match? What's flexible? |
| **Review scope** | What needs human review before accepting? |

### Exercise: Bounded Prompt Design

1. Take a task: "Add a dark mode toggle to the dashboard"
2. Write an unbounded prompt: "Add dark mode"
3. Rewrite with all 4 bounding dimensions
4. Compare results — the bounded version will produce more focused output

---

## 5. Manual vs. Codex Evaluation

Knowing when to use AI vs. when to do it manually is a core skill.

### Decision Matrix

| Task Type | Use AI | Do Manually |
|-----------|--------|-------------|
| **Boilerplate code** | ✅ Generate | — |
| **Complex business logic** | — | ✅ Design first |
| **Repetitive edits** | ✅ Bulk refactor | — |
| **Debugging** | ✅ Assist with search | ✅ Own the diagnosis |
| **Code review** | ✅ Check for issues | ✅ Final judgment |
| **Architecture decisions** | — | ✅ Own the decision |
| **Documentation** | ✅ Draft | ✅ Review/refine |

### Manual-vs-Codex Exercise

For each task in a sprint:
1. Estimate time to do it manually
2. Estimate time with AI assistance
3. Note which parts AI handled well and which it didn't
4. Reflect: Would you delegate this task to AI again?

---

## 6. Workflow Specification (Spec → Plan → Implement → Validate)

Adapted from Spec Kit's SDD model, this pattern ensures structured delivery:

```
SPECIFY ──→ PLAN ──→ IMPLEMENT ──→ VALIDATE ──→ HANDOFF
   │          │           │             │            │
   └── What   └── How     └── Do        └── Check    └── Document
```

| Phase | Output | AI Role |
|-------|--------|---------|
| **Specify** | Acceptance criteria, scope, constraints | Draft spec from conversation |
| **Plan** | File list, approach, risks | Propose plan, identify gaps |
| **Implement** | Working code | Execute changes file-by-file |
| **Validate** | Tests pass, lint clean, review done | Run checks, flag issues |
| **Handoff** | Handoff note, PR description, change log | Draft handoff from session log |

---

## 7. Agentic Workflow Automation (gh-aw Patterns)

For advanced learners: GitHub's Agentic Workflows (`gh-aw`) enable persistent, multi-step automation.

### Common Patterns

| Pattern | Use Case | Key Feature |
|---------|----------|-------------|
| **Batch Ops** | Process many issues/PRs | List processing with parallel execution |
| **Work Queue Ops** | Sequential task processing | Issue checklist, cache memory, sub-issues |
| **Research → Plan → Assign** | Developer-supervised work | Research phase, plan review, then execute |
| **Pull Request Bridge** | Auto-generate PR content | PR descriptions, checklists, summaries from specs |

### Key Concepts

- **Safe outputs** — Controlled write capabilities (reply to review comments, dismiss reviews, create issues)
- **Cache memory** — Persistent state across workflow runs
- **MCP scripts** — Tool execution within workflows
- **Handoff artifacts** — Structured output between workflow steps

---

## References

- [gh-aw Agentic Workflows](https://github.com/github/gh-aw) — GitHub's agentic workflow engine
- [gh-aw Workflow Patterns](https://github.com/github/gh-aw/tree/main/docs/src/content/docs/patterns) — Batch ops, work queue ops, research-plan-assign
- [Spec Kit SDD](https://github.com/github/spec-kit) — Spec-driven development workflow model
- [gh-aw Glossary](https://github.com/github/gh-aw/tree/main/docs/src/content/docs/reference/glossary.md) — Handoff, safe outputs, cache memory definitions
