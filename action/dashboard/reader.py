"""
action/dashboard/reader.py
Read and parse all data from the action/ folder for the dashboard.
Provides clean DataFrames and dicts for the Streamlit UI layer.
"""
import glob
import os
import re
from datetime import date, datetime, timedelta
from collections import defaultdict

# ── Paths ───────────────────────────────────────────────────────────────────
DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))
ACTION_DIR = os.path.abspath(os.path.join(DASHBOARD_DIR, '..'))

NOTES_DIR = os.path.join(ACTION_DIR, 'notes')
EVIDENCE_DIR = os.path.join(ACTION_DIR, 'evidence')
REPORTS_DIR = os.path.join(ACTION_DIR, 'reports')

# ── Regex patterns ──────────────────────────────────────────────────────────
PAT_CLASSIFICATION = re.compile(
    r'Classification:\s*(Foundational|Developing|Operational|Ready For Codex Acceleration)',
    re.IGNORECASE
)
PAT_PRIMARY_TRACK = re.compile(
    r'Primary track:\s*(Pyramid operations|Codex productivity|BI judgment)',
    re.IGNORECASE
)
PAT_DAY_NUMBER = re.compile(r'Day\s*(\d+)')
PAT_ARTIFACT = re.compile(r'Required Artifact:\s*(.+)', re.IGNORECASE)
PAT_LEARNED = re.compile(r'What I learned today:\s*(.+)', re.IGNORECASE)
PAT_EVIDENCE_REPORT = re.compile(r'What evidence I produced:\s*(.+)', re.IGNORECASE)
PAT_REMAINS = re.compile(r'What remains open:\s*(.+)', re.IGNORECASE)
PAT_NEXT_STEP = re.compile(r'Next narrow step:\s*(.+)', re.IGNORECASE)
PAT_WEEK_NUMBER = re.compile(r'Week Number:\s*(\d+)')

SCORE_AREAS = [
    ('Prompt discipline', 'prompt_discipline'),
    ('Repo or workspace analysis', 'repo_analysis'),
    ('Change isolation', 'change_isolation'),
    ('Validation order', 'validation_order'),
    ('Deployment awareness', 'deployment_awareness'),
    ('Reviewer handoff', 'reviewer_handoff'),
    ('Reusability', 'reusability'),
]

CODEX_GATES = [
    ('One end-to-end workflow completed', 'end_to_end_workflow'),
    ('Business-logic ownership understood', 'business_logic_ownership'),
    ('Validation evidence produced without help', 'validation_evidence'),
    ('Proof tasks completed', 'proof_tasks_completed'),
    ('One clean reviewable change slice', 'clean_change_slice'),
    ('One reusable team asset created', 'reusable_asset'),
]

PROOF_TASKS = [
    ('Proof Task 1', 'PT1', 'Repository Analysis Brief'),
    ('Proof Task 2', 'PT2', 'Review Workflow Dry Run'),
    ('Proof Task 3', 'PT3', 'Metric Lineage Walkthrough'),
    ('Proof Task 4', 'PT4', 'QC Evidence Pack'),
    ('Proof Task 5', 'PT5', 'Deployment Rehearsal'),
    ('Proof Task 6', 'PT6', 'Reviewer Handoff Test'),
]


def parse_date_from_filename(filename):
    """Extract date from a YYYY-MM-DD.md filename."""
    basename = os.path.basename(filename).replace('.md', '')
    try:
        return datetime.strptime(basename, '%Y-%m-%d').date()
    except ValueError:
        return None


