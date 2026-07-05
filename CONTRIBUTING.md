# Contributing to MUE (Multifaceted User Education)

Welcome — this repository is a training bundle and working kit for Pyramid, Codex, and BI judgment readiness. To keep learning practical, evidence-backed, and team-friendly, follow these contribution guidelines.

## Core rules
- Training programs using this content must be limited to a **4-week maximum (28 calendar days)**. Any extended program must be explicitly approved and documented in a team decision note.
- Every day of training must produce **one evidence artifact** (note, prompt, checklist, validation record, handoff draft, or reusable asset) and store it under `notes/` or `evidence/`.
- Contributors must complete all 6 proof tasks (or show equivalent evidence) before making changes to production work.
- Start each week with the retention review in `templates/retention-review.md`.
- End the program with the contributor readiness check in `templates/contributor-readiness-check.md`.

## Repository layout for evidence
```
notes/                   # Daily notes (created by create_daily_note.py)
  YYYY-MM-DD.md
evidence/                # Proof task artifacts, validation records
  YYYY-WW/               # Weekly evidence collections
reports/                 # Aggregated reports and readiness summaries
  weekly-YYYY-WW.md      # Concatenated weekly notes
  readiness-YYYY-WW.md   # Structured readiness report (from generate_readiness_report.py)
templates/               # Reusable templates
  retention-review.md
  contributor-readiness-check.md
```

## The 60-day guide condensed to 28 days

The original Execution Guide (`Pyramid, Codex, and BI Judgment Daily Execution Guide.txt`) describes a full 60-day program. The [`4-Week Onboarding Map.md`](./4-Week%20Onboarding%20Map.md) condenses this into a **4-week (28-day) schedule** with:

- **Week 1** (Days 1–5): Foundation — tracks, Copilot habits, baseline readiness
- **Week 2** (Days 6–12): Data foundation & model layer — PT1 + PT3 due
- **Week 3** (Days 13–19): Snapshots, rollups, QC, deployment — PT4 + PT5 due
- **Week 4** (Days 20–28): Contribution, handoff, asset creation, Codex Gate — PT2 + PT6 due

### Proof Task Schedule (aligned to the 4-Week Map)

| Proof Task | Week Due | Days |
|---|---|---|
| PT1: Repository Analysis Brief | Week 2 | Day 9 |
| PT2: Review Workflow Dry Run | Week 4 | Day 21 |
| PT3: Metric Lineage Walkthrough | Week 2–3 | Days 12–13 |
| PT4: QC Evidence Pack | Week 3 | Days 15–16 |
| PT5: Deployment Rehearsal | Week 3 | Days 17–18 |
| PT6: Reviewer Handoff Test | Week 4 | Day 21 |

> **Important:** Use the `4-Week Onboarding Map.md` for day-by-day scheduling. The original 60-day Execution Guide is a reference for detail; do not use it to extend the program.

## Creating a daily note

Use the helper script `scripts/create_daily_note.py` to create a daily note from the template. The script enforces the 4-week limit.

```bash
python3 scripts/create_daily_note.py --date YYYY-MM-DD --day-number N
```

This creates `notes/YYYY-MM-DD.md` containing the Daily Working Template. The script refuses day numbers > 28.

## Generating readiness reports

After each week (or at any time), generate a structured readiness report:

```bash
# Latest week
python3 scripts/generate_readiness_report.py

# Specific week
python3 scripts/generate_readiness_report.py --year YYYY --week WW

# Full cumulative report
python3 scripts/generate_readiness_report.py --full
```

The report extracts: classification progression, primary track, scorecard scores, evidence artifacts, Codex Gate status, and proof task completion.

## Retention learning

To ensure retention across the 4 weeks:

1. **Daily retention checks** — built into each day of the 4-Week Onboarding Map
2. **Weekly retention review** — use `templates/retention-review.md` at the start of Weeks 2, 3, and 4
3. **Cumulative proof task tracking** — all 6 PTs must be complete before passing the Codex Gate

## Gates before heavier Codex use

All of the following must be true before using Codex as a primary tool:

- Complete at least one end-to-end manual workflow and all 6 proof tasks.
- Produce validation evidence without help.
- Create one reusable asset (prompt library, QC template, checklist, or handoff template).
- Pass the Codex Gate check (all 6 gates = Yes).

## How to open a contribution / evidence PR
- Keep scope narrow. One PR per reviewable change slice or evidence collection (do not mix unrelated artifacts).
- Attach or link to the daily notes/evidence that support the change.
- Use the reviewer checklist: purpose, acceptance criteria, validation evidence, and exact entrypoint for review.
- Include the latest readiness report from `reports/readiness-YYYY-WW.md`.

## Support and automation
- `scripts/create_daily_note.py` — creates daily notes (enforces day ≤ 28)
- `scripts/aggregate_weekly.py` — concatenates weekly notes into reports/
- `scripts/generate_readiness_report.py` — parses notes into structured readiness reports with scorecards
- `.github/workflows/weekly-aggregator.yml` — auto-generates weekly reports via GitHub Actions

## Questions or exceptions
- If you need more than 4 weeks for a specific reason, open an issue describing the rationale and get explicit team sign-off.
