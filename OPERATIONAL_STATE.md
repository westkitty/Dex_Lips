# Operational State — Dex_Lips

Updated: 2026-11-19 (America/Detroit)

## Controlling user objective

Create a reusable $0 lip-sync studio for user-supplied stills/videos and recorded speech, including nonhuman and stylized characters, with browser/hosted-first execution and minimal local storage. Supply an executable Codex prompt and maintain source references. A local-only deterministic editor/rendering MVP now exists; full automatic speech analysis, advanced video mouth removal, and free cloud deployment remain unproven.

## Known-good seed invariants

- Private repository intended: `westkitty/Dex_Lips` (remote creation status must be independently verified).
- Source images remain byte-for-byte identical to uploads and are checked by `scripts/verify_seed.py`.
- Canonical Tiger reference is the ORIGINAL full-body image; expression sheet is PROVISIONAL, not an approved replacement.
- Tiger: original head shape, eyes with no pupils, approximately 9 ft / 2.74 m scale, faceted obsidian and cyan crystalline structure; do not anthropomorphize or give human lips.
- Zero-dollar hard stop; no paid APIs, cloud spend, or model weights on constrained Macs; no Colab deepfake jobs.

## Status by capability

- Source-reference packaging and validation: completed locally (run verifier again after cloning).
- Gradio editor: IMPLEMENTED, local HTTP startup and backend render verified; Android touch interactions unverified.
- Rhubarb CLI integration: IMPLEMENTED and stub-adapter tested; REAL EXECUTABLE MISSING in tested runtime; phonetic recognition UNVERIFIED.
- Still-image user-approved mouth rig + manual cue render: VERIFIED in isolated runtime; exact phonetic lip-sync depends on real Rhubarb.
- Existing-video keyframed overlay: VERIFIED synthetic clip only; automatic tracking/removal NOT BUILT.
- MuseTalk/SadTalker hosted adapters: NOT BUILT / CONDITIONAL.
- Browser WebAssembly fallback: UNVERIFIED; never promise.
- Audio/video H.264/AAC MP4 export: VERIFIED on synthetic media and manually aligned spoken audio in isolated container; no actual target-machine proof.
- Hugging Face ZeroGPU eligibility, billing state, and deployment: UNVERIFIED.
- Automated Google Drive archive: NOT BUILT; avoid broad OAuth credentials.

## Immediate next task

Execute the bounded contract `prompts/CODEX_BUILD_PROMPT.md` from the verified repo. Protect uploaded media and all above invariant locks. A runnable app and four scenario tests are necessary before claiming product readiness.

## Regression risks

- A demo that draws moving shapes but does not output synchronized MP4 is not lip-sync delivery.
- A human-face model that transforms an unusual character into a human-faced creature violates identity.
- Auto-generating mouth sprites from the provisional sheet may override the canonical head.
- An uncapped hosted task can exceed free quota or be billed.
- A generic front-facing face detector may fail for 3/4 profile and monstrous mouths; require manual keyframe anchors and explicit failure states.
- Claims of automatic animal speech from one still image are unverified without a user-approved mouth rig.

## 2026-11-19 — Bounded reliability audit and compositor proof

- **Confirmed in an isolated container:** seed source hashes unchanged; Python stdlib seed checks; JSON schemas and examples separately checked using jsonschema; Pillow/FFmpeg/ffprobe available in isolated runtime. `scripts/proof_smoke.py` renders separate synthetic image + cues and moving synthetic video + cues to decodable 2s, 24fps, H.264/AAC MP4 files. Audio/video durations match in this narrow test.
- **Scope only:** cue-driven compositing was tested, not Rhubarb speech recognition, nonhuman mouth tracking, UI, free cloud hosting, or Tiger mouth approval. Synthetic test sources are not canonical art.
- **Confirmed specification correction:** ordinary Gradio/Docker compute Spaces require paid plan for new creation; eligible free ZeroGPU Spaces are the exception. Do not create paid hosted compute; static frontend is a separate, non-backend fallback.
- **Regression protection:** the proof renderer rejects bundled Tiger reference hashes even when an untrusted rig JSON lies about authority; renders refuse output overwrite; synthetic tests and manifest locks must remain intact.
- **Remaining next step:** execute the build prompt from the verified private repo, extend speech-derived cue generation using Rhubarb with a real WAV, implement editor and media tracking/mask states, obtain hosting eligibility without paid subscriptions, and validate all four original acceptance scenarios. No claim of full app completion is justified.

