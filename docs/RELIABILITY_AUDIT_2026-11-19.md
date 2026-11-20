# Dex_Lips: reliability audit and bounded proof (2026-11-19)

## Verdict

**NOT FULLY WORKING YET.** Seed integrity is verified and **synthetic cue-driven MP4 compositor** works with still-image and existing-video input under tested local disposable conditions. There is no validated speech-to-mouth automatic pipeline, browser editor, nonhuman mouth restoration, private hosted backend, or eligible free GPU deployment. The proof uses authored mouth-cue JSON with artificial audio; it is explicitly **not an end-to-end speech-sync demo**.

## Evidence and confirmation

- Private source: `westkitty/Dex_Lips`, original seed commit `ee5cca7780caaddbfd2e5b708795d1d86f431eaf`.
- Original canonical Tiger JPEG SHA-256 `098e017a4960e7eeda634ac58c3b2dafc7097f8af87cab439bfbb88d4c87d1e2`; provisional sheet `03fd4f144ebc005e70ce8e9e906da9979a94ebe1a6344982e49fcf2441e5a8b3` (preserved).
- Environment for this test: disposable container with Python 3, Pillow 12.3.0, FFmpeg and ffprobe; *not* MacBook or Big Mac.
- `python3 -m unittest discover -s tests -v` tests image hashes, schema loading, authority order, corrupt cues, source rig hashes, cannot use real Tiger reference as synthetic demo, still+video encoding.
- `PYTHONPATH=src python3 scripts/proof_smoke.py` creates separate 2.0s synthetic tone/audio and moving/non-moving synthetic nonhuman scenes; both output H.264 video/AAC audio and decode with FFmpeg. Receipts record output hash and **unverified audio-cue correspondence**.

## Confirmed issues and corrections

- **BUG-001 (high, fixed in spec):** Earlier documentation treated free CPU Basic Gradio Space creation as a default free hosting path. Official Hugging Face Spaces overview states ordinary Gradio/Docker compute Spaces require paid-plan eligibility, with a narrow free personal ZeroGPU exception. `docs/CLOUD_DEPLOYMENT.md`, README and Codex prompt now specify the conditional route: https://huggingface.co/docs/hub/spaces-overview.
- **BUG-002 (medium, fixed):** Seed test required literal `NOT BUILT` forever, creating a stale test as implementation progresses. Replaced with reference-authority manifest ordering test.
- **BUG-003 (high, partly mitigated):** Prior handoff contained no executable media proof and could pass seed tests without rendering anything. Added deterministic 2s still + moving-video compositing tests and clearly labeled the missing recognition stage.
- **BUG-004 (high, guard added):** A caller-controlled rig JSON `approved` flag could be forged, bypassing intended canonical art protection in an immature renderer. Proof compositor now permits only synthetic_demo sources, checks actual media SHA and rejects *all* bundled source-reference hashes. The final app must implement independent approval verification before real-character rendering.
- **BUG-005 (high, unresolved product feature):** For actual existing cartoon/animal footage with a visible moving mouth, alpha overlay can create a doubled mouth and fail identity preservation. Required per-frame neutral restoration/masking and confidence/fail states in the Codex prompt. The synthetic test video is intentionally mouth-free and does not prove repair.
- **BUG-006 (high, unresolved external dependency):** Rhubarb CLI and valid free hosted infrastructure not yet proven available in Codex target; tests currently use authored cue JSON only. Complete speech recognition/inference and deployment checks remain release-blocking.

## Required final-app release proof

1. Real spoken WAV analyzed by a permitted Rhubarb binary into JSON `mouthCues` (not manually fabricated), then used in a still image + audio MP4 with visible mouth motion matched to waveform/dialogue.
2. Same with existing video, including visible mouth replacement, tracked positions, perspective/occlusion and source-background preservation.
3. Repeat using actual user-approved nonhuman mouth sprites; no silent Tiger canon promotion.
4. Live browser UI tested on desktop and Android tablet, file upload limits, manual timing, previews and exports; no accidental public sharing or paid cloud service.
5. H.264/AAC decoding, duration, first/last frames, visual timeline sample and source-hash nonregression. Each unrun test marked UNVERIFIED rather than PASS.

## Current command sequence for Codex

```bash
python3 scripts/verify_seed.py
python3 -m unittest discover -s tests -v
# In a disposable environment with Pillow, ffmpeg, ffprobe (never auto-install weights on Macs):
PYTHONPATH=src python3 scripts/proof_smoke.py
```

This report does not certify deployment or finished app functionality.
