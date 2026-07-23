#!/usr/bin/env python3
"""
action/proxy/server.py
Learner Web Interface — Phase 2: Core UI (daily note editor + curriculum viewer).

Serves the learner's interactive web UI using only Python stdlib.
Pattern matched to action/dashboard/review_server.py for consistency.

Usage:
    python action/proxy/server.py [--port 5000] [--host 127.0.0.1]

Pages:
    GET  /                     → Dashboard / home (learner status, today's task)
    GET  /curriculum           → Full 28-day curriculum viewer
    GET  /notes                → List all notes
    GET  /notes/new?day=N      → Note editor for day N
    GET  /notes/{date}         → View / edit an existing note

API:
    GET  /api/status           → Learner status + current day info
    GET  /api/curriculum       → Full 28-day schedule as JSON
    GET  /api/notes            → List all notes as JSON
    GET  /api/notes/{date}     → Get a specific note as JSON
    POST /api/notes            → Create / update a note
    POST /api/rebuild          → Trigger build_data.py

Architecture:
    ┌─────────────────────────────────────┐
    │  server.py (this file)              │
    │  http.server + AJAX endpoints       │
    │  HTML string templates              │
    ├─────────────────────────────────────┤
    │  WebLearner (web_interface.py)      │
    │  Content staging → file I/O         │
    ├─────────────────────────────────────┤
    │  build_data.py → data.json → dash   │
    └─────────────────────────────────────┘
"""
import argparse
import json
import os
import random
import re
import secrets
import smtplib
import subprocess
import sys
import threading
import time
from datetime import date, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Ensure the repo root is on sys.path so action.proxy imports work
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from action.proxy.web_interface import WebLearner
from action.proxy.curriculum import CURRICULUM, get_classification, get_primary_track, get_level_for_day
from action.proxy.constants import PROOF_TASKS, PROOF_TASK_CRITERIA, ADMIN_PROFILE_IDS
from action.proxy.feedback import (
    get_feedback_for_learner, get_unread_feedback, mark_seen, mark_all_seen,
    get_qa_thread, add_qa_entry,
    get_level_progress, get_reviewer_display,
    create_revision, get_revision_history,
    compile_learner_daily_summary,
    load_reviews, load_profiles,
)

# ── Paths ──────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROXY_DIR = SCRIPT_DIR
REPO_ROOT = SCRIPT_DIR.parent.parent
ACTION_DIR = REPO_ROOT / 'action'
NOTES_DIR = ACTION_DIR / 'notes'
EVIDENCE_DIR = ACTION_DIR / 'evidence'
BUILD_SCRIPT = ACTION_DIR / 'dashboard' / 'build_data.py'
STATIC_DIR = SCRIPT_DIR / 'web_static'

# ── Security helpers ──────────────────────────────────────────────────────
def _safe_filename(name: str, allowed_dir: Path) -> str:
    """
    Sanitize a user-supplied filename to prevent path traversal.
    Returns the cleaned filename (basename only) or raises ValueError.
    """
    from pathlib import PurePath
    # Decode URL encoding
    from urllib.parse import unquote
    name = unquote(name)
    # Get just the filename, strip any directory components
    clean = PurePath(name).name
    if not clean:
        raise ValueError('Empty filename')
    # Reject hidden paths with ..
    if '..' in clean or clean.startswith('.'):
        raise ValueError('Invalid filename')
    # Resolve and verify it's within the allowed directory
    resolved = (allowed_dir / clean).resolve()
    if not str(resolved).startswith(str(allowed_dir.resolve())):
        raise ValueError('Path traversal detected')
    return clean


# ── Learner instance & profile support ────────────────────────────────────
_learner = WebLearner(action_dir=ACTION_DIR, auto_build=True)  # fallback (legacy)

# ── Admin profile access control ────────────────────────────────────────────
# Only these profile IDs are considered administrative (repo owner).
# They are hidden from the profile switcher for non-admin sessions.
# ADMIN_PROFILE_IDS is defined in action/proxy/constants.py


def _is_admin_session(profile_id: str | None) -> bool:
    """Return True if the current session is an admin profile."""
    if not profile_id:
        return False
    return profile_id in ADMIN_PROFILE_IDS


def _is_admin_profile(profile_id: str) -> bool:
    """Return True if the given profile ID is an administrative profile."""
    return profile_id in ADMIN_PROFILE_IDS


def _has_learner_profiles() -> bool:
    """Return True if there are any non-admin (learner) profiles."""
    return any(p.get('id') not in ADMIN_PROFILE_IDS for p in _profiles_list)


def _learner_profiles_count() -> int:
    """Return the count of non-admin (learner) profiles."""
    return sum(1 for p in _profiles_list if p.get('id') not in ADMIN_PROFILE_IDS)


# ── Admin email confirmation code auth ──────────────────────────────────────
ADMIN_SESSION_COOKIE = 'mue_admin_session'
ADMIN_SESSION_TTL = 86400  # 24 hours
_admin_sessions = {}  # {session_id: {username, created_at}}
_admin_sessions_lock = threading.Lock()
_admin_codes = {}  # {username: {code, expires_at}}
_admin_codes_lock = threading.Lock()
ADMIN_CODE_TTL = 600  # 10 minutes
# ADMIN_VERIFY_EMAIL is set after .env loading below (moved to email config section)


def _create_admin_session(username: str) -> str:
    """Create an admin session and return the session ID."""
    session_id = secrets.token_hex(24)
    with _admin_sessions_lock:
        _admin_sessions[session_id] = {
            'username': username,
            'created_at': time.time(),
        }
    return session_id


def _get_admin_session(session_id: str) -> str | None:
    """Get the username for a valid admin session, or None if invalid/expired."""
    if not session_id:
        return None
    with _admin_sessions_lock:
        session = _admin_sessions.get(session_id)
        if not session:
            return None
        if time.time() - session['created_at'] > ADMIN_SESSION_TTL:
            del _admin_sessions[session_id]
            return None
        return session['username']


def _get_admin_from_cookies(cookie_header: str) -> str | None:
    """Extract admin username from a Cookie header string."""
    for part in cookie_header.split(';'):
        part = part.strip()
        if part.startswith(ADMIN_SESSION_COOKIE + '='):
            sid = part[len(ADMIN_SESSION_COOKIE) + 1:]
            return _get_admin_session(sid)
    return None


def _esc_html(s):
    """HTML-escape a string for safe rendering."""
    if not isinstance(s, str):
        s = str(s or '')
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#x27;')


# Load profiles and create per-profile learners
_profiles_list: list[dict] = []
_learners: dict[str, WebLearner] = {}

try:
    from action.proxy.web_interface import load_profiles as _load_profiles
    _profiles_list = _load_profiles()
    for _p in _profiles_list:
        _pid = _p['id']
        _learners[_pid] = WebLearner(profile_id=_pid, auto_build=True)
except Exception:
    pass  # profiles.json may not exist yet


def _reload_profiles():
    """Reload profile list from disk and sync _learners dict."""
    global _profiles_list, _learners
    try:
        from action.proxy.web_interface import load_profiles as _lp
        _profiles_list = _lp()
        seen = set()
        for _p in _profiles_list:
            pid = _p['id']
            seen.add(pid)
            if pid not in _learners:
                _learners[pid] = WebLearner(profile_id=pid, auto_build=True)
        # Remove learners that no longer exist in profiles
        for pid in list(_learners.keys()):
            if pid not in seen:
                del _learners[pid]
    except Exception:
        pass

# ── .env file loader ───────────────────────────────────────────────────────
def _load_env_file(path: Path) -> None:
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


# Load proxy .env before reading email config
_load_env_file(PROXY_DIR / '.env')

# ── Email configuration (from env vars / .env) ───────────────────────────────
ADMIN_VERIFY_EMAIL = os.environ.get('MUE_ADMIN_VERIFY_EMAIL', 'monteretroion@gmail.com')
SMTP_HOST = os.environ.get('MUE_SMTP_HOST', '')
SMTP_PORT = int(os.environ.get('MUE_SMTP_PORT', '587'))
SMTP_USER = os.environ.get('MUE_SMTP_USER', '')
SMTP_PASS = os.environ.get('MUE_SMTP_PASS', '')
SMTP_FROM = os.environ.get('MUE_SMTP_FROM', SMTP_USER or 'mue-learner@localhost')
SMTP_USE_TLS = os.environ.get('MUE_SMTP_TLS', 'true').lower() == 'true'
LEARNER_EMAIL = os.environ.get('MUE_LEARNER_EMAIL', '')
DAILY_SUMMARY_HOUR = int(os.environ.get('MUE_SUMMARY_HOUR', '6'))
DAILY_SUMMARY_MINUTE = int(os.environ.get('MUE_SUMMARY_MINUTE', '0'))
SUMMARY_ENABLED = os.environ.get('MUE_LEARNER_SUMMARY', 'false').lower() == 'true'

# Email scheduler state
_scheduler_running = False
_scheduler_thread = None

# ── Week names ──────────────────────────────────────────────────────────────
WEEK_NAMES = {1: 'Foundation', 2: 'Application', 3: 'Integration', 4: 'Graduation'}

# ── Classification colours ──────────────────────────────────────────────────
CLASS_COLOURS = {
    'Foundational': '#f59e0b',
    'Developing': '#3b82f6',
    'Operational': '#10b981',
    'Ready For Codex Acceleration': '#8b5cf6',
}


# ═══════════════════════════════════════════════════════════════════════════
# HTML Template Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _html_page(title: str, body: str, active_nav: str = '') -> str:
    """Wrap body content in the full HTML page layout."""
    nav_items = [
        ('/', 'Home', active_nav == 'home'),
        ('/guide', 'Guide', active_nav == 'guide'),
        ('/curriculum', 'Curriculum', active_nav == 'curriculum'),
        ('/notes', 'Notes', active_nav == 'notes'),
        ('/evidence', 'Evidence', active_nav == 'evidence'),
        ('/feedback', 'Feedback', active_nav == 'feedback'),
        ('/progress', 'Progress', active_nav == 'progress'),
    ]
    nav_links = ''.join(
        f'<a href="{href}"{" class=\"active\"" if active else ""}>{label}</a>'
        for href, label, active in nav_items
    )
    # ── Profile selector ────────────────────────────────────────────
    try:
        _pid = _learner.profile_id or 'default'
        _pname = _learner.get_profile_label()
    except Exception:
        _pid = 'default'
        _pname = 'Default'

    # Determine if current session is admin
    _session_is_admin = _is_admin_session(_pid)

    # Filter profiles: non-admin sessions only see non-admin profiles
    _visible_profiles = [p for p in _profiles_list if _session_is_admin or not _is_admin_profile(p['id'])]

    if not _has_learner_profiles():
        _profile_html = '<a href="/" class="btn btn-sm" style="text-decoration:none;">➕ Create Profile</a>'
    elif len(_visible_profiles) <= 1:
        # Only one profile visible — show name as badge, no switch dropdown
        _profile_html = f'<span class="profile-badge">{_pname}</span>'
    else:
        _profile_opts = ''
        for _p in _visible_profiles:
            _sel = 'selected' if _p.get('id') == _pid else ''
            _profile_opts += f'<option value="{_p["id"]}" {_sel}>{_p.get("name", _p["id"])}</option>'
        _profile_html = f'''<select id="profileSelect" onchange="switchProfile(this.value)">
      {_profile_opts}
    </select>
    <span class="profile-badge">{_pname}</span>'''

    # Add logout button when a profile is active (not default) OR when admin session is active
    _logout_html = ''
    if _pid != 'default' or _session_is_admin:
        _logout_html = '<button class="btn btn-outline btn-sm" onclick="logoutProfile()" style="margin-left:4px;font-size:11px;">🚪 Logout</button>'

    # Admin login / status indicator
    if _session_is_admin:
        _admin_html = '<span style="font-size:11px;color:#dc3545;margin-left:4px;">👑 Admin</span>'
    else:
        _admin_html = '<a href="/admin-login" class="btn btn-outline btn-sm" style="text-decoration:none;margin-left:4px;font-size:11px;">🔑 Admin</a>'

    manage_link = ''
    if _profiles_list:
        manage_link = '<a href="/manage" class="btn btn-outline btn-sm" style="text-decoration:none;margin-left:4px;">⚙️</a>'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — MUE Learner</title>
<link rel="stylesheet" href="/static/style.css">
</head>
<body>
<header>
  <div class="logo"><span>MUE</span> Learner</div>
  <nav>{nav_links}</nav>
  <div class="profile-selector">
    {_profile_html}
    {_logout_html}
    {_admin_html}
    {manage_link}
  </div>
</header>
<div class="container">
{body}
</div>
<div id="toast" class="toast"></div>
<script>
function showToast(msg, type) {{
  var t = document.getElementById('toast');
  t.textContent = msg; t.className = 'toast ' + type + ' show';
  setTimeout(function() {{ t.className = 'toast'; }}, 3000);
}}

function switchProfile(profileId) {{
  fetch('/api/profile/switch', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{profile_id: profileId}})
  }})
  .then(function(r){{return r.json()}})
  .then(function(r){{
    if(r.status==='ok'){{showToast('🔄 Switched to ' + profileId,'success');setTimeout(function(){{location.reload()}},600);}}
    else{{showToast('❌ '+r.message,'error');}}
  }})
  .catch(function(e){{showToast('❌ '+e,'error');}});
}}

function createProfile(name, startDate, password, email) {{
  fetch('/api/profiles/create', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{name: name, start_date: startDate || null, password: password, email: email || null}})
  }})
  .then(function(r){{return r.json()}})
  .then(function(r){{
    if(r.status==='ok'){{showToast('✅ Profile created!','success');setTimeout(function(){{location.reload()}},600);}}
    else{{showToast('❌ '+r.message,'error');}}
  }})
  .catch(function(e){{showToast('❌ '+e,'error');}});
}}

function deleteProfile(profileId) {{
  if(!confirm('Are you sure you want to delete your profile? All progress data will be disconnected (files remain on disk).')) return;
  fetch('/api/profiles/delete', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{profile_id: profileId}})
  }})
  .then(function(r){{return r.json()}})
  .then(function(r){{
    if(r.status==='ok'){{showToast('🗑️ Profile deleted.','success');setTimeout(function(){{location.reload()}},600);}}
    else{{showToast('❌ '+r.message,'error');}}
  }})
  .catch(function(e){{showToast('❌ '+e,'error');}});
}}

function logoutProfile() {{
  fetch('/api/profile/logout', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}}
  }})
  .then(function(r){{return r.json()}})
  .then(function(r){{
    if(r.status==='ok'){{showToast('🚪 Logged out','success');setTimeout(function(){{location.reload()}},600);}}
    else{{showToast('❌ '+r.message,'error');}}
  }})
  .catch(function(e){{showToast('❌ '+e,'error');}});
}}
</script>
</body>
</html>'''


def _day_progress_bar(current: int, total: int = 28) -> str:
    pct = round(current / total * 100)
    return f'''<div class="progress-bar"><div class="fill" style="width:{pct}%"></div></div>
<div style="font-size:12px;color:#6b7280;text-align:center;">Day {current} of {total}</div>'''


# ═══════════════════════════════════════════════════════════════════════════
# Page Handlers
# ═══════════════════════════════════════════════════════════════════════════

def _page_guide() -> str:
    """Render the learner guide — what, how, when, where."""
    body = f'''
<div class="card">
  <h2 style="font-size:22px;margin-bottom:12px;">🧭 Learner Guide</h2>
  <p style="font-size:14px;color:#4b5563;margin-bottom:20px;">
    Everything you need to know about working through the MUE curriculum —
    <strong>what</strong> to do, <strong>how</strong> to do it,
    <strong>when</strong> to do it, and <strong>where</strong> to find things.
  </p>
</div>

<!-- ──── WHAT ──── -->
<div class="card">
  <h2 style="font-size:18px;margin-bottom:8px;">📌 What</h2>
  <p style="font-size:14px;color:#4b5563;margin-bottom:12px;">
    <strong>MUE</strong> (Model-Understanding-Evidence) is a 28-day Business Intelligence
    onboarding curriculum. Each day you will:
  </p>
  <ul style="font-size:14px;color:#4b5563;padding-left:20px;margin-bottom:12px;line-height:1.8;">
    <li>📖 <strong>Read</strong> the day&rsquo;s focus topic and understand the learning objective</li>
    <li>✍️ <strong>Reflect</strong> on what you learned and what evidence you produced</li>
    <li>📎 <strong>Create</strong> the required artifact (markdown doc, screenshot, CSV, etc.)</li>
    <li>✅ <strong>Score</strong> your work using the scorecard and Codex gates</li>
    <li>📬 <strong>Submit</strong> for feedback when you&rsquo;re ready</li>
  </ul>
  <p style="font-size:14px;color:#4b5563;">
    The curriculum covers: AI prompt crafting &bull; Codex workflow &bull; Pyramid operations &bull;
    BI judgment &bull; data lineage &bull; change isolation &bull; deployment checklists &bull;
    delivery handoffs &bull; team standups &bull; retention reviews &bull; reusable assets.
  </p>
</div>

<!-- ──── HOW ──── -->
<div class="card">
  <h2 style="font-size:18px;margin-bottom:8px;">⚙️ How</h2>

  <h3 style="font-size:15px;margin:16px 0 8px;">🏠 Dashboard (Home)</h3>
  <p style="font-size:14px;color:#4b5563;margin-bottom:8px;">
    Your starting point each day. Shows your current day, today&rsquo;s focus topic,
    a progress bar, and any <em>Catch Up</em> items for incomplete prior days.
    Use the <strong>Work Ahead</strong> section to preview future days.
  </p>

  <h3 style="font-size:15px;margin:16px 0 8px;">📚 Curriculum</h3>
  <p style="font-size:14px;color:#4b5563;margin-bottom:8px;">
    A grid of all 28 days. Click any day card to open its <strong>Day Workspace</strong> —
    a consolidated page with instructions, the note editor, scorecard, gates, and
    evidence upload. Filter by week using the buttons at the top.
  </p>

  <h3 style="font-size:15px;margin:16px 0 8px;">📝 Daily Reflection (Note Editor)</h3>
  <p style="font-size:14px;color:#4b5563;margin-bottom:8px;">
    Each day you fill out a <strong>Daily Reflection</strong> note with these fields:
  </p>
  <ul style="font-size:14px;color:#4b5563;padding-left:20px;margin-bottom:8px;line-height:1.8;">
    <li><strong>What I learned today</strong> &mdash; key takeaways, prompt structures, techniques</li>
    <li><strong>What evidence I produced</strong> &mdash; artifacts created, outputs generated</li>
    <li><strong>What remains open</strong> &mdash; unresolved questions or tasks</li>
    <li><strong>Next narrow step</strong> &mdash; your immediate action item</li>
    <li><strong>Scorecard</strong> &mdash; self-assess each of the 9 competency areas (Pass / Moderate / Fail / Unscored)</li>
    <li><strong>Codex Gates</strong> &mdash; confirm you&rsquo;ve followed each Codex acceleration gate</li>
  </ul>
  <p style="font-size:14px;color:#4b5563;margin-bottom:8px;">
    The note fields show <strong>dynamic hints</strong> based on the day&rsquo;s tags
    (AI, Codex, Pyramid, etc.). Use the <strong>👁️ Preview</strong> button to see
    a live markdown render of your writing. Text areas <strong>auto-resize</strong>
    as you type. Click <strong>Save Note</strong> when finished.
  </p>

  <h3 style="font-size:15px;margin:16px 0 8px;">📎 Evidence &amp; Artifacts</h3>
  <p style="font-size:14px;color:#4b5563;margin-bottom:8px;">
    Every day has a <strong>required artifact</strong> (shown in the day workspace).
    Supported formats:
  </p>
  <ul style="font-size:14px;color:#4b5563;padding-left:20px;margin-bottom:8px;line-height:1.8;">
    <li>📝 <strong>Markdown</strong> (.md) &mdash; use the <strong>📄 Use Template</strong> button to pre-fill a template</li>
    <li>🖼️ <strong>Screenshot</strong> (.png, .jpg) &mdash; use the <strong>📸 Screenshot Guide</strong> for best practices</li>
    <li>📊 <strong>CSV / Data</strong> (.csv, .txt) &mdash; upload raw data files</li>
    <li>📄 <strong>PDF</strong> &mdash; upload reference documents</li>
  </ul>
  <p style="font-size:14px;color:#4b5563;margin-bottom:8px;">
    Upload files via the drag-and-drop zone at the bottom of each day workspace,
    or use the standalone <strong>Evidence</strong> page from the navigation bar.
  </p>

  <h3 style="font-size:15px;margin:16px 0 8px;">📬 Feedback</h3>
  <p style="font-size:14px;color:#4b5563;margin-bottom:8px;">
    After completing a day&rsquo;s work, you can request or view <strong>reviewer feedback</strong>
    on the Feedback page. Each review artifact shows comments, a quality score, and
    reviewer Q&amp;A. Use the <strong>Ask a Question</strong> button to start a
    conversation with your reviewer.
  </p>

  <h3 style="font-size:15px;margin:16px 0 8px;">📊 Progress</h3>
  <p style="font-size:14px;color:#4b5563;margin-bottom:8px;">
    The Progress page gives you an overview of your completion status across all 28 days:
    which days have notes, which have evidence, your scorecard trends, and Codex gate
    compliance. It also shows your classification progression over time.
  </p>
</div>

<!-- ──── WHEN ──── -->
<div class="card">
  <h2 style="font-size:18px;margin-bottom:8px;">📅 When</h2>

  <h3 style="font-size:15px;margin:16px 0 8px;">Daily Workflow</h3>
  <ol style="font-size:14px;color:#4b5563;padding-left:20px;margin-bottom:12px;line-height:1.8;">
    <li>Start at the <strong>Dashboard</strong> to see what day you&rsquo;re on</li>
    <li>Click <strong>Work on Day N</strong> or navigate via <strong>Curriculum</strong></li>
    <li>Read the <strong>Requirements for Today</strong> and check each item as you complete it</li>
    <li>Write your <strong>Daily Reflection</strong> note</li>
    <li>Create and upload the <strong>required artifact</strong></li>
    <li>Self-assess using the <strong>Scorecard</strong> and <strong>Codex Gates</strong></li>
    <li>Click <strong>Save Note</strong> to persist your work</li>
  </ol>

  <h3 style="font-size:15px;margin:16px 0 8px;">Weekly Milestones</h3>
  <table style="width:100%;font-size:14px;color:#4b5563;border-collapse:collapse;margin-bottom:12px;">
    <tr style="border-bottom:1px solid #e5e7eb;">
      <th style="padding:6px 8px;text-align:left;font-weight:600;">Week</th>
      <th style="padding:6px 8px;text-align:left;font-weight:600;">Theme</th>
      <th style="padding:6px 8px;text-align:left;font-weight:600;">Focus</th>
    </tr>
    <tr style="border-bottom:1px solid #e5e7eb;">
      <td style="padding:6px 8px;">1</td>
      <td style="padding:6px 8px;">🏗️ Foundation</td>
      <td style="padding:6px 8px;">AI modes, prompt crafting, Codex Loop, change isolation, model lineage, operations checklist</td>
    </tr>
    <tr style="border-bottom:1px solid #e5e7eb;">
      <td style="padding:6px 8px;">2</td>
      <td style="padding:6px 8px;">🔗 Data Foundation</td>
      <td style="padding:6px 8px;">Hierarchy &amp; structure, data dictionary, SCD logic, peer review, certification prep</td>
    </tr>
    <tr style="border-bottom:1px solid #e5e7eb;">
      <td style="padding:6px 8px;">3</td>
      <td style="padding:6px 8px;">📊 BI Delivery</td>
      <td style="padding:6px 8px;">Delivery checklist, deployment, handoff, retention review, reusable assets</td>
    </tr>
    <tr style="border-bottom:1px solid #e5e7eb;">
      <td style="padding:6px 8px;">4</td>
      <td style="padding:6px 8px;">🧠 BI Judgment</td>
      <td style="padding:6px 8px;">Advanced judgment, compliance, audit, capability review, Codex acceleration readiness</td>
    </tr>
  </table>

  <h3 style="font-size:15px;margin:16px 0 8px;">Working Ahead</h3>
  <p style="font-size:14px;color:#4b5563;margin-bottom:8px;">
    You can <strong>preview or start working on any day</strong> at any time.
    Future days appear in the <strong>🔮 Work Ahead</strong> section on the dashboard.
    The note editor will automatically use the correct calendar date for that
    curriculum day.
  </p>

  <h3 style="font-size:15px;margin:16px 0 8px;">Catching Up</h3>
  <p style="font-size:14px;color:#4b5563;margin-bottom:8px;">
    Days you&rsquo;ve missed appear in the <strong>⏰ Catch Up</strong> section on
    the dashboard. Click <strong>✏️ Catch Up</strong> to jump directly to that
    day&rsquo;s workspace. You can complete past days in any order.
  </p>
