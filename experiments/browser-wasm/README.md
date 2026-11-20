# Dex_Lips browser challenger — verified proof, isolated (November 19, 2026 Eastern)

**Verdict: COMPETES, not SURPASSES.** Real Rhubarb WASM speech analysis, browser H.264/AAC MP4 exports for two-second synthetic still and moving source, audio correlation, and source immutability were proven on localhost in Mac Chrome 157. Galaxy Tab S9 Ultra was checked via read-only Chrome DevTools for **codec capabilities only**. The production champion repository was not modified, pushed, deployed, or made public.

## Contents

* `src/wasm_mp4.html`: actual engine integration using Rhubarb WASM + Mediabunny + AAC polyfill. This is an isolated test harness, not a production editor. It requires pinned vendor packages unpacked beside it. No proprietary or canonical art bundled.
* `src/run_browser_mp4.cjs`: Node 26 + Chrome CDP local runner. The script must be placed in the same working directory as the HTML, `wasm_dep/`, `mediabunny_dep/`, and fixtures (or paths adjusted to fit). Fresh Chrome profile on each run to prevent second-run stale lock. Browser may create disposable profile caches; do not treat them as persisted user assets.
* `fixtures/`: synthetic neutral-source fixtures and spoken voice WAV with validated SHA-256.
* `evidence/readback_receipts.json`: observed run receipts read back from Mac, including output hashes; **not** the underlying browser-encoded MP4 bytes (Mac-to-Drive transfer blocked by 403 rate limits). Do not treat receipts as independent binary reproduction.
* `evidence/actual_rhubarb_mouthCues.json`: actual v1.0.3 Rhubarb result, not DSP energy-only timing.
* `references/SOURCE_PINS_AND_LICENSES.json`: pinned upstream source and package integrity metadata.
* `REPORT.md`: comparative verdict and limitations.

## Reproduction in a disposable macOS workspace (no global installation)

The harness assumes Node 26, Chrome at `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`, and npm registry access. Copy `src/wasm_mp4.html` and `src/run_browser_mp4.cjs` into the working directory root (as the Mac run did); copy the three fixtures to that same root. Do **not** run inside a protected Git repository or on storage-constrained hardware without checking temporary capacity. Packages are unpacked, not installed system-wide:

```sh
npm pack lip-sync-engine@1.0.3 --ignore-scripts
npm pack mediabunny@1.66.2 --ignore-scripts
npm pack @mediabunny/aac-encoder@1.66.2 --ignore-scripts
mkdir wasm_dep mediabunny_dep mediabunny_aac_dep
tar -xzf lip-sync-engine-1.0.3.tgz -C wasm_dep --strip-components 1
tar -xzf mediabunny-1.66.2.tgz -C mediabunny_dep --strip-components 1
tar -xzf mediabunny-aac-encoder-1.66.2.tgz -C mediabunny_aac_dep --strip-components 1
node run_browser_mp4.cjs still
node run_browser_mp4.cjs moving
ffprobe -v error -show_entries stream=codec_name,codec_type,nb_frames -show_entries format=duration,size -of json wasm_still.mp4
ffprobe -v error -show_entries stream=codec_name,codec_type,nb_frames -show_entries format=duration,size -of json wasm_moving.mp4
ffmpeg -v error -xerror -i wasm_still.mp4 -f null -
ffmpeg -v error -xerror -i wasm_moving.mp4 -f null -
```

Verify the exact npm integrity hashes in `references/` before deployment or bundling. The Emscripten speech model data are ~36 MB; no free cloud worker is required for this browser test but it does run locally on the client device. Build optimization and Android renderer proof remain open.

**This ZIP intentionally excludes the npm vendor assets and the actual Mac-rendered MP4 files.** Source, fixtures, verification steps and reproducibility evidence are provided. No user-supplied personal media, Tiger reference artwork, tokens, or model weights are packaged.

### Android full-render attempt
The real-device Chrome codec check passed; one reversible background-tab full-render attempt stopped before page creation (`CDP_TIMEOUT Target.getTargets`). The tablet received no media/model payload, and the harness removed its temporary ADB tunnels. Android MP4 execution is still unverified. Avoid retrying the same blocked operation without checking the device's CDP connectivity.
