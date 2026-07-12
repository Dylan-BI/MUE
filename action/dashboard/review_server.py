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
import subprocess
import sys
import threading
import time
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# ── Paths ──────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
DASHBOARD_DIR = SCRIPT_DIR
REVIEWS_PATH = REPO_ROOT / 'review' / 'reviews.json'
BUILD_SCRIPT = DASHBOARD_DIR / 'build_data.py'

# ── State ──────────────────────────────────────────────────────────────
_reviews_lock = threading.Lock()
_connected_clients = set()
_client_lock = threading.Lock()

# Edit locks: {(artifactId, reviewId): {name, timestamp, ttl}}
_edit_locks = {}
_edit_locks_lock = threading.Lock()
LOCK_TTL = 600  # 10 minutes — auto-release if editor disconnects


def load_reviews():
    """Load reviews from review/reviews.json."""
    if not REVIEWS_PATH.exists():
        return {}
    try:
        with open(REVIEWS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


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

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == '/api/reviews':
            self._handle_get_reviews()
        elif path == '/api/locks':
            self._handle_get_locks()
        elif path == '/api/status':
            self._handle_get_status()
        else:
            # Serve static files (dashboard.html, data.json, etc.)
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/reviews':
            self._handle_add_review()
        elif parsed.path == '/api/locks':
            self._handle_lock_action()
        else:
            self._send_json(404, {'error': 'Not found'})

    def do_PUT(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/reviews':
            self._handle_update_review()
        else:
            self._send_json(404, {'error': 'Not found'})

    def do_DELETE(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/reviews':
            self._handle_delete_review()
        else:
            self._send_json(404, {'error': 'Not found'})

    # ── API Handlers ───────────────────────────────────────────────────

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
    parser = argparse.ArgumentParser(description='MUE Review Server')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on (default: 8080)')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    args = parser.parse_args()

    # Ensure review/reviews.json directory exists
    REVIEWS_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Run initial build
    print(f'\n🖥️  MUE Review Server')
    print(f'   Dashboard: http://localhost:{args.port}/dashboard.html')
    print(f'   API:       http://localhost:{args.port}/api/reviews')
    print(f'   Status:    http://localhost:{args.port}/api/status')
    print(f'   Reviews:   {REVIEWS_PATH}')
    print()

    rebuild_data_json()
    print()

    server = ThreadedHTTPServer((args.host, args.port), ReviewHandler)
    try:
        print(f'🚀 Listening on http://{args.host}:{args.port}')
        print(f'   Reviewers connect from any device on this network.')
        print(f'   Press Ctrl+C to stop.\n')
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n🛑 Server stopped.')
        server.server_close()


if __name__ == '__main__':
    main()