</div>

<!-- ──── WHERE ──── -->
<div class="card">
  <h2 style="font-size:18px;margin-bottom:8px;">📍 Where</h2>

  <table style="width:100%;font-size:14px;color:#4b5563;border-collapse:collapse;margin-bottom:12px;">
    <tr style="border-bottom:1px solid #e5e7eb;">
      <th style="padding:6px 8px;text-align:left;font-weight:600;">Page</th>
      <th style="padding:6px 8px;text-align:left;font-weight:600;">URL</th>
      <th style="padding:6px 8px;text-align:left;font-weight:600;">What You&rsquo;ll Find</th>
    </tr>
    <tr style="border-bottom:1px solid #e5e7eb;">
      <td style="padding:6px 8px;">🏠 Home</td>
      <td style="padding:6px 8px;"><code>/</code></td>
      <td style="padding:6px 8px;">Dashboard with today&rsquo;s focus, progress bar, catch-up &amp; work-ahead sections</td>
    </tr>
    <tr style="border-bottom:1px solid #e5e7eb;">
      <td style="padding:6px 8px;">🧭 Guide</td>
      <td style="padding:6px 8px;"><code>/guide</code></td>
      <td style="padding:6px 8px;">This page — full learner orientation</td>
    </tr>
    <tr style="border-bottom:1px solid #e5e7eb;">
      <td style="padding:6px 8px;">📚 Curriculum</td>
      <td style="padding:6px 8px;"><code>/curriculum</code></td>
      <td style="padding:6px 8px;">28-day grid, filterable by week, click to open a day workspace</td>
    </tr>
    <tr style="border-bottom:1px solid #e5e7eb;">
      <td style="padding:6px 8px;">📝 Notes</td>
      <td style="padding:6px 8px;"><code>/notes</code></td>
      <td style="padding:6px 8px;">List of all your daily reflection notes, sorted by date</td>
    </tr>
    <tr style="border-bottom:1px solid #e5e7eb;">
      <td style="padding:6px 8px;">📎 Evidence</td>
      <td style="padding:6px 8px;"><code>/evidence</code></td>
      <td style="padding:6px 8px;">All uploaded artifacts, filterable, with preview and delete</td>
    </tr>
    <tr style="border-bottom:1px solid #e5e7eb;">
      <td style="padding:6px 8px;">📬 Feedback</td>
      <td style="padding:6px 8px;"><code>/feedback</code></td>
      <td style="padding:6px 8px;">Reviewer comments, quality scores, Q&amp;A threads</td>
    </tr>
    <tr style="border-bottom:1px solid #e5e7eb;">
      <td style="padding:6px 8px;">📊 Progress</td>
      <td style="padding:6px 8px;"><code>/progress</code></td>
      <td style="padding:6px 8px;">Completion overview, scorecard trends, classification progression</td>
    </tr>
    <tr style="border-bottom:1px solid #e5e7eb;">
      <td style="padding:6px 8px;">📖 Day Workspace</td>
      <td style="padding:6px 8px;"><code>/day/{{n}}</code></td>
      <td style="padding:6px 8px;">Consolidated page for a specific day: requirements, note editor, scorecard, gates, evidence upload</td>
    </tr>
  </table>

  <h3 style="font-size:15px;margin:16px 0 8px;">File Locations</h3>
  <p style="font-size:14px;color:#4b5563;margin-bottom:8px;">
    Your work is saved as plain files in the <code>action/</code> directory:
  </p>
  <table style="width:100%;font-size:14px;color:#4b5563;border-collapse:collapse;margin-bottom:12px;">
    <tr style="border-bottom:1px solid #e5e7eb;">
      <th style="padding:6px 8px;text-align:left;font-weight:600;">Content</th>
      <th style="padding:6px 8px;text-align:left;font-weight:600;">Folder</th>
      <th style="padding:6px 8px;text-align:left;font-weight:600;">File Naming</th>
    </tr>
    <tr style="border-bottom:1px solid #e5e7eb;">
      <td style="padding:6px 8px;">Daily notes</td>
      <td style="padding:6px 8px;"><code>action/notes/</code></td>
      <td style="padding:6px 8px;"><code>YYYY-MM-DD.md</code></td>
    </tr>
    <tr style="border-bottom:1px solid #e5e7eb;">
      <td style="padding:6px 8px;">Evidence / artifacts</td>
      <td style="padding:6px 8px;"><code>action/evidence/</code></td>
      <td style="padding:6px 8px;">Day- or proof-task prefixed filenames</td>
    </tr>
    <tr style="border-bottom:1px solid #e5e7eb;">
      <td style="padding:6px 8px;">Reports</td>
      <td style="padding:6px 8px;"><code>action/reports/</code></td>
      <td style="padding:6px 8px;">Weekly or periodic summary reports</td>
    </tr>
    <tr style="border-bottom:1px solid #e5e7eb;">
      <td style="padding:6px 8px;">Learner config</td>
      <td style="padding:6px 8px;"><code>action/</code></td>
      <td style="padding:6px 8px;"><code>learner_config.json</code></td>
    </tr>
  </table>
</div>

<!-- ──── TIPS ──── -->
<div class="card">
  <h2 style="font-size:18px;margin-bottom:8px;">💡 Tips &amp; Best Practices</h2>
  <ul style="font-size:14px;color:#4b5563;padding-left:20px;line-height:1.8;">
    <li><strong>Save often</strong> &mdash; your note is only persisted when you click Save Note</li>
    <li><strong>Use the preview</strong> &mdash; the 👁️ Preview button shows how your markdown will look when rendered</li>
    <li><strong>Follow the hints</strong> &mdash; dynamic help text adapts to each day&rsquo;s topic tags</li>
    <li><strong>Score honestly</strong> &mdash; the scorecard helps you track growth; &ldquo;Fail&rdquo; is a learning signal, not a penalty</li>
    <li><strong>Work ahead</strong> &mdash; future days are accessible any time from the Work Ahead section or Curriculum grid</li>
    <li><strong>Use templates</strong> &mdash; the 📄 Use Template button pre-fills a structured markdown template for .md artifacts</li>
    <li><strong>Take screenshots</strong> &mdash; for image artifacts, use Snipping Tool (Win+Shift+S) and upload via the day workspace</li>
    <li><strong>Ask questions</strong> &mdash; use the Feedback page Q&amp;A to discuss review comments with your reviewer</li>
  </ul>
</div>

<!-- ──── KEYBOARD SHORTCUTS ──── -->
<div class="card">
  <h2 style="font-size:18px;margin-bottom:8px;">⌨️ Quick Reference</h2>
  <p style="font-size:14px;color:#4b5563;margin-bottom:8px;">
    Your learning journey at a glance:
  </p>
  <div style="font-size:14px;color:#4b5563;padding:12px;background:#f9fafb;border-radius:6px;line-height:1.8;">
    <strong>1.</strong> Login via your unique URL<br>
    <strong>2.</strong> Dashboard shows where you are<br>
    <strong>3.</strong> Open today&rsquo;s day workspace<br>
    <strong>4.</strong> Review requirements &amp; checkbox each one<br>
    <strong>5.</strong> Write your reflection + create the artifact<br>
    <strong>6.</strong> Self-score &amp; check Codex gates<br>
    <strong>7.</strong> Save → repeat next day<br>
    <strong>8.</strong> Check Feedback when reviewers respond<br>
    <strong>9.</strong> Track your Progress weekly<br>
    <strong>10.</strong> Celebrate completing all 28 days! 🎉
  </div>
</div>
'''
    return _html_page('Learner Guide', body, 'guide')


def _page_welcome() -> str:
    """Render the welcome / create-profile page (shown when no profiles exist)."""
    today_str = date.today().isoformat()
    body = f'''
<div class="welcome-page">
  <div style="max-width:540px;margin:60px auto;text-align:center;">
    <div style="font-size:64px;margin-bottom:16px;">👋</div>
    <h1>Welcome to the MUE Learning Program</h1>
    <p style="color:#6b7280;font-size:16px;line-height:1.6;">
      This is your personal workspace for the 28-day Business Intelligence
      curriculum. Before you begin, let's set up your learner profile.
    </p>
    <div class="card" style="margin-top:32px;text-align:left;">
      <h2 style="margin-top:0;">Create Your Profile</h2>
      <div class="form-group">
        <label for="nameInput">Your Name <span style="color:#ef4444;">*</span></label>
        <input type="text" id="nameInput" class="form-input"
               placeholder="e.g. Alex Chen" autofocus>
      </div>
      <div class="form-group">
        <label for="emailInput">Email Address <span style="color:#ef4444;">*</span></label>
        <input type="email" id="emailInput" class="form-input"
               placeholder="e.g. alex@example.com" required>
        <p style="font-size:12px;color:#6b7280;margin:4px 0 0;">
          Required for notifications and account recovery.
        </p>
      </div>
      <div class="form-group">
        <label for="startDateInput">Curriculum Start Date</label>
        <input type="date" id="startDateInput" class="form-input"
               value="{today_str}">
        <p style="font-size:12px;color:#6b7280;margin:4px 0 0;">
          Leave as today to follow the real schedule, or pick a past date to catch up.
        </p>
      </div>
      <div class="form-group">
        <label for="passwordInput">Password <span style="color:#ef4444;">*</span></label>
        <input type="password" id="passwordInput" class="form-input"
               placeholder="Create a password" required>
        <p style="font-size:12px;color:#6b7280;margin:4px 0 0;">
          Required to protect your profile. You'll need this to switch profiles or delete.
        </p>
      </div>
      <div class="form-group">
        <label for="confirmPasswordInput">Confirm Password <span style="color:#ef4444;">*</span></label>
        <input type="password" id="confirmPasswordInput" class="form-input"
               placeholder="Confirm your password" required>
      </div>
      <button class="btn btn-primary" onclick="doCreateProfile()"
              style="width:100%;padding:12px;font-size:16px;">
        🚀 Start Learning
      </button>
      <div id="createError" style="color:#ef4444;margin-top:12px;display:none;"></div>
    </div>
    <p style="font-size:13px;color:#9ca3af;margin-top:24px;">
      One profile per user. You can delete your profile later to start fresh.
    </p>
  </div>
</div>
<script>
function doCreateProfile() {{
  var name = document.getElementById('nameInput').value.trim();
  var email = document.getElementById('emailInput').value.trim() || null;
  var startDate = document.getElementById('startDateInput').value || null;
  var password = document.getElementById('passwordInput').value;
  var confirmPassword = document.getElementById('confirmPasswordInput').value;
  var errDiv = document.getElementById('createError');
  if(!name) {{ errDiv.textContent = 'Please enter your name.'; errDiv.style.display = 'block'; return; }}
  if(!email) {{ errDiv.textContent = 'Email address is required for daily summaries and reviewer feedback notifications.'; errDiv.style.display = 'block'; return; }}
  if(!password) {{ errDiv.textContent = 'Please enter a password.'; errDiv.style.display = 'block'; return; }}
  if(password !== confirmPassword) {{ errDiv.textContent = 'Passwords do not match.'; errDiv.style.display = 'block'; return; }}
  if(password.length < 4) {{ errDiv.textContent = 'Password must be at least 4 characters.'; errDiv.style.display = 'block'; return; }}
  errDiv.style.display = 'none';
  createProfile(name, startDate, password, email);
}}

function createProfile(name, startDate, password, email) {{
  fetch('/api/profiles/create', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{name: name, start_date: startDate, password: password, email: email}})
  }})
  .then(function(r){{return r.json()}})
  .then(function(r){{
    if(r.status==='ok'){{showToast('✅ Profile created!','success');setTimeout(function(){{location.reload()}},600);}}
    else{{showToast('❌ '+r.message,'error');}}
  }})
  .catch(function(e){{showToast('❌ '+e,'error');}});
}}
</script>'''
    return _html_page('Welcome — MUE Learner', body)


def _page_manage_profile() -> str:
    """Render the profile management page (edit profile details, change password, delete)."""
    try:
        _pid = _learner.profile_id or 'default'
        _pname = _learner.get_profile_label()
        # Fetch full profile info for email / start_date
        from action.proxy.web_interface import get_profile_by_id as _gpbi2
        _profile_full = _gpbi2(_pid) or {}
        _pemail = _profile_full.get('email', '')
        _pstart = _profile_full.get('start_date', '')
        _has_password = bool(_profile_full.get('password_hash'))
    except Exception:
        _pid = 'default'
        _pname = 'Unknown'
        _pemail = ''
        _pstart = ''
        _has_password = False

    today_str = date.today().isoformat()
    start_val = _pstart if _pstart else today_str

    body = f'''
<div style="max-width:540px;margin:40px auto;">
  <h1>⚙️ Profile Management</h1>

  <!-- ── Current Profile Info ── -->
  <div class="card" style="margin-top:20px;">
    <h2 style="margin-top:0;">Current Profile</h2>
    <p><strong>Name:</strong> {_pname}</p>
    <p><strong>ID:</strong> <code>{_pid}</code></p>
    <p><strong>Email:</strong> {_pemail or '<em style="color:#9ca3af;">Not set</em>'}</p>
    <p><strong>Password:</strong> {'✅ Set' if _has_password else '⚠️ Not set'}</p>
  </div>

  <!-- ── Edit Profile Details ── -->
  <div class="card" style="margin-top:20px;border-left:3px solid #6366f1;">
    <h2 style="margin-top:0;">✏️ Edit Profile Details</h2>
    <p style="font-size:13px;color:#6b7280;margin-bottom:12px;">
      Update your display name, email address, or curriculum start date.
      Your current password is required to make changes.
    </p>
    <div class="form-group">
      <label for="editName">Display Name</label>
      <input type="text" id="editName" class="form-input" value="{_pname}">
    </div>
    <div class="form-group">
      <label for="editEmail">Email Address <span style="color:#ef4444;">*</span></label>
      <input type="email" id="editEmail" class="form-input" value="{_pemail}" placeholder="your@email.com">
      <div style="font-size:12px;color:#6b7280;margin-top:4px;">Required for daily summaries and reviewer feedback notifications.</div>
    </div>
    <div class="form-group">
      <label for="editStartDate">Curriculum Start Date</label>
      <input type="date" id="editStartDate" class="form-input" value="{start_val}">
    </div>
    <div class="form-group">
      <label for="editCurrentPassword">Current Password <span style="color:#ef4444;">*</span></label>
      <input type="password" id="editCurrentPassword" class="form-input"
             placeholder="Required to save changes">
    </div>
    <button class="btn btn-primary" onclick="updateProfile()">
      💾 Save Changes
    </button>
    <div id="updateError" style="color:#ef4444;margin-top:12px;display:none;"></div>
    <div id="updateSuccess" style="color:#059669;margin-top:12px;display:none;"></div>
  </div>

  <!-- ── Change Password ── -->
  <div class="card" style="margin-top:20px;border-left:3px solid #f59e0b;">
    <h2 style="margin-top:0;">🔑 Change Password</h2>
    <p style="font-size:13px;color:#6b7280;margin-bottom:12px;">
      Set a new password for your profile. You will need your current password
      to confirm the change.
    </p>
    <div class="form-group">
      <label for="pwCurrent">Current Password <span style="color:#ef4444;">*</span></label>
      <input type="password" id="pwCurrent" class="form-input" placeholder="Enter current password">
    </div>
    <div class="form-group">
      <label for="pwNew">New Password <span style="color:#ef4444;">*</span></label>
      <input type="password" id="pwNew" class="form-input" placeholder="At least 4 characters">
    </div>
    <div class="form-group">
      <label for="pwConfirm">Confirm New Password <span style="color:#ef4444;">*</span></label>
      <input type="password" id="pwConfirm" class="form-input" placeholder="Re-enter new password">
    </div>
    <button class="btn btn-primary" onclick="changePassword()">
      🔑 Change Password
    </button>
    <div id="pwError" style="color:#ef4444;margin-top:12px;display:none;"></div>
    <div id="pwSuccess" style="color:#059669;margin-top:12px;display:none;"></div>
  </div>

  <!-- ── Danger Zone ── -->
  <div class="card" style="margin-top:20px;border-left:3px solid #ef4444;">
    <h2 style="margin-top:0;color:#ef4444;">⚠️ Danger Zone</h2>
    <p style="font-size:14px;color:#6b7280;">
      Deleting your profile will disconnect it from the dashboard. Your notes,
      evidence, and reports remain on disk and can be recovered if needed.
      You will be able to create a new profile afterward.
    </p>
    <div class="form-group" style="margin-top:16px;">
      <label for="deletePassword">Password <span style="color:#ef4444;">*</span></label>
      <input type="password" id="deletePassword" class="form-input" placeholder="Enter your password to confirm">
    </div>
    <button class="btn btn-danger" onclick="deleteProfile('{_pid}')">
      🗑️ Delete My Profile
    </button>
    <div id="deleteError" style="color:#ef4444;margin-top:12px;display:none;"></div>
  </div>
  <p style="margin-top:16px;">
    <a href="/" style="margin-right:12px;">← Back to Dashboard</a>
    <button class="btn btn-outline btn-sm" onclick="logoutProfile()">🚪 Logout</button>
</p>
</div>
<script>
function updateProfile() {{
  var name = document.getElementById('editName').value.trim();
  var email = document.getElementById('editEmail').value.trim();
  var startDate = document.getElementById('editStartDate').value || null;
  var currentPassword = document.getElementById('editCurrentPassword').value;
  var errDiv = document.getElementById('updateError');
  var successDiv = document.getElementById('updateSuccess');
  errDiv.style.display = 'none'; successDiv.style.display = 'none';
  if(!currentPassword) {{ errDiv.textContent = 'Current password is required to save changes.'; errDiv.style.display = 'block'; return; }}
  if(!name) {{ errDiv.textContent = 'Name cannot be empty.'; errDiv.style.display = 'block'; return; }}
  if(!email) {{ errDiv.textContent = 'Email cannot be empty.'; errDiv.style.display = 'block'; return; }}
  fetch('/api/profiles/update', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{profile_id: '{_pid}', current_password: currentPassword, name: name, email: email, start_date: startDate}})
  }})
  .then(function(r){{return r.json()}})
  .then(function(r){{
    if(r.status==='ok'){{
      successDiv.innerHTML = '✅ Profile updated! Changes: <ul style=\"margin:4px 0 0 16px;\">' + r.changes.map(function(c){{return '<li>' + c + '</li>'}}).join('') + '</ul>';
      successDiv.style.display = 'block';
      setTimeout(function(){{location.reload()}}, 2000);
    }}else{{
      errDiv.textContent = '❌ ' + r.message;
      errDiv.style.display = 'block';
    }}
  }})
  .catch(function(e){{errDiv.textContent = '❌ ' + e; errDiv.style.display = 'block';}});
}}

function changePassword() {{
  var currentPw = document.getElementById('pwCurrent').value;
  var newPw = document.getElementById('pwNew').value;
  var confirmPw = document.getElementById('pwConfirm').value;
  var errDiv = document.getElementById('pwError');
  var successDiv = document.getElementById('pwSuccess');
  errDiv.style.display = 'none'; successDiv.style.display = 'none';
  if(!currentPw) {{ errDiv.textContent = 'Please enter your current password.'; errDiv.style.display = 'block'; return; }}
  if(!newPw) {{ errDiv.textContent = 'Please enter a new password.'; errDiv.style.display = 'block'; return; }}
  if(newPw.length < 4) {{ errDiv.textContent = 'New password must be at least 4 characters.'; errDiv.style.display = 'block'; return; }}
  if(newPw !== confirmPw) {{ errDiv.textContent = 'New passwords do not match.'; errDiv.style.display = 'block'; return; }}
  fetch('/api/profiles/update', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{profile_id: '{_pid}', current_password: currentPw, new_password: newPw}})
  }})
  .then(function(r){{return r.json()}})
  .then(function(r){{
    if(r.status==='ok'){{
      successDiv.innerHTML = '✅ Password changed successfully!';
      successDiv.style.display = 'block';
      document.getElementById('pwCurrent').value = '';
      document.getElementById('pwNew').value = '';
      document.getElementById('pwConfirm').value = '';
      setTimeout(function(){{location.reload()}}, 2000);
    }}else{{
      errDiv.textContent = '❌ ' + r.message;
      errDiv.style.display = 'block';
    }}
  }})
  .catch(function(e){{errDiv.textContent = '❌ ' + e; errDiv.style.display = 'block';}});
}}

function deleteProfile(profileId) {{
  var password = document.getElementById('deletePassword').value;
  var errDiv = document.getElementById('deleteError');
  if(!password) {{ errDiv.textContent = 'Password is required to delete your profile.'; errDiv.style.display = 'block'; return; }}
  errDiv.style.display = 'none';
  if(!confirm('Are you sure you want to delete your profile? All progress data will be disconnected (files remain on disk).')) return;
  fetch('/api/profiles/delete', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{profile_id: profileId, password: password}})
  }})
  .then(function(r){{return r.json()}})
  .then(function(r){{
    if(r.status==='ok'){{showToast('🗑️ Profile deleted.','success');setTimeout(function(){{location.reload()}},600);}}
    else{{showToast('❌ '+r.message,'error');}}
  }})
  .catch(function(e){{showToast('❌ '+e,'error');}});
}}
</script>'''
    return _html_page('Manage Profile — MUE Learner', body, 'home')


def _page_admin_login(cookie_header: str = '') -> str:
    """Render the admin login page — two-step email confirmation code flow."""
    current_admin = _get_admin_from_cookies(cookie_header)
    admin_profiles = [p for p in _profiles_list if _is_admin_profile(p['id'])]

    if not admin_profiles:
        body = '''
<div style="max-width:480px;margin:60px auto;text-align:center;">
  <h1>🔑 Admin Access</h1>
  <div class="card">
    <p style="color:#6b7280;">No administrative profiles exist yet.</p>
    <p style="font-size:13px;color:#6b7280;">Create a profile named "owner_user" to enable admin access.</p>
    <a href="/" class="btn btn-primary" style="display:inline-block;margin-top:12px;">← Back to Home</a>
  </div>
</div>'''
        return _html_page('Admin Login — MUE Learner', body)

    logged_in_html = ''
    if current_admin:
        logged_in_html = f'''
<div style="background:#d1fae5;border:1px solid #6ee7b7;border-radius:8px;padding:12px;margin-bottom:16px;text-align:center;font-size:14px;">
  ✅ Signed in as <strong>{_esc_html(current_admin)}</strong>
  <br><a href="/" style="color:#6366f1;font-size:13px;">← Back to Dashboard</a>
  <br><button onclick="adminLogout()" class="btn btn-outline btn-sm" style="margin-top:8px;font-size:12px;">🚪 Logout</button>
