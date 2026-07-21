#!/usr/bin/env python3
"""
action/proxy/run_proxy.py
CLI entry point for the MUE Dummy Learner Proxy.

Generates daily notes, evidence artifacts, and weekly reports
that follow the 28-day curriculum. Archives completed work.

Usage:
    # Generate today's note (auto-detects day number)
    python action/proxy/run_proxy.py --today

    # Generate note for a specific date
    python action/proxy/run_proxy.py --date 2026-07-15 --day 20

    # Generate notes for a day range
    python action/proxy/run_proxy.py --range 1-14

    # Archive completed days
    python action/proxy/run_proxy.py --archive 1-14

    # Full cycle: generate + archive
    python action/proxy/run_proxy.py --cycle 1-28

    # Full run: generate all 28 days, archive each week
    python action/proxy/run_proxy.py --full-run
"""
import argparse
import os
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

# Ensure the repo root is on the path for imports
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

# ── Test data is stored in action/test-data/ to keep it isolated
#    from the real learner workspace (action/notes/, action/evidence/).
#    The MUE Learner web interface never reads from test-data.
TEST_DATA_DIR = REPO_ROOT / 'action' / 'test-data'

from action.proxy.dummy import DummyLearner


def parse_range(range_str: str) -> tuple[int, int]:
    """Parse a range string like '1-14' into (1, 14)."""
    parts = range_str.split('-')
    if len(parts) != 2:
        raise ValueError(f'Invalid range format: {range_str}. Expected START-END')
    return int(parts[0]), int(parts[1])


def day_to_date(start_date: date, day_number: int) -> date:
    """Convert curriculum day number to calendar date (skipping weekends)."""
    working_days = 0
    current = start_date
    while working_days < day_number:
        if current.weekday() < 5:
            working_days += 1
        if working_days < day_number:
            current += timedelta(days=1)
    return current


def run_build():
    """Run build_data.py to refresh data.json."""
    build_script = REPO_ROOT / 'action' / 'dashboard' / 'build_data.py'
    if build_script.exists():
        print('\n🔄 Running build_data.py...')
        subprocess.run(
            [sys.executable, str(build_script)],
            cwd=str(REPO_ROOT),
            check=False,
        )


def cmd_today(learner: DummyLearner):
    """Generate today's note."""
    today = date.today()
    today_str = today.isoformat()
    day = learner.get_curriculum_day(today_str)

    if day is None:
        print(f'📅 {today_str} is not a curriculum day (weekend or outside cycle).')
        return

    print(f'📅 Generating note for {today_str} (Day {day})...')
    learner.generate_daily_note(today_str, day)

    # Generate evidence for proof task days
    from action.proxy.curriculum import CURRICULUM
    entry = CURRICULUM.get(day, {})
    if entry.get('proof_task'):
        learner.generate_evidence(day, entry['proof_task'])


def cmd_date(learner: DummyLearner, date_str: str, day_number: int):
    """Generate a note for a specific date and day."""
    print(f'📅 Generating note for {date_str} (Day {day_number})...')
    learner.generate_daily_note(date_str, day_number)

    # Generate evidence for proof task days
    from action.proxy.curriculum import CURRICULUM
    entry = CURRICULUM.get(day_number, {})
    if entry.get('proof_task'):
        learner.generate_evidence(day_number, entry['proof_task'])


def cmd_range(learner: DummyLearner, start: int, end: int):
    """Generate notes for a day range."""
    print(f'📅 Generating notes for days {start}-{end}...')
    for day in range(start, end + 1):
        date_str = day_to_date(learner.start_date, day).isoformat()
        learner.generate_daily_note(date_str, day)

        # Generate evidence for proof task days
        from action.proxy.curriculum import CURRICULUM
        entry = CURRICULUM.get(day, {})
        if entry.get('proof_task'):
            learner.generate_evidence(day, entry['proof_task'])


def cmd_archive(learner: DummyLearner, start: int, end: int):
    """Archive completed days."""
    print(f'📦 Archiving days {start}-{end}...')
    archived_notes = learner.archive_completed((start, end))

    # Archive matching evidence
    from action.proxy.sync import sync_evidence_to_archive
    archived_evidence = sync_evidence_to_archive(learner.action_dir, (start, end))

    # Archive weekly reports for completed weeks
    from action.proxy.sync import sync_reports_to_archive
    for week in range(1, 5):
        week_start_day = (week - 1) * 7 + 1
        week_end_day = min(week * 7, 28)
        if start <= week_start_day and end >= week_end_day:
            sync_reports_to_archive(learner.action_dir, week)

    total = len(archived_notes) + len(archived_evidence)
    if total == 0:
        print('  Nothing to archive.')
    else:
        print(f'  ✅ Archived {total} file(s).')


def cmd_cycle(learner: DummyLearner, start: int, end: int):
    """Generate notes for a range, then archive."""
    cmd_range(learner, start, end)
    cmd_archive(learner, start, end)


def cmd_full_run(learner: DummyLearner):
    """Generate all 28 days, archive each week as completed."""
    print('🚀 Full curriculum run — generating all 28 days...\n')

    for day in range(1, 29):
        date_str = day_to_date(learner.start_date, day).isoformat()
        learner.generate_daily_note(date_str, day)

        # Generate evidence for proof task days
        from action.proxy.curriculum import CURRICULUM
        entry = CURRICULUM.get(day, {})
        if entry.get('proof_task'):
            learner.generate_evidence(day, entry['proof_task'])

        # Generate weekly report at end of each week
        if day % 7 == 0 or day == 28:
            week = (day - 1) // 7 + 1
            learner.generate_weekly_report(week)

    # Archive each week
    print('\n📦 Archiving completed weeks...')
    for week in range(1, 5):
        week_start = (week - 1) * 7 + 1
        week_end = min(week * 7, 28)
        cmd_archive(learner, week_start, week_end)

    print('\n✅ Full run complete!')


def main():
    parser = argparse.ArgumentParser(
        description='MUE Dummy Learner Proxy — generates curriculum artifacts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--today', action='store_true',
                       help="Generate today's note (auto-detects day number)")
    group.add_argument('--date', nargs=2, metavar=('DATE', 'DAY'),
                       help='Generate note for DATE (YYYY-MM-DD) and DAY number')
    group.add_argument('--range', metavar='START-END',
                       help='Generate notes for day range (e.g., 1-14)')
    group.add_argument('--archive', metavar='START-END',
                       help='Archive completed days (e.g., 1-14)')
    group.add_argument('--cycle', metavar='START-END',
                       help='Generate + archive for day range')
    group.add_argument('--full-run', action='store_true',
                       help='Generate all 28 days with weekly reports and archive')

    args = parser.parse_args()
    learner = DummyLearner(action_dir=TEST_DATA_DIR)

    print(f'🎓 Dummy Learner Proxy — {learner.get_name()}')
    print(f'📅 Start date: {learner.start_date.isoformat()}\n')

    if args.today:
        cmd_today(learner)
    elif args.date:
        date_str, day_str = args.date
        cmd_date(learner, date_str, int(day_str))
    elif args.range:
        start, end = parse_range(args.range)
        cmd_range(learner, start, end)
    elif args.archive:
        start, end = parse_range(args.archive)
        cmd_archive(learner, start, end)
    elif args.cycle:
        start, end = parse_range(args.cycle)
        cmd_cycle(learner, start, end)
    elif args.full_run:
        cmd_full_run(learner)

    # Auto-run build_data.py to refresh dashboard
    run_build()


if __name__ == '__main__':
    main()
