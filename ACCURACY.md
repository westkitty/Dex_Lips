# Dex_Lips automatic mouth-cue accuracy

> **Generated file.** Rewritten by `make accuracy` (`PYTHONPATH=src python -m dex_lips.eval`). Do not hand-edit numbers.

## Read this first

- **The reference cue tracks are the reviewer's own judgment, not ground truth.** They were drafted semi-automatically (transcript forced alignment + dictionary pronunciations + the documented phoneme→shape table) and then checked by eye against spectrograms. See `eval/README.md`.
- **Bias disclosure.** The references use the same phoneme→shape table as the wav2vec2 engine, so that engine is favoured on *which* shape is chosen for a given sound. Rhubarb uses its own context-dependent rules (tweening, anticipation), so lower exact-match numbers for Rhubarb partly measure disagreement in style, not just error. The grouped score (closed / narrow / open / round) and the boundary offsets are less sensitive to that bias.
- **Small set:** 8 LibriSpeech test-clean utterances, 8 speakers, 24.0 s of speech in total. Read audiobook English only; numbers will not transfer to noisy, emotional, cartoon or non-English voices.
- Scoring: 100 frames/s. *Frame accuracy* = share of 10 ms frames whose shape exactly matches the reference. *Boundary offset* = for every reference shape change, distance to the nearest engine shape change (signed mean: negative = engine changes shape earlier).

## Headline results

| Engine | Status | Frame accuracy (exact) | Grouped accuracy | Mean boundary offset | Median boundary offset | Signed mean | Runtime (all clips) |
|---|---|---|---|---|---|---|---|
| Rhubarb 1.14.0, pocketSphinx recognizer, audio only | ran | **55.6%** | 59.8% | 57 ms | **40 ms** | -14 ms | 28.6 s |
| Rhubarb 1.14.0, phonetic recognizer, audio only | ran | **47.6%** | 53.2% | 52 ms | **30 ms** | -13 ms | 6.5 s |
| Rhubarb 1.14.0, pocketSphinx + transcript (--dialogFile) | ran | **56.5%** | 61.1% | 52 ms | **30 ms** | -11 ms | 29.1 s |
| wav2vec2 phoneme CTC (facebook/wav2vec2-lv-60-espeak-cv-ft), audio only | ran | **67.4%** | 69.4% | 33 ms | **30 ms** | -14 ms | 3.9 s |

## Per-clip results

### Rhubarb 1.14.0, pocketSphinx recognizer, audio only

| Clip | Exact | Grouped | Median offset | Cues |
|---|---|---|---|---|
| 6930-75918-0000 | 52.9% | 58.3% | 50 ms | 19 |
| 1320-122617-0030 | 60.3% | 63.6% | 40 ms | 21 |
| 5639-40744-0008 | 46.4% | 46.4% | 30 ms | 15 |
| 260-123440-0000 | 53.2% | 53.2% | 80 ms | 9 |
| 7729-102255-0000 | 49.1% | 53.7% | 30 ms | 23 |
| 2094-142345-0004 | 62.5% | 66.7% | 30 ms | 16 |
| 3575-170457-0001 | 53.5% | 57.2% | 40 ms | 14 |
| 7127-75947-0002 | 63.6% | 73.1% | 35 ms | 16 |

### Rhubarb 1.14.0, phonetic recognizer, audio only

| Clip | Exact | Grouped | Median offset | Cues |
|---|---|---|---|---|
| 6930-75918-0000 | 50.0% | 55.1% | 40 ms | 22 |
| 1320-122617-0030 | 47.2% | 51.5% | 40 ms | 20 |
| 5639-40744-0008 | 42.8% | 50.0% | 30 ms | 17 |
| 260-123440-0000 | 35.6% | 41.2% | 40 ms | 17 |
| 7729-102255-0000 | 41.5% | 47.6% | 30 ms | 27 |
| 2094-142345-0004 | 58.7% | 63.6% | 30 ms | 16 |
| 3575-170457-0001 | 52.5% | 54.2% | 45 ms | 15 |
| 7127-75947-0002 | 49.4% | 59.9% | 45 ms | 21 |

### Rhubarb 1.14.0, pocketSphinx + transcript (--dialogFile)

| Clip | Exact | Grouped | Median offset | Cues |
|---|---|---|---|---|
| 6930-75918-0000 | 52.0% | 57.4% | 30 ms | 22 |
| 1320-122617-0030 | 63.6% | 66.8% | 30 ms | 22 |
| 5639-40744-0008 | 46.8% | 48.2% | 30 ms | 15 |
| 260-123440-0000 | 58.3% | 58.3% | 35 ms | 13 |
| 7729-102255-0000 | 49.1% | 53.7% | 30 ms | 23 |
| 2094-142345-0004 | 62.5% | 66.7% | 30 ms | 16 |
| 3575-170457-0001 | 53.5% | 59.9% | 55 ms | 14 |
| 7127-75947-0002 | 63.6% | 73.1% | 35 ms | 16 |

