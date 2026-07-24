"""Helper script to run sync-from-action.py and capture its output."""
import subprocess
import sys
import os

script = os.path.join(os.path.dirname(__file__), 'review', 'scripts', 'sync-from-action.py')
result = subprocess.run([sys.executable, script], capture_output=True, text=True, cwd=os.path.dirname(__file__))
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("RETURNCODE:", result.returncode)
