# Learner Web Interface — Design Proposal

## 1. Architecture Overview

```
┌──────────────────────────────────────────────────┐
│               WebLearner (Flask/FastAPI)          │
│  action/proxy/web_interface.py                    │
│                                                   │
│  Implements LearnerProxy interface                │
│  + Web UI routes for interactive learning         │
│  + Real-time sync with archive                    │
│  + Auto-triggers build_data.py                    │
└──────────┬──────────┬──────────┬─────────────────┘
           │          │          │
      Reads│    Writes│    Triggers│
           ▼          ▼          ▼
   ┌──────────┐ ┌──────────┐ ┌──────────────┐
   │source/   │ │action/   │ │build_data.py │
   │curriculum│ │notes/    │ │→ data.json   │
   │reference │ │evidence/ │ │→ dashboard   │
   │files     │ │reports/  │ │  refresh     │
   └──────────┘ └──────────┘ └──────────────┘
                     │
                     ▼
              ┌──────────────┐
              │action/archive│
              │(auto-sync)   │
              └──────────────┘
```

## 2. What to Implement

### 2.1 `WebLearner` class (action/proxy/web_interface.py)

Implements the 6 abstract methods from `LearnerProxy`:

| Method | Role | Web Behaviour |
|--------|------|---------------|
| `get_name()` | Returns learner display name | Reads from session/auth or `learner_config.json` |
| `generate_daily_note(date, day)` | Writes note to `action/notes/` | Called when learner submits via the daily note form |
| `generate_evidence(day, type)` | Writes evidence file | Called when learner uploads/submits evidence |
| `generate_weekly_report(week)` | Creates aggregated report | Called on request or auto-triggered at week boundaries |
| `get_curriculum_day(date)` | Maps date → day number (1-28) | Same logic as dummy — counts working days from start |
| `archive_completed(days_range)` | Moves files to archive | Called when learner marks a day/week as complete |

### 2.2 Web UI Pages

The web interface should serve the following pages to the learner:

#### A. Dashboard / Home (`/`)
- Greeting with learner name
- **Current curriculum day** & progress (e.g., "Day 5 of 28")
- Readiness classification (Foundational / Developing / Operational / Ready)
- Quick stats: notes completed, evidence submitted, current week
- **Today's task card** — what the curriculum says for the current day

#### B. Curriculum Viewer (`/curriculum`)
- Full 28-day schedule rendered from `curriculum.py`
- Filterable by week (1-4)
- Each day card shows:
  - Day number, date, week, theme
  - Category tags (🤖 AI, 📊 BI, 🏗️ Pyr, etc.)
  - Today's focus description
  - Required evidence artifact
  - Proof task (if applicable)
- **Click a day** → opens the daily note editor for that day

#### C. Daily Note Editor (`/notes/new` or `/notes/{date}`)
- Auto-populates from the curriculum for the given day
- Form fields matching `build_data.py`'s `parse_note()` regex patterns:
  - **Date** (auto-filled, read-only)
  - **Day number** (auto-filled from curriculum)
  - **Level** (select: 1-4)
  - **Classification** (dropdown: Foundational / Developing / Operational / Ready For Codex Acceleration)
  - **Primary track** (dropdown: Pyramid operations / Codex productivity / BI judgment)
  - **Week Number** (auto-calculated)
  - **Required Artifact** (auto-populated from curriculum)
  - **What I learned today** (textarea — markdown supported)
  - **What evidence I produced** (textarea)
  - **What remains open** (textarea)
  - **Next narrow step** (textarea)
  - **Scorecard** (toggle per area: Pass / Moderate / Fail / Unscored)
  - **Codex gates** (toggle per gate: Yes / No)
- **Save** button → calls `generate_daily_note()` → writes to `action/notes/{date}.md`
- **Auto-trigger**: after save, runs `build_data.py` to refresh dashboard

#### D. Evidence Manager (`/evidence`)
- List existing evidence files in `action/evidence/`
- **Upload** new evidence (file upload for .md, .txt, .png, .csv, etc.)
- **Create from template** for proof tasks PT1-PT6:
  - PT1: Repository Analysis Brief
  - PT2: Review Workflow Dry Run
  - PT3: Metric Lineage Walkthrough
  - PT4: QC Evidence Pack
  - PT5: Deployment Rehearsal
  - PT6: Reviewer Handoff Test
- Each template provides the required sections as form fields
- **Edit** existing evidence (inline markdown editor)
- **Delete** with confirmation
- **Preview** rendered markdown