</div>'''

    body = f'''
<div style="max-width:480px;margin:40px auto;">
  <h1 style="text-align:center;">🔑 Admin Access</h1>
  <p style="font-size:13px;color:#6b7280;margin-bottom:16px;text-align:center;">
    Administrative profiles are hidden from the profile switcher.
    Sign in with an admin account to access them.
  </p>
  {logged_in_html}
  <div id="loginForm" style="display:{'none' if current_admin else 'block'};">
    <!-- Step 1: Enter username -->
    <div id="step1" class="card" style="padding:20px;">
      <label style="font-size:13px;color:#6b7280;display:block;margin-bottom:6px;">Admin Username</label>
      <input type="text" id="username" class="form-input" style="width:100%;font-size:16px;" placeholder="e.g. owner_user" autocomplete="off" onkeydown="if(event.key==='Enter')requestCode()">
      <button class="btn btn-primary" style="width:100%;margin-top:12px;" onclick="requestCode()" id="requestBtn">📧 Send Confirmation Code</button>
      <p style="font-size:12px;color:#6b7280;margin-top:8px;text-align:center;">A one-time code will be sent to the admin email.</p>
      <p class="toast-error" id="step1Error" style="display:none;text-align:center;"></p>
    </div>
    <!-- Step 2: Enter confirmation code -->
    <div id="step2" class="card" style="padding:20px;display:none;">
      <label style="font-size:13px;color:#6b7280;display:block;margin-bottom:6px;">Confirmation Code</label>
      <input type="text" id="code" class="form-input" style="width:100%;font-size:24px;text-align:center;letter-spacing:8px;font-weight:700;" placeholder="000000" autocomplete="off" onkeydown="if(event.key==='Enter')verifyCode()">
      <p style="font-size:12px;color:#6b7280;margin-top:4px;text-align:center;" id="codeSentInfo">A code was sent to the admin email.</p>
      <button class="btn btn-primary" style="width:100%;margin-top:12px;" onclick="verifyCode()" id="verifyBtn">🔐 Verify &amp; Sign In</button>
      <div style="margin-top:8px;text-align:center;">
        <a onclick="backToStep1()" style="color:#6366f1;font-size:12px;cursor:pointer;text-decoration:underline;">← Use a different username</a>
      </div>
      <p class="toast-error" id="step2Error" style="display:none;text-align:center;"></p>
    </div>
  </div>
  <div style="margin-top:16px;text-align:center;">
    <a href="/" class="btn btn-outline btn-sm" style="text-decoration:none;">← Back to Home</a>
  </div>
</div>
<script>
var _pendingUsername = '';
function showError(id, msg) {{ var el = document.getElementById(id); if(el) {{ el.textContent = msg; el.style.display = 'block'; }} }}
function hideError(id) {{ var el = document.getElementById(id); if(el) el.style.display = 'none'; }}

async function requestCode() {{
  var user = document.getElementById('username').value.trim();
  var btn = document.getElementById('requestBtn');
  if(!user) {{ showError('step1Error', 'Username is required.'); return; }}
  hideError('step1Error');
  btn.disabled = true; btn.textContent = '⏳ Sending…';
  try {{
    var resp = await fetch('/api/admin/auth', {{
      method: 'POST',
      headers: {{'Content-Type':'application/json'}},
      body: JSON.stringify({{username: user, action: 'request_code'}})
    }});
    var data = await resp.json();
    if(data.ok) {{
      _pendingUsername = user;
      document.getElementById('step1').style.display = 'none';
      document.getElementById('step2').style.display = 'block';
      document.getElementById('codeSentInfo').textContent = 'A confirmation code was sent to the registered admin email.';
      document.getElementById('code').value = '';
      document.getElementById('code').focus();
    }} else {{
      showError('step1Error', data.error || 'Failed to send code.');
    }}
  }} catch(e) {{
    showError('step1Error', 'Connection error: ' + e.message);
  }}
  btn.disabled = false; btn.textContent = '📧 Send Confirmation Code';
}}

async function verifyCode() {{
  var code = document.getElementById('code').value.trim();
  var btn = document.getElementById('verifyBtn');
  if(!code) {{ showError('step2Error', 'Please enter the confirmation code.'); return; }}
  if(!_pendingUsername) {{ showError('step2Error', 'Session expired. Start again.'); return; }}
  hideError('step2Error');
  btn.disabled = true; btn.textContent = '⏳ Verifying…';
  try {{
    var resp = await fetch('/api/admin/auth', {{
      method: 'POST',
      headers: {{'Content-Type':'application/json'}},
      body: JSON.stringify({{username: _pendingUsername, code: code, action: 'verify_code'}})
    }});
    var data = await resp.json();
    if(data.ok) {{
      window.location.href = '/';
    }} else {{
      showError('step2Error', data.error || 'Invalid code.');
    }}
  }} catch(e) {{
    showError('step2Error', 'Connection error: ' + e.message);
  }}
  btn.disabled = false; btn.textContent = '🔐 Verify &amp; Sign In';
}}

function backToStep1() {{
  document.getElementById('step2').style.display = 'none';
  document.getElementById('step1').style.display = 'block';
  _pendingUsername = '';
  hideError('step2Error');
}}

async function adminLogout() {{
  try {{
    await fetch('/api/profile/logout', {{ method: 'POST' }});
    window.location.href = '/admin-login';
  }} catch(e) {{
    console.error('Logout failed:', e);
    window.location.href = '/admin-login';
  }}
}}
</script>'''
    return _html_page('Admin Login — MUE Learner', body)


def _page_dashboard() -> str:
    """Render the dashboard/home page."""
    today_str = date.today().isoformat()
    day_num = _learner.get_curriculum_day(today_str)
    if day_num is None:
        day_num = 1  # fallback for weekends

    entry = _learner.get_curriculum_day_info(day_num)
    classification = get_classification(day_num)
    primary_track = get_primary_track(day_num)
    level = get_level_for_day(day_num)
    week_num = (day_num - 1) // 7 + 1
    focus = entry.get('focus', '')
    required_artifact = entry.get('required_artifact', '')
    tags = entry.get('tags', [])
    tag_html = ' '.join(f'<span>{t}</span>' for t in tags)

    notes_count = len(_learner.list_notes())
    evidence_count = len(_learner.list_evidence())

    colour = CLASS_COLOURS.get(classification, '#6b7280')

        # ── Build list of incomplete prior days ─────────────────────────────
    existing_notes = {n.stem for n in _learner.list_notes()}  # {'2026-07-21', ...}
    incomplete_prior = []
    for d in range(1, day_num):
        day_info = CURRICULUM.get(d, {})
        day_info['_day_num'] = d
        # Check if any existing note maps to this curriculum day
        has_note = False
        for note_stem in existing_notes:
            try:
                nd = _learner.get_curriculum_day(note_stem)
                if nd == d:
                    has_note = True
                    break
            except Exception:
                continue
        if not has_note:
            incomplete_prior.append(day_info)

    catchup_rows = ''
    if incomplete_prior:
        for d_info in incomplete_prior[:10]:  # limit to 10 to avoid clutter
            d_num = d_info['_day_num']
            focus_short = d_info.get('focus', '')[:60]
            catchup_rows += f'''<div class="note-list-item">
  <div>
    <div class="note-date">Day {d_num}</div>
    <div style="font-size:12px;color:#6b7280;">{focus_short}</div>
  </div>
  <div class="note-actions">
    <a href="/day/{d_num}" class="btn btn-outline btn-sm">✏️ Catch Up</a>
  </div>
</div>'''
        catchup_section = f'''
<div class="card" style="border-left:3px solid #f59e0b;">
  <h2>⏰ Catch Up — {len(incomplete_prior)} incomplete day(s)</h2>
  <p style="font-size:13px;color:#6b7280;margin-bottom:8px;">
    You haven't written notes for these prior days yet.
  </p>
  {catchup_rows}
  {f'<p style="font-size:12px;color:#6b7280;text-align:center;">… and {len(incomplete_prior) - 10} more</p>' if len(incomplete_prior) > 10 else ''}
</div>'''
    else:
        catchup_section = ''

    # Check if profile has an email address
    try:
        from action.proxy.web_interface import get_profile_by_id as _gpbi3
        _profile_data = _gpbi3(_learner.profile_id)
        _has_email = bool(_profile_data and _profile_data.get('email'))
    except Exception:
        _has_email = False

    email_banner = ''
    if not _has_email:
        email_banner = '''
<div class="card" style="border-left:4px solid #f59e0b;background:#fefce8;margin-bottom:16px;">
  <div style="display:flex;align-items:center;gap:12px;">
    <span style="font-size:24px;">📧</span>
    <div>
      <strong>Email address required</strong>
      <p style="font-size:13px;color:#6b7280;margin:2px 0 0;">
        Set your email address on the <a href="/manage" style="color:#6366f1;">Profile Management</a> page
        to receive daily summaries and reviewer feedback notifications.
      </p>
    </div>
  </div>
</div>'''

    body = f'''
{email_banner}
<div class="stats-grid">
  <div class="stat-card">
    <div class="stat-value">Day {day_num}</div>
    <div class="stat-label">Current Day</div>
  </div>
  <div class="stat-card">
    <div class="stat-value">Week {week_num}</div>
    <div class="stat-label">{WEEK_NAMES.get(week_num, '')}</div>
  </div>
  <div class="stat-card">
    <div class="stat-value">{notes_count}</div>
    <div class="stat-label">Notes</div>
  </div>
  <div class="stat-card">
    <div class="stat-value">{evidence_count}</div>
    <div class="stat-label">Evidence Files</div>
  </div>
</div>

<div class="card">
  <h2>📋 Today — Day {day_num}</h2>
  <div style="margin-bottom:12px;">
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
      <span style="font-size:18px;font-weight:600;">{focus}</span>
      <span style="font-size:13px;padding:3px 10px;border-radius:12px;background:{colour}20;color:{colour};font-weight:600;">{classification}</span>
    </div>
    <div class="day-tags" style="margin-top:6px;">{tag_html}</div>
  </div>
  <div style="font-size:14px;color:#6b7280;margin-bottom:12px;">
    Track: <strong>{primary_track}</strong> · Level: <strong>{level}</strong>
  </div>
  {_day_progress_bar(day_num)}
  <div style="margin-top:16px;display:flex;gap:8px;flex-wrap:wrap;">
    <a href="/day/{day_num}" class="btn btn-primary">✏️ Work on Day {day_num}</a>
    <a href="/curriculum" class="btn btn-outline">📖 View Curriculum</a>
  </div>
</div>

{catchup_section}

<!-- ── Upcoming / Future Days ────────────────────────────── -->
{_upcoming_section(day_num)}

<div class="card">
  <h2>📅 Quick Actions</h2>
  <div style="display:flex;gap:8px;flex-wrap:wrap;">
    <a href="/notes" class="btn btn-outline btn-sm">📝 All Notes</a>
    <a href="/curriculum" class="btn btn-outline btn-sm">📚 Full Schedule</a>
  </div>
</div>

<div class="card" style="border-left:3px solid #6366f1;">
  <h2>👤 Profile</h2>
  <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
    <span style="font-size:14px;color:#6b7280;">
      Signed in as <strong>{_learner.get_profile_label()}</strong>
    </span>
    <a href="/manage" class="btn btn-outline btn-sm">⚙️ Manage Profile</a>
  </div>
</div>
'''
    return _html_page('Dashboard', body, 'home')


def _upcoming_section(current_day: int) -> str:
    """Render a small 'Work Ahead' section showing future days."""
    future_days = []
    for d in range(current_day + 1, min(current_day + 6, 29)):  # show next 5 days
        info = CURRICULUM.get(d, {})
        if info:
            info['_day_num'] = d
            future_days.append(info)
    if not future_days:
        return ''
    rows = ''
    for d_info in future_days:
        d_num = d_info['_day_num']
        focus_short = d_info.get('focus', '')[:60]
        rows += f'''<div class="note-list-item">
  <div>
    <div class="note-date">Day {d_num}</div>
    <div style="font-size:12px;color:#6b7280;">{focus_short}</div>
  </div>
  <div class="note-actions">
    <a href="/day/{d_num}" class="btn btn-outline btn-sm">👁️ Preview</a>
  </div>
</div>'''
    return f'''
<div class="card" style="border-left:3px solid #8b5cf6;">
  <h2>🔮 Work Ahead — Upcoming Days</h2>
  <p style="font-size:13px;color:#6b7280;margin-bottom:8px;">
    You can preview or start working on future days at any time.
  </p>
  {rows}
</div>'''


def _page_curriculum(week_filter: int = 0) -> str:
    """Render the full 28-day curriculum viewer."""
    week_buttons = '<div class="week-filter">'
    week_buttons += f'<button class="{"active" if week_filter == 0 else ""}" onclick="location.href=\'/curriculum\'">All</button>'
    for w in range(1, 5):
        cls = 'active' if week_filter == w else ''
        week_buttons += f'<button class="{cls}" onclick="location.href=\'/curriculum?week={w}\'">Week {w}</button>'
    week_buttons += '</div>'

    today_str = date.today().isoformat()
    current_day = _learner.get_curriculum_day(today_str)

    # Build a set of curriculum day numbers that already have notes
    completed_days = set()
    for note_path in _learner.list_notes():
        nd = _learner._extract_day_from_note(note_path)
        if nd:
            completed_days.add(nd)

    cards = []
    for day_num in range(1, 29):
        entry = CURRICULUM.get(day_num, {})
        entry_week = entry.get('week', (day_num - 1) // 7 + 1)
        if week_filter and entry_week != week_filter:
            continue

        focus = entry.get('focus', '')
        tags = entry.get('tags', [])
        required_artifact = entry.get('required_artifact', '')
        proof_task = entry.get('proof_task', '')
        tag_html = ' '.join(f'<span>{t}</span>' for t in tags)
        is_current = 'current' if day_num == current_day else ''
        is_complete = day_num in completed_days
        is_past = current_day is not None and day_num < current_day
        past_class = 'past' if is_past and not is_complete else ''
        badge = '✅' if is_complete else ('⏳' if is_past else '')
        pt_html = f'<div style="font-size:12px;color:#8b5cf6;margin-top:4px;">🔖 {proof_task}</div>' if proof_task else ''

        evidence_desc = (entry.get('evidence_description', '') or '')[:120]
        if len(entry.get('evidence_description', '')) > 120:
            evidence_desc += '…'
        cards.append(f'''
<div class="day-card {is_current} {past_class}" onclick="location.href='/day/{day_num}'">
  <div class="day-header">
    <span class="day-number">Day {day_num}</span>
    <span class="day-week">Week {entry_week} — {WEEK_NAMES.get(entry_week, '')}</span>
    {f'<span style="font-size:16px;">{badge}</span>' if badge else ''}
  </div>
  <div class="day-focus">{focus}</div>
  <div style="font-size:12px;color:#6b7280;margin:4px 0;">{evidence_desc}</div>
  <div class="day-tags">{tag_html}</div>
  {pt_html}
  <div class="day-artifact">{required_artifact}</div>
</div>''')

    body = f'''
<h2 style="margin-bottom:16px;">📚 Full Curriculum — 28 Days</h2>
{week_buttons}
<div class="curriculum-grid">
{''.join(cards)}
</div>
<p style="font-size:12px;color:#6b7280;text-align:center;margin-top:12px;">
  ✅ = complete · ⏳ = past due · Click a day card for full requirements
</p>
'''
    return _html_page('Curriculum', body, 'curriculum')


def _page_day_workspace(day_number: int) -> str:
    """Consolidated day workspace — instructions, note editor, scorecard, gates, and evidence all on one page."""
    entry = CURRICULUM.get(day_number)
    if not entry:
        return _html_page('Not Found', f'<div class="card"><h2>❌ Day {day_number} not found</h2><a href="/curriculum" class="btn btn-outline">← Back</a></div>', 'curriculum')

    week = entry.get('week', (day_number - 1) // 7 + 1)
    theme = entry.get('theme', WEEK_NAMES.get(week, ''))
    focus = entry.get('focus', '')
    evidence_desc = entry.get('evidence_description', '')
    required_artifact = entry.get('required_artifact', '')
    proof_task = entry.get('proof_task', '')
    tags = entry.get('tags', [])
    tag_html = ' '.join(f'<span>{t}</span>' for t in tags)
    classification = get_classification(day_number)
    track = get_primary_track(day_number)
    level = get_level_for_day(day_number)
    colour = CLASS_COLOURS.get(classification, '#6b7280')
    has_codex = any('⚡ Codex' in t or 'Codex' in t for t in tags)
    has_ai = any('🤖 AI' in t or 'AI' in t for t in tags)
    has_pyr = any('🏗️ Pyr' in t or 'Pyr' in t for t in tags)
    has_team = any('💬 Team' in t or 'Team' in t for t in tags)
    has_data = any('🔗 Data' in t or 'Data' in t for t in tags)
    has_del = any('📦 Del' in t or 'Del' in t for t in tags)
    has_bi = any('📊 BI' in t or 'BI' in t for t in tags)
    has_ret = any('🧠 Ret' in t or 'Ret' in t for t in tags)

    today_str = date.today().isoformat()
    # Calculate the correct calendar date for this curriculum day
    day_date = _learner._day_to_date(day_number).isoformat()

    # ── Check completion / load existing note ──────────────────────────
    is_complete = False
    existing_note_data = None
    existing_note_date = None
    for note_path in _learner.list_notes():
        nd = _learner._extract_day_from_note(note_path)
        if nd == day_number:
            is_complete = True
            existing_note_date = note_path.stem
            try:
                raw = note_path.read_text(encoding='utf-8')
                ndata = {}
                def _es(heading):
                    pat = rf'## {heading}:\s*\n(.*?)(?:\n## |\Z)'
                    m = re.search(pat, raw, re.DOTALL)
                    return m.group(1).strip() if m else ''
                ndata = {
                    'what_learned': _es('What I learned'),
                    'evidence_produced': _es('Evidence produced'),
                    'what_remains': _es('What remains'),
                    'next_step': _es('Next step'),
                }
                ndata['scorecard'] = {}
                sc_match = re.search(r'\*\*Scorecard:\*\*(.*?)(?:\n## |\Z)', raw, re.DOTALL)
                if sc_match:
                    for line in sc_match.group(1).strip().split('\n'):
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            ndata['scorecard'][parts[0].strip()] = parts[1].strip()
                ndata['codex_gate'] = {}
                cg_match = re.search(r'\*\*Codex Gates:\*\*(.*?)(?:\n## |\Z)', raw, re.DOTALL)
                if cg_match:
                    for line in cg_match.group(1).strip().split('\n'):
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            ndata['codex_gate'][parts[0].strip()] = parts[1].strip()
                existing_note_data = ndata
            except Exception:
                pass
            break

    # ── Evidence for this day ─────────────────────────────────────────
    day_evidence = []
    for f in sorted(_learner.evidence_dir.glob('*.*'), reverse=True):
        d = _extract_day_from_filename(f.name)
        if d == day_number or (f.name.startswith(f'Day{day_number}') or f.name.startswith(f'Day_{day_number}')):
            pt_id = _extract_pt_id(f.name)
            size_kb = round(f.stat().st_size / 1024, 1) if f.stat().st_size else 0
            day_evidence.append({'filename': f.name, 'pt_id': pt_id, 'size_kb': size_kb})
        if f.stem == existing_note_date:
            pt_id = _extract_pt_id(f.name)
            size_kb = round(f.stat().st_size / 1024, 1) if f.stat().st_size else 0
            if not any(e['filename'] == f.name for e in day_evidence):
                day_evidence.append({'filename': f.name, 'pt_id': pt_id, 'size_kb': size_kb})

    evidence_rows = ''
    if day_evidence:
        for ev in day_evidence:
            pt_badge = f'<span class="pt-badge">{ev["pt_id"]}</span>' if ev['pt_id'] else ''
            evidence_rows += f'''<div class="note-list-item">
  <div>
    <div class="note-date" style="font-size:13px;">{ev['filename']}</div>
    <div style="font-size:11px;color:#6b7280;display:flex;gap:6px;align-items:center;margin-top:2px;">
      {pt_badge}<span>{ev['size_kb']} KB</span>
    </div>
  </div>
  <div class="note-actions">
    <a href="/evidence/{ev['filename']}" class="btn btn-outline btn-sm">View</a>
    <button class="btn btn-outline btn-sm" onclick="deleteEvidenceDay({day_number},'{ev['filename']}')">🗑️</button>
  </div>
</div>'''
    else:
        evidence_rows = '<p style="font-size:13px;color:#6b7280;padding:8px 0;">No evidence uploaded for this day yet.</p>'

    # ── Scorecard toggles ─────────────────────────────────────────────
    scorecard_areas = _learner.get_scorecard_areas()
    scorecard_html = ''
    for area in scorecard_areas:
        val = existing_note_data.get('scorecard', {}).get(area, 'Unscored') if existing_note_data else 'Unscored'
        scorecard_html += f'''<div class="toggle-item">
  <span>{area}</span>
  <select name="scorecard_{area}">
    <option {"selected" if val=="Pass" else ""}>Pass</option>
    <option {"selected" if val=="Moderate" else ""}>Moderate</option>
    <option {"selected" if val=="Fail" else ""}>Fail</option>
    <option {"selected" if val=="Unscored" else ""}>Unscored</option>
  </select>
</div>'''

    # ── Codex gate toggles ────────────────────────────────────────────
    codex_gates = _learner.get_codex_gates_list()
    gate_html = ''
    for gate in codex_gates:
        val = existing_note_data.get('codex_gate', {}).get(gate, 'No') if existing_note_data else 'No'
        gate_html += f'''<div class="toggle-item">
  <span>{gate}</span>
  <select name="codexgate_{gate}">
    <option {"selected" if val=="Yes" else ""}>Yes</option>
    <option {"selected" if val=="No" else ""}>No</option>
  </select>
