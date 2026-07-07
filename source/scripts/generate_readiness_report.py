#!/usr/bin/env python3
"""
source/scripts/generate_readiness_report.py
Parse daily notes in action/notes/ and extract structured evidence, scores, readiness.
Generates a consolidated readiness report in action/reports/.

Usage:
    python3 source/scripts/generate_readiness_report.py                    # latest week
    python3 source/scripts/generate_readiness_report.py --year 2026 --week 27
    python3 source/scripts/generate_readiness_report.py --full             # all notes
"""
import argparse
import glob
import os
import re
from datetime import datetime, date, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))

NOTES_DIR = os.path.join(REPO_ROOT, 'action', 'notes')
REPORTS_DIR = os.path.join(REPO_ROOT, 'action', 'reports')
EVIDENCE_DIR = os.path.join(REPO_ROOT, 'action', 'evidence')

# Patterns to extract from daily notes
PATTERNS = {
    'classification': re.compile(r'Classification:\s*(Foundational|Developing|Operational|Ready For Codex Acceleration)', re.IGNORECASE),
    'primary_track': re.compile(r'Primary track:\s*(Pyramid operations|Codex productivity|BI judgment)', re.IGNORECASE),
    'artifact': re.compile(r'Required Artifact:\s*(.+)', re.IGNORECASE),
    'what_learned': re.compile(r'What I learned today:\s*(.+)', re.IGNORECASE),
    'what_evidence': re.compile(r'What evidence I produced:\s*(.+)', re.IGNORECASE),
    'what_remains': re.compile(r'What remains open:\s*(.+)', re.IGNORECASE),
    'next_narrow_step': re.compile(r'Next narrow step:\s*(.+)', re.IGNORECASE),
}


def parse_date_from_filename(filename):
    """Extract date from YYYY-MM-DD.md filename."""
    basename = os.path.basename(filename).replace('.md', '')
    try:
        return datetime.strptime(basename, '%Y-%m-%d').date()
    except ValueError:
        return None


