# Release test matrix (all four are mandatory for a full claim)

## Static/structural

- Seed verifier exits 0 and both media hashes match manifest.
- JSON job/rig schemas validate examples using a standards-compliant validator (after dependency selected).
- No secret, models, cache, live recordings or personal outputs in staged files.
- Entire interface works by keyboard and touch; no hidden controls only accessible via mouse.

## Media E2E with actual export

| ID | Scenario | Proof | Failure conditions |
|----|----------|-------|-------------------|
| T1 | Human-like still + spoken audio | MP4 with plausible synchronized mouth or clear blocked/fallback state | Generic static video labeled successful lip-sync; paid model silently invoked |
| T2 | Human-like existing video + new spoken audio | Original camera/body/background preserved; mouth synced | Replaced entire scene; new face identity; incorrect original sound mix |
| T3 | Nonhuman still + user-approved mouth art | Source anatomy/head/eyes unchanged; cue-driven mouth movement; MP4 | Human lips, changed head, unauthorized canon promotion |
| T4 | Moving nonhuman video + mouth rig | Keyframed/trackable mouth anchor stays aligned through turns; MP4 | Drifting or detached mouth; unbounded manual fix concealed |

For complete release, all four must actually pass with evidence. For MVP, T3 (using a distinct **synthetic demo** rig, not Tiger canon) and T4 are minimum functional checkpoints **with mouth cues genuinely derived from the supplied speech**. T1/T2 may remain `UNAVAILABLE_FREE_NEURAL` until evidence-backed hosted adapters work. Never mark the full contract PASS under that limitation.

**Proof-level distinction:** `scripts/proof_smoke.py` does *not* pass T3/T4 end-to-end because it feeds **authored cue JSON and artificial tone audio** to a compositor. It proves MP4 frame rendering, moving manual mouth anchors and audio mux, not speech recognition, viseme accuracy, production tracking, occlusion repair or a user-facing app. Treat these as `COMPOSITOR_PASS / FULL_SCENARIO_UNVERIFIED` until Codex adds a real Rhubarb speech-derived cue test and visual validation.

## Technical acceptance per rendered clip

- Video file is decodable from first to last frame; codec/dimensions/FPS/duration are recorded.
- Audio track present, non-silent where expected, start/end alignment error within one frame at output FPS in deterministic pipeline; measurable basis recorded.
- Open/closed, rounded-vowel, silence cues inspected; anchor placement/occlusion/crossfade checked on multiple timestamps, including head motion.
- File checksum recorded; no placeholder/source-only/static fake claimed as actual result.
- Zero-dollar charges, cloud usage, external transfer consent and temp-space use recorded.
- Manual visual verdict required for characters and AI models; automated tests alone do not prove canon.

## Stop condition

One bounded implementation pass and one repair pass. If a mandatory scenario remains blocked, report PARTIAL, exact failure, reproduction, and proposed next step; do not falsify PASS.

## Current proof status (2026-11-19 QQQ pass)

- T1: **PARTIAL** — deterministic user-authored rig can render a portrait with reviewed cues; neural portrait automatic route NOT AVAILABLE.
- T2: **PARTIAL** — existing video deterministic overlay with source FPS/length validation and user-confirmed neutral mouth; no automatic human lip substitution.
- T3: **PARTIAL** — synthetic/noncanonical sprite rig + authored cues + MP4 with actual spoken audio; Tiger-specific canonical rig approval MISSING; real Rhubarb not yet installed.
- T4: **PARTIAL** — two-second synthetic video keyframes + actual decodable MP4; no automated head turns/occlusion/mouth removal, and real-world footage NOT VALIDATED.
- Source hash guard: **PASS**. 19 local tests: **PASS** at time of report. Desktop Gradio HTTP smoke: **PASS**. Android: **UNVERIFIED**. Cloud hosted $0: **UNVERIFIED**.

No original full-contract PASS is justified. See `docs/QQQ_PERFORMANCE_REPAIR_2026-11-19.md` for evidence, performance measurements, and remaining blockers.
