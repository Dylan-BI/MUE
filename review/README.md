# Third Party Review — MUE

> **Overarching Goal:** Assess whether the learner has become a confident, operationally reliable **Business Intelligence (BI) team contributor** who can analyze data, validate logic, deploy models, communicate and collaborate with the team, and hand off work cleanly — using Pyramid, Codex, BI judgment, and team collaboration skills.

## Purpose

This folder synchronizes completed work from `../action/` for independent reviewer assessment. It provides a clean, isolated view of what the learner has produced — without the working context, templates, or in-progress notes.

**No local repo required.** All reviewer interaction happens through GitHub.

---

## Standards Enforcement

Every review you submit should address a specific curriculum standard. The dashboard provides tools to ensure your feedback is structured, traceable, and actionable.

### Rating Rubric

| Rating | When to Use | What It Means |
|--------|-------------|---------------|
| **👍 Pass** | Learner meets the standard | Artifact demonstrates competency in the tagged category |
| **⚡ Needs Work** | Learner is close but not there | Specific improvement needed — describe what's missing |
| **❌ Rework** | Learner does not meet the standard | Must redo — fundamental gap in understanding or execution |

### Curriculum Categories (Tag Your Reviews)

Tag each review with the primary category it addresses:

| Tag | Category | What to Assess |
|-----|----------|----------------|
| 🤖 AI | AI & Copilot | Mode selection, prompt quality, instruction files, drift avoidance |
| ⚡ Codex | Codex Productivity | Codex Loop fluency, handoff quality, bounded automation |
| 🏗️ Pyramid | Pyramid Platform | Model logic, deployment sequence, QC evidence, access policy |
| 📊 BI | BI Judgment | Business question articulation, metric grain, validation evidence |
| 🔗 Data | Data & Lineage | Source-to-model tracing, row ownership, double-counting risk |
| 📦 Delivery | Delivery & Handoff | Change isolation, review packages, handoff quality |
| 💬 Team | Team Communication | Standup quality, status updates, blocker identification |
| 🧠 Retention | Retention & Readiness | Scorecard accuracy, proof task completeness, gate status |

### Progression Gates (What You're Enforcing)

| Gate | Criteria | Consequence if Failed |
|------|----------|----------------------|
| **Week 1 Gate** | 2+ scorecard areas score Fail | Repeat Week 1 before advancing |
| **Week 3 Gate** | 2+ scorecard areas score Fail | Repeat this layer in Week 4 instead of expanding |
| **Codex Gate** | All 6 Codex criteria must pass | Cannot advance to next level |
| **Classification** | Foundational → Developing → Operational → Ready | Must demonstrate increasing autonomy |
| **Proof Tasks** | PT1–PT6 due on specific days | Required for Codex Gate eligibility |

### Reviewer Guidelines

1. **Be specific** — reference the exact artifact, section, or behavior you're assessing
2. **Tag the category** — helps the learner understand which competency area needs attention
3. **Use the rubric** — consistent rating across reviewers ensures fair assessment
4. **Check scorecard trends** — if a category shows 2+ consecutive Fails, flag it as a progression gate concern
5. **Verify proof tasks** — PT1–PT6 have specific due days; late submission affects Codex Gate eligibility
6. **Monitor classification** — the learner's classification should advance as they demonstrate competency; if it stalls, investigate
7. **Submit daily** — the dashboard's daily summary email aggregates all reviews for the team; your input matters

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
| Reviewer submits via dashboard | Reviews sync to server in real-time | Review Server |
| Dashboard rebuilds | `build_data.py` reads `action/` + `review/` → `data.json` | Review Server |
| Daily summary | Aggregated reviews emailed to opted-in instructors | Review Server |

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
