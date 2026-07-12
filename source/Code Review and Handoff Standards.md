# Code Review and Handoff Standards

> **Category:** 📦 Delivery & Handoff  
> **Source:** `github/awesome-copilot` code review patterns, `github/gh-aw` handoff workflows, `github/codeql-coding-standards`  
> **Weeks:** 3–4

---

## Overview

This guide defines how learners should prepare review packages, conduct code reviews, and create handoff notes. These standards ensure that work can be assessed by third-party reviewers without requiring context recovery.

---

## 1. Change Isolation

### What Makes a Good Change Slice

A reviewable change slice must be:

- **Atomic** — Does one thing, does it completely
- **Scoped** — Affects a limited set of files
- **Independent** — Can be reviewed without understanding unrelated changes
- **Tested** — Includes or references evidence of correctness

### Change Slice Checklist

```
□ Single logical change (not "while I was here" fixes)
□ Fewer than 10 files changed (ideally <5)
□ No unrelated formatting/whitespace changes
□ Tests or validation evidence included
□ Follows project conventions
□ No debug code, commented code, or TODOs
```

---

## 2. Review Package Preparation

A review package is the complete set of materials a reviewer needs. Prepare it before submitting for review.

### Review Package Template

```markdown
## Review Package: {Title}

### Summary
{One paragraph describing what changed and why}

### Files Changed
| File | Change Type | Impact |
|------|-------------|--------|
| path/to/file.py | Modified | Core logic |
| path/to/test_file.py | Added | Test coverage |

### Acceptance Criteria
- [ ] Criterion 1 — How to verify
- [ ] Criterion 2 — How to verify

### Validation Evidence
- {Link to passing CI run}
- {Screenshot of expected behavior}
- {Test output summary}

### Reviewer Questions
- {Specific question for the reviewer}
- {Area where reviewer judgment is needed}

### Handoff Notes
{See handoff section below}
```

---

## 3. Code Review Standards

### What Reviewers Look For

| Area | What to Check | Common Issues |
|------|---------------|---------------|
| **Correctness** | Does the code do what it says? | Off-by-one, missing edge cases, wrong return type |
| **Clarity** | Is the intent obvious? | Magic numbers, unclear names, missing comments |
| **Maintainability** | Will this be easy to change? | Duplication, tight coupling, deep nesting |
| **Security** | Are there vulnerabilities? | Injection risks, unvalidated input, hardcoded secrets |
| **Performance** | Will this scale? | N+1 queries, unnecessary allocations, missing indexes |
| **Testing** | Is the behavior verified? | Missing edge cases, no error-path tests, low coverage |

### Review Checklist Template

```
## Code Review Checklist

### Structure
□ Does the code follow project structure conventions?
□ Are files organized logically?
□ Is the change scoped appropriately?

### Style
□ Follows language idioms and project style guide?
□ Naming is clear and consistent?
□ Comments explain WHY not what?

### Correctness
□ All acceptance criteria met?
□ Edge cases handled?
□ Error paths covered?

### Evidence
□ Tests pass?
□ Lint/type checks pass?
□ Manual verification described?

### Handoff
□ Handoff note written?
□ Next step identified?
□ Decisions documented?
```

---

## 4. Handoff Note Standards

### Handoff Note Template

Every handoff must include these 5 facts:

```markdown
# Handoff: {YYYY-MM-DD} — {Topic}

## 1. What Was Done
{Concrete description of completed work. Reference specific files and functions.}

## 2. Why It Was Done
{Business or technical rationale. Link to issue/PR if applicable.}

## 3. What's Pending
{List of remaining work, known issues, or follow-up tasks.}

## 4. Key Decisions
{Architecture decisions, trade-offs accepted, patterns established.}
- Decision: {what} → Rationale: {why}
- Decision: {what} → Rationale: {why}

## 5. Next Step
{Single, concrete, actionable next step. Include file path if relevant.}
```

### Handoff Timing

| When | Required? | Detail |
|------|-----------|--------|
| **End of session/day** | ✅ Required | Full handoff with all 5 facts |
| **After completing a task** | ✅ Required | At minimum: what was done + next step |
| **Before handoff to reviewer** | ✅ Required | Include review-specific questions |
| **Mid-task break** | ⚠️ Recommended | Brief state note (2-3 sentences) |

---

## 5. Pull Request Standards

### PR Description Template

```markdown
## Summary
{One-line summary of the change}

## Motivation
{Why this change is needed — link to issue}

## Changes
- {File}: {what changed and why}
- {File}: {what changed and why}

## Testing
- [ ] Unit tests added/passed
- [ ] Manual testing completed
- [ ] Edge cases verified

## Review Notes
- {Area where reviewer should focus}
- {Known limitations or risks}

Closes #{issue-number}
```

### PR Review Checklist

```
□ Description clearly states what and why
□ Change is scoped (not mixing unrelated fixes)
□ Tests are included and passing
□ CI passes
□ No debugging artifacts (console.log, print, breakpoints)
□ Documentation updated if needed
□ Handoff note filed in action/notes/
```

---

## 6. Reusable Asset Creation

Part of the Delivery & Handoff category includes creating assets that others can reuse.

### Asset Types

| Asset Type | Example | Criteria |
|------------|---------|----------|
| **Prompt templates** | Review prompt, test prompt | Parameterized, documented, tested |
| **Checklists** | Deployment checklist, review checklist | Actionable, complete, versioned |
| **Scripts** | Automation, validation | Tested, error-handled, documented |
| **Templates** | PR template, handoff template | Adopted by team, iterated |

### Asset Quality Rubric

| Criterion | Pass | Moderate | Fail |
|-----------|------|---------|------|
| **Documented** | Usage, inputs, outputs explained | Partial docs | No docs |
| **Tested** | Works in expected scenarios | Works in happy path | Not tested |
| **Reusable** | Parameterized, configurable | Hardcoded values | One-off |
| **Versioned** | Git history, changelog | In git but no changelog | Not versioned |

---

## References

- [Awesome Copilot Code Review](https://github.com/github/awesome-copilot) — Code review instructions and agents
- [CodeQL Coding Standards](https://github.com/github/codeql-coding-standards) — Code review checklist and development handbook
- [gh-aw Contributing Guide](https://github.com/github/gh-aw/blob/main/CONTRIBUTING.md) — PR handoff process, environment gates
- [Spec Kit PR Bridge](https://github.com/github/spec-kit) — Auto-generate PR descriptions from spec artifacts
