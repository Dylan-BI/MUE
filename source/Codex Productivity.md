# ⚡ Codex Productivity — Training Reference

> **Category:** ⚡ Codex Productivity  
> **Weeks Active:** 1–4  
> **Focus:** Workflow orientation, handoff fluency, context synthesis, targeted AI use, bounded automation

---

## Table of Contents

1. [The Codex Productivity Loop](#1-the-codex-productivity-loop)
2. [Handoff Fluency](#2-handoff-fluency)
3. [Context Synthesis](#3-context-synthesis)
4. [Prompt Patterns for Codex](#4-prompt-patterns-for-codex)
5. [Bounded Codex Use](#5-bounded-codex-use)
6. [Manual-vs-Codex Comparison](#6-manual-vs-codex-comparison)
7. [Codex Gate Preparation](#7-codex-gate-preparation)
8. [Codex Practice Exercises](#8-codex-practice-exercises)
9. [Quick Reference Cards](#9-quick-reference-cards)

---

## 1. The Codex Productivity Loop

Codex productivity follows a **five-step loop** that applies to nearly every task:

```
┌─────────────────────────────────────────────────────────┐
│                     CODEX LOOP                          │
│                                                         │
│  ① Pull Context → ② Summarize State → ③ Identify Next  │
│                                          ↓              │
│                  ⑤ Record Handoff ← ④ Execute          │
└─────────────────────────────────────────────────────────┘
```

### Step ① — Pull Context
**Goal:** Gather all relevant information before acting.

| Action | Prompt Pattern | Time Target |
|--------|---------------|-------------|
| Read current handoff | "Summarize the current state, completed work, and next action from this handoff." | <30s |
| Scan workspace | "What changed in this repo since the last commit? Summarize scope and risk." | <60s |
| Find relevant files | "Find files related to [metric/model/workflow]. Show their purpose and dependency order." | <60s |
| Check review status | "Are there open review comments or pending changes on this branch?" | <30s |

**Discipline:** Do not skip to Step ③ without completing Step ①. Context pulls should happen **automatically** at session start.

### Step ② — Summarize State
**Goal:** Express current state in one paragraph. If you cannot, you do not have enough context.

```
Current state should answer:
• What workflow am I in? (analysis, validation, deployment, review, handoff)
• What is the last known completed step?
• What is blocking or pending?
• What evidence or artifact exists so far?
```

**Check:** If your summary exceeds 3 sentences, refine. A good state summary is scannable in 5 seconds.

### Step ③ — Identify Next Action
**Goal:** Name the single next narrow action. Not the next five actions — the **one** thing that advances the workflow.

| Good | Poor |
|------|------|
| "Validate the active-row filter against the source WHERE clause." | "Complete the validation and deployment workflow." |
| "Draft the before/after note for the change slice." | "Finish the handoff package." |
| "Run `build_data.py` and inspect the output diff." | "Update the dashboard." |

**Rule:** If the next action takes longer than 25 minutes, it is not narrow enough. Break it down.

### Step ④ — Execute
**Goal:** Perform the work with Codex as a bounded assistant — not as the decision-maker.

- Use **Edit Mode** for narrow, scoped changes
- Use **Agent Mode** only after the workflow is clear and bounded
- Use **Ask Mode** for validation questions
- Use **Plan Mode** before multi-step tasks

### Step ⑤ — Record Handoff
**Goal:** Leave the next session (or reviewer) with everything they need.

A good handoff has exactly these sections:

```
# Handoff — YYYY-MM-DD

## Current State
[One paragraph — what is happening now]

## Completed
- [ ] What was finished this session

## Remains Open
- [ ] What still needs to be done
- [ ] Known blockers or questions

## Next Action
[Single narrow action — one sentence]

## Context
- Relevant files, links, or review references
- Decisions made and why
- Anything the next person needs to know
```

**Time Target:** A handoff should take <2 minutes to write. If it takes longer, you are including too much operational detail or not enough structure.

---

## 2. Handoff Fluency

Handoff fluency is the **most important Codex productivity skill**. A learner who can read, understand, and create handoffs efficiently can work across sessions, repos, and team members without repeating context.

### Reading a Handoff (Extraction)

When you open an existing handoff, extract these five facts **in order**:

| # | Fact | Question to Answer |
|---|------|-------------------|
| 1 | Current State | "What is happening right now?" |
| 2 | Completed Work | "What was just finished?" |
| 3 | Remaining Work | "What is still open?" |
| 4 | Next Action | "What should I do next?" |
| 5 | Context | "What files, decisions, or constraints matter?" |

**Fluency drill:** Read any handoff and recite these 5 facts from memory within 60 seconds. Repeat until automatic.

### Creating a Handoff (Drafting)

Use the **5-3-1 rule**:

- **5 minutes** of work → **1 sentence** handoff
- **25 minutes** of work → **3 sentences** handoff
- **Full session** → **5-section handoff** (as above)

### Handoff Quality Rubric

| Criterion | Pass | Fail |
|-----------|------|------|
| Current State | One clear sentence, not a list | Vague or missing |
| Completed | Bullet list of what was done | Assumes reader knows |
| Remains Open | Specific open items with context | "Nothing" when there are open items |
| Next Action | One narrow, doable action | Multiple actions or vague direction |
| Context | Files, decisions, rationale included | No context or assumed knowledge |

### Handoff Anti-Patterns

| Anti-Pattern | Fix |
|-------------|-----|
| "No blockers" when there are open questions | Name the question explicitly, even if unanswered |
| "Same as last session" | Always rewrite — state may have changed |
| "See the file" | Summarize the file's relevance in one line |
| Procedural blow-by-blow | Reduce to completed vs. remains-open; skip the step-by-step |
| No next action | Always include one, even if it is "Wait for review feedback" |

---

## 3. Context Synthesis

Context synthesis is the skill of **gathering the right amount of information before acting** — not too little (you guess) and not too much (you waste time).

### The 3-Question Context Pull

Before any Codex interaction, answer:

1. **What domain?** (Pyramid model, deployment, QC, review, handoff, analysis)
2. **What artifact?** (file, metric, workflow, dashboard, report, scorecard)
3. **What question?** (validate, explore, compare, draft, summarize, fix)

This keeps context narrow and targeted.

### Context Sources

| Source | What to Ask Codex |
|--------|------------------|
| Handoff note | Summarize state, next action, open items |
| Git diff | What changed, scope, risk |
| File content | Purpose, dependencies, key logic |
| Scorecard | Trend, areas needing attention |
| Proof task | Status, evidence, gaps |
| Review comments | Open threads, decisions, blockers |
| Error output | Type, location, likely cause |

### Handling Incomplete Context

When context is missing, **do not guess**. Use targeted prompts:

- "I need [specific fact] to proceed. Where can I find it?"
- "The handoff mentions [concept] but does not explain it. Can you infer from related files?"
- "I found [evidence] but it contradicts [assumption]. Which should I trust?"

**Rule:** If Codex cannot answer with confidence, flag it as a context gap and note it in the handoff. Do not let Codex invent missing context.

---

## 4. Prompt Patterns for Codex

These are reusable prompt templates for common Codex productivity tasks.

### Pattern 1 — Context Pull
```
I am starting a session on [workflow]. Find and summarize:
1. The most recent handoff note
2. Any open review comments or PR threads
3. The current git branch and recent changes
4. The relevant files for [metric/model]
Keep it under 3 sentences.
```

### Pattern 2 — State Summary
```
Summarize the current state of [workflow/metric/model].
Use this structure:
• Workflow:
• Last completed:
• Blockers:
• Next action:
```

### Pattern 3 — Handoff Draft
```
Draft a handoff note for this session.
Current work: [one sentence]
Completed: [what was done]
Remains: [what is open]
Next action: [the single next step]
Context: [files, decisions, reasoning]
```

### Pattern 4 — Validation Check
```
I am validating [metric/model/logic]. My expected behavior is [expectation].
The actual output is [actual].
Is there a logic error, data-quality issue, or presentation limitation?
Do NOT fix it — only classify the gap.
```

### Pattern 5 — Manual-vs-Codex Comparison
```
Compare the manual approach vs. Codex-assisted approach for [task].
Evaluate:
• Time taken (manual vs. assisted)
• Accuracy (did either make errors?)
• Understanding gained (did I learn by doing it manually?)
• Risk (did Codex introduce plausible-sounding wrong answers?)
```

### Pattern 6 — Change Impact
```
I changed [file/metric]. Before the change: [baseline]. After: [new state].
1. Does this change affect any downstream rollups or reports?
2. Is there any risk of double-counting or misalignment?
3. What validation should I run before marking complete?
```

### Pattern 7 — Bounded Codex Prompt
```
I need to [specific task]. Do:
• [allowed action 1]
• [allowed action 2]
Do NOT:
• [forbidden action 1]
• [forbidden action 2]
If you cannot do this within these bounds, say "Cannot complete within bounds" and explain why.
```

---

## 5. Bounded Codex Use

"Bounded Codex use" means Codex operates within **explicit constraints** — it accelerates execution but does not define business logic, make review decisions, or close open questions without human validation.

### The Bounded Codex Manifesto

| Codex CAN Do | Codex MUST NOT Do |
|-------------|-------------------|
| Pull and summarize context | Define or modify business logic |
| Draft handoff notes from your input | Decide whether something is correct |
| Highlight inconsistencies | Close a review thread |
| Suggest prompt improvements | Select metrics or grain without direction |
| Run validation checks you define | Interpret ambiguous requirements |
| Generate comparison templates | Declare a winner in manual-vs-Codex |
| Find relevant files | Decide which files to change |
| Restate your reasoning | Replace your reasoning |

### Bounded Codex Checklist

Before each Codex interaction:

- [ ] Have I defined the business question myself?
- [ ] Have I specified what Codex should and should not do?
- [ ] Am I validating the output, not accepting it?
- [ ] Would I catch a plausible-sounding wrong answer?
- [ ] Have I documented the decision, not just the result?

### When NOT to Use Codex

| Situation | Why |
|-----------|-----|
| Defining metric grain or filters | Business logic — must be human decision |
| Closing review comments | Reviewer accountability |
| Interpreting ambiguous stakeholder feedback | Requires human judgment |
| Making deployment decisions | Risk ownership |
| Choosing between competing interpretations | Context and domain knowledge |
| Writing business requirements | Must come from stakeholder interaction |

---

## 6. Manual-vs-Codex Comparison

The manual-vs-Codex comparison is a **required exercise** (Day 28). It trains the learner to evaluate when Codex helps and when it adds risk.

### Methodology

1. Pick a defined task (e.g., trace a KPI, validate a rollup, draft a handoff)
2. Do it **manually first** — time yourself, note difficulty
3. Do it **with Codex** — time yourself, note accuracy
4. Compare across four dimensions:

| Dimension | Manual | Codex-Assisted | Verdict |
|-----------|--------|----------------|---------|
| Time | | | |
| Accuracy | | | |
| Understanding Gained | | | |
| Risk of Wrong Answer | | | |

### Comparison Template

```
## Manual-vs-Codex Comparison

**Task:** [description]
**Date:** YYYY-MM-DD

### Manual Approach
- Time taken:
- Steps followed:
- Accuracy assessment:
- Understanding gained:

### Codex-Assisted Approach
- Time taken:
- Prompts used:
- Accuracy assessment (did Codex introduce errors?):
- Understanding gained (did I learn or just accept?):

### Evaluation
- Which approach was faster?
- Which approach was more accurate?
- Did Codex introduce plausible-sounding wrong answers?
- Would I trust the Codex result without manual validation?
- When would I use Codex for this task again?

### Decision
[ ] Use Codex for this task type in the future
[ ] Continue manual-only for this task type
[ ] Use Codex with bounded constraints (specify)
```

---

## 7. Codex Gate Preparation

The Codex Gate (Day 28) tests readiness for **bounded Codex use**. Each gate maps to Codex skills.

| Gate | Codex Skill Required | Practice Exercise |
|------|---------------------|-------------------|
| One end-to-end workflow completed | Handoff-to-execution loop | Exercise 1–6 |
| Business-logic ownership understood | Knowing when NOT to use Codex | Exercise 5 |
| Validation evidence without help | Bounded prompt design | Exercise 6 |
| All 6 proof tasks completed | Cross-category Codex use | All exercises |
| One clean reviewable change slice | Change impact analysis (Pattern 6) | Exercise 4 |
| One reusable team asset | Prompt pattern creation | Pattern 1–7 |

### Codex Gate Self-Assessment

Before the gate, answer:

1. **Can I use Codex to pull context without it inventing facts?**
   - Test: Give Codex an empty handoff and ask it to summarize. Does it say "No handoff found" or does it invent one?

2. **Can I keep Codex within bounds?**
   - Test: Ask Codex to "improve the metric definition." Does it change the business logic, or does it suggest presentation improvements?

3. **Can I detect plausible wrong answers?**
   - Test: Ask Codex a question about your own work where you already know the answer. Does it get it right?

4. **Can I produce a handoff without Codex?**
   - Test: Write a handoff manually. Then ask Codex to draft one from the same input. Compare completeness.

5. **Can I decide when NOT to use Codex?**
   - Test: List 3 situations where using Codex would be inappropriate for your current workflow.

---

## 8. Codex Practice Exercises

### Exercise 1: Handoff Reading (Week 1)
**Goal:** Read any handoff and extract the 5 facts in <60 seconds.

1. Open any handoff note from `action/evidence/` or create one
2. Set a timer for 60 seconds
3. Extract: Current State, Completed, Remains Open, Next Action, Context
4. Write them down from memory
5. Check against the actual handoff
6. Repeat with 3 different handoffs

**Pass:** 5/5 facts correct, all under 60 seconds

### Exercise 2: Context Pull (Week 2)
**Goal:** Use Codex to gather context without over-scoping.

1. Pick a workflow (e.g., "validate the active-row filter")
2. Write a context-pull prompt using Pattern 1
3. Run it
4. Evaluate: Did Codex pull relevant context? Did it go beyond scope?
5. Refine the prompt to be narrower
6. Compare first attempt vs. refined

**Pass:** Refined prompt produces relevant, scoped context in <3 sentences

### Exercise 3: State Summary (Week 2)
**Goal:** Summarize any workflow state in one paragraph.

1. Pick a workflow you worked on recently
2. Draft a state summary using Pattern 2
3. Check: Does it name workflow, last step, blockers, and next action?
4. Shorten to exactly 3 sentences without losing key facts
5. Ask someone else to read it — can they understand the state?

**Pass:** Summary is 3 sentences, contains all 4 elements, understood by another person

### Exercise 4: Handoff Creation (Week 3)
**Goal:** Create a handoff that passes the quality rubric.

1. Complete any 25-minute work session
2. Write a handoff using the 5-section template
3. Grade it against the Handoff Quality Rubric
4. If any criterion fails, rewrite that section
5. Save the handoff to `evidence/`

**Pass:** All 5 rubric criteria at Pass

### Exercise 5: Manual-vs-Codex Comparison (Week 4)
**Goal:** Evaluate when Codex helps vs. when it introduces risk.

1. Pick a defined task (e.g., trace a KPI lineage)
2. Do it manually — time yourself
3. Do it with Codex — time yourself
4. Fill out the Comparison Template
5. Write a one-paragraph decision: when will you use Codex for this task?

**Pass:** Comparison template fully filled, decision paragraph written, saved to `evidence/`

### Exercise 6: Bounded Codex Simulation (Week 4)
**Goal:** Keep Codex within explicit boundaries.

1. Pick a task where Codex might overreach (e.g., "review this metric definition")
2. Write a bounded prompt using Pattern 7
3. Include at least 2 "Do NOT" constraints
4. Run the prompt
5. Did Codex respect the bounds? If not, what constraint was missing?
6. Refine and retry
7. Write a note on what makes a constraint effective vs. ineffective

**Pass:** Codex respects bounds on first attempt, or refined prompt succeeds on second attempt

---

## 9. Quick Reference Cards

### Card 1: The Codex Loop
```
① Pull Context → ② Summarize State → ③ Identify Next → ④ Execute → ⑤ Record Handoff
```

### Card 2: Handoff Structure
```
# Handoff
## Current State
## Completed
## Remains Open
## Next Action
## Context
```

### Card 3: Bounded Codex Rules
```
✓ Pull context       ✗ Define business logic
✓ Draft from input   ✗ Make review decisions
✓ Highlight issues   ✗ Close open questions
✓ Suggest prompts    ✗ Select metrics/grain
```

### Card 4: 5-Fact Extraction
```
1. Current State — "What is happening now?"
2. Completed — "What was finished?"
3. Remaining — "What is still open?"
4. Next Action — "What should I do next?"
5. Context — "What files/decisions matter?"
```

### Card 5: Prompt Pattern Quick Pick
| When You Need… | Use Pattern… |
|----------------|-------------|
| Starting a session | 1 — Context Pull |
| Checking where you are | 2 — State Summary |
| Wrapping up | 3 — Handoff Draft |
| Checking your work | 4 — Validation Check |
| Evaluating Codex value | 5 — Manual-vs-Codex |
| Changing something | 6 — Change Impact |
| Keeping Codex in check | 7 — Bounded Prompt |

---

> **Next:** Practice Exercise 1 before Week 1 Day 2. Complete all exercises by Week 4 Day 28.
> **Reference:** Use these patterns alongside `Custom Workflows for MUE.md` and `Copilot Reference for MUE.md`.
