# Engine demo MP4s

Same picture, same audio, same mouth art; only the cue engine differs. Rebuild with
`PATH=<rhubarb dir>:$PATH PYTHONPATH=src python scripts/make_demos.py` (refuses to run if either engine is missing).

| File | What |
|---|---|
| `demo_rhubarb.mp4` | Cues from **Rhubarb Lip Sync 1.14.0** (pocketSphinx, audio only) — `cues_rhubarb.json` |
| `demo_wav2vec2.mp4` | Cues from the **wav2vec2 phoneme recognizer** (audio only) — `cues_wav2vec2.json` |
| `demo_side_by_side.mp4` | Both, left Rhubarb / right wav2vec2, with the shared audio |
| `receipts.json` | Render receipts (hashes, frame counts, crossfade 0.04 s) |

- Picture: a generic procedural cartoon dog drawn by the script (not Dexter, not Tiger).
- Mouth art: `assets/mouth_sets/generic_muzzle`.
- Audio: LibriSpeech test-clean `3575-170457-0001`, "Why are we to be denied each other's society", CC BY 4.0 (Panayotov et al., ICASSP 2015, https://www.openslr.org/12).
- A Dexter demo was not made: the approved Dexter reference sheet was not accessible to the build (see `assets/mouth_sets/README.md`).
