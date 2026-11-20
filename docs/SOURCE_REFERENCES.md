# Source references and license notes

Verified research starting points (visited in conversation on **2026-11-19 America/Detroit**; links may change). These are **external references**, not vendored software or guaranteed runtime compatibility. Codex must inspect exact releases, code paths, dependency licenses, and current service rules before integration. Record current immutable commit IDs if any dependency is cloned or consumed.

1. **Rhubarb Lip Sync** — Daniel Wolf: https://github.com/DanielSWolf/rhubarb-lip-sync  — speech-driven 2D mouth cues, JSON output, C++/native CLI, MIT license. Documentation: https://github.com/DanielSWolf/rhubarb-lip-sync/blob/master/README.adoc  — `mouthCues: [{start,end,value}]`; shape X closed, A-F core, G/H optional. Do not assume unverified WASM forks are maintained or compatible.
2. **MuseTalk** — TMElyralab: https://github.com/TMElyralab/MuseTalk  — audio-driven human face inpainting in video; project indicates 4GB-VRAM test, but 8s video can take ~5 min on tested GPU. MIT source code; check weights, dependencies, and hosted service terms separately.
3. **SadTalker** — OpenTalker: https://github.com/OpenTalker/SadTalker  — human-style animated still portraits; Apache-2.0 project license, check third-party exceptions. Not a universal nonhuman solution.
4. **Hugging Face ZeroGPU** — official: https://huggingface.co/docs/hub/main/spaces-zerogpu  — free accounts **in good standing** can host up to two ZeroGPU Spaces, with daily free GPU quota subject to queues and policy. The claim is not an entitlement verification for this user's account. Official Spaces overview: https://huggingface.co/docs/hub/spaces-overview
5. **Gradio** — official guide: https://www.gradio.app/guides/quickstart  — web application UI option. Verify current minimum Python and framework versions.
6. **FFmpeg** — official: https://ffmpeg.org/documentation.html  — encode, remux, and examine MP4 output; pin version/installation method in actual runtime.
7. **Colab managed runtimes** — official FAQ: https://research.google.com/colaboratory/faq.html  — explicitly prohibits creating deepfakes. Do not use as a workaround for this lip-sync project.
8. **GitHub `gh` CLI** — official: https://cli.github.com/manual/gh_repo_create  — create a private repository; verify authenticated owner/visibility before operations.
9. **Google Drive API scope** — official: https://developers.google.com/workspace/drive/api/guides/api-specific-auth  — `drive.file` preferred over broad access; production Drive automation requires explicit user authorization.

## User-provided visual assets

- `assets/references/tiger_original_canonical.jpg` (source original `1000233378.jpg`) — user-designated PRIMARY; SHA-256 recorded in `SOURCE_MANIFEST.json`.
- `assets/references/tiger_expressions_provisional.jpg` (uploaded as `1000233387.png` but contains JPEG bytes) — user-provided PROVISIONAL; SHA-256 recorded.

No consent or license to publish those images **publicly** is inferred. Private repo/Drive source inclusion is part of the current requested handoff. The character profile and artwork are not distributed as open-source media.
