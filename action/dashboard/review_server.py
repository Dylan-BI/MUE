#!/usr/bin/env python3
"""
action/dashboard/review_server.py
Lightweight HTTP server that enables multi-reviewer collaboration.

Serves the dashboard and provides a REST API for review CRUD.
Reviews are stored in review/reviews.json (shared across all reviewers).
After each change, data.json is auto-rebuilt so all connected dashboards
see the update on their next auto-refresh cycle.

Usage:
    python action/dashboard/review_server.py [--port 8080] [--host 0.0.0.0]

API:
    GET  /api/reviews              → all reviews as JSON
    POST /api/reviews              → add review   {artifactId, review}
    PUT  /api/reviews              → update review {artifactId, reviewId, updates, version?}
    DELETE /api/reviews            → delete review {artifactId, reviewId}
    GET  /api/locks                → all active edit locks
    POST /api/locks                → claim/release/check locks
    GET  /api/status               → server status + connected reviewer count

Conflict Prevention:
    - Edit locks: soft locks prevent concurrent editing (10 min TTL)
    - Version tracking: each review has a version number, checked on update
    - Fast polling: dashboard polls every 8s for real-time awareness

Storage:
    review/reviews.json            → canonical shared review store
    action/dashboard/data.json     → rebuilt after each review change

Notes:
    - Serves static files from action/dashboard/ (the dashboard itself)
    - No external dependencies — uses only Python stdlib
    - CORS headers included for cross-origin access (file:// fallback)
    - Author-only edit/delete enforced server-side by reviewer name
"""
import argparse
import json
import os
import smtplib
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Local structured logging
from _log import log

# ── Paths ──────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
DASHBOARD_DIR = SCRIPT_DIR
REVIEWS_PATH = REPO_ROOT / 'review' / 'reviews.json'
PROFILES_PATH = REPO_ROOT / 'review' / 'reviewer_profiles.json'
ACTIVITY_PATH = REPO_ROOT / 'review' / 'profile_activity.json'
BUILD_SCRIPT = DASHBOARD_DIR / 'build_data.py'
ENV_FILE = DASHBOARD_DIR / '.env'

# Set dynamically at startup so emails link to the correct address
_SERVER_BASE_URL = 'http://localhost:8080'

# Access token — set at startup for secure remote access
# When set, all requests must include ?t=<token> to access the dashboard/API
SERVER_ACCESS_TOKEN = None

# API Version
API_VERSION = 'v1'
API_VERSION_HEADER = 'X-API-Version'


def _get_lan_ips():
    """Return a list of non-loopback IPv4 addresses for this machine."""
    import socket
    ips = []
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            sockaddr = info[4]
            if isinstance(sockaddr, tuple) and len(sockaddr) >= 1:
                addr = sockaddr[0]
                if isinstance(addr, str) and addr not in ips and not addr.startswith('127.'):
                    ips.append(addr)
    except Exception:
        pass
    # Fallback: connect a UDP socket to an external IP to discover the default route IP
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(('8.8.8.8', 80))
            default_ip = s.getsockname()[0]
            if default_ip not in ips and not default_ip.startswith('127.'):
                ips.append(default_ip)
    except Exception:
        pass
    return ips


def _load_env_file(path):
    """Load a .env file into os.environ (does not overwrite existing vars)."""
    if not path.exists():
        return
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            key, _, value = line.partition('=')
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


# Load .env file before reading config (env vars take precedence over .env)
_load_env_file(ENV_FILE)

# ── SMTP / Email Configuration ──────────────────────────────────────
# Priority: CLI args > env vars > .env file > defaults
# To configure permanently, edit action/dashboard/.env (see .env.example)
# Examples:
#   Gmail:    MUE_SMTP_HOST=smtp.gmail.com MUE_SMTP_PORT=587 MUE_SMTP_USER=you@gmail.com MUE_SMTP_PASS=app-password
#   Outlook:  MUE_SMTP_HOST=smtp.office365.com MUE_SMTP_PORT=587 MUE_SMTP_USER=you@outlook.com MUE_SMTP_PASS=yourpass
#   Local:    MUE_SMTP_HOST=localhost MUE_SMTP_PORT=25 (no auth)
SMTP_HOST = os.environ.get('MUE_SMTP_HOST', '')
SMTP_PORT = int(os.environ.get('MUE_SMTP_PORT', '587'))
SMTP_USER = os.environ.get('MUE_SMTP_USER', '')
SMTP_PASS = os.environ.get('MUE_SMTP_PASS', '')
SMTP_FROM = os.environ.get('MUE_SMTP_FROM', SMTP_USER or 'mue-review-server@localhost')
SMTP_USE_TLS = os.environ.get('MUE_SMTP_TLS', 'true').lower() == 'true'
DAILY_SUMMARY_HOUR = int(os.environ.get('MUE_SUMMARY_HOUR', '6'))  # 6 AM default
ADMIN_EMAIL = os.environ.get('MUE_ADMIN_EMAIL', 'dylan@bicyclebi.com')  # receives all reviewer input
DAILY_SUMMARY_MINUTE = int(os.environ.get('MUE_SUMMARY_MINUTE', '0'))


# ── State ──────────────────────────────────────────────────────────────
_reviews_lock = threading.Lock()
_connected_clients = set()
_client_lock = threading.Lock()

# Edit locks: {(artifactId, reviewId): {name, timestamp, ttl}}
_edit_locks = {}
_edit_locks_lock = threading.Lock()
LOCK_TTL = 600  # 10 minutes — auto-release if editor disconnects

# Presence tracking: {name: {last_seen, color, avatar}}
_presence = {}
_presence_lock = threading.Lock()
PRESENCE_TTL = 30  # 30s — offline if no heartbeat in 30s

# Profile access control: only these usernames can edit any profile
ADMIN_USERS = ['jane_doe', 'dylan_bi']

# Test Proxy Reviewer — invisible automated testing profile
TPR_USERNAME = 'tpr_bot'

# TPL access secret — separate from SERVER_ACCESS_TOKEN.
# When set, TPL generate/cleanup endpoints require this secret
# (via X-TPL-Secret header). Without it, anyone with the main token
# can trigger TPL operations. Set via --tpl-secret CLI argument.
TPL_SECRET = None

# Test Proxy Learner — generates temporary dummy learner data for data-flow testing
TPL_USERNAME = 'tpl_bot'

# ── Security: blocked static files (never served, even with valid token) ──
BLOCKED_STATIC_PATTERNS = (
    '.env', '.env.', '.git', '.gitignore', '.gitattributes',
    'config.json', 'credentials', 'secrets',
)

# ── Rate limiter: simple in-memory IP-based throttle ──
_rate_limit_store = {}
_rate_limit_lock = threading.Lock()
RATE_LIMIT_WINDOW = 60        # seconds
RATE_LIMIT_MAX_REQUESTS = 60   # max requests per window per IP


def _check_rate_limit(ip):
    """Return True if request is allowed, False if rate-limited."""
    now = time.time()
    with _rate_limit_lock:
        window_start = now - RATE_LIMIT_WINDOW
        # Prune stale entries
        if ip in _rate_limit_store:
            _rate_limit_store[ip] = [t for t in _rate_limit_store[ip] if t > window_start]
            if len(_rate_limit_store[ip]) >= RATE_LIMIT_MAX_REQUESTS:
                return False
            _rate_limit_store[ip].append(now)
        else:
            _rate_limit_store[ip] = [now]
    return True


def _is_blocked_static(path):
    """Return True if the path matches a blocked static file pattern."""
    clean = path.lstrip('/').lower()
    for pat in BLOCKED_STATIC_PATTERNS:
        if clean == pat or clean.startswith(pat + '/') or clean.startswith(pat + '\\'):
            return True
        # Also block extension-like matches: .env, .env.local, etc.
        if pat.endswith('.') and clean.startswith(pat):
            return True
    return False


