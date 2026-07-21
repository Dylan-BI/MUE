"""
action/proxy/dummy.py
DummyLearner — simulates a learner progressing through the 28-day MUE curriculum.

Produces notes, evidence, and reports that match the exact format expected by
build_data.py's parse_note() and the dashboard rendering pipeline.

Configurable via action/learner_config.json for start date and learner name.
"""
import json
import os
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from action.proxy.interface import LearnerProxy
from action.proxy.curriculum import (
    CURRICULUM, PROOF_TASKS, get_classification, get_primary_track,
)
from action.proxy.templates.daily_note import build_note_content, get_scorecard, get_codex_gates
from action.proxy.sync import sync_to_archive, sync_evidence_to_archive


# ── Directory paths ──────────────────────────────────────────────────────────
# DummyLearner writes to action/test-data/ by default to keep test data
# isolated from the real learner workspace (action/notes/, action/evidence/).
# The MUE Learner web interface (WebLearner / server.py) never reads test-data.
ACTION_DIR = Path(__file__).resolve().parent.parent  # action/
TEST_DATA_DIR = ACTION_DIR / 'test-data'
NOTES_DIR = ACTION_DIR / 'notes'
EVIDENCE_DIR = ACTION_DIR / 'evidence'
REPORTS_DIR = ACTION_DIR / 'reports'
ARCHIVE_DIR = ACTION_DIR / 'archive'
CONFIG_PATH = ACTION_DIR / 'learner_config.json'

# ── Evidence file templates ──────────────────────────────────────────────────
EVIDENCE_TEMPLATES = {
    'PT1': {
        'filename': 'PT1_repository_analysis.md',
        'content': """# PT1: Repository Analysis Brief

## Business Purpose
{purpose}

## Dependency Order
{dependency_order}

## Key Inputs & Outputs
{io_summary}

## Risks Identified
{risks}

## Safe Change Points
{safe_changes}
""",
    },
    'PT2': {
        'filename': 'PT2_review_dry_run.md',
        'content': """# PT2: Review Workflow Dry Run

## Review Scope
{scope}

## Reviewer Path
{reviewer_path}

## Dry Run Results
{results}

## Issues Found
{issues}

## Resolution
{resolution}
""",
    },
    'PT3': {
        'filename': 'PT3_metric_lineage.md',
        'content': """# PT3: Metric Lineage Walkthrough

## Counting Grain
{grain}

## Active-Row Rules
{active_rows}

## Period Definitions
{periods}

## Calculation Point
{calc_point}

## Rollup Path
{rollup_path}

## Snapshot Validation
{snapshot_validation}
""",
    },
    'PT4': {
        'filename': 'PT4_qc_evidence_pack.md',
        'content': """# PT4: QC Evidence Pack

## QC Checklist Results
{checklist}

## Defects Found
{defects}

## Limitations Identified
{limitations}

## Anomaly Classification
{anomalies}

## Sign-off
{signoff}
""",
    },
    'PT5': {
        'filename': 'PT5_deployment_rehearsal.md',
        'content': """# PT5: Deployment Rehearsal

## Draft Sequence
{sequence}

## Dry Run Results
{dry_run}

## Gaps Identified
{gaps}

## Corrective Actions
{corrective}

## Final Status
{status}
""",
    },
    'PT6': {
        'filename': 'PT6_reusable_asset.md',
        'content': """# PT6: Reusable Team Asset

## Asset Charter
{charter}

## Description
{description}

## Example Use Case
{example}

## Testing Results
{testing}

## Peer Review
{review}

## Published Location
{location}
""",
    },
}