## 2026-11-19 — QQQ/Performance/Repair current state

- Starting remote revision `0d40a3de2747f27cd3a9d2912115a6212e51346c` verified before repair. The new work must be verified from the final remote commit separately before declaring Git delivery complete.
- Actual UI application (Gradio) starts on localhost and served HTTP 200 in disposable Linux container; source+audio+user approved mouth sprite ZIP+manual cues produces an H.264/AAC MP4. No paid calls, model weights or third-party user media uploads.
- Spoken-voice fixture (via `espeak`) plus manually authored cues proved compositing; Rhubarb CLI API adapter tested via fake executable, NOT real speech recognizer. Missing binary must fail closed.
- Video camera/body/source preservation verified only on a synthetic moving-video input without a pre-existing speaking mouth. Real mouth masking/tracking and tablet UI remain unverified.
- Source art hashes protected and checked. User's 1024x1536 portrait-style source dimensions can now be resized to fit output 480x720 without rewriting the source; the canonical original cannot be used for unapproved rig playback.
- Measured single-container six-second, five-run median improvements against baseline: still 0.7932s -> 0.6324s (20.3%), video 1.0172s -> 0.6617s (34.9%). These are not guaranteed device/cloud improvements. See `docs/QQQ_PERFORMANCE_REPAIR_2026-11-19.md`.
- Remaining: real Rhubarb binary + true audio-derived cues, fully automatic video lip replacement, free hosted compute proof, actual Android UI testing, canonical Tiger rig authorization. FULL PRODUCT STATUS: **PARTIALLY VERIFIED**, not complete.

## 2026-11-19 — Isolated browser challenger archived

- Experimental source and synthetic fixtures committed **separately** under `experiments/browser-wasm/` after authorizing stage/commit/push. No production code, routes, renderer, canonical art or user private media changed.
- **Verified only on localhost in Mac Chrome 157:** pinned Rhubarb WASM `lip-sync-engine@1.0.3` produced 10 audio-derived mouth cues from the 2-second spoken fixture; Mediabunny `1.66.2` plus `@mediabunny/aac-encoder@1.66.2` produced separate 48-frame H.264/AAC MP4 still and moving-video proofs. Audio correlation was approximately 0.9998 with no detected lag at test resolution. Source fixture hashes matched.
- Two successful renders of each scenario were recorded, with one intervening CDP stale-profile test-harness failure; the isolated harness was revised to use fresh profiles. The output files were not included in the repository. Check `experiments/browser-wasm/REPORT.md`, `evidence/` and the preserved Drive ZIP for precise receipt limits.
- **Unverified:** true Galaxy Tab S9 Ultra end-to-end rendering (one CDP timeout before loading media), 30s+ resource stability, accurate mouth replacement through head turns, peak total-process memory, same-machine parity vs Python/FFmpeg, and deployable nonhuman UI. Android codec capability check alone passed.
- Champion remains default. Verdict: **COMPETES**, NOT SURPASSES. Promote nothing from the experimental engine into production until the missing gates pass.
- Security and storage: the small experiment excludes npm vendor packages and browser models; browser load still needs ~40 MB speech assets. The archived Mac scratch directory was observed around 427 MiB and remained uncleaned; its removal requires a separate safe storage action.

## 2026-11-20 — Generated mouth assets (feature branch, NOT product-verified)

- User explicitly corrected the scope: Dex_Lips must CREATE its own mouth assets; no external drawing/ZIP is a mandatory input. This is a required built-in capability.
- Feature-branch implementation adds deterministic, source-palette draft overlays X/A–H for still images and sampled video frames, nine PNGs, a visual D-pose preview, downloadable ZIP and automatic ZIP selection in Gradio. Creator does not detect mouth location; the user positions the mouth center and width/height. It does not infer anatomy or repair original animated mouths.
- Generated ZIP carries `generated_draft` / `approved: false`. The existing staging importer converts it to job-scoped user-reviewed `approved_user_rig` only after the explicit approval checkbox. Bundled canonical/provisional reference hashes are excluded from generated-rig route.
- Proposed tests cover sprite packaging, zero mutation of source, protected reference, invalid inputs, and video-frame sampling. They have NOT been executed in this connector-only session; target-runtime Gradio/MP4 and Android validation are still pending. Do not claim end-to-end verified until executed.
- Pending: run all existing/new tests and actual generated-mouth ZIP → real speech-derived cues → rendered MP4, assess feature quality with nonhuman source, then merge if successful. Existing manual-import compositor remains intact.

