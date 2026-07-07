# Third Party Review — MUE

## Purpose

This folder synchronizes completed work from `../action/` for independent reviewer assessment. It provides a clean, isolated view of what the learner has produced — without the working context, templates, or in-progress notes.

## How It Works

The review folder is populated by running the sync script:

```bash
python3 review/scripts/sync-from-action.py
```

This copies the following from `action/` into `review/`:
- All completed daily notes (from `action/notes/`)
- All evidence artifacts (from `action/evidence/`)
- All generated reports (from `action/reports/`)
- The latest scorecard and readiness summary
- The contributor readiness check (if completed)

The sync script **does not** copy:
- Templates (these are working tools, not evidence)
- In-progress notes (only completed days)
- Empty directories

## Reviewer Workflow

1. **Run the sync** to get the latest learner output
2. **Review the readiness report** at `reports/readiness-YYYY-WW.md` for scores and progression
3. **Review evidence artifacts** in `evidence/` for proof task completeness
4. **Review daily notes** in `notes/` for depth, retention, and independence
5. **Complete the reviewer feedback** using the template below

## Reviewer Feedback Template

```markdown
# Review — {Learner Name} — Week {N}

## Readiness Classification
Current: {Foundational / Developing / Operational / Ready For Codex Acceleration}

## Scorecard
| Area | Score | Notes |
|------|-------|-------|
| Prompt discipline | Pass/Partial/Fail | |
| Repo/workspace analysis | Pass/Partial/Fail | |
| Change isolation | Pass/Partial/Fail | |
| Validation order | Pass/Partial/Fail | |
| Deployment awareness | Pass/Partial/Fail | |
| Reviewer handoff | Pass/Partial/Fail | |
| Reusability | Pass/Partial/Fail | |

## Proof Task Completion
- PT1: ✅ / ❌
- PT2: ✅ / ❌
- PT3: ✅ / ❌
- PT4: ✅ / ❌
- PT5: ✅ / ❌
- PT6: ✅ / ❌

## Observations
- Strengths:
- Areas for improvement:
- Retention demonstrated:
- Next week focus:

## Codex Gate
- All gates met: Yes / No
- Decision: Begin bounded Codex use / Stay with standard Copilot workflows
```

## Directory Layout After Sync

```
review/
├── README.md
├── scripts/
│   └── sync-from-action.py
├── notes/                # Synced from action/notes/
├── evidence/             # Synced from action/evidence/
├── reports/              # Synced from action/reports/
└── feedback/             # Reviewer feedback notes (created by reviewer)
```

## Notes

- The review folder is a **snapshot**, not a live workspace. Re-sync to get the latest.
- Reviewers should provide feedback in `review/feedback/` as markdown files.
- Do not modify files in `action/` — the reviewer's job is to assess, not to edit learner work.
