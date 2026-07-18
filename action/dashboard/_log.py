"""
action/dashboard/_log.py
Structured logging for the MUE dashboard build pipeline and review server.

Provides a simple severity-based logging function (stdlib only) that:
  - Timestamps every message
  - Tags severity levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - Routes errors to stderr, everything else to stdout
  - Supports optional structured context (key=value pairs)

Usage:
    from _log import log

    log('INFO', 'Rebuilding data.json', notes=42, evidence=5)
    log('ERROR', 'Failed to parse note', file='2026-07-18.md')
"""

import sys
from datetime import datetime


# Minimum severity level to display: 0=DEBUG, 1=INFO, 2=WARNING, 3=ERROR, 4=CRITICAL
_MIN_LEVEL = 1  # INFO and above by default

_SEVERITY = {
    'DEBUG': 0,
    'INFO': 1,
    'WARNING': 2,
    'ERROR': 3,
    'CRITICAL': 4,
}


def set_min_level(level_name: str) -> None:
    """Set the minimum severity level for logging.
    Args:
        level_name: One of 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    """
    global _MIN_LEVEL
    _MIN_LEVEL = _SEVERITY.get(level_name.upper(), 1)


def log(severity: str, message: str, **context) -> None:
    """Emit a structured log entry.

    Args:
        severity: Severity level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Human-readable log message
        **context: Optional key=value pairs for structured context
    """
    level = _SEVERITY.get(severity.upper(), 1)
    if level < _MIN_LEVEL:
        return

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    tag = severity.upper().ljust(8)

    if context:
        ctx_str = ' | ' + ' '.join(f'{k}={v}' for k, v in sorted(context.items()))
    else:
        ctx_str = ''

    line = f'[{timestamp}] [{tag}] {message}{ctx_str}'

    if level >= 3:  # ERROR or CRITICAL → stderr
        print(line, file=sys.stderr, flush=True)
    else:
        print(line, flush=True)
