"""Quick test: verify email sending works for tunnel notifications."""
import os, sys
from pathlib import Path

# Load .env manually
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    for line in open(env_path):
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            if k not in os.environ:
                os.environ[k] = v

# Test SMTP direct
from server import _send_email

ok, err = _send_email(
    'monteretroion@gmail.com',
    'MUE Learner — SMTP Test',
    '<h1>SMTP Test</h1><p>If you receive this, email works from the learner server.</p>'
)
print(f'Send result: ok={ok}, err={err}')
