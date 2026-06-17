import json
from pathlib import Path

ok = True

for path in sorted(Path('.').rglob('*.json')):
    if '.git' in path.parts:
        continue
    try:
        json.loads(path.read_text(encoding='utf-8'))
        print(f'OK {path}')
    except Exception as exc:
        ok = False
        print(f'BAD {path}: {exc}')

raise SystemExit(0 if ok else 1)
