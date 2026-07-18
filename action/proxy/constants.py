"""
action/proxy/constants.py
Shared constants for the MUE learner proxy and dashboard build pipeline.

This module centralizes all static data used across the proxy implementation,
build pipeline, and dashboard to ensure consistency and reduce duplication.
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
    'Codex handoff fluency',
    'Codex bounded use',
]

# ── Scorecard Rubric: Behavioral anchors for each score level ────────────────
# Used by reviewers to consistently assess learner competency.
# Each area has explicit criteria for Pass / Moderate / Fail.
SCORECARD_RUBRIC = {
    'Prompt discipline': {
        'Pass': 'Consistently uses structured prompts (Context + Task + Format + Constraints); revises prompts based on output quality; documents reusable prompt patterns in prompt library',
        'Moderate': 'Uses structured prompts occasionally; sometimes revises prompts; limited prompt pattern documentation',
        'Fail': 'Ad-hoc prompting without structure; no revision based on output; no prompt pattern reuse'
    },
    'Repo or workspace analysis': {
        'Pass': 'Produces complete repository analysis with business purpose, dependency order, key inputs/outputs, risk areas, and safe change points; analysis enables targeted work',
        'Moderate': 'Produces partial repository analysis; covers some elements but misses key dependencies or risks',
        'Fail': 'No repository analysis or analysis is superficial; cannot identify dependency order or risk areas'
    },
    'Change isolation': {
        'Pass': 'Every change scoped to single logical unit; <5 files changed; no unrelated formatting/whitespace; tests or validation evidence included; follows project conventions',
        'Moderate': 'Most changes scoped appropriately; occasional scope creep; validation evidence sometimes missing',
        'Fail': 'Changes span unrelated areas; "while I was here" fixes common; no validation evidence; debug code or TODOs left in'
    },
    'Validation order': {
        'Pass': 'Validates from bottom up (source → transform → snapshot → rollup → presentation); identifies upstream defects before downstream; documents validation steps and results',
        'Moderate': 'Validates some layers but not consistently bottom-up; sometimes trusts downstream without verifying upstream',
        'Fail': 'No systematic validation; trusts output without checking logic; cannot trace validation path'
    },
    'Deployment awareness': {
        'Pass': 'Builds deployment checklists covering preflight, migration, access, rerun; validates against actual deployment; documents rollback plan; uses correct environment connections',
        'Moderate': 'Creates basic deployment checklist; misses some environments or validation steps; rollback plan incomplete',
        'Fail': 'No deployment checklist; deploys without validation; no rollback plan; uses wrong connections'
    },
    'Reviewer handoff': {
        'Pass': 'Produces review packages with purpose, audience, focus, reviewer questions; handoff notes have current state, completed, remains open, next action; passes quality rubric',
        'Moderate': 'Produces handoff notes but missing some sections; review package lacks focus or reviewer questions',
        'Fail': 'No handoff notes or review package; reviewer cannot understand change without clarification'
    },
    'Reusability': {
        'Pass': 'Creates reusable team assets (prompt templates, QC checklists, deployment scripts, handoff templates) that another team member has successfully used; documents usage',
        'Moderate': 'Creates assets but they are not yet used by others; documentation incomplete',
        'Fail': 'No reusable assets created; work is not packaged for reuse'
    },
    'Codex handoff fluency': {
        'Pass': 'Completes Codex Loop (Pull→Summarize→Identify→Execute→Record) in <5 min; handoff passes quality rubric; bounds self-enforced without reminders',
        'Moderate': 'Completes Codex Loop with guidance; handoff needs revision; bounds occasionally need enforcement',
        'Fail': 'Cannot complete Codex Loop independently; handoff fails quality rubric; bounds not self-enforced'
    },
    'Codex bounded use': {
        'Pass': 'Applies bounded Codex use to proven workflows only; evaluates manual vs Codex for each task; documents bounds and rationale',
        'Moderate': 'Uses Codex for some tasks but bounds not consistently documented; manual-vs-Codex evaluation inconsistent',
        'Fail': 'Uses Codex without bounds; lets AI define business logic; no manual-vs-Codex evaluation'
    },
}

# ── Codex gates (matches build_data.py CODEX_GATES) ─────────────────────────
CODEX_GATES = [
    'One end-to-end workflow completed',
    'Business-logic ownership understood',
    'Validation evidence produced without help',
    'Proof tasks completed',
    'One clean reviewable change slice',
    'One reusable team asset created',
    'Manual-vs-Codex comparison completed',
    'All 6 Codex exercises passed',
    'Can explain Bounded Codex rules',
]

# ── Codex Gate Criteria: Measurable acceptance criteria for each gate ────────
# Used by reviewers to verify gate completion with evidence.
CODEX_GATE_CRITERIA = {
    'end_to_end_workflow': {
        'criterion': 'Learner completed full Codex Loop (Pull→Summarize→Identify→Execute→Record) for a real task, documented in handoff note with timestamps',
        'evidence_required': ['handoff_note.md', 'context_pull_log', 'execution_record'],
        'verifier': 'reviewer'
    },
    'business_logic_ownership': {
        'criterion': 'Learner explains business purpose, grain, filters, and validation rules for at least one metric they worked on, without referencing documentation',
        'evidence_required': ['oral_exam_record.md', 'metric_lineage_note.md'],
        'verifier': 'reviewer'
    },
    'validation_evidence': {
        'criterion': 'Learner produced validation evidence (row counts, QC checks, snapshot diffs) for a model change without reviewer prompting',
        'evidence_required': ['qc_evidence_pack.md', 'validation_log'],
        'verifier': 'reviewer'
    },
    'proof_tasks': {
        'criterion': 'All 6 proof tasks (PT1–PT6) submitted with passing reviewer assessment',
        'evidence_required': ['PT1_repository_analysis.md', 'PT2_review_dry_run.md', 'PT3_metric_lineage.md', 'PT4_qc_evidence.md', 'PT5_deployment_rehearsal.md', 'PT6_reviewer_handoff.md'],
        'verifier': 'reviewer'
    },
    'clean_change_slice': {
        'criterion': 'Submitted a reviewable change slice meeting all Code Review Standards checklist items',
        'evidence_required': ['review_package.md', 'changed_files_diff'],
        'verifier': 'reviewer'
    },
    'reusable_asset': {
        'criterion': 'Created a reusable team asset (prompt template, QC checklist, deployment script, handoff template) that another team member has successfully used',
        'evidence_required': ['asset_file', 'usage_testimony.md'],
        'verifier': 'reviewer'
    },
    'manual_vs_codex': {
        'criterion': 'Completed Exercise 5: Manual-vs-Codex Comparison for one defined task with documented results',
        'evidence_required': ['codex_comparison_note.md'],
        'verifier': 'reviewer'
    },
    'codex_exercises': {
        'criterion': 'All 6 Codex exercises passed (Handoff Reading, Context Pull, State Summary, Handoff Creation, Manual-vs-Codex, Bounded Codex Simulation)',
        'evidence_required': ['exercise_1_handoff_reading.md', 'exercise_2_context_pull.md', 'exercise_3_state_summary.md', 'exercise_4_handoff_creation.md', 'exercise_5_manual_vs_codex.md', 'exercise_6_bounded_codex.md'],
        'verifier': 'reviewer'
    },
    'bounded_codex_rules': {
        'criterion': 'Can explain Bounded Codex rules: only proven workflows, manual-vs-Codex evaluation required, bounds self-enforced, handoff quality rubric applies',
        'evidence_required': ['bounded_codex_explanation.md'],
        'verifier': 'reviewer'
    },
}

# ── Proof tasks (matches build_data.py PROOF_TASKS) ─────────────────────────
PROOF_TASKS = {
    'PT1': {'name': 'Repository Analysis Brief', 'due_day': 9, 'week': 2},
    'PT2': {'name': 'Review Workflow Dry Run', 'due_day': 19, 'week': 4},
    'PT3': {'name': 'Metric Lineage Walkthrough', 'due_day': 13, 'week': 3},
    'PT4': {'name': 'QC Evidence Pack', 'due_day': 16, 'week': 3},
    'PT5': {'name': 'Deployment Rehearsal', 'due_day': 18, 'week': 3},
    'PT6': {'name': 'Reviewer Handoff Test', 'due_day': 21, 'week': 4},
}

# ── Proof Task Criteria: Minimum viable artifact definitions ────────────────
# Used by build_data.py to validate proof task completion quality.
PROOF_TASK_CRITERIA = {
    'PT1': {
        'name': 'Repository Analysis Brief',
        'required_sections': [
            'Business Purpose',
            'Dependency Order',
            'Key Inputs & Outputs',
            'Risks Identified',
            'Safe Change Points'
        ],
        'min_content_length': 500,
        'quality_checks': [
            'Must identify at least 3 dependencies in correct order',
            'Must list at least 2 risks with mitigation',
            'Must identify at least 2 safe change points'
        ]
    },
    'PT2': {
        'name': 'Review Workflow Dry Run',
        'required_sections': [
            'Review Scope',
            'Reviewer Path',
            'Dry Run Results',
            'Issues Found',
            'Resolution'
        ],
        'min_content_length': 400,
        'quality_checks': [
            'Must document the review workflow steps followed',
            'Must list at least 1 issue found during dry run',
            'Must show resolution or plan for each issue'
        ]
    },
    'PT3': {
        'name': 'Metric Lineage Walkthrough',
        'required_sections': [
            'Counting Grain',
            'Active-Row Rules',
            'Period Definitions',
            'Calculation Point',
            'Rollup Path',
            'Snapshot Validation'
        ],
        'min_content_length': 600,
        'quality_checks': [
            'Must define grain explicitly (e.g., "one row per customer per month")',
            'Must specify active-row filter logic',
            'Must trace rollup from source to final presentation',
            'Must include snapshot validation results'
        ]
    },
    'PT4': {
        'name': 'QC Evidence Pack',
        'required_sections': [
            'What Was Validated',
            'Validation Results',
            'Edge Cases Tested',
            'Performance Metrics'
        ],
        'min_content_length': 500,
        'quality_checks': [
            'Must include row count comparison (source vs target)',
            'Must test at least 3 edge cases (nulls, duplicates, boundaries)',
            'Must document query performance within SLA'
        ]
    },
    'PT5': {
        'name': 'Deployment Rehearsal',
        'required_sections': [
            'Preflight Checklist',
            'Migration Steps',
            'Access & Security Validation',
            'Rerun Procedure',
            'Rollback Plan'
        ],
        'min_content_length': 500,
        'quality_checks': [
            'Must include complete preflight checklist with pass/fail',
            'Must document migration steps in order',
            'Must specify rollback trigger and procedure'
        ]
    },
    'PT6': {
        'name': 'Reviewer Handoff Test',
        'required_sections': [
            'Handoff Package',
            'Reviewer Feedback',
            'Incorporation Log',
            'Final Handoff'
        ],
        'min_content_length': 400,
        'quality_checks': [
            'Must include reviewer feedback (Pass/Needs Work/Rework)',
            'Must show incorporation of all reviewer comments',
            'Must produce final handoff that passes quality rubric'
        ]
    },
}

# ── Codex Gate Criteria: Measurable acceptance criteria for each gate ────────
# Used by reviewers to verify gate completion with evidence.
CODEX_GATE_CRITERIA = {
    'end_to_end_workflow': {
        'criterion': 'Learner completed full Codex Loop (Pull→Summarize→Identify→Execute→Record) for a real task, documented in handoff note with timestamps',
        'evidence_required': ['handoff_note.md', 'context_pull_log', 'execution_record'],
        'verifier': 'reviewer'
    },
    'business_logic_ownership': {
        'criterion': 'Learner explains business purpose, grain, filters, and validation rules for at least one metric they worked on, without referencing documentation',
        'evidence_required': ['oral_exam_record.md', 'metric_lineage_note.md'],
        'verifier': 'reviewer'
    },
    'validation_evidence': {
        'criterion': 'Learner produced validation evidence (row counts, QC checks, snapshot diffs) for a model change without reviewer prompting',
        'evidence_required': ['qc_evidence_pack.md', 'validation_log'],
        'verifier': 'reviewer'
    },
    'proof_tasks': {
        'criterion': 'All 6 proof tasks (PT1–PT6) submitted with passing reviewer assessment',
        'evidence_required': ['PT1_repository_analysis.md', 'PT2_review_dry_run.md', 'PT3_metric_lineage.md', 'PT4_qc_evidence.md', 'PT5_deployment_rehearsal.md', 'PT6_reviewer_handoff.md'],
        'verifier': 'reviewer'
    },
    'clean_change_slice': {
        'criterion': 'Submitted a reviewable change slice meeting all Code Review Standards checklist items',
        'evidence_required': ['review_package.md', 'changed_files_diff'],
        'verifier': 'reviewer'
    },
    'reusable_asset': {
        'criterion': 'Created a reusable team asset (prompt template, QC checklist, deployment script, handoff template) that another team member has successfully used',
        'evidence_required': ['asset_file', 'usage_testimony.md'],
        'verifier': 'reviewer'
    },
    'manual_vs_codex': {
        'criterion': 'Completed Exercise 5: Manual-vs-Codex Comparison for one defined task with documented results',
        'evidence_required': ['codex_comparison_note.md'],
        'verifier': 'reviewer'
    },
    'codex_exercises': {
        'criterion': 'All 6 Codex exercises passed (Handoff Reading, Context Pull, State Summary, Handoff Creation, Manual-vs-Codex, Bounded Codex Simulation)',
        'evidence_required': ['exercise_1_handoff_reading.md', 'exercise_2_context_pull.md', 'exercise_3_state_summary.md', 'exercise_4_handoff_creation.md', 'exercise_5_manual_vs_codex.md', 'exercise_6_bounded_codex.md'],
        'verifier': 'reviewer'
    },
    'bounded_codex_rules': {
        'criterion': 'Can explain Bounded Codex rules: only proven workflows, manual-vs-Codex evaluation required, bounds self-enforced, handoff quality rubric applies',
        'evidence_required': ['bounded_codex_explanation.md'],
        'verifier': 'reviewer'
    },
}

# ── Classification progression milestones ────────────────────────────────────
CLASSIFICATION_MILESTONES = [
    (1, 'Foundational'),
    (8, 'Developing'),
    (18, 'Operational'),
    (25, 'Ready For Codex Acceleration'),
]

# ── Level Competency Gates: Requirements to advance to next level ────────────
# Each level requires minimum competency across scorecard, proof tasks, gates, and categories.
LEVEL_COMPETENCY_GATES = {
    1: {  # Foundation → Development
        'min_scorecard_pass_rate': 0.5,      # 4/7 areas Pass
        'min_proof_tasks': 2,                # PT1, PT3
        'min_codex_gates': 2,                # end_to_end_workflow, business_logic_ownership
        'min_categories_covered': 5,
    },
    2: {  # Development → Operational
        'min_scorecard_pass_rate': 0.7,      # 5/7 areas Pass
        'min_proof_tasks': 4,                # PT1, PT3, PT4, PT5
        'min_codex_gates': 4,                # + validation_evidence, clean_change_slice
        'min_categories_covered': 7,
    },
    3: {  # Operational → Mastery
        'min_scorecard_pass_rate': 0.85,     # 6/7 areas Pass
        'min_proof_tasks': 6,                # All PTs
        'min_codex_gates': 6,                # All gates
        'min_categories_covered': 8,
    },
}

# ── Primary track rotation (matches curriculum tags) ─────────────────────────
TRACK_ROTATION = {
    27: 'Pyramid operations',
    28: 'Codex productivity',
}

# ── Page mapping: file path patterns → dashboard page id ─────────────────────────────────
PAGE_MAP = [
    ('daily',       ['action/notes/', 'notes/']),
    ('evidence',    ['action/evidence/', 'evidence/']),
    ('reports',     ['action/reports/', 'reports/']),
    ('scorecard',   []),  # derived from note content, not direct file map
    ('proof-tasks', []),  # derived from note content
    ('classification', []),
    ('codex-gate',  []),
    ('templates',   ['action/templates/', 'templates/']),
    ('scripts',     ['action/scripts/', 'scripts/']),
    ('dashboard',   ['action/dashboard/', 'dashboard/']),
    ('review',      ['review/']),
    ('source',      ['source/']),
]

# ── Learning Categories (aligned with LEARNING_CATEGORIES.md) ──────────────
CATEGORIES = {
    'ai-copilot': {
        'id': 'ai-copilot',
        'emoji': '🤖',
        'label': 'AI & Copilot',
        'description': 'Chat modes, prompt engineering, custom instructions, context management, tool use. Learners practice mode selection, prompt structure, and drift avoidance.',
        'weeks': [1, 2, 3, 4],
        'skills': ['Mode selection', 'Prompt structure', 'Instruction files', 'Prompt files', 'Context management', 'Drift avoidance'],
    },
    'codex': {
        'id': 'codex',
        'emoji': '⚡',
        'label': 'Codex Productivity',
        'description': 'Workflow orientation, handoff fluency, context synthesis, targeted AI use, bounded automation, Codex loop mastery (Pull → Summarize → Identify → Execute → Record).',
        'weeks': [1, 2, 3, 4],
        'skills': ['Codex Loop', 'Handoff extraction', 'Context pull', 'Bounded prompt design', 'Manual-vs-Codex evaluation'],
    },
    'pyramid': {
        'id': 'pyramid',
        'emoji': '🏗️',
        'label': 'Pyramid Platform',
        'description': 'Model logic, deployment sequencing, QC, security, artifact movement, reviewer access. Learners build deployment checklists and QC evidence packs.',
        'weeks': [2, 3, 4],
        'skills': ['Model lineage', 'Deployment preflight', 'Artifact migration', 'QC execution', 'Access policy'],
    },
    'bi-judgment': {
        'id': 'bi-judgment',
        'emoji': '📊',
        'label': 'BI Judgment',
        'description': 'Business reasoning, metric definition, grain, validation, trusted delivery, tool-agnostic thinking. Learners articulate business questions and validate metrics.',
        'weeks': [1, 2, 3, 4],
        'skills': ['Business question articulation', 'Metric selection', 'Grain/filter/exclusion definition', 'Validation evidence'],
    },
    'data-lineage': {
        'id': 'data-lineage',
        'emoji': '🔗',
        'label': 'Data & Lineage',
        'description': 'Source-to-model lineage, aggregation, rollups, snapshots, dependency mapping, row ownership. Learners trace dependencies and map data flows.',
        'weeks': [1, 2, 3],
        'skills': ['Dependency tracing', 'Row ownership identification', 'Deduplication logic', 'Aggregation boundaries'],
    },
    'delivery-handoff': {
        'id': 'delivery-handoff',
        'emoji': '📦',
        'label': 'Delivery & Handoff',
        'description': 'Change isolation, review packages, handoff drafting, reusable assets, reviewer readiness. Learners prepare change charters and review packages.',
        'weeks': [3, 4],
        'skills': ['Change-slice scoping', 'Review package preparation', 'Handoff note generation', 'Asset creation'],
    },
    'readiness': {
        'id': 'readiness',
        'emoji': '🧠',
        'label': 'Retention & Readiness',
        'description': 'Weekly retention checks, scorecards, proof tasks, Codex Gate, readiness classification. Learners self-assess across all tracks and track progress.',
        'weeks': [1, 2, 3, 4],
        'skills': ['Cross-track recall', 'Self-assessment', 'Proof task tracking', 'Gate readiness evaluation'],
    },
    'team-communication': {
        'id': 'team-communication',
        'emoji': '💬',
        'label': 'Team Communication & Task Management',
        'description': 'Team collaboration, status communication, task tracking, feedback, blocker escalation, shared workflows. Learners practise daily standups, status reporting, and feedback incorporation.',
        'weeks': [1, 2, 3, 4],
        'skills': ['Daily standup updates', 'Status reporting', 'Asking for help effectively', 'Giving/receiving feedback', 'Task tracking with GitHub Issues', 'Blocker communication', 'Team decision documentation'],
    },
}

# ── Emoji tag → category id mapping (used by curriculum tags) ──
TAG_TO_CATEGORY_MAP = {
    '🤖 AI': 'ai-copilot',
    '⚡ Codex': 'codex',
    '🏗️ Pyr': 'pyramid',
    '📊 BI': 'bi-judgment',
    '🔗 Data': 'data-lineage',
    '📦 Del': 'delivery-handoff',
    '🧠 Ret': 'readiness',
    '💬 Team': 'team-communication',
}

# ── Source file → category mapping (inferred from path/filename patterns) ──
SOURCE_CATEGORY_MAP = {
    # AI & Copilot
    'Copilot Reference for MUE.md': ['ai-copilot'],
    'Custom Workflows for MUE.md': ['ai-copilot', 'delivery-handoff'],
    'Copilot Best Practices Guide.md': ['ai-copilot'],
    # Codex Productivity
    'Codex Productivity Training Handoff.md': ['codex'],
    'Codex Productivity.md': ['codex'],
    'Agentic Workflow Patterns.md': ['codex', 'delivery-handoff'],
    # Pyramid
    'Pyramid Platform Reference.md': ['pyramid'],
    # BI Judgment
    'Pyramid, Codex, and BI Judgment Daily Execution Guide.txt': ['pyramid', 'codex', 'bi-judgment'],
    'Pyramid, Codex, and BI Judgment Daily Working Template.txt': ['pyramid', 'codex', 'bi-judgment'],
    'Pyramid, Codex, and BI Judgment Readiness Plan.md': ['pyramid', 'codex', 'bi-judgment', 'readiness'],
    # Data & Lineage
    # (embedded in onboarding map and category notes)
    # Delivery & Handoff
    'Code Review and Handoff Standards.md': ['delivery-handoff', 'codex'],
    'CONTRIBUTING.md': ['delivery-handoff'],
    # Readiness
    'GitHub Well-Architected Principles.md': ['pyramid', 'bi-judgment', 'delivery-handoff'],
    '4-Week Onboarding Map.md': ['ai-copilot', 'codex', 'pyramid', 'bi-judgment', 'data-lineage', 'delivery-handoff', 'readiness', 'team-communication'],
    'LEARNING_CATEGORIES.md': ['ai-copilot', 'codex', 'pyramid', 'bi-judgment', 'data-lineage', 'delivery-handoff', 'readiness', 'team-communication'],
    'BI Academic Framework.md': ['ai-copilot', 'codex', 'pyramid', 'bi-judgment', 'data-lineage', 'delivery-handoff', 'readiness'],
}

# ── 4-Level Curriculum Framework ──────────────────────────────────────────
# Each level has its own independent 28-working-day curriculum across all 8 categories.
# Level 1 (Foundation) is for complete amateurs; Level 4 (Mastery) for expert-ready.

LEVELS = {
    1: {
        'id': 1,
        'label': 'Foundation',
        'emoji': '🌱',
        'subtitle': 'For complete amateurs — no prior experience needed. Learn vocabulary and basic concepts with maximum guidance.',
        'color': '#4CAF50',
    },
    2: {
        'id': 2,
        'label': 'Development',
        'emoji': '🌿',
        'subtitle': 'For learners with some experience — build competence through guided application and practice.',
        'color': '#2196F3',
    },
    3: {
        'id': 3,
        'label': 'Operational',
        'emoji': '🌳',
        'subtitle': 'For confident practitioners — deep concepts with significant independence and quality focus.',
        'color': '#FF9800',
    },
    4: {
        'id': 4,
        'label': 'Mastery',
        'emoji': '🏆',
        'subtitle': 'For expert-ready learners — advanced optimization, automation, and strategic thinking with full autonomy.',
        'color': '#9C27B0',
    },
}

# ── Level-specific category content ───────────────────────────────────────
# Each level adjusts the 8 learning categories with appropriate descriptions,
# skills, and weekly coverage for that proficiency tier.
LEVEL_CATEGORIES = {
    1: {
        'ai-copilot': {
            'description': 'What is an AI coding assistant? Learn to chat, ask simple questions, and understand basic responses. No prior experience needed — just curiosity.',
            'skills': ['Basic chat interaction', 'Simple question asking', 'Understanding AI responses', 'AI assistant overview'],
            'weeks': [1, 2, 3, 4],
        },
        'codex': {
            'description': 'Introduction to the Codex workflow. Learn what the Codex Loop is and practice following simple guided prompts step by step.',
            'skills': ['Codex Loop vocabulary', 'Following guided prompts', 'Basic observation skills', 'Simple note-taking'],
            'weeks': [1, 2, 3, 4],
        },
        'pyramid': {
            'description': 'What is a data platform? Learn basic vocabulary — models, deployments, QC — and see examples of each. Build awareness of the analytics ecosystem.',
            'skills': ['Platform vocabulary', 'Model awareness', 'Deployment concept', 'QC overview'],
            'weeks': [2, 3, 4],
        },
        'bi-judgment': {
            'description': 'What is business intelligence? Learn to identify simple business questions and understand what metrics are at a basic level.',
            'skills': ['BI vocabulary', 'Business question awareness', 'Metric concept', 'Simple data observation'],
            'weeks': [1, 2, 3, 4],
        },
        'data-lineage': {
            'description': 'What is data lineage? Learn where data comes from and where it goes. Build simple dependency awareness and follow data flows.',
            'skills': ['Lineage vocabulary', 'Source-to-destination concept', 'Simple dependency awareness', 'Data flow overview'],
            'weeks': [1, 2, 3],
        },
        'delivery-handoff': {
            'description': 'What does it mean to deliver work? Learn about change tracking, review concepts, and why communication matters.',
            'skills': ['Delivery vocabulary', 'Change awareness', 'Review concept introduction', 'Communication basics'],
            'weeks': [3, 4],
        },
        'readiness': {
            'description': 'How do we track learning? Learn about progress tracking, simple check-ins, and basic self-assessment of your own work.',
            'skills': ['Progress tracking', 'Simple check-ins', 'Basic self-assessment', 'Learning awareness'],
            'weeks': [1, 2, 3, 4],
        },
        'team-communication': {
            'description': 'What does it mean to work with a team? Learn how to give a standup update, report status, and ask for help when you need it.',
            'skills': ['Standup introduction', 'Status updates', 'Asking for help', 'Listening to feedback', 'Task awareness'],
            'weeks': [1, 2, 3, 4],
        },
    },
    2: {
        'ai-copilot': {
            'description': 'Choose the right chat mode for the task. Write clear, structured prompts. Understand context management basics and when to use each tool.',
            'skills': ['Mode selection', 'Prompt structure', 'Context management', 'Tool introduction'],
            'weeks': [1, 2, 3, 4],
        },
        'codex': {
            'description': 'Practice the Codex Loop with real tasks. Learn handoff extraction, context pull techniques, and bounded prompt design for safe automation.',
            'skills': ['Handoff extraction', 'Context pull', 'Bounded prompt design', 'Codex Loop practice'],
            'weeks': [1, 2, 3, 4],
        },
        'pyramid': {
            'description': 'Build deployment checklists. Practice preflight checks before releases. Learn artifact migration basics between environments.',
            'skills': ['Model lineage', 'Deployment preflight', 'Artifact migration', 'QC checklist creation'],
            'weeks': [2, 3, 4],
        },
        'bi-judgment': {
            'description': 'Articulate clear business questions. Select appropriate metrics for each scenario. Start validating data outputs against expectations.',
            'skills': ['Business question articulation', 'Metric selection', 'Basic validation', 'Output type selection'],
            'weeks': [1, 2, 3, 4],
        },
        'data-lineage': {
            'description': 'Trace dependencies from source to model. Identify row ownership patterns. Understand basic deduplication and its importance.',
            'skills': ['Dependency tracing', 'Row ownership', 'Deduplication basics', 'Aggregation awareness'],
            'weeks': [1, 2, 3],
        },
        'delivery-handoff': {
            'description': 'Scope clean change slices for review. Prepare review packages with change context. Generate handoff notes that reviewers can act on.',
            'skills': ['Change-slice scoping', 'Review package prep', 'Handoff note creation', 'Basic asset creation'],
            'weeks': [3, 4],
        },
        'readiness': {
            'description': 'Track progress across all learning tracks. Practice accurate self-assessment. Complete proof tasks and build gate awareness.',
            'skills': ['Cross-track recall', 'Self-assessment practice', 'Proof task completion', 'Gate awareness'],
            'weeks': [1, 2, 3, 4],
        },
        'team-communication': {
            'description': 'Give regular standup updates and status reports. Practise asking for help effectively and receiving feedback constructively. Start tracking tasks in a shared board.',
            'skills': ['Daily standup updates', 'Status reporting', 'Asking for help effectively', 'Receiving feedback', 'Task board basics'],
            'weeks': [1, 2, 3, 4],
        },
    },
    3: {
        'ai-copilot': {
            'description': 'Create instruction files and prompt files for consistent results. Manage context across long sessions. Detect and avoid prompt drift.',
            'skills': ['Instruction files', 'Prompt files', 'Context windows', 'Drift avoidance', 'Advanced mode use'],
            'weeks': [1, 2, 3, 4],
        },
        'codex': {
            'description': 'Master the Codex Loop unassisted in under 5 minutes. Apply quality rubrics to handoffs. Evaluate manual vs Codex approaches systematically.',
            'skills': ['Codex Loop mastery', 'Handoff quality rubric', 'Manual-vs-Codex evaluation', 'Pattern library use'],
            'weeks': [1, 2, 3, 4],
        },
        'pyramid': {
            'description': 'Execute QC independently with full evidence packs. Manage access policies and roles. Set up reviewer paths for smooth handoffs.',
            'skills': ['QC execution', 'Access policy management', 'Reviewer path setup', 'Security awareness'],
            'weeks': [2, 3, 4],
        },
        'bi-judgment': {
            'description': 'Define grain, filters, and exclusions precisely. Produce validation evidence that stands up to scrutiny. Select optimal output types confidently.',
            'skills': ['Grain/filter/exclusion definition', 'Validation evidence', 'Output type mastery', 'Cross-tool thinking'],
            'weeks': [1, 2, 3, 4],
        },
        'data-lineage': {
            'description': 'Apply deduplication logic correctly. Define aggregation boundaries and understand their impact. Identify and mitigate double-counting risks.',
            'skills': ['Deduplication logic', 'Aggregation boundaries', 'Double-counting risk', 'Dependency mapping'],
            'weeks': [1, 2, 3],
        },
        'delivery-handoff': {
            'description': 'Generate professional handoff notes that pass quality rubrics. Create reusable assets (prompts, checklists, templates). Set up reviewer workflows.',
            'skills': ['Handoff note generation', 'Reusable asset creation', 'Reviewer workflow', 'Change impact analysis'],
            'weeks': [3, 4],
        },
        'readiness': {
            'description': 'Track proof tasks rigorously to completion. Evaluate gate readiness against all criteria. Drive your own progress independently.',
            'skills': ['Proof task tracking', 'Gate readiness evaluation', 'Self-directed progress', 'Quality assessment'],
            'weeks': [1, 2, 3, 4],
        },
        'team-communication': {
            'description': 'Lead standups and status updates. Give and receive feedback professionally. Track and prioritise tasks across the team. Escalate blockers promptly and document team decisions.',
            'skills': ['Standup leadership', 'Giving/receiving feedback', 'Task prioritisation', 'Blocker escalation', 'Team decision documentation'],
            'weeks': [1, 2, 3, 4],
        },
    },
    4: {
        'ai-copilot': {
            'description': 'Design custom agent workflows and sophisticated prompt systems. Optimize team-wide AI usage patterns. Define AI strategy and best practices.',
            'skills': ['Custom workflow design', 'Advanced prompt engineering', 'Team optimization', 'AI strategy'],
            'weeks': [1, 2, 3, 4],
        },
        'codex': {
            'description': 'Automate Codex workflows end to end. Optimize the loop for speed and quality. Teach others. Design evaluation frameworks for Codex proficiency.',
            'skills': ['Workflow automation', 'Codex optimization', 'Teaching and mentoring', 'Evaluation design'],
            'weeks': [1, 2, 3, 4],
        },
        'pyramid': {
            'description': 'Own the full deployment pipeline end to end. Design security architecture. Define platform strategy and automation roadmaps.',
            'skills': ['Full pipeline ownership', 'Security architecture', 'Platform strategy', 'Deployment automation'],
            'weeks': [2, 3, 4],
        },
        'bi-judgment': {
            'description': 'Design strategic metrics that drive decisions. Validate insights across domains and systems. Deliver trusted BI independently with executive-ready communication.',
            'skills': ['Strategic metric design', 'Cross-domain validation', 'Trusted delivery', 'BI strategy'],
            'weeks': [1, 2, 3, 4],
        },
        'data-lineage': {
            'description': 'Design data architecture for lineage transparency. Automate lineage tracking and dependency management. Implement quality monitoring systems.',
            'skills': ['Data architecture', 'Lineage automation', 'Quality monitoring', 'Dependency management'],
            'weeks': [1, 2, 3],
        },
        'delivery-handoff': {
            'description': 'Design review programs and quality standards. Manage asset libraries for team reuse. Drive process improvement through metrics and feedback.',
            'skills': ['Review program design', 'Asset library management', 'Process improvement', 'Quality standards'],
            'weeks': [3, 4],
        },
        'readiness': {
            'description': 'Evaluate program-level effectiveness. Improve the curriculum based on outcomes. Mentor others through their readiness journey. Drive quality assurance.',
            'skills': ['Program evaluation', 'Curriculum improvement', 'Mentoring', 'Quality assurance'],
            'weeks': [1, 2, 3, 4],
        },
        'team-communication': {
            'description': 'Lead team communication strategy. Design feedback frameworks and escalation protocols. Mentor others in effective collaboration. Drive team productivity through shared workflows.',
            'skills': ['Communication strategy', 'Feedback framework design', 'Escalation protocol', 'Collaboration mentoring', 'Workflow optimisation'],
            'weeks': [1, 2, 3, 4],
        },
    },
}

# ── Page classification helpers ────────────────────────────────────────────

def classify_path_to_page(rel_path):
    """Map a file path (relative to repo root) to a dashboard page id."""
    p = rel_path.replace('\\', '/')
    for page_id, patterns in PAGE_MAP:
        for pat in patterns:
            if pat in p or p.startswith(pat):
                return page_id
    return 'other'

# ── Legacy data functions (unchanged from original) ────────────────────────

def parse_date_from_filename(filename):
    basename = os.path.basename(filename).replace('.md', '')
    try:
        return str(datetime.strptime(basename, '%Y-%m-%d').date())
    except ValueError:
        return None


def parse_note(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    note = {
        'id': os.path.basename(filepath).replace('.md', ''),
        'filename': os.path.basename(filepath),
        'date': parse_date_from_filename(filepath),
        'day_number': None,
        'classification': None,
        'primary_track': None,
        'required_artifact': None,
        'what_learned': None,
        'evidence_produced': None,
        'what_remains': None,
        'next_step': None,
        'week_number': None,
        'scorecard': {},
        'codex_gate': {},
    }

    m = PAT_DAY_NUMBER.search(content)
    if m:
        note['day_number'] = int(m.group(1))

    m = PAT_CLASSIFICATION.search(content)
    if m:
        note['classification'] = m.group(1).strip()

    m = PAT_PRIMARY_TRACK.search(content)
    if m:
        note['primary_track'] = m.group(1).strip()

    m = PAT_ARTIFACT.search(content)
    if m:
        note['required_artifact'] = m.group(1).strip()

    for pat, key in [
        (PAT_LEARNED, 'what_learned'),
        (PAT_EVIDENCE, 'evidence_produced'),
        (PAT_REMAINS, 'what_remains'),
        (PAT_NEXT_STEP, 'next_step'),
    ]:
        m = pat.search(content)
        if m:
            note[key] = m.group(1).strip()

    m = PAT_WEEK_NUMBER.search(content)
    if m:
        note['week_number'] = int(m.group(1))

    m = PAT_LEVEL.search(content)
    if m:
        note['level'] = int(m.group(1))
    else:
        # Backward compatible: notes without Level field default to Level 1
        note['level'] = 1

    for area in SCORE_AREAS:
        p = re.compile(rf'{re.escape(area)}:\s*(Pass|Moderate|Fail|Unscored)', re.IGNORECASE)
        m = p.search(content)
        if m:
            safe_key = area.lower().replace(' ', '_').replace('(', '').replace(')', '')
            note['scorecard'][safe_key] = m.group(1).capitalize()

    for gate in CODEX_GATES:
        p = re.compile(rf'{re.escape(gate)}:\s*(Yes|No)', re.IGNORECASE)
        m = p.search(content)
        if m:
            safe_key = gate.lower().replace(' ', '_').replace('(', '').replace(')', '')
            note['codex_gate'][safe_key] = m.group(1).capitalize()

    return note


def scan_evidence():
    files = []
    if not os.path.isdir(EVIDENCE_DIR):
        return files
    for root, dirs, fnames in os.walk(EVIDENCE_DIR):
        for f in fnames:
            if f == '.gitkeep':
                continue
            fp = os.path.join(root, f)
            rel = os.path.relpath(fp, EVIDENCE_DIR)
            files.append({
                'path': rel,
                'size': os.path.getsize(fp),
                'modified': datetime.fromtimestamp(os.path.getmtime(fp)).isoformat(),
            })
    files.sort(key=lambda x: x['modified'], reverse=True)
    return files


def scan_reports():
    files = []
    if not os.path.isdir(REPORTS_DIR):
        return files
    pattern = os.path.join(REPORTS_DIR, '*.md')
    for fp in sorted(glob.glob(pattern)):
        if os.path.basename(fp) == '.gitkeep':
            continue
        files.append({
            'path': os.path.basename(fp),
            'size': os.path.getsize(fp),
            'modified': datetime.fromtimestamp(os.path.getmtime(fp)).isoformat(),
        })
    return files


def compute_summary(notes):
    if not notes:
        # Detect earliest artifact even with no notes (evidence/reports may exist)
        earliest_artifact = detect_earliest_learner_artifact()
        # Build empty level progression for consistent dashboard state
        empty_progression = detect_level_progression([])
        return {
            'total_days': 0,
            'unique_weeks': 0,
            'latest_classification': '—',
            'classification_sequence': [],
            'evidence_count': 0,
            'completed_tracks': {},
            'scorecard_trend': {},
            'codex_gate_status': {},
            'proof_tasks': {},
            'current_week': 0,
            'curriculum_start_date': earliest_artifact,  # still detect from evidence/reports
            'curriculum_current_day': 0,
            'calendar_days_elapsed': 0,
            'working_days_elapsed': 0,
            'calendar_status': 'no_data',
            'week_progress': [],
            'learner_level': 1,
            'level_progression': empty_progression,
            'earliest_artifact_date': earliest_artifact,
            'today': date.today().isoformat(),
        }

    cls_seq = []
    for n in notes:
        if n['classification']:
            cls_seq.append({
                'day': n['day_number'],
                'date': n['date'],
                'classification': n['classification'],
            })

    days_per_week = defaultdict(int)
    for n in notes:
        if n['week_number']:
            days_per_week[n['week_number']] += 1
        elif n['day_number']:
            w = (n['day_number'] - 1) // 5 + 1
            days_per_week[w] += 1

    scorecard_trend = defaultdict(list)
    for n in notes:
        if n['scorecard']:
            for area, score in n['scorecard'].items():
                scorecard_trend[area].append({
                    'day': n['day_number'],
                    'date': n['date'],
                    'score': score,
                })

    codex_gate_status = {}
    for n in reversed(notes):
        if n['codex_gate']:
            codex_gate_status = n['codex_gate']
            break

    completed_tracks = defaultdict(int)
    for n in notes:
        if n['primary_track']:
            completed_tracks[n['primary_track']] += 1

    proof_tasks = {}
    for pt_id, pt_desc in PROOF_TASKS:
        proof_tasks[pt_id] = {
            'id': pt_id,
            'description': pt_desc,
            'found': False,
            'days': [],
        }
    for n in notes:
        fpath = n.get('filepath', n.get('id', ''))
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            content = ''
        for pt_id, pt_desc in PROOF_TASKS:
            if re.search(f'{pt_id}|{re.escape(pt_desc)}', content, re.IGNORECASE):
                proof_tasks[pt_id]['found'] = True
                if n['day_number']:
                    proof_tasks[pt_id]['days'].append(n['day_number'])

    # ── Dynamic level progression detection ──
    # Primary method: detect start dates from earliest learner artifacts.
    # This replaces the old config-first approach with true dynamic detection
    # based on when the learner first submitted curriculum fulfillment artifacts.
    today = date.today()
    level_progression = detect_level_progression(notes)
    earliest_artifact = detect_earliest_learner_artifact()

    # For backward compatibility, populate curriculum_start_date from detection.
    # Priority: 1) learner_config.json override, 2) earliest artifact, 3) level_1 start
    curriculum_start_date = None
    _start_source = 'auto_detected_from_artifacts'

    # 1) Check learner_config.json for manual override (kept for backwards compat)
    if os.path.exists(LEARNER_CONFIG_PATH):
        try:
            with open(LEARNER_CONFIG_PATH, 'r', encoding='utf-8') as f:
                lcfg = json.load(f)
            cfg_date = lcfg.get('curriculum_start_date')
            if cfg_date:
                datetime.strptime(cfg_date, '%Y-%m-%d')  # validate format
                curriculum_start_date = cfg_date
                _start_source = 'learner_config'
                print(f'  📅 Using learner-configured start date (override): {curriculum_start_date}')
        except (json.JSONDecodeError, ValueError, OSError) as e:
            print(f'  ⚠️  Warning: could not read learner_config.json: {e}')

    # 2) Auto-detect from earliest artifact across all learner dirs
    if not curriculum_start_date and earliest_artifact:
        curriculum_start_date = earliest_artifact
        _start_source = 'auto_detected_from_artifacts'
        print(f'  📅 Dynamic start date from earliest learner artifact: {curriculum_start_date}')

    # 3) Fall back to Level 1 note detection
    if not curriculum_start_date:
        l1_info = level_progression.get('levels', {}).get(1, {})
        if l1_info.get('start_date'):
            curriculum_start_date = l1_info['start_date']
            _start_source = 'auto_detected_from_level_1_notes'
            print(f'  📅 Fallback start date from Level 1 notes: {curriculum_start_date}')

    # If we have a config override, propagate it into level_progression
    if _start_source == 'learner_config' and curriculum_start_date:
        lvl_info = level_progression.get('levels', {}).get(1, {})
        if lvl_info:
            if not lvl_info['start_date']:
                lvl_info['start_date'] = curriculum_start_date
        level_progression['overall_start_date'] = curriculum_start_date

    curriculum_current_day = max((n.get('day_number') or 0) for n in notes)

    calendar_days_elapsed = 0
    working_days_elapsed = 0
    if curriculum_start_date:
        try:
            start = datetime.strptime(curriculum_start_date, '%Y-%m-%d').date()
            calendar_days_elapsed = (today - start).days
            current = start
            while current <= today:
                if current.weekday() < 5:
                    working_days_elapsed += 1
                current += timedelta(days=1)
        except Exception:
            pass

    # Determine calendar status
    if curriculum_current_day == 0:
        calendar_status = 'not_started'
    elif curriculum_current_day >= working_days_elapsed + 2:
        calendar_status = 'ahead'
    elif curriculum_current_day >= working_days_elapsed - 2:
        calendar_status = 'on_track'
    else:
        calendar_status = 'behind'

    # Week-by-week progress with real calendar dates
    week_progress = []
    for w in range(1, 5):
        week_start_day = (w - 1) * 7 + 1
        week_end_day = min(w * 7, 28)
        days_in_week = week_end_day - week_start_day + 1
        days_completed = sum(1 for n in notes if n.get('day_number') and week_start_day <= n['day_number'] <= week_end_day)
        cal_start_str = ''
        cal_end_str = ''
        if curriculum_start_date:
            try:
                start = datetime.strptime(curriculum_start_date, '%Y-%m-%d').date()
                cal_start = start + timedelta(days=(w-1)*7)
                cal_end = cal_start + timedelta(days=6)
                cal_start_str = cal_start.isoformat()
                cal_end_str = cal_end.isoformat()
            except Exception:
                pass
        week_progress.append({
            'week': w,
            'days_completed': days_completed,
            'days_in_week': days_in_week,
            'pct': round(days_completed / days_in_week * 100, 1) if days_in_week else 0,
            'calendar_start': cal_start_str,
            'calendar_end': cal_end_str,
        })