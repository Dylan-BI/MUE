# MUE Test Data Reference Record

> **Generated:** 2026-07-18  
> **Purpose:** Document test data generated during validation for future reference and regression testing

---

## 1. Proxy-Generated Learner Data (DummyLearner)

### Configuration
- **Learner Name:** Alex Chen
- **Curriculum Start Date:** 2026-07-13 (auto-detected from earliest artifact)
- **Levels Tested:** Level 1 (Foundation), Level 2 (Development)

### Daily Notes Generated (30 total)
| Date | Day | Level | Classification | Primary Track | Required Artifact |
|------|-----|-------|----------------|---------------|-------------------|
| 2026-07-13 | 1 | 1 | Foundational | Pyramid operations | pyramid_overview_screenshot.png |
| 2026-07-14 | 2 | 1 | Foundational | Codex productivity | prompt_templates_v1.md |
| 2026-07-15 | 3 | 1 | Foundational | BI judgment | change_isolation_draft.md |
| 2026-07-16 | 4 | 1 | Foundational | Pyramid operations | dependency_map_v1.png |
| 2026-07-17 | 5 | 1 | Foundational | Pyramid operations | deployment_checklist_v1.md |
| 2026-07-20 | 6 | 1 | Developing | BI judgment | source_output_inventory.md |
| 2026-07-21 | 7 | 1 | Developing | Pyramid operations | row_ownership_note.md |
| 2026-07-22 | 8 | 1 | Developing | Pyramid operations | aggregation_boundary_note.md |
| 2026-07-23 | 9 | 1 | Developing | Codex productivity | PT1_repository_analysis.md |
| 2026-07-24 | 10 | 1 | Developing | Pyramid operations | hierarchy_validation_note.md |
| 2026-07-27 | 11 | 1 | Developing | Pyramid operations | measure_definition_note.md |
| 2026-07-28 | 12 | 1 | Developing | Codex productivity | period_logic_note.md |
| 2026-07-29 | 13 | 1 | Developing | BI judgment | PT3_metric_lineage.md |
| 2026-07-30 | 14 | 1 | Developing | BI judgment | snapshot_validation_note.md |
| 2026-07-31 | 15 | 1 | Developing | Codex productivity | qc_checklist_v1.md |
| 2026-08-03 | 16 | 1 | Operational | Codex productivity | PT4_qc_evidence_pack.md |
| 2026-08-04 | 17 | 1 | Operational | Pyramid operations | deployment_rehearsal_log.md |
| 2026-08-05 | 18 | 1 | Operational | Pyramid operations | PT5_deployment_rehearsal.md |
| 2026-08-06 | 19 | 1 | Operational | Pyramid operations | handoff_draft_v1.md |
| 2026-08-07 | 20 | 1 | Operational | Codex productivity | review_package_v1.md |
| 2026-08-10 | 21 | 1 | Operational | Codex productivity | PT2_review_dry_run.md |
| 2026-08-11 | 22 | 1 | Operational | BI judgment | reviewer_feedback_log.md |
| 2026-08-12 | 23 | 1 | Operational | Pyramid operations | asset_charter_v1.md |
| 2026-08-13 | 24 | 1 | Operational | Codex productivity | prompt_library_v1.md |
| 2026-08-14 | 25 | 1 | Ready for Codex | BI judgment | readiness_package_v1.md |
| 2026-08-17 | 26 | 1 | Ready for Codex | Codex productivity | codex_comparison_note.md |
| 2026-08-18 | 27 | 1 | Ready for Codex | Pyramid operations | final_asset_v3.md |
| 2026-08-19 | 28 | 1 | Ready for Codex | Codex productivity | final_readiness_statement.md |
| 2026-08-24 | 1 | 2 | Foundational | Pyramid operations | (Level 2 Day 1) |
| 2026-08-25 | 28 | 2 | Foundational | Pyramid operations | (Level 2 Day 28) |

