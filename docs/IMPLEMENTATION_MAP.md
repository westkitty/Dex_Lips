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