#### E. Weekly Report Generator (`/reports`)
- Select week (1-4)
- Auto-aggregates notes from that week
- Shows scorecard summary across all days
- Shows Codex gate status
- **Generate Report** button → calls `generate_weekly_report()`
- **View** existing reports

#### F. Archive & Sync Status (`/archive`)
- Shows what's been archived vs. what's active
- **Archive completed days** — select day range and archive
- **Sync to review** — trigger the sync process
- Shows sync status: last synced, pending changes

#### G. Curriculum Reference (`/reference`)
- Browse source files from `source/` directory
- Filter by category (🤖 AI, ⚡ Codex, 🏗️ Pyr, etc.)
- View rendered markdown reference documents
- Download source files

### 2.3 API Endpoints (for programmatic access)

The web interface should also expose a REST API so the dashboard/review server can interact with it:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/status` | Learner status, current day, classification |
| GET | `/api/curriculum` | Full 28-day schedule |
| GET | `/api/notes` | List all notes |
| GET | `/api/notes/{date}` | Get a specific note |
| POST | `/api/notes` | Create/update a note |
| GET | `/api/evidence` | List all evidence files |
| POST | `/api/evidence` | Upload evidence |
| GET | `/api/reports` | List reports |
| POST | `/api/reports/generate` | Generate weekly report |
| POST | `/api/archive` | Archive completed days |
| POST | `/api/sync` | Trigger build_data.py |

## 3. Technology Choices

### Recommended: **FastAPI** (as suggested by existing `.venv/` packages)

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Web framework** | FastAPI | Already in `.venv/`, async support, auto-docs, Pydantic validation |
| **Templating** | Jinja2 (included with FastAPI) | Server-side rendering of curriculum pages |
| **Markdown rendering** | Python `markdown` stdlib or `mistune` | Render curriculum files and notes |
| **File storage** | Local filesystem (`action/`) | No database needed — files are the source of truth |
| **Auth** | Simple token or none (local tool) | It's a local education tool, not a production service |
| **Auto-build** | `subprocess.run(['python', 'build_data.py'])` | Trigger after every write |
| **Frontend** | Minimal — CSS framework optional (Bootstrap via CDN or just clean HTML) | Keep it simple, no build step |

### Alternative: **Flask**
Also already installable, simpler, more lightweight. Either works fine.

### Fallback: **Python http.server + AJAX**
Zero dependencies (stdlib only), matches the existing `review_server.py` pattern. More coding effort but keeps the purity of the stdlib-only architecture.

## 4. Swap-In Procedure

Following the documented pattern in `action/proxy/__init__.py`:

```python
# ── SWAP POINT: Change this import when the real interface is ready ──
# FROM:
ActiveLearner = DummyLearner
# TO:
from .web_interface import WebLearner as ActiveLearner
```

No other code changes needed. `build_data.py`, `dashboard.html`, `review_server.py`, and the archive system all consume the same output format regardless of which implementation produces it.

## 5. Integration with the Reviewer Dashboard

The data flow for reviewer visibility:

```
Learner submits note/evidence via Web UI
  → web_interface.py writes to action/notes/ or action/evidence/
    → subprocess.run(['python', 'action/dashboard/build_data.py'])
      → data.json regenerated
        → dashboard.html auto-refreshes (2-min poll)
          → Reviewer sees updated data
