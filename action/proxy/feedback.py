"""
action/proxy/feedback.py
Feedback, progression, and Q&A data access for the learner web interface.

Provides read-only access to reviewer feedback (from review/reviews.json),
tracks read/unread status, manages Q&A threads on feedback items, and
exposes level progression data from the dashboard build.

BOUNDARY ENFORCEMENT:
    This module NEVER writes to review/ — learner cannot create, modify,
    or delete reviewer feedback. All writes are to action/proxy/ for
    learner-owned data (seen status, Q&A threads, revision history).
"""
import json
import os
import re
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

# ── Paths ──────────────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REVIEW_DIR = _REPO_ROOT / 'review'
REVIEWS_PATH = REVIEW_DIR / 'reviews.json'
PROFILES_PATH = REVIEW_DIR / 'reviewer_profiles.json'
ACTION_DIR = _REPO_ROOT / 'action'
PROXY_DIR = ACTION_DIR / 'proxy'
NOTES_DIR = ACTION_DIR / 'notes'
EVIDENCE_DIR = ACTION_DIR / 'evidence'
ARCHIVE_NOTES = ACTION_DIR / 'archive' / 'notes'
DATA_JSON = ACTION_DIR / 'dashboard' / 'data.json'

# Learner-owned data (never touches review/)
_FEEDBACK_SEEN_PATH = PROXY_DIR / '.feedback_seen.json'
_QA_PATH = PROXY_DIR / '.feedback_qa.json'
_REVISION_INDEX = PROXY_DIR / '.revision_index.json'

# ── Read reviews (read-only) ───────────────────────────────────────────────

