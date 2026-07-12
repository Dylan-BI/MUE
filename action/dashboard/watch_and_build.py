#!/usr/bin/env python3
"""
action/dashboard/watch_and_build.py
File watcher that auto-runs build_data.py when learner data changes.
Watches action/notes/, action/evidence/, action/reports/ for new/modified files.
"""
import hashlib
import os
import subprocess
import sys
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
WATCH_DIRS = ['action/notes', 'action/evidence', 'action/reports']
WATCH_EXTS = {'.md', '.txt', '.json', '.csv', '.xlsx', '.pdf', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.log'}
POLL_INTERVAL = 3  # seconds
DEBOUNCE = 5  # seconds — wait for writes to finish before rebuilding


def file_hashes(root):
    """Snapshot of all watched files: {relpath: mtime}."""
    snap = {}
    for subdir in WATCH_DIRS:
        full = os.path.join(root, subdir)
        if not os.path.isdir(full):
            continue
        for dp, _, fnames in os.walk(full):
            for f in fnames:
                if any(f.endswith(e) for e in WATCH_EXTS):
                    fp = os.path.join(dp, f)
                    rel = os.path.relpath(fp, root)
                    snap[rel] = os.path.getmtime(fp)
    return snap


def rebuild(root):
    """Run build_data.py and return True on success."""
    try:
        # Small delay to let file writes finish
        time.sleep(1)
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        result = subprocess.run(
            [sys.executable, 'action/dashboard/build_data.py'],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
            encoding='utf-8',
            errors='replace'
        )
        if result.returncode == 0:
            print(f'[{time.strftime("%H:%M:%S")}] ✅ Rebuilt data.json')
            return True
        else:
            stderr = result.stderr.strip().split('\n')[-1] if result.stderr else 'unknown error'
            print(f'[{time.strftime("%H:%M:%S")}] ⚠️ build_data.py failed: {stderr}')
            return False
    except subprocess.TimeoutExpired:
        print(f'[{time.strftime("%H:%M:%S")}] ⚠️ build_data.py timed out')
        return False
    except Exception as e:
        print(f'[{time.strftime("%H:%M:%S")}] ❌ Error: {e}')
        return False


def main():
    root = REPO_ROOT
    print(f'👀 Watching for learner data changes in: {", ".join(WATCH_DIRS)}')
    print(f'   Poll interval: {POLL_INTERVAL}s | Debounce: {DEBOUNCE}s')
    print(f'   Repo root: {root}')
    print()

    prev = file_hashes(root)
    first_change = None  # Timestamp of first detection in current batch

    # Build once on startup
    rebuild(root)
    prev = file_hashes(root)  # Snapshot after startup build

    while True:
        time.sleep(POLL_INTERVAL)
        current = file_hashes(root)

        # Detect added, removed, or modified files
        added = set(current.keys()) - set(prev.keys())
        removed = set(prev.keys()) - set(current.keys())
        modified = {k for k in set(current.keys()) & set(prev.keys()) if current[k] != prev[k]}

        if added or removed or modified:
            if first_change is None:
                # Log changes only once per batch
                changed = added | removed | modified
                for c in sorted(changed):
                    if c in added:
                        print(f'  📄 New: {c}')
                    elif c in removed:
                        print(f'  🗑️ Removed: {c}')
                    else:
                        print(f'  ✏️ Modified: {c}')
                first_change = time.time()
            # Don't update prev yet — let debounce detect stability

        # Debounce: once we detect a change, wait for DEBOUNCE seconds of stability
        if first_change is not None and time.time() - first_change >= DEBOUNCE:
            new_snap = file_hashes(root)
            if new_snap != prev:
                rebuild(root)
                prev = new_snap
            first_change = None


if __name__ == '__main__':
    main()
