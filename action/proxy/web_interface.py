"""
action/proxy/web_interface.py
WebLearner — interactive learner interface for the 28-day MUE curriculum.

Implements the LearnerProxy interface as a swap-in replacement for DummyLearner.
Instead of fabricating dummy content, WebLearner accepts real learner input
through a content-staging mechanism that the web UI (Phases 2+) uses.

ARCHITECTURE:
    Web UI (Phases 2+)
        │  stages content via stage_note_content(), stage_evidence_content()
        ▼
    WebLearner.generate_daily_note() / generate_evidence()
        │  writes to action/notes/ or action/evidence/
        ▼
    Optionally triggers build_data.py → data.json → dashboard refresh

SWAP INSTRUCTIONS (in action/proxy/__init__.py):
    FROM:  ActiveLearner = DummyLearner
    TO:    from .web_interface import WebLearner as ActiveLearner

Everything downstream (build_data.py, dashboard, archive) stays unchanged
because the file format is identical.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from action.proxy.interface import LearnerProxy
from action.proxy.curriculum import (
    CURRICULUM, PROOF_TASKS, SCORE_AREAS, CODEX_GATES,
    get_classification, get_primary_track, get_level_for_day,
)
from action.proxy.templates.daily_note import build_note_content, get_scorecard, get_codex_gates
from action.proxy.sync import sync_to_archive, sync_evidence_to_archive


# ── Directory paths ──────────────────────────────────────────────────────────
ACTION_DIR = Path(__file__).resolve().parent.parent  # action/
NOTES_DIR = ACTION_DIR / 'notes'
EVIDENCE_DIR = ACTION_DIR / 'evidence'
REPORTS_DIR = ACTION_DIR / 'reports'
ARCHIVE_DIR = ACTION_DIR / 'archive'
CONFIG_PATH = ACTION_DIR / 'learner_config.json'
BUILD_SCRIPT = ACTION_DIR.parent / 'action' / 'dashboard' / 'build_data.py'


class WebLearner(LearnerProxy):
    """
    Interactive learner that accepts real input from the web UI.

    The web UI stages content via stage_note_content(), then calls
    generate_daily_note() which writes it to disk. If no content is
    staged, a minimal placeholder is created (graceful fallback).

    After every write, the build_data.py script can be triggered to
    refresh the reviewer dashboard.
    """

    def __init__(self, action_dir: Optional[Path] = None, auto_build: bool = True):
        """
        Args:
            action_dir: Path to action/ directory (default: auto-detect)
            auto_build: If True, run build_data.py after each write
        """
        self.action_dir = action_dir or ACTION_DIR
        self.notes_dir = self.action_dir / 'notes'
        self.evidence_dir = self.action_dir / 'evidence'
        self.reports_dir = self.action_dir / 'reports'
        self.auto_build = auto_build

        # ── Content staging ────────────────────────────────────────────
        # The web UI stages content here before calling generate methods.
        # Key: (date, day_number) for notes; (day_number, evidence_type) for evidence
        self._staged_notes: dict[tuple[str, int], dict] = {}
        self._staged_evidence: dict[tuple[int, str], dict] = {}

        # Load config
        self.config = self._load_config()
        self.start_date = self._resolve_start_date()

    # ── Config helpers ─────────────────────────────────────────────────────

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
        cfg_date = self.config.get('curriculum_start_date')
        if cfg_date:
            try:
                return datetime.strptime(cfg_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        for note_file in sorted(self.notes_dir.glob('*.md')):
            day = self._extract_day_from_note(note_file)
            if day == 1:
                try:
                    return datetime.strptime(note_file.stem, '%Y-%m-%d').date()
                except ValueError:
                    pass
        return date.today()

    def _extract_day_from_note(self, note_path: Path) -> Optional[int]:
        """Extract day number from a note file's content."""
        try:
            with open(note_path, 'r', encoding='utf-8') as f:
                content = f.read(500)
            m = re.search(r'Day\s*(\d+)', content)
            return int(m.group(1)) if m else None
        except OSError:
            return None

    def save_config(self, **overrides) -> dict:
        """Update learner_config.json with new values. Returns the merged config."""
        config = {**self.config, **overrides}
        try:
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            self.config = config
            if 'curriculum_start_date' in overrides:
                self.start_date = self._resolve_start_date()
        except OSError as e:
            print(f'  ⚠️ Could not save config: {e}')
        return config

    # ── Content staging (called by the web UI) ────────────────────────────

    def stage_note_content(self, date: str, day_number: int, fields: dict) -> None:
        """
        Stage content for a daily note before calling generate_daily_note().

        Args:
            date: ISO date string (YYYY-MM-DD)
            day_number: Curriculum day number (1-28)
            fields: Dictionary with note fields:
                - classification (str)
                - primary_track (str)
                - level (int)
                - what_learned (str)
                - evidence_produced (str)
                - what_remains (str)
                - next_step (str)
                - scorecard (dict[str, str]) — area → Pass/Moderate/Fail/Unscored
                - codex_gate (dict[str, str]) — gate → Yes/No
        """
        self._staged_notes[(date, day_number)] = fields

    def stage_evidence_content(self, day_number: int, evidence_type: str, fields: dict) -> None:
        """
        Stage content for an evidence artifact before calling generate_evidence().

        Args:
            day_number: Curriculum day number
            evidence_type: e.g. 'PT1', 'PT2', 'validation', 'handoff'
            fields: Dictionary with evidence fields (varies by type)
        """
        self._staged_evidence[(day_number, evidence_type)] = fields

    def clear_staged_content(self) -> None:
        """Clear all staged content."""
        self._staged_notes.clear()
        self._staged_evidence.clear()

    # ── LearnerProxy interface implementation ─────────────────────────────

    def get_name(self) -> str:
        """Return the learner's display name from config."""
        return self.config.get('learner_name') or 'Web Learner'

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
        """
        Write a daily note to action/notes/{date}.md.

        Uses staged content if available (set via stage_note_content()).
        Falls back to a minimal placeholder if nothing is staged.
        After writing, optionally triggers build_data.py.
        """
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        note_path = self.notes_dir / f'{date_str}.md'

        # Check if staged content exists
        staged = self._staged_notes.pop((date_str, day_number), None)

        if staged:
            content = self._build_note_from_fields(date_str, day_number, staged)
        else:
            # Graceful fallback: use DummyLearner's template content
            content = build_note_content(date_str, day_number)

        with open(note_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f'  ✅ Saved note: {note_path.name} (Day {day_number})')
        self._trigger_build()
        return note_path

    def generate_evidence(self, day_number: int, evidence_type: str) -> Path:
        """
        Write an evidence artifact to action/evidence/.

        Uses staged content if available (set via stage_evidence_content()).
        Falls back to a minimal placeholder if nothing is staged.
        After writing, optionally triggers build_data.py.
        """
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

        staged = self._staged_evidence.pop((day_number, evidence_type), None)

        if staged and staged.get('content'):
            # Use content provided by the web UI (raw file content or upload)
            filename = staged.get('filename', f'{evidence_type.lower()}_day{day_number}.md')
            evidence_path = self.evidence_dir / filename
            with open(evidence_path, 'w', encoding='utf-8') as f:
                f.write(staged['content'])
        elif staged and staged.get('sections'):
            # Build from structured sections
            filename = staged.get('filename', f'{evidence_type.lower()}_day{day_number}.md')
            evidence_path = self.evidence_dir / filename
            content = self._build_evidence_from_sections(evidence_type, staged['sections'])
            with open(evidence_path, 'w', encoding='utf-8') as f:
                f.write(content)
        else:
            # Graceful fallback: minimal placeholder
            evidence_path = self.evidence_dir / f'{evidence_type.lower()}_day{day_number}.md'
            if evidence_path.exists():
                print(f'  Evidence already exists: {evidence_path.name}')
                return evidence_path
            entry = CURRICULUM.get(day_number, {})
            focus = entry.get('focus', evidence_type)
            content = f'# {evidence_type}\n\n**Day {day_number} — {focus}**\n\nEvidence artifact for curriculum day {day_number}.'
            with open(evidence_path, 'w', encoding='utf-8') as f:
                f.write(content)

        print(f'  ✅ Saved evidence: {evidence_path.name} (Day {day_number})')
        self._trigger_build()
        return evidence_path

    def generate_weekly_report(self, week: int) -> Path:
        """
        Generate a weekly scorecard report from existing notes.

        Aggregates all notes in the given week and produces a summary.
        After writing, optionally triggers build_data.py.
        """
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        report_path = self.reports_dir / f'weekly-{self.start_date.year}-W{week:02d}.md'
        if report_path.exists():
            print(f'  Report already exists: {report_path.name}')
            return report_path

        week_notes = []
        for day_num in range((week - 1) * 7 + 1, min(week * 7, 29)):
            note_path = self.notes_dir / f'{self._day_to_date(day_num).isoformat()}.md'
            if note_path.exists():
                with open(note_path, 'r', encoding='utf-8') as f:
                    week_notes.append((day_num, f.read()))

        lines = [f'# Weekly Report — Week {week}\n']
        lines.append(f'**Learner:** {self.get_name()}')
        lines.append(f'**Period:** Week {week} of 4')
        lines.append(f'**Days covered:** {len(week_notes)}\n')

        lines.append('## Scorecard Summary\n')
        all_scores = {}
        for day_num, content in week_notes:
            scores = get_scorecard(day_num)
            for area, score in scores.items():
                all_scores.setdefault(area, []).append(score)

        for area, scores in all_scores.items():
            pass_c = scores.count('Pass')
            mod_c = scores.count('Moderate')
            fail_c = scores.count('Fail')
            unscored_c = scores.count('Unscored')
            trend = '↑' if pass_c > fail_c else ('↓' if fail_c > pass_c else '→')
            lines.append(f'- **{area}:** {pass_c} Pass / {mod_c} Moderate / {fail_c} Fail / {unscored_c} Unscored {trend}')

        lines.append('\n## Codex Gate Status\n')
        last_day = max((d for d, _ in week_notes), default=week * 7)
        gates = get_codex_gates(last_day)
        for gate, status in gates.items():
            icon = '✅' if status == 'Yes' else '❌'
            lines.append(f'- {icon} {gate}')

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        print(f'  ✅ Generated report: {report_path.name}')
        self._trigger_build()
        return report_path

    def archive_completed(self, days_range: tuple[int, int]) -> list[Path]:
        """
        Move completed notes/evidence/reports for a day range to archive/.

        Args:
            days_range: (start_day, end_day) inclusive

        Returns:
            List of archived file paths.
        """
        archived = sync_to_archive(self.action_dir, days_range)
        archived += sync_evidence_to_archive(self.action_dir, days_range)
        if archived:
            self._trigger_build()
        return archived

    # ── Internal helpers ──────────────────────────────────────────────────

    def _build_note_from_fields(self, date_str: str, day_number: int, fields: dict) -> str:
        """
        Build a daily note markdown string from structured form fields.

        The output format must match what build_data.py's parse_note() expects.
        """
        entry = CURRICULUM.get(day_number, {})
        classification = fields.get('classification', get_classification(day_number))
        primary_track = fields.get('primary_track', get_primary_track(day_number))
        level = fields.get('level', get_level_for_day(day_number))
        week_number = entry.get('week_number', (day_number - 1) // 7 + 1)
        required_artifact = fields.get('required_artifact', entry.get('required_artifact', ''))
        what_learned = fields.get('what_learned', '')
        evidence_produced = fields.get('evidence_produced', '')
        what_remains = fields.get('what_remains', '')
        next_step = fields.get('next_step', '')
        scorecard = fields.get('scorecard', get_scorecard(day_number))
        codex_gate = fields.get('codex_gate', get_codex_gates(day_number))

        # Build scorecard lines
        scorecard_lines = '\n'.join(
            f'{area}: {scorecard.get(area, "Unscored")}'
            for area in SCORE_AREAS
        )

        # Build codex gate lines
        gate_lines = '\n'.join(
            f'{gate}: {codex_gate.get(gate, "No")}'
            for gate in CODEX_GATES
        )

        # Build category tags from curriculum
        category_tags = ' · '.join(entry.get('tags', []))

        note = f"""# Daily Note — Day {day_number}

**Date:** {date_str}
**Classification:** {classification}
**Primary track:** {primary_track}
**Level:** {level}
**Week Number:** {week_number}
**Day {day_number}**
**Required Artifact:** {required_artifact}
**Category Tags:** {category_tags}

## What I learned today:
{what_learned}

## What evidence I produced:
{evidence_produced}

## What remains open:
{what_remains}

## Next narrow step:
{next_step}

## Scorecard:
{scorecard_lines}

## Codex gates:
{gate_lines}
"""
        return note

    def _build_evidence_from_sections(self, evidence_type: str, sections: dict) -> str:
        """
        Build an evidence markdown file from structured sections.

        Args:
            evidence_type: e.g. 'PT1', 'PT2', 'validation'
            sections: Dict of section heading → content

        Returns:
            Markdown string
        """
        lines = [f'# {evidence_type}', '']
        for heading, content in sections.items():
            lines.append(f'## {heading}')
            lines.append(str(content))
            lines.append('')
        return '\n'.join(lines)

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

    def _trigger_build(self) -> None:
        """Run build_data.py to regenerate data.json for the dashboard."""
        if not self.auto_build:
            return
        try:
            build_script = self.action_dir / 'dashboard' / 'build_data.py'
            if build_script.exists():
                result = subprocess.run(
                    [sys.executable, str(build_script)],
                    cwd=self.action_dir.parent,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    print(f'  🔄 Dashboard data rebuilt')
                else:
                    err = result.stderr.strip().split('\n')[-1] if result.stderr else 'unknown'
                    print(f'  ⚠️ build_data.py: {err}')
        except Exception as e:
            print(f'  ⚠️ Could not trigger build: {e}')

    # ── Web UI helpers (used by Phases 2+) ────────────────────────────────

    def list_notes(self) -> list[Path]:
        """Return all note files sorted by date."""
        return sorted(self.notes_dir.glob('*.md'))

    def list_evidence(self) -> list[Path]:
        """Return all evidence files sorted by name."""
        return sorted(self.evidence_dir.glob('*.*'))

    def list_reports(self) -> list[Path]:
        """Return all report files sorted by name."""
        return sorted(self.reports_dir.glob('*.md'))

    def get_curriculum_day_info(self, day_number: int) -> dict:
        """Return the curriculum entry for a given day."""
        return CURRICULUM.get(day_number, {})

    def get_all_curriculum(self) -> dict:
        """Return the full 28-day curriculum schedule."""
        return dict(CURRICULUM)

    def get_proof_tasks(self) -> dict:
        """Return proof task definitions."""
        return dict(PROOF_TASKS)

    def get_scorecard_areas(self) -> list:
        """Return the list of scorecard areas."""
        return list(SCORE_AREAS)

    def get_codex_gates_list(self) -> list:
        """Return the list of Codex gates."""
        return list(CODEX_GATES)