### wav2vec2 phoneme CTC (facebook/wav2vec2-lv-60-espeak-cv-ft), audio only

| Clip | Exact | Grouped | Median offset | Cues |
|---|---|---|---|---|
| 6930-75918-0000 | 80.0% | 82.9% | 30 ms | 22 |
| 1320-122617-0030 | 67.3% | 69.1% | 20 ms | 29 |
| 5639-40744-0008 | 60.8% | 60.8% | 35 ms | 16 |
| 260-123440-0000 | 74.5% | 75.5% | 30 ms | 17 |
| 7729-102255-0000 | 51.5% | 55.5% | 20 ms | 28 |
| 2094-142345-0004 | 78.8% | 78.8% | 20 ms | 19 |
| 3575-170457-0001 | 58.9% | 60.5% | 30 ms | 19 |
| 7127-75947-0002 | 68.5% | 71.9% | 40 ms | 16 |

## Per-shape confusion (frames)

Rows are the reference shape, columns the engine output. `·` = 0.

### Rhubarb 1.14.0, pocketSphinx recognizer, audio only

| ref \ engine | X | A | B | C | D | E | F | G | H | frames | recall |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **X** | 501 | · | 88 | 19 | · | 6 | 27 | · | · | 641 | 78.2% |
| **A** | · | 20 | 17 | 19 | · | 18 | · | · | 8 | 82 | 24.4% |
| **B** | 2 | 37 | 532 | 134 | 7 | 61 | 101 | 10 | 26 | 910 | 58.5% |
| **C** | 1 | 23 | 115 | 114 | 14 | 6 | 5 | · | 16 | 294 | 38.8% |
| **D** | · | 6 | 65 | 15 | 14 | 7 | 2 | · | · | 109 | 12.8% |
| **E** | · | · | 60 | 10 | · | 36 | 3 | · | · | 109 | 33.0% |
| **F** | 1 | 9 | 50 | 14 | · | 14 | 96 | · | · | 184 | 52.2% |
| **G** | 5 | · | 8 | 3 | · | · | · | 6 | · | 22 | 27.3% |
| **H** | · | · | 5 | 13 | · | · | 11 | 5 | 16 | 50 | 32.0% |
| precision | 98.2% | 21.1% | 56.6% | 33.4% | 40.0% | 24.3% | 39.2% | 28.6% | 24.2% | | |

### Rhubarb 1.14.0, phonetic recognizer, audio only

| ref \ engine | X | A | B | C | D | E | F | G | H | frames | recall |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **X** | 439 | 21 | 131 | 24 | 4 | 9 | 2 | 11 | · | 641 | 68.5% |
| **A** | · | 18 | 6 | 16 | · | 31 | · | · | 11 | 82 | 22.0% |
| **B** | · | 62 | 475 | 115 | 13 | 87 | 118 | 10 | 30 | 910 | 52.2% |
| **C** | · | 28 | 114 | 84 | 16 | 16 | 30 | · | 6 | 294 | 28.6% |
| **D** | · | 20 | 48 | 10 | 11 | 3 | 17 | · | · | 109 | 10.1% |
| **E** | · | · | 59 | 7 | 7 | 36 | · | · | · | 109 | 33.0% |
| **F** | · | 26 | 52 | 12 | 9 | 22 | 63 | · | · | 184 | 34.2% |
| **G** | · | · | 18 | 4 | · | · | · | · | · | 22 | 0.0% |
| **H** | · | 4 | 8 | 15 | · | 1 | 5 | · | 17 | 50 | 34.0% |
| precision | 100.0% | 10.1% | 52.1% | 29.3% | 18.3% | 17.6% | 26.8% | 0.0% | 26.6% | | |

### Rhubarb 1.14.0, pocketSphinx + transcript (--dialogFile)

| ref \ engine | X | A | B | C | D | E | F | G | H | frames | recall |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **X** | 512 | · | 58 | 48 | · | 6 | 17 | · | · | 641 | 79.9% |
| **A** | · | 26 | 12 | 18 | · | 18 | · | · | 8 | 82 | 31.7% |
| **B** | 3 | 37 | 527 | 152 | 7 | 58 | 90 | 10 | 26 | 910 | 57.9% |
| **C** | 1 | 23 | 105 | 128 | 14 | 6 | · | · | 17 | 294 | 43.5% |
| **D** | · | 3 | 57 | 26 | 14 | 7 | 2 | · | · | 109 | 12.8% |
| **E** | · | · | 64 | 10 | · | 32 | 3 | · | · | 109 | 29.4% |
| **F** | 1 | 9 | 51 | 14 | · | 14 | 95 | · | · | 184 | 51.6% |
| **G** | 5 | · | 8 | 3 | · | · | · | 6 | · | 22 | 27.3% |
| **H** | · | · | 5 | 12 | · | · | 11 | 5 | 17 | 50 | 34.0% |
| precision | 98.1% | 26.5% | 59.4% | 31.1% | 40.0% | 22.7% | 43.6% | 28.6% | 25.0% | | |