## 2026-11-20 — PR #1 source-geometry continuation (unmerged)

- Added source-soft and source-faceted modes using connected high-contrast contours inside the user-defined mouth region. Preserves observed asymmetric boundary, source fill, and painted details through each pose transform; exposes a traced-region diagnostic and dark/light/auto contrast modes in Gradio. Existing soft/faceted graphic modes, import ZIP, Rhubarb adapter, MP4 renderer and reference-hash locks are preserved.
- Any absent or ambiguous contour blocks source mode rather than replacing it silently with invented anatomy. Source tracing is deterministic pixel processing, not identity recognition, exact topology, segmentation ground truth, or verified canonical character production. Explicit job-level review is still required; bundled Tiger references remain blocked from generated-rig and render routes.
- Local isolated synthetic source-geometry checks were executed for dark and bright faceted regions plus blank-background fail-closed, and representative PNG diagnostics inspected. Integration tests were authored for nine sprites -> ZIP -> job-approved rig -> actual spoken-WAV/archived real Rhubarb cue JSON -> H.264/AAC still/video output; synthetic fixtures are not canon or quality approval. GitHub Actions workflow runs tests without consuming MacBook/Big Mac storage.
- CI run 44728363379 failed on missing ffmpeg/ffprobe in runner before Python tests; workflow now installs these prerequisites. No result has yet been promoted to full E2E PASS in this note. Do not merge without completed green CI and visual review of nonhuman examples; video mouth replacement and existing face-animation removal remain unimplemented.

## 2026-11-20 — PR #1 final verified CI evidence (feature branch)

- GitHub Actions [run 44728641740](https://github.com/westkitty/Dex_Lips/actions/runs/44728641740) on feature commit `d26f921b1aeb43978d43292c35576697f5a9d64f` succeeded. All 30 Python tests passed; `scripts/verify_seed.py`, source compile, existing `scripts/proof_smoke.py`, FFmpeg/AAC encoder checks and Gradio Blocks construction passed.
- The new end-to-end callback test `test_gradio_generated_zip_to_existing_render_callback` passed: source-traced faceted draft -> Gradio generated ZIP -> user-approved noncanonical rig -> recorded spoken WAV plus archived real Rhubarb mouth cues -> H.264/AAC MP4, decoded with FFmpeg and original source hash unchanged. Separate still/video integration tests passed. These prove pipeline behavior on synthetic nonhuman artwork, NOT fresh automatic speech recognition, anatomical accuracy on arbitrary real characters, video mouth removal, or approved Tiger art.
- The PR may be merged as **source-aware draft generator** after confirming current head CI remains green. Canon status remains USER_REVIEW_REQUIRED for all generated character artwork. No paid runtime, local Mac model weight install, or provider upload was added.

## 2026-11-20 — Pages browser rig studio deployed (verified GitHub receipt)

- User instructed stage/push/update Pages. Implemented isolated static `site/` image/video-frame mouth rig editor with source-aware pixel tracing, graphic fallback, separate X/A-H PNG downloads, ZIP with `generated_draft`/`approved:false`, protected SHA-256 source refusal, cue-based audio preview, and mobile-focused controls. No source media or canonical reference files are copied to `site/`.
- The original Python/Gradio/FFmpeg backend remains unchanged. Pages is static only; no claim of automatic speech analysis or MP4 export on Pages. Repository visibility observed PUBLIC (contradicts older 'private repo' wording).
- PR #2 merged; `main` commit `c2d8d7253143fd2afe9847843ebc7b04abf65129`. Source/test browser QA passed GitHub run 44731510532. Follow-up workflow-only timing fix committed as `c43c2c541d021b8ebcefee6575bc57438fad7ca0` after transient Pages artifact indexing/duplicate artifact failures. Fresh GitHub [run 44731970189](https://github.com/westkitty/Dex_Lips/actions/runs/44731970189) passed browser-check and publish; deploy-pages reported success and environment URL https://westkitty.github.io/Dex_Lips/.
- Production **deployment receipt VERIFIED**; separate HTTP navigation/Android end-user proof **UNVERIFIED**, because external page fetch was unavailable in the current tools. Canonical character-specific visual quality and in-browser speech-to-MP4 remain unverified/unsupported. No unrelated project files or references mutated.
