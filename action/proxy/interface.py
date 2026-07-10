"""
action/proxy/interface.py
Abstract base class for learner behavior in action/.

The dummy implementation satisfies this today.
The real learner web interface will implement this when live.
Both produce the same output: notes, evidence, reports.

SWAP INSTRUCTIONS:
    When the real learner web interface is ready:
    1. Create action/proxy/web_interface.py implementing LearnerProxy
    2. In action/proxy/__init__.py, change:
         ActiveLearner = DummyLearner  →  from .web_interface import WebLearner as ActiveLearner
    3. Everything downstream (build_data.py, dashboard, archive) stays unchanged.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class LearnerProxy(ABC):
    """
    Interface contract for learner behavior in action/.

    Every method produces artifacts that build_data.py can parse
    and the dashboard can render. The contract is format-based:
    if the output matches the expected markdown structure, it works.
    """

    @abstractmethod
    def get_name(self) -> str:
        """Return the learner's display name."""

    @abstractmethod
    def generate_daily_note(self, date: str, day_number: int) -> Path:
        """
        Generate a daily note for the given date and day.
        Must follow the template format parseable by build_data.py's parse_note().

        Args:
            date: ISO date string (YYYY-MM-DD)
            day_number: Curriculum day number (1-28)

        Returns:
            Path to the created note file.
        """

    @abstractmethod
    def generate_evidence(self, day_number: int, evidence_type: str) -> Path:
        """
        Generate an evidence artifact.

        Args:
            day_number: Curriculum day number
            evidence_type: e.g. 'PT1', 'PT2', 'validation', 'handoff'

        Returns:
            Path to the created evidence file.
        """

    @abstractmethod
    def generate_weekly_report(self, week: int) -> Path:
        """
        Generate a weekly scorecard or readiness report.

        Args:
            week: Week number (1-4)

        Returns:
            Path to the created report file.
        """

    @abstractmethod
    def get_curriculum_day(self, date: str) -> Optional[int]:
        """
        Given a date, return which curriculum day it maps to (1-28),
        or None if it's a weekend/holiday/not in cycle.
        """

    @abstractmethod
    def archive_completed(self, days_range: tuple[int, int]) -> list[Path]:
        """
        Move completed notes/evidence/reports to archive/.

        Args:
            days_range: (start_day, end_day) inclusive

        Returns:
            List of archived file paths.
        """
