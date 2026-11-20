#!/usr/bin/env python3
"""Verify this experiment's checked-in source/fixture integrity, no external dependencies."""
import hashlib
import json
from pathlib import Path

root=Path(__file__).resolve().parent
manifest=json.loads((root/'MANIFEST_SHA256.json').read_text(encoding='utf-8'))
assert len(manifest['files'])>=10
for info in manifest['files']:
    p=root/info['path']
    assert p.is_file(), f'Missing: {p}'
    data=p.read_bytes()
    assert len(data)==info['bytes'], f'Length mismatch: {p}'
    assert hashlib.sha256(data).hexdigest()==info['sha256'], f'Hash mismatch: {p}'
assert not list(root.rglob('*.pem')) and not list(root.rglob('*.key'))
print(f'PASS: {len(manifest["files"])} immutable proof items; non-manifest integration files are not runtime-tested')
