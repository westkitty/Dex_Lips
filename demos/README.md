# Engine demo MP4s

Same audio, same cues; only the cue engine (and, between the two groups, the picture and mouth art) differs. Rebuild with
`PATH=<rhubarb dir>:$PATH PYTHONPATH=src python scripts/make_demos.py` (refuses to run if either engine is missing).
Each engine runs once; the generic and Dexter renders share its cue file.

### Dexter (owner-approved reference sheet)

| File | What |
|---|---|
| `demo_dexter_rhubarb.mp4` | Dexter still + `dexter_muzzle` mouths, cues from **Rhubarb Lip Sync 1.14.0** (pocketSphinx, audio only) |
| `demo_dexter_wav2vec2.mp4` | Dexter still + `dexter_muzzle` mouths, cues from the **wav2vec2 phoneme recognizer** (audio only) |
| `demo_dexter_side_by_side.mp4` | Both, left Rhubarb / right wav2vec2, with the shared audio |
| `source_dexter_*.png` | The exact still each video was rendered from (with the caption bar) |

- Picture: `assets/reference/dexter/dexter_front_still.png`, a crop of the front-facing head in row 1 col 3 ("Left-Proflle") of the owner-approved Dexter sheet (sha256 `ed81548c…c12c41`), with a caption bar added on top.
- Mouth art: `assets/mouth_sets/dexter_muzzle` (cut only from the same sheet; cells listed in `assets/mouth_sets/README.md`).

### Generic (no character)

| File | What |
|---|---|
| `demo_rhubarb.mp4` | Generic procedural dog + `generic_muzzle`, Rhubarb cues |
| `demo_wav2vec2.mp4` | Generic procedural dog + `generic_muzzle`, wav2vec2 cues |
| `demo_side_by_side.mp4` | Both, left Rhubarb / right wav2vec2 |
| `source_rhubarb.png`, `source_wav2vec2.png` | The generic pictures (not Dexter, not Tiger) |

### Shared

| File | What |
|---|---|
| `cues_rhubarb.json` | Cues produced by running Rhubarb on the audio (14 cues) |
| `cues_wav2vec2.json` | Cues produced by running wav2vec2 on the audio (19 cues) |
| `receipts.json` | Render receipts keyed by `generic` / `dexter` then engine (hashes, frame counts, crossfade 0.04 s, mouth set, engine result) |

- Audio: LibriSpeech test-clean `3575-170457-0001`, "Why are we to be denied each other's society", CC BY 4.0 (Panayotov et al., ICASSP 2015, https://www.openslr.org/12).
