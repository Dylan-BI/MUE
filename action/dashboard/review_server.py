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

# ── Paths ──────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
DASHBOARD_DIR = SCRIPT_DIR
REVIEWS_PATH = REPO_ROOT / 'review' / 'reviews.json'
PROFILES_PATH = REPO_ROOT / 'review' / 'reviewer_profiles.json'
BUILD_SCRIPT = DASHBOARD_DIR / 'build_data.py'
ENV_FILE = DASHBOARD_DIR / '.env'

# Set dynamically at startup so emails link to the correct address
_SERVER_BASE_URL = 'http://localhost:8080'

# Access token — set at startup for secure remote access
# When set, all requests must include ?t=<token> to access the dashboard/API
SERVER_ACCESS_TOKEN = None


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
DAILY_SUMMARY_HOUR = int(os.environ.get('MUE_SUMMARY_HOUR', '17'))  # 5 PM default
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
ADMIN_USERS = ['dylan_bi']


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
            print(f'  [{datetime.now().strftime("%H:%M:%S")}] ✅ data.json rebuilt')
        else:
            err = result.stderr.strip().split('\n')[-1] if result.stderr else 'unknown'
            print(f'  [{datetime.now().strftime("%H:%M:%S")}] ⚠️ build failed: {err}')
    except Exception as e:
        print(f'  [{datetime.now().strftime("%H:%M:%S")}] ❌ build error: {e}')


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


def _heartbeat_presence(name, display_name=None, color=None, avatar=None):
    """Update reviewer's last-seen timestamp."""
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
        else:
            _presence[name] = {
                'last_seen': now,
                'display_name': display_name or name,
                'color': color or '#7c73ff',
                'avatar': avatar or ''
            }


def _leave_presence(name):
    """Remove a reviewer from presence list."""
    with _presence_lock:
        _presence.pop(name, None)


def _get_all_presence():
    """Return all reviewers with online/offline status."""
    _cleanup_stale_presence()
    now = time.time()
    with _presence_lock:
        result = []
        for name, info in _presence.items():
            result.append({
                'name': name,
                'display_name': info.get('display_name', name),
                'color': info.get('color', '#7c73ff'),
                'avatar': info.get('avatar', ''),
                'last_seen': info['last_seen'],
                'online': (now - info['last_seen']) <= PRESENCE_TTL
            })
        return result


# ── Daily Summary Email ──────────────────────────────────────────────

def _compile_daily_summary(hours=24):
    """Compile review activity from the last N hours into a structured summary."""
    reviews = load_reviews()
    profiles = load_profiles()
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
            name = r.get('name', 'Unknown')
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
        'when_newest': when_newest
    }