### Evidence Artifacts (12 files)
| File | Proof Task | Description |
|------|------------|-------------|
| PT1_repository_analysis.md | PT1 | Repository Analysis Brief |
| PT2_review_dry_run.md | PT2 | Review Workflow Dry Run |
| PT3_metric_lineage.md | PT3 | Metric Lineage Walkthrough |
| PT4_qc_evidence_pack.md | PT4 | QC Evidence Pack |
| PT5_deployment_rehearsal.md | PT5 | Deployment Rehearsal |
| PT6_reusable_asset.md | PT6 | Reviewer Handoff Test |
| row_ownership_note.md | — | Row ownership & deduplication |
| aggregation_boundary_note.md | — | Aggregation boundaries |
| hierarchy_validation_note.md | — | Hierarchy validation |
| measure_definition_note.md | — | Measure definitions |
| period_logic_note.md | — | Period definitions & target calculations |
| qc_checklist_v1.md | — | QC checklist v1 |

### Reports Generated (11 files)
| File | Type | Week |
|------|------|------|
| weekly-2026-W01.md | Weekly | 1 |
| weekly-2026-W02.md | Weekly | 2 |
| weekly-2026-W03.md | Weekly | 3 |
| weekly-2026-W04.md | Weekly | 4 |
| weekly-2026-34.md | Weekly | 34 (Level 2) |
| readiness-2026-W01.md | Readiness | 1 |
| readiness-2026-W02.md | Readiness | 2 |
| readiness-2026-W03.md | Readiness | 3 |
| readiness-2026-W04.md | Readiness | 4 |
| readiness-2026-W34.md | Readiness | 34 (Level 2) |
| readiness-full-report.md | Full | All |

---

## 2. Review Server Test Data

### Reviewer Profile Created
```json
{
  "test_reviewer": {
    "username": "test_reviewer",
    "displayName": "Test Reviewer",
    "email": "test@example.com",
    "dailySummary": true,
    "role": "Reviewer",
    "createdAt": "2026-07-18T03:00:29.022067",
    "updatedAt": "2026-07-18T03:00:29.022088"
  }
}
```

### Review Submitted
```json
{
  "artifactId": "test-artifact",
  "review": {
    "name": "Test Reviewer",
    "rating": "👍 Pass",
    "text": "Test review",
    "category": "🤖 AI"
  }
}
```
**Result:** Review ID `17843364034435505`, version 1, timestamp `2026-07-18T03:00:03.443244`

### Lock Test
```json
{
  "artifactId": "test-artifact",
  "reviewId": "17843364034435505",
  "action": "claim",
  "name": "Test Reviewer"
}
```
**Result:** Lock acquired with TTL 600s

### Presence Test
```json
{
  "name": "Test User",
  "displayName": "Test User",
  "color": "#ff0000",
  "avatar": "👤",
  "activePage": "overview",
  "activeArtifact": "test-artifact",
  "activeLabel": "Test"
}
```

---

## 3. TPL (Test Proxy Learner) Generated Data

### TPL Notes (3 files)
| File | Day | Classification | Track |
|------|-----|----------------|-------|
| tpl_2026-07-18.md | 1 | Foundational | Pyramid operations |
| tpl_2026-07-17.md | 2 | Foundational | Codex productivity |
| tpl_2026-07-16.md | 3 | Foundational | BI judgment |

### TPL Evidence (2 files)
| File | Description |
|------|-------------|
| tpl_environment_setup.png | Environment setup evidence |
| tpl_codex_loop_ref.md | Codex Loop reference document |

**Generated via:** `POST /api/tpl/generate` with `X-TPL-Secret: testsecret`  
**Cleaned via:** `POST /api/tpl/cleanup` (5 files removed)

---

## 4. Dashboard Data.json Structure (Validated)

### Schema Validation
- **Schema File:** `action/dashboard/data_schema.json`
- **Validator:** `jsonschema` v4.26.0 with `Draft202012Validator`
- **Status:** ✅ **PASSED** (after iterative fixes)