def load_reviews() -> dict:
    """Load reviews from review/reviews.json. Returns {artifactId: [review, ...]}."""
    if not REVIEWS_PATH.exists():
        return {}
    try:
        with open(REVIEWS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def load_profiles() -> dict:
    """Load reviewer profiles from review/reviewer_profiles.json."""
    if not PROFILES_PATH.exists():
        return {}
    try:
        with open(PROFILES_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def get_reviewer_display(username: str) -> dict:
    """Return display info for a reviewer username."""
    profiles = load_profiles()
    profile = profiles.get(username.lower().replace(' ', '_'), {})
    return {
        'username': username,
        'display_name': profile.get('displayName', username),
        'role': profile.get('role', 'Reviewer'),
        'color': profile.get('color', '#7c73ff'),
        'avatar': profile.get('avatar', ''),
    }


def get_feedback_for_learner() -> list[dict]:
    """
    Return all reviews that reference learner artifacts (notes/evidence files),
    enriched with reviewer display info and the local artifact filename.

    Returns list of dicts sorted by timestamp descending.
    """
    reviews = load_reviews()
    profiles = load_profiles()
    all_feedback = []

    # Get all learner artifact filenames for matching
    learner_notes = {f.stem.lower() for f in NOTES_DIR.glob('*.md') if not f.name.startswith('.')}
    learner_evidence = {f.name.lower() for f in EVIDENCE_DIR.glob('*.*') if not f.name.startswith('.')}

    for artifact_id, review_list in reviews.items():
        if not isinstance(review_list, list):
            continue
        artifact_lower = artifact_id.lower()

        # Determine if this artifact is learner-owned
        is_note = any(artifact_lower == note or artifact_lower.startswith(note)
                      for note in learner_notes)
        is_evidence = any(artifact_lower == ev or artifact_lower.startswith(ev)
                          for ev in learner_evidence)

        for r in review_list:
            if not isinstance(r, dict):
                continue
            username = r.get('name', 'Unknown')
            profile_info = get_reviewer_display(username)

            all_feedback.append({
                'artifactId': artifact_id,
                'reviewId': r.get('reviewId', ''),
                'is_note': is_note,
                'is_evidence': is_evidence,
                'reviewer': profile_info,
                'rating': r.get('rating', ''),
                'text': r.get('text', ''),
                'timestamp': r.get('timestamp', ''),
                'version': r.get('version', 1),
                'category': r.get('category', ''),
            })

    all_feedback.sort(key=lambda x: x['timestamp'], reverse=True)
    return all_feedback


# ── Read/unread tracking (learner-owned) ────────────────────────────────────

def _load_seen() -> dict:
    """Load seen status for feedback items."""
    if not _FEEDBACK_SEEN_PATH.exists():
        return {}
    try:
        with open(_FEEDBACK_SEEN_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_seen(data: dict):
    """Save seen status."""
    _FEEDBACK_SEEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_FEEDBACK_SEEN_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def get_unread_feedback() -> list[dict]:
    """Return feedback items that the learner hasn't seen yet."""
    all_feedback = get_feedback_for_learner()
    seen = _load_seen()
    unread = []
    for fb in all_feedback:
        # Check if this review has been seen
        seen_key = f"{fb['artifactId']}::{fb['reviewId']}"
        if seen_key not in seen:
            unread.append(fb)
    return unread


def mark_seen(artifact_id: str, review_id: str):
    """Mark a specific review as seen by the learner."""
    seen = _load_seen()
    seen_key = f"{artifact_id}::{review_id}"
    seen[seen_key] = datetime.now().isoformat()
    _save_seen(seen)


def mark_all_seen():
    """Mark all feedback for the learner's artifacts as seen."""
    all_feedback = get_feedback_for_learner()
    seen = _load_seen()
    for fb in all_feedback:
        seen_key = f"{fb['artifactId']}::{fb['reviewId']}"
        seen[seen_key] = datetime.now().isoformat()
    _save_seen(seen)


# ── Q&A on feedback (learner-owned) ────────────────────────────────────────

def _load_qa() -> dict:
    """Load Q&A threads. {reviewId: [entry, ...]}"""
    if not _QA_PATH.exists():
        return {}
    try:
        with open(_QA_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_qa(data: dict):
    """Save Q&A threads."""
    _QA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_QA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def get_qa_thread(review_id: str) -> list[dict]:
    """Return Q&A entries for a specific review."""
    qa = _load_qa()
    return qa.get(review_id, [])


def add_qa_entry(review_id: str, author: str, text: str, artifact_id: str = '') -> dict:
    """
    Add a Q&A entry to a review thread.
    author: 'learner' or reviewer username
    """
    qa = _load_qa()
    if review_id not in qa:
        qa[review_id] = []
    entry = {
        'reviewId': review_id,
        'artifactId': artifact_id,
        'author': author,
        'text': text,
        'timestamp': datetime.now().isoformat(),
    }
    qa[review_id].append(entry)
    _save_qa(qa)
    return entry


# ── Level progression (read-only from data.json) ────────────────────────────

def get_level_progress() -> dict:
    """
    Read level progression data from the dashboard's data.json.
    Returns the level_progression object or a default.
    """
    if not DATA_JSON.exists():
        return _default_progress()

    try:
        with open(DATA_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return _default_progress()

    summary = data.get('summary', {})
    level_prog = summary.get('level_progression', {})

    if not level_prog:
        return _default_progress()

    # Enrich with current-day info
    current_day = summary.get('curriculum_current_day', 0)
    current_week = summary.get('current_week', 0)

    return {
        'current_level': level_prog.get('current_level', 1),
        'overall_start_date': level_prog.get('overall_start_date'),
        'levels': level_prog.get('levels', {}),
        'current_day': current_day,
        'current_week': current_week,
        'total_days': summary.get('total_days', 0),
        'working_days_elapsed': summary.get('working_days_elapsed', 0),
        'scorecard_trend': summary.get('scorecard_trend', {}),
        'codex_gate_status': summary.get('codex_gate_status', {}),
        'proof_tasks': summary.get('proof_tasks', {}),
        'latest_classification': summary.get('latest_classification', '—'),
    }


def _default_progress() -> dict:
    """Return default progression when data.json is unavailable."""
    return {
        'current_level': 1,
        'overall_start_date': None,
        'levels': {
            '1': {
                'start_date': None,
                'completion_date': None,
                'days_completed': 0,
                'days_required': 28,
                'is_unlocked': True,
                'is_completed': False,
                'in_progress': False,
                'reviewer_confirmed': False,
                'label': 'Foundation',
                'emoji': '🌱',
                'gates': {'met': False, 'details': {}, 'blockers': ['No data']},
            },
            '2': {
                'start_date': None,
                'completion_date': None,
                'days_completed': 0,
                'days_required': 28,
                'is_unlocked': False,
                'is_completed': False,
                'in_progress': False,
                'reviewer_confirmed': False,
                'label': 'Development',
                'emoji': '🌿',
                'gates': {'met': False, 'details': {}, 'blockers': ['Complete Level 1 first']},
            },
            '3': {
                'start_date': None,
                'completion_date': None,
                'days_completed': 0,
                'days_required': 28,
                'is_unlocked': False,
                'is_completed': False,
                'in_progress': False,
                'reviewer_confirmed': False,
                'label': 'Operational',
                'emoji': '🌳',
                'gates': {'met': False, 'details': {}, 'blockers': ['Complete Level 2 first']},
            },
            '4': {
                'start_date': None,
                'completion_date': None,
                'days_completed': 0,
                'days_required': 28,
                'is_unlocked': False,
                'is_completed': False,
                'in_progress': False,
                'reviewer_confirmed': False,
                'label': 'Mastery',
                'emoji': '🏆',
                'gates': {'met': False, 'details': {}, 'blockers': ['Complete Level 3 first']},
            },
        },
        'current_day': 0,
        'current_week': 0,
        'total_days': 0,
        'working_days_elapsed': 0,
        'scorecard_trend': {},
        'codex_gate_status': {},
        'proof_tasks': {},
        'latest_classification': '—',
    }


# ── Revision tracking (learner-owned) ───────────────────────────────────────

def _load_revision_index() -> dict:
    """Load revision index. {artifactPath: [revision, ...]}"""
    if not _REVISION_INDEX.exists():
        return {}
    try:
        with open(_REVISION_INDEX, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_revision_index(data: dict):
    """Save revision index."""
    _REVISION_INDEX.parent.mkdir(parents=True, exist_ok=True)
    with open(_REVISION_INDEX, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def create_revision(file_path: Path, artifact_type: str, artifact_id: str) -> Optional[Path]:
    """
    Before updating a file, save a copy as a revision.
    Returns the revision path, or None if the file doesn't exist.

    Revisions are stored in action/archive/revisions/{type}/{id}_v{timestamp}.md
    """
    if not file_path.exists():
        return None

    rev_dir = ACTION_DIR / 'archive' / 'revisions' / artifact_type
    rev_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    rev_name = f"{file_path.stem}_v{timestamp}{file_path.suffix}"
    rev_path = rev_dir / rev_name

    import shutil
    shutil.copy2(str(file_path), str(rev_path))

    # Update index
    idx = _load_revision_index()
    key = str(file_path)
    if key not in idx:
        idx[key] = []
    idx[key].append({
        'revision_path': str(rev_path),
        'timestamp': datetime.now().isoformat(),
        'artifact_type': artifact_type,
        'artifact_id': artifact_id,
    })
    _save_revision_index(idx)

    return rev_path


def get_revision_history(file_path: Path) -> list[dict]:
    """Return revision history for a file."""
    idx = _load_revision_index()
    key = str(file_path)
    return idx.get(key, [])


# ── Learner daily email summary ─────────────────────────────────────────────

def compile_learner_daily_summary() -> dict:
    """
    Compile a daily summary for the learner: what they did,
    what remains, what feedback needs attention.

    Returns a dict with summary sections.
    """
    # Count today's activity
    today_str = date.today().isoformat()
    notes_today = list(NOTES_DIR.glob(f'{today_str}.md'))
    evidence_today = [f for f in EVIDENCE_DIR.glob('*.*')
                      if not f.name.startswith('.')
                      and date.fromtimestamp(f.stat().st_mtime).isoformat() == today_str]

    # Total work
    total_notes = len(list(NOTES_DIR.glob('*.md')))
    total_evidence = len([f for f in EVIDENCE_DIR.glob('*.*') if not f.name.startswith('.')])

    # Unread feedback
    unread = get_unread_feedback()

    # Outstanding by priority
    outstanding = {
        'unread_feedback': len(unread),
        'notes_today': len(notes_today),
        'evidence_today': len(evidence_today),
        'total_notes': total_notes,
        'total_evidence': total_evidence,
        'latest_classification': '—',
        'current_day': 0,
    }

    # Try to get more context from data.json
    prog = get_level_progress()
    outstanding['current_day'] = prog.get('current_day', 0)
    outstanding['latest_classification'] = prog.get('latest_classification', '—')

    return outstanding