</div>'''

    # Pre-fill note fields
    wl = existing_note_data.get('what_learned', '') if existing_note_data else ''
    ep = existing_note_data.get('evidence_produced', '') if existing_note_data else ''
    wr = existing_note_data.get('what_remains', '') if existing_note_data else ''
    ns = existing_note_data.get('next_step', '') if existing_note_data else ''
    note_save_label = 'Update Note' if existing_note_date else 'Save Note'
    note_saved_status = f'<span style="font-size:13px;color:#059669;">✅ Saved — <a href="/notes/{existing_note_date}" style="font-size:13px;">view note</a></span>' if existing_note_date else ''

    # ── Dynamic field placeholders based on day tags ──────────────────
    wl_ph = 'Describe what you learned today…'
    ep_ph = 'Describe the evidence you produced…'
    wr_ph = 'What is still unresolved?'
    ns_ph = 'What is your immediate next action?'
    wl_help = ''
    ep_help = ''
    if has_ai:
        wl_help = '💡 Include the prompt structure you used (Context + Task + Format + Constraints)'
        ep_ph = 'List the prompts you crafted and their outputs…'
    if has_codex:
        wl_help = ('💡 Include your Codex Loop steps: Pull → Summarize → Identify → Execute → Record' if not wl_help else wl_help + '; also note Codex Loop steps')
        ep_ph = 'Document your Codex exercise results, before/after comparisons…'
    if has_pyr:
        wl_help = ('💡 Reference specific Pyramid operations or model interactions' if not wl_help else wl_help + '; reference Pyramid operations')
    if has_data:
        wl_help = ('💡 Note the data layers and transformations you worked with' if not wl_help else wl_help + '; document data transformations')
    if has_del:
        ep_ph = 'Describe the delivery artifacts produced (checklists, handoffs, deployments)…'
    if has_bi:
        wl_help = ('💡 Focus on BI-judgment decisions and validation reasoning' if not wl_help else wl_help + '; capture BI-judgment decisions')
    if has_team:
        ns_ph = 'What is your next step for team sync or handoff?'
    if has_ret:
        wl_help = ('💡 Note what research or review findings you uncovered' if not wl_help else wl_help + '; capture research findings')

    # ── Requirement checklist ─────────────────────────────────────────
    def _parse_checklist(text: str) -> list:
        items = []
        # Split on common delimiters: +, -, •, numbered lists, or sentence endings with clear action items
        for sep in ['\n', ',', ' + ']:
            if sep in text:
                candidates = text.split(sep)
                if len(candidates) >= 2:
                    for c in candidates:
                        c = c.strip().strip('+').strip('-').strip('•').strip()
                        if c and len(c) > 8:
                            items.append(c)
                    if items:
                        break
        if not items or len(items) < 2:
            items = [text]
        return items[:8]  # max 8 items

    checklist_items = _parse_checklist(evidence_desc)
    checklist_html = ''
    if len(checklist_items) > 1:
        checklist_html = '<ul class="req-checklist" id="reqChecklist">'
        for item in checklist_items:
            safe_item = item.replace("'", "&#39;").replace('"', '&quot;')
            checklist_html += f'<li onclick="toggleReq(this)"><input type="checkbox"><span>{safe_item}</span></li>'
        checklist_html += '</ul>'

    # ── Artifact format badge ─────────────────────────────────────────
    artifact_ext = required_artifact.rsplit('.', 1)[-1].lower() if '.' in required_artifact else ''
    ext_labels = {'md': '📝 Markdown', 'png': '🖼️ Screenshot', 'jpg': '🖼️ Image', 'jpeg': '🖼️ Image', 'pdf': '📄 PDF', 'csv': '📊 CSV', 'txt': '📄 Text'}
    format_badge = f'<span class="artifact-format">{ext_labels.get(artifact_ext, "📄 File")}</span>' if artifact_ext else ''

    # ── Template button logic ─────────────────────────────────────────
    template_btn = ''
    if artifact_ext == 'md':
        template_btn = f'<button type="button" class="btn btn-outline btn-sm" onclick="useTemplate(\'{required_artifact}\', {day_number})">📄 Use Template</button>'
    elif artifact_ext in ('png', 'jpg', 'jpeg'):
        template_btn = f'<button type="button" class="btn btn-outline btn-sm" onclick="showScreenshotGuide()">📸 Screenshot Guide</button>'

    # ── Proof task details ────────────────────────────────────────────
    pt_info = ''
    if proof_task and proof_task in PROOF_TASKS:
        pt = PROOF_TASKS[proof_task]
        criteria = PROOF_TASK_CRITERIA.get(proof_task, {})
        sections = criteria.get('required_sections', [])
        checks = criteria.get('quality_checks', [])
        sections_html = ''.join(f'<li>{s}</li>' for s in sections)
        checks_html = ''.join(f'<li>{c}</li>' for c in checks)
        pt_info = f'''
<div class="card" style="border-left:3px solid #8b5cf6;">
  <h3>🔖 {proof_task}: {pt.get('name', '')}</h3>
  <p style="font-size:13px;color:#6b7280;">Due by Day {pt.get('due_day', '?')} · Level {pt.get('level', '?')}</p>
  <details style="margin-top:8px;">
    <summary style="font-size:13px;cursor:pointer;font-weight:600;">Required Sections & Quality Checks</summary>
    <h4 style="margin-top:8px;font-size:13px;">Required Sections</h4>
    <ul>{sections_html}</ul>
    <h4 style="margin-top:8px;font-size:13px;">Quality Checks</h4>
    <ul>{checks_html}</ul>
  </details>
  <div style="margin-top:8px;">
    <a href="/evidence/new?pt={proof_task}&day={pt.get('due_day', day_number)}" class="btn btn-primary btn-sm">Create {proof_task} Evidence</a>
  </div>
</div>'''

    # ── Navigation ────────────────────────────────────────────────────
    prev_link = f'<a href="/day/{day_number - 1}" class="btn btn-outline btn-sm">◀ Day {day_number - 1}</a>' if day_number > 1 else '<span class="btn btn-outline btn-sm" style="opacity:0.4;cursor:default;">◀ Day 1</span>'
    next_link = f'<a href="/day/{day_number + 1}" class="btn btn-outline btn-sm">Day {day_number + 1} ▶</a>' if day_number < 28 else '<span class="btn btn-outline btn-sm" style="opacity:0.4;cursor:default;">Day 28 ▶</span>'

    body = f'''
<h2 style="margin-bottom:16px;">📖 Day {day_number}: {focus}</h2>

<div style="display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap;align-items:center;">
  {prev_link}
  {next_link}
  <span style="flex:1;"></span>
  <a href="/curriculum" class="btn btn-outline btn-sm">← All Days</a>
</div>

<!-- ════════════════ DAY HEADER ════════════════ -->
<div class="card">
  <div style="display:flex;justify-content:space-between;align-items:start;flex-wrap:wrap;gap:8px;">
    <div>
      <h3 style="margin:0;">{focus}</h3>
      <p style="font-size:13px;color:#6b7280;margin:4px 0;">
        Week {week} — {theme} · {tag_html}
      </p>
    </div>
    <div style="text-align:right;">
      <span style="font-size:13px;padding:3px 10px;border-radius:12px;background:{colour}20;color:{colour};font-weight:600;">{classification}</span>
      <div style="font-size:12px;color:#6b7280;margin-top:4px;">Level {level} · {track}</div>
      {f'<div style="font-size:16px;margin-top:4px;">✅ Complete</div>' if is_complete else f'<div style="font-size:16px;margin-top:4px;">⏳ Pending</div>'}
    </div>
  </div>
</div>

<!-- ════════════════ REQUIREMENTS ════════════════ -->
<div class="card">
  <details open>
    <summary style="font-size:16px;font-weight:600;cursor:pointer;">📋 Requirements for Today</summary>
    <div style="font-size:14px;line-height:1.7;margin-top:8px;">
      {evidence_desc}
    </div>
    {checklist_html}
  </details>
</div>

<!-- ════════════════ REQUIRED ARTIFACT ════════════════ -->
<div class="card">
  <h3 style="display:flex;justify-content:space-between;align-items:center;">
    <span>📎 Required Artifact</span>
    {format_badge}
  </h3>
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-top:8px;">
    <code style="font-size:14px;background:#f3f4f6;padding:6px 12px;border-radius:4px;">{required_artifact}</code>
    <div style="display:flex;gap:6px;">
      {template_btn}
      <button type="button" class="btn btn-primary btn-sm" onclick="document.getElementById('evidenceUploadInput').click()">📎 Upload Artifact</button>
      <a href="/notes/new?day={day_number}" class="btn btn-outline btn-sm">✏️ Full Note Page</a>
    </div>
  </div>
</div>

<!-- ════════════════ PROOF TASK ════════════════ -->
{pt_info}

<!-- ════════════════ DAILY NOTE EDITOR ════════════════ -->
<div class="card" id="noteSection">
  <h2 style="display:flex;justify-content:space-between;align-items:center;">
    <span>📝 Daily Reflection</span>
    {note_saved_status}
  </h2>

  <form id="dayNoteForm" onsubmit="return saveDayNote(event, {day_number})">
    <div class="form-row">
      <div class="form-group">
        <label>Date</label>
        <input type="date" name="date" value="{existing_note_date or day_date}" readonly>
      </div>
      <div class="form-group">
        <label>Day Number</label>
        <input type="number" name="day_number" value="{day_number}" readonly>
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Classification</label>
        <select name="classification">
          <option {"selected" if classification=="Foundational" else ""}>Foundational</option>
          <option {"selected" if classification=="Developing" else ""}>Developing</option>
          <option {"selected" if classification=="Operational" else ""}>Operational</option>
          <option {"selected" if classification=="Ready For Codex Acceleration" else ""}>Ready For Codex Acceleration</option>
        </select>
      </div>
      <div class="form-group">
        <label>Primary Track</label>
        <select name="primary_track">
          <option {"selected" if track=="Pyramid operations" else ""}>Pyramid operations</option>
          <option {"selected" if track=="Codex productivity" else ""}>Codex productivity</option>
          <option {"selected" if track=="BI judgment" else ""}>BI judgment</option>
        </select>
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Level</label>
        <select name="level">
          <option {"selected" if level==1 else ""}>1</option>
          <option {"selected" if level==2 else ""}>2</option>
          <option {"selected" if level==3 else ""}>3</option>
          <option {"selected" if level==4 else ""}>4</option>
        </select>
      </div>
      <div class="form-group">
        <label>Week Number</label>
        <input type="number" name="week_number" value="{week}" readonly>
      </div>
    </div>

    <div class="form-group">
      <label>What I learned today</label>
      <div style="display:flex;gap:6px;margin-bottom:4px;">
        <button type="button" class="btn btn-outline btn-sm" onclick="togglePreview(this, 'what_learned')">👁️ Preview</button>
        {f'<span class="field-help">{wl_help}</span>' if wl_help else ''}
      </div>
      <textarea class="note-field" name="what_learned" placeholder="{wl_ph}" oninput="autoResize(this)">{wl}</textarea>
      <div class="md-preview" id="preview_what_learned"></div>
    </div>
    <div class="form-group">
      <label>What evidence I produced</label>
      <div style="display:flex;gap:6px;margin-bottom:4px;">
        <button type="button" class="btn btn-outline btn-sm" onclick="togglePreview(this, 'evidence_produced')">👁️ Preview</button>
      </div>
      <textarea class="note-field" name="evidence_produced" placeholder="{ep_ph}" oninput="autoResize(this)">{ep}</textarea>
      <div class="md-preview" id="preview_evidence_produced"></div>
    </div>
    <div class="form-group">
      <label>What remains open</label>
      <div style="display:flex;gap:6px;margin-bottom:4px;">
        <button type="button" class="btn btn-outline btn-sm" onclick="togglePreview(this, 'what_remains')">👁️ Preview</button>
      </div>
      <textarea class="note-field" name="what_remains" placeholder="{wr_ph}" oninput="autoResize(this)">{wr}</textarea>
      <div class="md-preview" id="preview_what_remains"></div>
    </div>
    <div class="form-group">
      <label>Next narrow step</label>
      <div style="display:flex;gap:6px;margin-bottom:4px;">
        <button type="button" class="btn btn-outline btn-sm" onclick="togglePreview(this, 'next_step')">👁️ Preview</button>
      </div>
      <textarea class="note-field" name="next_step" placeholder="{ns_ph}" oninput="autoResize(this)">{ns}</textarea>
      <div class="md-preview" id="preview_next_step"></div>
    </div>

    <!-- Scorecard -->
    <details style="margin-top:12px;">
      <summary style="font-size:14px;font-weight:600;cursor:pointer;">📊 Scorecard</summary>
      <p style="font-size:12px;color:#6b7280;margin:8px 0;">Rate your competency in each area for this day.</p>
      <div class="toggle-grid">{scorecard_html}</div>
    </details>

    <!-- Codex Gates -->
    <details style="margin-top:8px;">
      <summary style="font-size:14px;font-weight:600;cursor:pointer;">🚦 Codex Gates</summary>
      <p style="font-size:12px;color:#6b7280;margin:8px 0;">Mark which Codex gates you have passed.</p>
      <div class="toggle-grid">{gate_html}</div>
    </details>

    <div style="display:flex;gap:8px;margin-top:16px;">
      <button type="submit" class="btn btn-primary">{note_save_label}</button>
      <span style="font-size:12px;color:#6b7280;align-self:center;">
        {f'Last saved: {existing_note_date}' if existing_note_date else 'Not yet saved'}
      </span>
    </div>
  </form>
</div>

<!-- ════════════════ EVIDENCE FOR THIS DAY ════════════════ -->
<div class="card">
  <h2>📎 Evidence for Day {day_number}</h2>

  <!-- Inline upload -->
  <div style="margin-bottom:12px;">
    <div class="upload-zone" onclick="document.getElementById('evidenceUploadInput').click()">
      <div class="icon">📤</div>
      <p>Click to upload a file as evidence for Day {day_number}</p>
      <p style="font-size:11px;color:#9ca3af;">Supported: .md, .txt, .csv, .png, .pdf, .jpg</p>
    </div>
    <input type="file" id="evidenceUploadInput" style="display:none;" accept=".md,.txt,.csv,.png,.pdf,.jpg" onchange="uploadDayEvidence(event, {day_number})">
    <div id="uploadStatus" style="margin-top:6px;font-size:13px;"></div>
  </div>

  <!-- Existing evidence list -->
  <div id="dayEvidenceList">
    {evidence_rows}
  </div>
</div>

<!-- ════════════════ BOTTOM NAV ════════════════ -->
<div style="display:flex;gap:6px;margin-top:12px;flex-wrap:wrap;align-items:center;">
  {prev_link}
  {next_link}
  <span style="flex:1;"></span>
  <a href="/curriculum" class="btn btn-outline">← Back to All Days</a>
</div>

<script>
// ── Markdown renderer ──────────────────────────────────────────
function renderMarkdown(text) {{
  if (!text) return '';
  var html = text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>')
    .replace(/\\*(.+?)\\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/^\\d+\\. (.+)$/gm, '<li>$1</li>')
    .replace(/\\[(.+?)\\]\\((.+?)\\)/g, '<a href="$2" target="_blank">$1</a>')
    .replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>');
  html = html.replace(/((?:<li>.*?<\\/li>\\n?)+)/g, '<ul>$1</ul>');
  html = html.replace(/((?:<blockquote>.*?<\\/blockquote>\\n?)+)/g, '<blockquote>$1</blockquote>');
  html = html.replace(/\\n\\n/g, '<\\/p><p>');
  html = '<p>' + html + '<\\/p>';
  html = html.replace(/<p><\\/p>/g, '');
  return html;
}}

// ── Markdown preview toggle ────────────────────────────────────
function togglePreview(btn, fieldName) {{
  var ta = document.getElementsByName(fieldName)[0];
  if (!ta) return;
  var preview = document.getElementById('preview_' + fieldName);
  if (!preview) return;
  if (preview.classList.contains('visible')) {{
    preview.classList.remove('visible');
    preview.innerHTML = '';
    btn.textContent = '👁️ Preview';
    ta.style.display = '';
  }} else {{
    preview.innerHTML = renderMarkdown(ta.value);
    preview.classList.add('visible');
    ta.style.display = 'none';
    btn.textContent = '✏️ Edit';
  }}
}}

// ── Auto-resize textareas ──────────────────────────────────────
function autoResize(el) {{
  el.style.height = 'auto';
  el.style.height = Math.max(80, el.scrollHeight) + 'px';
}}

// ── Requirement checklist toggle ───────────────────────────────
function toggleReq(li) {{
  var cb = li.querySelector('input[type="checkbox"]');
  if (cb) {{
    cb.checked = !cb.checked;
    li.classList.toggle('checked', cb.checked);
  }}
}}

// ── Template fill for markdown artifacts ───────────────────────
function useTemplate(filename, dayNum) {{
  var ext = filename.split('.').pop().toLowerCase();
  var templates = {{
    'md': function(name) {{
      var title = name.replace(/\\.md$/i, '').replace(/_/g, ' ').replace(/\\b\\w/g, function(c){{return c.toUpperCase();}});
      return '# ' + title + '\\n\\n## Purpose\\n\\n<!-- Briefly describe the purpose of this artifact -->\\n\\n## Details\\n\\n<!-- Add your work details here -->\\n\\n## Checklist\\n\\n- [ ] Item 1\\n- [ ] Item 2\\n- [ ] Item 3\\n\\n## Notes\\n\\n<!-- Any additional notes -->\\n';
    }}
  }};
  var tplFn = templates[ext];
  if (!tplFn) {{ showToast('No template available for ' + ext, 'error'); return; }}
  var content = tplFn(filename);
  fetch('/api/evidence', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{filename: filename, content: content, day_number: dayNum}})
  }})
  .then(function(r) {{ return r.json(); }})
  .then(function(r) {{
    if (r.status === 'ok') {{
      showToast('✅ Template created! Edit it in evidence.', 'success');
      setTimeout(function() {{ location.reload(); }}, 800);
    }} else {{
      showToast('❌ ' + r.message, 'error');
    }}
  }})
  .catch(function(e) {{ showToast('❌ ' + e, 'error'); }});
}}

// ── Screenshot guide ───────────────────────────────────────────
function showScreenshotGuide() {{
  showToast('📸 Take a screenshot, then upload it using the Upload button above.', 'success');
  var guide = document.getElementById('uploadStatus');
  if (guide) {{
    guide.innerHTML = '<div style="background:#f0fdf4;padding:10px 14px;border-radius:6px;font-size:13px;line-height:1.6;">' +
      '<strong>📸 Screenshot Tips:</strong><br>' +
      '• Capture the full relevant area (use Snipping Tool or Win+Shift+S)<br>' +
      '• Name your file matching the required artifact name<br>' +
      '• Accepted formats: .png, .jpg<br>' +
      '• Recommended: annotate key areas before uploading</div>';
  }}
}}

// ── Save day note ──────────────────────────────────────────────
function saveDayNote(event, dayNum) {{
  event.preventDefault();
  var form = document.getElementById('dayNoteForm');
  var data = {{}};
  for (var i = 0; i < form.elements.length; i++) {{
    var el = form.elements[i];
    if (el.name) {{
      if (el.name.startsWith('scorecard_')) {{
        if (!data.scorecard) data.scorecard = {{}};
        data.scorecard[el.name.replace('scorecard_', '')] = el.value;
      }} else if (el.name.startsWith('codexgate_')) {{
        if (!data.codex_gate) data.codex_gate = {{}};
        data.codex_gate[el.name.replace('codexgate_', '')] = el.value;
      }} else {{
        data[el.name] = el.value;
      }}
    }}
  }}
  fetch('/api/notes', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify(data)
  }})
  .then(function(r) {{ return r.json(); }})
  .then(function(r) {{
    if (r.status === 'ok') {{
      showToast('✅ Note saved!', 'success');
      setTimeout(function() {{ location.href = '/day/' + dayNum; }}, 800);
    }} else {{
      showToast('❌ ' + r.message, 'error');
    }}
  }})
  .catch(function(e) {{ showToast('❌ Network error: ' + e, 'error'); }});
  return false;
}}

// ── Upload day evidence ────────────────────────────────────────
function uploadDayEvidence(event, dayNum) {{
  var input = event.target;
  if (!input.files || !input.files[0]) return;
  var file = input.files[0];
  var ext = file.name.split('.').pop().toLowerCase();
  var textExts = {{'md':1,'txt':1,'csv':1,'json':1,'yaml':1,'yml':1,'toml':1,'ini':1,'cfg':1,'log':1,'sql':1,'py':1,'js':1,'ts':1,'html':1,'css':1,'xml':1,'svg':1}};
  var statusDiv = document.getElementById('uploadStatus');
  statusDiv.innerHTML = '<span style="color:#6b7280;">Uploading ' + file.name + '...</span>';

  function doUpload(content, isBase64) {{
    var payload = {{filename: file.name, day_number: dayNum}};
    if (isBase64) {{
      payload.content_base64 = content;
      fetch('/api/evidence/binary', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify(payload)
      }})
      .then(function(r) {{ return r.json(); }})
      .then(function(r) {{
        if (r.status === 'ok') {{
          showToast('✅ ' + file.name + ' uploaded!', 'success');
          setTimeout(function() {{ location.reload(); }}, 800);
        }} else {{
          statusDiv.innerHTML = '<span style="color:#dc2626;">❌ ' + r.message + '</span>';
        }}
      }})
      .catch(function(e) {{ statusDiv.innerHTML = '<span style="color:#dc2626;">❌ ' + e + '</span>'; }});
    }} else {{
      payload.content = content;
      fetch('/api/evidence', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify(payload)
      }})
      .then(function(r) {{ return r.json(); }})
      .then(function(r) {{
        if (r.status === 'ok') {{
          showToast('✅ ' + file.name + ' uploaded!', 'success');
          setTimeout(function() {{ location.reload(); }}, 800);
        }} else {{
          statusDiv.innerHTML = '<span style="color:#dc2626;">❌ ' + r.message + '</span>';
        }}
      }})
      .catch(function(e) {{ statusDiv.innerHTML = '<span style="color:#dc2626;">❌ ' + e + '</span>'; }});
    }}
  }}

  if (textExts[ext]) {{
    var reader = new FileReader();
    reader.onload = function(e) {{ doUpload(e.target.result, false); }};
    reader.readAsText(file);
  }} else {{
    var reader = new FileReader();
    reader.onload = function(e) {{
      var base64 = e.target.result.split(',')[1];
      doUpload(base64, true);
    }};
    reader.readAsDataURL(file);
  }}
}}

// ── Delete evidence ────────────────────────────────────────────
function deleteEvidenceDay(dayNum, filename) {{
  if (!confirm('Delete ' + filename + '?')) return;
  fetch('/api/evidence/' + encodeURIComponent(filename), {{method: 'DELETE'}})
  .then(function(r) {{ return r.json(); }})
  .then(function(r) {{
    if (r.status === 'ok') {{
      showToast('🗑️ Deleted', 'success');
      setTimeout(function() {{ location.reload(); }}, 800);
    }} else {{
      showToast('❌ ' + r.message, 'error');
    }}
  }})
  .catch(function(e) {{ showToast('❌ ' + e, 'error'); }});
}}

// ── Auto-resize all textareas on load ──────────────────────────
document.addEventListener('DOMContentLoaded', function() {{
  var tas = document.querySelectorAll('textarea.note-field');
  for (var i = 0; i < tas.length; i++) {{ autoResize(tas[i]); }}
}});
</script>
'''
    return _html_page(f'Day {day_number}', body, 'curriculum')


def _page_note_editor(day_number: int = 1, note_data: dict = None, existing_date: str = None) -> str:
    """Render the daily note editor form."""
    entry = CURRICULUM.get(day_number, {})
    classification = get_classification(day_number)
    primary_track = get_primary_track(day_number)
    level = get_level_for_day(day_number)
    week_num = (day_number - 1) // 7 + 1
    focus = entry.get('focus', '')
    required_artifact = entry.get('required_artifact', '')
    tags = entry.get('tags', [])
    tag_str = ' · '.join(tags)

    today_str = existing_date or date.today().isoformat()

    # Scorecard toggles
    scorecard_areas = _learner.get_scorecard_areas()
    scorecard_html = ''
    for area in scorecard_areas:
        val = note_data.get('scorecard', {}).get(area, 'Unscored') if note_data else 'Unscored'
        scorecard_html += f'''<div class="toggle-item">
  <span>{area}</span>
  <select name="scorecard_{area}">
    <option {"selected" if val=="Pass" else ""}>Pass</option>
    <option {"selected" if val=="Moderate" else ""}>Moderate</option>
    <option {"selected" if val=="Fail" else ""}>Fail</option>
    <option {"selected" if val=="Unscored" else ""}>Unscored</option>
  </select>
</div>'''

    # Codex gate toggles
    codex_gates = _learner.get_codex_gates_list()
    gate_html = ''
    for gate in codex_gates:
        val = note_data.get('codex_gate', {}).get(gate, 'No') if note_data else 'No'
        gate_html += f'''<div class="toggle-item">
  <span>{gate}</span>
  <select name="codexgate_{gate}">
    <option {"selected" if val=="Yes" else ""}>Yes</option>
    <option {"selected" if val=="No" else ""}>No</option>
  </select>