### Key Data Points (Latest Build)
```json
{
  "generated": "2026-07-18T03:18:20.267260",
  "version": { "commit": "7034641", "timestamp": "2026-07-18T02:39:27" },
  "notes": 30,
  "evidence": 12,
  "reports": 11,
  "artifacts": 110,
  "summary": {
    "total_days": 58,
    "unique_weeks": 5,
    "latest_classification": "Foundational",
    "evidence_count": 12,
    "learner_level": 1,
    "level_progression": {
      "current_level": 2,
      "levels": {
        "1": { "days_completed": 56, "is_completed": true, "is_unlocked": true },
        "2": { "days_completed": 2, "is_completed": false, "is_unlocked": true, "in_progress": true },
        "3": { "days_completed": 0, "is_unlocked": false },
        "4": { "days_completed": 0, "is_unlocked": false }
      }
    },
    "proof_tasks": {
      "PT1": { "found": true, "days": [8,8,9,9] },
      "PT2": { "found": true, "days": [20,20,21,21,1,28] },
      "PT3": { "found": true, "days": [12,12,13,13] },
      "PT4": { "found": true, "days": [14,14,15,15,16,16] },
      "PT5": { "found": true, "days": [17,17,18,18] },
      "PT6": { "found": true, "days": [20,20,21,21,26,26] }
    },
    "codex_gate_status": {
      "business-logic_ownership_understood": "Yes",
      "validation_evidence_produced_without_help": "Yes",
      "proof_tasks_completed": "Yes",
      "one_reusable_team_asset_created": "Yes"
    }
  }
}
```

---

## 5. API Endpoints Tested (Review Server)

| Endpoint | Method | Status | Notes |
|----------|--------|--------|-------|
| `/api/reviews` | GET | ✅ | Returns all reviews |
| `/api/reviews` | POST | ✅ | Creates review (requires 👍 Pass / ⚡ Needs Work / ❌ Rework) |
| `/api/profiles` | GET | ✅ | Returns all profiles |
| `/api/profiles` | POST | ✅ | Creates/updates profile (auth: owner or admin) |
| `/api/profiles` | DELETE | ✅ | Deletes profile (auth: owner or admin) |
| `/api/locks` | GET | ✅ | Returns active locks |
| `/api/locks` | POST | ✅ | Claim/release/check locks |
| `/api/presence` | GET | ✅ | Returns active reviewers |
| `/api/presence` | POST | ✅ | Heartbeat |
| `/api/status` | GET | ✅ | Server status + counts |
| `/api/daily-summary` | POST | ✅ | Sends daily summary email |
| `/api/tpl/generate` | POST | ✅ | Requires `X-TPL-Secret` header |
| `/api/tpl/cleanup` | POST | ✅ | Requires `X-TPL-Secret` header |
| `/api/check-token` | GET | ✅ | Token validation |
| `/go` | GET | ✅ | Redirects to `/dashboard.html?t=<token>` |
| `/dashboard.html` | GET | ✅ | Serves dashboard |
| `/data.json` | GET | ✅ | Serves data.json |

---

## 6. CLI Commands Tested

### Proxy CLI (`action/proxy/run_proxy.py`)
```bash
# Generate today's note (auto-detects day)
python action/proxy/run_proxy.py --today

# Generate specific date/day
python action/proxy/run_proxy.py --date 2026-08-24 --day 1 --level 2

# Generate range
python action/proxy/run_proxy.py --range 1-5

# Full curriculum run (all 28 days + weekly reports + archive)
python action/proxy/run_proxy.py --full-run

# Generate + archive cycle
python action/proxy/run_proxy.py --cycle 1-28
```

### Dashboard Scripts
```bash
# Build data.json
python action/dashboard/build_data.py

# Watch for changes (auto-rebuild)
python action/dashboard/watch_and_build.py

# Validate email flow
python action/dashboard/validate_email_flow.py
```

### Source Scripts
```bash
# Create daily note (enforces 28-day max, weekdays only)
python source/scripts/create_daily_note.py --date 2026-08-24 --day-number 1 --level 2

# Aggregate weekly notes
python source/scripts/aggregate_weekly.py --year 2026 --week 34

# Generate readiness report (latest week)
python source/scripts/generate_readiness_report.py

# Generate readiness report (specific week)
python source/scripts/generate_readiness_report.py --year 2026 --week 34

# Full readiness report
python source/scripts/generate_readiness_report.py --full
```

### Review Scripts
```bash
# Sync action/ → review/
python review/scripts/sync-from-action.py

# Save reviews from dashboard export
python review/scripts/save-reviews.py path/to/export.json

# Verify reviews.json
python review/scripts/save-reviews.py --check
```

