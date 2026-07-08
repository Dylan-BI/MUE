"""
action/dashboard/build_data.py
Third-Party Review Dashboard builder for MUE.
Scans action/, source/, and review/ then generates data.json consumed by
dashboard.html. Tracks per-page version changes, git diffs, source criteria
alignment, and provides version-based review metadata.

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
from datetime import date, datetime

DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))
ACTION_DIR = os.path.abspath(os.path.join(DASHBOARD_DIR, '..'))
NOTES_DIR = os.path.join(ACTION_DIR, 'notes')
EVIDENCE_DIR = os.path.join(ACTION_DIR, 'evidence')
REPORTS_DIR = os.path.join(ACTION_DIR, 'reports')
OUTPUT_PATH = os.path.join(DASHBOARD_DIR, 'data.json')

# Parent repo root (for review/ dir and git root)
REPO_ROOT = os.path.abspath(os.path.join(ACTION_DIR, '..'))
REVIEW_DIR = os.path.join(REPO_ROOT, 'review')
SOURCE_DIR = os.path.join(REPO_ROOT, 'source')

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
    r'Classification:\s*(Foundational|Developing|Operational|Ready for Codex Acceleration)',
    re.IGNORECASE,
)
PAT_PRIMARY_TRACK = re.compile(
    r'Primary track:\s*(Pyramid operations|Codex productivity|BI judgment)',
    re.IGNORECASE,
)
PAT_DAY_NUMBER = re.compile(r'Day\s*(\d+)')
PAT_ARTIFACT = re.compile(r'Required Artifact:\s*(.+)', re.IGNORECASE)
PAT_LEARNED = re.compile(r'What I learned today:\s*(.+)', re.IGNORECASE)
PAT_EVIDENCE = re.compile(r'What evidence I produced:\s*(.+)', re.IGNORECASE)
PAT_REMAINS = re.compile(r'What remains open:\s*(.+)', re.IGNORECASE)
PAT_NEXT_STEP = re.compile(r'Next narrow step:\s*(.+)', re.IGNORECASE)
PAT_WEEK_NUMBER = re.compile(r'Week Number:\s*(\d+)')

SCORE_AREAS = [
    'Prompt discipline',
    'Repo or workspace analysis',
    'Change isolation',
    'Validation order',
    'Deployment awareness',
    'Reviewer handoff',
    'Reusability',
]

CODEX_GATES = [
    'One end-to-end workflow completed',
    'Business-logic ownership understood',
    'Validation evidence produced without help',
    'Proof tasks completed',
    'One clean reviewable change slice',
    'One reusable team asset created',
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
    '4-Week Onboarding Map.md': ['ai-copilot', 'codex', 'pyramid', 'bi-judgment', 'data-lineage', 'delivery-handoff', 'readiness'],
    'LEARNING_CATEGORIES.md': ['ai-copilot', 'codex', 'pyramid', 'bi-judgment', 'data-lineage', 'delivery-handoff', 'readiness'],
}

# ── 4-Level Curriculum Framework ──────────────────────────────────────────
# Each level has its own independent 28-day curriculum across all 7 categories.
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
# Each level adjusts the 7 learning categories with appropriate descriptions,
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
    """Scan source/ folder and return list of reference criteria files."""
    files = []
    if not os.path.isdir(SOURCE_DIR):
        return files
    for f in sorted(os.listdir(SOURCE_DIR)):
        fpath = os.path.join(SOURCE_DIR, f)
        if os.path.isfile(fpath) and not f.startswith('.'):
            files.append({
                'path': f,
                'size': os.path.getsize(fpath),
                'modified': datetime.fromtimestamp(os.path.getmtime(fpath)).isoformat(),
            })
    return files


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

    for area in SCORE_AREAS:
        p = re.compile(rf'{re.escape(area)}:\s*(Pass|Partial|Fail)', re.IGNORECASE)
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
    }


def scan_all_artifacts():
    """Recursively scan the entire action/ directory and categorize every file."""
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
            preview = None
            if is_markdown:
                try:
                    with open(fp, 'r', encoding='utf-8') as fh:
                        preview = fh.read(500)
                except Exception:
                    preview = None

            entry = {
                'path': rel,
                'filename': f,
                'folder': rel_dir,
                'size': os.path.getsize(fp),
                'modified': mtime,
                'preview': preview,
                'is_markdown': is_markdown,
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
                synced[sub].append({
                    'path': rel,
                    'filename': f,
                    'size': os.path.getsize(fp),
                    'modified': datetime.fromtimestamp(os.path.getmtime(fp)).isoformat(),
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


def scan_all_artifacts():
    """Recursively scan the entire action/ directory and categorize every file."""
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
            preview = None
            if is_markdown:
                try:
                    with open(fp, 'r', encoding='utf-8') as fh:
                        preview = fh.read(500)
                except Exception:
                    preview = None

            entry = {
                'path': rel,
                'filename': f,
                'folder': rel_dir,
                'size': os.path.getsize(fp),
                'modified': mtime,
                'preview': preview,
                'is_markdown': is_markdown,
                'page_category': classify_path_to_page(rel),
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
                synced[sub].append({
                    'path': rel,
                    'filename': f,
                    'size': os.path.getsize(fp),
                    'modified': datetime.fromtimestamp(os.path.getmtime(fp)).isoformat(),
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
            d = parse_date_from_filename(f)
            if d:
                note = parse_note(f)
                note['filepath'] = f  # keep for proof-task scan
                notes.append(note)
    notes.sort(key=lambda x: x['date'] or '0000-00-00')

    print(f'  Found {len(notes)} daily notes')
    summary = compute_summary(notes)

    print('Scanning evidence...')
    evidence = scan_evidence()
    summary['evidence_count'] = len(evidence)
    print(f'  Found {len(evidence)} evidence files')

    print('Scanning reports...')
    reports = scan_reports()
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

    # Strip filepath from notes for clean JSON
    notes_clean = []
    for n in notes:
        notes_clean.append({k: v for k, v in n.items() if k != 'filepath'})

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
        'summary': summary,
        'categories': CATEGORIES,
        'source_category_map': SOURCE_CATEGORY_MAP,
        'levels': LEVELS,
        'level_categories': LEVEL_CATEGORIES,
    }

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

    print(f'\nDone — wrote {OUTPUT_PATH}')
    return data


if __name__ == '__main__':
    main()
