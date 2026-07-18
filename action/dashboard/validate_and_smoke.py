"""
action/dashboard/validate_and_smoke.py
data.json validation and smoke tests for CI/CD pipeline.

Usage:
    python action/dashboard/validate_and_smoke.py

Returns exit code 0 on success, 1 on failure.
"""

import json
import os
import sys

DATA_PATH = os.path.join(os.path.dirname(__file__), 'data.json')


def validate_structure(data):
    """Validate data.json has all required top-level keys and sub-structures."""
    errors = []

    # Required top-level keys
    required = ['generated', 'version', 'notes', 'evidence',
                'summary', 'artifacts', 'page_artifacts']
    for key in required:
        if key not in data:
            errors.append(f'Missing required key: {key}')

    # Version sub-keys
    if 'version' in data:
        for vk in ['commit', 'timestamp']:
            if vk not in data['version']:
                errors.append(f'Missing version.{vk}')

    # Notes structure
    notes = data.get('notes', [])
    if not isinstance(notes, list):
        errors.append('notes must be a list')
    elif notes:
        for i, n in enumerate(notes):
            if not isinstance(n.get('date'), str):
                errors.append(f'notes[{i}].date missing or invalid')
            if not isinstance(n.get('day_number'), (int, float)):
                errors.append(f'notes[{i}].day_number missing or invalid')

    # Summary structure
    summary = data.get('summary', {})
    for sk in ['total_days', 'evidence_count', 'learner_level']:
        if sk not in summary:
            errors.append(f'Missing summary.{sk}')

    return errors


def smoke_tests(data):
    """Run smoke tests to verify data.json is usable by the dashboard."""
    failures = []

    # File size sanity
    size = os.path.getsize(DATA_PATH)
    if size < 100:
        failures.append(f'data.json too small: {size} bytes')

    # Notes count
    n = len(data.get('notes', []))
    if n == 0:
        failures.append('No notes found in data.json')

    # Summary present
    s = data.get('summary', {})
    if not s:
        failures.append('summary missing')

    # Version present
    v = data.get('version', {})
    if not v.get('commit'):
        failures.append('version.commit missing')

    return failures


def main():
    if not os.path.exists(DATA_PATH):
        print(f'FAIL: data.json not found at {DATA_PATH}')
        sys.exit(1)

    with open(DATA_PATH, 'r') as f:
        data = json.load(f)

    print('=== data.json Structure Validation ===')
    errors = validate_structure(data)
    if errors:
        for e in errors:
            print(f'  FAIL: {e}')
        print('Result: VALIDATION FAILED')
        sys.exit(1)
    else:
        print('  PASS: All required keys present')
        print('Result: VALIDATION PASSED')

    print()
    print('=== data.json Smoke Tests ===')
    failures = smoke_tests(data)
    all_pass = True
    for name, value, cond, fail_msg in [
        ('File size', f'{os.path.getsize(DATA_PATH)} bytes', os.path.getsize(DATA_PATH) > 100, 'Too small'),
        ('Notes count', str(len(data.get('notes', []))), len(data.get('notes', [])) > 0, 'No notes'),
        ('Summary present', 'yes', bool(data.get('summary', {})), 'Missing'),
        ('Version present', 'yes', bool(data.get('version', {}).get('commit')), 'Missing commit'),
    ]:
        status = 'PASS' if cond else 'FAIL'
        if not cond:
            all_pass = False
            print(f'  [{status}] {name}: {value} -> {fail_msg}')
        else:
            print(f'  [{status}] {name}: {value}')

    if all_pass:
        print('Result: ALL SMOKE TESTS PASSED')
    else:
        print('Result: SOME SMOKE TESTS FAILED')
        sys.exit(1)

    print()
    print('data.json is valid and ready for deployment.')


if __name__ == '__main__':
    main()
