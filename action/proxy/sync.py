"""
action/proxy/sync.py
Archive sync logic — moves completed learner work to action/archive/.

Safety: only moves files, never deletes. Logs everything.
build_data.py already scans both NOTES_DIR and NOTES_ARCHIVE_DIR.
"""
import os
import re
import shutil
from pathlib import Path
from typing import Optional

ACTION_DIR = Path(__file__).resolve().parent.parent
NOTES_DIR = ACTION_DIR / 'notes'
EVIDENCE_DIR = ACTION_DIR / 'evidence'
REPORTS_DIR = ACTION_DIR / 'reports'
ARCHIVE_NOTES = ACTION_DIR / 'archive' / 'notes'
ARCHIVE_EVIDENCE = ACTION_DIR / 'archive' / 'evidence'
ARCHIVE_REPORTS = ACTION_DIR / 'archive' / 'reports'


def _extract_day_number(note_path: Path) -> Optional[int]:
    """Extract day number from a note file's content."""
    try:
        with open(note_path, 'r', encoding='utf-8') as f:
            content = f.read(500)
        m = re.search(r'Day\s*(\d+)', content)
        return int(m.group(1)) if m else None
    except OSError:
        return None


def _move_file(src: Path, dst_dir: Path) -> Optional[Path]:
    """Move a file to dst_dir, creating dir if needed. Returns destination path."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    if dst.exists():
        return None  # already archived
    shutil.move(str(src), str(dst))
    return dst


def sync_to_archive(action_dir: Path, days_range: tuple[int, int]) -> list[Path]:
    """
    Move notes for days in [start, end] from action/notes/ to action/archive/notes/.

    Args:
        action_dir: Path to action/ directory
        days_range: (start_day, end_day) inclusive

    Returns:
        List of archived file paths.
    """
    start_day, end_day = days_range
    archive_dir = action_dir / 'archive' / 'notes'
    notes_dir = action_dir / 'notes'
    archived = []

    if not notes_dir.exists():
        return archived

    for note_file in notes_dir.glob('*.md'):
        day = _extract_day_number(note_file)
        if day is not None and start_day <= day <= end_day:
            dst = _move_file(note_file, archive_dir)
            if dst:
                archived.append(dst)
                print(f'  📦 Archived note: {note_file.name} → archive/notes/')

    return archived


def sync_evidence_to_archive(action_dir: Path, days_range: tuple[int, int]) -> list[Path]:
    """
    Move evidence files matching days in [start, end] to action/archive/evidence/.

    Evidence files are matched by name patterns like PT1_*, PT2_*, etc.
    """
    start_day, end_day = days_range
    archive_dir = action_dir / 'archive' / 'evidence'
    evidence_dir = action_dir / 'evidence'
    archived = []

    if not evidence_dir.exists():
        return archived

    # Map proof tasks to their due days
    from action.proxy.curriculum import PROOF_TASKS
    pt_days = {pt: info['due_day'] for pt, info in PROOF_TASKS.items()}

    for ev_file in evidence_dir.glob('*.md'):
        # Check if this evidence file matches a day in range
        should_archive = False

        # Check PT files
        for pt, due_day in pt_days.items():
            if pt.lower() in ev_file.name.lower() and start_day <= due_day <= end_day:
                should_archive = True
                break

        # Check day-suffixed files
        day_match = re.search(r'day(\d+)', ev_file.name, re.IGNORECASE)
        if day_match:
            day_num = int(day_match.group(1))
            if start_day <= day_num <= end_day:
                should_archive = True

        if should_archive:
            dst = _move_file(ev_file, archive_dir)
            if dst:
                archived.append(dst)
                print(f'  📦 Archived evidence: {ev_file.name} → archive/evidence/')

    return archived


def sync_reports_to_archive(action_dir: Path, week: int) -> list[Path]:
    """
    Move weekly reports for a completed week to action/archive/reports/.
    """
    archive_dir = action_dir / 'archive' / 'reports'
    reports_dir = action_dir / 'reports'
    archived = []

    if not reports_dir.exists():
        return archived

    for report_file in reports_dir.glob(f'*W{week:02d}*'):
        dst = _move_file(report_file, archive_dir)
        if dst:
            archived.append(dst)
            print(f'  📦 Archived report: {report_file.name} → archive/reports/')

    return archived
