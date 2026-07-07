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

The dashboard is designed to be served via **GitHub Pages**.

1. Go to your repo **Settings → Pages**
2. Set **Source** to **Deploy from a branch**
3. Select the branch (e.g. `main`) and folder (`/` or `/docs`)
4. Save — your dashboard will be live at:
   `https://<owner>.github.io/<repo>/action/dashboard/dashboard.html`

Once deployed, double-click `dashboard.url` (Windows) to open it in your browser.

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
