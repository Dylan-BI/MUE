#!/usr/bin/env python3
"""
action/dashboard/test_integration.py
Minimal integration test for the MUE dashboard build pipeline.

Run: python action/dashboard/test_integration.py

Tests:
1. build_data.py runs without errors
2. data.json is valid JSON
3. data.json passes schema validation
4. data.json passes smoke tests
5. review_server.py imports without errors
"""

import json
import os
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_SCRIPT = os.path.join(DASHBOARD_DIR, 'build_data.py')
DATA_JSON = os.path.join(DASHBOARD_DIR, 'data.json')
SCHEMA_JSON = os.path.join(DASHBOARD_DIR, 'data_schema.json')
VALIDATE_SCRIPT = os.path.join(DASHBOARD_DIR, 'validate_and_smoke.py')


def run_cmd(cmd, cwd=None):
    """Run command and return (success, stdout, stderr)."""
    result = subprocess.run(cmd, cwd=cwd or REPO_ROOT, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr


def test_build_runs():
    """Test 1: build_data.py runs without errors."""
    print('Test 1: build_data.py runs...')
    ok, out, err = run_cmd([sys.executable, BUILD_SCRIPT])
    if not ok:
        print(f'  FAIL: {err}')
        return False
    print('  PASS')
    return True


def test_data_json_exists():
    """Test 2: data.json exists after build."""
    print('Test 2: data.json exists...')
    if not os.path.exists(DATA_JSON):
        print('  FAIL: data.json not found')
        return False
    print('  PASS')
    return True


def test_data_json_valid():
    """Test 3: data.json is valid JSON."""
    print('Test 3: data.json is valid JSON...')
    try:
        with open(DATA_JSON, 'r') as f:
            json.load(f)
        print('  PASS')
        return True
    except json.JSONDecodeError as e:
        print(f'  FAIL: {e}')
        return False


def test_schema_validation():
    """Test 4: data.json passes schema validation."""
    print('Test 4: schema validation...')
    ok, out, err = run_cmd([sys.executable, VALIDATE_SCRIPT])
    if not ok:
        print(f'  FAIL: {err}')
        return False
    print('  PASS')
    return True


def test_review_server_imports():
    """Test 5: review_server.py imports without errors."""
    print('Test 5: review_server.py imports...')
    ok, out, err = run_cmd([sys.executable, '-c', 'import sys; sys.path.insert(0, "action/dashboard"); import review_server; print("OK")'])
    if not ok:
        print(f'  FAIL: {err}')
        return False
    print('  PASS')
    return True


def test_required_keys():
    """Test 6: data.json has all required top-level keys."""
    print('Test 6: required keys present...')
    required = ['generated', 'version', 'notes', 'evidence', 'summary', 'artifacts', 'page_artifacts']
    with open(DATA_JSON, 'r') as f:
        data = json.load(f)
    missing = [k for k in required if k not in data]
    if missing:
        print(f'  FAIL: missing keys: {missing}')
        return False
    print('  PASS')
    return True


def test_version_structure():
    """Test 7: version object has commit and timestamp."""
    print('Test 7: version structure...')
    with open(DATA_JSON, 'r') as f:
        data = json.load(f)
    version = data.get('version', {})
    if not isinstance(version, dict):
        print('  FAIL: version is not an object')
        return False
    if 'commit' not in version or 'timestamp' not in version:
        print('  FAIL: version missing commit or timestamp')
        return False
    print('  PASS')
    return True


def test_notes_structure():
    """Test 8: notes array has expected structure."""
    print('Test 8: notes structure...')
    with open(DATA_JSON, 'r') as f:
        data = json.load(f)
    notes = data.get('notes', [])
    if not isinstance(notes, list):
        print('  FAIL: notes is not a list')
        return False
    if notes:
        note = notes[0]
        required = ['id', 'date', 'day_number', 'classification', 'level']
        missing = [k for k in required if k not in note]
        if missing:
            print(f'  FAIL: note missing keys: {missing}')
            return False
    print('  PASS')
    return True


def main():
    """Run all integration tests."""
    print('=' * 60)
    print('MUE Dashboard Integration Tests')
    print('=' * 60)
    print()

    tests = [
        test_build_runs,
        test_data_json_exists,
        test_data_json_valid,
        test_schema_validation,
        test_review_server_imports,
        test_required_keys,
        test_version_structure,
        test_notes_structure,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f'  ERROR: {e}')
            failed += 1
        print()

    print('=' * 60)
    print(f'Results: {passed} passed, {failed} failed')
    print('=' * 60)

    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)