import json
with open('action/dashboard/data.json') as f:
    data = json.load(f)

# Check notes for any test-like entries
notes = data.get('notes', [])
print('Total notes:', len(notes))
for n in notes:
    id_val = n.get('id', '').lower()
    if 'tpl' in id_val or 'test' in id_val:
        print('  TEST-LIKE note:', n.get('id'))

# Check evidence
evidence = data.get('evidence', [])
print('Total evidence:', len(evidence))
for e in evidence:
    fn = e.get('filename', '').lower()
    if 'tpl' in fn or 'test' in fn:
        print('  TEST-LIKE evidence:', e.get('filename'))

# Check artifacts
artifacts = data.get('artifacts', {})
for cat, items in artifacts.items():
    for item in items:
        fn = item.get('filename', '').lower()
        if 'tpl' in fn or 'test' in fn:
            print('  TEST-LIKE in', cat, ':', item.get('filename'))