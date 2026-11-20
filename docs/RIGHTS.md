# Rights and distribution

**Repository visibility: PUBLIC** (verified 2026-11-20). Older notes that call this a private repository are out of date.

## Project code license: UNDECIDED

No license has been chosen, so no rights are granted to others yet (default copyright). This is the owner's decision; no blanket MIT or other grant is inferred, and none applies to user artwork. **Owner action needed.**

## Character artwork

- **Tiger** (`assets/references/tiger_*.jpg`): user-supplied references. Ownership/licensing, third-party provenance and redistribution rights have not been independently verified. Do not license, train a model on, or bundle them in a public demo without separate permission. ⚠️ They are currently committed to this **public** repository, which conflicts with the original "do not rehost publicly" note — **owner decision needed** (keep, or remove from the repo and its history). Dex_Lips refuses to generate rigs from these exact files (SHA-256 lock).
- **Dexter**: the owner supplied and approved the "DEXTER 'Furious Little Stinkweasel' – Character Reference Sheet" for building a Dexter muzzle mouth set on **2026-11-20** (user-supplied, approved for this project). The file is **not yet in the repository** (the automated build could not access the private attachment), so no Dexter-derived art exists here. Planned path: `assets/reference/dexter/dexter_reference_sheet.png`. Dexter's likeness must only ever be cut/edited from that sheet, never invented.
- **Generic muzzle template** (`assets/mouth_sets/generic_muzzle/`) and the demo character in `demos/`: drawn procedurally by this repo's code; not derived from any character art.

## Third-party components

| Component | Use | License | Notes |
|---|---|---|---|
| Rhubarb Lip Sync 1.14.0 (Daniel S. Wolf) | automatic engine (external binary, not vendored) | MIT; bundled deps MIT/BSD/Boost/similar (see its LICENSE.md) | Linux zip SHA-256 `a9a9074862cff47b2d59b8bf399a678a3b0b74f9452ad6ad94cb292913dd8667` observed 2026-11-20 (no upstream digest published) |
| facebook/wav2vec2-lv-60-espeak-cv-ft @ `ae45363b` | second automatic engine (weights downloaded explicitly, not vendored) | Apache-2.0 (model card) | |
| facebook/wav2vec2-base-960h @ `22aad52d` | word-alignment *aid* for drafting eval references only (`eval/tools/`) | Apache-2.0 | not used at runtime |
| espeak-ng | dictionary pronunciations for drafting eval references only | GPL-3.0 (called as an external program, not linked or vendored) | not used at runtime |
| LibriSpeech test-clean (8 clips in `eval/clips/`) | evaluation audio + demo audio | CC BY 4.0 — Panayotov et al., ICASSP 2015, https://www.openslr.org/12 | attribution in `eval/manifest.json`, `eval/README.md`, `demos/README.md` |
| PyTorch, Transformers, huggingface_hub, OpenCV, Gradio, Pillow, NumPy | optional/runtime Python packages (not vendored) | BSD / Apache-2.0 / MIT-style | keep notices if redistributed |

MuseTalk, SadTalker and other talking-face models remain unevaluated and unused.
