# Drive handoff and archive plan

The requested source project is mirrored as a ZIP or folder under a user-owned Google Drive `Dex_Lips` destination. The GitHub repo is the versioned code source of truth; Google Drive holds independently retrievable source packets, character reference originals, and eventual output archives.

## Seed package expected

`Dex_Lips_seed_2026-11-19.zip` — file tree, immutable source images, source manifest, Codex build prompt, specs and proof scripts. The archived seed is not yet a completed application.

## Later production uploads

- `Dex_Lips/Character_Rigs/<character-id>/`: approved assets, rig config and immutable references; do not auto-promote drafts.
- `Dex_Lips/Jobs/<job-id>/`: optional job spec/timing/audio, only after privacy/retention approval.
- `Dex_Lips/Exports/<job-id>/`: finished video and checksum/QA evidence.

Avoid broad full-Drive OAuth or destructive sync. Use a scoped `drive.file` integration when available, create-only revisions, exact remote readback, no local deletion unless independently verified and explicitly authorized. Do not overwrite files named identically without a conflict policy.
