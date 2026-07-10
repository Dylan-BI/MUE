# Education Actioning — MUE Daily Learner Workspace

> **Overarching Goal:** Become a confident, operationally reliable **Business Intelligence (BI) team contributor** who can analyze data, validate logic, deploy models, communicate and collaborate with the team, and hand off work cleanly — using Pyramid, Codex, BI judgment, and team collaboration skills.

## Purpose

This is where you do your daily work. All notes, evidence, reports, and templates live here. The training materials themselves are in `../source/` — you reference them but do not modify them.

## Quick Start

```bash
# 1. Create today's note (enforces day ≤ 28, weekday only)
python3 ../source/scripts/create_daily_note.py --date YYYY-MM-DD --day-number N

# 2. At end of week, aggregate notes
python3 ../source/scripts/aggregate_weekly.py --year YYYY --week WW

# 3. Generate readiness report
python3 ../source/scripts/generate_readiness_report.py              # latest week
python3 ../source/scripts/generate_readiness_report.py --full        # all notes
```

## Directory Layout

```
action/
├── README.md            # This file
├── notes/               # Daily notes (created by create_daily_note.py)
│   └── YYYY-MM-DD.md
├── evidence/            # Proof task artifacts, validation records
├── reports/             # Generated weekly reports
│   ├── weekly-YYYY-WW.md
│   └── readiness-YYYY-WW.md
├── archive/             # Completed learner work (moved from notes/evidence/reports)
│   ├── notes/
│   ├── evidence/
│   └── reports/
├── templates/           # Working templates (copy into your notes as needed)
│   ├── contributor-readiness-check.md
│   └── retention-review.md
├── proxy/               # Dummy learner proxy (simulates curriculum progression)
│   ├── run_proxy.py     # CLI entry point
│   ├── curriculum.py    # 28-day schedule data
│   ├── interface.py     # Abstract LearnerProxy contract
│   ├── dummy.py         # DummyLearner implementation
│   └── README.md        # Proxy documentation
└── dashboard/           # Dashboard UI and data builder
```

## Daily Workflow

1. **Read today's objective** from `../source/4-Week Onboarding Map.md`
2. **Reference source materials** in `../source/` as needed
3. **Create your daily note** using the script above
4. **Complete the day's tasks** and produce your evidence artifact
5. **Save artifacts** under `evidence/` with descriptive names
6. **Close out** with the end-of-day report in your note
7. **End of week** run reports and complete the scorecard

## Rules

- Do NOT modify files in `../source/` — that's the reference library
- Every day must produce at least one evidence artifact
- Day numbers must be 1–28 (script enforces this)
- Start each week with the retention review in `templates/retention-review.md`
- End week 4 with the contributor readiness check in `templates/contributor-readiness-check.md`

## When You're Done

Your completed work in `notes/`, `evidence/`, and `reports/` is what a reviewer will assess. Run the sync script from `../review/scripts/sync-from-action.py` to push your output to the review folder.