</div>'''

    # Pre-fill form fields from existing note data or curriculum defaults
    wl = note_data.get('what_learned', '') if note_data else ''
    ep = note_data.get('evidence_produced', '') if note_data else ''
    wr = note_data.get('what_remains', '') if note_data else ''
    ns = note_data.get('next_step', '') if note_data else ''

    title = f'✏️ Day {day_number} — {focus}' if not existing_date else f'📝 Note — {existing_date}'
    save_label = 'Update Note' if existing_date else 'Save Note'

    # ── Day navigation ────────────────────────────────────────────
    prev_day = day_number - 1
    next_day = day_number + 1
    prev_link = f'<a href="/day/{prev_day}" class="btn btn-outline btn-sm" style="font-size:13px;">◀ Day {prev_day}</a>' if prev_day >= 1 else '<span class="btn btn-outline btn-sm" style="font-size:13px;opacity:0.4;cursor:default;">◀ Day 1</span>'
    next_link = f'<a href="/day/{next_day}" class="btn btn-outline btn-sm" style="font-size:13px;">Day {next_day} ▶</a>' if next_day <= 28 else '<span class="btn btn-outline btn-sm" style="font-size:13px;opacity:0.4;cursor:default;">Day 28 ▶</span>'
    day_selector_options = ''
    for d in range(1, 29):
        d_entry = CURRICULUM.get(d, {})
        d_focus = (d_entry.get('focus', '') or '')[:40]
        selected = 'selected' if d == day_number else ''
        day_selector_options += f'<option value="{d}" {selected}>Day {d}: {d_focus}</option>'

    day_nav = f'''
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;gap:8px;flex-wrap:wrap;">
  <div style="display:flex;gap:6px;">
    {prev_link}
    {next_link}
  </div>
  <div style="display:flex;gap:6px;align-items:center;">
    <label for="dayJump" style="font-size:12px;color:#6b7280;">Jump to:</label>
    <select id="dayJump" onchange="if(this.value) location.href='/day/'+this.value" style="font-size:13px;padding:4px 8px;border:1px solid #d1d5db;border-radius:4px;">
      {day_selector_options}
    </select>
  </div>
</div>'''

    body = f'''
<h2 style="margin-bottom:16px;">{title}</h2>

{day_nav}

<form id="noteForm" onsubmit="return saveNote(event)">
  <div class="card" style="margin-bottom:16px;">
    <h2>📋 Curriculum Context</h2>
    <div class="form-row">
      <div class="form-group">
        <label>Date</label>
        <input type="date" name="date" value="{today_str}" readonly>
      </div>
      <div class="form-group">
        <label>Day Number</label>
        <input type="number" name="day_number" value="{day_number}" readonly>
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Classification</label>
        <select name="classification">
          <option {"selected" if classification=="Foundational" else ""}>Foundational</option>
          <option {"selected" if classification=="Developing" else ""}>Developing</option>
          <option {"selected" if classification=="Operational" else ""}>Operational</option>
          <option {"selected" if classification=="Ready For Codex Acceleration" else ""}>Ready For Codex Acceleration</option>
        </select>
      </div>
      <div class="form-group">
        <label>Primary Track</label>
        <select name="primary_track">
          <option {"selected" if primary_track=="Pyramid operations" else ""}>Pyramid operations</option>
          <option {"selected" if primary_track=="Codex productivity" else ""}>Codex productivity</option>
          <option {"selected" if primary_track=="BI judgment" else ""}>BI judgment</option>
        </select>
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Level</label>
        <select name="level">
          <option {"selected" if level==1 else ""}>1</option>
          <option {"selected" if level==2 else ""}>2</option>
          <option {"selected" if level==3 else ""}>3</option>
          <option {"selected" if level==4 else ""}>4</option>
        </select>
      </div>
      <div class="form-group">
        <label>Week Number</label>
        <input type="number" name="week_number" value="{week_num}" readonly>
      </div>
    </div>
    <div class="form-group">
      <label>Required Artifact</label>
      <input type="text" name="required_artifact" value="{required_artifact}" readonly>
    </div>
    <div class="form-group">
      <label>Category Tags</label>
      <input type="text" value="{tag_str}" readonly style="color:#6b7280;">
    </div>
  </div>

  <div class="card" style="margin-bottom:16px;">
    <h2>📝 Daily Reflection</h2>
    <div class="form-group">
      <label>What I learned today</label>
      <textarea class="note-field" name="what_learned" placeholder="Describe what you learned today...">{wl}</textarea>
    </div>
    <div class="form-group">
      <label>What evidence I produced</label>
      <textarea class="note-field" name="evidence_produced" placeholder="Describe the evidence you produced...">{ep}</textarea>
    </div>
    <div class="form-group">
      <label>What remains open</label>
      <textarea class="note-field" name="what_remains" placeholder="What is still unresolved?">{wr}</textarea>
    </div>
    <div class="form-group">
      <label>Next narrow step</label>
      <textarea class="note-field" name="next_step" placeholder="What is your immediate next action?">{ns}</textarea>
    </div>
  </div>

  <div class="card" style="margin-bottom:16px;">
    <h2>📊 Scorecard</h2>
    <p style="font-size:13px;color:#6b7280;margin-bottom:8px;">Rate your competency in each area for this day.</p>
    <div class="toggle-grid">{scorecard_html}</div>
  </div>

  <div class="card" style="margin-bottom:16px;">
    <h2>🚦 Codex Gates</h2>
    <p style="font-size:13px;color:#6b7280;margin-bottom:8px;">Mark which Codex gates you have passed.</p>
    <div class="toggle-grid">{gate_html}</div>
  </div>

  <div style="display:flex;gap:8px;margin-top:16px;">
    <button type="submit" class="btn btn-primary">{save_label}</button>
    <a href="/notes" class="btn btn-outline">Cancel</a>
  </div>
</form>

<script>
function saveNote(event) {{
  event.preventDefault();
  var form = document.getElementById('noteForm');
  var data = {{}};
  for (var i = 0; i < form.elements.length; i++) {{
    var el = form.elements[i];
    if (el.name) {{
      if (el.name.startsWith('scorecard_')) {{
        if (!data.scorecard) data.scorecard = {{}};
        data.scorecard[el.name.replace('scorecard_', '')] = el.value;
      }} else if (el.name.startsWith('codexgate_')) {{
        if (!data.codex_gate) data.codex_gate = {{}};
        data.codex_gate[el.name.replace('codexgate_', '')] = el.value;
      }} else {{
        data[el.name] = el.value;
      }}
    }}
  }}
  fetch('/api/notes', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify(data)
  }})
  .then(function(r) {{ return r.json(); }})
  .then(function(r) {{
    if (r.status === 'ok') {{
      showToast('✅ Note saved! Dashboard updating...', 'success');
      setTimeout(function() {{ window.location.href = '/notes/' + r.date; }}, 1000);
    }} else {{
      showToast('❌ ' + r.message, 'error');
    }}
  }})
  .catch(function(e) {{ showToast('❌ Network error: ' + e, 'error'); }});
  return false;
}}
</script>
'''
    return _html_page(f'Day {day_number}', body, 'notes')


def _page_note_list() -> str:
    """Render the list of all notes."""
    notes = _learner.list_notes()
    if not notes:
        body = '''
<h2 style="margin-bottom:16px;">📝 All Notes</h2>
<div class="card">
  <p style="color:#6b7280;text-align:center;padding:20px;">No notes yet. Write your first note!</p>
  <div style="text-align:center;margin-top:8px;">
    <a href="/notes/new?day=1" class="btn btn-primary">✏️ Write Day 1 Note</a>
  </div>
</div>'''
        return _html_page('Notes', body, 'notes')

    items = []
    for n in reversed(notes):
        day = _learner._extract_day_from_note(n)
        day_str = f'Day {day}' if day else ''
        items.append(f'''<div class="note-list-item">
  <div>
    <div class="note-date">{n.stem}</div>
    <div class="note-day">{day_str}</div>
  </div>
  <div class="note-actions">
    <a href="/notes/{n.stem}" class="btn btn-outline btn-sm">View</a>
    <a href="/notes/new?day={day if day else 1}&date={n.stem}" class="btn btn-outline btn-sm">Edit</a>
  </div>
</div>''')

    body = f'''
<h2 style="margin-bottom:16px;">📝 All Notes ({len(notes)})</h2>
<div class="card">
{''.join(items)}
</div>
<div style="margin-top:12px;">
  <a href="/notes/new?day=1" class="btn btn-primary">✏️ New Note</a>
</div>'''
    return _html_page('Notes', body, 'notes')


def _page_note_view(date_str: str) -> str:
    """Render a single note for viewing/editing."""
    # Sanitize date_str to prevent path traversal
    from urllib.parse import unquote
    date_str = unquote(date_str)
    # Only allow date-like filenames (YYYY-MM-DD)
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return _html_page('Invalid', '<div class="card"><h2>❌ Invalid date</h2><a href="/notes">← Back</a></div>', 'notes')
    note_path = _learner.notes_dir / f'{date_str}.md'
    if not note_path.exists():
        return _html_page('Not Found', '<div class="card"><h2>❌ Note not found</h2><p style="color:#6b7280;">No note for {date_str}.</p><a href="/notes" class="btn btn-outline" style="margin-top:12px;">← Back to Notes</a></div>', 'notes')

    content = note_path.read_text(encoding='utf-8')

    # Parse note to extract structured fields (mirrors build_data.py parse_note logic)
    def _extract(field):
        m = re.search(rf'\*\*{field}:\*\*\s*(.*?)(?:\n|$)', content)
        return m.group(1).strip() if m else ''

    def _extract_section(heading):
        pattern = rf'## {heading}:\s*\n(.*?)(?:\n## |\Z)'
        m = re.search(pattern, content, re.DOTALL)
        return m.group(1).strip() if m else ''

    day_str = _extract('Day')  # "Day 3" → "3"
    day_match = re.search(r'Day\s*(\d+)', day_str)
    day_num = int(day_match.group(1)) if day_match else 1

    # Load revision history
    revisions = get_revision_history(note_path)
    rev_html = ''
    if revisions:
        rev_items = ''
        for rev in reversed(revisions):
            rev_time = rev.get('timestamp', '')
            rev_path = rev.get('revision_path', '')
            rev_label = rev_time.replace('T', ' ')[:16] if rev_time else 'unknown'
            from urllib.parse import quote as _url_quote
            rev_url_path = _url_quote(rev_path, safe='/:')
            rev_items += f'<li style="margin:4px 0;"><a href="/notes/revision?path={rev_url_path}" style="color:#7c73ff;font-size:12px;">📄 {rev_label}</a></li>'
        rev_html = f'''
<div class="card" style="margin-top:12px;">
  <h4 style="margin:0 0 8px 0;font-size:14px;">📜 Revision History ({len(revisions)})</h4>
  <ul style="margin:0;padding-left:16px;">{rev_items}</ul>
</div>'''

    body = f'''
<h2 style="margin-bottom:16px;">📝 Note — {date_str}</h2>

<div class="card" style="margin-bottom:16px;">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:12px;">
    <div>
      <strong>{_extract('Classification')}</strong> ·
      {_extract('Primary track')} ·
      Level {_extract('Level')} ·
      {_extract('Week Number')}
    </div>
    <a href="/day/{day_num}" class="btn btn-outline btn-sm">📖 Day {day_num}</a>
  </div>
  <div style="font-family:var(--font-mono);font-size:13px;background:#f9fafb;padding:16px;border-radius:6px;white-space:pre-wrap;line-height:1.5;">{content}</div>
</div>

{rev_html}

<div style="display:flex;gap:8px;">
  <a href="/notes" class="btn btn-outline">← Back to Notes</a>
  <a href="/day/{day_num}" class="btn btn-primary">📖 Open Day {day_num} Workspace</a>
</div>'''
    return _html_page(f'Note {date_str}', body, 'notes')


def _page_revision_view(rev_path: str) -> str:
    """Render a historical revision for viewing."""
    try:
        from pathlib import Path as _Path
        from urllib.parse import unquote as _url_unquote
        rev_path = _url_unquote(rev_path)
        p = _Path(rev_path)
        # Ensure revision is within the archive directory
        archive_dir = (ACTION_DIR / 'archive').resolve()
        if not str(p.resolve()).startswith(str(archive_dir)):
            return _html_page('Forbidden',
                              '<div class="card"><h2>❌ Access denied</h2><a href="/notes">← Back</a></div>',
                              'notes')
        if not p.exists():
            return _html_page('Revision Not Found',
                              '<div class="card"><h2>❌ Revision not found</h2><p style="color:#6b7280;">The revision file no longer exists.</p><a href="/notes" class="btn btn-outline">← Back to Notes</a></div>',
                              'notes')
        content = p.read_text(encoding='utf-8')
        # Try to extract parent note date from filename
        parent_date = p.stem.split('_v')[0] if '_v' in p.stem else ''
        back_link = f'/notes/{parent_date}' if parent_date else '/notes'
        body = f'''
<h2 style="margin-bottom:16px;">📜 Revision: {p.name}</h2>
<div style="color:#6b7280;font-size:13px;margin-bottom:12px;">
  Restored from <code>{p.name}</code>
</div>
<div class="card" style="margin-bottom:16px;">
  <div style="font-family:var(--font-mono);font-size:13px;background:#f9fafb;padding:16px;border-radius:6px;white-space:pre-wrap;line-height:1.5;">{content}</div>
</div>
<a href="{back_link}" class="btn btn-outline">← Back to Note</a>'''
        return _html_page(f'Revision: {p.name}', body, 'notes')
    except Exception as e:
        return _html_page('Error', f'<div class="card"><h2>❌ Error</h2><p>{e}</p><a href="/notes" class="btn btn-outline">← Back to Notes</a></div>', 'notes')


# ═══════════════════════════════════════════════════════════════════════════
# Phase 3: Evidence Page Handlers
# ═══════════════════════════════════════════════════════════════════════════


def _extract_pt_id(filename: str) -> str:
    """Extract proof task ID from a filename, e.g. 'PT1_Day9_analysis.md' → 'PT1'."""
    for pt_id in PROOF_TASKS:
        if filename.upper().startswith(pt_id.upper()):
            return pt_id
    return ''


def _extract_day_from_filename(filename: str) -> int:
    """Extract day number from a filename, e.g. 'PT1_Day9_analysis.md' → 9."""
    m = re.search(r'[Dd]ay[ _]?(\d+)', filename)
    return int(m.group(1)) if m else 0


def _evidence_list_data() -> list[dict]:
    """Return structured list of evidence files."""
    items = []
    for f in sorted(_learner.evidence_dir.glob('*.*'), reverse=True):
        if f.name == '.gitkeep':
            continue
        pt_id = _extract_pt_id(f.name)
        day_num = _extract_day_from_filename(f.name)
        size_kb = round(f.stat().st_size / 1024, 1) if f.stat().st_size else 0
        items.append({
            'filename': f.name,
            'pt_id': pt_id,
            'pt_name': PROOF_TASKS.get(pt_id, {}).get('name', '') if pt_id else '',
            'day': day_num,
            'size_kb': size_kb,
            'path': str(f),
        })
    return items


def _page_evidence_list() -> str:
    """Render the evidence manager page."""
    items = _evidence_list_data()

    # Template quick-create buttons
    pt_buttons = ''
    for pt_id in sorted(PROOF_TASKS):
        pt = PROOF_TASKS[pt_id]
        due_day = pt['due_day']
        pt_buttons += f'''
<a href="/evidence/new?pt={pt_id}&day={due_day}" class="btn btn-outline btn-sm">{pt_id}: {pt['name']}</a>'''

    if not items:
        list_html = '''
<div class="card">
  <p style="color:#6b7280;text-align:center;padding:20px;">No evidence files yet. Create one from a template or upload a file.</p>
</div>'''
    else:
        rows = []
        for it in items:
            pt_badge = f'<span style="font-size:11px;padding:2px 6px;background:#f0f5ff;color:#3b82f6;border-radius:4px;">{it["pt_id"]}</span>' if it['pt_id'] else ''
            day_label = f'Day {it["day"]}' if it['day'] else ''
            rows.append(f'''<div class="note-list-item">
  <div>
    <div class="note-date">{it['filename']}</div>
    <div style="font-size:12px;color:#6b7280;display:flex;gap:6px;align-items:center;margin-top:2px;">
      {pt_badge}{day_label}<span>{it['size_kb']} KB</span>
    </div>
  </div>
  <div class="note-actions">
    <a href="/evidence/{it['filename']}" class="btn btn-outline btn-sm">View</a>
    <a href="/evidence/{it['filename']}?edit=1" class="btn btn-outline btn-sm">Edit</a>
    <button class="btn btn-outline btn-sm" onclick="deleteEvidence('{it['filename']}')">🗑️</button>
  </div>
</div>''')
        list_html = f'<div class="card">{"".join(rows)}</div>'

    body = f'''
<h2 style="margin-bottom:16px;">📎 Evidence Manager</h2>

<div class="card" style="margin-bottom:16px;">
  <h2>Create from Proof Task Template</h2>
  <p style="font-size:13px;color:#6b7280;margin-bottom:8px;">Choose a proof task to open its template with the required sections pre-filled.</p>
  <div style="display:flex;gap:6px;flex-wrap:wrap;">
    {pt_buttons}
  </div>
</div>

<div class="card" style="margin-bottom:16px;">
  <h2>Upload Evidence File</h2>
  <p style="font-size:13px;color:#6b7280;margin-bottom:8px;">Upload a .md, .txt, .csv, .png, or .pdf file to action/evidence/.</p>
  <form id="uploadForm" onsubmit="return uploadEvidence(event)" enctype="multipart/form-data">
    <div style="display:flex;gap:8px;align-items:center;">
      <input type="file" name="file" id="fileInput" style="flex:1;" accept=".md,.txt,.csv,.png,.pdf,.jpg">
      <button type="submit" class="btn btn-primary">Upload</button>
    </div>
  </form>
  <div id="uploadStatus" style="margin-top:8px;font-size:13px;"></div>
</div>

<div class="card" style="margin-bottom:16px;">
  <h2>📁 Upload Folder as Evidence</h2>
  <p style="font-size:13px;color:#6b7280;margin-bottom:8px;">Select a folder to upload all supported files as individual evidence items (recursive to 1 level).</p>
  <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
    <input type="file" name="folder" id="folderInput" style="flex:1;" webkitdirectory multiple>
    <button type="button" class="btn btn-primary" onclick="uploadFolder()">Upload Folder</button>
  </div>
  <div id="folderUploadProgress" style="margin-top:8px;font-size:13px;"></div>
</div>

<h2 style="margin-bottom:12px;">Saved Evidence ({len(items)})</h2>
{list_html}

<script>
function uploadEvidence(event) {{
  event.preventDefault();
  var input = document.getElementById('fileInput');
  if (!input.files || !input.files[0]) {{ showToast('Please select a file', 'error'); return; }}
  var file = input.files[0];
  var reader = new FileReader();
  reader.onload = function(e) {{
    var content = e.target.result;
    var filename = file.name;
    fetch('/api/evidence', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{filename: filename, content: content, day_number: 0}})
    }})
    .then(function(r) {{ return r.json(); }})
    .then(function(r) {{
      if (r.status === 'ok') {{
        showToast('✅ ' + filename + ' uploaded!', 'success');
        setTimeout(function() {{ location.reload(); }}, 1000);
      }} else {{
        showToast('❌ ' + r.message, 'error');
      }}
    }})
    .catch(function(e) {{ showToast('❌ ' + e, 'error'); }});
  }};
  reader.readAsText(file);
  return false;
}}

function uploadFolder() {{
  var input = document.getElementById('folderInput');
  if (!input.files || input.files.length === 0) {{ showToast('Please select a folder', 'error'); return; }}
  var files = Array.from(input.files);
  var total = files.length;
  var done = 0;
  var failed = 0;
  var progressDiv = document.getElementById('folderUploadProgress');
  progressDiv.innerHTML = '<div style="color:#6b7280;">Preparing ' + total + ' file(s)...</div>';

  function uploadNext(index) {{
    if (index >= files.length) {{
      var msg = '✅ Uploaded ' + done + '/' + total + ' files' + (failed > 0 ? ' (' + failed + ' failed)' : '');
      progressDiv.innerHTML = '<div style="color:' + (failed === 0 ? '#059669' : '#dc2626') + ';">' + msg + '</div>';
      if (done > 0) setTimeout(function() {{ location.reload(); }}, 1500);
      return;
    }}
    var file = files[index];
    // Skip hidden files and unsupported binary types
    var ext = file.name.split('.').pop().toLowerCase();
    var textExts = {{'md':1,'txt':1,'csv':1,'json':1,'yaml':1,'yml':1,'toml':1,'ini':1,'cfg':1,'log':1,'sql':1,'py':1,'js':1,'ts':1,'html':1,'css':1,'xml':1,'svg':1,'env':1,'gitignore':1,'dockerfile':1}};
    if (file.name.startsWith('.')) {{ uploadNext(index + 1); return; }}

    progressDiv.innerHTML = '<div style="color:#6b7280;">[' + (index+1) + '/' + total + '] Uploading ' + file.name + '...</div>';

    if (textExts[ext]) {{
      // Read as text and POST via JSON
      var reader = new FileReader();
      reader.onload = function(e) {{
        fetch('/api/evidence', {{
          method: 'POST',
          headers: {{'Content-Type': 'application/json'}},
          body: JSON.stringify({{filename: file.name, content: e.target.result, day_number: 0}})
        }})
        .then(function(r) {{ return r.json(); }})
        .then(function(r) {{
          if (r.status === 'ok') {{ done++; }} else {{ failed++; }}
          uploadNext(index + 1);
        }})
        .catch(function() {{ failed++; uploadNext(index + 1); }});
      }};
      reader.readAsText(file);
    }} else {{
      // Binary file — read as base64 and use binary upload endpoint
      var reader = new FileReader();
      reader.onload = function(e) {{
        var base64 = e.target.result.split(',')[1];
        fetch('/api/evidence/binary', {{
          method: 'POST',
          headers: {{'Content-Type': 'application/json'}},
          body: JSON.stringify({{filename: file.name, content_base64: base64, day_number: 0}})
        }})
        .then(function(r) {{ return r.json(); }})
        .then(function(r) {{
          if (r.status === 'ok') {{ done++; }} else {{ failed++; }}
          uploadNext(index + 1);
        }})
        .catch(function() {{ failed++; uploadNext(index + 1); }});
      }};
      reader.readAsDataURL(file);
    }}
  }}

  uploadNext(0);
}}

function deleteEvidence(filename) {{
  if (!confirm('Delete ' + filename + '?')) return;
  fetch('/api/evidence/' + encodeURIComponent(filename), {{method: 'DELETE'}})
  .then(function(r) {{ return r.json(); }})
  .then(function(r) {{
    if (r.status === 'ok') {{
      showToast('🗑️ Deleted ' + filename, 'success');
      setTimeout(function() {{ location.reload(); }}, 1000);
    }} else {{
      showToast('❌ ' + r.message, 'error');
    }}
  }})
  .catch(function(e) {{ showToast('❌ ' + e, 'error'); }});
}}
</script>
'''
    return _html_page('Evidence Manager', body, 'evidence')


def _page_evidence_new(pt_id: str, day_number: int) -> str:
    """Render a proof task template form for creating new evidence."""
    pt = PROOF_TASKS.get(pt_id)
    criteria = PROOF_TASK_CRITERIA.get(pt_id)
    if not pt or not criteria:
        return _html_page('Not Found', '<div class="card"><h2>❌ Unknown proof task</h2><a href="/evidence" class="btn btn-outline">← Back</a></div>', 'evidence')

    sections = criteria.get('required_sections', [])
    min_len = criteria.get('min_content_length', 0)
    quality_checks = criteria.get('quality_checks', [])

    # Build section textarea fields
    section_fields = ''
    for i, sec in enumerate(sections):
        safe_id = sec.lower().replace(' ', '_').replace('&', 'and')
        section_fields += f'''<div class="form-group">
  <label>{i+1}. {sec}</label>
  <textarea class="note-field" name="section_{safe_id}" placeholder="Describe {sec.lower()}..." oninput="updateCharCount()"></textarea>
