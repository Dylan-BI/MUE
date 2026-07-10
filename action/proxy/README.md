# Dummy Learner Proxy — MUE

> Simulates a learner progressing through the 28-day MUE curriculum.
> Produces notes, evidence, and reports that the dashboard and build pipeline understand.

## What It Does

The proxy generates realistic daily notes, proof task evidence, and weekly reports
that follow the exact format expected by `build_data.py` and the dashboard. It
reads the curriculum schedule from `curriculum.py` and the start date from
`learner_config.json`.

## Quick Start

```bash
# Generate today's note (auto-detects day number)
python action/proxy/run_proxy.py --today

# Generate notes for days 1-5 (Week 1)
python action/proxy/run_proxy.py --range 1-5

# Generate ALL 28 days with weekly reports and archive
python action/proxy/run_proxy.py --full-run

# Archive completed days (move to action/archive/)
python action/proxy/run_proxy.py --archive 1-14
```

## Architecture

```
action/proxy/
├── __init__.py          # Package exports — SWAP POINT for real interface
├── interface.py         # Abstract LearnerProxy contract
├── curriculum.py        # 28-day schedule data
├── dummy.py             # DummyLearner implementation
├── sync.py              # Archive sync logic
├── run_proxy.py         # CLI entry point
├── templates/
│   └── daily_note.py    # Note content builder
└── README.md            # This file
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `--today` | Generate today's note (auto-detects day number) |
| `--date YYYY-MM-DD N` | Generate note for specific date and day |
| `--range START-END` | Generate notes for a day range |
| `--archive START-END` | Archive completed days |
| `--cycle START-END` | Generate + archive for a range |
| `--full-run` | Generate all 28 days with reports and archive |

All commands auto-run `build_data.py` to refresh `data.json`.

## Configuration

Edit `action/learner_config.json` to set the start date:

```json
{
  "curriculum_start_date": "2026-07-10",
  "learner_name": "Your Name"
}
```

Set `curriculum_start_date` to `null` to auto-detect from Day 1 note.

## Swapping to the Real Interface

The proxy implements an abstract `LearnerProxy` interface. To replace it:

1. Create `action/proxy/web_interface.py` implementing `LearnerProxy`
2. In `action/proxy/__init__.py`, change:
   ```python
   # FROM:
   ActiveLearner = DummyLearner
   # TO:
   from .web_interface import WebLearner as ActiveLearner
   ```
3. Everything downstream (build_data.py, dashboard, archive) stays unchanged.

## How It Integrates

```
proxy generates notes/evidence → build_data.py reads → data.json → dashboard.html
proxy archives completed work → archive/ → build_data.py still reads archived notes
proxy generates reports → reports/ → aggregate_weekly.py / readiness reports
```
