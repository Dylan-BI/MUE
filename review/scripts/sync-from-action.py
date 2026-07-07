#!/usr/bin/env python3
"""
review/scripts/sync-from-action.py
Sync completed learner work from action/ into review/ for third-party assessment.
Copies daily notes, evidence artifacts, and reports — but not templates or
in-progress files.

Usage:
    python3 review/scripts/sync-from-action.py
    python3 review/scripts/sync-from-action.py --dry-run   # preview only
"""
import argparse
import glob
import os
import shutil
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ACTION_DIR = os.path.join(REPO_ROOT, 'action')
REVIEW_DIR = os.path.join(REPO_ROOT, 'review')

# Paths relative to action/ and review/
SYNC_PATHS = {
    'notes': ('notes', '*.md'),
    'evidence': ('evidence', '*'),
    'reports': ('reports', '*.md'),
}


def sync_directory(action_subdir, review_subdir, glob_pattern, dry_run=False):
    """Sync files from action/ to review/ for a given subdirectory."""
    src_dir = os.path.join(ACTION_DIR, action_subdir)
    dst_dir = os.path.join(REVIEW_DIR, review_subdir)

    if not os.path.isdir(src_dir):
        print(f'  Source not found: {src_dir}')
        return 0

    os.makedirs(dst_dir, exist_ok=True)
    pattern = os.path.join(src_dir, glob_pattern)
    files = glob.glob(pattern)

    count = 0
    for f in files:
        rel_path = os.path.relpath(f, src_dir)
        dst_file = os.path.join(dst_dir, rel_path)

        # Skip if destination is identical
        if os.path.exists(dst_file) and os.path.getsize(f) == os.path.getsize(dst_file):
            continue

        if dry_run:
            print(f'  Would copy: {action_subdir}/{rel_path} -> review/{review_subdir}/{rel_path}')
        else:
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            shutil.copy2(f, dst_file)
            print(f'  Copied: {action_subdir}/{rel_path} -> review/{review_subdir}/{rel_path}')
        count += 1

    return count


def main():
    parser = argparse.ArgumentParser(description='Sync learner work from action/ to review/')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without copying')
    args = parser.parse_args()

    print('Syncing action/ -> review/')
    if args.dry_run:
        print('  (DRY RUN — no files will be copied)')

    total = 0
    for review_subdir, (action_subdir, pattern) in SYNC_PATHS.items():
        count = sync_directory(action_subdir, review_subdir, pattern, dry_run=args.dry_run)
        total += count

    if total == 0:
        print('No new files to sync.')
    else:
        print(f'Synced {total} file(s).')

    # Also sync the contributor-readiness-check if completed
    readiness_src = os.path.join(ACTION_DIR, 'evidence', 'contributor-readiness-check.md')
    readiness_dst = os.path.join(REVIEW_DIR, 'evidence', 'contributor-readiness-check.md')
    if os.path.exists(readiness_src):
        os.makedirs(os.path.dirname(readiness_dst), exist_ok=True)
        if not args.dry_run:
            shutil.copy2(readiness_src, readiness_dst)
            print('  Copied: evidence/contributor-readiness-check.md -> review/evidence/')
        else:
            print('  Would copy: evidence/contributor-readiness-check.md -> review/evidence/')

    print('Done.')


if __name__ == '__main__':
    main()
