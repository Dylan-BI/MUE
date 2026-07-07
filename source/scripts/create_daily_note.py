#!/usr/bin/env python3
"""
source/scripts/create_daily_note.py
Create a daily note from the Daily Working Template and enforce 4-week (28 day) max.
Usage:
    # From repo root:
    python3 source/scripts/create_daily_note.py --date YYYY-MM-DD --day-number N
    
    # From source/scripts/:
    python3 create_daily_note.py --date YYYY-MM-DD --day-number N
"""
import argparse
import os
import sys
from datetime import datetime

# Script lives in source/scripts/, repo root is two levels up
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))

TEMPLATE_PATH = os.path.join(REPO_ROOT, 'source', 'Pyramid, Codex, and BI Judgment Daily Working Template.txt')
NOTES_DIR = os.path.join(REPO_ROOT, 'action', 'notes')


def load_template():
    with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        return f.read()


def write_note(date_str, day_number, template_content):
    os.makedirs(NOTES_DIR, exist_ok=True)
    filename = f"{date_str}.md"
    path = os.path.join(NOTES_DIR, filename)
    header = f"# Daily Working Note — {date_str} (Day {day_number})\n\n"
    if os.path.exists(path):
        print(f"Note already exists: {path}")
        return path
    with open(path, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write(template_content)
    print(f"Created note: {path}")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', required=True, help='Date for the note YYYY-MM-DD')
    parser.add_argument('--day-number', type=int, required=True, help='Day number in training (1..28)')
    args = parser.parse_args()

    # Enforce 4-week max (28 days)
    if args.day_number < 1 or args.day_number > 28:
        print('Error: --day-number must be between 1 and 28 (4 weeks max).')
        sys.exit(2)

    # Validate date
    try:
        datetime.strptime(args.date, '%Y-%m-%d')
    except ValueError:
        print('Error: --date must be YYYY-MM-DD')
        sys.exit(2)

    template = load_template()
    write_note(args.date, args.day_number, template)


if __name__ == '__main__':
    main()
