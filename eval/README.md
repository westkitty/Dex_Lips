# Mouth-cue evaluation set

`make accuracy` (= `PYTHONPATH=src python -m dex_lips.eval`) runs every available engine on these clips and rewrites `../ACCURACY.md`.

## Audio

Eight utterances from **LibriSpeech test-clean** (eight different speakers, 2.2–4.0 s each, 24 s total),
V. Panayotov, G. Chen, D. Povey, S. Khudanpur, *LibriSpeech: an ASR corpus based on public domain audio books*, ICASSP 2015, https://www.openslr.org/12 — licensed **CC BY 4.0**.
Retrieved 2026-11-20 through the Hugging Face datasets-server rows API (`openslr/librispeech_asr`, config `clean`, split `test`). File names are the LibriSpeech utterance IDs (`speaker-chapter-utterance`); `manifest.json` lists transcript, speaker, duration, row index and SHA-256 for each file.

## Reference cue tracks — reviewer judgment, NOT ground truth

`reference/*.json` were made by Grok Bot (an automated assistant), not by a trained phonetician:

1. **Draft** with `tools/draft_reference.py`: the published transcript is force-aligned with `facebook/wav2vec2-base-960h` (a *character* model; Apache-2.0) to get word boundaries, refined with a 10 ms energy check; each word's espeak-ng (en-us) pronunciation is spread over the word with fixed weights; phonemes become shapes through `src/dex_lips/visemes.py`.
2. **Review**: a spectrogram with word boundaries and the cue overlay was rendered for every clip and inspected; one clip was zoomed and corrected (`1320-122617-0030`, "rush"). Each reference file records what was checked and changed under `review`.

Known biases (also stated in ACCURACY.md):

- The reference and the wav2vec2 engine share the same phoneme→shape table, which favours that engine on shape choice.
- The word-boundary aid is also a wav2vec2-family model (different checkpoint, vocabulary and task).
- Phoneme boundaries *inside* words come from fixed duration weights plus visual review, so they are approximate (roughly ±30–50 ms).
- Rhubarb deliberately anticipates and tweens shapes for animation; exact frame matching penalizes that style.

Treat the numbers as a consistent yardstick for comparing engines and regressions on this set, not as absolute lip-sync accuracy.
