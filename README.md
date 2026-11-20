# Dex_Lips

**Status: SOURCE-BACKED CODEX HANDOFF SEED — application NOT YET IMPLEMENTED.**

A reusable, strictly zero-out-of-pocket-cost lip-sync production studio for still images, existing videos, stylized art, and nonhuman fictional characters. The intended deliverable is a browser-accessible workflow that selects a neural human-face route only when genuinely free compute is available, and otherwise uses deterministic audio-to-mouth-cue animation with reusable character mouth rigs and manual controls.

## Start here

1. Read `OPERATIONAL_STATE.md`, `Dex_Lips_bible.md` and `docs/PRODUCT_SPEC.md`.
2. Inspect `assets/references/SOURCE_MANIFEST.json` and `docs/CHARACTER_REFERENCE_POLICY.md` **before touching reference artwork**.
3. Inspect `docs/SOURCE_REFERENCES.md`, `docs/CLOUD_DEPLOYMENT.md`, `docs/SECURITY_PRIVACY.md`.
4. Run `python3 scripts/verify_seed.py` and `python3 -m unittest discover -s tests -v` (stdlib only).
5. Give Codex the **complete prompt** in `prompts/CODEX_BUILD_PROMPT.md` (or use it directly as the handoff).

This seed contains a project contract, immutable source images, source hashes, schemas, QA fixtures, and operational instructions. It does **not** pretend to contain a finished lip-sync engine, a deployed Space, paid-service access, approved mouth sprite assets, or completed rendering tests.

## Reference authority

- `assets/references/tiger_original_canonical.jpg`: user's **controlling** Shard-God Tiger image reference; preserve exact head silhouette, pupil-less eyes, crystalline/faceted visual language, and user-locked 9 ft height.
- `assets/references/tiger_expressions_provisional.jpg`: reference sheet supplied by user, titled *Provisional Visual Reference*. Its proportions/head geometry are NOT approved; use only as a noncanonical expression-label exploration unless explicitly promoted by user.
- The expression sheet's upload name ended in `.png`, but the bytes are JPEG; this repo stores the unmodified bytes with the correct `.jpg` extension. Original upload name is recorded in the manifest.

## No-spend, storage, and privacy boundaries

- Default repo remains **private**. Do not publish source images, copy them to public demos, or use them for model training.
- No paid inference, paid GPU rental, credit-based fallback, automatic purchase, or external spending. If free capacity is unavailable, stop or route to local/browser CPU work.
- Do not install large model weights on MacBook or Big Mac. Cloud compute is ephemeral and must be eligibility-checked, not promised.
- Do not put voice files, generated clips, secret keys, access tokens, credentials, or personal media into Git. `.gitignore` protects obvious folders, but review `git status` before each commit.
- Google Colab managed runtimes are **not** a neural lip-sync fallback under their prohibited deepfake policy.

## What is here

See `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/ACCEPTANCE_TESTS.md`, `docs/SOURCE_REFERENCES.md`, `docs/DRIVE_HANDOFF.md`, `schemas/`, and `examples/`. The build prompt is in `prompts/CODEX_BUILD_PROMPT.md`.