def _build_summary_html(summary):
    """Build an HTML email body from a summary dict."""
    who = summary['who']
    what = summary['what']

    who_rows = ''
    for name, info in who.items():
        ratings = info['ratings']
        who_rows += f'''<tr style="border-bottom:1px solid #eee">
          <td style="padding:8px 12px;font-weight:600">{info["display"]} <span style="color:#888">@{name.lower().replace(" ","_")}</span></td>
          <td style="padding:8px;text-align:center">{info["reviews_count"]}</td>
          <td style="padding:8px;text-align:center;color:#198754">{ratings["👍 Pass"]}</td>
          <td style="padding:8px;text-align:center;color:#ffc107">{ratings["⚡ Needs Work"]}</td>
          <td style="padding:8px;text-align:center;color:#dc3545">{ratings["❌ Rework"]}</td>
        </tr>'''

    review_rows = ''
    for r in what[:20]:  # show up to 20 most recent
        rc = '#198754' if 'Pass' in r['rating'] else ('#dc3545' if 'Rework' in r['rating'] else '#ffc107')
        ts = r['timestamp'][:16].replace('T', ' ')
        review_rows += f'''<tr style="border-bottom:1px solid #f0f0f0">
          <td style="padding:6px 12px;font-size:13px">{ts}</td>
          <td style="padding:6px;font-size:13px;font-weight:600">{r["name"]}</td>
          <td style="padding:6px;font-size:13px">{r["artifact"]}</td>
          <td style="padding:6px"><span style="background:{rc};color:#fff;padding:2px 8px;border-radius:4px;font-size:12px">{r["rating"]}</span></td>
          <td style="padding:6px;font-size:12px;color:#555;max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{r["text"]}</td>
        </tr>'''

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
    """Compile and send daily summaries to all opted-in reviewers."""
    print(f'  [{datetime.now().strftime("%H:%M:%S")}] 📬 Running daily summary...')
    summary = _compile_daily_summary(hours=24)
    if summary['total_reviews'] == 0:
        print(f'  [{datetime.now().strftime("%H:%M:%S")}] ℹ️  No reviews in the last 24h — skipping email')
        return 0

    html_body = _build_summary_html(summary)
    profiles = load_profiles()
    sent_count = 0

    for username, profile in profiles.items():
        if not profile.get('dailySummary') or not profile.get('email'):
            continue
        email = profile['email']
        display = profile.get('displayName', username)
        ok, err = _send_email(email, f'📬 MUE Daily Summary — {summary["total_reviews"]} review(s), {summary["total_reviewers"]} reviewer(s)', html_body)
        if ok:
            print(f'  [{datetime.now().strftime("%H:%M:%S")}] ✅ Summary sent to {display} <{email}>')
            sent_count += 1
        else:
            print(f'  [{datetime.now().strftime("%H:%M:%S")}] ❌ Failed to send to {display} <{email}>: {err}')

    print(f'  [{datetime.now().strftime("%H:%M:%S")}] 📬 Daily summary complete — {sent_count} email(s) sent')
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


