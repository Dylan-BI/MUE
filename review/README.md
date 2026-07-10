# Third Party Review — MUE

> **Overarching Goal:** Assess whether the learner has become a confident, operationally reliable **Business Intelligence (BI) team contributor** who can analyze data, validate logic, deploy models, communicate and collaborate with the team, and hand off work cleanly — using Pyramid, Codex, BI judgment, and team collaboration skills.

## Purpose

This folder synchronizes completed work from `../action/` for independent reviewer assessment. It provides a clean, isolated view of what the learner has produced — without the working context, templates, or in-progress notes.

**No local repo required.** All reviewer interaction happens through GitHub.

---

## Quick Start for Reviewers

### 1. Open the Dashboard

**→ [MUE Dashboard on GitHub Pages](https://dylan-bi.github.io/MUE/dashboard.html)**

The dashboard shows all learner artifacts, progress, scorecards, and evidence — synced automatically from `action/`.

### 2. Review Learner Artifacts

Browse the dashboard to review:
- **Daily notes** — depth, retention, independence
- **Evidence artifacts** — proof task completeness
- **Reports** — scorecards, readiness summaries
- **Classification & Codex Gate** — progression status

### 3. Submit Feedback

Open a **GitHub Issue** using the [Reviewer Feedback template](../../issues/new?template=reviewer-feedback.md):

1. Go to **Issues → New Issue**
2. Select **Reviewer Feedback**
3. Fill in: learner name, week, rating, feedback
4. Submit

**That's it.** The feedback automatically syncs to the dashboard on the next deploy. No scripts, no local tools.

### 4. Check Status

After submitting, the feedback appears on the dashboard under the relevant artifact. Check the dashboard to confirm your review was captured.

---

## How Synchronization Works

| Step | What Happens | Where |
|------|-------------|-------|
| Learner pushes to `main` | GitHub Actions syncs `action/` → `review/` | GitHub Actions |
| Reviewer submits Issue | GitHub Actions parses feedback into `review/reviews.json` | GitHub Actions |
| Dashboard rebuilds | `build_data.py` reads `action/` + `review/` → `data.json` | GitHub Actions |
| Deploy to Pages | Dashboard updates at `dylan-bi.github.io/MUE/` | GitHub Pages |

**Reviewers never need to:**
- Clone the repo locally
- Run sync scripts
- Run build scripts
- Edit files directly

---

## Environment Requirements

Reviewers need only:
- **A web browser** — to access the GitHub Pages dashboard
- **A GitHub account** — to submit feedback via Issues
- **Repository read access** — to view the dashboard and issues

**For curriculum documentation:** The dashboard renders all formats (Markdown, text, JSON) in-browser. No special viewers needed.

If your environment is inadequate, submit a request using the [Environment Request template](../../issues/new?template=reviewer-environment-request.md).

---

## Directory Layout

```
review/
├── README.md              ← this file
├── reviews.json           ← reviewer feedback (auto-populated by GitHub Actions)
├── notes/                 ← synced from action/notes/
├── evidence/              ← synced from action/evidence/
├── reports/               ← synced from action/reports/
├── archive/               ← archived reviews
└── templates/
    └── reviewer-environment-check.md
```

## Notes

- The `review/` folder is a **synced snapshot** — populated automatically by GitHub Actions.
- Reviewer feedback flows through **GitHub Issues** — never edited directly in `review/reviews.json`.
- Do not modify files in `action/` — the reviewer's job is to assess, not to edit learner work.
- Local scripts (`sync-from-action.py`, `save-reviews.py`) exist for manual/local use but are not required for the standard reviewer workflow.