</div>'''

    # Build quality check list
    qc_html = ''.join(f'<li style="font-size:13px;color:#6b7280;">☐ {qc}</li>' for qc in quality_checks)

    suggested_filename = f'{pt_id}_Day{day_number}_{pt["name"].lower().replace(" ", "_")}.md'

    body = f'''
<h2 style="margin-bottom:16px;">📎 {pt_id}: {pt['name']}</h2>

<form id="evidenceForm" onsubmit="return saveEvidence(event)">
  <div class="card" style="margin-bottom:16px;">
    <h2>📋 Details</h2>
    <div class="form-row">
      <div class="form-group">
        <label>Proof Task</label>
        <input type="text" value="{pt_id} — {pt['name']}" readonly>
      </div>
      <div class="form-group">
        <label>Due Day</label>
        <input type="text" value="Day {pt['due_day']} (Week {pt['week']})" readonly>
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Day Number</label>
        <input type="number" name="day_number" value="{day_number}">
      </div>
      <div class="form-group">
        <label>Filename</label>
        <input type="text" name="filename" value="{suggested_filename}">
      </div>
    </div>
  </div>

  <div class="card" style="margin-bottom:16px;">
    <h2>📝 Required Sections</h2>
    <p style="font-size:13px;color:#6b7280;margin-bottom:8px;">Minimum content length: <strong>{min_len} characters</strong> <span id="charCount" style="color:#6b7280;">(0 so far)</span></p>
    {section_fields}
  </div>

  <div class="card" style="margin-bottom:16px;">
    <h2>✅ Quality Checklist</h2>
    <ul style="padding-left:20px;">{qc_html}</ul>
  </div>

  <div style="display:flex;gap:8px;">
    <button type="submit" class="btn btn-primary">💾 Save Evidence</button>
    <a href="/evidence" class="btn btn-outline">Cancel</a>
  </div>
</form>

<script>
function updateCharCount() {{
  var total = 0;
  var ta = document.querySelectorAll('textarea[name^="section_"]');
  for (var i = 0; i < ta.length; i++) total += ta[i].value.length;
  document.getElementById('charCount').textContent = '(' + total + ' so far' + (total >= {min_len} ? ' ✅' : '') + ')';
}}

function saveEvidence(event) {{
  event.preventDefault();
  var form = document.getElementById('evidenceForm');
  var data = {{}};
  var sections = {{}};
  for (var i = 0; i < form.elements.length; i++) {{
    var el = form.elements[i];
    if (!el.name) continue;
    if (el.name.startsWith('section_')) {{
      var heading = el.name.replace('section_', '').replace(/_/g, ' ').replace(/\\b\\w/g, function(c){{return c.toUpperCase();}});
      sections[heading] = el.value;
    }} else {{
      data[el.name] = el.value;
    }}
  }}
  data.pt_id = '{pt_id}';
  data.sections = sections;
  fetch('/api/evidence', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify(data)
  }})
  .then(function(r) {{ return r.json(); }})
  .then(function(r) {{
    if (r.status === 'ok') {{
      showToast('✅ Evidence saved!', 'success');
      setTimeout(function() {{ window.location.href = '/evidence/' + encodeURIComponent(r.filename); }}, 1000);
    }} else {{
      showToast('❌ ' + r.message, 'error');
    }}
  }})
  .catch(function(e) {{ showToast('❌ ' + e, 'error'); }});
  return false;
}}

// Initial char count
updateCharCount();
</script>
'''
    return _html_page(f'{pt_id}: {pt["name"]}', body, 'evidence')


def _page_evidence_view(filename: str, edit_mode: bool = False) -> str:
    """Render evidence view/edit/delete page."""
    # URL-decode filename
    from urllib.parse import unquote
    filename = unquote(filename)

    # Path traversal check
    try:
        filename = _safe_filename(filename, _learner.evidence_dir)
    except ValueError:
        return _html_page('Invalid', '<div class="card"><h2>❌ Invalid filename</h2><a href="/evidence">← Back</a></div>', 'evidence')

    file_path = _learner.evidence_dir / filename
    if not file_path.exists():
        return _html_page('Not Found', f'<div class="card"><h2>❌ File not found</h2><p style="color:#6b7280;">{filename}</p><a href="/evidence" class="btn btn-outline" style="margin-top:12px;">← Back to Evidence</a></div>', 'evidence')

    content = file_path.read_text(encoding='utf-8') if file_path.suffix in ('.md', '.txt', '.csv') else '[Binary file — preview not available]'
    pt_id = _extract_pt_id(filename)
    day_num = _extract_day_from_filename(filename)
    pt_name = PROOF_TASKS.get(pt_id, {}).get('name', '') if pt_id else ''

    meta_info = f'{pt_id} — {pt_name}' if pt_id else 'General evidence'
    day_info = f'Day {day_num}' if day_num else ''

    if edit_mode:
        # Inline edit mode
        body = f'''
<h2 style="margin-bottom:16px;">✏️ Edit — {filename}</h2>

<form id="editForm" onsubmit="return saveEdit(event)">
  <div class="card" style="margin-bottom:16px;">
    <div style="font-size:13px;color:#6b7280;margin-bottom:8px;">
      {meta_info} {day_info}
    </div>
    <div class="form-group">
      <label>Filename</label>
      <input type="text" name="filename" value="{filename}">
    </div>
    <div class="form-group">
      <label>Content (markdown)</label>
      <textarea class="note-field" name="content" style="min-height:400px;font-family:var(--font-mono);">{content}</textarea>
    </div>
  </div>
  <div style="display:flex;gap:8px;">
    <button type="submit" class="btn btn-primary">💾 Save Changes</button>
    <a href="/evidence/{filename}" class="btn btn-outline">Cancel</a>
    <span style="flex:1;"></span>
    <button type="button" class="btn btn-outline" onclick="deleteEvidence('{filename}')" style="color:#ef4444;">🗑️ Delete</button>
  </div>
</form>

<script>
function saveEdit(event) {{
  event.preventDefault();
  var form = document.getElementById('editForm');
  var data = {{}};
  for (var i = 0; i < form.elements.length; i++) {{
    var el = form.elements[i];
    if (el.name) data[el.name] = el.value;
  }}
  data.day_number = {day_num};
  fetch('/api/evidence', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify(data)
  }})
  .then(function(r) {{ return r.json(); }})
  .then(function(r) {{
    if (r.status === 'ok') {{
      showToast('✅ Saved!', 'success');
      window.location.href = '/evidence/' + encodeURIComponent(r.filename);
    }} else {{
      showToast('❌ ' + r.message, 'error');
    }}
  }})
  .catch(function(e) {{ showToast('❌ ' + e, 'error'); }});
  return false;
}}

function deleteEvidence(filename) {{
  if (!confirm('Delete ' + filename + '?')) return;
  fetch('/api/evidence/' + encodeURIComponent(filename), {{method: 'DELETE'}})
  .then(function(r) {{ return r.json(); }})
  .then(function(r) {{
    if (r.status === 'ok') {{
      showToast('🗑️ Deleted', 'success');
      window.location.href = '/evidence';
    }} else {{
      showToast('❌ ' + r.message, 'error');
    }}
  }})
  .catch(function(e) {{ showToast('❌ ' + e, 'error'); }});
}}
</script>
'''
    else:
        # View mode
        # Load revision history
        ev_revisions = get_revision_history(file_path)
        ev_rev_html = ''
        if ev_revisions:
            ev_rev_items = ''
            for rev in reversed(ev_revisions):
                rev_time = rev.get('timestamp', '')
                rev_path = rev.get('revision_path', '')
                rev_label = rev_time.replace('T', ' ')[:16] if rev_time else 'unknown'
                from urllib.parse import quote as _url_quote
                rev_url_path = _url_quote(rev_path, safe='/:')
                ev_rev_items += f'<li style="margin:4px 0;"><a href="/evidence/revision?path={rev_url_path}" style="color:#7c73ff;font-size:12px;">📄 {rev_label}</a></li>'
            ev_rev_html = f'''
<div class="card" style="margin-top:12px;">
  <h4 style="margin:0 0 8px 0;font-size:14px;">📜 Revision History ({len(ev_revisions)})</h4>
  <ul style="margin:0;padding-left:16px;">{ev_rev_items}</ul>
</div>'''

        body = f'''
<h2 style="margin-bottom:16px;">📄 {filename}</h2>

<div class="card" style="margin-bottom:16px;">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:12px;">
    <div style="font-size:13px;color:#6b7280;">
      {meta_info} {day_info} · {file_path.stat().st_size:,} bytes
    </div>
    <div style="display:flex;gap:6px;">
      <a href="/evidence/{filename}?edit=1" class="btn btn-outline btn-sm">✏️ Edit</a>
      <button class="btn btn-outline btn-sm" onclick="deleteEvidence('{filename}')" style="color:#ef4444;">🗑️ Delete</button>
    </div>
  </div>
  <div style="font-family:var(--font-mono);font-size:13px;background:#f9fafb;padding:16px;border-radius:6px;white-space:pre-wrap;line-height:1.5;">{content}</div>
</div>

{ev_rev_html}

<div style="display:flex;gap:8px;">
  <a href="/evidence" class="btn btn-outline">← Back to Evidence</a>
  <a href="/evidence/{filename}?edit=1" class="btn btn-primary">✏️ Edit</a>
</div>

<script>
function deleteEvidence(filename) {{
  if (!confirm('Delete ' + filename + '?')) return;
  fetch('/api/evidence/' + encodeURIComponent(filename), {{method: 'DELETE'}})
  .then(function(r) {{ return r.json(); }})
  .then(function(r) {{
    if (r.status === 'ok') {{
      showToast('🗑️ Deleted', 'success');
      window.location.href = '/evidence';
    }} else {{
      showToast('❌ ' + r.message, 'error');
    }}
  }})
  .catch(function(e) {{ showToast('❌ ' + e, 'error'); }});
}}
</script>
'''

    return _html_page(filename, body, 'evidence')


# ═══════════════════════════════════════════════════════════════════════════
# Phase 4: Feedback, Progress, Q&A Page Handlers
# ═══════════════════════════════════════════════════════════════════════════


def _page_feedback_list() -> str:
    """Render the feedback page showing all reviewer feedback on learner artifacts."""
    all_feedback = get_feedback_for_learner()
    unread = get_unread_feedback()
    unread_ids = {f"{fb['artifactId']}::{fb['reviewId']}" for fb in unread}

    if not all_feedback:
        body = '''
<h2 style="margin-bottom:16px;">📬 Feedback</h2>
<div class="card">
  <p style="color:#6b7280;text-align:center;padding:20px;">No feedback yet. Feedback from reviewers will appear here once they review your work.</p>
</div>'''
        return _html_page('Feedback', body, 'feedback')

    # Group by artifact
    by_artifact = {}
    for fb in all_feedback:
        aid = fb['artifactId']
        if aid not in by_artifact:
            by_artifact[aid] = {'artifactId': aid, 'reviews': [], 'is_note': fb['is_note'], 'is_evidence': fb['is_evidence']}
        by_artifact[aid]['reviews'].append(fb)

    rows = []
    for aid, group in by_artifact.items():
        latest = group['reviews'][0]
        has_unread = any(f"{fb['artifactId']}::{fb['reviewId']}" in unread_ids for fb in group['reviews'])
        rating_colors = {'👍 Pass': '#198754', '⚡ Needs Work': '#ffc107', '❌ Rework': '#dc3545'}
        rating_color = rating_colors.get(latest['rating'], '#6b7280')
        artifact_type = '📝 Note' if group['is_note'] else ('📎 Evidence' if group['is_evidence'] else '📄 Artifact')
        unread_badge = '<span class="unread-dot" title="Unread feedback"></span>' if has_unread else ''
        reviewer_name = latest['reviewer']['display_name']
        reviewer_color = latest['reviewer'].get('color', '#7c73ff')

        rows.append(f'''<div class="feedback-item {'unread' if has_unread else ''}">
  <div class="feedback-meta">
    <div class="feedback-artifact">
      {unread_badge}
      <strong>{artifact_type}:</strong> {aid}
    </div>
    <div style="font-size:12px;color:#6b7280;">
      <span style="color:{reviewer_color};font-weight:600;">{reviewer_name}</span>
      · <span style="color:{rating_color};font-weight:600;">{latest['rating']}</span>
      · {latest['timestamp'][:10] if latest['timestamp'] else ''}
      · {len(group['reviews'])} review(s)
    </div>
  </div>
  <div class="feedback-preview">{latest['text'][:200]}{'...' if len(latest['text']) > 200 else ''}</div>
  <div class="feedback-actions">
    <a href="/feedback/{aid}" class="btn btn-outline btn-sm">View Details</a>
  </div>
</div>''')

    unread_count = len(unread)
    unread_banner = f'<div class="alert alert-info" style="margin-bottom:16px;">📬 You have <strong>{unread_count}</strong> unread feedback item(s). <a href="#" onclick="markAllSeen()">Mark all as seen</a></div>' if unread_count else ''

    body = f'''
<h2 style="margin-bottom:16px;">📬 Feedback ({len(all_feedback)} total)</h2>
{unread_banner}
<div class="card">
  {"".join(rows)}
</div>

<script>
function markAllSeen() {{
  fetch('/api/feedback/seen', {{method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: '{{}}'}})
  .then(function(r){{return r.json()}})
  .then(function(r){{if(r.status==='ok'){{showToast('✅ All marked as seen','success');setTimeout(function(){{location.reload()}},1000);}}}})
  .catch(function(e){{showToast('❌ '+e,'error')}});
}}
</script>
'''
    return _html_page('Feedback', body, 'feedback')


def _page_feedback_detail(artifact_id: str) -> str:
    """Render detail page for a specific artifact's feedback with Q&A threads."""
    from urllib.parse import unquote
    artifact_id = unquote(artifact_id)
    all_feedback = get_feedback_for_learner()
    artifact_feedback = [fb for fb in all_feedback if fb['artifactId'] == artifact_id]

    if not artifact_feedback:
        return _html_page('Not Found', f'<div class="card"><h2>❌ No feedback found</h2><p>{artifact_id}</p><a href="/feedback" class="btn btn-outline">← Back</a></div>', 'feedback')

    # Mark as seen
    for fb in artifact_feedback:
        mark_seen(fb['artifactId'], fb['reviewId'])

    # Group reviews by reviewId for Q&A
    rating_colors = {'👍 Pass': '#198754', '⚡ Needs Work': '#ffc107', '❌ Rework': '#dc3545'}

    review_cards = []
    for fb in artifact_feedback:
        rc = rating_colors.get(fb['rating'], '#6b7280')
        qa_thread = get_qa_thread(fb['reviewId'])
        reviewer_color = fb['reviewer'].get('color', '#7c73ff')

        # Q&A thread
        qa_html = ''
        for entry in qa_thread:
            author_style = 'font-weight:600;color:#7c73ff;' if entry['author'] == 'learner' else f'font-weight:600;color:{reviewer_color};'
            author_label = 'You' if entry['author'] == 'learner' else fb['reviewer']['display_name']
            qa_html += f'''<div class="qa-entry">
  <div style="display:flex;justify-content:space-between;font-size:12px;">
    <span style="{author_style}">{author_label}</span>
    <span style="color:#6b7280;">{entry['timestamp'][:16].replace('T',' ')}</span>
  </div>
  <div style="margin-top:4px;font-size:13px;">{entry['text']}</div>
</div>'''

        review_cards.append(f'''<div class="card" style="margin-bottom:16px;border-left:4px solid {rc};">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:8px;">
    <div>
      <span style="font-weight:600;color:{reviewer_color};">{fb['reviewer']['display_name']}</span>
      <span style="font-size:12px;color:#6b7280;"> · {fb['reviewer'].get('role', 'Reviewer')}</span>
    </div>
    <div style="display:flex;gap:8px;align-items:center;">
      <span style="background:{rc};color:#fff;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:600;">{fb['rating']}</span>
      <span style="font-size:11px;color:#6b7280;">{fb['timestamp'][:16].replace('T',' ') if fb['timestamp'] else ''}</span>
    </div>
  </div>
  <div style="font-size:14px;line-height:1.6;margin-bottom:12px;white-space:pre-wrap;">{fb['text']}</div>

  <div class="qa-section">
    <h4 style="font-size:13px;color:#333;margin:0 0 8px;">💬 Discussion ({len(qa_thread)})</h4>
    {qa_html if qa_html else '<p style="font-size:12px;color:#6b7280;">No questions yet. Ask a question about this feedback.</p>'}
    <div class="qa-input" style="display:flex;gap:8px;margin-top:8px;">
      <textarea id="qaText_{fb['reviewId']}" placeholder="Ask a question about this feedback..." style="flex:1;padding:8px;border:1px solid #ddd;border-radius:6px;font-size:13px;resize:none;min-height:40px;"></textarea>
      <button class="btn btn-primary btn-sm" onclick="postQA('{fb['reviewId']}','{artifact_id}')">Ask</button>
    </div>
  </div>
</div>''')

    body = f'''
<h2 style="margin-bottom:16px;">📬 Feedback: {artifact_id}</h2>
{"".join(review_cards)}
<div style="display:flex;gap:8px;">
  <a href="/feedback" class="btn btn-outline">← Back to Feedback</a>
</div>

<script>
function postQA(reviewId, artifactId) {{
  var ta = document.getElementById('qaText_' + reviewId);
  var text = ta.value.trim();
  if (!text) {{ showToast('Please enter a question', 'error'); return; }}
  fetch('/api/feedback/qa', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{reviewId: reviewId, artifactId: artifactId, text: text}})
  }})
  .then(function(r){{return r.json()}})
  .then(function(r){{
    if(r.status==='ok'){{showToast('✅ Question posted!','success');ta.value='';setTimeout(function(){{location.reload()}},1000);}}
    else{{showToast('❌ '+r.message,'error');}}
  }})
  .catch(function(e){{showToast('❌ '+e,'error');}});
}}
</script>
'''
    return _html_page(f'Feedback: {artifact_id}', body, 'feedback')


def _page_progress() -> str:
    """Render the level progression page."""
    prog = get_level_progress()
    levels = prog.get('levels', {})
    current_level = prog.get('current_level', 1)
    current_day = prog.get('current_day', 0)
    latest_class = prog.get('latest_classification', '—')
    scorecard = prog.get('scorecard_trend', {})
    codex_gates = prog.get('codex_gate_status', {})
    proof_tasks = prog.get('proof_tasks', {})

    # Level cards
    level_cards = []
    level_labels = {1: ('🌱', 'Foundation'), 2: ('🌿', 'Development'), 3: ('🌳', 'Operational'), 4: ('🏆', 'Mastery')}
    for lvl_num in range(1, 5):
        lvl_info = levels.get(str(lvl_num), {})
        emoji, label = level_labels.get(lvl_num, ('📘', f'Level {lvl_num}'))
        is_current = lvl_num == current_level
        is_unlocked = lvl_info.get('is_unlocked', False) or is_current
        is_completed = lvl_info.get('is_completed', False)
        days_done = lvl_info.get('days_completed', 0)
        days_req = lvl_info.get('days_required', 28)
        gates = lvl_info.get('gates', {})
        blockers = gates.get('blockers', [])

        status_icon = '🔓' if is_unlocked else '🔒'
        if is_completed:
            status_icon = '✅'
        progress_pct = min(round(days_done / max(days_req, 1) * 100), 100)

        # Gate details
        gate_details = gates.get('details', {})
        gate_rows = ''
        for metric, value in gate_details.items():
            gate_rows += f'''<div style="display:flex;justify-content:space-between;font-size:12px;padding:2px 0;">
  <span style="color:#6b7280;">{metric}</span>
  <span>{value}</span>
</div>'''

        # Reviewer confirmation indicator
        reviewer_confirmed = lvl_info.get('reviewer_confirmed', False)
        if lvl_num < 4:  # Only levels 1-3 need reviewer confirmation to advance
            if reviewer_confirmed:
                reviewer_html = '<div style="margin-top:6px;font-size:12px;color:#198754;">👤 Reviewer: ✅ Confirmed</div>'
            elif is_completed:
                reviewer_html = '<div style="margin-top:6px;font-size:12px;color:#ffc107;">👤 Reviewer: ⏳ Awaiting confirmation</div>'
            else:
                reviewer_html = '<div style="margin-top:6px;font-size:12px;color:#6b7280;">👤 Reviewer: ⏳ Pending</div>'
        else:
            reviewer_html = ''  # Mastery doesn't need reviewer confirmation

        blocker_html = ''
        if blockers:
            blocker_html = '<div style="margin-top:8px;font-size:12px;color:#dc3545;">⚠️ ' + '; '.join(blockers[:3]) + '</div>'

        active_class = ' level-active' if is_current else ''
        completed_class = ' level-completed' if is_completed else ''

        level_cards.append(f'''<div class="level-card{active_class}{completed_class}">
  <div class="level-header" style="display:flex;justify-content:space-between;align-items:center;">
    <div>
      <span style="font-size:20px;margin-right:8px;">{emoji}</span>
      <strong>Level {lvl_num}: {label}</strong>
      <span style="font-size:12px;color:#6b7280;margin-left:8px;">{status_icon}</span>
    </div>
    {f'<span style="font-size:12px;background:#19875420;color:#198754;padding:2px 8px;border-radius:4px;">✅ Completed</span>' if is_completed else ''}
  </div>
  <div class="progress-bar" style="margin:8px 0;">
    <div class="fill" style="width:{progress_pct}%;background:{'#198754' if is_completed else ('#7c73ff' if is_current else '#d1d5db')};"></div>
  </div>
  <div style="font-size:12px;color:#6b7280;">{days_done}/{days_req} days ({progress_pct}%)</div>
  {reviewer_html}
  {gate_rows}
  {blocker_html}
</div>''')

    # Scorecard summary
    scorecard_rows = ''
    for area, entries in sorted(scorecard.items()):
        if entries:
            latest_score = entries[-1].get('score', 'Unscored')
            score_color = {'Pass': '#198754', 'Moderate': '#ffc107', 'Fail': '#dc3545', 'Unscored': '#6b7280'}.get(latest_score, '#6b7280')
            scorecard_rows += f'''<div style="display:flex;justify-content:space-between;font-size:13px;padding:6px 0;border-bottom:1px solid #f0f0f0;">
  <span>{area}</span>
  <span style="color:{score_color};font-weight:600;">{latest_score}</span>
</div>'''

    # Codex gates
    gate_rows = ''
    for gate, status in sorted(codex_gates.items()):
        passed = status == 'Yes'
        gate_rows += f'''<div style="display:flex;justify-content:space-between;font-size:13px;padding:6px 0;border-bottom:1px solid #f0f0f0;">
  <span>{gate}</span>
  <span style="color:{'#198754' if passed else '#6b7280'};">{'✅ Passed' if passed else '⏳ Not yet'}</span>
</div>'''

    # Proof tasks
    pt_rows = ''
    for pt, done in sorted(proof_tasks.items()):
        pt_rows += f'''<div style="display:flex;justify-content:space-between;font-size:13px;padding:6px 0;border-bottom:1px solid #f0f0f0;">
  <span>{pt}</span>
  <span style="color:{'#198754' if done else '#6b7280'};">{'✅ Done' if done else '⏳ Pending'}</span>
</div>'''

    body = f'''
<h2 style="margin-bottom:16px;">📊 Progress & Level Progression</h2>

<div class="stats-grid" style="margin-bottom:16px;">
  <div class="stat-card">
    <div class="stat-value">Level {current_level}</div>
    <div class="stat-label">Current Level</div>
  </div>
  <div class="stat-card">
    <div class="stat-value">Day {current_day}</div>
    <div class="stat-label">Current Day</div>
  </div>
  <div class="stat-card">
    <div class="stat-value">{latest_class}</div>
    <div class="stat-label">Classification</div>
  </div>