def _start_tunnel(port, tool_path, tool_name):
    """Start a tunnel in a background thread, print public URL when ready."""
    import subprocess
    import re

    TUNNEL_NOTIFY_EMAIL = 'dylan@bicyclebi.com'

    if tool_name == 'cloudflared':
        cmd = [tool_path, 'tunnel', '--url', f'http://localhost:{port}', '--no-autoupdate']
    elif tool_name == 'ngrok':
        cmd = [tool_path, 'http', str(port)]
    else:
        print(f'  ❌ Unknown tunnel tool: {tool_name}')
        return

    print(f'  🌐 Starting {tool_name} tunnel...')
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
            print(f'  ❌ {tool_name} failed to start')
            return
        for line in stdout:
            line = line.strip()
            # cloudflared prints URL to stderr/stdout with 'trycloudflare.com'
            # ngrok prints URL with 'ngrok.io' or 'ngrok-free.app'
            match = re.search(r'(https://[a-zA-Z0-9.-]+\.(?:trycloudflare\.com|ngrok(?:-free)?\.app)[^\s]*)', line)
            if match and not url_found:
                public_url = match.group(1)
                url_found = True
                go_url = f'{public_url}/go'
                print(f'  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
                print(f'  🌍 PUBLIC URL:  {go_url}')
                print(f'  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
                print(f'  Share this URL with reviewers on any network.')
                print(f'  The tunnel stays open while the server is running.\n')
                # Email notification
                _tunnel_notify_url(TUNNEL_NOTIFY_EMAIL, public_url, tool_name)
        if not url_found:
            print(f'  ⚠️  {tool_name} started but URL not captured. Check the terminal.')
        # Monitor tunnel process — notify if it dies
        proc.wait()
        if _scheduler_running:
            print(f'  ⚠️  {tool_name} tunnel disconnected.')
            _tunnel_notify_down(TUNNEL_NOTIFY_EMAIL, tool_name)
    except FileNotFoundError:
        print(f'  ❌ {tool_name} not found — install it from https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/')
    except Exception as e:
        print(f'  ❌ Tunnel error: {e}')


def _tunnel_notify_url(to_addr, public_url, tool_name):
    """Send email when a new tunnel URL is available."""
    # Build shareable URL — /go handles token injection server-side
    secure_url = f'{public_url}/go'
    subject = f'🌐 MUE Tunnel Active — {tool_name}'
    body = f'''<!DOCTYPE html><html><body style="font-family:system-ui,sans-serif;background:#f5f5f5;padding:20px">
  <div style="max-width:520px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.08)">
    <div style="background:linear-gradient(135deg,#6c5ce7,#a29bfe);padding:24px;color:#fff">
      <h1 style="margin:0;font-size:18px">🌐 MUE Tunnel Active</h1>
      <p style="margin:6px 0 0;opacity:.85;font-size:13px">{tool_name} · {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
    </div>
    <div style="padding:20px 24px">
      <p style="font-size:14px;color:#333;margin:0 0 16px">A new tunnel URL has been generated. Share this with reviewers:</p>
      <div style="background:#f8f9fa;border-radius:8px;padding:16px;text-align:center;margin-bottom:16px">
        <a href="{secure_url}" style="font-size:16px;font-weight:600;color:#6c5ce7;text-decoration:none;word-break:break-all">{secure_url}</a>
      </div>
      <p style="font-size:11px;color:#aaa;margin:0;text-align:center">This URL will change if the tunnel is restarted.<br>Sent by MUE Review Server</p>
    </div>
  </div></body></html>'''
    ok, err = _send_email(to_addr, subject, body)
    if ok:
        print(f'  📧 Tunnel notification sent to {to_addr}')
    else:
        print(f'  ⚠️  Could not send tunnel email: {err}')


def _tunnel_notify_down(to_addr, tool_name):
    """Send email when the tunnel disconnects."""
    subject = f'⚠️ MUE Tunnel Disconnected — {tool_name}'
    body = f'''<!DOCTYPE html><html><body style="font-family:system-ui,sans-serif;background:#f5f5f5;padding:20px">
  <div style="max-width:520px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.08)">
    <div style="background:linear-gradient(135deg,#dc3545,#e57373);padding:24px;color:#fff">
      <h1 style="margin:0;font-size:18px">⚠️ Tunnel Disconnected</h1>
      <p style="margin:6px 0 0;opacity:.85;font-size:13px">{tool_name} · {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
    </div>
    <div style="padding:20px 24px">
      <p style="font-size:14px;color:#333;margin:0 0 16px">The {tool_name} tunnel has stopped. Remote reviewers can no longer access the dashboard.</p>
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
        print(f'  📧 Tunnel-down notification sent to {to_addr}')
    else:
        print(f'  ⚠️  Could not send tunnel-down email: {err}')


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
        print(f'  [{datetime.now().strftime("%H:%M:%S")}] ⏰ Next daily summary at {target.strftime("%H:%M")} ({int(wait_seconds//3600)}h {int((wait_seconds%3600)//60)}m)')
        # Sleep in small increments so we can stop cleanly
        slept = 0
        while slept < wait_seconds and _scheduler_running:
            time.sleep(min(30, wait_seconds - slept))
            slept += 30
        if _scheduler_running:
            send_daily_summaries()


class ReviewHandler(SimpleHTTPRequestHandler):
    """HTTP handler: REST API for reviews + static file serving."""

    def __init__(self, *args, **kwargs):
        # Serve files from the dashboard directory
        super().__init__(*args, directory=str(DASHBOARD_DIR), **kwargs)

    def end_headers(self):
        # CORS headers for cross-origin access (file:// fallback)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.end_headers()

    def _check_token(self, qs):
        """Verify access token. Returns True if allowed, False if denied (sends 403)."""
        if not SERVER_ACCESS_TOKEN:
            return True  # No token required
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

        # Token check — skip for token-check endpoint, /go redirect, root redirect, data.json, and CORS preflight
        if path not in ('/api/check-token', '/go', '/', '/data.json') and not self._check_token(qs):
            return

        if path == '/go':
            # Short redirect — /go → /dashboard.html?t=<token>
            token_qs = f'?t={SERVER_ACCESS_TOKEN}' if SERVER_ACCESS_TOKEN else ''
            self.send_response(302)
            self.send_header('Location', f'/dashboard.html{token_qs}')
            self.end_headers()
            return
        elif path == '/':
            # Root redirect — /?t=<token> → /dashboard.html?t=<token>
            token_qs = f'?t={SERVER_ACCESS_TOKEN}' if SERVER_ACCESS_TOKEN else ''
            self.send_response(302)
            self.send_header('Location', f'/dashboard.html{token_qs}')
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
            self._handle_get_profiles()
        elif path == '/api/file':
            self._handle_get_file()
        elif path == '/api/check-token':
            self._handle_check_token(qs)
        else:
            # Serve static files (dashboard.html, data.json, etc.)
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

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
        elif parsed.path == '/api/daily-summary':
            self._handle_daily_summary()
        else:
            self._send_json(404, {'error': 'Not found'})

    def do_PUT(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        if not self._check_token(qs):
            return
        if parsed.path == '/api/reviews':
            self._handle_update_review()
        else:
            self._send_json(404, {'error': 'Not found'})

    def do_DELETE(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        if not self._check_token(qs):
            return
        if parsed.path == '/api/reviews':
            self._handle_delete_review()
        else:
            self._send_json(404, {'error': 'Not found'})

    # ── API Handlers ───────────────────────────────────────────────────

    def _handle_get_profiles(self):
        """GET /api/profiles — return all reviewer profiles."""
        profiles = load_profiles()
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
        if not is_new and not is_owner and not is_admin:
            self._send_json(403, {'error': 'access denied — only the profile owner or an admin can edit this profile'})
            print(f'  🚫 Profile save denied: @{requester} tried to edit @{username}')
            return
        profiles[username] = {
            'username': username,
            'displayName': display_name or username,
            'email': body.get('email', '').strip(),
            'dailySummary': bool(body.get('dailySummary', False)),
            'createdAt': body.get('createdAt', datetime.now().isoformat()),
            'updatedAt': datetime.now().isoformat()
        }
        save_profiles(profiles)
        print(f'  👤 Profile saved: {display_name} (@{username}) by @{requester}')
        self._send_json(200, {'ok': True, 'profile': profiles[username]})

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
                print(f'  [{datetime.now().strftime("%H:%M:%S")}] ✅ Summary sent to {display} <{email}>')
                sent += 1
            else:
                print(f'  [{datetime.now().strftime("%H:%M:%S")}] ❌ Failed to send to {display} <{email}>: {err}')
        self._send_json(200, {'ok': True, 'sent': sent, 'reviews': summary['total_reviews'], 'reviewers': summary['total_reviewers']})

    def _handle_get_reviews(self):
        """GET /api/reviews — return all reviews."""
        reviews = load_reviews()
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
                print(f'  🔒 Lock claimed: {name} editing {review_id[:12]}...')
                self._send_json(200, {'ok': True})
            else:
                self._send_json(409, {'error': err})
        elif action == 'release':
            if not name:
                self._send_json(400, {'error': 'name required for release'})
                return
            released = _release_lock(artifact_id, review_id, name)
            if released:
                print(f'  🔓 Lock released: {name} on {review_id[:12]}...')
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
        _heartbeat_presence(name, display_name, color, avatar)
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

        # Assign ID, timestamp, and version
        review['id'] = review.get('id') or generate_id()
        review['timestamp'] = review.get('timestamp') or datetime.now().isoformat()
        review['version'] = 1
        review['_source'] = 'synced'

        # Save to reviews.json
        all_reviews = load_reviews()
        if artifact_id not in all_reviews:
            all_reviews[artifact_id] = []
        all_reviews[artifact_id].append(review)
        save_reviews(all_reviews)

        print(f'  📝 Review added by {review["name"]} on {artifact_id}')
        rebuild_data_json()

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

        # Apply updates
        for key, val in updates.items():
            if key.startswith('_'):
                continue  # Don't allow overwriting internal fields
            review[key] = val

        review['editedAt'] = datetime.now().isoformat()
        review['version'] = review.get('version', 0) + 1
        save_reviews(all_reviews)

        print(f'  ✏️ Review {review_id} updated by {review.get("name", "?")}')
        rebuild_data_json()

        self._send_json(200, {'ok': True, 'review': review})

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
        print(f'  🗑️ Review {review_id} deleted from {artifact_id}')
        rebuild_data_json()

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
        """Serve a file from the repo root. ?path=<relative-path>&format=text|json"""
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        rel_path = (qs.get('path', [''])[0]).strip().lstrip('/')
        if not rel_path or '..' in rel_path:
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
        file_path = REPO_ROOT / repo_path
        if not file_path.exists() or not file_path.is_file():
            self._send_json(404, {'error': f'File not found: {rel_path}'})
            return
        try:
            text = file_path.read_text(encoding='utf-8')
            self._send_json(200, {'content': text, 'path': rel_path})
        except Exception as e:
            self._send_json(500, {'error': str(e)})

    def _send_json(self, status, data):
        """Send a JSON response."""
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        """Custom log format."""
        # Skip noisy static file logs
        msg = format % args
        if '/api/' in msg or 'Error' in msg:
            print(f'  [{datetime.now().strftime("%H:%M:%S")}] {msg}')


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
    args = parser.parse_args()

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
        SERVER_ACCESS_TOKEN = args.token if args.token else ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(20))

    # Set global base URL for email links (uses first LAN IP if available, else localhost)
    global _SERVER_BASE_URL
    lan_ips = _get_lan_ips()
    base_ip = lan_ips[0] if lan_ips else 'localhost'
    _SERVER_BASE_URL = f'http://{base_ip}:{args.port}'

    # Ensure review/reviews.json directory exists
    REVIEWS_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Run initial build
    print(f'\n🖥️  MUE Review Server')
    print(f'   Reviews:   {REVIEWS_PATH}')
    print()

    rebuild_data_json()
    print()

    # Test-summary mode: send now and exit
    if args.test_summary:
        print('📬 Test mode — sending daily summary now...')
        count = send_daily_summaries()
        print(f'Done — {count} email(s) sent.')
        return

    # Print SMTP status
    if SMTP_HOST:
        env_tag = ' (.env)' if ENV_FILE.exists() and not os.environ.get('MUE_SMTP_HOST') else ''
        print(f'   📧 SMTP: {SMTP_HOST}:{SMTP_PORT} (from: {SMTP_FROM}){env_tag}')
        print(f'   📬 Daily summary at {DAILY_SUMMARY_HOUR:02d}:{DAILY_SUMMARY_MINUTE:02d}')
    else:
        print('   📧 SMTP: not configured (set MUE_SMTP_HOST or --smtp-host)')
        print('   📬 Daily summaries: disabled (no SMTP)')
    print()

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
            print('   ⚠️  --tunnel requested but no tunnel tool found.')
            print('   Install cloudflared: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/')
            print('   Or install ngrok:     https://ngrok.com/download')
            print()

    try:
        listen_addr = args.host if args.host != '0.0.0.0' else 'all interfaces'
        print(f'🚀 Listening on http://{listen_addr}:{args.port}')
        if not args.tunnel:
            if lan_ips:
                go_url = f'http://{lan_ips[0]}:{args.port}/go'
                print(f'   🔒 Share this URL:  {go_url}')
                if SERVER_ACCESS_TOKEN:
                    print(f'   (Auto-redirects to dashboard — token passed server-side)')
            else:
                print(f'   ⚠️  No LAN IP detected — use localhost:{args.port}/go')
        print(f'   Press Ctrl+C to stop.\n')
        server.serve_forever()
    except KeyboardInterrupt:
        global _scheduler_running
        _scheduler_running = False
        print('\n🛑 Server stopped.')
        server.server_close()


if __name__ == '__main__':
    main()
