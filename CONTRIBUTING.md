# Contributing to MUE (Multifaceted Learning)

Welcome — this repository is a training bundle and working kit for Pyramid, Codex, and BI judgment readiness. To keep learning practical, evidence-backed, and team-friendly, follow these contribution guidelines.

## Core rules
- Training programs using this content must be limited to a 4-week maximum (28 calendar days). Any extended program must be explicitly approved and documented in a team decision note.
- Every day of training must produce one evidence artifact (note, prompt, checklist, validation record, handoff draft, or reusable asset) and store it under `notes/` or `evidence/` (recommended layout below).
- Contributors must complete the minimum proof tasks or show equivalent evidence before making changes to production work.

## Repository layout for evidence
- `notes/YYYY-MM-DD.md` — daily note created from the Daily Working Template
- `evidence/YYYY-WW/` — weekly evidence collected and summarized
- `reports/` — aggregated weekly reports and readiness packages

## The template runs 60 days; we condense to 28

The Daily Working Template (`Pyramid, Codex, and BI Judgment Daily Working Template.txt`) describes a full 60-day program with Foundation (Days 1–5), Operational (Days 6–30), Contribution (Days 31–60), and an asset-creation phase.

For this 4-week bundle, we condense the original six proof tasks into four weeks:

- **Week 1**: Proof Task 1 (Repository Analysis Brief) + baseline readiness and prompts
- **Week 2**: Proof Task 3 (Metric Lineage Walkthrough) + start Proof Task 4 (QC Evidence)
- **Week 3**: Complete Proof Task 4 & Proof Task 5 (Deployment Rehearsal)
- **Week 4**: Proof Task 2 (Review Workflow Dry Run) & Proof Task 6 (Reviewer Handoff Test) and publish one reusable team asset

## Creating a daily note

Use the helper script `scripts/create_daily_note.py` to create a daily note from the template. The script enforces the 4-week limit if you pass `--day-number`.

Example:
```
python3 scripts/create_daily_note.py --date 2026-07-02 --day-number 5
```

This will create `notes/2026-07-02.md` containing the Daily Working Template and the provided day number. The script will refuse day numbers greater than 28.

## Gates before heavier Codex use
- Complete at least one end-to-end manual workflow and the proof tasks mapped above.
- Produce validation evidence without help.
- Create one reusable asset (prompt library, QC template, checklist, or handoff template).

## How to open a contribution / evidence PR
- Keep scope narrow. One PR per reviewable change slice or evidence collection (do not mix unrelated artifacts).
- Attach or link to the daily notes/evidence that support the change.
- Use the reviewer checklist: purpose, acceptance criteria, validation evidence, and exact entrypoint for review.

## Support and automation
- This repo includes helper scripts in `scripts/` to create daily notes and aggregate weekly evidence.
- A GitHub Actions workflow (`.github/workflows/weekly-aggregator.yml`) can compile weekly evidence into `reports/` automatically.

## Questions or exceptions
- If you need more than 4 weeks for a specific reason, open an issue describing the rationale and get explicit team sign-off.
