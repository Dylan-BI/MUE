"""Diagnostic: test SMTP and write result to a file for review."""
import sys, os
from pathlib import Path

result_file = Path(__file__).parent / '_email_test_result.txt'

# Load .env
env_path = Path(__file__).parent / '.env'
if not env_path.exists():
    result_file.write_text('ERROR: .env file not found')
    sys.exit(1)

for line in open(env_path):
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        if k not in os.environ:
            os.environ[k] = v

# Check SMTP vars
smtp_host = os.environ.get('MUE_SMTP_HOST', '')
smtp_user = os.environ.get('MUE_SMTP_USER', '')
smtp_pass = os.environ.get('MUE_SMTP_PASS', '')
smtp_from = os.environ.get('MUE_SMTP_FROM', '')

lines = []
lines.append(f'MUE_SMTP_HOST={smtp_host}')
lines.append(f'MUE_SMTP_USER={smtp_user}')
lines.append(f'MUE_SMTP_PASS={"***" if smtp_pass else "(empty)"}')
lines.append(f'MUE_SMTP_FROM={smtp_from}')

if not smtp_host:
    lines.append('ERROR: SMTP_HOST not configured')
    result_file.write_text('\n'.join(lines))
    sys.exit(1)

# Now import and test
sys.path.insert(0, str(Path(__file__).parent))
try:
    from server import _send_email
    ok, err = _send_email(
        'monteretroion@gmail.com',
        'MUE Learner — SMTP Diagnostic',
        '<h1>SMTP Diagnostic</h1><p>Sent from _diag.py</p>'
    )
    lines.append(f'Send result: ok={ok}, err={err}')
except Exception as e:
    lines.append(f'Import/call error: {e}')

result_file.write_text('\n'.join(lines))
print('\n'.join(lines))
