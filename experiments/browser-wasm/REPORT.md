# Dex_Lips — champion/challenger continuation certificate

**Date:** November 19, 2026, America/Detroit.  **Verdict: COMPETES.** Read-only immutable baseline SHA `d6caff6a25e0859a3f8a6bf4843d2666c169e31e`; no push, merge, deploy, or canon mutation.

## What changed from the first browser prototype

Earlier diagnostic browser prototype used RMS/zero-crossing mouth timing and produced VP9/Opus despite an MP4 MIME label. It lost to the FFmpeg champion. This continuation retrieved real pinned package bytes, verified package registry integrity, exercised Rhubarb 1.0.3 WASM on genuine spoken WAV, and achieved actual H.264/AAC MP4 with Mediabunny 1.66.2 + its 1.66.2 AAC extension. Two independent fixtures (320x240 still, moving 24 FPS), 48 frames each, actual speech-derived cues. Both encoded streams fully decoded via FFmpeg. Original synthetic fixture digests identical before/after.

## Evidence table

| Criterion | Champion (Python/Pillow/FFmpeg) | Browser challenger (WASM/Mediabunny) |
|---|---|---|
| Actual audio-derived Rhubarb cues | CLI adapter only; real executable unverified in preceding champion audit | **PASS** genuine 10 cues from 2s WAV |
| Still H.264/AAC MP4 | PASS prior synthetic tests | **PASS** Mac Chrome 157, 48 frames, full decode |
| Moving H.264/AAC MP4 | PASS on neutral synthetic video | **PASS** Mac Chrome 157, 48 input frames, full decode |
| Audible timed speech | PASS | **PASS**, decoded WAV correlation 0.9998, zero lag at sample-check resolution |
| Browser runtime dependency | Needs server/FFmpeg | **No backend required** but ~40MB speech-model data download and browser codec capability |
| Warm encode, exclusive of analysis | Prior Linux 2s runs ~0.47s still/~0.48s moving, including FFmpeg decode QA | Mac Chrome 0.072–0.077s still, 0.197–0.201s moving; **different test platform, not directly comparable** |
| Actual device-local memory peak | Not compared | **NOT MEASURED**; JS heap snapshot around 85–87 MB, excludes WASM/native/chrome process and transient peak |
| Head turns, preexisting mouth/occlusion | Manual anchor and neutral-source rule | Fixed synthetic neutral mouth overlay only, **not** full automatic mouth replacement |
| Galaxy Tab S9 Ultra | App not run there | Native H.264 codec supported; native AAC unsupported; **full rendering untested** |
| Source/art authority | Explicit Tiger hash lock and canon policy | Only synthetic assets used; canonical sources not bundled or changed |

## Repeat and reliability findings

Initial browser CDP runner used fixed Chrome profile paths, leading to NO_CDP_TARGET on subsequent attempts. Patched the **isolated test harness** to use a fresh profile per run. Readback receipts then showed 2 more PASS_RENDERED outputs and different encoded MP4 hashes, with matching source digests and audio. Chrome created significant temporary profile files (total scratch approx. 427 MiB after repeat). This browser code is a test harness, not a production-capable resource lifecycle system. Some DEX task response experienced a timeout despite output files being completed; do not treat that RPC error as a benchmark result or reproducible release pass.

## Exact input/output proof

Input spoken WAV SHA-256 `b14528b43805e02e327ef0c69577c7ddfa27508b843e5b18a0b5abff447b1f14`. Still SHA-256 `4d806e96d83731bc21f91c26c1a6d641bb28ecf71f1e5aa99d92e16a467c41b1`. Moving SHA-256 `005ed0209e72d62159191c1f0874e1755ea98c2794d6bd7161255c2775025731`.

Latest still MP4 SHA-256 `7cee6d8ef138fa62de8f0213787102001d532bd5be995e7054ff0c8c3348c2af`. Latest moving MP4 SHA-256 `be38f8dbf0e2450c41993a4dc19c7335e57c05a4d8b1d811e31ede9e4baf5451`. Both `ffprobe` h264 48 frames + aac 33 frames, duration 2.048s. FFmpeg decode checks independently passed for the initial outputs. Latest replay output files were read back as PASS_RENDERED in the scratch directory. Test output files live on Mac, not in this ZIP.

## Android compatibility readout

SM-X910 Chrome 157 was inspected via read-only DevTools on an existing tab: `secureContext=true`, H.264 WebCodecs supported, native AAC unsupported, AudioEncoder available, deviceMemory=8 GiB, crossOriginIsolated=false. Browser AAC polyfill and whole-video MP4 export on Android remain **unverified**. ADB forwarded debugging endpoint was removed after test.

## Risks, failure modes, and competition verdict

* **Storage**: npm Rhubarb WASM data 37,853,278 bytes, Wasm binary 1,890,181 bytes, Mediabunny ES module ~1.64 MB, AAC extension module ~1.14 MB. 40+MB initial fetch and model cache pressure are material on small devices; first session can be slow.
* **Licenses**: MIT for upstream Rhubarb port; Apache-2.0 for Lip Sync Generator analogue; MPL-2.0 for Mediabunny plus licenses for its FFmpeg-derived AAC encoder. Vendoring requires notices/compliance. No vendor assets in ZIP.
* **Accuracy**: real Rhubarb category timing now proven, not human-correct lip placement for unusual nonhuman anatomy. User-approved sprite art remains required.
* **Robustness**: long sessions, large files, worker cancellation/cleanup, peak memory, speech quality with multiple accents, browser cross-compatibility, 30-second limit and tablet whole-render remain unproven. Current engine v1.0.3 has upstream worker lifecycle history; newer 2.0 features were unmerged at research time. Use pinned versions rather than master drift.
* **Privacy**: local-only localhost test, no user media uploaded to external providers. Test harness intentionally uses same-origin static assets. Do not deploy publicly with private reference images.
* **Environment**: MacBook scratch `<MacBook home>/.dex_lips_challenger_courier_20261119` holds npm packages/output and Chrome profile data (~427 MiB observed after repeat), **NOT CLEANED**. No packages installed system-wide. Remote deletion requires the policy-compliant cleanup route; do not claim reclaimed space until verified.

**Verdict `COMPETES`, not `SURPASSES`:** Browser has advanced from failed codec demonstration to genuine speech + two working, verified MP4s; it has a meaningful offline/serverless advantage. But independent mobile MP4, peak resource proof, long-session reliability, and matched-machine performance remain missing. Preserve the incumbent and propose a very small opt-in `experiments/browser-wasm/` isolated integration later, using shared cues.json and source-hash invariants. No production change now.

## Addendum: bounded full-Android attempt

A single best-effort full-render attempt on the connected Galaxy Tab S9 Ultra through existing Chrome DevTools was made after the codec capability check. CDP `Target.getTargets` timed out before creating a test tab or requesting source/model media. The harness reported `MOBILE_TEST_BLOCKED` with zero HTTP requests and confirmed both temporary ADB tunnels removed. This **does not** prove Android incompatibility or actual renderer performance. No second automatic attempt was made; tablet full-render remains **UNVERIFIED**. See `evidence/android_full_render_blocked.json`; the attempt script `src/android_full_gate.cjs` is provided for review only.
