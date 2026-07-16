"""
action/dashboard/build_data.py
Third-Party Review Dashboard builder for MUE.
Scans action/, source/, and review/ then generates data.json consumed by
dashboard.html. Tracks per-page version changes, git diffs, source criteria
alignment, and provides version-based review metadata.

🔒 ONE-WAY SYNC SAFETY:
  - This script READS from action/, source/, and review/ — it only WRITES to
    action/dashboard/data.json (a generated build artifact, not learner work).
  - It NEVER writes to review/ or modifies learner files in action/.
  - Synced reviews from review/reviews.json are read-only and merged with
    localStorage reviews in the dashboard for display only.

Usage:
    python action/dashboard/build_data.py
    # Output: action/dashboard/data.json
"""
import glob
import json
import os
import re
import subprocess
from collections import defaultdict
from datetime import date, datetime, timedelta

DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))
ACTION_DIR = os.path.abspath(os.path.join(DASHBOARD_DIR, '..'))
NOTES_DIR = os.path.join(ACTION_DIR, 'notes')
EVIDENCE_DIR = os.path.join(ACTION_DIR, 'evidence')
REPORTS_DIR = os.path.join(ACTION_DIR, 'reports')
OUTPUT_PATH = os.path.join(DASHBOARD_DIR, 'data.json')

# Archive directories for completed learner work
NOTES_ARCHIVE_DIR = os.path.join(ACTION_DIR, 'archive', 'notes')
EVIDENCE_ARCHIVE_DIR = os.path.join(ACTION_DIR, 'archive', 'evidence')
REPORTS_ARCHIVE_DIR = os.path.join(ACTION_DIR, 'archive', 'reports')

# Parent repo root (for review/ dir and git root)
REPO_ROOT = os.path.abspath(os.path.join(ACTION_DIR, '..'))
REVIEW_DIR = os.path.join(REPO_ROOT, 'review')
SOURCE_DIR = os.path.join(REPO_ROOT, 'source')

# Learner config — dynamic start date override
LEARNER_CONFIG_PATH = os.path.join(ACTION_DIR, 'learner_config.json')

# ── Page mapping: file path patterns → dashboard page id ──
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

# ── Regex patterns ──────────────────────────────────────────────────────────
PAT_CLASSIFICATION = re.compile(
    r'Classification:\*?\*?\s*(Foundational|Developing|Operational|Ready for Codex Acceleration)',
    re.IGNORECASE,
)
PAT_PRIMARY_TRACK = re.compile(
    r'Primary track:\*?\*?\s*(Pyramid operations|Codex productivity|BI judgment)',
    re.IGNORECASE,
)
PAT_DAY_NUMBER = re.compile(r'Day\*?\*?\s*(\d+)')
PAT_ARTIFACT = re.compile(r'Required Artifact:\*?\*?\s*(.+)', re.IGNORECASE)
PAT_LEARNED = re.compile(r'What I learned today:\*?\*?\s*(.+)', re.IGNORECASE)
PAT_EVIDENCE = re.compile(r'What evidence I produced:\*?\*?\s*(.+)', re.IGNORECASE)
PAT_REMAINS = re.compile(r'What remains open:\*?\*?\s*(.+)', re.IGNORECASE)
PAT_NEXT_STEP = re.compile(r'Next narrow step:\*?\*?\s*(.+)', re.IGNORECASE)
PAT_WEEK_NUMBER = re.compile(r'Week Number:\*?\*?\s*(\d+)')
PAT_LEVEL = re.compile(r'Level:\*?\*?\s*(\d+)')
PAT_CATEGORY_TAGS = re.compile(r'Category Tags:\*?\*?\s*(.+)', re.IGNORECASE)

# ── Level framework ────────────────────────────────────────────────────────
LEVEL_DAYS = 28  # working days per curriculum level


