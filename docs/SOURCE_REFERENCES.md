# Source references and license notes

Verified research starting points (visited in conversation on **2026-11-19 America/Detroit**; links may change). These are **external references**, not vendored software or guaranteed runtime compatibility. Codex must inspect exact releases, code paths, dependency licenses, and current service rules before integration. Record current immutable commit IDs if any dependency is cloned or consumed.

1. **Rhubarb Lip Sync** — Daniel Wolf: https://github.com/DanielSWolf/rhubarb-lip-sync  — speech-driven 2D mouth cues, JSON output, C++/native CLI, MIT license. Documentation: https://github.com/DanielSWolf/rhubarb-lip-sync/blob/master/README.adoc  — `mouthCues: [{start,end,value}]`; shape X closed, A-F core, G/H optional. Do not assume unverified WASM forks are maintained or compatible.
2. **MuseTalk** — TMElyralab: https://github.com/TMElyralab/MuseTalk  — audio-driven human face inpainting in video; project indicates 4GB-VRAM test, but 8s video can take ~5 min on tested GPU. MIT source code; check weights, dependencies, and hosted service terms separately.
3. **SadTalker** — OpenTalker: https://github.com/OpenTalker/SadTalker  — human-style animated still portraits; Apache-2.0 project license, check third-party exceptions. Not a universal nonhuman solution.
4. **Hugging Face ZeroGPU and hosting policy** — official: https://huggingface.co/docs/hub/main/spaces-zerogpu and https://huggingface.co/docs/hub/spaces-overview . Reverified 2026-11-19: ordinary compute Gradio/Docker Space creation requires a paid plan, except eligible free accounts in good standing can create up to two ZeroGPU Gradio Spaces. Static Spaces are free but cannot run the Python/FFmpeg backend. Not an account eligibility verification. Do not mistake CPU Basic $0/hour hardware listing for free eligibility to create a compute Space.
5. **Gradio** — official guide: https://www.gradio.app/guides/quickstart  — web application UI option. Verify current minimum Python and framework versions.
6. **FFmpeg** — official: https://ffmpeg.org/documentation.html  — encode, remux, and examine MP4 output; pin version/installation method in actual runtime.
7. **Colab managed runtimes** — official FAQ: https://research.google.com/colaboratory/faq.html  — explicitly prohibits creating deepfakes. Do not use as a workaround for this lip-sync project.
8. **GitHub `gh` CLI** — official: https://cli.github.com/manual/gh_repo_create  — create a repository; verify authenticated owner/visibility before operations.
9. **Google Drive API scope** — official: https://developers.google.com/workspace/drive/api/guides/api-specific-auth  — `drive.file` preferred over broad access; production Drive automation requires explicit user authorization.

## User-provided visual assets

- `assets/references/tiger_original_canonical.jpg` (source original `1000233378.jpg`) — user-designated PRIMARY; SHA-256 recorded in `SOURCE_MANIFEST.json`.
- `assets/references/tiger_expressions_provisional.jpg` (uploaded as `1000233387.png` but contains JPEG bytes) — user-provided PROVISIONAL; SHA-256 recorded.

No consent or license to publish those images **publicly** is inferred. The repository is now PUBLIC (verified 2026-11-20), so their continued presence here is an open owner decision (see docs/RIGHTS.md). The character profile and artwork are not distributed as open-source media.

10. **Synthetic rendering proof source** — this repository's `src/dex_lips/proof_render.py`, `scripts/proof_smoke.py`, and `tests/test_proof_renderer.py`, verified in a disposable Python 3 / Pillow / FFmpeg environment 2026-11-19. This is original project code, not upstream Rhubarb audio recognition or final app implementation.
11. **Rhubarb Lip Sync 1.14.0** — https://github.com/DanielSWolf/rhubarb-lip-sync/releases/tag/v1.14.0 (MIT). Mouth-shape semantics used for the phoneme table: https://github.com/DanielSWolf/rhubarb-lip-sync#mouth-shapes
12. **wav2vec2 phoneme model** — https://huggingface.co/facebook/wav2vec2-lv-60-espeak-cv-ft (Apache-2.0), revision `ae45363bf3413b374fecd9dc8bc1df0e24c3b7f4`. Xu, Baevski, Auli, *Simple and Effective Zero-shot Cross-lingual Phoneme Recognition* (2021).
13. **LibriSpeech** — https://www.openslr.org/12 (CC BY 4.0), Panayotov et al., ICASSP 2015.