```

**Additional integration points:**

1. **Auto-sync to review/**: After each learner action, optionally trigger `review/scripts/sync-from-action.py` so reviewer workspace stays current
2. **Webhook notifications**: The web interface can call the `review_server.py` API to notify reviewers when new evidence is ready
3. **Version tracking**: Each save updates the git commit → dashboard version chip updates

## 6. Curriculum-Specific Behaviour per Day

The web interface should adapt to what each curriculum day requires:

| Day Range | Behaviour | Web UI Adaptation |
|-----------|-----------|-------------------|
| Days 1-2 | Readiness note, prompt crafting | Show AI mode reference, prompt structure template |
| Day 3 | Change isolation, review draft | Show review draft template form |
| Day 4 | Model lineage | Show dependency map upload, lineage template |
| Day 5 | Ops checklist, scorecard | Show checklist builder, scorecard form |
| Days 6-8 | Source inventory, row ownership, aggregation | Show data mapping forms |
| Day 9 | PT1: Repository Analysis | Show PT1 template with all required sections |
| Days 10-12 | Hierarchy, measures, time logic | Show targeted validation forms |
| Day 13 | PT3: Metric Lineage | Show PT3 template with lineage form |
| Days 14-16 | Rollup, QC, PT4 | Show QC checklist builder |
| Days 17-18 | Deployment preflight, PT5 | Show deployment sequence builder |
| Day 19 | Scorecard, closeout | Show week summary form |
| Days 20-21 | Content movement, PT2, PT6 | Show handoff templates |
| Days 22-24 | Change slice, fix path, review package | Show change charter form |
| Days 25-27 | Handoff, reusable asset | Show asset builder |
| Day 28 | Codex gate, closeout | Show final readiness package |

## 7. What to Improve in the Existing Infrastructure

### 7.1 Consolidate Duplicated Constants

**Problem:** `build_data.py` and `proxy/constants.py` both define `SCORE_AREAS`, `CODEX_GATES`, `PROOF_TASKS`, `CATEGORIES`, and `WEEK_BOUNDARIES`. These WILL drift.

**Fix:** Extract a shared module at `action/_shared.py` (or `action/proxy/_shared.py`) that both import from. The web interface would import from this same shared module.

```python
# action/_shared.py — single source of truth
SCORE_AREAS = [...]
CODEX_GATES = [...]
PROOF_TASKS = {...}
WEEK_BOUNDARIES = [(1,1,5), (2,6,12), (3,13,19), (4,20,28)]
CATEGORIES = {...}
```

### 7.2 Add a Learner File Watch Mode

The `watch_and_build.py` already watches for file changes. The web interface should trigger a build on every save, not wait for a 3-second poll cycle. Add an explicit Webhook or HTTP endpoint:

```python
# In review_server.py or web_interface.py
@app.post("/api/rebuild")
async def trigger_rebuild():
    subprocess.run(["python", "action/dashboard/build_data.py"])
    return {"status": "ok"}
```

### 7.3 Improve Evidence Validation

The web interface should validate evidence against `PROOF_TASK_CRITERIA` before saving:
- Check required sections are present
- Check minimum content length
- Flag missing quality checks

This gives the learner immediate feedback instead of waiting for a reviewer.

### 7.4 Add Real Learner Identity Detection

The `BLOCKED_NAMES` list in `build_data.py` is fragile. Replace with a proper flag:

```python
# learner_config.json
{
  "curriculum_start_date": "2026-07-10",
  "learner_name": "Dylan",
  "is_real_learner": true  # ← explicit flag instead of blocked-names heuristic
}
```

### 7.5 Expose Level Competency Gates in Dashboard

The `LEVEL_COMPETENCY_GATES` dict in `build_data.py` defines what's needed to advance from L1→L2→L3→L4, but the dashboard never shows these criteria. The web interface should expose them so the learner knows what they need to achieve.

### 7.6 Add Auth (Optional, Future)

For a production deployment, add simple token-based auth to the web interface. For local development, skip it — the tool runs on `localhost`.

## 8. Implementation Order (Recommended)

| Phase | What | Effort | Delivers |
|-------|------|--------|----------|
| **1** | Create `WebLearner` class implementing `LearnerProxy` | 1 day | Swap-in ready; all methods return correct paths |
| **2** | Core UI: Daily note editor + save to `action/notes/` | 2 days | Learner can write and save notes |
| **3** | Evidence upload + proof task templates | 2 days | Learner can submit evidence |
| **4** | Curriculum viewer + today's task card | 1 day | Learner can see what to do |
| **5** | Auto-build trigger + sync status | 0.5 day | Dashboard auto-updates |
| **6** | Archive integration | 0.5 day | Completed work moves to archive |
| **7** | Weekly report generator | 1 day | Learner can generate reports |
| **8** | Reference document viewer | 0.5 day | Learner can browse source materials |
| **9** | Shared constants consolidation | 0.5 day | Resolves duplication tech debt |
| **10** | Level gate visibility in UI | 0.5 day | Learner sees advancement requirements |

**Total: ~10 days for full implementation.**

## 9. Files to Create

| File | Purpose |
|------|---------|
| `action/proxy/web_interface.py` | `WebLearner` class implementing `LearnerProxy` |
| `action/proxy/web_templates/` | Jinja2 templates for UI pages |
| `action/proxy/web_static/` | CSS/JS assets |
| `action/_shared.py` | Extracted shared constants (optional, debt-reduction) |
| `action/proxy/server.py` | Entry point to run the web server |
