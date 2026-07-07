# MUE Learner Dashboard

An interactive static dashboard for tracking MUE (Multifaceted User Education) training progress.

## How it works

1. **Generate data** — After creating daily notes in `action/notes/`, run the build script:
   ```bash
   python action/dashboard/build_data.py
   ```
   This scans `action/notes/`, `action/evidence/`, and `action/reports/` and produces `action/dashboard/data.json`.

2. **View the dashboard** — Open `dashboard.html` in your browser.

## Deployment (GitHub Pages)

The dashboard auto-deploys to GitHub Pages via the included workflow (`.github/workflows/deploy-dashboard.yml`).

**One-time setup:**
1. Go to your repo **Settings → Pages**
2. Under **Source**, select **GitHub Actions**
3. The workflow will deploy on every push to `main` that touches the dashboard or action files

Once deployed, the dashboard is live at:
`https://dylan-bi.github.io/MUE/`

Double-click `dashboard.url` (Windows) to open it in your browser.

### Manual deployment

If you prefer not to use the workflow:
1. Run `python action/dashboard/build_data.py` to regenerate `data.json`
2. Upload the `action/dashboard/` folder to any static host
3. Open `dashboard.html` in your browser

## Files

| File | Purpose |
|------|---------|
| `dashboard.html` | Self-contained static HTML dashboard (7 pages) |
| `data.json` | Generated data file consumed by the HTML |
| `build_data.py` | Python script to regenerate `data.json` from notes |
| `dashboard.url` | Windows internet shortcut to the live dashboard |
| `README.md` | This file |

## Pages

- **📋 Overview** — Metrics, progress bar, track distribution chart
- **📅 Daily Progress** — Expandable day-by-day timeline
- **🏆 Scorecard** — Color-coded competency area scores
- **✅ Proof Tasks** — 6 proof task tracker
- **📁 Evidence** — Browse evidence artifacts by week
- **📈 Classification** — Readiness level trend chart
- **🚪 Codex Gate** — 6-gate pass/fail checklist

## Requirements

- Python 3.9+ for `build_data.py`
- Modern web browser for the HTML dashboard
