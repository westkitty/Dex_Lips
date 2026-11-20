# Browser WASM challenger — isolated staging receipt

- Purpose: preserve the verified alternate browser engine as a **separate experiment**, not a production replacement.
- Champion: `westkitty/Dex_Lips` at immutable baseline `d6caff6a25e0859a3f8a6bf4843d2666c169e31e`.
- All browser dependency packages are external and pinned; no vendor weights, node_modules, model data, or browser profiles are committed.
- Reproduce the Mac browser experiment using `README.md` and `references/SOURCE_PINS_AND_LICENSES.json`. Verify exact package integrity (npm `dist.integrity`) before unpacking.
- The original raw proof ZIP is preserved separately in the existing Google Drive Dex_Lips archive. This repository adaptation redacts the MacBook personal path in `REPORT.md` and replaces one hard-coded Android debugging address in `src/android_full_gate.cjs` with `DEX_LIPS_ADB_SERIAL`; the **Mac render runner and browser HTML are unchanged** from the verified proof packet.
- The Android full-render test **did not pass**; its CDP target enumeration timed out before loading source media. Never present the Android harness as verified; run it only with an explicitly selected authorized device.
- No Tiger reference image, mouth art, credentials, or user footage has been added here. The only media are original synthetic fixtures.
- Protected production files: `src/dex_lips/proof_render.py`, `app.py`, `assets/references/*`, and all canonical image SHA-256s. No production engine imports or routes change in this commit.
- Do not merge the browser engine into the production path until the tablet render, full resource lifecycle, and matched benchmark gates are proven. No public deployment or paid compute.

Validate source and fixtures with `python3 verify_experiment.py` (stdlib only). A passing hash check validates packaged bytes, **not** a live browser render.
