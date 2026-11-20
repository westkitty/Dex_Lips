# Proposed module map for Codex

```
app.py                         Gradio app shell and states
src/dex_lips/ingest.py         file type detection, duration/size limits, probes
src/dex_lips/cues.py           Rhubarb adapter, cue validation, manual edits
src/dex_lips/rig.py            2D mouth sprites, anchors, masks, transforms
src/dex_lips/track.py          video keyframes, interpolation, optional tracking
src/dex_lips/renderer.py       per-frame composite and FFmpeg encode/mux
src/dex_lips/jobs.py           session jobs, cache/temp cleanup, receipts
src/dex_lips/neural.py         opt-in, gated human neural adapters (conditional)
web/                          Gradio JS extension or small standalone editor
schemas/                      rig/job contracts (seed exists)
tests/                        unit, offline, and integration tests
```

Recommended implementation order: source invariant tests -> input path -> Rhubarb JSON -> rig/preview -> still 2D export -> moving-video keyframe compositing -> QA -> hosted neural adapters -> Drive optional. Do not build arbitrary cloud infrastructure. Thin interface first, actual media export before polish.

## Observed after 2026-11-19 QQQ pass

- `app.py` — working localhost Gradio render entry, manual cues, per-job source upload, video receipt download, and synthetic demo.
- `src/dex_lips/proof_render.py` — actual bounded still/video H.264/AAC compositor with one-pass encode and internal sprite cache; still no real visual mouth tracking or source mouth removal.
- `src/dex_lips/speech.py` — executable Rhubarb command-line bridge; binary not bundled and true spoken-phoneme alignment remains externally unverified.
- `src/dex_lips/jobs.py` — bounded ZIP mouth rig import, authorization guard, cleanup, sha/source binding.
- `tests/test_speech_jobs.py` — checks audio/manual output and protocol wiring; does not claim installed Rhubarb recognition.
- `requirements-ui.txt` — optional UI package requirements; do NOT install them automatically on Mac hardware under storage pressure.

The older proposed module map above is aspirational; many named modules do not yet exist. Do not recreate existing code solely to match those old filenames.
