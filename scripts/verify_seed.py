#!/usr/bin/env python3
"""Check source assets without dependencies or modifying them."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'assets/references/SOURCE_MANIFEST.json').read_text(encoding='utf-8'))
failures=[]
for asset in manifest['assets']:
 p=(ROOT/asset['path']).resolve()
 if ROOT not in p.parents: failures.append('path escapes repo: '+asset['path']); continue
 if not p.is_file(): failures.append('missing: '+asset['path']); continue
 digest=hashlib.sha256(p.read_bytes()).hexdigest()
 if digest!=asset['sha256']: failures.append('hash mismatch: '+asset['path'])
 if p.stat().st_size!=asset['byte_size']: failures.append('size mismatch: '+asset['path'])
 if p.read_bytes()[:3]!=b'\xff\xd8\xff': failures.append('not JPEG: '+asset['path'])
 if not p.name.endswith(('.jpg','.jpeg')): failures.append('JPEG wrong extension: '+asset['path'])
 print(f"{asset['role']}: {p.relative_to(ROOT)} size={p.stat().st_size} sha256={digest}")
if failures:
 print('FAIL:', ' | '.join(failures),file=sys.stderr); sys.exit(1)
print('PASS: all source references verified')
