# Multifaceted User Education (MUE)

> **Overarching Goal:** Become a confident, operationally reliable **Business Intelligence (BI) team contributor** who can analyze data, validate logic, deploy models, communicate and collaborate with the team, and hand off work cleanly — using Pyramid, Codex, BI judgment, and team collaboration skills.

A **maximum 4-week** training bundle for Pyramid, Codex, BI judgment, and team collaboration readiness — with evidence-backed results, retention learning, and a **BI team contributor** outcome.

> **Hard constraint:** This program must not exceed 28 calendar days. See `source/CONTRIBUTING.md` for extension rules.

---

## Repository Structure

This repo is organized into three folders:

| Folder | Purpose |
|--------|---------|
| [`source/`](./source/) | **Source files** — training materials, reference documentation, and scripts (read-only) |
| [`action/`](./action/) | **Education actioning** — learner workspace for daily notes, evidence, reports, and templates |
| [`review/`](./review/) | **Third party review** — reviewer workspace synced from action/ for independent assessment |

---

## Quick Start — The 4-Week Path

**Start here.** Read [`source/4-Week Onboarding Map.md`](./source/4-Week%20Onboarding%20Map.md) for the full day-by-day plan.

| Week | Focus | Proof Tasks Due | Evidence |
|------|-------|-----------------|----------|
| **1** | Foundation — tracks, Copilot habits, team norms, baseline readiness | — | Readiness note, 3 prompts, dependency map, ops checklist, team norms note |
| **2** | Data foundation & model layer validation | PT1 (Repo Analysis), PT3 (Metric Lineage) | Source inventory, row ownership, hierarchy/measure notes, status updates |
| **3** | Snapshots, rollups, QC, deployment rehearsal, team sync | PT4 (QC Evidence), PT5 (Deployment Rehearsal) | QC pack, snapshot/rollup notes, preflight checklist, task breakdown |
| **4** | Contribution, handoff, team communication, reusable asset, Codex Gate | PT2 (Review Dry Run), PT6 (Handoff Test) | Change slice, handoff package, feedback log, reusable asset, readiness package |

---

## How the Three Folders Work Together

```
MUE/
├── source/                  # TRAINING MATERIALS (reference, read-only)
│   ├── 4-Week Onboarding Map.md
│   ├── Codex Productivity Training Handoff.md
│   ├── Copilot Reference for MUE.md
│   ├── Custom Workflows for MUE.md
│   ├── Pyramid, Codex, and BI Judgment Readiness Plan.md
│   ├── Pyramid, Codex, and BI Judgment Daily Execution Guide.txt
│   ├── Pyramid, Codex, and BI Judgment Daily Working Template.txt
│   ├── CONTRIBUTING.md
│   └── scripts/              # Utility scripts (operate on ../action/)
│       ├── create_daily_note.py
│       ├── aggregate_weekly.py
│       └── generate_readiness_report.py
│
├── action/                   # EDUCATION ACTIONING (learner workspace)
│   ├── README.md             # Learner quick-start
│   ├── notes/                # Daily notes (created by create_daily_note.py)
│   ├── evidence/             # Proof task artifacts, validation records
│   ├── reports/              # Generated weekly reports
│   └── templates/            # Working templates (retention-review, readiness-check)
│
├── review/                   # THIRD PARTY REVIEW (reviewer workspace)
│   ├── README.md             # Reviewer instructions
│   └── scripts/
│       └── sync-from-action.py  # Copies action/ output into review/
│
├── .github/                  # GitHub Actions + instructions
│   ├── workflows/weekly-aggregator.yml
│   └── instructions/mue-instructions.yml
│
└── README.md                 # This file
```

---

## For Learners — Daily Workflow

```bash
# 1. Read today's objective in source/4-Week Onboarding Map.md
# 2. Create today's note (enforces day ≤ 28)
python3 source/scripts/create_daily_note.py --date YYYY-MM-DD --day-number N

# 3. Work through the tasks, save evidence in action/evidence/
# 4. End of week: aggregate and generate reports
python3 source/scripts/aggregate_weekly.py --year YYYY --week WW
python3 source/scripts/generate_readiness_report.py
```

See [`action/README.md`](./action/README.md) for full learner instructions.

## For Reviewers

```bash
# Sync learner output into review/
python3 review/scripts/sync-from-action.py

# Then review the synced files in review/notes/, review/evidence/, review/reports/
```

See [`review/README.md`](./review/README.md) for full reviewer instructions.

---

## Retention Learning

Retention is built into the program via:
1. **Daily retention checks** — each day in the 4-Week Map includes a recall question from prior material
2. **Weekly retention review** — use `action/templates/retention-review.md` at the start of Weeks 2, 3, and 4
3. **Cumulative proof task tracking** — all 6 proof tasks must be complete before Codex Gate

---

## Standard Equipped Team Contributor

The end state is a contributor who can:

| Capability | Evidence |
|------------|----------|
| Understand dependency order source → reporting | Dependency map, lineage walkthrough |
| Validate model logic before trusting numbers | PT3 (Metric Lineage), PT4 (QC Evidence) |
| Move artifacts through environments correctly | PT5 (Deployment Rehearsal), ops checklist |
| Produce QC evidence with review entrypoint | PT4 (QC Evidence Pack) |
| Hand off work cleanly to reviewers | PT6 (Reviewer Handoff Test) |
| Use Codex to accelerate proven workflows | Codex Gate pass, manual-vs-Codex comparison |
| Apply BI judgment independent of tool | PT1 (Repo Analysis), PT2 (Review Dry Run) |
| Create reusable team assets | Published prompt library, checklist, or template |

See `action/templates/contributor-readiness-check.md` for the full certification checklist.

---

## Recommended Use Order

1. Read [`source/4-Week Onboarding Map.md`](./source/4-Week%20Onboarding%20Map.md) — get oriented
2. Read [`source/Codex Productivity Training Handoff.md`](./source/Codex%20Productivity%20Training%20Handoff.md) — understand the three-track intent
3. Read [`source/Copilot Reference for MUE.md`](./source/Copilot%20Reference%20for%20MUE.md) — learn Copilot habits
4. Use [`source/Custom Workflows for MUE.md`](./source/Custom%20Workflows%20for%20MUE.md) — build workflow patterns
5. Work through [`source/Pyramid, Codex, and BI Judgment Readiness Plan.md`](./source/Pyramid%2C%20Codex%2C%20and%20BI%20Judgment%20Readiness%20Plan.md) — detailed day-by-day
6. Use `source/Pyramid, Codex, and BI Judgment Daily Working Template.txt` — daily working sheet
7. Do your daily work in [`action/`](./action/) — notes, evidence, reports
8. Reviewers use [`review/`](./review/) for sync and assessment

## Sharing Notes

- This repo is self-contained. Clone and follow the 4-Week Onboarding Map.
- Learners work in `action/`. Reviewers use `review/`.
- Keep filenames stable so all remote users follow the same structure.