</div>

<h3 style="margin:16px 0 8px;">🏔️ Levels</h3>
{"".join(level_cards)}

<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px;">
  <div class="card">
    <h3 style="font-size:15px;margin:0 0 8px;">🏆 Scorecard</h3>
    {scorecard_rows if scorecard_rows else '<p style="font-size:13px;color:#6b7280;">No scorecard data yet.</p>'}
  </div>
  <div class="card">
    <h3 style="font-size:15px;margin:0 0 8px;">🚪 Codex Gates</h3>
    {gate_rows if gate_rows else '<p style="font-size:13px;color:#6b7280;">No gate data yet.</p>'}
  </div>
</div>

<div class="card" style="margin-top:16px;">
  <h3 style="font-size:15px;margin:0 0 8px;">✅ Proof Tasks</h3>
  {pt_rows if pt_rows else '<p style="font-size:13px;color:#6b7280;">No proof task data yet.</p>'}
</div>
'''
    return _html_page('Progress', body, 'progress')


# ═══════════════════════════════════════════════════════════════════════════
# Phase 4: Feedback & Progress API Handlers
# ═══════════════════════════════════════════════════════════════════════════


def _api_feedback_list() -> str:
    """GET /api/feedback — all feedback for learner as JSON."""
    feedback = get_feedback_for_learner()
    return json.dumps(feedback, indent=2, default=str)


def _api_feedback_unread() -> str:
    """GET /api/feedback/unread — unread feedback count and items."""
    unread = get_unread_feedback()
    return json.dumps({'count': len(unread), 'items': unread}, indent=2, default=str)


def _api_feedback_mark_seen(body: dict) -> str:
    """POST /api/feedback/seen — mark feedback as seen."""
    artifact_id = body.get('artifactId', '')
    review_id = body.get('reviewId', '')
    if artifact_id and review_id:
        mark_seen(artifact_id, review_id)
    else:
        mark_all_seen()
    return json.dumps({'status': 'ok'})


def _api_feedback_qa_get(review_id: str) -> str:
    """GET /api/feedback/qa/{reviewId} — Q&A thread for a review."""
    thread = get_qa_thread(review_id)
    return json.dumps(thread, indent=2, default=str)


def _api_feedback_qa_add(body: dict) -> str:
    """POST /api/feedback/qa — add a Q&A entry."""
    review_id = body.get('reviewId', '')
    text = body.get('text', '').strip()
    artifact_id = body.get('artifactId', '')
    if not review_id or not text:
        return json.dumps({'status': 'error', 'message': 'reviewId and text required'})
    entry = add_qa_entry(review_id, 'learner', text, artifact_id)
    return json.dumps({'status': 'ok', 'entry': entry}, default=str)


def _api_progress() -> str:
    """GET /api/progress — level progression data as JSON."""
    return json.dumps(get_level_progress(), indent=2, default=str)


def _api_learner_summary() -> str:
    """GET /api/learner/summary — learner's daily summary data."""
    summary = compile_learner_daily_summary()
    return json.dumps(summary, indent=2, default=str)


# ═══════════════════════════════════════════════════════════════════════════
# Phase 4: Email Scheduler
# ═══════════════════════════════════════════════════════════════════════════


def _send_email(to_addr: str, subject: str, html_body: str) -> tuple:
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


def _build_learner_summary_html(summary: dict) -> str:
    """Build an HTML email body for the learner's daily summary."""
    unread = summary.get('unread_feedback', 0)
    notes_today = summary.get('notes_today', 0)
    evidence_today = summary.get('evidence_today', 0)
    total_notes = summary.get('total_notes', 0)
    total_evidence = summary.get('total_evidence', 0)
    current_day = summary.get('current_day', 0)
    latest_class = summary.get('latest_classification', '—')

    return f'''<!DOCTYPE html><html><body style="font-family:system-ui,sans-serif;background:#f5f5f5;padding:20px">
<div style="max-width:520px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.08)">
  <div style="background:linear-gradient(135deg,#7c73ff,#a29bfe);padding:24px;color:#fff">
    <h1 style="margin:0;font-size:18px">🌅 MUE Daily Summary</h1>
    <p style="margin:6px 0 0;opacity:.85;font-size:13px">{datetime.now().strftime("%A, %Y-%m-%d")}</p>
  </div>
  <div style="padding:20px 24px">
    <h2 style="font-size:15px;color:#333;margin:0 0 12px">📊 Your Progress</h2>
    <table style="width:100%;margin-bottom:16px"><tr>
      <td style="background:#f8f9fa;border-radius:8px;padding:12px;text-align:center;width:25%"><div style="font-size:22px;font-weight:700;color:#7c73ff">{current_day}/28</div><div style="font-size:11px;color:#888">Days</div></td>
      <td style="background:#f8f9fa;border-radius:8px;padding:12px;text-align:center;width:25%"><div style="font-size:22px;font-weight:700;color:#198754">{total_notes}</div><div style="font-size:11px;color:#888">Notes</div></td>
      <td style="background:#f8f9fa;border-radius:8px;padding:12px;text-align:center;width:25%"><div style="font-size:22px;font-weight:700;color:#3b82f6">{total_evidence}</div><div style="font-size:11px;color:#888">Evidence Files</div></td>
      <td style="background:#f8f9fa;border-radius:8px;padding:12px;text-align:center;width:25%"><div style="font-size:22px;font-weight:700;color:#f59e0b">{latest_class}</div><div style="font-size:11px;color:#888">Classification</div></td>
    </tr></table>

    <h2 style="font-size:15px;color:#333;margin:16px 0 8px">📋 Today's Activity</h2>
    <p style="font-size:13px;color:#333;">
      Notes written today: <strong>{notes_today}</strong><br>
      Evidence uploaded today: <strong>{evidence_today}</strong>
    </p>

    <h2 style="font-size:15px;color:#333;margin:16px 0 8px">📬 Feedback</h2>
    <p style="font-size:13px;color:{'#dc3545' if unread > 0 else '#198754'};">
      {'⚠️ You have <strong>' + str(unread) + '</strong> unread feedback item(s) requiring attention.' if unread > 0 else '✅ All feedback has been reviewed.'}
    </p>

    <p style="font-size:12px;color:#aaa;margin:20px 0 0;text-align:center;">
      Sent by MUE Learner Server · <a href="http://localhost:5005" style="color:#7c73ff;">Open Dashboard</a>
    </p>
  </div>
</div></body></html>'''


def _get_active_profile_email() -> str:
    """Get the email address from the active (current session) learner profile.

    Returns the email from the specific learner profile tied to the current
    session. Returns an empty string if no profile or no email is set, so
    that any email about reviewer input always goes to the correct learner.
    """
    try:
        from action.proxy.web_interface import get_profile_by_id as _gpbi3
        pid = _learner.profile_id
        if pid:
            p = _gpbi3(pid)
            if p and p.get('email'):
                return p['email']
    except Exception:
        pass
    return ''


def send_learner_daily_summary():
    """Compile and send the learner's daily summary email."""
    global _scheduler_running
    to_addr = _get_active_profile_email()
    if not SUMMARY_ENABLED or not to_addr:
        return False

    summary = compile_learner_daily_summary()
    html_body = _build_learner_summary_html(summary)
    subject = f'🌅 MUE Daily Summary — Day {summary["current_day"]} · {summary["total_notes"]} notes, {summary["total_evidence"]} evidence'

    ok, err = _send_email(to_addr, subject, html_body)
    if ok:
        print(f'  📧 Daily summary sent to {to_addr}')
    else:
        print(f'  ⚠️ Failed to send daily summary: {err}')
    return ok


def _scheduler_loop():
    """Background thread that checks every 60s if it's time for the daily summary."""
    global _scheduler_running
    _scheduler_running = True
    while _scheduler_running:
        try:
            now = datetime.now()
            if now.hour == DAILY_SUMMARY_HOUR and now.minute == DAILY_SUMMARY_MINUTE:
                send_learner_daily_summary()
                # Sleep extra to avoid re-triggering in the same minute
                time.sleep(70)
            else:
                time.sleep(55)
        except Exception:
            time.sleep(55)
    _scheduler_running = False


def start_email_scheduler():
    """Start the background email scheduler thread."""
    global _scheduler_thread
    if _scheduler_thread and _scheduler_thread.is_alive():
        return
    _scheduler_thread = threading.Thread(target=_scheduler_loop, daemon=True)
    _scheduler_thread.start()
    _sched_email = _get_active_profile_email()
    if SUMMARY_ENABLED and _sched_email:
        print(f'  📧 Daily summary scheduled for {DAILY_SUMMARY_HOUR:02d}:{DAILY_SUMMARY_MINUTE:02d} → {_sched_email}')


def _api_send_summary() -> str:
    """POST /api/learner/summary/send — manually trigger the daily summary email."""
    ok = send_learner_daily_summary()
    return json.dumps({'status': 'ok' if ok else 'error'})


def _build_welcome_email_html(profile: dict) -> str:
    """Build an HTML welcome email for a newly created learner profile."""
    profile_id = profile.get('id', '')
    name = profile.get('name', 'Learner')
    email = profile.get('email', '')
    created_at = profile.get('created_at', datetime.now().isoformat())
    start_date = profile.get('start_date', 'Auto-detected')
    has_password = bool(profile.get('password_hash'))
    created_str = created_at[:10] if created_at else 'today'
    login_url = f'http://localhost:5005'

    return f'''<!DOCTYPE html><html><body style="font-family:system-ui,sans-serif;background:#f0f4ff;padding:20px">
<div style="max-width:560px;margin:0 auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.10)">
  <div style="background:linear-gradient(135deg,#7c73ff,#a29bfe);padding:28px 32px;color:#fff">
    <div style="font-size:40px;margin-bottom:8px;">🎉</div>
    <h1 style="margin:0 0 4px;font-size:22px;font-weight:700;">Welcome to MUE, {name}!</h1>
    <p style="margin:0;opacity:.85;font-size:14px;">Your BI learning journey starts today</p>
  </div>
  <div style="padding:24px 32px">
    <p style="font-size:15px;color:#333;line-height:1.6;margin:0 0 20px;">
      Your learner profile has been created. Below are your profile details and
      security information — please save them for your records.
    </p>

    <table style="width:100%;border-collapse:collapse;margin-bottom:20px;">
      <tr>
        <td style="padding:10px 14px;background:#f8f9fa;font-size:13px;font-weight:600;color:#333;width:120px;border-radius:8px 0 0 8px;">Display Name</td>
        <td style="padding:10px 14px;background:#f8f9fa;font-size:14px;color:#333;border-radius:0 8px 8px 0;">{name}</td>
      </tr>
      <tr><td colspan="2" style="height:6px;"></td></tr>
      <tr>
        <td style="padding:10px 14px;background:#f8f9fa;font-size:13px;font-weight:600;color:#333;border-radius:8px 0 0 8px;">Profile ID</td>
        <td style="padding:10px 14px;background:#f8f9fa;font-size:14px;color:#6366f1;font-family:monospace;border-radius:0 8px 8px 0;">{profile_id}</td>
      </tr>
      <tr><td colspan="2" style="height:6px;"></td></tr>
      <tr>
        <td style="padding:10px 14px;background:#f8f9fa;font-size:13px;font-weight:600;color:#333;border-radius:8px 0 0 8px;">Email</td>
        <td style="padding:10px 14px;background:#f8f9fa;font-size:14px;color:#333;border-radius:0 8px 8px 0;">{email}</td>
      </tr>
      <tr><td colspan="2" style="height:6px;"></td></tr>
      <tr>
        <td style="padding:10px 14px;background:#f8f9fa;font-size:13px;font-weight:600;color:#333;border-radius:8px 0 0 8px;">Password</td>
        <td style="padding:10px 14px;background:#f8f9fa;font-size:14px;color:#333;border-radius:0 8px 8px 0;">{'✅ Set (hashed, not stored in plain text)' if has_password else '⚠️ Not set'}</td>
      </tr>
      <tr><td colspan="2" style="height:6px;"></td></tr>
      <tr>
        <td style="padding:10px 14px;background:#f8f9fa;font-size:13px;font-weight:600;color:#333;border-radius:8px 0 0 8px;">Created</td>
        <td style="padding:10px 14px;background:#f8f9fa;font-size:14px;color:#333;border-radius:0 8px 8px 0;">{created_str}</td>
      </tr>
      <tr><td colspan="2" style="height:6px;"></td></tr>
      <tr>
        <td style="padding:10px 14px;background:#f8f9fa;font-size:13px;font-weight:600;color:#333;border-radius:8px 0 0 8px;">Start Date</td>
        <td style="padding:10px 14px;background:#f8f9fa;font-size:14px;color:#333;border-radius:0 8px 8px 0;">{start_date}</td>
      </tr>
    </table>

    <div style="background:#fef3c7;border-left:4px solid #f59e0b;padding:12px 16px;border-radius:6px;margin-bottom:20px;">
      <p style="margin:0;font-size:13px;color:#92400e;">
        <strong>🔒 Security Notice:</strong> Your password is stored using
        PBKDF2-HMAC-SHA256 hashing. It is never stored in plain text.
        Never share your password or profile ID with anyone.
      </p>
    </div>

    <div style="background:#f0fdf4;border-left:4px solid #22c55e;padding:12px 16px;border-radius:6px;margin-bottom:20px;">
      <p style="margin:0;font-size:13px;color:#166534;">
        <strong>🚀 Getting Started:</strong> Open your personal dashboard to
        begin your 28-day curriculum. Your profile is ready and waiting.
      </p>
    </div>

    <div style="text-align:center;margin:24px 0;">
      <a href="{login_url}"
         style="display:inline-block;background:linear-gradient(135deg,#7c73ff,#a29bfe);color:#fff;padding:14px 32px;border-radius:10px;font-size:15px;font-weight:600;text-decoration:none;">
        🚀 Open MUE Dashboard
      </a>
    </div>

    <p style="font-size:12px;color:#9ca3af;text-align:center;margin:20px 0 0;">
      MUE — Model-Understanding-Evidence · 28-Day BI Curriculum<br>
      Sent by the MUE Learner Server
    </p>
  </div>
</div></body></html>'''


def _build_profile_update_email_html(profile: dict, changes_html: str) -> str:
    """Build an HTML email notifying the learner of profile changes."""
    name = profile.get('name', 'Learner')
    email = profile.get('email', '')
    login_url = 'http://localhost:5005'

    return f'''<!DOCTYPE html><html><body style="font-family:system-ui,sans-serif;background:#f0f4ff;padding:20px">
<div style="max-width:560px;margin:0 auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.10)">
  <div style="background:linear-gradient(135deg,#6366f1,#818cf8);padding:28px 32px;color:#fff">
    <div style="font-size:40px;margin-bottom:8px;">🔐</div>
    <h1 style="margin:0 0 4px;font-size:22px;font-weight:700;">Profile Updated, {name}!</h1>
    <p style="margin:0;opacity:.85;font-size:14px;">Your MUE learner profile has been changed</p>
  </div>
  <div style="padding:24px 32px">
    <p style="font-size:15px;color:#333;line-height:1.6;margin:0 0 20px;">
      The following changes were made to your profile:
    </p>

    <div style="background:#f8f9fa;border-radius:10px;padding:16px 20px;margin-bottom:20px;">
      <ul style="margin:0;padding-left:20px;font-size:14px;color:#333;line-height:1.8;">
        {changes_html}
      </ul>
    </div>

    <div style="background:#fef3c7;border-left:4px solid #f59e0b;padding:12px 16px;border-radius:6px;margin-bottom:20px;">
      <p style="margin:0;font-size:13px;color:#92400e;">
        <strong>🔒 Security Notice:</strong> If you did not make these changes,
        please contact your administrator immediately. Your password is stored
        using PBKDF2-HMAC-SHA256 hashing and is never stored in plain text.
      </p>
    </div>

    <table style="width:100%;border-collapse:collapse;margin-bottom:20px;">
      <tr>
        <td style="padding:10px 14px;background:#f8f9fa;font-size:13px;font-weight:600;color:#333;width:120px;border-radius:8px 0 0 8px;">Profile ID</td>
        <td style="padding:10px 14px;background:#f8f9fa;font-size:14px;color:#6366f1;font-family:monospace;border-radius:0 8px 8px 0;">{profile.get('id', '')}</td>
      </tr>
      <tr><td colspan="2" style="height:6px;"></td></tr>
      <tr>
        <td style="padding:10px 14px;background:#f8f9fa;font-size:13px;font-weight:600;color:#333;border-radius:8px 0 0 8px;">Email</td>
        <td style="padding:10px 14px;background:#f8f9fa;font-size:14px;color:#333;border-radius:0 8px 8px 0;">{email}</td>
      </tr>
      <tr><td colspan="2" style="height:6px;"></td></tr>
      <tr>
        <td style="padding:10px 14px;background:#f8f9fa;font-size:13px;font-weight:600;color:#333;border-radius:8px 0 0 8px;">Updated</td>
        <td style="padding:10px 14px;background:#f8f9fa;font-size:14px;color:#333;border-radius:0 8px 8px 0;">{datetime.now().strftime('%Y-%m-%d %H:%M')}</td>
      </tr>
    </table>

    <div style="text-align:center;margin:24px 0;">
      <a href="{login_url}"
         style="display:inline-block;background:linear-gradient(135deg,#6366f1,#818cf8);color:#fff;padding:14px 32px;border-radius:10px;font-size:15px;font-weight:600;text-decoration:none;">
        🚀 Open MUE Dashboard
      </a>
    </div>

    <p style="font-size:12px;color:#9ca3af;text-align:center;margin:20px 0 0;">
      MUE — Model-Understanding-Evidence · 28-Day BI Curriculum<br>
      Sent by the MUE Learner Server
    </p>
  </div>