# ── Level progression helpers ─────────────────────────────────────────────
def detect_earliest_learner_artifact():
    """
    Scan all learner artifact directories (notes, evidence, reports) in both
    action/ and archive/ to find the earliest date any artifact was created.
    
    This is the true dynamic start date — determined by when the learner
    first provided curriculum fulfillment input, not by a config file.
    """
    earliest = None
    
    # 1) Note filenames are YYYY-MM-DD.md — parse directly
    #    Strip known prefixes (tpl_) before date parsing
    for d in [NOTES_DIR, NOTES_ARCHIVE_DIR]:
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f.endswith('.md') and not f.startswith('.') and not f.startswith('tpl_'):
                try:
                    basename = f.replace('.md', '')
                    dt = datetime.strptime(basename, '%Y-%m-%d').date()
                    if earliest is None or dt < earliest:
                        earliest = dt
                except ValueError:
                    pass
    
    # 2) Evidence & report files — use modification time as proxy
    for d in [EVIDENCE_DIR, REPORTS_DIR, EVIDENCE_ARCHIVE_DIR, REPORTS_ARCHIVE_DIR]:
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f == '.gitkeep' or f.startswith('.'):
                continue
            fp = os.path.join(d, f)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(fp)).date()
                if earliest is None or mtime < earliest:
                    earliest = mtime
            except Exception:
                pass
    
    return earliest.isoformat() if earliest else None


def detect_level_progression(notes):
    """
    Detect level progression from learner notes.
    
    Each level has LEVEL_DAYS (28) working days of curriculum content.
    Level 1 starts on the date of the earliest learner artifact.
    Level N+1 can only begin after Level N is completed (all 28 days done).
    
    Returns a dict:
    {
        'current_level': 1..4,
        'overall_start_date': '2026-06-15' or None,
        'levels': {
            1: { 'start_date': ..., 'completion_date': ..., 'days_completed': N,
                 'days_required': 28, 'is_unlocked': True, 'is_completed': bool,
                 'in_progress': bool },
            2: { ... },
            3: { ... },
            4: { ... },
        }
    }
    """
    from collections import defaultdict
    
    # Group notes by level (default to Level 1 if no level field)
    level_notes = defaultdict(list)
    for n in notes:
        lvl = n.get('level', 1)
        if lvl < 1 or lvl > 4:
            lvl = 1
        level_notes[lvl].append(n)
    
    levels_info = {}
    current_level = 1
    overall_start = None
    
    for lvl in range(1, 5):
        l_notes = level_notes.get(lvl, [])
        days_completed = len(l_notes)
        
        # Start date: earliest note date for this level
        start_date = None
        last_date = None
        if l_notes:
            dates = sorted(filter(None, (n.get('date') for n in l_notes)))
            if dates:
                start_date = dates[0]
                last_date = dates[-1]
        
        is_completed = days_completed >= LEVEL_DAYS
        in_progress = bool(l_notes) and not is_completed
        
        # Unlock logic: Level 1 always unlocked; others need prior level complete
        if lvl == 1:
            is_unlocked = True
        else:
            prev = levels_info.get(lvl - 1, {})
            is_unlocked = prev.get('is_completed', False)
        
        # Track current level as highest level with any notes
        if l_notes:
            current_level = lvl
        
        levels_info[lvl] = {
            'start_date': start_date,
            'completion_date': last_date,
            'days_completed': days_completed,
            'days_required': LEVEL_DAYS,
            'is_unlocked': is_unlocked,
            'is_completed': is_completed,
            'in_progress': in_progress,
        }
        
        if start_date and (overall_start is None or start_date < overall_start):
            overall_start = start_date
    
    return {
        'current_level': current_level,
        'overall_start_date': overall_start,
        'levels': levels_info,
    }


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

