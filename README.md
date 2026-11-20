# Dex_Lips

**Status: locally verified deterministic lip-sync MVP, NOT a complete automatically recognizing or cloud-hosted product.**

Dex_Lips takes a still image or existing video, a spoken audio recording and the character's separately authored mouth-sprite artwork. It applies reviewed Rhubarb-compatible mouth cues and creates an H.264/AAC MP4. It also includes an optional adapter for the real [Rhubarb Lip Sync](https://github.com/DanielSWolf/rhubarb-lip-sync) CLI: if that executable is installed, it can derive cues from actual speech. If missing, automatic recognition is BLOCKED, not replaced by pretend cues.

## What currently works

- Gradio upload/edit/render interface, bound to `127.0.0.1` (not publicly shared) with actual MP4 output and receipt.
- User-authorized mouth sprites (PNG) packaged as a ZIP, user-adjustable placement, editable cue JSON, moving-video keyframes.
- Input integrity checks, canonical-source SHA-256 refusal, no overwrite of originals, per-job bounded scratch processing.
- Portrait/landscape stills and videos downsampled to even H.264 dimensions within 1280×720; original source files are never edited.
- Repeatable synthetic still and moving-video tests plus spoken-audio/manual-timing integration checks.
- Bounded CPU and temporary disk, bounded cue counts, and optional real Rhubarb `--exportFormat json` integration; no neural weights, paid APIs, telemetry or cloud uploads.

## What is not yet proven

- A genuine installed Rhubarb binary recognizing speech end to end on the target runtime (none installed in the last test container).
- Fully automatic existing-video mouth removal and tracking, webcam capture, neural human-avatar models, offline-browser-only MP4, persistent cloud hosting, or Android tablet touch-runtime QA.
- Any approved mouth art for Shard-God Tiger. Tiger's canonical reference is locked and cannot be used as a synthetic rig.

## Run in a disposable, authorized Python environment

Prerequisites: Python 3.11+, `ffmpeg` and `ffprobe` with H.264/AAC encoders, sufficient free temporary disk, and packages installed from `requirements-ui.txt`. This installs Gradio; **do not install on a storage-constrained MacBook or Big Mac by default**. Run in an available disposable machine or eligible free compute environment. No free hosted CPU Space is assumed.

```bash
python3 -m pip install -r requirements-ui.txt
python3 scripts/verify_seed.py
python3 -m unittest discover -s tests -v
python3 app.py
```

Open `http://127.0.0.1:7860` on the **same** machine. The app binds only to localhost and does **not** create a public or remote URL. The synthetic self-test is available under its own tab; it is visibly not speech recognition.

### Make your own mouth rig ZIP

Supply separately drawn transparent sprites in one ZIP:

```text
mouth_rig.zip
  X.png   (rest/closed)
  A.png   (closed pressure)
  B.png   (small opening)
  C.png   (medium opening)
  D.png   (wide opening)
  E.png   (rounded)
  F.png   (narrow rounded)
  G.png   (optional)
  H.png   (optional)
```

Rhubarb uses six core shapes A–F; X/G/H are optional to that algorithm, but **Dex_Lips currently requires X** for clean silence and at least one open shape. If you use the Rhubarb-generated cue route, provide every sprite actually referenced in the returned JSON. You can also include a `rig.json` with a shape-to-PNG map; it must be source-hash compatible. Never represent a user-approved generic rig as Starsilk canonical approval.

Upload your source, voice recording and ZIP, confirm you own or have authority to use the mouth sprites, then either:

1. Press **Analyze the actual audio** if Rhubarb is installed; review the generated cue JSON, or
2. Paste real/hand-edited Rhubarb-style `mouthCues` JSON (`examples/mouthCues.example.json` shows the format).

For moving footage add time-keyframed mouth anchors. The existing mouth must already be neutral/masked or it will appear beneath the overlay; the app blocks video export without acknowledgement. Press **Render verified MP4**, inspect the downloadable clip, and review the JSON receipt for exact limitations.

## Proof commands

```bash
python3 scripts/verify_seed.py
python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 scripts/proof_smoke.py
```

`proof_smoke.py` is an authored-cue compositor test using artificial tones, **not** a phonetic lip-sync test. The spoken-voice fixture in the suite uses actual `espeak` voice audio where available but manually defined mouth cues. The Rhubarb CLI adapter's fake binary test exercises wiring only, **not** recognition accuracy. Do not call automatic speech-to-mouth sync verified until a real Rhubarb binary and representative voice recording pass.

## Project authority and sources

- Canonical primary: `assets/references/tiger_original_canonical.jpg`, exact SHA-256 locked in `assets/references/SOURCE_MANIFEST.json`.
- **Not canon:** `assets/references/tiger_expressions_provisional.jpg`. It does not authorize elongated head geometry, pupils or human facial anatomy.
- See `OPERATIONAL_STATE.md`, `Dex_Lips_bible.md`, `docs/ACCEPTANCE_TESTS.md`, `docs/QQQ_PERFORMANCE_REPAIR_2026-11-19.md`, and `docs/SOURCE_REFERENCES.md`.
- Codex handoff: `prompts/CODEX_BUILD_PROMPT.md` is for finishing the remaining capabilities, not rebuilding the verified compositor.

**Cost:** $0 for code/runtime in the disposable test environment, with no paid calls. Free production cloud hosting is **not** promised. Hugging Face now requires paid-plan access for ordinary new Gradio/Docker compute Spaces; free ZeroGPU creation is conditional. GitHub is private and code contains no user-uploaded working media.