</div></body></html>'''


def _api_status() -> str:
    """GET /api/status — learner status, current day, classification."""
    today_str = date.today().isoformat()
    day_num = _learner.get_curriculum_day(today_str) or 1
    entry = CURRICULUM.get(day_num, {})
    notes_count = len(_learner.list_notes())
    evidence_count = len(_learner.list_evidence())

    try:
        profile_id = _learner.profile_id or 'default'
        profile_name = _learner.get_profile_label()
    except Exception:
        profile_id = 'default'
        profile_name = 'Default'

    return json.dumps({
        'learner_name': _learner.get_name(),
        'profile_id': profile_id,
        'profile_name': profile_name,
        'current_day': day_num,
        'week': (day_num - 1) // 7 + 1,
        'total_days': 28,
        'focus': entry.get('focus', ''),
        'classification': get_classification(day_num),
        'primary_track': get_primary_track(day_num),
        'level': get_level_for_day(day_num),
        'notes_count': notes_count,
        'evidence_count': evidence_count,
    })


def _api_curriculum() -> str:
    """GET /api/curriculum — full 28-day schedule as JSON."""
    return json.dumps({str(k): v for k, v in CURRICULUM.items()}, indent=2)


def _api_notes_list() -> str:
    """GET /api/notes — list all notes as JSON."""
    notes = []
    for n in _learner.list_notes():
        day = _learner._extract_day_from_note(n)
        notes.append({
            'date': n.stem,
            'day': day,
            'path': str(n),
        })
    return json.dumps(notes, indent=2)


def _api_note_get(date_str: str) -> str:
    """GET /api/notes/{date} — get a specific note's content as JSON."""
    from urllib.parse import unquote
    date_str = unquote(date_str)
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return json.dumps({'error': 'invalid date'})
    note_path = _learner.notes_dir / f'{date_str}.md'
    if not note_path.exists():
        return json.dumps({'error': 'not found'})
    content = note_path.read_text(encoding='utf-8')
    return json.dumps({'date': date_str, 'content': content}, indent=2)


def _api_note_save(body: dict) -> str:
    """POST /api/notes — create or update a note."""
    date_str = body.get('date', date.today().isoformat())
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return json.dumps({'status': 'error', 'message': 'Invalid date format'})
    day_number = int(body.get('day_number', 1))

    fields = {
        'classification': body.get('classification', 'Foundational'),
        'primary_track': body.get('primary_track', 'BI judgment'),
        'level': int(body.get('level', 1)),
        'what_learned': body.get('what_learned', ''),
        'evidence_produced': body.get('evidence_produced', ''),
        'what_remains': body.get('what_remains', ''),
        'next_step': body.get('next_step', ''),
        'scorecard': body.get('scorecard', {}),
        'codex_gate': body.get('codex_gate', {}),
        'required_artifact': body.get('required_artifact', ''),
    }

    try:
        # Create revision before overwriting (if note already exists)
        note_path = _learner.notes_dir / f'{date_str}.md'
        create_revision(note_path, 'note', f'{date_str}.md')

        _learner.stage_note_content(date_str, day_number, fields)
        note_path = _learner.generate_daily_note(date_str, day_number)
        return json.dumps({'status': 'ok', 'date': date_str, 'path': str(note_path)})
    except Exception as e:
        return json.dumps({'status': 'error', 'message': str(e)})


def _api_evidence_list() -> str:
    """GET /api/evidence — list all evidence files as JSON."""
    return json.dumps(_evidence_list_data(), indent=2)


def _api_evidence_get(filename: str) -> str:
    """GET /api/evidence/{filename} — get evidence content."""
    from urllib.parse import unquote
    filename = unquote(filename)
    try:
        filename = _safe_filename(filename, _learner.evidence_dir)
    except ValueError:
        return json.dumps({'error': 'invalid filename'})
    file_path = _learner.evidence_dir / filename
    if not file_path.exists():
        return json.dumps({'error': 'not found'})
    content = file_path.read_text(encoding='utf-8') if file_path.suffix in ('.md', '.txt', '.csv') else '[binary]'
    pt_id = _extract_pt_id(filename)
    return json.dumps({
        'filename': filename,
        'content': content,
        'pt_id': pt_id,
        'day': _extract_day_from_filename(filename),
        'size': file_path.stat().st_size,
    }, indent=2)


def _api_evidence_save(body: dict) -> str:
    """POST /api/evidence — create or update evidence."""
    filename = body.get('filename', '')
    if not filename:
        return json.dumps({'status': 'error', 'message': 'No filename provided'})
    try:
        filename = _safe_filename(filename, _learner.evidence_dir)
    except ValueError:
        return json.dumps({'status': 'error', 'message': 'Invalid filename'})

    # If sections were provided (from template), build markdown
    sections = body.get('sections')
    content = body.get('content')

    if sections and not content:
        # Build from template sections
        lines = [f'# {body.get("pt_id", "Evidence")}', '']
        for heading, text in sections.items():
            lines.append(f'## {heading}')
            lines.append(str(text))
            lines.append('')
        content = '\n'.join(lines)

    if not content:
        return json.dumps({'status': 'error', 'message': 'No content provided'})

    day_number = int(body.get('day_number', 0))

    try:
        # Create revision before overwriting
        ev_path_existing = _learner.evidence_dir / filename
        create_revision(ev_path_existing, 'evidence', filename)

        _learner.stage_evidence_content(day_number if day_number else 1, filename, {
            'filename': filename,
            'content': content,
        })
        ev_path = _learner.generate_evidence(day_number if day_number else 1, filename)
        # If the filename changed, clean up old file
        old_filename = body.get('_original_filename')
        if old_filename and old_filename != filename:
            old_path = _learner.evidence_dir / old_filename
            if old_path.exists():
                old_path.unlink()
        return json.dumps({'status': 'ok', 'filename': filename, 'path': str(ev_path)})
    except Exception as e:
        return json.dumps({'status': 'error', 'message': str(e)})


def _api_evidence_binary_save(body: dict) -> str:
    """POST /api/evidence/binary — upload binary evidence (base64-encoded)."""
    import base64
    filename = body.get('filename', '')
    content_b64 = body.get('content_base64', '')
    if not filename or not content_b64:
        return json.dumps({'status': 'error', 'message': 'Missing filename or content'})
    try:
        filename = _safe_filename(filename, _learner.evidence_dir)
    except ValueError:
        return json.dumps({'status': 'error', 'message': 'Invalid filename'})
    try:
        raw = base64.b64decode(content_b64)
        file_path = _learner.evidence_dir / filename
        # Create revision before overwriting
        create_revision(file_path, 'evidence', filename)
        file_path.write_bytes(raw)
        return json.dumps({'status': 'ok', 'filename': filename, 'size': len(raw)})
    except Exception as e:
        return json.dumps({'status': 'error', 'message': str(e)})


def _api_evidence_delete(filename: str) -> str:
    """DELETE /api/evidence/{filename} — delete evidence file."""
    from urllib.parse import unquote
    filename = unquote(filename)
    try:
        filename = _safe_filename(filename, _learner.evidence_dir)
    except ValueError:
        return json.dumps({'status': 'error', 'message': 'Invalid filename'})
    file_path = _learner.evidence_dir / filename
    if not file_path.exists():
        return json.dumps({'status': 'error', 'message': 'File not found'})
    try:
        file_path.unlink()
        return json.dumps({'status': 'ok'})
    except Exception as e:
        return json.dumps({'status': 'error', 'message': str(e)})


def _api_rebuild() -> str:
    """POST /api/rebuild — trigger build_data.py scoped to current profile."""
    try:
        pid = _learner.profile_id
        cmd = [sys.executable, str(BUILD_SCRIPT)]
        if pid:
            cmd.extend(['--profile', pid])
        result = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return json.dumps({'status': 'ok'})
        else:
            return json.dumps({'status': 'error', 'message': result.stderr.strip()[-200:]})
    except Exception as e:
        return json.dumps({'status': 'error', 'message': str(e)})


# ═══════════════════════════════════════════════════════════════════════════
# HTTP Request Handler
# ═══════════════════════════════════════════════════════════════════════════

class LearnerHTTPHandler(SimpleHTTPRequestHandler):
    """HTTP request handler for the learner web interface."""

    def log_message(self, format, *args):
        """Quiet logs — only print non-static requests."""
        try:
            if len(args) >= 2:
                code = str(args[0])
                target = str(args[1]) if len(args) > 1 else ''
                if not code.startswith('200') or not target.startswith('/static/'):
                    print(f'  {code} {target}')
        except Exception:
            pass  # Ignore logging errors

    def _send_json(self, data: str, status: int = 200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(data.encode('utf-8'))

    def _send_html(self, html: str, status: int = 200):
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def _send_redirect(self, location: str):
        self.send_response(302)
        self.send_header('Location', location)
        self.end_headers()

    def _read_body(self) -> dict:
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            return {}
        raw = self.rfile.read(content_length)
        return json.loads(raw.decode('utf-8'))

    # ── Profile resolution ────────────────────────────────────────

    def _get_profile_id(self) -> str:
        """Determine the active profile from query param or cookie."""
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        if 'profile' in qs:
            return qs['profile'][0]
        cookies = self.headers.get('Cookie', '')
        for c in cookies.split(';'):
            c = c.strip()
            if c.startswith('mue_profile='):
                return c[len('mue_profile='):]
        # Fallback: check for admin session cookie
        admin_user = _get_admin_from_cookies(cookies)
        if admin_user:
            return admin_user
        try:
            from action.proxy.web_interface import get_active_profile_id as _gapi
            return _gapi()
        except Exception:
            return 'default'

    def _resolve_learner(self):
        """Set _learner based on the request's profile."""
        global _learner
        pid = self._get_profile_id()
        if pid in _learners:
            _learner = _learners[pid]
        # else keep default _learner

    def do_GET(self):
        self._resolve_learner()
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/') or '/'
        qs = parse_qs(parsed.query)

        # ── Profile API ───────────────────────────────────────────
        if path == '/api/profiles':
            try:
                from action.proxy.web_interface import load_profiles as _lp
                all_profiles = _lp()
                # Filter out admin profiles for non-admin sessions
                current_pid = self._get_profile_id()
                if _is_admin_session(current_pid):
                    return self._send_json(json.dumps({'profiles': all_profiles}))
                else:
                    visible = [p for p in all_profiles if not _is_admin_profile(p['id'])]
                    return self._send_json(json.dumps({'profiles': visible}))
            except Exception as e:
                return self._send_json(json.dumps({'profiles': [], 'error': str(e)}))

        # ── Static files ──────────────────────────────────────────
        if path.startswith('/static/'):
            rel_path = path[len('/static/'):]
            static_file = STATIC_DIR / rel_path
            if static_file.exists() and static_file.is_file():
                self.send_response(200)
                if static_file.suffix == '.css':
                    self.send_header('Content-Type', 'text/css; charset=utf-8')
                elif static_file.suffix == '.js':
                    self.send_header('Content-Type', 'application/javascript')
                else:
                    self.send_header('Content-Type', 'application/octet-stream')
                self.send_header('Cache-Control', 'max-age=3600')
                self.end_headers()
                with open(static_file, 'rb') as f:
                    self.wfile.write(f.read())
                return
            self.send_error(404, 'Static file not found')
            return

        # ── API routes ────────────────────────────────────────────
        if path == '/api/status':
            return self._send_json(_api_status())
        if path == '/api/curriculum':
            return self._send_json(_api_curriculum())
        if path == '/api/notes':
            return self._send_json(_api_notes_list())
        if path.startswith('/api/notes/'):
            date_str = path[len('/api/notes/'):]
            return self._send_json(_api_note_get(date_str))
        if path == '/api/evidence':
            return self._send_json(_api_evidence_list())
        if path.startswith('/api/evidence/'):
            filename = path[len('/api/evidence/'):]
            return self._send_json(_api_evidence_get(filename))
        # Phase 4 API routes
        if path == '/api/feedback':
            return self._send_json(_api_feedback_list())
        if path == '/api/feedback/unread':
            return self._send_json(_api_feedback_unread())
        if path.startswith('/api/feedback/qa/'):
            review_id = path[len('/api/feedback/qa/'):]
            return self._send_json(_api_feedback_qa_get(review_id))
        if path == '/api/progress':
            return self._send_json(_api_progress())
        if path == '/api/learner/summary':
            return self._send_json(_api_learner_summary())

        # ── Page routes ───────────────────────────────────────────
        if path == '/' or path == '':
            if not _has_learner_profiles():
                return self._send_html(_page_welcome())
            return self._send_html(_page_dashboard())

        # If no learner profiles exist, redirect all non-API/non-static pages to /
        if not _has_learner_profiles() and not path.startswith('/api/') and not path.startswith('/static/'):
            return self._send_redirect('/')

        if path == '/curriculum':
            week = int(qs.get('week', [0])[0])
            return self._send_html(_page_curriculum(week))
        if path == '/day':
            return self._send_redirect('/curriculum')
        if path.startswith('/day/'):
            try:
                day_num = int(path[len('/day/'):])
                if 1 <= day_num <= 28:
                    return self._send_html(_page_day_workspace(day_num))
            except (ValueError, IndexError):
                pass
            return self._send_redirect('/curriculum')
        if path.startswith('/curriculum/'):
            try:
                day_num = int(path[len('/curriculum/'):])
                if 1 <= day_num <= 28:
                    return self._send_html(_page_day_workspace(day_num))
            except (ValueError, IndexError):
                pass
            return self._send_html('<h2>Invalid day</h2><a href="/curriculum">← Back</a>')
        if path == '/notes':
            return self._send_html(_page_note_list())
        if path == '/notes/new':
            day = int(qs.get('day', [1])[0])
            existing_date = qs.get('date', [None])[0]
            return self._send_html(_page_note_editor(day, existing_date=existing_date))
        if path == '/notes/revision':
            rev_path = qs.get('path', [None])[0]
            if rev_path:
                return self._send_html(_page_revision_view(rev_path))
            return self._send_html('<h2>Missing revision path</h2><a href="/notes">← Back</a>')
        if path.startswith('/notes/'):
            date_str = path[len('/notes/'):]
            return self._send_html(_page_note_view(date_str))
        if path == '/evidence':
            return self._send_html(_page_evidence_list())
        if path == '/evidence/new':
            pt = qs.get('pt', [''])[0]
            day = int(qs.get('day', ['1'])[0])
            return self._send_html(_page_evidence_new(pt, day))
        if path == '/evidence/revision':
            rev_path = qs.get('path', [None])[0]
            if rev_path:
                return self._send_html(_page_revision_view(rev_path))
            return self._send_html('<h2>Missing revision path</h2><a href="/evidence">← Back</a>')
        if path.startswith('/evidence/'):
            filename = path[len('/evidence/'):]
            edit_mode = 'edit' in qs
            return self._send_html(_page_evidence_view(filename, edit_mode))
        # Phase 4 page routes
        if path == '/guide':
            return self._send_html(_page_guide())
        if path == '/feedback':
            return self._send_html(_page_feedback_list())
        if path.startswith('/feedback/'):
            artifact_id = path[len('/feedback/'):]
            return self._send_html(_page_feedback_detail(artifact_id))
        if path == '/progress':
            return self._send_html(_page_progress())
        if path == '/manage':
            return self._send_html(_page_manage_profile())
        if path == '/admin-login':
            return self._send_html(_page_admin_login(self.headers.get('Cookie', '')))
        if path == '/api/admin/check':
            cookie = self.headers.get('Cookie', '')
            username = _get_admin_from_cookies(cookie)
            if username:
                self._send_json(json.dumps({'admin': True, 'username': username}))
            else:
                self._send_json(json.dumps({'admin': False, 'username': None}))
            return

        self.send_error(404, 'Not found')

    def do_POST(self):
        self._resolve_learner()
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/') or '/'

        # ── Admin auth (email confirmation code) ──────────────────
        if path == '/api/admin/auth':
            body = self._read_body()
            if not body:
                return
            username = body.get('username', '').strip()
            action = body.get('action', '').strip()
            if not username or not action:
                self._send_json(json.dumps({'ok': False, 'error': 'Username and action required.'}), 400)
                return
            if not _is_admin_profile(username):
                self._send_json(json.dumps({'ok': False, 'error': 'Access denied.'}), 403)
                print(f'  ⚠️ Admin auth denied: @{username} is not an admin profile')
                return

            if action == 'request_code':
                code = ''.join(str(random.randint(0, 9)) for _ in range(6))
                expires_at = time.time() + ADMIN_CODE_TTL
                with _admin_codes_lock:
                    _admin_codes[username] = {'code': code, 'expires_at': expires_at}
                subject = f'🔐 MUE Admin Login Code — {username}'
                html_body = f'''<!DOCTYPE html><html><body style="font-family:system-ui,sans-serif;background:#f5f5f5;padding:20px">
<div style="max-width:480px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.08)">
<div style="background:linear-gradient(135deg,#6c5ce7,#a29bfe);padding:24px;color:#fff;text-align:center">
<h1 style="margin:0;font-size:18px">🔐 Admin Login Code</h1>
<p style="margin:6px 0 0;opacity:.85;font-size:13px">Username: <strong>{_esc_html(username)}</strong></p>
</div>
<div style="padding:24px;text-align:center">
<p style="font-size:14px;color:#333;margin:0 0 16px">Use this code to sign in to the MUE Learner Dashboard:</p>
<div style="background:#f8f9fa;border-radius:12px;padding:20px;font-size:36px;font-weight:700;letter-spacing:12px;color:#6c5ce7;font-family:monospace;margin-bottom:16px">{code}</div>
<p style="font-size:12px;color:#888;margin:0">This code expires in 10 minutes.</p>
<p style="font-size:11px;color:#aaa;margin:8px 0 0">Sent by MUE Learner Server · {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
</div>
</div></body></html>'''
                ok, err = _send_email(ADMIN_VERIFY_EMAIL, subject, html_body)
                if ok:
                    print(f'  📧 Admin login code sent to {ADMIN_VERIFY_EMAIL} for @{username}')
                    self._send_json(json.dumps({'ok': True, 'message': 'Code sent to admin email.'}))
                else:
                    print(f'  ⚠️ Failed to send admin login code: {err}')
                    self._send_json(json.dumps({'ok': False, 'error': f'Failed to send email: {err}'}), 500)
                return

            elif action == 'verify_code':
                code = body.get('code', '').strip()
                if not code:
                    self._send_json(json.dumps({'ok': False, 'error': 'Confirmation code required.'}), 400)
                    return
                with _admin_codes_lock:
                    stored = _admin_codes.get(username)
                    if not stored:
                        self._send_json(json.dumps({'ok': False, 'error': 'No code requested. Request a new code.'}), 403)
                        return
                    if time.time() > stored['expires_at']:
                        del _admin_codes[username]
                        self._send_json(json.dumps({'ok': False, 'error': 'Code expired. Request a new code.'}), 403)
                        return
                    if stored['code'] != code:
                        self._send_json(json.dumps({'ok': False, 'error': 'Invalid code.'}), 403)
                        print(f'  ⚠️ Admin login failed: wrong code for @{username}')
                        return
                    del _admin_codes[username]
                session_id = _create_admin_session(username)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Set-Cookie', f'{ADMIN_SESSION_COOKIE}={session_id}; Path=/; Max-Age={ADMIN_SESSION_TTL}; HttpOnly; SameSite=Lax')
                # Also set the profile cookie so the header shows the admin profile and logout button
                self.send_header('Set-Cookie', f'mue_profile={username}; Path=/; Max-Age={ADMIN_SESSION_TTL}; SameSite=Lax')
                body_bytes = json.dumps({'ok': True, 'username': username}).encode('utf-8')
                self.send_header('Content-Length', str(len(body_bytes)))
                self.end_headers()
                self.wfile.write(body_bytes)
                print(f'  📧 Admin login successful: @{username}')
                return

            else:
                self._send_json(json.dumps({'ok': False, 'error': 'Unknown action. Use request_code or verify_code.'}), 400)
            return

        # ── Profile logout ─────────────────────────────────────────
        if path == '/api/profile/logout':
            # Reset active profile to 'default' in profiles.json so fallback doesn't re-login
            try:
                from action.proxy.web_interface import _save_profiles as _sp, load_profiles as _lp
                profiles = _lp()
                _sp(profiles, active_profile='default')
            except Exception:
                pass  # Best effort; cookie clear is the primary mechanism
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            # Clear the profile cookie (Max-Age=0 → immediate expiry)
            self.send_header('Set-Cookie', 'mue_profile=; Path=/; Max-Age=0')
            # Also clear the admin session cookie if present
            self.send_header('Set-Cookie', f'{ADMIN_SESSION_COOKIE}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok', 'message': 'Logged out'}).encode('utf-8'))
            print('  🚪 Profile logged out')
            return

        # ── Profile switch ─────────────────────────────────────────
        if path == '/api/profile/switch':
            body = self._read_body()
            pid = body.get('profile_id', 'default')
            password = body.get('password') or None
            from action.proxy.web_interface import get_profile_by_id as _gpbi, _verify_password as _vp
            profile = _gpbi(pid)
            if profile or pid == 'default':
                # Admin profile protection:
                # Switching to an admin profile requires an active admin email session
                # (from the /admin-login two-step code flow)
                current_pid = self._get_profile_id()
                is_current_admin = _is_admin_session(current_pid)
                is_target_admin = _is_admin_profile(pid) if pid != 'default' else False

                if is_target_admin and not is_current_admin:
                    # Non-admin session trying to switch to an admin profile
                    # Check for admin session cookie as alternative
                    cookie = self.headers.get('Cookie', '')
                    admin_username = _get_admin_from_cookies(cookie)
                    if admin_username != pid:
                        return self._send_json(json.dumps({
                            'status': 'error',
                            'message': 'Admin profile requires email confirmation. Use the Admin Login page.'
                        }))
                elif profile and profile.get('password_hash'):
                    # Standard password check for non-admin profiles that have a password
                    if not password:
                        return self._send_json(json.dumps({
                            'status': 'error',
                            'message': 'This profile requires a password.'
                        }))
                    if not _vp(password, profile['password_hash'], profile['password_salt']):
                        return self._send_json(json.dumps({
                            'status': 'error',
                            'message': 'Incorrect password.'
                        }))
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Set-Cookie', f'mue_profile={pid}; Path=/; Max-Age=31536000')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'ok', 'profile_id': pid}).encode('utf-8'))
                return
            return self._send_json(json.dumps({'status': 'error', 'message': 'Unknown profile'}))

        # ── Profile create ─────────────────────────────────────────
        if path == '/api/profiles/create':
            body = self._read_body()
            name = body.get('name', '').strip()
            start_date = body.get('start_date') or None
            password = body.get('password') or None
            email = body.get('email') or None
            if not password:
                return self._send_json(json.dumps({'status': 'error', 'message': 'Password is required.'}))
            try:
                from action.proxy.web_interface import create_profile as _cp
                profile = _cp(name, start_date, password, email)
                _reload_profiles()
                # Send welcome email with profile details and security information
                profile_email = profile.get('email', '')
                if profile_email:
                    welcome_subject = f'🎉 Welcome to MUE, {profile.get("name", "Learner")}! Your Profile Details'
                    welcome_html = _build_welcome_email_html(profile)
                    ok, err = _send_email(profile_email, welcome_subject, welcome_html)
                    if ok:
                        print(f'  📧 Welcome email sent to {profile_email}')
                    else:
                        print(f'  ⚠️ Could not send welcome email to {profile_email}: {err}')
                else:
                    print(f'  ⚠️ No email address for profile {profile["id"]}; welcome email not sent')
                # Set cookie to the newly created profile
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Set-Cookie', f'mue_profile={profile["id"]}; Path=/; Max-Age=31536000')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'ok', 'profile': profile}).encode('utf-8'))
            except ValueError as e:
                return self._send_json(json.dumps({'status': 'error', 'message': str(e)}))
            return

        # ── Profile delete ─────────────────────────────────────────
        if path == '/api/profiles/delete':
            body = self._read_body()
            profile_id = body.get('profile_id', '')
            password = body.get('password') or None
            owner_id = self._get_profile_id()
            # Only the profile owner can delete their own profile
            if profile_id != owner_id:
                return self._send_json(json.dumps({
                    'status': 'error',
                    'message': 'You can only delete your own profile.'
                }))
            from action.proxy.web_interface import delete_profile as _dp
            try:
                if _dp(profile_id, password):
                    _reload_profiles()
                    # Clear profile cookie
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Set-Cookie', 'mue_profile=; Path=/; Max-Age=0')
                    self.end_headers()
                    self.wfile.write(json.dumps({'status': 'ok', 'message': 'Profile deleted'}).encode('utf-8'))
                else:
                    return self._send_json(json.dumps({'status': 'error', 'message': 'Profile not found'}))
            except ValueError as e:
                return self._send_json(json.dumps({'status': 'error', 'message': str(e)}))
            return

        # ── Profile update ─────────────────────────────────────────
        if path == '/api/profiles/update':
            body = self._read_body()
            pid = body.get('profile_id', '')
            current_password = body.get('current_password') or None
            new_name = body.get('name')
            new_email = body.get('email')
            new_start_date = body.get('start_date')
            new_password = body.get('new_password') or None
            owner_id = self._get_profile_id()
            # Only the profile owner can update their own profile
            if pid != owner_id:
                return self._send_json(json.dumps({
                    'status': 'error',
                    'message': 'You can only update your own profile.'
                }))
            from action.proxy.web_interface import update_profile as _up
            from action.proxy.web_interface import get_profile_by_id as _gpbi
            try:
                updated_profile, changes = _up(
                    pid, current_password,
                    new_name=new_name, new_email=new_email,
                    new_start_date=new_start_date, new_password=new_password
                )
                _reload_profiles()
                # Notify via email if profile has an email address
                profile_email = updated_profile.get('email', '')
                if profile_email:
                    changes_bullets = '\n'.join(f'<li>{c}</li>' for c in changes)
                    update_subject = f'🔐 MUE Profile Updated — {updated_profile.get("name", "Learner")}'
                    update_html = _build_profile_update_email_html(
                        updated_profile, changes_bullets
                    )
                    ok, err = _send_email(profile_email, update_subject, update_html)
                    if ok:
                        print(f'  📧 Profile update notification sent to {profile_email}')
                    else:
                        print(f'  ⚠️ Could not send profile update email to {profile_email}: {err}')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'status': 'ok',
                    'profile': updated_profile,
                    'changes': changes
                }).encode('utf-8'))
            except ValueError as e:
                return self._send_json(json.dumps({'status': 'error', 'message': str(e)}))
            return

        if path == '/api/notes':
            body = self._read_body()
            return self._send_json(_api_note_save(body))
        if path == '/api/evidence/binary':
            body = self._read_body()
            return self._send_json(_api_evidence_binary_save(body))
        if path == '/api/evidence':
            body = self._read_body()
            return self._send_json(_api_evidence_save(body))
        if path == '/api/rebuild':
            return self._send_json(_api_rebuild())
        # Phase 4 POST endpoints
        if path == '/api/feedback/seen':
            body = self._read_body()
            return self._send_json(_api_feedback_mark_seen(body))
        if path == '/api/feedback/qa':
            body = self._read_body()
            return self._send_json(_api_feedback_qa_add(body))
        if path == '/api/learner/summary/send':
            return self._send_json(_api_send_summary())

        self.send_error(404, 'Not found')

    def do_DELETE(self):
        """Handle DELETE requests for evidence deletion."""
        self._resolve_learner()
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/') or '/'

        if path.startswith('/api/evidence/'):
            filename = path[len('/api/evidence/'):]
            return self._send_json(_api_evidence_delete(filename))

        self.send_error(404, 'Not found')

    def do_OPTIONS(self):
        """CORS preflight."""
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


# ═══════════════════════════════════════════════════════════════════════════
# Entry Point
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='MUE Learner Web Interface')
    parser.add_argument('--port', type=int, default=5000, help='Port to serve on (default: 5000)')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host to bind (default: 127.0.0.1)')
    args = parser.parse_args()

    # Start email scheduler
    start_email_scheduler()

    server = HTTPServer((args.host, args.port), LearnerHTTPHandler)
    profile_count = len(_profiles_list)
    if _profiles_list:
        profile_names = ', '.join(p.get('name', p['id']) for p in _profiles_list)
    else:
        profile_names = 'None — create one at /'
    _startup_email = _get_active_profile_email()
    print(f'''
╔══════════════════════════════════════════════════════════╗
║        MUE Learner Web Interface                         ║
║        Phase 5: Single-profile per user                  ║
╠══════════════════════════════════════════════════════════╣
║  ● Learner: {_learner.get_name():<40s}║
║  ● Start date: {str(_learner.start_date):<37s}║
║  ● Profiles: {profile_count:<2d} ({profile_names:<29s})║
║  ● Notes on disk: {len(_learner.list_notes()):<3d}                      ║
║  ● Email summary: {'ON → ' + _startup_email if SUMMARY_ENABLED and _startup_email else 'OFF':<39s}║
║                                                          ║
║  🏠  Dashboard:  http://{args.host}:{args.port}/            ║
║  📚  Curriculum: http://{args.host}:{args.port}/curriculum  ║
║  📝  Notes:      http://{args.host}:{args.port}/notes       ║
║  📎  Evidence:   http://{args.host}:{args.port}/evidence    ║
║  📬  Feedback:   http://{args.host}:{args.port}/feedback    ║
║  📊  Progress:   http://{args.host}:{args.port}/progress    ║
║                                                          ║
║  Press Ctrl+C to stop.                                   ║
╚══════════════════════════════════════════════════════════╝''')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down...')
        server.server_close()


if __name__ == '__main__':
    main()
