# Operational State — Dex_Lips

Updated: 2026-11-19 (America/Detroit)

## Controlling user objective

Create a reusable $0 lip-sync studio for user-supplied stills/videos and recorded speech, including nonhuman and stylized characters, with browser/hosted-first execution and minimal local storage. Supply an executable Codex prompt and maintain source references. The current work unit is repository/Drive seed creation, NOT the actual full implementation.

## Known-good seed invariants

- Private repository intended: `westkitty/Dex_Lips` (remote creation status must be independently verified).
- Source images remain byte-for-byte identical to uploads and are checked by `scripts/verify_seed.py`.
- Canonical Tiger reference is the ORIGINAL full-body image; expression sheet is PROVISIONAL, not an approved replacement.
- Tiger: original head shape, eyes with no pupils, approximately 9 ft / 2.74 m scale, faceted obsidian and cyan crystalline structure; do not anthropomorphize or give human lips.
- Zero-dollar hard stop; no paid APIs, cloud spend, or model weights on constrained Macs; no Colab deepfake jobs.

## Status by capability

- Source-reference packaging and validation: completed locally (run verifier again after cloning).
- Workable Gradio/HTML editor: NOT BUILT.
- Rhubarb integration: NOT BUILT.
- Still-image character lip-sync: NOT BUILT.
- Existing-video mouth animation and tracking: NOT BUILT.
- MuseTalk/SadTalker hosted adapters: NOT BUILT / CONDITIONAL.
- Browser WebAssembly fallback: UNVERIFIED; never promise.
- Audio/video export and artifact validation: NOT BUILT.
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