def extract_daily_data(filepath):
    """Extract structured data from a daily note."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    data = {'file': filepath, 'date': parse_date_from_filename(filepath)}
    for key, pattern in PATTERNS.items():
        match = pattern.search(content)
        data[key] = match.group(1).strip() if match else None

    # Extract day number from header
    day_match = re.search(r'Day\s*(\d+)', content)
    data['day_number'] = int(day_match.group(1)) if day_match else None

    # Check for scorecard indicators
    data['scorecard'] = {}
    score_areas = [
        'prompt_discipline', 'repo_analysis', 'change_isolation',
        'validation_order', 'deployment_awareness', 'reviewer_handoff', 'reusability'
    ]
    score_labels = [
        'Prompt discipline', 'Repo or workspace analysis', 'Change isolation',
        'Validation order', 'Deployment awareness', 'Reviewer handoff', 'Reusability'
    ]
    for area, label in zip(score_areas, score_labels):
        pattern = re.compile(rf'{re.escape(label)}:\s*(Pass|Partial|Fail)', re.IGNORECASE)
        match = pattern.search(content)
        data['scorecard'][area] = match.group(1).capitalize() if match else None

    # Check for Codex gate
    gate_items = [
        'end_to_end_workflow', 'business_logic_ownership', 'validation_evidence',
        'proof_tasks_completed', 'clean_change_slice', 'reusable_asset'
    ]
    gate_labels = [
        'One end-to-end workflow completed',
        'Business-logic ownership understood',
        'Validation evidence produced without help',
        'Proof tasks completed',
        'One clean reviewable change slice',
        'One reusable team asset'
    ]
    data['codex_gate'] = {}
    for item, label in zip(gate_items, gate_labels):
        pattern = re.compile(rf'{re.escape(label)}:\s*(Yes|No)', re.IGNORECASE)
        match = pattern.search(content)
        data['codex_gate'][item] = match.group(1).capitalize() if match else None

    return data


def find_notes_for_week(year, week):
    """Find all notes belonging to the given ISO week."""
    pattern = os.path.join(NOTES_DIR, '*.md')
    files = glob.glob(pattern)
    selected = []
    for p in files:
        d = parse_date_from_filename(p)
        if d and d.isocalendar()[0] == year and d.isocalendar()[1] == week:
            selected.append((d, p))
    selected.sort()
    return [p for (_, p) in selected]


def find_all_notes():
    """Return all notes sorted by date."""
    pattern = os.path.join(NOTES_DIR, '*.md')
    files = glob.glob(pattern)
    dated = []
    for p in files:
        d = parse_date_from_filename(p)
        if d:
            dated.append((d, p))
    dated.sort()
    return [p for (_, p) in dated]


def generate_week_report(year, week, data_list):
    """Generate a structured weekly readiness report."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    out_path = os.path.join(REPORTS_DIR, f'readiness-{year}-W{week:02d}.md')

    with open(out_path, 'w', encoding='utf-8') as out:
        out.write(f'# Readiness Report — {year} W{week:02d}\n\n')
        out.write(f'**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}\n\n')

        # Summary stats
        out.write('## Summary\n\n')
        out.write(f'- Days with notes: {len(data_list)}\n')
        out.write(f'- Date range: {data_list[0]["date"]} to {data_list[-1]["date"]}\n\n')

        # Classification progression
        out.write('## Classification Progression\n\n')
        out.write('| Day | Date | Classification | Primary Track |\n')
        out.write('|-----|------|----------------|---------------|\n')
        for d in data_list:
            cls = d.get('classification', '—') or '—'
            track = d.get('primary_track', '—') or '—'
            day = d.get('day_number', '—') or '—'
            out.write(f'| {day} | {d["date"]} | {cls} | {track} |\n')
        out.write('\n')

        # Evidence artifacts
        out.write('## Evidence Artifacts Produced\n\n')
        for d in data_list:
            artifact = d.get('artifact', '—') or '—'
            day = d.get('day_number', '—') or '—'
            out.write(f'- **Day {day} ({d["date"]}):** {artifact}\n')
        out.write('\n')

        # Daily reports
        out.write('## Daily Reports\n\n')
        for d in data_list:
            day = d.get('day_number', '—') or '—'
            out.write(f'### Day {day} — {d["date"]}\n\n')
            out.write(f'- **Learned:** {d.get("what_learned", "—") or "—"}\n')
            out.write(f'- **Evidence:** {d.get("what_evidence", "—") or "—"}\n')
            out.write(f'- **Remains Open:** {d.get("what_remains", "—") or "—"}\n')
            out.write(f'- **Next Step:** {d.get("next_narrow_step", "—") or "—"}\n\n')

        # Scorecard aggregation
        scorecard_data = {}
        for d in data_list:
            if d.get('scorecard'):
                for area, score in d['scorecard'].items():
                    if score:
                        scorecard_data.setdefault(area, []).append(score)

        if scorecard_data:
            out.write('## Weekly Scorecard\n\n')
            out.write('| Area | Trend |\n')
            out.write('|------|-------|\n')
            for area, scores in scorecard_data.items():
                label = area.replace('_', ' ').title()
                trend = ' → '.join(scores)
                final = scores[-1] if scores else '—'
                out.write(f'| {label} | {trend} → **{final}** |\n')
            out.write('\n')

            # Fail count
            fail_count = sum(1 for scores in scorecard_data.values() if scores and scores[-1] == 'Fail')
            out.write(f'**Fail count this week: {fail_count}**\n')
            if fail_count >= 2:
                out.write('> ⚠️ Two or more areas scored Fail. Repeat this layer next week.\n')
            out.write('\n')

        # Codex Gate
        gate_found = any(d.get('codex_gate') and any(v == 'Yes' for v in d['codex_gate'].values()) for d in data_list)
        if gate_found:
            out.write('## Codex Gate Check\n\n')
            out.write('| Gate | Latest Status |\n')
            out.write('|------|---------------|\n')
            latest = data_list[-1]
            if latest.get('codex_gate'):
                gate_labels_readable = {
                    'end_to_end_workflow': 'End-to-end workflow completed',
                    'business_logic_ownership': 'Business-logic ownership understood',
                    'validation_evidence': 'Validation evidence without help',
                    'proof_tasks_completed': 'Proof tasks completed',
                    'clean_change_slice': 'Clean change slice delivered',
                    'reusable_asset': 'Reusable asset created',
                }
                for gate_key, gate_label in gate_labels_readable.items():
                    status = latest['codex_gate'].get(gate_key, '—') or '—'
                    out.write(f'| {gate_label} | {status} |\n')
            out.write('\n')

            all_yes = all(
                latest['codex_gate'].get(k) == 'Yes'
                for k in ['end_to_end_workflow', 'business_logic_ownership', 'validation_evidence',
                          'proof_tasks_completed', 'clean_change_slice', 'reusable_asset']
            )
            out.write(f'**Codex Gate Decision:** {"✅ Pass — Begin bounded Codex use" if all_yes else "❌ Not yet ready — see missing gates above"}\n\n')

        # Retention prompts
        out.write('## Retention Check\n\n')
        out.write('Answer these at the end of the week:\n\n')
        out.write('1. What concept from **Week 1** am I still using daily?\n')
        out.write('2. What concept from **prior week** am I still using daily?\n')
        out.write('3. Which track advanced most this week?\n')
        out.write('4. Which track needs the most attention next week?\n\n')

        out.write('---\n')
        out.write('*Report generated by `scripts/generate_readiness_report.py`*\n')

    print(f'Generated report: {out_path}')
    return out_path