### wav2vec2 phoneme CTC (facebook/wav2vec2-lv-60-espeak-cv-ft), audio only

| ref \ engine | X | A | B | C | D | E | F | G | H | frames | recall |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **X** | 549 | · | 48 | 28 | · | 12 | 2 | 2 | · | 641 | 85.6% |
| **A** | · | 41 | 4 | 10 | 7 | 15 | · | · | 5 | 82 | 50.0% |
| **B** | 40 | 24 | 678 | 67 | 26 | 21 | 25 | 12 | 17 | 910 | 74.5% |
| **C** | · | 23 | 106 | 133 | 15 | 1 | · | 3 | 13 | 294 | 45.2% |
| **D** | · | · | 42 | · | 54 | · | 13 | · | · | 109 | 49.5% |
| **E** | · | · | 61 | · | · | 48 | · | · | · | 109 | 44.0% |
| **F** | 7 | 6 | 67 | 20 | 1 | · | 83 | · | · | 184 | 45.1% |
| **G** | · | · | · | 3 | · | 2 | · | 17 | · | 22 | 77.3% |
| **H** | · | · | · | 19 | 7 | · | 4 | 4 | 16 | 50 | 32.0% |
| precision | 92.1% | 43.6% | 67.4% | 47.5% | 49.1% | 48.5% | 65.4% | 44.7% | 31.4% | | |

## Phoneme → shape table (wav2vec2 engine and reference drafts)

| Shape | Meaning | IPA phonemes |
|---|---|---|
| A | closed (P B M) | p b m |
| B | teeth together (most consonants, EE) | t d k g ɡ s z n ŋ ɹ r ɾ j h ʃ ʒ tʃ dʒ θ ð ʔ x ç n̩ ts i iː ɪ ᵻ iə ɪɹ i: |
| C | open (EH AE AH) | ɛ e eɪ æ ʌ ə ɐ ɛɹ eə |
| D | wide open (AA) | ɑ ɑː a aɪ aʊ ɑːɹ ɑɹ aɪə aʊə ɒ |
| E | slightly rounded (AO ER) | ɚ ɔ ɔː ɔːɹ ɔɹ ɜ ɜː ɝ ɔɪ oːɹ |
| F | puckered (UW OW W) | u uː ʊ oʊ o oː w ʊɹ əʊ ʊə ʍ |
| G | lip on teeth (F V) | f v |
| H | L | l ɫ l̩ |
| X | silence | CTC blank / low-energy frames |

## Evaluation set

Source: LibriSpeech ASR corpus, test-clean subset. V. Panayotov, G. Chen, D. Povey, S. Khudanpur, "LibriSpeech: an ASR corpus based on public domain audio books", ICASSP 2015. https://www.openslr.org/12 License: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Hugging Face datasets-server rows API for dataset openslr/librispeech_asr, config clean, split test (2026-11-20). Audio files are byte-for-byte the FLAC served for each row.

| Clip | Speaker | Duration | Transcript | sha256 (first 12) |
|---|---|---|---|---|
| 6930-75918-0000 | 6930 | 3.50 s | CONCORD RETURNED TO ITS PLACE AMIDST THE TENTS | `9ce35224156f` |
| 1320-122617-0030 | 1320 | 3.98 s | SO CHOOSE FOR YOURSELF TO MAKE A RUSH OR TARRY HERE | `4c8d784cdabe` |
| 5639-40744-0008 | 5639 | 2.21 s | WHO TOUCHES ME AM I IN BED | `ad34d071015b` |
| 260-123440-0000 | 260 | 2.17 s | AND HOW ODD THE DIRECTIONS WILL LOOK | `6ca7d1967ad6` |
| 7729-102255-0000 | 7729 | 3.29 s | THE BOGUS LEGISLATURE NUMBERED THIRTY SIX MEMBERS | `3e143b9c2d52` |
| 2094-142345-0004 | 2094 | 2.64 s | AND WHAT THROUGH THE LEFT HAND WINDOW | `de2ffb60c2b2` |
| 3575-170457-0001 | 3575 | 2.99 s | WHY ARE WE TO BE DENIED EACH OTHER'S SOCIETY | `7c88157fc692` |
| 7127-75947-0002 | 7127 | 3.23 s | DO YOU THINK SO SHE REPLIED WITH INDIFFERENCE | `64354098b5ab` |

## Environment of the last run

- Python 3.13.5 on Linux x86_64
- Rhubarb available: True
- wav2vec2 model: facebook/wav2vec2-lv-60-espeak-cv-ft @ ae45363bf3413b374fecd9dc8bc1df0e24c3b7f4 (apache-2.0)
- Engine outputs for every clip are in `eval/results/<engine>/`; machine-readable totals in `eval/results/summary.json`.