class DummyLearner(LearnerProxy):
    """
    Simulates a learner progressing through the 28-day MUE curriculum.

    Reads start date from action/learner_config.json.
    Generates notes, evidence, and reports matching the exact format
    expected by build_data.py and the dashboard.
    """

    def __init__(self, action_dir: Optional[Path] = None):
        self.action_dir = action_dir or TEST_DATA_DIR
        self.notes_dir = self.action_dir / 'notes'
        self.evidence_dir = self.action_dir / 'evidence'
        self.reports_dir = self.action_dir / 'reports'

        # Warn if writing to the live learner directory (not test-data)
        if self.action_dir.resolve() == ACTION_DIR.resolve():
            print('  ⚠️  DummyLearner writing directly to action/ — test data will be visible in the MUE Learner UI!')
            print(f'  💡  Use action/test-data/ instead: DummyLearner(action_dir=Path("action/test-data"))')
        self.config = self._load_config()
        self.start_date = self._resolve_start_date()

    def _load_config(self) -> dict:
        """Load learner configuration from learner_config.json."""
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def _resolve_start_date(self) -> date:
        """Resolve the curriculum start date from config or first note."""
        # 1) Check learner_config.json
        cfg_date = self.config.get('curriculum_start_date')
        if cfg_date:
            try:
                return datetime.strptime(cfg_date, '%Y-%m-%d').date()
            except ValueError:
                pass

        # 2) Auto-detect from existing notes (Day 1)
        for note_file in sorted(self.notes_dir.glob('*.md')):
            day = self._extract_day_from_note(note_file)
            if day == 1:
                date_str = note_file.stem
                try:
                    return datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    pass

        # 3) Default to today
        return date.today()

    def _extract_day_from_note(self, note_path: Path) -> Optional[int]:
        """Extract day number from a note file's content."""
        try:
            import re
            with open(note_path, 'r', encoding='utf-8') as f:
                content = f.read(500)  # only read header
            m = re.search(r'Day\s*(\d+)', content)
            return int(m.group(1)) if m else None
        except OSError:
            return None

    def get_name(self) -> str:
        """Return the learner's display name."""
        return self.config.get('learner_name') or 'Dummy Learner'

    def get_curriculum_day(self, date_str: str) -> Optional[int]:
        """
        Given a date string, return which curriculum day it maps to (1-28).
        Returns None if it's a weekend or outside the 28-day cycle.
        """
        try:
            d = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return None

        if d.weekday() >= 5:  # Saturday or Sunday
            return None

        # Count working days from start_date to this date
        working_days = 0
        current = self.start_date
        while current <= d:
            if current.weekday() < 5:
                working_days += 1
            current += timedelta(days=1)

        if working_days < 1 or working_days > 28:
            return None

        return working_days

    def generate_daily_note(self, date_str: str, day_number: int) -> Path:
        """Generate a daily note for the given date and day number."""
        self.notes_dir.mkdir(parents=True, exist_ok=True)

        # Check if note already exists
        note_path = self.notes_dir / f'{date_str}.md'
        if note_path.exists():
            print(f'  Note already exists: {note_path}')
            return note_path

        # Build content from curriculum
        content = build_note_content(date_str, day_number)

        # Write note
        with open(note_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f'  ✅ Created note: {note_path.name} (Day {day_number})')
        return note_path

    def generate_evidence(self, day_number: int, evidence_type: str) -> Path:
        """Generate an evidence artifact for the given day and type."""
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

        template = EVIDENCE_TEMPLATES.get(evidence_type)
        if not template:
            # Generic evidence file
            evidence_path = self.evidence_dir / f'{evidence_type.lower()}_day{day_number}.md'
            if evidence_path.exists():
                print(f'  Evidence already exists: {evidence_path}')
                return evidence_path
            content = f'# {evidence_type}\n\nDay {day_number} evidence artifact.\n'
            with open(evidence_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'  ✅ Created evidence: {evidence_path.name}')
            return evidence_path

        evidence_path = self.evidence_dir / template['filename']
        if evidence_path.exists():
            print(f'  Evidence already exists: {evidence_path}')
            return evidence_path

        # Fill template with realistic content
        entry = CURRICULUM.get(day_number, {})
        focus = entry.get('focus', evidence_type)
        content = template['content'].format(
            purpose=f'Analyse the MUE repository structure and dependencies for {focus}.',
            dependency_order='Source → Transformation → Snapshot → Rollup → Presentation',
            io_summary=f'Key inputs: daily notes, evidence artifacts. Key outputs: dashboard data, readiness reports.',
            risks=f'Risk 1: Incomplete data for {focus}. Risk 2: Missing validation coverage.',
            safe_changes='Dashboard display logic, template formatting, proxy configuration.',
            scope=f'Review workflow for Day {day_number} deliverables.',
            reviewer_path='Peer review → Team lead approval → Archive',
            results='All items reviewed. Minor formatting issues found.',
            issues='One missing validation step in Day {day_number} workflow.',
            resolution='Added validation step to checklist.',
            grain=f'Day {day_number} counting grain — individual note entries.',
            active_rows='Active rows: notes with day_number matching current curriculum day.',
            periods=f'Week {entry.get("week", 1)} period — 7 working days.',
            calc_point='Calculation occurs at note level, aggregated weekly.',
            rollup_path='Note → Weekly Report → Readiness Report → Dashboard Summary',
            snapshot_validation='Snapshot matches source notes. No drift detected.',
            checklist=f'[PASS] Data integrity check\n[PASS] Format validation\n[PASS] Completeness check',
            defects='None identified.',
            limitations='Dashboard rendering limited to 28-day window.',
            anomalies='No anomalies detected.',
            signoff='QC complete. Ready for deployment.',
            sequence='1. Export model → 2. Import to target → 3. Validate → 4. Go-live',
            dry_run='Dry run completed successfully. All steps validated.',
            gaps='Minor timing difference between planned and actual deployment.',
            corrective='Adjusted deployment window. No blocking issues.',
            status='Deployment rehearsal passed. Ready for production.',
            charter=f'Reusable asset for Day {day_number} curriculum support.',
            description=f'Asset supporting the {focus} curriculum area.',
            example=f'Use this asset when working on {focus} tasks.',
            testing='Tested with sample data. All scenarios pass.',
            review='Peer review completed. Minor suggestions incorporated.',
            location=f'action/evidence/{template["filename"]}',
        )

        with open(evidence_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f'  ✅ Created evidence: {evidence_path.name}')
        return evidence_path

    def generate_weekly_report(self, week: int) -> Path:
        """Generate a weekly scorecard report."""
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        report_path = self.reports_dir / f'weekly-{self.start_date.year}-W{week:02d}.md'
        if report_path.exists():
            print(f'  Report already exists: {report_path}')
            return report_path

        # Find notes for this week
        week_notes = []
        for day_num in range((week - 1) * 7 + 1, min(week * 7, 29)):
            note_path = self.notes_dir / f'{self._day_to_date(day_num).isoformat()}.md'
            if note_path.exists():
                with open(note_path, 'r', encoding='utf-8') as f:
                    week_notes.append((day_num, f.read()))

        # Build report
        lines = [f'# Weekly Report — Week {week}\n']
        lines.append(f'**Learner:** {self.get_name()}')
        lines.append(f'**Period:** Week {week} of 4')
        lines.append(f'**Days covered:** {len(week_notes)}\n')

        # Aggregate scorecard
        lines.append('## Scorecard Summary\n')
        all_scores = {}
        for day_num, content in week_notes:
            scores = get_scorecard(day_num)
            for area, score in scores.items():
                if area not in all_scores:
                    all_scores[area] = []
                all_scores[area].append(score)

        for area, scores in all_scores.items():
            pass_count = scores.count('Pass')
            unscored_count = scores.count('Unscored')
            pass_count = scores.count('Pass')
            moderate_count = scores.count('Moderate')
            fail_count = scores.count('Fail')
            trend = '\u2191' if pass_count > fail_count else '\u2193' if fail_count > pass_count else '\u2192'
            lines.append(f'- **{area}:** {pass_count} Pass / {moderate_count} Moderate / {fail_count} Fail / {unscored_count} Unscored {trend}')

        # Codex gates
        lines.append('\n## Codex Gate Status\n')
        last_day = max(d for d, _ in week_notes) if week_notes else week * 7
        gates = get_codex_gates(last_day)
        for gate, status in gates.items():
            icon = '✅' if status == 'Yes' else '❌'
            lines.append(f'- {icon} {gate}')

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print(f'  ✅ Created report: {report_path.name}')
        return report_path

    def _day_to_date(self, day_number: int) -> date:
        """Convert a curriculum day number to a calendar date."""
        working_days = 0
        current = self.start_date
        while working_days < day_number:
            if current.weekday() < 5:
                working_days += 1
            if working_days < day_number:
                current += timedelta(days=1)
        return current

    def archive_completed(self, days_range: tuple[int, int]) -> list[Path]:
        """Move completed notes/evidence/reports to archive/."""
        return sync_to_archive(self.action_dir, days_range)
