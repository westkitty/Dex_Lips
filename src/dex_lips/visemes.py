"""IPA phoneme -> Rhubarb mouth-shape mapping shared by the phoneme engine and
the evaluation reference drafts.

The table follows the *published* Rhubarb Lip Sync shape descriptions
(https://github.com/DanielSWolf/rhubarb-lip-sync#mouth-shapes):

  A  closed mouth: P, B, M
  B  slightly open, clenched teeth: most consonants (K, S, T ...), also EE (bee)
  C  open mouth: EH (men), AE (bat), also AH/schwa
  D  wide open: AA (father)
  E  slightly rounded: AO (off), ER (bird)
  F  puckered: UW (you), OW (show), W (way)
  G  upper teeth on lower lip: F, V
  H  tongue raised: long L
  X  idle / silence

It is a documented simplification of human articulation, NOT Rhubarb's own
internal context-dependent rules, and it is not a claim about any nonhuman
character's anatomy. Diphthongs map to their first (dominant) vowel shape.
"""
from __future__ import annotations

# Ordered for display in docs; keys are IPA symbols as emitted by
# espeak-style phoneme vocabularies (with or without length marks).
PHONEME_TO_SHAPE: dict[str, str] = {
    # A - lips closed
    'p': 'A', 'b': 'A', 'm': 'A',
    # B - teeth nearly together (most consonants + EE / short i)
    't': 'B', 'd': 'B', 'k': 'B', 'g': 'B', 'ɡ': 'B', 's': 'B', 'z': 'B',
    'n': 'B', 'ŋ': 'B', 'ɹ': 'B', 'r': 'B', 'ɾ': 'B', 'j': 'B', 'h': 'B',
    'ʃ': 'B', 'ʒ': 'B', 'tʃ': 'B', 'dʒ': 'B', 'θ': 'B', 'ð': 'B', 'ʔ': 'B',
    'x': 'B', 'ç': 'B', 'n̩': 'B', 'ts': 'B',
    'i': 'B', 'iː': 'B', 'ɪ': 'B', 'ᵻ': 'B', 'iə': 'B', 'ɪɹ': 'B', 'i:': 'B',
    # C - open (EH, AE, AH, schwa, EY)
    'ɛ': 'C', 'e': 'C', 'eɪ': 'C', 'æ': 'C', 'ʌ': 'C', 'ə': 'C', 'ɐ': 'C',
    'ɛɹ': 'C', 'eə': 'C', 'ɚ': 'E',
    # D - wide open (AA, AY, AW)
    'ɑ': 'D', 'ɑː': 'D', 'a': 'D', 'aɪ': 'D', 'aʊ': 'D', 'ɑːɹ': 'D', 'ɑɹ': 'D',
    'aɪə': 'D', 'aʊə': 'D', 'ɒ': 'D',
    # E - slightly rounded (AO, ER)
    'ɔ': 'E', 'ɔː': 'E', 'ɔːɹ': 'E', 'ɔɹ': 'E', 'ɜ': 'E', 'ɜː': 'E', 'ɝ': 'E',
    'ɔɪ': 'E', 'oːɹ': 'E',
    # F - puckered (UW, OW, W, UH)
    'u': 'F', 'uː': 'F', 'ʊ': 'F', 'oʊ': 'F', 'o': 'F', 'oː': 'F', 'w': 'F',
    'ʊɹ': 'F', 'əʊ': 'F', 'ʊə': 'F', 'ʍ': 'F',
    # G - labiodental
    'f': 'G', 'v': 'G',
    # H - L
    'l': 'H', 'ɫ': 'H', 'l̩': 'H',
}

SILENCE_TOKENS = frozenset({'<pad>', '<s>', '</s>', '<unk>', '|', ' ', ''})


def phoneme_to_shape(symbol: str) -> str:
    """Return the Rhubarb shape for one IPA phoneme token (never raises)."""
    if symbol in SILENCE_TOKENS:
        return 'X'
    s = symbol.strip()
    if s in PHONEME_TO_SHAPE:
        return PHONEME_TO_SHAPE[s]
    for strip in ('ː', 'ˑ', '̃', '̩', 'ʰ', 'ʲ', 'ʷ', 'ˈ', 'ˌ'):
        s = s.replace(strip, '')
    if s in PHONEME_TO_SHAPE:
        return PHONEME_TO_SHAPE[s]
    # Fall back on the first recognizable character (diphthongs / rare symbols).
    for i in range(len(s), 0, -1):
        if s[:i] in PHONEME_TO_SHAPE:
            return PHONEME_TO_SHAPE[s[:i]]
    return 'B'  # unknown consonant-like sound: neutral teeth-together shape


def mapping_table_markdown() -> str:
    by_shape: dict[str, list[str]] = {}
    for ph, shape in PHONEME_TO_SHAPE.items():
        by_shape.setdefault(shape, []).append(ph)
    names = {'A': 'closed (P B M)', 'B': 'teeth together (most consonants, EE)',
             'C': 'open (EH AE AH)', 'D': 'wide open (AA)', 'E': 'slightly rounded (AO ER)',
             'F': 'puckered (UW OW W)', 'G': 'lip on teeth (F V)', 'H': 'L', 'X': 'silence'}
    rows = ['| Shape | Meaning | IPA phonemes |', '|---|---|---|']
    for shape in 'ABCDEFGH':
        rows.append(f"| {shape} | {names[shape]} | {' '.join(by_shape.get(shape, []))} |")
    rows.append('| X | silence | CTC blank / low-energy frames |')
    return '\n'.join(rows)
