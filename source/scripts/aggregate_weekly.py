#!/usr/bin/env python3
"""
source/scripts/aggregate_weekly.py
Aggregate daily notes in action/notes/ for a given ISO week into action/reports/weekly-YYYY-WW.md
Usage:
    python3 source/scripts/aggregate_weekly.py --year 2026 --week 27
    
    # From source/scripts/:
    python3 aggregate_weekly.py --year 2026 --week 27
"""
import argparse
import os
from datetime import datetime
import glob

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))

NOTES_DIR = os.path.join(REPO_ROOT, 'action', 'notes')
REPORTS_DIR = os.path.join(REPO_ROOT, 'action', 'reports')


def find_notes_for_week(year, week):
    pattern = os.path.join(NOTES_DIR, '*.md')
    files = glob.glob(pattern)
    selected = []
    for p in files:
        name = os.path.basename(p)
        try:
            date = datetime.strptime(name.replace('.md', ''), '%Y-%m-%d')
        except Exception:
            continue
        if date.isocalendar()[0] == year and date.isocalendar()[1] == week:
            selected.append((date, p))
    selected.sort()
    return [p for (_, p) in selected]


def aggregate(year, week):
    notes = find_notes_for_week(year, week)
    if not notes:
        print('No notes found for', year, week)
        return
    os.makedirs(REPORTS_DIR, exist_ok=True)
    out_path = os.path.join(REPORTS_DIR, f'weekly-{year}-{week:02d}.md')
    with open(out_path, 'w', encoding='utf-8') as out:
        out.write(f'# Weekly Report {year} W{week:02d}\n\n')
        for p in notes:
            out.write(f'---\n\n')
            out.write(f'## Note: {os.path.basename(p)}\n\n')
            with open(p, 'r', encoding='utf-8') as f:
                out.write(f.read())
                out.write('\n\n')
    print('Aggregated', len(notes), 'notes into', out_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--year', type=int, required=True)
    parser.add_argument('--week', type=int, required=True)
    args = parser.parse_args()
    aggregate(args.year, args.week)
