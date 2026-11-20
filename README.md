# Dex_Lips

**Status (2026-11-20): locally verified lip-sync studio with two real automatic mouth-timing engines. Not a cloud-hosted product.** New here? Read [START_HERE.md](START_HERE.md).

Dex_Lips takes a still image or existing video, a spoken audio recording, and mouth artwork generated in-app or separately authored by the user. It creates Rhubarb-compatible mouth cues (nine shapes X, A–H) and renders an H.264/AAC MP4. Automatic cues come only from an engine that actually ran on the audio:

- **[Rhubarb Lip Sync](https://github.com/DanielSWolf/rhubarb-lip-sync)** (installed binary, MIT), and/or
- a **wav2vec2 phoneme recognizer** ([facebook/wav2vec2-lv-60-espeak-cv-ft](https://huggingface.co/facebook/wav2vec2-lv-60-espeak-cv-ft), Apache-2.0), mapped to the same nine shapes.

If neither is available, automatic recognition is **BLOCKED**, never replaced by pretend cues.

## Accuracy (8 LibriSpeech clips, 24 s, reviewer-judged reference — not ground truth)

| Engine | Frame accuracy | Median boundary offset |
|---|---|---|
| Rhubarb 1.14.0 (pocketSphinx, audio only) | 55.6% | 40 ms |
| wav2vec2 phoneme recognizer (audio only) | 67.4% | 30 ms |

Full tables, per-shape confusion and the bias caveats: [ACCURACY.md](ACCURACY.md). Reproduce with `make accuracy`.

## What currently works

- Gradio studio bound to `127.0.0.1` (never `share=True`): click-on-picture mouth placement, draft mouth generation (source tracing, graphic shapes, generic muzzle template) with **jaw modes** (human, muzzle, beak, wide jaw), automatic cues from either engine, a **timing editor** (waveform with cue bands + editable cue table), **2-second preview**, configurable **crossfade** between shapes, MP4 + receipt.
- **Phone videos:** variable / 29.97 fps converted to a constant-rate working copy; mismatched audio/video lengths resolved by the user's **trim** or **pad** choice (listed in the receipt).
- Opt-in **mouth cover** (patch, or OpenCV inpaint) to hide an existing mouth in video; follows the anchor/keyframes (not tracking).
- Python and browser mouth tracing share one specification, enforced by an exact parity test that runs the real `site/assets/trace_core.js` under Node.
- Generic procedural **muzzle mouth set** in `assets/mouth_sets/generic_muzzle/`; engine demo MP4s in `demos/`.
- Input integrity checks, canonical-source SHA-256 refusal, no overwrite of originals, bounded per-job scratch processing; no paid APIs, telemetry or cloud uploads.

## What is not yet proven / not built

- **Dexter muzzle set:** the owner approved a Dexter reference sheet on 2026-11-20, but it has not been imported into the repo yet, so no Dexter art exists here. See `assets/mouth_sets/README.md` for the exact cells needed.
- Accuracy beyond 8 short read-English clips; noisy, emotional, cartoon or non-English voices are untested.
- Automatic mouth tracking or detection in video; neural talking-face models; persistent cloud hosting; Android tablet touch QA.
- Any approved mouth art for Shard-God Tiger. Tiger's canonical reference is locked and cannot be used as a rig source.
- **Code license: UNDECIDED** (owner decision; see `docs/RIGHTS.md`).

## Run in a disposable, authorized Python environment

Prerequisites: Python 3.11+, `ffmpeg` and `ffprobe` with H.264/AAC encoders, sufficient free temporary disk, and packages installed from `requirements-ui.txt`. This installs Gradio; **do not install on a storage-constrained MacBook or Big Mac by default**. Run in an available disposable machine or eligible free compute environment. No free hosted CPU Space is assumed.

```bash
python3 -m pip install -r requirements-ui.txt
python3 scripts/verify_seed.py
python3 -m unittest discover -s tests -v
python3 app.py
```

Open `http://127.0.0.1:7860` on the **same** machine. The app binds only to localhost and does **not** create a public or remote URL. The synthetic self-test is available under its own tab; it is visibly not speech recognition.

### Generate mouth assets directly in Dex_Lips

In the **Render** tab, upload a source image or video and select the approximate mouth location and region size. **Source soft** and **Source faceted** attempt to isolate the mouth silhouette within that user-selected box, retaining the painted source pixels, asymmetry and edge shape while resizing that exact sampled silhouette into X/A-H poses. A translucent green region preview shows which pixels were extracted; open-D preview shows the resulting overlay. For unusually bright mouths on dark figures, choose the **Light** contrast setting; for dark mouths choose **Dark**; **Auto** attempts both. If the contour cannot be isolated, generation **fails visibly**; it never silently substitutes generic anatomy. Choose legacy **Soft** or **Faceted** explicitly for simple graphics when the image lacks a distinct visible mouth. Then click **Generate draft mouth assets from source**. The app samples color near the indicated mouth, constructs **nine separate editable transparent PNGs** (X, A–H), previews the open D pose over your original, and produces a source-hash-bound ZIP that is filled into the render input automatically. You can download the ZIP and edit the sprites in any ordinary painting tool. No external art generator or paid API is needed.

This is a **deterministic source-conditioned draft**, **not** anatomy or identity understanding. Source tracing extracts a high-contrast connected mouth-shaped region of pixels **inside the user-defined box**, not a verified facial landmark, and deforms its pixels without synthesizing lips, teeth, tongue or a new head. It does **not** automatically find the mouth on the full face, model jaw articulation, remove a previously moving mouth in video, or certify that the mouth matches a particular creature. A drawn mouth that is extremely subtle, already shut, or partly hidden can fail to trace. A short preview and human review remain necessary. X is fully transparent to show the source's existing neutral/rest face. The user must visually review the preview and explicitly approve the generated mouth art **for this job** before rendering. For a canonical character such as Tiger, the bundled reference-image hash remains protected and the tool refuses unapproved automated rig generation from that reference. No canon approval is implied.

### Or supply your own mouth rig ZIP

Alternatively, supply separately drawn transparent sprites in one ZIP:

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

1. Press **Analyze the actual audio** (Rhubarb or wav2vec2 must be installed; otherwise it reports BLOCKED); review the cues in the timing editor, or
2. Paste real/hand-edited Rhubarb-style `mouthCues` JSON (`examples/mouthCues.example.json` shows the format).

For moving footage add time-keyframed mouth anchors. The existing mouth must already be neutral/masked or it will appear beneath the overlay; the app blocks video export without acknowledgement. Press **Render verified MP4**, inspect the downloadable clip, and review the JSON receipt for exact limitations.

## Proof commands

```bash
python3 scripts/verify_seed.py
python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 scripts/proof_smoke.py
make accuracy        # rewrites ACCURACY.md from eval/ (runs whichever engines are installed)
```

`proof_smoke.py` is an authored-cue compositor test using artificial tones, **not** a phonetic lip-sync test. The spoken-voice fixture in the suite uses actual `espeak` voice audio where available but manually defined mouth cues. The Rhubarb stub test exercises wiring only; `tests/test_engines_eval.py` additionally runs the **real** Rhubarb binary (skipped if it is not on PATH; CI installs it) and the wav2vec2 engine (skipped unless the model is cached) on real LibriSpeech speech. Accuracy: `make accuracy`.

## Project authority and sources

- Canonical primary: `assets/references/tiger_original_canonical.jpg`, exact SHA-256 locked in `assets/references/SOURCE_MANIFEST.json`.
- **Not canon:** `assets/references/tiger_expressions_provisional.jpg`. It does not authorize elongated head geometry, pupils or human facial anatomy.
- See `OPERATIONAL_STATE.md`, `Dex_Lips_bible.md`, `docs/ACCEPTANCE_TESTS.md`, `docs/QQQ_PERFORMANCE_REPAIR_2026-11-19.md`, and `docs/SOURCE_REFERENCES.md`.
- Codex handoff: `prompts/CODEX_BUILD_PROMPT.md` is for finishing the remaining capabilities, not rebuilding the verified compositor.

**Cost:** $0 for code/runtime in the disposable test environment, with no paid calls. Free production cloud hosting is **not** promised. Hugging Face now requires paid-plan access for ordinary new Gradio/Docker compute Spaces; free ZeroGPU creation is conditional. GitHub repository visibility is PUBLIC (verified 2026-11-20). The Pages artifact contains only the purpose-built browser studio; bundled canonical image references and private working media are excluded from the public Pages artifact.

## Browser mouth rig studio — GitHub Pages

**Site:** https://westkitty.github.io/Dex_Lips/

The static `site/` application supports browser-local still/image/video-frame import; manually positioned source-pixel mouth contour tracing (soft/faceted/dark/light); nine separately exportable transparent PNG sprites (X, A–H); cue JSON visual preview with local audio; source SHA-256 and bundled-reference hash refusal; preview, per-job draft review, and a ZIP containing PNGs and an unapproved, source-bound `rig.json`. The original image stays local and unchanged.

**Not hosted on Pages:** the Python/Gradio renderer, Rhubarb subprocess speech recognition, mouth removal/tracking, canonical image approval or H.264/AAC MP4 export. Use the separate verified Python/FFmpeg studio to produce MP4 from the reviewed rig. No character art, audio, or video is uploaded to the Pages backend (there is no backend).

GitHub Actions publishes only `site/`. The test workflow runs Chromium image-to-PNG/ZIP exercises, source hash checks, fail-closed tracing tests, and a mobile width check. Production deployment [run 44731970189](https://github.com/westkitty/Dex_Lips/actions/runs/44731970189) reported **SUCCESS** on commit `c43c2c541d021b8ebcefee6575bc57438fad7ca0` and emitted the URL above. External HTTP readback from this assistant's network was unavailable at the time of the run; do not mistake the deployment receipt for cross-browser/live-device QA.

## Experimental browser WASM challenger

A separate, non-production research implementation is in [`experiments/browser-wasm/`](experiments/browser-wasm/README.md): genuine Rhubarb WASM speech cues and H.264/AAC MP4 on synthetic still and moving sources, with pinned npm packages and external licensing documented. The full Android test, real footage masking, robust memory behavior, and same-machine performance comparison are not yet proven. The verified Python/FFmpeg renderer remains the default; this experiment is not an automatic fallback or a public application.