def generate_full_report(data_list):
    """Generate a full cumulative readiness report across all notes."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    out_path = os.path.join(REPORTS_DIR, 'readiness-full-report.md')

    with open(out_path, 'w', encoding='utf-8') as out:
        out.write('# Full Readiness Report — Cumulative\n\n')
        out.write(f'**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}\n')
        out.write(f'**Total days with notes:** {len(data_list)}\n')
        out.write(f'**Date range:** {data_list[0]["date"]} to {data_list[-1]["date"]}\n\n')

        # Progression overview
        out.write('## Readiness Progression\n\n')
        out.write('```\n')
        for d in data_list:
            cls = d.get('classification', '?') or '?'
            track = d.get('primary_track', '?') or '?'
            day = d.get('day_number', '??') or '??'
            out.write(f'Day {day:>2} ({d["date"]}): {cls:<15} | {track}\n')
        out.write('```\n\n')

        # Proof task tracking
        out.write('## Proof Task Completion\n\n')
        out.write('| Proof Task | Evidence Found |\n')
        out.write('|------------|----------------|\n')
        pt_patterns = {
            'PT1: Repository Analysis Brief': r'Proof Task 1|Repository Analysis Brief',
            'PT2: Review Workflow Dry Run': r'Proof Task 2|Review Workflow Dry Run',
            'PT3: Metric Lineage Walkthrough': r'Proof Task 3|Metric Lineage Walkthrough',
            'PT4: QC Evidence Pack': r'Proof Task 4|QC Evidence Pack|QC evidence',
            'PT5: Deployment Rehearsal': r'Proof Task 5|Deployment Rehearsal',
            'PT6: Reviewer Handoff Test': r'Proof Task 6|Reviewer Handoff Test',
        }
        for pt_name, pt_pattern in pt_patterns.items():
            found_in = []
            for d in data_list:
                filepath = d['file']
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                if re.search(pt_pattern, content, re.IGNORECASE):
                    found_in.append(str(d.get('day_number', d['date'])))
            if found_in:
                out.write(f'| {pt_name} | ✅ Found in days: {", ".join(found_in)} |\n')
            else:
                out.write(f'| {pt_name} | ❌ Not found |\n')
        out.write('\n')

        # Reusable assets
        out.write('## Reusable Assets Created\n\n')
        asset_patterns = [
            r'reusable\s*(team\s*)?asset',
            r'prompt\s*(library|template)',
            r'QC\s*(evidence\s*)?template',
            r'deployment\s*checklist',
            r'handoff\s*template',
            r'troubleshooting\s*guide',
        ]
        assets_found = []
        for d in data_list:
            with open(d['file'], 'r', encoding='utf-8') as f:
                content = f.read()
            for pat in asset_patterns:
                if re.search(pat, content, re.IGNORECASE):
                    assets_found.append((d.get('day_number', d['date']), pat))
        if assets_found:
            for day, pat in assets_found:
                out.write(f'- Day {day}: mentions "{pat}"\n')
        else:
            out.write('- None detected\n')
        out.write('\n')

        out.write('---\n')
        out.write('*Report generated by `scripts/generate_readiness_report.py`*\n')

    print(f'Generated full report: {out_path}')
    return out_path


def main():
    parser = argparse.ArgumentParser(description='Generate structured readiness report from daily notes.')
    parser.add_argument('--year', type=int, default=None, help='ISO year')
    parser.add_argument('--week', type=int, default=None, help='ISO week number')
    parser.add_argument('--full', action='store_true', help='Generate report across all notes')
    args = parser.parse_args()

    if args.full:
        files = find_all_notes()
        if not files:
            print('No notes found in notes/')
            return
        data_list = [extract_daily_data(f) for f in files]
        generate_full_report(data_list)
        return

    # Determine target week
    if args.year and args.week:
        year, week = args.year, args.week
    else:
        today = date.today()
        iso = today.isocalendar()
        year, week = iso[0], iso[1]

    files = find_notes_for_week(year, week)
    if not files:
        print(f'No notes found for {year} W{week:02d}')
        return

    data_list = [extract_daily_data(f) for f in files]
    generate_week_report(year, week, data_list)


if __name__ == '__main__':
    main()