def _esc_html(s):
    """HTML-escape a string for safe email rendering. Replaces &, <, >, quotes."""
    if not isinstance(s, str):
        s = str(s or '')
    return (s
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&#39;'))


_VALID_RATINGS = frozenset(['👍 Pass', '⚡ Needs Work', '❌ Rework'])


def load_reviews():
    """Load reviews from review/reviews.json."""
    if not REVIEWS_PATH.exists():
        return {}
    try:
        with open(REVIEWS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def load_profiles():
    """Load reviewer profiles from review/reviewer_profiles.json."""
    if not PROFILES_PATH.exists():
        return {}
    try:
        with open(PROFILES_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_profiles(data):
    """Save reviewer profiles (thread-safe)."""
    PROFILES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _reviews_lock:
        with open(PROFILES_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def save_reviews(data):
    """Save reviews to review/reviews.json (thread-safe)."""
    REVIEWS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _reviews_lock:
        with open(REVIEWS_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# ── Activity Log ─────────────────────────────────────────────────────
def load_activity():
    """Load activity log from review/profile_activity.json."""
    if not ACTIVITY_PATH.exists():
        return []
    try:
        with open(ACTIVITY_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_activity(data):
    """Save activity log (thread-safe, last 500 entries)."""
    ACTIVITY_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Keep only the last 500 entries to avoid unbounded growth
    trimmed = data[-500:]
    with _reviews_lock:
        with open(ACTIVITY_PATH, 'w', encoding='utf-8') as f:
            json.dump(trimmed, f, indent=2, ensure_ascii=False)


def log_activity(username, action, detail, metadata=None):
    """Append an activity entry for a profile."""
    entry = {
        'username': username,
        'action': action,
        'detail': detail,
        'timestamp': datetime.now().isoformat(),
    }
    if metadata:
        entry['metadata'] = metadata
    activities = load_activity()
    activities.append(entry)
    save_activity(activities)


def rebuild_data_json():
    """Run build_data.py to regenerate data.json."""
    try:
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        result = subprocess.run(
            [sys.executable, str(BUILD_SCRIPT)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
            encoding='utf-8',
            errors='replace'
        )
        if result.returncode == 0:
            log('INFO', 'data.json rebuilt')
        else:
            err = result.stderr.strip().split('\n')[-1] if result.stderr else 'unknown'
            log('WARNING', f'build failed: {err}')
    except Exception as e:
        log('ERROR', f'build error: {e}')


def generate_id():
    """Generate a unique review ID."""
    import random
    return str(int(time.time() * 1000)) + random.randint(1000, 9999).__format__('d')


def _cleanup_expired_locks():
    """Remove expired locks (called periodically)."""
    now = time.time()
    with _edit_locks_lock:
        expired = [k for k, v in _edit_locks.items() if now - v['timestamp'] > v.get('ttl', LOCK_TTL)]
        for k in expired:
            del _edit_locks[k]


def _get_all_locks():
    """Return all active (non-expired) locks."""
    _cleanup_expired_locks()
    with _edit_locks_lock:
        return {f"{k[0]}::{k[1]}": v for k, v in _edit_locks.items()}


def _claim_lock(artifact_id, review_id, name, ttl=LOCK_TTL):
    """Claim an edit lock. Returns (ok, error_msg)."""
    _cleanup_expired_locks()
    key = (artifact_id, review_id)
    with _edit_locks_lock:
        existing = _edit_locks.get(key)
        if existing and existing['name'] != name:
            return False, f"{existing['name']} is currently editing this review"
        _edit_locks[key] = {'name': name, 'timestamp': time.time(), 'ttl': ttl}
    return True, None


def _release_lock(artifact_id, review_id, name):
    """Release an edit lock. Returns True if released."""
    key = (artifact_id, review_id)
    with _edit_locks_lock:
        existing = _edit_locks.get(key)
        if existing and existing['name'] == name:
            del _edit_locks[key]
            return True
    return False


def _check_lock(artifact_id, review_id):
    """Check if a review is locked. Returns lock info or None."""
    _cleanup_expired_locks()
    key = (artifact_id, review_id)
    with _edit_locks_lock:
        return _edit_locks.get(key)


# ── Presence helpers ─────────────────────────────────────────────────

def _cleanup_stale_presence():
    """Remove reviewers who haven't sent a heartbeat in PRESENCE_TTL seconds."""
    now = time.time()
    with _presence_lock:
        stale = [name for name, info in _presence.items() if now - info['last_seen'] > PRESENCE_TTL]
        for name in stale:
            del _presence[name]


def _heartbeat_presence(name, display_name=None, color=None, avatar=None, active_page=None, active_artifact=None, active_label=None):
    """Update reviewer's last-seen timestamp and current location."""
    now = time.time()
    with _presence_lock:
        if name in _presence:
            _presence[name]['last_seen'] = now
            if display_name:
                _presence[name]['display_name'] = display_name
            if color:
                _presence[name]['color'] = color
            if avatar:
                _presence[name]['avatar'] = avatar
            if active_page is not None:
                _presence[name]['active_page'] = active_page
            if active_artifact is not None:
                _presence[name]['active_artifact'] = active_artifact
            if active_label is not None:
                _presence[name]['active_label'] = active_label
        else:
            _presence[name] = {
                'last_seen': now,
                'display_name': display_name or name,
                'color': color or '#7c73ff',
                'avatar': avatar or '',
                'active_page': active_page or '',
                'active_artifact': active_artifact or '',
                'active_label': active_label or ''
            }


def _leave_presence(name):
    """Remove a reviewer from presence list."""
    with _presence_lock:
        _presence.pop(name, None)


def _get_all_presence():
    """Return all reviewers with online/offline status and current location."""
    _cleanup_stale_presence()
    now = time.time()
    with _presence_lock:
        result = []
        for name, info in _presence.items():
            if name == TPR_USERNAME:
                continue
            result.append({
                'name': name,
                'display_name': info.get('display_name', name),
                'color': info.get('color', '#7c73ff'),
                'avatar': info.get('avatar', ''),
                'last_seen': info['last_seen'],
                'online': (now - info['last_seen']) <= PRESENCE_TTL,
                'active_page': info.get('active_page', ''),
                'active_artifact': info.get('active_artifact', ''),
                'active_label': info.get('active_label', '')
            })
        return result


# ── Daily Summary Email ──────────────────────────────────────────────

def _load_dashboard_data():
    """Load the dashboard data.json for learner progress context."""
    data_path = os.path.join(DASHBOARD_DIR, 'data.json')
    if os.path.exists(data_path):
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _compute_learner_progress(data):
    """Compute learner progress metrics from dashboard data."""
    notes = data.get('notes', [])
    summary = data.get('summary', {})
    level_prog = summary.get('level_progression', {})
    current_level = level_prog.get('current_level', 1)
    levels = level_prog.get('levels', {})
    
    # Current level info
    lvl_info = levels.get(current_level, {})
    days_completed = lvl_info.get('days_completed', 0)
    days_required = lvl_info.get('days_required', 28)
    
    # Overall progress
    total_days = summary.get('total_days', 0)
    working_days_elapsed = summary.get('working_days_elapsed', 0)
    calendar_status = summary.get('calendar_status', 'no_data')
    
    # Classification
    latest_classification = 'Not Started'
    if notes:
        latest_note = max(notes, key=lambda n: n.get('date', ''))
        latest_classification = latest_note.get('classification', 'Not Started')
    
    # Proof tasks
    proof_tasks = summary.get('proof_tasks', {})
    completed_proofs = sum(1 for v in proof_tasks.values() if v)
    total_proofs = len(proof_tasks)
    
    # Codex gates
    codex_gates = summary.get('codex_gate_status', {})
    passed_gates = sum(1 for v in codex_gates.values() if v == 'Yes')
    total_gates = len(codex_gates)
    
    # Scorecard areas
    scorecard = summary.get('scorecard_trend', {})
    scored_areas = sum(1 for v in scorecard.values() if v and v[-1].get('score') != 'Unscored')
    total_areas = len(scorecard)
    
    # Category coverage from notes
    category_counts = {}
    for n in notes:
        cats = n.get('category_tags', '')
        for cat in cats.split(','):
            cat = cat.strip()
            if cat:
                category_counts[cat] = category_counts.get(cat, 0) + 1
    
    return {
        'current_level': current_level,
        'level_label': lvl_info.get('label', 'Foundation'),
        'level_emoji': lvl_info.get('emoji', '🌱'),
        'days_completed': days_completed,
        'days_required': days_required,
        'total_days': total_days,
        'working_days_elapsed': working_days_elapsed,
        'calendar_status': calendar_status,
        'latest_classification': latest_classification,
        'completed_proofs': completed_proofs,
        'total_proofs': total_proofs,
        'passed_gates': passed_gates,
        'total_gates': total_gates,
        'scored_areas': scored_areas,
        'total_areas': total_areas,
        'category_counts': category_counts,
        'notes_count': len(notes),
    }


def _compute_outstanding_tasks(data, progress):
    """Compute outstanding/incomplete tasks relative to curriculum standards."""
    outstanding = []
    notes = data.get('notes', [])
    summary = data.get('summary', {})
    
    # 1. Missing daily notes (days without notes up to current day)
    current_day = progress.get('days_completed', 0)
    if current_day > 0:
        noted_days = set(n.get('day_number') for n in notes if n.get('day_number'))
        missing_days = [d for d in range(1, current_day + 1) if d not in noted_days]
        if missing_days:
            outstanding.append({
                'category': '📅 Daily Notes',
                'item': f'{len(missing_days)} missing daily note(s) (Days: {", ".join(map(str, missing_days[:10]))}{"..." if len(missing_days) > 10 else ""})',
                'priority': 'High' if len(missing_days) > 3 else 'Medium'
            })
    
    # 2. Unscored scorecard areas
    scorecard = summary.get('scorecard_trend', {})
    unscored = [area for area, entries in scorecard.items() if not entries or entries[-1].get('score') == 'Unscored']
    if unscored:
        outstanding.append({
            'category': '🏆 Scorecard',
            'item': f'{len(unscored)} unscored area(s): {", ".join(unscored[:5])}{"..." if len(unscored) > 5 else ""}',
            'priority': 'High'
        })
    
    # 3. Incomplete proof tasks
    proof_tasks = summary.get('proof_tasks', {})
    incomplete_proofs = [pt for pt, done in proof_tasks.items() if not done]
    if incomplete_proofs:
        outstanding.append({
            'category': '✅ Proof Tasks',
            'item': f'{len(incomplete_proofs)} incomplete: {", ".join(incomplete_proofs[:5])}{"..." if len(incomplete_proofs) > 5 else ""}',
            'priority': 'High'
        })
    
    # 4. Unpassed Codex gates
    codex_gates = summary.get('codex_gate_status', {})
    unpassed_gates = [gate for gate, status in codex_gates.items() if status != 'Yes']
    if unpassed_gates:
        outstanding.append({
            'category': '🚪 Codex Gate',
            'item': f'{len(unpassed_gates)} gate(s) not passed: {", ".join(unpassed_gates[:5])}{"..." if len(unpassed_gates) > 5 else ""}',
            'priority': 'Critical'
        })
    
    # 5. Category coverage gaps (8 categories expected)
    expected_categories = ['🤖 AI', '⚡ Codex', '🏗️ Pyr', '📊 BI', '🔗 Data', '📦 Del', '🧠 Ret', '💬 Team']
    category_counts = progress.get('category_counts', {})
    missing_cats = [cat for cat in expected_categories if cat not in category_counts or category_counts[cat] == 0]
    if missing_cats:
        outstanding.append({
            'category': '📚 Curriculum Coverage',
            'item': f'{len(missing_cats)} category(ies) with no activity: {", ".join(missing_cats)}',
            'priority': 'Medium'
        })
    
    # 6. Missing required artifacts (from notes)
    missing_artifacts = []
    for n in notes:
        artifact = n.get('required_artifact')
        if artifact and artifact not in str(data.get('evidence', [])):
            missing_artifacts.append(f"Day {n.get('day_number')}: {artifact}")
    if missing_artifacts:
        outstanding.append({
            'category': '📁 Evidence Artifacts',
            'item': f'{len(missing_artifacts)} missing: {", ".join(missing_artifacts[:5])}{"..." if len(missing_artifacts) > 5 else ""}',
            'priority': 'Medium'
        })
    
    return outstanding


def _compile_daily_summary(hours=24):
    """Compile review activity + learner progress from the last N hours into a structured summary."""
    reviews = load_reviews()
    profiles = load_profiles()
    data = _load_dashboard_data()
    progress = _compute_learner_progress(data)
    outstanding = _compute_outstanding_tasks(data, progress)
    cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

    who = {}       # {name: {display, reviews_count, ratings: {pass, needs_work, rework}}}
    what = []      # [{artifact, name, rating, text, timestamp}]
    when_oldest = None
    when_newest = None

    for artifact_id, review_list in reviews.items():
        for r in review_list:
            ts = r.get('timestamp', '')
            if ts < cutoff:
                continue
            # Skip TPR bot reviews — only real reviewer data in summaries
            name = r.get('name', 'Unknown')
            if name == TPR_USERNAME or r.get('role', '').strip() == 'Test Proxy':
                continue
            rating = r.get('rating', '?')
            if name not in who:
                profile = profiles.get(name.lower().replace(' ', '_'), {})
                who[name] = {
                    'display': profile.get('displayName', name),
                    'email': profile.get('email', ''),
                    'reviews_count': 0,
                    'ratings': {'👍 Pass': 0, '⚡ Needs Work': 0, '❌ Rework': 0}
                }
            who[name]['reviews_count'] += 1
            if rating in who[name]['ratings']:
                who[name]['ratings'][rating] += 1
            what.append({
                'artifact': artifact_id,
                'name': name,
                'rating': rating,
                'text': r.get('text', '')[:200],
                'timestamp': ts
            })
            if not when_oldest or ts < when_oldest:
                when_oldest = ts
            if not when_newest or ts > when_newest:
                when_newest = ts

    total_reviews = len(what)
    total_reviewers = len(who)
    pass_count = sum(1 for w in what if w['rating'] == '👍 Pass')
    pass_rate = f"{pass_count}/{total_reviews} ({pass_count*100//total_reviews}%)" if total_reviews else 'N/A'

    return {
        'hours': hours,
        'total_reviews': total_reviews,
        'total_reviewers': total_reviewers,
        'pass_rate': pass_rate,
        'who': who,
        'what': sorted(what, key=lambda x: x['timestamp'], reverse=True),
        'when_oldest': when_oldest,
        'when_newest': when_newest,
        'learner_progress': progress,
        'outstanding_tasks': outstanding,
    }


def _build_summary_html(summary):
    """Build an HTML email body from a summary dict."""
    who = summary['who']
    what = summary['what']
    learner_progress = summary.get('learner_progress', {})
    outstanding_tasks = summary.get('outstanding_tasks', [])

    who_rows = ''
    for name, info in who.items():
        ratings = info['ratings']
        safe_display = _esc_html(info["display"])
        safe_name = _esc_html(name.lower().replace(" ","_"))
        who_rows += f'''<tr style="border-bottom:1px solid #eee">
          <td style="padding:8px 12px;font-weight:600">{safe_display} <span style="color:#888">@{safe_name}</span></td>
          <td style="padding:8px;text-align:center">{info["reviews_count"]}</td>
          <td style="padding:8px;text-align:center;color:#198754">{ratings["👍 Pass"]}</td>
          <td style="padding:8px;text-align:center;color:#ffc107">{ratings["⚡ Needs Work"]}</td>
          <td style="padding:8px;text-align:center;color:#dc3545">{ratings["❌ Rework"]}</td>
        </tr>'''

    review_rows = ''
    for r in what[:20]:  # show up to 20 most recent
        rc = '#198754' if 'Pass' in r['rating'] else ('#dc3545' if 'Rework' in r['rating'] else '#ffc107')
        ts = r['timestamp'][:16].replace('T', ' ')
        safe_name = _esc_html(r["name"])
        safe_artifact = _esc_html(r["artifact"])
        safe_rating = _esc_html(r["rating"])
        safe_text = _esc_html(r["text"])
        review_rows += f'''<tr style="border-bottom:1px solid #f0f0f0">
          <td style="padding:6px 12px;font-size:13px">{ts}</td>
          <td style="padding:6px;font-size:13px;font-weight:600">{safe_name}</td>
          <td style="padding:6px;font-size:13px">{safe_artifact}</td>
          <td style="padding:6px"><span style="background:{rc};color:#fff;padding:2px 8px;border-radius:4px;font-size:12px">{safe_rating}</span></td>
          <td style="padding:6px;font-size:12px;color:#555;max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{safe_text}</td>
        </tr>'''

    # Learner Progress Section
    progress_html = ''
    if learner_progress:
        prog = learner_progress
        progress_html = f'''
      <h2 style="font-size:15px;color:#333;margin:24px 0 8px">🎓 Learner Progress</h2>
      <table style="width:100%;margin-bottom:20px"><tr>
        <td style="background:#eef7f2;border-radius:8px;padding:12px;text-align:center;width:25%"><div style="font-size:22px;font-weight:700;color:#198754">{prog.get("current_day", 0)}/28</div><div style="font-size:11px;color:#888">Days Completed</div></td>
        <td style="background:#eef2fa;border-radius:8px;padding:12px;text-align:center;width:25%"><div style="font-size:22px;font-weight:700;color:#6c5ce7">{prog.get("current_week", 0)}/4</div><div style="font-size:11px;color:#888">Weeks Completed</div></td>
        <td style="background:#faf6ea;border-radius:8px;padding:12px;text-align:center;width:25%"><div style="font-size:22px;font-weight:700;color:#d49330">{prog.get("evidence_count", 0)}</div><div style="font-size:11px;color:#888">Evidence Files</div></td>
        <td style="background:#fef3c7;border-radius:8px;padding:12px;text-align:center;width:25%"><div style="font-size:22px;font-weight:700;color:#92400e">{prog.get("classification", "Foundational")}</div><div style="font-size:11px;color:#888">Classification</div></td>
      </tr></table>
      <div style="font-size:12px;color:#555;margin-bottom:12px"><strong>Level:</strong> {prog.get("current_level", 1)} ({prog.get("level_label", "Foundation")}) · <strong>Codex Gates:</strong> {prog.get("codex_gates_passed", 0)}/9 passed · <strong>Proof Tasks:</strong> {prog.get("proof_tasks_completed", 0)}/6 completed</div>'''

    # Outstanding Tasks Section
    outstanding_html = ''
    if outstanding_tasks:
        rows = ''
        for ot in outstanding_tasks:
            priority_color = {'Critical': '#dc3545', 'High': '#fd7e14', 'Medium': '#ffc107', 'Low': '#198754'}.get(ot.get('priority', 'Medium'), '#6c757d')
            rows += f'''<tr style="border-bottom:1px solid #f0f0f0">
              <td style="padding:8px 12px;font-weight:600">{_esc_html(ot.get('category', ''))}</td>
              <td style="padding:8px 12px">{_esc_html(ot.get('item', ''))}</td>
              <td style="padding:8px;text-align:center"><span style="background:{priority_color};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px">{_esc_html(ot.get('priority', 'Medium'))}</span></td>
            </tr>'''
        outstanding_html = f'''
      <h2 style="font-size:15px;color:#333;margin:24px 0 8px">⚠️ Outstanding / Incomplete Tasks (vs Curriculum Standards)</h2>
      <table style="width:100%;border-collapse:collapse;border:1px solid #eee;border-radius:8px;overflow:hidden">
        <tr style="background:#f8f9fa"><th style="padding:8px 12px;text-align:left;font-size:12px">Category</th><th style="padding:8px;text-align:left;font-size:12px">Details</th><th style="padding:8px;text-align:center;font-size:12px">Priority</th></tr>
        {rows}
      </table>'''

    period = f"Last {summary['hours']}h"
    when = f"{summary['when_oldest'][:16].replace('T',' ')} — {summary['when_newest'][:16].replace('T',' ')}" if summary['when_oldest'] else 'N/A'

    return f'''<!DOCTYPE html><html><body style="font-family:system-ui,sans-serif;background:#f5f5f5;padding:20px">
  <div style="max-width:640px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.08)">
    <div style="background:linear-gradient(135deg,#6c5ce7,#a29bfe);padding:24px;color:#fff">
      <h1 style="margin:0;font-size:20px">📬 MUE Daily Review Summary</h1>
      <p style="margin:6px 0 0;opacity:.85;font-size:13px">{period} · Generated {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
    </div>
    <div style="padding:20px 24px">
      <h2 style="font-size:15px;color:#333;margin:0 0 12px">📊 Overview</h2>
      <table style="width:100%;margin-bottom:20px"><tr>
        <td style="background:#f8f9fa;border-radius:8px;padding:12px;text-align:center;width:33%"><div style="font-size:22px;font-weight:700;color:#6c5ce7">{summary["total_reviews"]}</div><div style="font-size:11px;color:#888">Reviews</div></td>
        <td style="background:#f8f9fa;border-radius:8px;padding:12px;text-align:center;width:33%"><div style="font-size:22px;font-weight:700;color:#6c5ce7">{summary["total_reviewers"]}</div><div style="font-size:11px;color:#888">Reviewers</div></td>
        <td style="background:#f8f9fa;border-radius:8px;padding:12px;text-align:center;width:33%"><div style="font-size:22px;font-weight:700;color:#198754">{summary["pass_rate"]}</div><div style="font-size:11px;color:#888">Pass Rate</div></td>
      </tr></table>

      <h2 style="font-size:15px;color:#333;margin:0 0 8px">👥 Who Reviewed</h2>
      <table style="width:100%;border-collapse:collapse;margin-bottom:20px;border:1px solid #eee;border-radius:8px;overflow:hidden">
        <tr style="background:#f8f9fa"><th style="padding:8px 12px;text-align:left;font-size:12px">Reviewer</th><th style="padding:8px;text-align:center;font-size:12px">Total</th><th style="padding:8px;text-align:center;font-size:12px;color:#198754">Pass</th><th style="padding:8px;text-align:center;font-size:12px;color:#ffc107">Needs Work</th><th style="padding:8px;text-align:center;font-size:12px;color:#dc3545">Rework</th></tr>
        {who_rows}
      </table>

      <h2 style="font-size:15px;color:#333;margin:0 0 8px">📝 What Was Reviewed</h2>
      <table style="width:100%;border-collapse:collapse;border:1px solid #eee;border-radius:8px;overflow:hidden">
        <tr style="background:#f8f9fa"><th style="padding:8px 12px;text-align:left;font-size:12px">When</th><th style="padding:8px;text-align:left;font-size:12px">Who</th><th style="padding:8px;text-align:left;font-size:12px">Artifact</th><th style="padding:8px;text-align:left;font-size:12px">Rating</th><th style="padding:8px;text-align:left;font-size:12px">Comment</th></tr>
        {review_rows}
      </table>

      {progress_html}
      {outstanding_html}

      <p style="font-size:11px;color:#aaa;margin:20px 0 0;text-align:center">Period: {when}<br>Sent by MUE Review Server · <a href="{_SERVER_BASE_URL}/go" style="color:#6c5ce7">Open Dashboard</a></p>
    </div>
  </div></body></html>'''


def _send_email(to_addr, subject, html_body):
    """Send an email via SMTP. Returns (ok, error_msg)."""
    if not SMTP_HOST:
        return False, 'SMTP not configured — set MUE_SMTP_HOST environment variable'
    if not to_addr:
        return False, 'No recipient email address'
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SMTP_FROM
        msg['To'] = to_addr
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        if SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15)
        else:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15)
            if SMTP_USE_TLS:
                server.starttls()
        if SMTP_USER and SMTP_PASS:
            server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_FROM, [to_addr], msg.as_string())
        server.quit()
        return True, None
    except Exception as e:
        return False, str(e)


def send_daily_summaries():
    """Compile and send daily summaries to all opted-in reviewers + admin."""
    log('INFO', 'Running daily summary...')
    summary = _compile_daily_summary(hours=24)
    if summary['total_reviews'] == 0:
        log('INFO', 'No reviews in the last 24h — skipping email')
        return 0

    html_body = _build_summary_html(summary)
    profiles = load_profiles()
    sent_count = 0

    # Send to opted-in reviewers
    for username, profile in profiles.items():
        if not profile.get('dailySummary') or not profile.get('email'):
            continue
        email = profile['email']
        display = profile.get('displayName', username)
        ok, err = _send_email(email, f'📬 MUE Daily Summary — {summary["total_reviews"]} review(s), {summary["total_reviewers"]} reviewer(s)', html_body)
        if ok:
            log('INFO', f'Summary sent to {display} <{email}>')
            sent_count += 1
        else:
            log('WARNING', f'Failed to send to {display} <{email}>: {err}')

    # Also send to admin (comprehensive assessment of all reviewer input)
    if ADMIN_EMAIL:
        ok, err = _send_email(ADMIN_EMAIL, f'📬 MUE Admin Daily Summary — {summary["total_reviews"]} review(s), {summary["total_reviewers"]} reviewer(s)', html_body)
        if ok:
            log('INFO', f'Admin summary sent to {ADMIN_EMAIL}')
            sent_count += 1
        else:
            log('WARNING', f'Failed to send admin summary: {err}')

    log('INFO', f'Daily summary complete — {sent_count} email(s) sent')
    return sent_count


# ── Tunnel Support ───────────────────────────────────────────────────

def _find_tunnel_tool():
    """Detect available tunnel tool. Returns (tool_name, cmd_list) or None."""
    import shutil
    import subprocess
    # Try cloudflared first (free, no account needed)
    cf = shutil.which('cloudflared')
    if cf:
        return ('cloudflared', cf)
    # Try ngrok
    ng = shutil.which('ngrok')
    if ng:
        return ('ngrok', ng)
    return None


def _start_tunnel(port, tool_path, tool_name, max_retries=10, retry_delay=5):
    """Start a tunnel in a background thread, print public URL when ready.
    
    Auto-restarts on failure with exponential backoff.
    Sends email notifications for each new URL and restart.
    
    Args:
        port: Local port to tunnel
        tool_path: Path to tunnel executable
        tool_name: 'cloudflared' or 'ngrok'
        max_retries: Maximum restart attempts (0 = infinite)
        retry_delay: Initial delay between retries (seconds, doubles each retry)
    """
    import subprocess
    import re
    import time

    TUNNEL_NOTIFY_EMAIL = os.environ.get('MUE_TUNNEL_NOTIFY_EMAIL', 'monteretroion@gmail.com')
    attempt = 0
    
    while True:
        attempt += 1
        if max_retries > 0 and attempt > max_retries:
            log('ERROR', f'Tunnel max retries ({max_retries}) exhausted — giving up')
            _tunnel_notify_down(TUNNEL_NOTIFY_EMAIL, tool_name, reason='max retries exhausted')
            break
        
        if attempt > 1:
            delay = min(retry_delay * (2 ** (attempt - 2)), 120)  # Exponential backoff, max 2 min
            log('INFO', f'Restarting tunnel in {delay}s (attempt {attempt}/{max_retries or "∞"})...')
            time.sleep(delay)
        
        if tool_name == 'cloudflared':
            cmd = [tool_path, 'tunnel', '--url', f'http://localhost:{port}', '--no-autoupdate']
        elif tool_name == 'ngrok':
            cmd = [tool_path, 'http', str(port)]
        else:
            log('ERROR', f'Unknown tunnel tool: {tool_name}')
            return

        log('INFO', f'Starting {tool_name} tunnel (attempt {attempt})...')
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            url_found = False
            stdout = proc.stdout
            if not stdout:
                log('ERROR', f'{tool_name} failed to start')
                continue
            
            for line in stdout:
                line = line.strip()
                # cloudflared prints URL to stderr/stdout with 'trycloudflare.com'
                # ngrok prints URL with 'ngrok.io' or 'ngrok-free.app'
                match = re.search(r'(https://[a-zA-Z0-9.-]+\.(?:trycloudflare\.com|ngrok(?:-free)?\.app)[^\s]*)', line)
                if match and not url_found:
                    public_url = match.group(1)
                    url_found = True
                    go_url = f'{public_url}/go'
                    log('INFO', f'PUBLIC URL: {go_url}')
                    log('INFO', 'Share this URL with reviewers on any network.')
                    log('INFO', 'The tunnel stays open while the server is running.')
                    # Email notification with attempt info
                    _tunnel_notify_url(TUNNEL_NOTIFY_EMAIL, public_url, tool_name, attempt)
            
            if not url_found:
                log('WARNING', f'{tool_name} started but URL not captured. Check the terminal.')
            
            # Monitor tunnel process — wait for it to exit
            proc.wait()
            exit_code = proc.returncode
            
            # Tunnel exited — log and prepare to restart
            if _scheduler_running:
                if exit_code == 0:
                    log('WARNING', f'{tool_name} tunnel exited cleanly (code 0)')
                else:
                    log('WARNING', f'{tool_name} tunnel disconnected (exit code {exit_code})')
                
                # Only notify if we're going to stop (max retries exceeded)
                if max_retries > 0 and attempt >= max_retries:
                    _tunnel_notify_down(TUNNEL_NOTIFY_EMAIL, tool_name, 
                                        reason=f'exit code {exit_code}, max retries reached')
                else:
                    log('INFO', f'Tunnel will auto-restart in a few seconds...')
        
        except FileNotFoundError:
            log('ERROR', f'{tool_name} not found — install it from https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/')
            _tunnel_notify_down(TUNNEL_NOTIFY_EMAIL, tool_name, reason=f'{tool_name} not found')
            break
        except Exception as e:
            log('ERROR', f'Tunnel error: {e}')
            if _scheduler_running and (max_retries <= 0 or attempt < max_retries):
                log('INFO', 'Will retry tunnel in a few seconds...')
                continue
            else:
                _tunnel_notify_down(TUNNEL_NOTIFY_EMAIL, tool_name, reason=str(e))
                break


def _tunnel_notify_url(to_addr, public_url, tool_name, attempt=1):
    """Send email when a new tunnel URL is available."""
    # Build shareable URL — /go handles token injection server-side
    secure_url = f'{public_url}/go'
    attempt_info = f' · Attempt {attempt}' if attempt > 1 else ''
    subject = f'🌐 MUE Tunnel Active — {tool_name}{attempt_info}'
    body = f'''<!DOCTYPE html><html><body style="font-family:system-ui,sans-serif;background:#f5f5f5;padding:20px">
  <div style="max-width:520px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.08)">
    <div style="background:linear-gradient(135deg,#6c5ce7,#a29bfe);padding:24px;color:#fff">
      <h1 style="margin:0;font-size:18px">🌐 MUE Tunnel Active</h1>
      <p style="margin:6px 0 0;opacity:.85;font-size:13px">{tool_name} · {datetime.now().strftime("%Y-%m-%d %H:%M")}{attempt_info}</p>
    </div>
    <div style="padding:20px 24px">
      <p style="font-size:14px;color:#333;margin:0 0 16px">A new tunnel URL has been generated. Share this with reviewers:</p>
      <div style="background:#f8f9fa;border-radius:8px;padding:16px;text-align:center;margin-bottom:16px">
        <a href="{secure_url}" style="font-size:16px;font-weight:600;color:#6c5ce7;text-decoration:none;word-break:break-all">{secure_url}</a>
      </div>
      {"<p style='font-size:12px;color:#28a745;margin:0 0 8px;text-align:center'>✅ Auto-restarted after disconnection</p>" if attempt > 1 else ""}
      <p style="font-size:11px;color:#aaa;margin:0;text-align:center">This URL will change if the tunnel is restarted.<br>Sent by MUE Review Server</p>
    </div>
  </div></body></html>'''
    ok, err = _send_email(to_addr, subject, body)
    if ok:
        log('INFO', f'Tunnel notification sent to {to_addr}')
    else:
        log('WARNING', f'Could not send tunnel email: {err}')


def _tunnel_notify_down(to_addr, tool_name, reason='unknown'):
    """Send email when the tunnel disconnects permanently."""
    subject = f'⚠️ MUE Tunnel Disconnected — {tool_name}'
    body = f'''<!DOCTYPE html><html><body style="font-family:system-ui,sans-serif;background:#f5f5f5;padding:20px">
  <div style="max-width:520px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.08)">
    <div style="background:linear-gradient(135deg,#dc3545,#e57373);padding:24px;color:#fff">
      <h1 style="margin:0;font-size:18px">⚠️ Tunnel Disconnected</h1>
      <p style="margin:6px 0 0;opacity:.85;font-size:13px">{tool_name} · {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
    </div>
    <div style="padding:20px 24px">
      <p style="font-size:14px;color:#333;margin:0 0 16px">The {tool_name} tunnel has stopped and could not auto-restart.</p>
      <p style="font-size:13px;color:#555;margin:0 0 8px"><strong>Reason:</strong> {reason}</p>
      <p style="font-size:13px;color:#555;margin:0 0 8px"><strong>To restore access:</strong></p>
      <ol style="font-size:13px;color:#555;margin:0;padding:0 0 0 20px;line-height:1.8">
        <li>Restart the review server with <code>--tunnel</code></li>
        <li>A new URL will be emailed automatically</li>
      </ol>
      <p style="font-size:11px;color:#aaa;margin:16px 0 0;text-align:center">Sent by MUE Review Server</p>
    </div>
  </div></body></html>'''
    ok, err = _send_email(to_addr, subject, body)
    if ok:
        log('INFO', f'Tunnel-down notification sent to {to_addr}')
    else:
        log('WARNING', f'Could not send tunnel-down email: {err}')


# ── Daily Scheduler ──────────────────────────────────────────────────

_scheduler_running = True


def _daily_scheduler_loop():
    """Background thread that fires daily summaries at the configured hour."""
    while _scheduler_running:
        now = datetime.now()
        target = now.replace(hour=DAILY_SUMMARY_HOUR, minute=DAILY_SUMMARY_MINUTE, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        wait_seconds = (target - now).total_seconds()
        log('INFO', f'Next daily summary at {target.strftime("%H:%M")} ({int(wait_seconds//3600)}h {int((wait_seconds%3600)//60)}m)')
        # Sleep in small increments so we can stop cleanly
        slept = 0
        while slept < wait_seconds and _scheduler_running:
            time.sleep(min(30, wait_seconds - slept))
            slept += 30
        if _scheduler_running:
            send_daily_summaries()


# ── Test Proxy Learner (TPL) — dummy generative data for data-flow testing ──

TPL_NOTES_DIR = REPO_ROOT / 'action' / 'notes'
TPL_EVIDENCE_DIR = REPO_ROOT / 'action' / 'evidence'

# Dummy note templates for TPL data generation
TPL_NOTE_TEMPLATES = [
    {
        'day': 1, 'date_offset': 0, 'classification': 'Foundational',
        'track': 'Pyramid operations', 'week': 1, 'artifact': 'pyramid_overview_screenshot.png',
        'learned': 'Set up development environment. Explored admin console and chat modes.',
        'evidence': 'Environment setup screenshots captured. Mode selection criteria documented.',
        'remains': 'Practice prompt crafting with real repo analysis.',
        'next_step': 'Build three reusable prompts and practice the Codex loop.',
    },
    {
        'day': 2, 'date_offset': 1, 'classification': 'Foundational',
        'track': 'Codex productivity', 'week': 1, 'artifact': 'codex_loop_diagram.png',
        'learned': 'Learned the Codex Loop: Pull → Summarize → Identify → Execute → Record.',
        'evidence': 'Codex loop diagram created. Handoff extraction template drafted.',
        'remains': 'Need to practice handoff extraction with real examples.',
        'next_step': 'Extract handoffs from three completed tasks.',
    },
    {
        'day': 3, 'date_offset': 2, 'classification': 'Foundational',
        'track': 'BI judgment', 'week': 1, 'artifact': 'business_question_list.md',
        'learned': 'Identified five business questions from team standup notes.',
        'evidence': 'Business question list created. Metric definitions drafted.',
        'remains': 'Metric validation needs practice.',
        'next_step': 'Validate two metrics against source data.',
    },
]

TPL_EVIDENCE_TEMPLATES = [
    {'filename': 'tpl_environment_setup.png', 'content': '# Environment Setup Evidence\n\nScreenshots of development environment configuration.\n'},
    {'filename': 'tpl_codex_loop_ref.md', 'content': '# Codex Loop Reference\n\n## Pull → Summarize → Identify → Execute → Record\n\nThis is a reference document for the Codex workflow.\n'},
]


def _generate_tpl_notes():
    """Generate dummy learner notes for TPL data-flow testing.
    Returns list of generated file paths."""
    TPL_NOTES_DIR.mkdir(parents=True, exist_ok=True)
    generated = []
    from datetime import date, timedelta
    base_date = date.today()
    for i, tmpl in enumerate(TPL_NOTE_TEMPLATES):
        note_date = base_date - timedelta(days=tmpl['date_offset'])
        filename = f"tpl_{note_date.isoformat()}.md"
        filepath = TPL_NOTES_DIR / filename
        content = f"""# Daily Note — Day {tmpl['day']}

**Date:** {note_date.isoformat()}
**Classification:** {tmpl['classification']}
**Primary track:** {tmpl['track']}
**Level:** 1
**Week Number:** {tmpl['week']}
**Day {tmpl['day']}**
**Required Artifact:** {tmpl['artifact']}

## What I learned today:
{tmpl['learned']}

## What evidence I produced:
{tmpl['evidence']}

## What remains open:
{tmpl['remains']}

## Next narrow step:
{tmpl['next_step']}

## Scorecard:
Prompt discipline: Unscored
Repo or workspace analysis: Unscored
Change isolation: Unscored
Validation order: Unscored
Deployment awareness: Unscored
Reviewer handoff: Unscored
Reusability: Unscored

## Codex gates:
One end-to-end workflow completed: No
Business-logic ownership understood: No
Validation evidence produced without help: No
Proof tasks completed: No
One clean reviewable change slice: No
One reusable team asset created: No
"""
        filepath.write_text(content, encoding='utf-8')
        generated.append(str(filepath))
    return generated


def _generate_tpl_evidence():
    """Generate dummy evidence files for TPL data-flow testing.
    Returns list of generated file paths."""
    TPL_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    generated = []
    for tmpl in TPL_EVIDENCE_TEMPLATES:
        filepath = TPL_EVIDENCE_DIR / tmpl['filename']
        filepath.write_text(tmpl['content'], encoding='utf-8')
        generated.append(str(filepath))
    return generated


def _cleanup_tpl_data():
    """Remove all TPL-generated dummy files (tpl_ prefix). Returns count removed."""
    removed = 0
    for d in [TPL_NOTES_DIR, TPL_EVIDENCE_DIR]:
        if not d.exists():
            continue
        for f in d.iterdir():
            if f.name.startswith('tpl_'):
                f.unlink()
                removed += 1
    return removed


def _cleanup_tpr_test_artifacts():
    """Remove all TPR/TPL test artifacts from reviews.json and activity logs.

    Cleans up:
    - review keys starting with 'tpr_test_' or 'tpl_security_test' from reviews.json
    - activity entries from tpr_bot / tpl_bot / Test Proxy in profile_activity.json
    - TPR bot profile from reviewer_profiles.json

    Returns dict with counts of removed items.
    """
    result = {'reviews_removed': 0, 'activities_removed': 0, 'profile_removed': False}

    # 1) Clean reviews.json — remove test artifact keys
    reviews = load_reviews()
    test_prefixes = ('tpr_test_', 'tpl_', '_integrity_test', '_audit_test', 'test')
    before = len(reviews)
    reviews = {k: v for k, v in reviews.items()
               if not any(k.startswith(p) or k == p for p in test_prefixes)}
    result['reviews_removed'] = before - len(reviews)
    if result['reviews_removed'] > 0:
        save_reviews(reviews)

    # 2) Clean activity log — remove TPR/TPL/test entries
    activities = load_activity()
    test_users = {TPR_USERNAME, TPL_USERNAME, 'Test Proxy', 'tester',
                  'test_user_a', 'Integrity Test', 'Integrity Test 2', 'Integrity Audit'}
    before_act = len(activities)
    activities = [a for a in activities if a.get('username', '') not in test_users]
    result['activities_removed'] = before_act - len(activities)
    if result['activities_removed'] > 0:
        save_activity(activities)

    # 3) Remove TPR bot profile from reviewer_profiles.json
    profiles = load_profiles()
    if TPR_USERNAME in profiles:
        del profiles[TPR_USERNAME]
        save_profiles(profiles)
        result['profile_removed'] = True

    return result



class ReviewHandler(SimpleHTTPRequestHandler):
    """HTTP handler: REST API for reviews + static file serving."""

    def __init__(self, *args, **kwargs):
        # Serve files from the dashboard directory
        super().__init__(*args, directory=str(DASHBOARD_DIR), **kwargs)

    def end_headers(self):
        # CORS headers for cross-origin access (file:// fallback)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.end_headers()

    def _get_client_ip(self):
        """Extract client IP from request."""
        forwarded = self.headers.get('X-Forwarded-For', '')
        if forwarded:
            return forwarded.split(',')[0].strip()
        return self.client_address[0]

    def _check_token(self, qs):
        """Verify access token from query string or Authorization header.
        Returns True if allowed, False if denied (sends 403)."""
        if not SERVER_ACCESS_TOKEN:
            return True  # No token required
        # Try Authorization: Bearer header first
        auth = self.headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            token = auth[7:]
            if token == SERVER_ACCESS_TOKEN:
                return True
        # Fallback to query string ?t=token
        token = qs.get('t', [''])[0]
        if token == SERVER_ACCESS_TOKEN:
            return True
        # Deny — send a generic 403 that reveals nothing about the server
        body = b'<!DOCTYPE html><html><head><title>403 Forbidden</title></head><body style="font-family:system-ui,sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;background:#f5f5f5"><div style="text-align:center;padding:40px;background:#fff;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,.08)"><h1 style="font-size:48px;margin:0;color:#dc3545">403</h1><p style="color:#666;margin:8px 0 0">Access denied</p><p style="color:#999;font-size:13px;margin:16px 0 0">Invalid or missing access token.</p></div></body></html>'
        self.send_response(403)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        return False

    def _handle_check_token(self, qs):
        """Check if a token is valid. Returns {valid: true/false}."""
        token = qs.get('t', [''])[0]
        valid = (not SERVER_ACCESS_TOKEN) or (token == SERVER_ACCESS_TOKEN)
        self._send_json(200, {'valid': valid})

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        # Rate limit check (skip for static files to avoid breaking dashboard loads)
        if path.startswith('/api/'):
            client_ip = self._get_client_ip()
            if not _check_rate_limit(client_ip):
                self.send_response(429)
                self.send_header('Content-Type', 'application/json')
                body = b'{"error":"Too many requests"}'
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

        # Token check — skip for token-check endpoint, /go redirect, data.json, and CORS preflight
        if path not in ('/api/check-token', '/go', '/data.json') and not self._check_token(qs):
            return

        if path == '/go':
            # Short redirect — /go → /dashboard.html?t=<token>
            token_qs = f'?t={SERVER_ACCESS_TOKEN}' if SERVER_ACCESS_TOKEN else ''
            self.send_response(302)
            self.send_header('Location', f'/dashboard.html{token_qs}')
            self.end_headers()
            return
        elif path == '/':
            # Root redirect — always go through /go so only one entry point exists
            self.send_response(302)
            self.send_header('Location', '/go')
            self.end_headers()
            return
        elif path == '/api/reviews':
            self._handle_get_reviews()
        elif path == '/api/locks':
            self._handle_get_locks()
        elif path == '/api/status':
            self._handle_get_status()
        elif path == '/api/presence':
            self._handle_get_presence()
        elif path == '/api/profiles':
            self._handle_get_profiles(qs)
        elif path == '/api/activity':
            self._handle_get_activity(qs)
        elif path == '/api/file':
            self._handle_get_file()
        elif path == '/api/check-token':
            self._handle_check_token(qs)
        else:
            # Block sensitive files from being served statically
            if _is_blocked_static(path):
                self.send_response(403)
                body = b'{"error":"Forbidden"}'
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            # Serve static files (dashboard.html, data.json, etc.)
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        # Rate limit check
        client_ip = self._get_client_ip()
        if not _check_rate_limit(client_ip):
            self.send_response(429)
            self.send_header('Content-Type', 'application/json')
            body = b'{"error":"Too many requests"}'
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # Token check
        if not self._check_token(qs):
            return

        if parsed.path == '/api/reviews':
            self._handle_add_review()
        elif parsed.path == '/api/locks':
            self._handle_lock_action()
        elif parsed.path == '/api/presence':
            self._handle_heartbeat()
        elif parsed.path == '/api/presence/leave':
            self._handle_leave()
        elif parsed.path == '/api/profiles':
            self._handle_save_profile()
        elif parsed.path == '/api/activity':
            self._handle_log_activity()
        elif parsed.path == '/api/daily-summary':
            self._handle_daily_summary()
        elif parsed.path == '/api/tpl/generate':
            self._handle_tpl_generate()
        elif parsed.path == '/api/tpl/cleanup':
            self._handle_tpl_cleanup()
        elif parsed.path == '/api/tpr/cleanup':
            self._handle_tpr_cleanup()
        else:
            self._send_json(404, {'error': 'Not found'})

    def do_PUT(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        # Rate limit check
        client_ip = self._get_client_ip()
        if not _check_rate_limit(client_ip):
            self.send_response(429)
            self.send_header('Content-Type', 'application/json')
            body = b'{"error":"Too many requests"}'
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if not self._check_token(qs):
            return
        if parsed.path == '/api/reviews':
            self._handle_update_review()
        else:
            self._send_json(404, {'error': 'Not found'})

    def do_DELETE(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        # Rate limit check
        client_ip = self._get_client_ip()
        if not _check_rate_limit(client_ip):
            self.send_response(429)
            self.send_header('Content-Type', 'application/json')
            body = b'{"error":"Too many requests"}'
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if not self._check_token(qs):
            return
        if parsed.path == '/api/reviews':
            self._handle_delete_review()
        elif parsed.path == '/api/profiles':
            self._handle_delete_profile()
        else:
            self._send_json(404, {'error': 'Not found'})

    # ── API Handlers ───────────────────────────────────────────────────

    def _handle_get_profiles(self, qs=None):
        """GET /api/profiles — return all reviewer profiles.
        Test Proxy Learner (TPL) is hidden unless ?include_tpr=1."""
        profiles = load_profiles()
        include_tpr = qs and any(v in ('1', 'true') for v in qs.get('include_tpr', []))
        if not include_tpr:
            profiles = {k: v for k, v in profiles.items() if v.get('username') != TPR_USERNAME}
        self._send_json(200, profiles)

    def _handle_save_profile(self):
        """POST /api/profiles — save or update a reviewer profile.

        Authorization: only the profile owner or an admin can save.
        Client sends 'requester' (their username) for auth check.
        """
        body = self._read_body()
        if not body:
            return
        username = body.get('username', '').strip()
        display_name = body.get('displayName', '').strip()
        requester = body.get('requester', '').strip()
        if not username:
            self._send_json(400, {'error': 'username required'})
            return
        # Access control: only owner or admin can save
        profiles = load_profiles()
        is_new = username not in profiles
        is_owner = requester == username
        is_admin = requester in ADMIN_USERS

        # Uniqueness: username can only be claimed by one person
        if is_new and not is_admin:
            existing_owner = None
            for uname, prof in profiles.items():
                if prof.get('username') == username:
                    existing_owner = uname
                    break
            if existing_owner:
                self._send_json(409, {'error': f'username @{username} is already claimed by another reviewer'})
                log('WARNING', f'Profile create denied: @{requester} tried to claim @{username} (taken by @{existing_owner})')
                return
            # Check if requester already has a different profile
            if requester and requester != username and requester in profiles:
                self._send_json(409, {'error': f'@{requester} already has a profile — edit your existing profile or contact an admin'})
                log('WARNING', f'Profile create denied: @{requester} already has profile @{requester}')
                return

        if not is_new and not is_owner and not is_admin:
            self._send_json(403, {'error': 'access denied — only the profile owner or an admin can edit this profile'})
            log('WARNING', f'Profile save denied: @{requester} tried to edit @{username}')
            return

        profiles[username] = {
            'username': username,
            'displayName': display_name or username,
            'email': body.get('email', '').strip(),
            'dailySummary': bool(body.get('dailySummary', False)),
            'role': body.get('role', '').strip() or '',
            'createdAt': body.get('createdAt', datetime.now().isoformat()),
            'updatedAt': datetime.now().isoformat()
        }
        save_profiles(profiles)
        action = 'profile_created' if is_new else 'profile_updated'
        log_activity(username, action,
                     f'{"Created" if is_new else "Updated"} profile as {display_name or username}',
                     {'requester': requester})
        log('INFO', f'Profile saved: {display_name} (@{username}) by @{requester}')
        self._send_json(200, {'ok': True, 'profile': profiles[username]})

    # ── Activity Log Handlers ────────────────────────────────────────

    def _handle_get_activity(self, qs):
        """GET /api/activity — return activity log, optionally filtered by ?username=xxx."""
        activities = load_activity()
        username = (qs.get('username', [''])[0]).strip()
        if username:
            activities = [a for a in activities if a.get('username') == username]
        # Return newest first, cap at 100
        activities.reverse()
        self._send_json(200, activities[:100])

    def _handle_log_activity(self):
        """POST /api/activity — log an activity event from the client."""
        body = self._read_body()
        if not body:
            return
        username = body.get('username', '').strip()
        action = body.get('action', '').strip()
        detail = body.get('detail', '').strip()
        if not username or not action:
            self._send_json(400, {'error': 'username and action required'})
            return
        log_activity(username, action, detail, body.get('metadata'))
        self._send_json(200, {'ok': True})

    def _handle_daily_summary(self):
        """POST /api/daily-summary — send daily summary email(s).

        Body: {username?} — if provided, only send to that user.
        If omitted, send to all opted-in reviewers.
        Admin can trigger for all users.
        """
        body = self._read_body()
        if not body:
            return
        requester = body.get('username', '').strip()
        profiles = load_profiles()
        summary = _compile_daily_summary(hours=24)
        html_body = _build_summary_html(summary)
        sent = 0
        for username, profile in profiles.items():
            if not profile.get('dailySummary') or not profile.get('email'):
                continue
            # If a specific user requested, only send to them (or if admin, send to all)
            if requester and requester != username and requester not in ADMIN_USERS:
                continue
            email = profile['email']
            display = profile.get('displayName', username)
            ok, err = _send_email(email, f'📬 MUE Daily Summary — {summary["total_reviews"]} review(s), {summary["total_reviewers"]} reviewer(s)', html_body)
            if ok:
                log('INFO', f'Summary sent to {display} <{email}>')
                sent += 1
            else:
                log('WARNING', f'Failed to send to {display} <{email}>: {err}')
        self._send_json(200, {'ok': True, 'sent': sent, 'reviews': summary['total_reviews'], 'reviewers': summary['total_reviewers']})

    def _handle_tpl_generate(self):
        """POST /api/tpl/generate — create dummy learner data, rebuild data.json.

        Authorization: requires either the TPL secret (X-TPL-Secret header) or
        if no TPL secret is configured, the main access token is sufficient.
        The old requester-field-based check has been removed because it was
        client-controlled and bypassable (requester spoofing).
        """
        if not self._check_tpl_auth():
            return
        # Clean up any existing TPL data first
        _cleanup_tpl_data()
        # Generate dummy data
        notes = _generate_tpl_notes()
        evidence = _generate_tpl_evidence()
        # Rebuild data.json
        rebuild_data_json()
        log('INFO', f'TPL data generated: {len(notes)} notes, {len(evidence)} evidence files')
        self._send_json(200, {
            'ok': True,
            'notes': len(notes),
            'evidence': len(evidence),
            'note_files': [os.path.basename(f) for f in notes],
            'evidence_files': [os.path.basename(f) for f in evidence],
        })

    def _handle_tpl_cleanup(self):
        """POST /api/tpl/cleanup — remove TPL dummy files, rebuild data.json.

        Authorization: requires either the TPL secret (X-TPL-Secret header) or
        if no TPL secret is configured, the main access token is sufficient.
        """
        if not self._check_tpl_auth():
            return
        removed = _cleanup_tpl_data()
        rebuild_data_json()
        log('INFO', f'TPL cleanup: {removed} files removed')
        self._send_json(200, {'ok': True, 'removed': removed})

    def _handle_tpr_cleanup(self):
        """POST /api/tpr/cleanup — remove all TPR/TPL test artifacts.

        Cleans reviews.json, activity logs, and the TPR bot profile.
        Requires admin or TPR auth.
        """
        if not self._check_tpl_auth():
            return
        result = _cleanup_tpr_test_artifacts()
        rebuild_data_json()
        log('INFO', f'TPR/TPL test cleanup: {result["reviews_removed"]} review(s), {result["activities_removed"]} activity log(s), profile={result["profile_removed"]}')
        self._send_json(200, {'ok': True, **result})

    def _check_tpl_auth(self):
        """Check authorization for TPL operations.

        TPL is for test-only data-flow checks. It must never be available through
        ordinary dashboard access, so a separate configured TPL secret is always
        required.
        """
        if not TPL_SECRET:
            self._send_json(403, {'error': 'TPL disabled — configure --tpl-secret to run test learner data operations'})
            log('WARNING', 'TPL auth denied: no TPL secret configured')
            return False

        tpl_secret = self.headers.get('X-TPL-Secret', '')
        if tpl_secret == TPL_SECRET:
            return True
        self._send_json(403, {'error': 'invalid or missing TPL secret — learners cannot influence generative data'})
        log('WARNING', 'TPL auth denied: X-TPL-Secret did not match configured secret')
        return False

    def _handle_get_reviews(self):
        """GET /api/reviews — return all reviews (TPR bot excluded)."""
        reviews = load_reviews()
        # Filter out TPR bot reviews — only real reviewer data visible in dashboard
        reviews = {
            aid: [r for r in revs
                  if r.get('name', '').strip() != TPR_USERNAME
                  and r.get('role', '').strip() != 'Test Proxy']
            for aid, revs in reviews.items()
        }
        reviews = {aid: revs for aid, revs in reviews.items() if revs}
        self._send_json(200, reviews)

    def _handle_get_locks(self):
        """GET /api/locks — return all active edit locks."""
        locks = _get_all_locks()
        self._send_json(200, locks)

    def _handle_lock_action(self):
        """POST /api/locks — claim, release, or check locks."""
        body = self._read_body()
        if not body:
            return
        action = body.get('action')
        artifact_id = body.get('artifactId')
        review_id = body.get('reviewId')
        name = body.get('name', '').strip()
        if not action or not artifact_id or not review_id:
            self._send_json(400, {'error': 'action, artifactId, and reviewId required'})
            return
        if action == 'claim':
            if not name:
                self._send_json(400, {'error': 'name required for claim'})
                return
            ok, err = _claim_lock(artifact_id, review_id, name)
            if ok:
                log('INFO', f'Lock claimed: {name} editing {review_id[:12]}...')
                self._send_json(200, {'ok': True})
            else:
                self._send_json(409, {'error': err})
        elif action == 'release':
            if not name:
                self._send_json(400, {'error': 'name required for release'})
                return
            released = _release_lock(artifact_id, review_id, name)
            if released:
                log('INFO', f'Lock released: {name} on {review_id[:12]}...')
            self._send_json(200, {'ok': True, 'released': released})
        elif action == 'check':
            lock = _check_lock(artifact_id, review_id)
            self._send_json(200, {'locked': lock is not None, 'lock': lock})
        else:
            self._send_json(400, {'error': f'Unknown action: {action}'})

    def _handle_get_presence(self):
        """GET /api/presence — return all reviewers with online/offline status."""
        reviewers = _get_all_presence()
        self._send_json(200, reviewers)

    def _handle_heartbeat(self):
        """POST /api/presence — reviewer heartbeat to signal they're online."""
        body = self._read_body()
        if not body:
            return
        name = body.get('name', '').strip()
        if not name:
            self._send_json(400, {'error': 'name required'})
            return
        display_name = body.get('displayName', '').strip() or name
        color = body.get('color', '#7c73ff')
        avatar = body.get('avatar', '')
        active_page = body.get('activePage', '')
        active_artifact = body.get('activeArtifact', '')
        active_label = body.get('activeLabel', '')
        _heartbeat_presence(name, display_name, color, avatar, active_page, active_artifact, active_label)
        self._send_json(200, {'ok': True})

    def _handle_leave(self):
        """POST /api/presence/leave — reviewer going offline."""
        body = self._read_body()
        if not body:
            return
        name = body.get('name', '').strip()
        if name:
            _leave_presence(name)
        self._send_json(200, {'ok': True})

    def _handle_get_status(self):
        """GET /api/status — server status."""
        reviews = load_reviews()
        total = sum(len(v) for v in reviews.values())
        with _client_lock:
            clients = len(_connected_clients)
        self._send_json(200, {
            'status': 'ok',
            'api_version': API_VERSION,
            'reviews': total,
            'artifacts': len(reviews),
            'connected_clients': clients,
            'reviews_file': str(REVIEWS_PATH),
            'timestamp': datetime.now().isoformat()
        })

    def _handle_add_review(self):
        """POST /api/reviews — add a new review."""
        body = self._read_body()
        if not body:
            return

        artifact_id = body.get('artifactId')
        review = body.get('review')

        if not artifact_id or not review:
            self._send_json(400, {'error': 'artifactId and review required'})
            return

        # Validate required fields
        for field in ('name', 'rating', 'text'):
            if not review.get(field):
                self._send_json(400, {'error': f'Missing required field: {field}'})
                return

        # Validate rating is one of the allowed values
        if review.get('rating') not in _VALID_RATINGS:
            self._send_json(400, {'error': f'Invalid rating: "{review.get("rating")}". Must be one of: {", ".join(sorted(_VALID_RATINGS))}'})
            return

        # Block Test Proxy Reviewer (TPR) from submitting reviews —
        # TPR bot reviews are invisible to the dashboard and must not
        # trigger data.json rebuilds or live-notification false positives.
        review_name = review.get('name', '').strip()
        review_role = review.get('role', '').strip()
        if review_name == TPR_USERNAME or review_role == 'Test Proxy':
            self._send_json(403, {'error': 'Test Proxy Reviewer cannot submit reviews'})
            return

        # Assign ID, timestamp, and version
        review['id'] = review.get('id') or generate_id()
        review['timestamp'] = review.get('timestamp') or datetime.now().isoformat()
        review['version'] = 1
        review['_source'] = 'synced'
        # Preserve curriculum category tag (optional — reviewer's category selection)
        if review.get('category'):
            review['category'] = review['category'].strip()

        # Save to reviews.json
        all_reviews = load_reviews()
        if artifact_id not in all_reviews:
            all_reviews[artifact_id] = []
        all_reviews[artifact_id].append(review)
        save_reviews(all_reviews)

        log('INFO', f'Review added by {review["name"]} on {artifact_id}')
        rebuild_data_json()
        log_activity(review.get('name', ''), 'review_submitted',
                     f'Reviewed {artifact_id} — {review.get("rating", "No rating")}',
                     {'artifactId': artifact_id, 'reviewId': review.get('id')})

        self._send_json(200, {'ok': True, 'review': review})

    def _handle_update_review(self):
        """PUT /api/reviews — update an existing review."""
        body = self._read_body()
        if not body:
            return

        artifact_id = body.get('artifactId')
        review_id = body.get('reviewId')
        updates = body.get('updates', {})

        if not artifact_id or not review_id:
            self._send_json(400, {'error': 'artifactId and reviewId required'})
            return

        all_reviews = load_reviews()
        reviews = all_reviews.get(artifact_id, [])
        review = next((r for r in reviews if r.get('id') == review_id), None)

        if not review:
            self._send_json(404, {'error': 'Review not found'})
            return

        # Version conflict check
        client_version = updates.pop('version', None)
        if client_version is not None:
            server_version = review.get('version', 1)
            if client_version != server_version:
                self._send_json(409, {
                    'error': 'Version conflict',
                    'server_version': server_version,
                    'client_version': client_version,
                    'edited_by': review.get('lastEditedBy', 'unknown'),
                    'edited_at': review.get('editedAt', 'unknown')
                })
                return

        # Validate rating if being updated
        if 'rating' in updates:
            if updates['rating'] not in _VALID_RATINGS:
                self._send_json(400, {'error': f'Invalid rating: "{updates["rating"]}". Must be one of: {", ".join(sorted(_VALID_RATINGS))}'})
                return

        # Apply updates
        for key, val in updates.items():
            if key.startswith('_'):
                continue  # Don't allow overwriting internal fields
            review[key] = val

        review['editedAt'] = datetime.now().isoformat()
        review['version'] = review.get('version', 0) + 1
        save_reviews(all_reviews)

        log('INFO', f'Review {review_id} updated by {review.get("name", "?")}')
        rebuild_data_json()
        log_activity(review.get('name', ''), 'review_edited',
                     f'Edited review on {artifact_id}',
                     {'artifactId': artifact_id, 'reviewId': review_id})

        self._send_json(200, {'ok': True, 'review': review})

    def _handle_delete_profile(self):
        """DELETE /api/profiles — permanently delete a reviewer profile.

        Authorization: only the profile owner or an admin can delete.
        After deletion, the username becomes available for re-registration.
        Activity logs for this user are also removed.
        Reviews authored by this user are preserved (they belong to artifacts)."""
        body = self._read_body()
        if not body:
            return

        username = body.get('username', '').strip()
        requester = body.get('requester', '').strip()
        if not username:
            self._send_json(400, {'error': 'username required'})
            return
        if username == TPR_USERNAME:
            self._send_json(403, {'error': 'Cannot delete the Test Proxy Reviewer profile'})
            return

        profiles = load_profiles()
        if username not in profiles:
            self._send_json(404, {'error': 'Profile not found'})
            return

        is_owner = requester == username
        is_admin = requester in ADMIN_USERS
        if not is_owner and not is_admin:
            self._send_json(403, {'error': 'access denied — only the profile owner or an admin can delete this profile'})
            log('WARNING', f'Profile delete denied: @{requester} tried to delete @{username}')
            return

        # Remove profile
        del profiles[username]
        save_profiles(profiles)

        # Remove activity logs for this user
        activities = load_activity()
        before_count = len(activities)
        activities = [a for a in activities if a.get('username') != username]
        removed_activities = before_count - len(activities)
        with open(ACTIVITY_PATH, 'w', encoding='utf-8') as f:
            json.dump(activities, f, indent=2, ensure_ascii=False)

        # Log the deletion itself (before removing, as log_activity appends)
        log_activity(requester, 'profile_deleted',
                     f'Deleted profile @{username}' + (f' (removed {removed_activities} activity logs)' if removed_activities else ''),
                     {'deletedUsername': username, 'removedActivities': removed_activities})

        log('INFO', f'Profile deleted: @{username} by @{requester} ({removed_activities} activity logs removed)')
        self._send_json(200, {'ok': True, 'removedActivities': removed_activities})

    def _handle_delete_review(self):
        """DELETE /api/reviews — delete a review."""
        body = self._read_body()
        if not body:
            return

        artifact_id = body.get('artifactId')
        review_id = body.get('reviewId')

        if not artifact_id or not review_id:
            self._send_json(400, {'error': 'artifactId and reviewId required'})
            return

        all_reviews = load_reviews()
        reviews = all_reviews.get(artifact_id, [])
        before = len(reviews)
        filtered = [r for r in reviews if r.get('id') != review_id]

        if len(filtered) == before:
            self._send_json(404, {'error': 'Review not found'})
            return

        if filtered:
            all_reviews[artifact_id] = filtered
        elif artifact_id in all_reviews:
            del all_reviews[artifact_id]

        save_reviews(all_reviews)
        log('INFO', f'Review {review_id} deleted from {artifact_id}')
        rebuild_data_json()
        log_activity('', 'review_deleted',
                     f'Deleted review from {artifact_id}',
                     {'artifactId': artifact_id, 'reviewId': review_id})

        self._send_json(200, {'ok': True})

    # ── Helpers ────────────────────────────────────────────────────────

    def _read_body(self):
        """Read and parse JSON request body."""
        try:
            length = int(self.headers.get('Content-Length', 0))
            raw = self.rfile.read(length)
            return json.loads(raw.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as e:
            self._send_json(400, {'error': f'Invalid JSON: {e}'})
            return None

    def _handle_get_file(self):
        """Serve a file from the repo root. ?path=<relative-path>&format=text|json
        Path traversal is prevented by resolving the absolute path and verifying
        it falls within REPO_ROOT."""
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        rel_path = (qs.get('path', [''])[0]).strip().lstrip('/')
        if not rel_path:
            self._send_json(400, {'error': 'Invalid path'})
            return
        # Map dashboard-relative paths to repo paths (same mapping as fetchRepoFile)
        dir_map = {
            'action/': '', 'source/': 'source/', 'review/': 'review/',
            'templates/': 'templates/', 'notes/': 'action/notes/',
            'evidence/': 'action/evidence/', 'reports/': 'action/reports/',
            'scripts/': 'action/scripts/', 'dashboard/': 'action/dashboard/',
            'archive/': 'review/archive/',
        }
        repo_path = rel_path
        for prefix, repo_prefix in dir_map.items():
            if rel_path.startswith(prefix):
                rest = rel_path[len(prefix):]
                repo_path = repo_prefix + rest
                break
        # Resolve to absolute path and verify it's inside REPO_ROOT
        try:
            resolved = (REPO_ROOT / repo_path).resolve()
            resolved_root = REPO_ROOT.resolve()
            if not str(resolved).startswith(str(resolved_root)):
                self._send_json(403, {'error': 'Access denied: path outside repository root'})
                return
        except (ValueError, OSError):
            self._send_json(400, {'error': 'Invalid path'})
            return
        if not resolved.exists() or not resolved.is_file():
            self._send_json(404, {'error': f'File not found: {rel_path}'})
            return
        try:
            text = resolved.read_text(encoding='utf-8')
            self._send_json(200, {'content': text, 'path': rel_path})
        except Exception as e:
            self._send_json(500, {'error': str(e)})

    def _send_json(self, status, data):
        """Send a JSON response."""
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header(API_VERSION_HEADER, API_VERSION)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        """Custom log format."""
        # Skip noisy static file logs
        msg = format % args
        if '/api/' in msg or 'Error' in msg:
            log('DEBUG', msg)


class ThreadedHTTPServer(HTTPServer):
    """Handle each request in a new thread."""
    allow_reuse_address = True

    def process_request(self, request, client_address):
        thread = threading.Thread(target=self.process_request_thread, args=(request, client_address))
        thread.daemon = True
        thread.start()

    def process_request_thread(self, request, client_address):
        try:
            self.finish_request(request, client_address)
        except Exception:
            self.handle_error(request, client_address)
        finally:
            self.shutdown_request(request)


def _validate_environment():
    """Validate required environment variables and configuration at startup.
    Returns (ok: bool, warnings: list[str], errors: list[str])."""
    warnings = []
    errors = []
    
    # Check SMTP configuration if email features are expected
    if not SMTP_HOST:
        warnings.append('SMTP not configured (MUE_SMTP_HOST) — daily summaries and tunnel notifications will be disabled')
    else:
        if not SMTP_USER:
            warnings.append('SMTP user not set (MUE_SMTP_USER) — authentication may fail')
        if not SMTP_PASS:
            warnings.append('SMTP password not set (MUE_SMTP_PASS) — authentication will fail')
        if not SMTP_FROM:
            warnings.append('SMTP from address not set (MUE_SMTP_FROM) — will default to SMTP_USER')
    
    # Check admin email
    if not ADMIN_EMAIL or ADMIN_EMAIL == 'dylan@bicyclebi.com':
        warnings.append('MUE_ADMIN_EMAIL not customized — using default')
    
    # Check tunnel notification email
    tunnel_email = os.environ.get('MUE_TUNNEL_NOTIFY_EMAIL', 'monteretroion@gmail.com')
    if tunnel_email == 'monteretroion@gmail.com':
        warnings.append('MUE_TUNNEL_NOTIFY_EMAIL not customized — using default')
    
    # Check .env file exists
    if not ENV_FILE.exists():
        warnings.append(f'.env file not found at {ENV_FILE} — copy .env.example and configure')
    
    # Check Python version
    import sys
    if sys.version_info < (3, 9):
        errors.append(f'Python 3.9+ required, found {sys.version_info.major}.{sys.version_info.minor}')
    
    # Check required directories
    for path, name in [(REVIEWS_PATH.parent, 'review/'), (DASHBOARD_DIR, 'action/dashboard/')]:
        if not path.exists():
            errors.append(f'Required directory missing: {path} ({name})')
    
    return len(errors) == 0, warnings, errors


def main():
    global SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM
    global DAILY_SUMMARY_HOUR, DAILY_SUMMARY_MINUTE

    parser = argparse.ArgumentParser(description='MUE Review Server')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on (default: 8080)')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0 — all interfaces, accessible from other devices)')
    parser.add_argument('--smtp-host', default='', help='SMTP server host (or set MUE_SMTP_HOST)')
    parser.add_argument('--smtp-port', type=int, default=587, help='SMTP server port (default: 587)')
    parser.add_argument('--smtp-user', default='', help='SMTP login username (or set MUE_SMTP_USER)')
    parser.add_argument('--smtp-pass', default='', help='SMTP login password (or set MUE_SMTP_PASS)')
    parser.add_argument('--smtp-from', default='', help='Sender email address (or set MUE_SMTP_FROM)')
    parser.add_argument('--summary-hour', type=int, default=17, help='Hour to send daily summary (default: 17 = 5 PM)')
    parser.add_argument('--summary-minute', type=int, default=0, help='Minute to send daily summary (default: 0)')
    parser.add_argument('--test-summary', action='store_true', help='Send daily summary now and exit')
    parser.add_argument('--tunnel', action='store_true', help='Expose server to the internet via cloudflared or ngrok tunnel')
    parser.add_argument('--token', default='', help='Access token for secure remote access (auto-generated if not set)')
    parser.add_argument('--no-token', action='store_true', help='Disable access token (for local-only use)')
    parser.add_argument('--tpl-secret', default='', help='Secret required to generate/cleanup TPL generative data. Prevents learners from influencing TPR test output.')
    args = parser.parse_args()

    # Validate environment early
    ok, warnings, errors = _validate_environment()
    for w in warnings:
        log('WARNING', w)
    for e in errors:
        log('ERROR', e)
    if errors:
        log('ERROR', 'Startup aborted due to configuration errors.')
        sys.exit(1)
    if warnings:
        log('INFO', 'Startup warnings shown above')

    # Apply CLI overrides to SMTP config
    if args.smtp_host: SMTP_HOST = args.smtp_host
    if args.smtp_port: SMTP_PORT = args.smtp_port
    if args.smtp_user: SMTP_USER = args.smtp_user
    if args.smtp_pass: SMTP_PASS = args.smtp_pass
    if args.smtp_from: SMTP_FROM = args.smtp_from
    DAILY_SUMMARY_HOUR = args.summary_hour
    DAILY_SUMMARY_MINUTE = args.summary_minute

    # Access token for secure remote access
    global SERVER_ACCESS_TOKEN
    if not args.no_token:
        import secrets, string
        # Priority: CLI arg > env var > auto-generated
        SERVER_ACCESS_TOKEN = args.token or os.environ.get('MUE_ACCESS_TOKEN') or ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(20))

    # TPL secret — prevents learners from triggering TPL data generation/cleanup
    global TPL_SECRET
    TPL_SECRET = args.tpl_secret or os.environ.get('MUE_TPL_SECRET')

    # Set global base URL for email links (uses first LAN IP if available, else localhost)
    global _SERVER_BASE_URL
    lan_ips = _get_lan_ips()
    base_ip = lan_ips[0] if lan_ips else 'localhost'
    _SERVER_BASE_URL = f'http://{base_ip}:{args.port}'

    # Ensure review/reviews.json directory exists
    REVIEWS_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Run initial build
    log('INFO', 'MUE Review Server')
    log('INFO', f'Reviews: {REVIEWS_PATH}')

    rebuild_data_json()

    # Test-summary mode: send now and exit
    if args.test_summary:
        log('INFO', 'Test mode — sending daily summary now...')
        count = send_daily_summaries()
        log('INFO', f'Done — {count} email(s) sent.')
        return

    # Print SMTP status
    if SMTP_HOST:
        env_tag = ' (.env)' if ENV_FILE.exists() and not os.environ.get('MUE_SMTP_HOST') else ''
        log('INFO', f'SMTP: {SMTP_HOST}:{SMTP_PORT} (from: {SMTP_FROM}){env_tag}')
        log('INFO', f'Daily summary at {DAILY_SUMMARY_HOUR:02d}:{DAILY_SUMMARY_MINUTE:02d}')
    else:
        log('WARNING', 'SMTP: not configured (set MUE_SMTP_HOST or --smtp-host)')
        log('WARNING', 'Daily summaries: disabled (no SMTP)')
    # Print TPL secret status
    if TPL_SECRET:
        log('INFO', 'TPL secret: configured (required for generative data operations)')
    else:
        log('WARNING', 'TPL secret: not set (any token holder can generate TPL data)')
    # Print access token status
    if SERVER_ACCESS_TOKEN:
        log('INFO', f'Access token: {SERVER_ACCESS_TOKEN}')
    else:
        log('INFO', 'Access token: disabled (--no-token)')

    server = ThreadedHTTPServer((args.host, args.port), ReviewHandler)

    # Start daily summary scheduler (if SMTP is configured)
    if SMTP_HOST:
        scheduler_thread = threading.Thread(target=_daily_scheduler_loop, daemon=True)
        scheduler_thread.start()

    # Start tunnel if requested
    if args.tunnel:
        tunnel_info = _find_tunnel_tool()
        if tunnel_info:
            tunnel_thread = threading.Thread(target=_start_tunnel, args=(args.port, tunnel_info[1], tunnel_info[0]), daemon=True)
            tunnel_thread.start()
        else:
            log('WARNING', '--tunnel requested but no tunnel tool found.')
            log('WARNING', 'Install cloudflared: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/')
            log('WARNING', 'Or install ngrok:     https://ngrok.com/download')

    try:
        listen_addr = args.host if args.host != '0.0.0.0' else 'all interfaces'
        log('INFO', f'Listening on http://{listen_addr}:{args.port}')
        if not args.tunnel:
            if lan_ips:
                go_url = f'http://{lan_ips[0]}:{args.port}/go'
                log('INFO', f'Share this URL: {go_url}')
                if SERVER_ACCESS_TOKEN:
                    log('INFO', 'Auto-redirects to dashboard — token passed server-side')
            else:
                log('WARNING', f'No LAN IP detected — use localhost:{args.port}/go')
        log('INFO', 'Press Ctrl+C to stop.')
        server.serve_forever()
    except KeyboardInterrupt:
        global _scheduler_running
        _scheduler_running = False
        log('INFO', 'Server stopped.')
        server.server_close()


if __name__ == '__main__':
    main()
