# Copilot Best Practices Guide

> **Category:** 🤖 AI & Copilot  
> **Source:** GitHub Copilot documentation, `github/docs`, `github/awesome-copilot` community patterns  
> **Weeks:** 1–4

---

## Overview

This guide consolidates proven patterns for using GitHub Copilot effectively across all four modes (Ask, Edit, Agent, Plan). It serves as a reference for learners developing prompt discipline and AI-assisted workflow habits.

---

## 1. Mode Selection

| Mode | Best For | When to Use |
|------|----------|-------------|
| **Ask** | Questions, explanations, code review, brainstorming | Understanding code, getting suggestions, learning concepts |
| **Edit** | Targeted code changes in the editor | Fixing a specific function, refactoring a narrow scope |
| **Agent** | Multi-step tasks, file creation, research | Building features end-to-end, diagnosing issues across files |
| **Plan** | Architecture decisions, design docs, implementation plans | Before starting complex work, reviewing approach |

**Key Principle:** Start with the simplest mode that can accomplish the task. Escalate to Agent/Plan only when the task crosses file boundaries or requires multiple steps.

---

## 2. Prompt Engineering Fundamentals

### Structure a Good Prompt

```
Context + Task + Format + Constraints
```

| Component | Example |
|-----------|---------|
| **Context** | "In this Python FastAPI app with SQLAlchemy..." |
| **Task** | "...add a GET endpoint for user profiles..." |
| **Format** | "...return JSON with id, name, email, and created_at." |
| **Constraints** | "...use async, include input validation, follow existing error patterns." |

### Prompt Anti-Patterns

| ❌ Anti-Pattern | ✅ Better Approach |
|----------------|-------------------|
| "Fix this" (no context) | "Fix the type error in `calculate_total()` — the `discount` param can be None" |
| "Write the whole app" | "Create the user auth module: register, login, token refresh endpoints" |
| Vague requirements | Explicit acceptance criteria + example inputs/outputs |
| Missing scope boundaries | "Only modify files in `src/api/`, don't touch tests" |

### Context Window Management

- Keep relevant files open in your editor — Copilot reads visible tabs
- Use `@workspace` to reference your whole codebase
- For large codebases, narrow with `@file` or `@folder` references
- Custom instructions (`.github/copilot-instructions.md`) persist context across sessions

---

## 3. Custom Instructions Strategy

### Repository-Level (`.github/copilot-instructions.md`)

```markdown
# Project Instructions

## Tech Stack
Python 3.14, FastAPI, SQLAlchemy, PostgreSQL

## Conventions
- Use async/await for all I/O operations
- Type hints required on all function signatures
- Follow existing error-handling patterns (custom exceptions → middleware)
- Tests use pytest with async fixtures
```

### Topic-Specific (`.github/instructions/<topic>.instructions.md`)

Create scoped instruction files with `applyTo` globs for monorepos:

```markdown
---
applyTo: "src/api/**"
---
# API Development Standards
- RESTful resource naming: plural nouns, kebab-case
- Version prefix: /api/v1/
- Response envelope: { data, meta, errors }
```

---

## 4. Agent Mode Best Practices

### When to Use Agent Mode

Agent mode excels at tasks that span multiple files or require research:

- **Feature implementation** — Create/modify multiple files with a single goal
- **Bug diagnosis** — Search logs, check types, trace execution paths
- **Refactoring** — Rename symbols, extract functions, restructure modules
- **Testing** — Generate test files covering happy path, edge cases, errors

### Agent Workflow Patterns

```
1. SETUP: Provide clear goal + acceptance criteria
2. PLAN: Let the agent propose an approach before coding
3. EXECUTE: Review each file change as it's made
4. VERIFY: Run tests / lint after each logical step
5. ITERATE: Refine via follow-up prompts
```

### Limits & Boundaries

- Agent mode has a context window — break very large tasks into phases
- Use `/plan` first for architecture-level decisions
- Review all file changes before accepting (use diff view)
- Set clear scope boundaries in your prompt to prevent scope creep

---

## 5. Prompt Patterns Library

### Pattern 1: Context Pull
```
@workspace Find all files that reference {concept} and summarize how
they connect. Focus on {specific concern}.
```

### Pattern 2: State Summary
```
Summarize the current state of {feature}: what's implemented, what's
pending, and what blockers exist. Reference specific files.
```

### Pattern 3: Validation Check
```
Review {file} for {concern}. List each issue with file:line.
Prioritize by severity.
```

### Pattern 4: Change Impact
```
I'm planning to {change}. What files would be affected?
What risks should I watch for?
```

### Pattern 5: Handoff Draft
```
Based on the work done in this session, draft a handoff note covering:
- What was accomplished
- What's still pending
- Key decisions made
- Next recommended step
```

---

## 6. Drift Avoidance

Copilot suggestions drift when context is unclear or ambiguous. Prevent drift by:

1. **Be specific** — Use exact function names, variable names, file paths
2. **Set scope** — "Only modify files in `src/`" prevents suggestions touching configs
3. **Use typing** — Type hints anchor Copilot's understanding of data structures
4. **Iterate** — If Copilot goes off-track, correct it immediately with a clarifying prompt
5. **Custom instructions** — Define patterns once in `.github/copilot-instructions.md`

---

## 7. Measuring Copilot Effectiveness

Track these metrics to assess AI-assisted productivity:

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Acceptance rate** | >30% | Copilot dashboard / telemetry |
| **Time to first suggestion** | <2s | IDE responsiveness |
| **Correction frequency** | Decreasing over time | Self-assessment per task |
| **Handoff quality** | Passes peer review | Rubric scoring |
| **Task completion time** | Trending down | Compare with/without AI |

---

## References

- [GitHub Copilot Best Practices](https://github.com/github/docs/tree/main/content/copilot) — Official documentation
- [Awesome GitHub Copilot](https://github.com/github/awesome-copilot) — Community instructions, agents, and skills
- [Prompt Engineering Guide](https://github.blog/2023-07-17-prompt-engineering-guide-generative-ai-llms/) — GitHub Blog