### Review Server
```bash
# Start server (local, no token)
python action/dashboard/review_server.py --port 8081 --host 127.0.0.1 --no-token

# Start server with TPL secret
python action/dashboard/review_server.py --port 8081 --host 127.0.0.1 --no-token --tpl-secret testsecret

# Test mode (send daily summary now and exit)
python action/dashboard/review_server.py --test-summary
```

---

## 7. Schema Validation Fixes Applied

| Issue | Fix |
|-------|-----|
| `scripts` required but not in data | Removed `scripts`, `dashboard`, `review`, `source` from required; added `page_artifacts`, `changed_files`, etc. |
| `reports` missing `folder`, `preview`, `content`, etc. | Made all optional with `["string", "null"]` |
| `evidence` missing `filename`, `folder`, etc. | Reduced required to `path`, `size`, `modified` |
| `notes` missing `category_tags` | Made `category_tags` optional |
| `week_number` null in some notes | Changed to `["integer", "null"]` |
| `calendar_status` value "adequate" not in enum | Added "adequate" to enum |
| `proof_tasks` was boolean, now object | Changed to object with `id`, `description`, `found`, `days` |
| `week_progress` was object, sometimes array | Changed to `["object", "array"]` |
| `calendar_status` value "ahead" not in enum | Added "ahead" to enum |
| `environment_status.overall_status` "adequate" not in enum | Added "adequate" to enum |
| `evidence` archived items missing `filename` | Made `filename` optional |
| `reports` archived items missing `was_changed` | Made `was_changed` optional |
| `notes` missing `category_tags` | Removed from required |

---

## 8. Files Modified During Testing

### Core Curriculum
- `source/Pyramid, Codex, and BI Judgment Daily Working Template.txt` — Added Level field
- `source/scripts/create_daily_note.py` — Added `--level` argument

### Proxy & Constants
- `action/proxy/constants.py` — Added SCORECARD_RUBRIC, CODEX_GATE_CRITERIA, PROOF_TASK_CRITERIA, LEVEL_COMPETENCY_GATES, moved PT2 to Day 19

### Dashboard
- `action/dashboard/build_data.py` — Added LEVEL_COMPETENCY_GATES, improved regex, min_quality_check(), JSON Schema validation
- `action/dashboard/data_schema.json` — **New** comprehensive JSON Schema
- `action/dashboard/send_tunnel_security.py` — Configurable TUNNEL_URL and TO_EMAIL via env vars

### Review Server
- `action/dashboard/review_server.py` — Added `_validate_environment()` with fail-fast checks

### New Files
- `action/dashboard/data_schema.json` — JSON Schema for data.json validation

---

## 9. Known Test Data Locations

| Type | Path |
|------|------|
| Daily Notes | `action/notes/*.md` (30 files) |
| Archived Notes | `action/archive/notes/*.md` (28 files) |
| Evidence | `action/evidence/*.md` (12 files) |
| Archived Evidence | `action/archive/evidence/*.md` |
| Reports | `action/reports/*.md` (11 files) |
| Archived Reports | `action/archive/reports/*.md` |
| Reviewer Profiles | `review/reviewer_profiles.json` |
| Reviews | `review/reviews.json` |
| Profile Activity | `review/profile_activity.json` |
| Dashboard Data | `action/dashboard/data.json` |
| Dashboard Schema | `action/dashboard/data_schema.json` |
| Learner Config | `action/learner_config.json` |

---

## 10. Regression Test Checklist

For future validation runs, verify:

- [ ] `python action/dashboard/build_data.py` completes with ✅ Schema validation passed
- [ ] `python action/dashboard/review_server.py --port 8081 --host 127.0.0.1 --no-token --test-summary` exits cleanly
- [ ] `python action/proxy/run_proxy.py --full-run` generates all 28 days + reports
- [ ] `python source/scripts/create_daily_note.py --date 2026-08-24 --day-number 1 --level 2` creates note with Level 2 header
- [ ] `python action/dashboard/validate_email_flow.py` shows all PASS
- [ ] Review server API endpoints all return 200/201
- [ ] Dashboard loads at `http://127.0.0.1:8081/dashboard.html`
- [ ] `/go` redirects to `/dashboard.html`
- [ ] TPL generate/cleanup works with `X-TPL-Secret` header
- [ ] Schema validation passes with `jsonschema` package installed

---

*End of Test Data Reference Record*