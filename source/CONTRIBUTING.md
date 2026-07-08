# Contributing to MUE (Multifaceted User Education)

> **7 Learning Categories** · 4-Week Program · Evidence-Backed Readiness

Welcome — this repository is a training bundle and working kit organized around **7 subject-material categories**: 🤖 AI & Copilot, ⚡ Codex Productivity, 🏗️ Pyramid Platform, 📊 BI Judgment, 🔗 Data & Lineage, 📦 Delivery & Handoff, and 🧠 Retention & Readiness.

See [`source/LEARNING_CATEGORIES.md`](./LEARNING_CATEGORIES.md) for the complete category reference.

## Core rules
- Training programs using this content must be limited to a **4-week maximum (28 calendar days)**. Any extended program must be explicitly approved and documented in a team decision note.
- Every day of training must produce **one evidence artifact** (note, prompt, checklist, validation record, handoff draft, or reusable asset) and store it under `action/notes/` or `action/evidence/`.
- Every daily task should be **tagged with its primary category** (🤖 ⚡ 🏗️ 📊 🔗 📦 🧠).
- Contributors must complete all 6 proof tasks (or show equivalent evidence) before making changes to production work.
- Start each week with the retention review in `action/templates/retention-review.md`.
- End the program with the contributor readiness check in `action/templates/contributor-readiness-check.md`.

## Repository layout

```
MUE/
├── source/                   # TRAINING MATERIALS (reference — read-only)
│   ├── LEARNING_CATEGORIES.md    🧠  Master category reference
│   ├── 4-Week Onboarding Map.md  🧠  Daily/weekly plan with category tags
│   ├── Copilot Reference.md      🤖  AI modes, prompts, context
│   ├── Custom Workflows.md       ⚡📦  Workflow patterns
│   ├── Codex Productivity.md     ⚡📊  Codex productivity vision
│   ├── Readiness Plan.md         🏗️📊⚡  Full readiness plan
│   ├── Daily Execution Guide.txt 🏗️  60-day reference
│   ├── Daily Working Template.txt🧠  Daily work blocks
│   ├── CONTRIBUTING.md           🧠  This file
│   └── scripts/                  🧠  Utility scripts
├── action/                   # EDUCATION ACTIONING (learner workspace)
│   ├── notes/                # Daily notes (YYYY-MM-DD.md)
│   ├── evidence/             # Proof task artifacts, validation records
│   ├── reports/              # Aggregated reports and readiness summaries
│   │   ├── weekly-YYYY-WW.md
│   │   └── readiness-YYYY-WW.md
│   ├── templates/            # 🧠 Reusable templates
│   │   ├── retention-review.md
│   │   └── contributor-readiness-check.md
│   └── dashboard/            # 🧠 Third-party review dashboard
├── review/                   # THIRD PARTY REVIEW (reviewer workspace)
│   ├── scripts/
│   │   └── sync-from-action.py
│   └── (synced from action/)
└── README.md                 # Root overview
```

## The 60-day guide condensed to 28 days with category tags

The original Execution Guide (`source/Pyramid, Codex, and BI Judgment Daily Execution Guide.txt`) describes a full 60-day program. The [`source/4-Week Onboarding Map.md`](./4-Week%20Onboarding%20Map.md) condenses this into a **4-week (28-day) schedule** with explicit **category tagging**:

- **Week 1** (Days 1–5): 🏗️ Foundation — 🤖 AI · 📊 BI · 🏗️ Pyr
- **Week 2** (Days 6–12): 🔗 Data Layer — 🔗 Data · 📊 BI · ⚡ Codex — PT1 + PT3 due
- **Week 3** (Days 13–19): ⚡ Operations — 🏗️ Pyr · ⚡ Codex · 📦 Del — PT4 + PT5 due
- **Week 4** (Days 20–28): 📦 Contribution — 📦 Del · ⚡ Codex · 🧠 Ret — PT2 + PT6 due

### Proof Task Schedule (with category mapping)

| Proof Task | Week | Categories | Days |
|---|---|---|---|
| PT1: Repository Analysis Brief | 2 | ⚡ Codex · 🧠 Ret | Day 9 |
| PT2: Review Workflow Dry Run | 4 | ⚡ Codex · 📦 Del | Day 21 |
| PT3: Metric Lineage Walkthrough | 2–3 | 📊 BI · 🔗 Data | Days 12–13 |
| PT4: QC Evidence Pack | 3 | ⚡ Codex · 🧠 Ret | Days 15–16 |
| PT5: Deployment Rehearsal | 3 | 🏗️ Pyr · 🧠 Ret | Days 17–18 |
| PT6: Reviewer Handoff Test | 4 | 📦 Del · 🧠 Ret | Day 21 |

> **Important:** Use the `source/4-Week Onboarding Map.md` for day-by-day scheduling. The original 60-day Execution Guide is a reference for detail; do not use it to extend the program.

## Creating a daily note

Use the helper script `source/scripts/create_daily_note.py` to create a daily note from the template. The script enforces the 4-week limit.

```bash
# From repo root:
python3 source/scripts/create_daily_note.py --date YYYY-MM-DD --day-number N
```

This creates `action/notes/YYYY-MM-DD.md` containing the Daily Working Template. The script refuses day numbers > 28.

## Generating readiness reports

After each week (or at any time), generate a structured readiness report:

```bash
# From repo root:
python3 source/scripts/generate_readiness_report.py              # latest week
python3 source/scripts/generate_readiness_report.py --year YYYY --week WW
python3 source/scripts/generate_readiness_report.py --full       # all notes
```

The report extracts: classification progression, primary track, scorecard scores, evidence artifacts, Codex Gate status, and proof task completion. Reports are written to `action/reports/`.

## Retention learning

To ensure retention across the 4 weeks:

1. **Daily retention checks** — built into each day of the 4-Week Onboarding Map
2. **Weekly retention review** — use `action/templates/retention-review.md` at the start of Weeks 2, 3, and 4
3. **Cumulative proof task tracking** — all 6 PTs must be complete before passing the Codex Gate

## Gates before heavier Codex use

All of the following must be true before using Codex as a primary tool:

- Complete at least one end-to-end manual workflow and all 6 proof tasks.
- Produce validation evidence without help.
- Create one reusable asset (prompt library, QC template, checklist, or handoff template).
- Pass the Codex Gate check (all 6 gates = Yes).

## How to open a contribution / evidence PR
- Keep scope narrow. One PR per reviewable change slice or evidence collection (do not mix unrelated artifacts).
- Attach or link to the daily notes/evidence that support the change (from `action/`).
- Use the reviewer checklist: purpose, acceptance criteria, validation evidence, and exact entrypoint for review.
- Include the latest readiness report from `action/reports/readiness-YYYY-WW.md`.

## Support and automation
- `source/scripts/create_daily_note.py` — creates daily notes (enforces day ≤ 28)
- `source/scripts/aggregate_weekly.py` — concatenates weekly notes into action/reports/
- `source/scripts/generate_readiness_report.py` — parses notes into structured readiness reports
- `review/scripts/sync-from-action.py` — syncs action/ output into review/ for third-party assessment
- `.github/workflows/weekly-aggregator.yml` — auto-generates weekly reports + syncs to review/

## Questions or exceptions
- If you need more than 4 weeks for a specific reason, open an issue describing the rationale and get explicit team sign-off.
