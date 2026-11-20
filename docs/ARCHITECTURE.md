# Architecture and implementation boundaries

## Proposed small-surface architecture

- `web/`: one lightweight HTML/JS UI or Gradio custom frontend for upload, canvas mouth-rig edit, live timeline, and preview.
- `server/`: Python API/Gradio controller with explicit job state machine: IMPORTED -> VALIDATED -> CUED -> RIGGED -> PREVIEWED -> RENDERED -> VERIFIED -> EXPORTED; FAILED/WAITING_FOR_RIG state.
- `engine/visemes/`: Rhubarb runner (CPU, output JSON); deterministic cue validation; optional manual cue editor when Rhubarb is unavailable. Never invent speech recognition success.
- `engine/rig/`: source-invariant shape overlays, anchoring, masks, transformations, occlusion order, interpolation, 2D render.
- `engine/video/`: FPS-aware frame decode/compose, verified FFmpeg output with original-quality dialogue audio and bounded temporary files.
- `engine/neural/`: optional and feature-flagged MuseTalk (existing video) and SadTalker (portrait) adapters activated only when free hosted capacity and account entitlement are proven. No proprietary paid fallback.
- `tests/`: focused unit tests plus runnable acceptance fixtures and honest evidence receipts; include visual/manual checks for actual sources.

## Routing

- Human-like face still -> neural portrait adapter if accessible for $0; otherwise ask for manual rig or mark blocked.
- Human-like face video -> neural video adapter if accessible for $0; otherwise manual mouth rig.
- Nonhuman or stylized still -> deterministic visemes and explicit approved mouth art; never create unapproved canonical mouth geometry silently.
- Nonhuman/stylized video -> manual keyframed anchors and optional tracker **with per-frame track confidence**; fall back to manual anchor corrections on drift; don't promise fully automatic profile tracking.

## File/state contracts

See `schemas/rig.schema.json`, `schemas/job.schema.json`, `examples/`. Files kept in the repo are small, nonsensitive sample configs only; user media and model weights are ignored.

## Build decision gates

1. Verify source artwork SHA256 and repository identity before programming.
2. Implement deterministic rig pipeline to actual export FIRST; it is the only hard $0 production path.
3. Verify user-approved rig asset availability; currently none exist for Tiger. Do not fabricate approval.
4. Test short image+audio export with a synthetic neutral rig.
5. Test existing-video compositing with manual anchor track; preserve source audio only when desired, otherwise mute/replace explicitly.
6. Only then attempt hosted neural adapters, and only on a guaranteed $0 account/run.
7. Document actual rendered artifacts, QA, quotas, codecs, and browser compatibility. Stop cleanly when unproven.

## Feasibility notes

- Source image alone cannot yield a fully authoritative set of novel character mouth drawings. This requires explicit art authoring or subsequent user-approved visual references.
- Exact talking-face model compatibility with free ZeroGPU and private-reference isolation is unverified.
- A web browser does not guarantee MP4/H.264 encoding; use verified FFmpeg output on an eligible server, or provide a transparent fallback.