PROOF_TASKS = [
    ('PT1', 'Repository Analysis Brief'),
    ('PT2', 'Review Workflow Dry Run'),
    ('PT3', 'Metric Lineage Walkthrough'),
    ('PT4', 'QC Evidence Pack'),
    ('PT5', 'Deployment Rehearsal'),
    ('PT6', 'Reviewer Handoff Test'),
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
    # BI Academic Framework
    'BI Academic Framework.md': ['bi-judgment', 'ai-copilot', 'codex', 'pyramid', 'data-lineage', 'delivery-handoff', 'readiness'],
    'BI Academic Framework - Updated.md': ['bi-judgment', 'ai-copilot', 'codex', 'pyramid', 'data-lineage', 'delivery-handoff', 'readiness'],
    # Data & Lineage
    # (embedded in onboarding map and category notes)
    # Delivery & Handoff
    'Code Review and Handoff Standards.md': ['delivery-handoff', 'codex'],
    'CONTRIBUTING.md': ['delivery-handoff'],
    # Readiness
    'GitHub Well-Architected Principles.md': ['pyramid', 'bi-judgment', 'delivery-handoff'],
    '4-Week Onboarding Map.md': ['ai-copilot', 'codex', 'pyramid', 'bi-judgment', 'data-lineage', 'delivery-handoff', 'readiness'],
    'LEARNING_CATEGORIES.md': ['ai-copilot', 'codex', 'pyramid', 'bi-judgment', 'data-lineage', 'delivery-handoff', 'readiness'],
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


# Page mapping for files relative to action/ (legacy)
PAGE_CATEGORY_FROM_ACTION = {
    'notes': 'daily',
    'evidence': 'evidence',
    'reports': 'reports',
    'templates': 'templates',
    'scripts': 'scripts',
    'dashboard': 'dashboard',
}

# ── Git helpers ─────────────────────────────────────────────────────────────

def get_git_changed_files():
    """Run git diff --name-only HEAD to find files changed by the agent since last commit."""
    try:
        result = subprocess.run(
            ['git', 'diff', '--name-only', 'HEAD'],
            capture_output=True, text=True, cwd=REPO_ROOT, timeout=10
        )
        if result.returncode == 0:
            changed = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            return changed
    except Exception:
        pass
    return []


def get_git_diff_for_file(filepath):
    """Get the unified diff for a specific file vs HEAD. Returns diff text or empty string."""
    try:
        result = subprocess.run(
            ['git', 'diff', 'HEAD', '--', filepath],
            capture_output=True, text=False, cwd=REPO_ROOT, timeout=10
        )
        if result.returncode == 0:
            return result.stdout.decode('utf-8', errors='replace')
    except Exception:
        pass
    return ''


def get_git_diff_stat(filepath):
    """Get a short stat summary for the diff of a file. Returns string like '+3/-1 lines'."""
    try:
        result = subprocess.run(
            ['git', 'diff', '--stat', 'HEAD', '--', filepath],
            capture_output=True, text=True, cwd=REPO_ROOT, timeout=10
        )
        if result.returncode == 0:
            line = result.stdout.strip()
            if line:
                # Parse stat like " 1 file changed, 3 insertions(+), 1 deletion(-)"
                m = re.search(r'(\d+) insertions?\(\+\)', line)
                added = int(m.group(1)) if m else 0
                m = re.search(r'(\d+) deletions?\(-\)', line)
                removed = int(m.group(1)) if m else 0
                if added or removed:
                    return f'+{added}/-{removed} lines'
    except Exception:
        pass
    return ''


def get_git_head_info():
    """Return the current HEAD commit short hash and timestamp."""
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%h|%ct', 'HEAD'],
            capture_output=True, text=True, cwd=REPO_ROOT, timeout=10
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split('|')
            if len(parts) == 2:
                return {
                    'commit': parts[0],
                    'timestamp': datetime.fromtimestamp(int(parts[1])).isoformat(),
                }
    except Exception:
        pass
    return {'commit': '—', 'timestamp': datetime.now().isoformat()}


def compute_changes_by_page(changed_files):
    """
    Group changed files by dashboard page. For each file, capture:
    - diff content, diff stat, version label, timestamp
    Returns dict: { page_id: { count: N, files: [...] } }
    """
    changes_by_page = defaultdict(lambda: {'count': 0, 'files': []})
    head_info = get_git_head_info()

    # Track all changed files for cross-reference
    all_file_details = []

    for fp in changed_files:
        page = classify_path_to_page(fp)
        diff = get_git_diff_for_file(fp)
        stat = get_git_diff_stat(fp)
        # Determine version label from file modification time or HEAD
        version = head_info['commit'][:7] if head_info['commit'] != '—' else 'v1'

        entry = {
            'path': fp,
            'page': page,
            'version': version,
            'commit': head_info['commit'],
            'timestamp': datetime.now().isoformat(),
            'diff_stat': stat,
            'has_diff': bool(diff.strip()) if diff else False,
        }
        changes_by_page[page]['count'] += 1
        changes_by_page[page]['files'].append(entry)
        all_file_details.append(entry)

    return dict(changes_by_page), all_file_details


def compute_page_change_counts(changes_by_page):
    """Build a flat { page_id: count } map for sidebar badges."""
    all_pages = [
        'overview', 'daily', 'scorecard', 'proof-tasks', 'evidence',
        'classification', 'codex-gate', 'artifacts', 'third-party',
        'templates', 'scripts', 'dashboard', 'source',
    ]
    counts = {}
    for p in all_pages:
        counts[p] = changes_by_page.get(p, {}).get('count', 0)
    return counts


def get_source_criteria():
    """Scan source/ folder and return list of reference criteria files with content."""
    files = []
    if not os.path.isdir(SOURCE_DIR):
        return files
    for f in sorted(os.listdir(SOURCE_DIR)):
        fpath = os.path.join(SOURCE_DIR, f)
        if os.path.isfile(fpath) and not f.startswith('.'):
            file_size = os.path.getsize(fpath)
            is_text = f.endswith(('.md', '.txt', '.py', '.json', '.html', '.css', '.js', '.yml', '.yaml', '.csv'))
            preview = None
            content = None
            if is_text:
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
                        full = fh.read()
                        preview = full[:500]
                        if file_size <= 204800:
                            content = full
                except Exception:
                    pass
            files.append({
                'path': f,
                'size': file_size,
                'modified': datetime.fromtimestamp(os.path.getmtime(fpath)).isoformat(),
                'is_markdown': f.endswith('.md'),
                'is_text': is_text,
                'preview': preview,
                'content': content,
            })
    return files


# ── Legacy data functions (unchanged from original) ────────────────────────

def parse_date_from_filename(filename):
    basename = os.path.basename(filename).replace('.md', '')
    # Strip known prefixes used for testing/generated data (e.g. tpl_)
    for prefix in ['tpl_']:
        if basename.startswith(prefix):
            basename = basename[len(prefix):]
            break
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

    m = PAT_CATEGORY_TAGS.search(content)
    if m:
        note['category_tags'] = m.group(1).strip()

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
            if f == '.gitkeep' or f.startswith('tpl_'):
                continue
            fp = os.path.join(root, f)
            rel = os.path.relpath(fp, EVIDENCE_DIR)
            files.append({
                'path': rel,
                'filename': f,
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

    # Estimate learner level from classification sequence
    learner_level = 1
    if cls_seq:
        latest_cls = cls_seq[-1]['classification'].lower()
        if 'mastery' in latest_cls:
            learner_level = 4
        elif 'operational' in latest_cls:
            learner_level = 3
        elif 'development' in latest_cls:
            learner_level = 2

    return {
        'total_days': len(notes),
        'unique_weeks': len(days_per_week),
        'latest_classification': cls_seq[-1]['classification'] if cls_seq else '—',
        'classification_sequence': cls_seq,
        'days_per_week': dict(days_per_week),
        'evidence_count': 0,
        'scorecard_trend': {k: v for k, v in scorecard_trend.items()},
        'codex_gate_status': codex_gate_status,
        'completed_tracks': dict(completed_tracks),
        'proof_tasks': proof_tasks,
        'current_week': max(days_per_week.keys()) if days_per_week else 0,
        # ── New curriculum-anchored fields ──
        'curriculum_start_date': curriculum_start_date,
        'curriculum_start_source': _start_source,
        'curriculum_current_day': curriculum_current_day,
        'calendar_days_elapsed': calendar_days_elapsed,
        'working_days_elapsed': working_days_elapsed,
        'calendar_status': calendar_status,
        'week_progress': week_progress,
        'learner_level': learner_level,
        'level_progression': level_progression,
        'earliest_artifact_date': earliest_artifact,
        'today': today.isoformat(),
    }


def scan_all_artifacts():
    """Recursively scan the entire action/ directory and categorize every file.
    Embeds full content for text files < 200 KB so the dashboard preview
    can show the complete artifact without a GitHub fetch. Larger files
    get a 500-char preview with a fallback to GitHub raw URL."""
    categories = {
        'notes': [],
        'evidence': [],
        'reports': [],
        'templates': [],
        'scripts': [],
        'dashboard': [],
        'other': [],
    }

    if not os.path.isdir(ACTION_DIR):
        return categories

    for root, dirs, fnames in os.walk(ACTION_DIR):
        if '.git' in root.split(os.sep):
            continue
        rel_dir = os.path.relpath(root, ACTION_DIR)

        for f in sorted(fnames):
            if f == '.gitkeep' or f.endswith('.pyc'):
                continue
            fp = os.path.join(root, f)
            rel = os.path.relpath(fp, ACTION_DIR)

            mtime = datetime.fromtimestamp(os.path.getmtime(fp)).isoformat()
            is_markdown = f.endswith('.md')
            is_text = is_markdown or f.endswith(('.txt', '.py', '.ps1', '.json', '.html', '.css', '.js', '.yml', '.yaml', '.cfg', '.ini', '.csv', '.mdown', '.markdown'))
            preview = None
            content = None
            file_size = os.path.getsize(fp)
            if is_text:
                try:
                    with open(fp, 'r', encoding='utf-8', errors='replace') as fh:
                        full = fh.read()
                        preview = full[:500]
                        if file_size <= 204800:  # 200 KB limit for embedded content
                            content = full
                except Exception:
                    pass

            entry = {
                'path': rel,
                'filename': f,
                'folder': rel_dir,
                'size': file_size,
                'modified': mtime,
                'preview': preview,
                'content': content,
                'is_markdown': is_markdown,
                'is_text': is_text,
                'page_category': classify_path_to_page(os.path.join('action', rel)),
            }

            # Categorize
            if rel.startswith('notes') or rel.startswith('notes\\') or rel.startswith('notes/'):
                categories['notes'].append(entry)
            elif rel.startswith('evidence') or rel.startswith('evidence\\') or rel.startswith('evidence/'):
                categories['evidence'].append(entry)
            elif rel.startswith('reports') or rel.startswith('reports\\') or rel.startswith('reports/'):
                categories['reports'].append(entry)
            elif rel.startswith('templates') or rel.startswith('templates\\') or rel.startswith('templates/'):
                categories['templates'].append(entry)
            elif rel.startswith('scripts') or rel.startswith('scripts\\') or rel.startswith('scripts/'):
                categories['scripts'].append(entry)
            elif rel.startswith('dashboard') or rel.startswith('dashboard\\') or rel.startswith('dashboard/'):
                categories['dashboard'].append(entry)
            else:
                categories['other'].append(entry)

    return categories


def scan_review_dir():
    """Scan the review/ directory for files synced from action/."""
    synced = {'notes': [], 'evidence': [], 'reports': []}
    if not os.path.isdir(REVIEW_DIR):
        return synced
    for sub in ['notes', 'evidence', 'reports']:
        subdir = os.path.join(REVIEW_DIR, sub)
        if not os.path.isdir(subdir):
            continue
        for root, dirs, fnames in os.walk(subdir):
            for f in fnames:
                if f == '.gitkeep':
                    continue
                fp = os.path.join(root, f)
                rel = os.path.relpath(fp, REVIEW_DIR)
                file_size = os.path.getsize(fp)
                is_markdown = f.endswith('.md')
                is_text = is_markdown or f.endswith(('.txt', '.py', '.ps1', '.json', '.html', '.css', '.js', '.yml', '.yaml', '.csv'))
                preview = None
                content = None
                if is_text:
                    try:
                        with open(fp, 'r', encoding='utf-8', errors='replace') as fh:
                            full = fh.read()
                            preview = full[:500]
                            if file_size <= 204800:
                                content = full
                    except Exception:
                        pass
                synced[sub].append({
                    'path': rel,
                    'filename': f,
                    'size': file_size,
                    'modified': datetime.fromtimestamp(os.path.getmtime(fp)).isoformat(),
                    'is_markdown': is_markdown,
                    'is_text': is_text,
                    'preview': preview,
                    'content': content,
                })
    return synced


def build_page_artifacts(artifacts, changed_set):
    """Group artifacts by dashboard page category for per-page review sections."""
    page_map = {
        'daily': [],
        'evidence': [],
        'reports': [],
        'templates': [],
        'scripts': [],
        'dashboard': [],
        'other': [],
    }
    for cat, items in artifacts.items():
        for item in items:
            pc = item.get('page_category', 'other')
            item['action_cat'] = cat
            item['was_changed'] = (
                'action/' + item['path'].replace('\\', '/') in changed_set
                or item['path'].replace('\\', '/') in changed_set
            )
            if pc in page_map:
                page_map[pc].append(item)
            else:
                page_map['other'].append(item)
    return page_map


def main():
    print('Scanning notes...')
    notes = []
    if os.path.isdir(NOTES_DIR):
        for f in sorted(glob.glob(os.path.join(NOTES_DIR, '*.md'))):
            # Skip TPL-generated files — only real learner data
            if os.path.basename(f).startswith('tpl_'):
                continue
            d = parse_date_from_filename(f)
            if d:
                note = parse_note(f)
                note['filepath'] = f  # keep for proof-task scan
                notes.append(note)
    notes.sort(key=lambda x: x['date'] or '0000-00-00')

    print(f'  Found {len(notes)} daily notes')

    # Also scan archive dirs for completed/finalized learner work
    archived_notes = 0
    if os.path.isdir(NOTES_ARCHIVE_DIR):
        for f in sorted(glob.glob(os.path.join(NOTES_ARCHIVE_DIR, '*.md'))):
            # Skip TPL-generated files — only real learner data
            if os.path.basename(f).startswith('tpl_'):
                continue
            d = parse_date_from_filename(f)
            if d:
                note = parse_note(f)
                note['filepath'] = f
                note['archived'] = True
                notes.append(note)
                archived_notes += 1
    if archived_notes:
        print(f'  + {archived_notes} archived note(s) from action/archive/notes/')
    notes.sort(key=lambda x: x['date'] or '0000-00-00')

    summary = compute_summary(notes)

    # Add days_since_start to each note for calendar positioning
    if summary.get('curriculum_start_date'):
        try:
            cs_start = datetime.strptime(summary['curriculum_start_date'], '%Y-%m-%d').date()
            for n in notes:
                if n.get('date'):
                    try:
                        nd = datetime.strptime(n['date'], '%Y-%m-%d').date()
                        n['days_since_start'] = (nd - cs_start).days
                    except Exception:
                        n['days_since_start'] = None
        except Exception:
            pass

    print('Scanning evidence...')
    evidence = scan_evidence()
    # Include archived evidence
    if os.path.isdir(EVIDENCE_ARCHIVE_DIR):
        for root, dirs, fnames in os.walk(EVIDENCE_ARCHIVE_DIR):
            for f in fnames:
                if f == '.gitkeep':
                    continue
                fp = os.path.join(root, f)
                rel = os.path.relpath(fp, EVIDENCE_ARCHIVE_DIR)
                evidence.append({
                    'path': 'archive/evidence/' + rel,
                    'size': os.path.getsize(fp),
                    'modified': datetime.fromtimestamp(os.path.getmtime(fp)).isoformat(),
                    'archived': True,
                })
    evidence.sort(key=lambda x: x['modified'], reverse=True)
    summary['evidence_count'] = len(evidence)
    print(f'  Found {len(evidence)} evidence files')

    print('Scanning reports...')
    reports = scan_reports()
    # Include archived reports
    if os.path.isdir(REPORTS_ARCHIVE_DIR):
        pattern = os.path.join(REPORTS_ARCHIVE_DIR, '*.md')
        for fp in sorted(glob.glob(pattern)):
            if os.path.basename(fp) == '.gitkeep':
                continue
            reports.append({
                'path': 'archive/reports/' + os.path.basename(fp),
                'filename': os.path.basename(fp),
                'size': os.path.getsize(fp),
                'modified': datetime.fromtimestamp(os.path.getmtime(fp)).isoformat(),
                'archived': True,
            })
    print(f'  Found {len(reports)} report files')

    print('Scanning all artifacts...')
    artifacts = scan_all_artifacts()
    total_artifacts = sum(len(v) for v in artifacts.values())
    print(f'  Found {total_artifacts} total artifacts across action/')

    print('Tracking agent changes (git diff)...')
    changed_files = get_git_changed_files()
    changed_set = set(changed_files)
    print(f'  Found {len(changed_set)} changed file(s) since last commit')

    print('Building page-categorized artifacts...')
    page_artifacts = build_page_artifacts(artifacts, changed_set)

    print('Scanning review/ directory...')
    review_data = scan_review_dir()
    review_total = sum(len(v) for v in review_data.values())
    print(f'  Found {review_total} synced file(s) in review/')

    print('Reading synced reviews from review/reviews.json...')
    synced_reviews = {}
    reviews_path = os.path.join(REVIEW_DIR, 'reviews.json')
    if os.path.exists(reviews_path):
        try:
            with open(reviews_path, 'r', encoding='utf-8') as f:
                synced_reviews = json.load(f)
            # Filter out TPR bot reviews — only real reviewer data visible in dashboard
            _TPR_BOT_NAMES = {'🧪 TPR', 'tpr_bot'}
            synced_reviews = {
                aid: [r for r in revs if r.get('name', '').strip() not in _TPR_BOT_NAMES
                      and r.get('role', '').strip() != 'Test Proxy']
                for aid, revs in synced_reviews.items()
            }
            synced_reviews = {aid: revs for aid, revs in synced_reviews.items() if revs}
            rcount = sum(len(v) for v in synced_reviews.values())
            print(f'  Loaded {rcount} synced review(s) across {len(synced_reviews)} artifact(s) (TPR bot excluded)')
        except (json.JSONDecodeError, OSError) as e:
            print(f'  ⚠️  Warning: could not read {reviews_path}: {e}')
    else:
        print('  No review/reviews.json found — no synced reviews yet.')

    print('Scanning source/ criteria...')
    source_criteria = get_source_criteria()
    print(f'  Found {len(source_criteria)} source criteria file(s)')

    print('Computing per-page version changes...')
    changes_by_page, all_file_changes = compute_changes_by_page(changed_files)
    change_counts = compute_page_change_counts(changes_by_page)
    total_changes = sum(change_counts.values())
    print(f'  {total_changes} change(s) across {len([c for c in change_counts.values() if c > 0])} page(s)')

    print('Getting HEAD version info...')
    head_info = get_git_head_info()

    print('Checking environment status...')
    env_status = get_environment_status()
    print(f'  Environment status: {env_status["overall_status"]}')
    if env_status['missing_items']:
        print(f'  Missing items: {", ".join(env_status["missing_items"])}')

    # Strip filepath from notes for clean JSON
    notes_clean = []
    for n in notes:
        notes_clean.append({k: v for k, v in n.items() if k != 'filepath'})

    # Emit level progression info for dashboard
    print(f'  \U0001f9d1\u200d\U0001f393 Learner Level: {summary.get("level_progression", {}).get("current_level", 1)}')
    for lvl in range(1, 5):
        li = summary.get('level_progression', {}).get('levels', {}).get(lvl, {})
        status = '\u2705 Complete' if li.get('is_completed') else ('\U0001f4dd In progress' if li.get('in_progress') else ('\U0001f512 Locked' if not li.get('is_unlocked') else '\u23f3 Not started'))
        print(f'    Level {lvl}: {li.get("days_completed", 0)}/{li.get("days_required", 28)} days {status}')
        if li.get('start_date'):
            print(f'      Start: {li["start_date"]}')

    data = {
        'generated': datetime.now().isoformat(),
        'version': head_info,
        'notes': notes_clean,
        'evidence': evidence,
        'reports': reports,
        'artifacts': artifacts,
        'page_artifacts': page_artifacts,
        'changed_files': changed_files,
        'changes_by_page': changes_by_page,
        'all_file_changes': all_file_changes,
        'change_counts': change_counts,
        'source_criteria': source_criteria,
        'review_data': review_data,
        'synced_reviews': synced_reviews,
        'summary': summary,
        'categories': CATEGORIES,
        'source_category_map': SOURCE_CATEGORY_MAP,
        'levels': LEVELS,
        'level_categories': LEVEL_CATEGORIES,
        'environment_status': env_status,
    }

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

    print(f'\nDone — wrote {OUTPUT_PATH}')
    return data


# ── Environment Status ──────────────────────────────────────────────────────

def get_environment_status():
    """
    Check and report environment status for reviewer readiness.
    
    Returns a dict with environment requirements and their status.
    This helps reviewers confirm they have adequate tools and access.
    """
    import shutil
    
    env_status = {
        'checked_at': datetime.now().isoformat(),
        'overall_status': 'unknown',
        'requirements': {
            'vscode': {
                'name': 'VS Code or Markdown editor',
                'status': 'unknown',
                'required_for': 'Viewing .md files, daily notes, evidence, reports',
            },
            'git': {
                'name': 'Git',
                'status': 'unknown',
                'required_for': 'Version control operations',
            },
            'python': {
                'name': 'Python 3.x',
                'status': 'unknown',
                'required_for': 'Running sync and build scripts',
            },
            'github_access': {
                'name': 'GitHub repository access',
                'status': 'unknown',
                'required_for': 'Review comments, issue tracking',
            },
            'markdown_support': {
                'name': 'Markdown file support',
                'status': 'unknown',
                'required_for': 'Viewing .md files (daily notes, evidence, reports, templates)',
            },
            'json_support': {
                'name': 'JSON file support',
                'status': 'unknown',
                'required_for': 'Viewing data files, configuration, reviews',
            },
            'text_support': {
                'name': 'Text file support',
                'status': 'unknown',
                'required_for': 'Viewing .txt files (reference documents, templates)',
            },
        },
        'curriculum_formats': {
            'markdown': {
                'extensions': ['.md'],
                'status': 'unknown',
                'description': 'Training materials, daily notes, evidence, reports',
            },
            'text': {
                'extensions': ['.txt'],
                'status': 'unknown',
                'description': 'Reference documents, execution guides, templates',
            },
            'json': {
                'extensions': ['.json'],
                'status': 'unknown',
                'description': 'Dashboard data, configuration files',
            },
            'python': {
                'extensions': ['.py'],
                'status': 'unknown',
                'description': 'Utility scripts, sync tools',
            },
        },
        'missing_items': [],
        'recommendations': [],
    }
    
    # Check for common tools
    tools_to_check = {
        'git': 'git',
        'python': 'python3',
    }
    
    for tool_key, tool_name in tools_to_check.items():
        if shutil.which(tool_name):
            env_status['requirements'][tool_key]['status'] = 'available'
        else:
            env_status['requirements'][tool_key]['status'] = 'missing'
            env_status['missing_items'].append(tool_key)
    
    # VS Code detection (check common paths or environment)
    vscode_indicators = [
        os.path.exists(os.path.expanduser('~/.vscode')),
        os.environ.get('VSCODE_INJECT_CLI') is not None,
        'vscode' in os.environ.get('TERM_PROGRAM', '').lower(),
    ]
    if any(vscode_indicators):
        env_status['requirements']['vscode']['status'] = 'available'
    else:
        env_status['requirements']['vscode']['status'] = 'likely_available'
    
    # GitHub access (check for gh CLI or git remote)
    gh_available = shutil.which('gh')
    git_remote_exists = False
    try:
        result = subprocess.run(
            ['git', 'remote', '-v'],
            capture_output=True, text=True, cwd=REPO_ROOT, timeout=5
        )
        if result.returncode == 0 and 'github.com' in result.stdout:
            git_remote_exists = True
    except Exception:
        pass
    
    if gh_available or git_remote_exists:
        env_status['requirements']['github_access']['status'] = 'available'
    else:
        env_status['requirements']['github_access']['status'] = 'unknown'
    
    # File format support (always available in modern editors)
    for format_key in ['markdown_support', 'json_support', 'text_support']:
        env_status['requirements'][format_key]['status'] = 'available'
    
    # Curriculum format status
    for format_key in env_status['curriculum_formats']:
        env_status['curriculum_formats'][format_key]['status'] = 'supported'
    
    # Determine overall status
    missing = [k for k, v in env_status['requirements'].items() if v['status'] == 'missing']
    env_status['overall_status'] = 'adequate' if not missing else 'inadequate'
    
    # Generate recommendations
    if missing:
        env_status['recommendations'].append(
            f"Missing required tools: {', '.join(missing)}. "
            "Install these before proceeding with review."
        )
    
    env_status['recommendations'].append(
        "Verify you can view all curriculum documentation formats "
        "(Markdown, text, JSON) in your editor."
    )
    
    env_status['recommendations'].append(
        "If environment is inadequate, submit a GitHub issue using the "
        "reviewer-environment-request.md template."
    )
    
    return env_status


if __name__ == '__main__':
    main()
