# QQQ / Performance / Recursive Repair — Evidence Ledger

Date of pass: 2026-11-19 America/Detroit (2026-11-20 UTC). Target `westkitty/Dex_Lips`, baseline commit `0d40a3de2747f27cd3a9d2912115a6212e51346c` (observed remote `main` head before repair).

## Scope and correction ledger

- **CORR-01 — NO APPLICATION CALLER (PARTIALLY VERIFIED):** Baseline contained only `proof_render.py` and a CLI smoke test. Added `app.py` with inputs, cue editor, rig packaging, source placement, keyframe text, local rendering, and MP4/receipt downloads. Gradio 6.5.1 was started locally; HTTP GET `/` returned 200. Browser widget interaction on actual Android not verified.
- **CORR-02 — NO SPEECH-ANALYSIS BRIDGE (IMPLEMENTED, REAL PROVIDER BLOCKED):** Added `src/dex_lips/speech.py`; normalizes actual audio through FFmpeg and runs the documented Rhubarb CLI with recognizer, optional dialog, and validated JSON. Tested subprocess wiring with a fake Rhubarb executable; **no real Rhubarb binary was available**. Missing executable fails closed; no automatic recognition claim.
- **CORR-03 — ONLY SYNTHETIC RIGS ACCEPTED (VERIFIED):** Added explicit user-approved noncanonical rig upload as bounded PNG ZIP, source-hash binding, path traversal/symlink controls, and stable failure states. The canonical Tiger SHA-256s are still blocked without authorized reference registration. User consent to artwork rights is required.
- **CORR-04 — HOT-LOOP/DOUBLE-MUX WORK (MEASURED):** Replaced two-step encode/mux with single FFmpeg process, bounded sprite transform cache (64), binary search over cue endpoints and forward-only keyframe interpolation. Streaming frames remain bounded; temp stderr avoids deadlock.
- **CORR-05 — OVERSIZED MEDIA CRASH/REJECTION (VERIFIED):** Resizes portrait or landscape media into even dimensions within 1280×720 without rewriting the original. Validates raw image dimensions before decoding; caps rig/cues/keyframe sizes and image sprites.
- **CORR-06 — ORIGINAL VIDEO MOUTH DOUBLING (PARTIALLY VERIFIED):** Adds explicit no-double-mouth acknowledgment for videos. Actual background mouth removal, occlusion and automatic motion tracking are NOT IMPLEMENTED. Manual keyframes only.
- **CORR-07 — SHALLOW TESTS (VERIFIED FOR BOUNDED SCOPE):** Added actual WAV speech+manual cue integration, malicious ZIP and unapproved canon rejection, video render, portrait source preservation, a fake Rhubarb CLI test, and all previous source SHA checks. The adapter test is intentionally not a recognition-quality proof.

## Matched local performance evidence

Run using same isolated Linux container, Python 3.13.5, Pillow 12.3.0, FFmpeg with libx264, 640×360, 6 seconds, 24 fps, 144 frames, 200×120 sprite artwork, 24 cues, original baseline script `bench_dex_lips.py` against extracted pre-repair ZIP and modified source. Five consecutive timed renders per route, same input generation and validation. Values in seconds (including FFmpeg encode and output probe):

| Route | BEFORE times | AFTER times | Median BEFORE | Median AFTER | Change |
|---|---|---|---:|---:|---:|
| Still image | 0.7242, 0.9310, 0.8769, 0.7932, 0.6483 | 0.5039, 0.7132, 0.6988, 0.6324, 0.5044 | 0.7932 | 0.6324 | 20.3% faster |
| Moving video | 1.0222, 1.0172, 1.0141, 1.0632, 0.9498 | 0.8455, 0.7138, 0.6419, 0.6392, 0.6617 | 1.0172 | 0.6617 | 34.9% faster |

Measurements are **local disposable container results**, NOT MacBook, Big Mac, cloud-hosted or Android measurements. Disk/memory and long-session use not benchmarked. The new codec compression preset and rendering blend can yield minor pixel-level variation; compare output visuals before treating this as lossless pixel-equivalent encoding.

## Verified runtime smoke

- `python3 scripts/verify_seed.py`: exact original JPEG reference SHA-256s match.
- `python3 -m unittest discover -s tests -v`: 19 passed after portrait-size correction (Pillow, ffmpeg/ffprobe and optional espeak available).
- `PYTHONPATH=src python3 scripts/proof_smoke.py`: two H.264/AAC synthetic 2-second outputs; full FFmpeg decodes successful.
- `app.build()` created 40 Gradio components. `build().launch(127.0.0.1:7869, share=False)` served HTTP 200 with title Dex_Lips.
- Real espeak synthetic spoken WAV + manually authored mouthCues + PNG sprite ZIP -> H.264/AAC MP4 with receipt; genuine Rhubarb phoneme-to-mouth alignment UNVERIFIED.
- Moving source video + user-acknowledged neutral mouth + keyframes + manually authored cues -> decodable MP4.

## Residual requirement contract

- **T1 human portrait**: can run only via user-supplied approved rig/manual cues; neural portrait inference UNAVAILABLE/UNVERIFIED at $0.
- **T2 human existing video**: same deterministic rig path; neural replacement UNAVAILABLE/UNVERIFIED; preexisting mouth removal not automatic.
- **T3 nonhuman still**: approved noncanonical rig and manual cue workflow verified; source Tiger images blocked pending approved mouth reference.
- **T4 moving nonhuman**: keyframed overlay verified on synthetic video; real mouth removal/tracking with turns/occlusion NOT VERIFIED.
- **Actual Rhubarb speech recognition, cloud eligibility, Android touch QA**: BLOCKED/UNVERIFIED; do not describe the whole original app as complete.

## Safeguards

- No paid APIs, GPU rental, external user-media upload, or model download invoked.
- Repo retains canonical full-body Tiger image and provisional sheet as immutable byte-identical references; no new canonical art was created.
- UI defaults localhost only. User media is staged into Dex_Lips-specific temporary directories with bounded sizes; expired jobs can be removed only under the own scratch root.
- Do not publish a Hugging Face Space without separate authority and verified zero-spend eligibility.
