"""
action/proxy/curriculum.py
28-day MUE curriculum schedule — single source of truth for the dummy learner.

Derived from source/4-Week Onboarding Map.md. Every day maps to a week,
theme, category tags, focus topic, evidence artifact, and optional proof task.
"""

# ── Level framework ────────────────────────────────────────────────────────
LEVEL_DAYS = 28  # working days per curriculum level

# ── Scorecard areas (matches build_data.py SCORE_AREAS) ─────────────────────
SCORE_AREAS = [
    'Prompt discipline',
    'Repo or workspace analysis',
    'Change isolation',
    'Validation order',
    'Deployment awareness',
    'Reviewer handoff',
    'Reusability',
]

# ── Codex gates (matches build_data.py CODEX_GATES) ─────────────────────────
CODEX_GATES = [
    'One end-to-end workflow completed',
    'Business-logic ownership understood',
    'Validation evidence produced without help',
    'Proof tasks completed',
    'One clean reviewable change slice',
    'One reusable team asset created',
]

# ── Proof tasks (matches build_data.py PROOF_TASKS) ─────────────────────────
PROOF_TASKS = {
    'PT1': {'name': 'Repository Analysis Brief', 'due_day': 9, 'week': 2},
    'PT2': {'name': 'Review Workflow Dry Run', 'due_day': 21, 'week': 4},
    'PT3': {'name': 'Metric Lineage Walkthrough', 'due_day': 13, 'week': 3},
    'PT4': {'name': 'QC Evidence Pack', 'due_day': 16, 'week': 3},
    'PT5': {'name': 'Deployment Rehearsal', 'due_day': 18, 'week': 3},
    'PT6': {'name': 'Reviewer Handoff Test', 'due_day': 21, 'week': 4},
}

# ── Classification progression milestones ────────────────────────────────────
CLASSIFICATION_MILESTONES = [
    (1, 'Foundational'),
    (8, 'Developing'),
    (18, 'Operational'),
    (25, 'Ready For Codex Acceleration'),
]

# ── Primary track rotation (matches curriculum tags) ─────────────────────────
TRACK_ROTATION = {
    1: 'Pyramid operations',
    2: 'Codex productivity',
    3: 'BI judgment',
    4: 'Pyramid operations',
    5: 'Pyramid operations',
    6: 'BI judgment',
    7: 'Pyramid operations',
    8: 'Pyramid operations',
    9: 'Codex productivity',
    10: 'Pyramid operations',
    11: 'Pyramid operations',
    12: 'Codex productivity',
    13: 'BI judgment',
    14: 'BI judgment',
    15: 'Codex productivity',
    16: 'Codex productivity',
    17: 'Pyramid operations',
    18: 'Pyramid operations',
    19: 'Pyramid operations',
    20: 'Pyramid operations',
    21: 'Codex productivity',
    22: 'BI judgment',
    23: 'Pyramid operations',
    24: 'Codex productivity',
    25: 'BI judgment',
    26: 'Codex productivity',
    27: 'Pyramid operations',
    28: 'Codex productivity',
}