def read_daily_note(filepath):
    """Parse a single daily note and return a dict of extracted fields."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    note = {
        'filepath': filepath,
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

    # Day number
    m = PAT_DAY_NUMBER.search(content)
    if m:
        note['day_number'] = int(m.group(1))

    # Classification
    m = PAT_CLASSIFICATION.search(content)
    if m:
        note['classification'] = m.group(1).capitalize()

    # Primary track
    m = PAT_PRIMARY_TRACK.search(content)
    if m:
        note['primary_track'] = m.group(1).strip()

    # Required artifact
    m = PAT_ARTIFACT.search(content)
    if m:
        note['required_artifact'] = m.group(1).strip()

    # Daily report fields
    for pat, key in [
        (PAT_LEARNED, 'what_learned'),
        (PAT_EVIDENCE_REPORT, 'evidence_produced'),
        (PAT_REMAINS, 'what_remains'),
        (PAT_NEXT_STEP, 'next_step'),
    ]:
        m = pat.search(content)
        if m:
            note[key] = m.group(1).strip()

    # Week number
    m = PAT_WEEK_NUMBER.search(content)
    if m:
        note['week_number'] = int(m.group(1))

    # Scorecard
    for label, key in SCORE_AREAS:
        p = re.compile(rf'{re.escape(label)}:\s*(Pass|Partial|Fail)', re.IGNORECASE)
        m = p.search(content)
        if m:
            note['scorecard'][key] = m.group(1).capitalize()

    # Codex gate
    for label, key in CODEX_GATES:
        p = re.compile(rf'{re.escape(label)}:\s*(Yes|No)', re.IGNORECASE)
        m = p.search(content)
        if m:
            note['codex_gate'][key] = m.group(1).capitalize()

    return note


def load_all_notes():
    """Load and parse all daily notes from action/notes/."""
    pattern = os.path.join(NOTES_DIR, '*.md')
    files = glob.glob(pattern)
    notes = []
    for f in files:
        d = parse_date_from_filename(f)
        if d:
            notes.append(read_daily_note(f))
    notes.sort(key=lambda x: x['date'] if x['date'] else date.min)
    return notes


def get_proof_task_evidence():
    """Scan evidence directory for proof task artifacts."""
    evidence = []
    if not os.path.isdir(EVIDENCE_DIR):
        return evidence

    for root, dirs, files in os.walk(EVIDENCE_DIR):
        for f in files:
            if f == '.gitkeep':
                continue
            filepath = os.path.join(root, f)
            rel_path = os.path.relpath(filepath, EVIDENCE_DIR)
            size = os.path.getsize(filepath)
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            evidence.append({
                'filepath': filepath,
                'filename': f,
                'relative_path': rel_path,
                'size_bytes': size,
                'modified': mtime,
            })

    evidence.sort(key=lambda x: x['modified'], reverse=True)
    return evidence


def get_reports():
    """List generated report files."""
    reports = []
    if not os.path.isdir(REPORTS_DIR):
        return reports
    pattern = os.path.join(REPORTS_DIR, '*.md')
    for f in sorted(glob.glob(pattern)):
        if os.path.basename(f) == '.gitkeep':
            continue
        reports.append({
            'filepath': f,
            'filename': os.path.basename(f),
            'size_bytes': os.path.getsize(f),
            'modified': datetime.fromtimestamp(os.path.getmtime(f)),
        })
    return reports


def compute_summary(notes):
    """Compute summary statistics from all parsed notes."""
    if not notes:
        return {
            'total_days': 0,
            'unique_weeks': 0,
            'latest_classification': '—',
            'classification_sequence': [],
            'days_per_week': {},
            'evidence_count': 0,
            'scorecard_trend': {},
            'codex_gate_status': {},
            'completed_tracks': defaultdict(int),
            'proof_task_mentions': {},
            'current_week': 0,
        }

    # Classification sequence
    cls_seq = []
    for n in notes:
        if n['classification']:
            cls_seq.append({
                'day': n['day_number'],
                'date': n['date'],
                'classification': n['classification'],
            })

    # Days per week
    days_per_week = defaultdict(int)
    for n in notes:
        if n['week_number']:
            days_per_week[n['week_number']] += 1
        elif n['day_number']:
            w = (n['day_number'] - 1) // 5 + 1
            days_per_week[w] += 1

    # Scorecard trend
    scorecard_trend = defaultdict(list)
    for n in notes:
        if n['scorecard']:
            for area, score in n['scorecard'].items():
                scorecard_trend[area].append({
                    'day': n['day_number'],
                    'date': n['date'],
                    'score': score,
                })

    # Codex gate latest
    codex_gate_status = {}
    for n in reversed(notes):
        if n['codex_gate']:
            codex_gate_status = n['codex_gate']
            break

    # Track distribution
    completed_tracks = defaultdict(int)
    for n in notes:
        if n['primary_track']:
            completed_tracks[n['primary_track']] += 1

    # Proof task mentions
    pt_mentions = {}
    for pt_name, pt_abbr, pt_desc in PROOF_TASKS:
        pt_mentions[pt_abbr] = {
            'title': pt_name,
            'description': pt_desc,
            'found': False,
            'days': [],
        }
    for n in notes:
        with open(n['filepath'], 'r', encoding='utf-8') as f:
            content = f.read()
        for pt_name, pt_abbr, pt_desc in PROOF_TASKS:
            if re.search(f'Proof Task {pt_abbr[-1]}|{pt_desc}', content, re.IGNORECASE):
                pt_mentions[pt_abbr]['found'] = True
                pt_mentions[pt_abbr]['days'].append(n['day_number'])

    return {
        'total_days': len(notes),
        'unique_weeks': len(days_per_week),
        'latest_classification': cls_seq[-1]['classification'] if cls_seq else '—',
        'classification_sequence': cls_seq,
        'days_per_week': dict(days_per_week),
        'evidence_count': len(get_proof_task_evidence()),
        'scorecard_trend': dict(scorecard_trend),
        'codex_gate_status': codex_gate_status,
        'completed_tracks': dict(completed_tracks),
        'proof_task_mentions': pt_mentions,
        'current_week': max(days_per_week.keys()) if days_per_week else 0,
    }


def compute_week_boundaries(notes):
    """Return (start_date, end_date) tuples for each week represented."""
    if not notes:
        return []
    weeks = defaultdict(list)
    for n in notes:
        if n['date']:
            # ISO week
            iso = n['date'].isocalendar()
            wk = f"{iso[0]}-W{iso[1]:02d}"
            weeks[wk].append(n['date'])
    boundaries = []
    for wk, dates in sorted(weeks.items()):
        boundaries.append({
            'week_label': wk,
            'start': min(dates),
            'end': max(dates),
        })
    return boundaries