# ── Full 28-day curriculum schedule ──────────────────────────────────────────
CURRICULUM = {
    # ═══════════════════════════════════════════════════════════════════════
    # WEEK 1 — 🏗️ Foundation (Days 1–5)
    # ═══════════════════════════════════════════════════════════════════════
    1: {
        'week': 1, 'theme': 'Foundation',
        'tags': ['🤖 AI', '💬 Team'],
        'focus': 'AI Modes & Prompts + Team Norms',
        'evidence_description': 'Readiness note explaining modes, prompt structure, context-window limits, team channels, standup structure',
        'required_artifact': 'pyramid_overview_screenshot.png',
        'proof_task': None,
        'week_number': 1,
    },
    2: {
        'week': 1, 'theme': 'Foundation',
        'tags': ['🤖 AI', '⚡ Codex'],
        'focus': 'Prompt Crafting + Codex Loop Intro',
        'evidence_description': 'Three working prompts + revision log + Handoff Reading exercise result',
        'required_artifact': 'prompt_templates_v1.md',
        'proof_task': None,
        'week_number': 1,
    },
    3: {
        'week': 1, 'theme': 'Foundation',
        'tags': ['📊 BI', '📦 Del', '💬 Team'],
        'focus': 'Change Isolation + First Standup',
        'evidence_description': 'Clean review draft: purpose, audience, focus, reviewer questions + standup note',
        'required_artifact': 'change_isolation_draft.md',
        'proof_task': None,
        'week_number': 1,
    },
    4: {
        'week': 1, 'theme': 'Foundation',
        'tags': ['🏗️ Pyr', '🔗 Data'],
        'focus': 'Model Lineage',
        'evidence_description': 'One-page dependency map naming each layer (source → transformation → snapshot → rollup → QC)',
        'required_artifact': 'dependency_map_v1.png',
        'proof_task': None,
        'week_number': 1,
    },
    5: {
        'week': 1, 'theme': 'Foundation',
        'tags': ['🏗️ Pyr', '📦 Del', '🧠 Ret', '💬 Team'],
        'focus': 'Operations Checklist + Task Tracking + Week 1 Scorecard',
        'evidence_description': 'v1 deployment + handoff checklist + task board snapshot + Week 1 Scorecard',
        'required_artifact': 'deployment_checklist_v1.md',
        'proof_task': None,
        'week_number': 1,
    },

    # ═══════════════════════════════════════════════════════════════════════
    # WEEK 2 — 🔗 Data Foundation (Days 6–12)
    # ═══════════════════════════════════════════════════════════════════════
    6: {
        'week': 2, 'theme': 'Data Foundation',
        'tags': ['📊 BI', '🔗 Data', '💬 Team'],
        'focus': 'Source-to-Output Inventory + Status Update',
        'evidence_description': 'Source-to-output inventory + status update note',
        'required_artifact': 'source_output_inventory.md',
        'proof_task': None,
        'week_number': 2,
    },
    7: {
        'week': 2, 'theme': 'Data Foundation',
        'tags': ['🔗 Data', '📊 BI'],
        'focus': 'Row Ownership & Deduplication',
        'evidence_description': 'Row ownership + deduplication note',
        'required_artifact': 'row_ownership_note.md',
        'proof_task': None,
        'week_number': 2,
    },
    8: {
        'week': 2, 'theme': 'Data Foundation',
        'tags': ['🔗 Data', '📊 BI'],
        'focus': 'Aggregation Boundaries',
        'evidence_description': 'Aggregation boundary note — double-counting risks, grain boundaries',
        'required_artifact': 'aggregation_boundary_note.md',
        'proof_task': None,
        'week_number': 2,
    },
    9: {
        'week': 2, 'theme': 'Data Foundation',
        'tags': ['⚡ Codex', '🧠 Ret', '💬 Team'],
        'focus': 'PT1: Repository Analysis Brief + Codex Exercise 2: Context Pull',
        'evidence_description': 'PT1 brief + Context Pull exercise with before/after prompt comparison + team update note',
        'required_artifact': 'PT1_repository_analysis.md',
        'proof_task': 'PT1',
        'week_number': 2,
    },
    10: {
        'week': 2, 'theme': 'Data Foundation',
        'tags': ['🏗️ Pyr', '🔗 Data'],
        'focus': 'Hierarchy & Structure + Week 2 Scorecard',
        'evidence_description': 'Week 2 scorecard + hierarchy validation note',
        'required_artifact': 'hierarchy_validation.md',
        'proof_task': None,
        'week_number': 2,
    },
    11: {
        'week': 2, 'theme': 'Data Foundation',
        'tags': ['🏗️ Pyr', '📊 BI'],
        'focus': 'Measure & Service Logic',
        'evidence_description': 'Active-row logic note — validate active/inactive rows, cancellations',
        'required_artifact': 'active_row_logic.md',
        'proof_task': None,
        'week_number': 2,
    },
    12: {
        'week': 2, 'theme': 'Data Foundation',
        'tags': ['⚡ Codex', '🔗 Data', '🧠 Ret'],
        'focus': 'Time Logic & Parameters + Codex Exercise 3: State Summary',
        'evidence_description': 'Time logic note + list/parameter note + State Summary exercise result + Week 2 Scorecard',
        'required_artifact': 'time_logic_note.md',
        'proof_task': None,
        'week_number': 2,
    },

    # ═══════════════════════════════════════════════════════════════════════
    # WEEK 3 — ⚡ Operations (Days 13–19)
    # ═══════════════════════════════════════════════════════════════════════
    13: {
        'week': 3, 'theme': 'Operations',
        'tags': ['📊 BI', '🔗 Data'],
        'focus': 'PT3: Metric Lineage Walkthrough + Snapshot Validation',
        'evidence_description': 'PT3 walkthrough + snapshot validation note',
        'required_artifact': 'PT3_metric_lineage.md',
        'proof_task': 'PT3',
        'week_number': 3,
    },
    14: {
        'week': 3, 'theme': 'Operations',
        'tags': ['📊 BI', '🔗 Data'],
        'focus': 'Rollup Behavior',
        'evidence_description': 'Rollup behavior note — lowest grain → summaries, weighted/summed/derived totals',
        'required_artifact': 'rollup_behavior_note.md',
        'proof_task': None,
        'week_number': 3,
    },
    15: {
        'week': 3, 'theme': 'Operations',
        'tags': ['⚡ Codex', '📦 Del', '💬 Team'],
        'focus': 'PT4: QC Plan + Codex Validation Practice',
        'evidence_description': 'QC evidence template (first pass) + Validation Check prompt result + anomaly escalation note',
        'required_artifact': 'PT4_qc_evidence_draft.md',
        'proof_task': 'PT4',
        'week_number': 3,
    },
    16: {
        'week': 3, 'theme': 'Operations',
        'tags': ['⚡ Codex', '🧠 Ret'],
        'focus': 'PT4: QC Evidence Pack Complete + Handoff Draft',
        'evidence_description': 'Completed PT4 QC evidence pack + Handoff Draft exercise result',
        'required_artifact': 'PT4_qc_evidence_pack.md',
        'proof_task': 'PT4',
        'week_number': 3,
    },
    17: {
        'week': 3, 'theme': 'Operations',
        'tags': ['🏗️ Pyr', '📦 Del', '💬 Team'],
        'focus': 'Deployment Preflight + Task Breakdown',
        'evidence_description': 'Preflight checklist + access note + task breakdown',
        'required_artifact': 'deployment_preflight.md',
        'proof_task': None,
        'week_number': 3,
    },
    18: {
        'week': 3, 'theme': 'Operations',
        'tags': ['🏗️ Pyr', '🧠 Ret'],
        'focus': 'PT5: Deployment Rehearsal',
        'evidence_description': 'Completed PT5 deployment rehearsal record — draft sequence → dry run → record',
        'required_artifact': 'PT5_deployment_rehearsal.md',
        'proof_task': 'PT5',
        'week_number': 3,
    },
    19: {
        'week': 3, 'theme': 'Operations',
        'tags': ['🏗️ Pyr', '📦 Del', '🧠 Ret', '💬 Team'],
        'focus': 'Close Operations Layer + Team Sync + Week 3 Scorecard',
        'evidence_description': 'Week 3 Scorecard + deployment closeout + team sync note',
        'required_artifact': 'week3_closeout.md',
        'proof_task': None,
        'week_number': 3,
    },

    # ═══════════════════════════════════════════════════════════════════════
    # WEEK 4 — 📦 Contribution (Days 20–28)
    # ═══════════════════════════════════════════════════════════════════════
    20: {
        'week': 4, 'theme': 'Contribution',
        'tags': ['🏗️ Pyr', '📦 Del', '💬 Team'],
        'focus': 'Content Movement & Handoff Path + Task Board',
        'evidence_description': 'Content-movement checklist + handoff draft + task board update',
        'required_artifact': 'content_movement_checklist.md',
        'proof_task': None,
        'week_number': 4,
    },
    21: {
        'week': 4, 'theme': 'Contribution',
        'tags': ['⚡ Codex', '📦 Del', '🧠 Ret'],
        'focus': 'PT2: Review Dry Run + PT6: Handoff Test + Codex Exercise 4',
        'evidence_description': 'PT2 review package + PT6 handoff test + Change Impact prompt result',
        'required_artifact': 'PT2_review_package.md',
        'proof_task': 'PT2',
        'week_number': 4,
    },
    22: {
        'week': 4, 'theme': 'Contribution',
        'tags': ['📊 BI', '📦 Del', '💬 Team'],
        'focus': 'Change Slice + Feedback Practice',
        'evidence_description': 'Change-slice charter + baseline note + owning-surface note + feedback reception note',
        'required_artifact': 'change_slice_charter.md',
        'proof_task': None,
        'week_number': 4,
    },
    23: {
        'week': 4, 'theme': 'Contribution',
        'tags': ['🏗️ Pyr', '⚡ Codex'],
        'focus': 'Fix Path & Validate + Bounded Codex Practice',
        'evidence_description': 'Fix-path draft + validation record + iteration note + Bounded Codex exercise result',
        'required_artifact': 'fix_path_validation.md',
        'proof_task': None,
        'week_number': 4,
    },
    24: {
        'week': 4, 'theme': 'Contribution',
        'tags': ['⚡ Codex', '📦 Del', '🧠 Ret', '💬 Team'],
        'focus': 'Review Package + Handoff Mastery + Week 4 Scorecard',
        'evidence_description': 'Before/after note + review package + closed contribution + handoff graded against rubric + Week 4 Scorecard',
        'required_artifact': 'review_package_final.md',
        'proof_task': None,
        'week_number': 4,
    },
    25: {
        'week': 4, 'theme': 'Contribution',
        'tags': ['📊 BI', '📦 Del', '💬 Team'],
        'focus': 'Handoff Rehearsal + Peer Review',
        'evidence_description': 'Surface recommendation + reviewer summary + final handoff rehearsal + peer feedback log',
        'required_artifact': 'handoff_rehearsal.md',
        'proof_task': None,
        'week_number': 4,
    },
    26: {
        'week': 4, 'theme': 'Contribution',
        'tags': ['⚡ Codex', '📦 Del', '💬 Team'],
        'focus': 'PT6: Reusable Asset (v1) — Codex Prompt Library',
        'evidence_description': 'Asset charter + draft v1 + test note + prompt pattern as asset + early feedback note',
        'required_artifact': 'PT6_reusable_asset_v1.md',
        'proof_task': 'PT6',
        'week_number': 4,
    },
    27: {
        'week': 4, 'theme': 'Contribution',
        'tags': ['🏗️ Pyr', '📦 Del', '💬 Team'],
        'focus': 'Reusable Asset (v2) + Team Handoff',
        'evidence_description': 'Surface-aware revision + example + gap list + v3 + final asset + team handoff record',
        'required_artifact': 'reusable_asset_final.md',
        'proof_task': None,
        'week_number': 4,
    },
    28: {
        'week': 4, 'theme': 'Contribution',
        'tags': ['🧠 Ret', '🤖 AI', '⚡ Codex', '💬 Team'],
        'focus': 'Codex Gate & Closeout + Final Team Communication',
        'evidence_description': 'Codex comparison note + final readiness statement + Final Readiness Package',
        'required_artifact': 'final_readiness_package.md',
        'proof_task': None,
        'week_number': 4,
    },
}


def get_classification(day_number: int) -> str:
    """Return the classification for a given day number based on milestones."""
    result = CLASSIFICATION_MILESTONES[0][1]
    for milestone_day, classification in CLASSIFICATION_MILESTONES:
        if day_number >= milestone_day:
            result = classification
    return result


def get_level_for_day(day_number: int) -> int:
    """
    Determine which curriculum level a day belongs to.

    Currently all days map to Level 1 (Foundation). When multi-level
    curriculum content is implemented, this will map day ranges to
    different levels (e.g., days 1-28 → Level 1, 29-56 → Level 2, etc.).
    """
    if day_number < 1:
        return 1
    return ((day_number - 1) // LEVEL_DAYS) + 1


def get_primary_track(day_number: int) -> str:
    """Return the primary track for a given day number."""
    return TRACK_ROTATION.get(day_number, 'BI judgment')


def get_week_for_day(day_number: int) -> int:
    """Return the week number (1-4) for a given day number."""
    entry = CURRICULUM.get(day_number)
    return entry['week'] if entry else ((day_number - 1) // 7) + 1
