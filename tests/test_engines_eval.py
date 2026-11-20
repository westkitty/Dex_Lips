"""Automatic engines, honesty (BLOCKED) path, viseme mapping and scoring."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
CLIP = ROOT / 'eval/clips/5639-40744-0008.flac'
MEDIA = bool(shutil.which('ffmpeg') and shutil.which('ffprobe'))


class TestBlockedPath(unittest.TestCase):
    def test_neither_engine_available_is_blocked_and_writes_nothing(self):
        from dex_lips import engines, phoneme_engine
        from dex_lips.proof_render import ProofError
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(phoneme_engine, 'phoneme_engine_status', return_value=(False, 'test: no model')):
            out = Path(d) / 'cues.json'
            with self.assertRaisesRegex(ProofError, 'BLOCKED'):
                engines.analyze(CLIP, out, engine='auto', rhubarb_executable='missing_rhubarb_98765')
            self.assertFalse(out.exists())
            self.assertEqual(engines.available_engines('missing_rhubarb_98765'), [])

    def test_explicit_engines_blocked_individually(self):
        from dex_lips import engines, phoneme_engine
        from dex_lips.proof_render import ProofError
        with tempfile.TemporaryDirectory() as d, \
                mock.patch.object(phoneme_engine, 'phoneme_engine_status', return_value=(False, 'test: no model')):
            with self.assertRaisesRegex(ProofError, 'Rhubarb BLOCKED'):
                engines.analyze(CLIP, Path(d) / 'a.json', engine='rhubarb', rhubarb_executable='missing_rhubarb_98765')
            with self.assertRaisesRegex(ProofError, 'Phoneme engine BLOCKED'):
                engines.analyze(CLIP, Path(d) / 'b.json', engine='wav2vec2')

    def test_app_reports_blocked_without_inventing_cues(self):
        import app
        from dex_lips import engines as eng, phoneme_engine
        with mock.patch.object(phoneme_engine, 'phoneme_engine_status', return_value=(False, 'test: no model')), \
                mock.patch.object(eng.shutil, 'which', return_value=None):
            cues, message = app.analyze_uploaded(str(CLIP), '', 'pocketSphinx', 'auto')
        self.assertEqual(cues, '')
        self.assertIn('BLOCKED', message)


class TestVisemesAndCues(unittest.TestCase):
    def test_mapping_follows_rhubarb_shape_descriptions(self):
        from dex_lips.visemes import phoneme_to_shape
        expected = {'p': 'A', 'b': 'A', 'm': 'A', 't': 'B', 's': 'B', 'iː': 'B', 'ɛ': 'C', 'æ': 'C',
                    'ɑː': 'D', 'ɔː': 'E', 'ɜː': 'E', 'uː': 'F', 'oʊ': 'F', 'w': 'F', 'f': 'G', 'v': 'G',
                    'l': 'H', '<pad>': 'X', 'ɑːɹ': 'D', 'aɪ': 'D'}
        for ph, shape in expected.items():
            self.assertEqual(phoneme_to_shape(ph), shape, ph)
        self.assertEqual(phoneme_to_shape('ʙ̥'), 'B')  # unknown -> neutral, never raises

    def test_phonemes_to_cues_is_deterministic_contiguous_and_silence_aware(self):
        from dex_lips.phoneme_engine import phonemes_to_cues
        events = [{'phoneme': 'h', 'start_frame': 20, 'end_frame': 20}, {'phoneme': 'ɛ', 'start_frame': 26, 'end_frame': 27},
                  {'phoneme': 'l', 'start_frame': 32, 'end_frame': 32}, {'phoneme': 'oʊ', 'start_frame': 37, 'end_frame': 39},
                  {'phoneme': 'm', 'start_frame': 90, 'end_frame': 90}, {'phoneme': 'iː', 'start_frame': 95, 'end_frame': 97}]
        energy = [-70.0] * 150
        for i in list(range(18, 44)) + list(range(88, 102)):
            energy[i] = -20.0
        a = phonemes_to_cues(events, energy, 3.0)
        self.assertEqual(a, phonemes_to_cues(events, energy, 3.0))
        self.assertEqual(a[0]['start'], 0.0)
        self.assertEqual(a[-1]['end'], 3.0)
        for prev, cur in zip(a, a[1:]):
            self.assertAlmostEqual(prev['end'], cur['start'])
            self.assertNotEqual(prev['value'], cur['value'])
        values = [c['value'] for c in a]
        self.assertEqual(values[:5], ['X', 'B', 'C', 'H', 'F'])
        self.assertIn('X', values[5:-2])  # the 1 s pause becomes rest
        self.assertIn('A', values)


class TestScoring(unittest.TestCase):
    def test_frame_accuracy_offsets_and_confusion(self):
        from dex_lips.eval import score_clip
        ref = [{'start': 0, 'end': .5, 'value': 'X'}, {'start': .5, 'end': 1.0, 'value': 'D'}, {'start': 1.0, 'end': 2.0, 'value': 'X'}]
        hyp = [{'start': 0, 'end': .6, 'value': 'X'}, {'start': .6, 'end': 1.0, 'value': 'C'}, {'start': 1.0, 'end': 2.0, 'value': 'X'}]
        s = score_clip(ref, hyp, 2.0)
        self.assertEqual(s['frames'], 200)
        self.assertEqual(s['exact'], 150)
        self.assertEqual(s['grouped'], 190)  # C and D are both "open"
        self.assertEqual([round(o, 3) for o in s['offsets']], [.1, 0.0])
        self.assertEqual(s['confusion'][('D', 'C')], 40)
        self.assertEqual(s['confusion'][('D', 'X')], 10)

    def test_reference_tracks_are_labelled_judgment_and_cover_clips(self):
        manifest = json.loads((ROOT / 'eval/manifest.json').read_text())
        self.assertGreaterEqual(len(manifest['clips']), 5)
        for clip in manifest['clips']:
            ref = json.loads((ROOT / 'eval/reference' / f"{clip['id']}.json").read_text())
            self.assertEqual(ref['status'], 'REVIEWER_JUDGMENT_NOT_GROUND_TRUTH')
            cues = ref['mouthCues']
            self.assertEqual(cues[0]['start'], 0)
            self.assertAlmostEqual(cues[-1]['end'], clip['duration_sec'], delta=.02)
            self.assertTrue((ROOT / clip['file']).is_file())


@unittest.skipUnless(MEDIA and shutil.which('rhubarb'), 'Real Rhubarb binary not on PATH (CI installs it)')
class TestRealRhubarb(unittest.TestCase):
    def test_real_rhubarb_produces_varied_cues_from_real_speech(self):
        from dex_lips.speech import analyze
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / 'cues.json'
            result = analyze(CLIP, out)
            doc = json.loads(out.read_text())
        self.assertEqual(doc['metadata']['analysis'], 'rhubarb')
        shapes = {c['value'] for c in doc['mouthCues']}
        self.assertGreaterEqual(result['cue_count'], 6)
        self.assertGreaterEqual(len(shapes - {'X'}), 3, shapes)


def _w2v_ready() -> bool:
    try:
        from dex_lips.phoneme_engine import phoneme_engine_available
        return MEDIA and phoneme_engine_available()
    except Exception:
        return False


@unittest.skipUnless(_w2v_ready(), 'wav2vec2 phoneme model not in local cache (optional; run `python -m dex_lips.engines --fetch-model`)')
class TestRealPhonemeEngine(unittest.TestCase):
    def test_wav2vec2_recognizes_phonemes_from_real_speech(self):
        from dex_lips.phoneme_engine import analyze
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / 'cues.json'
            result = analyze(CLIP, out)
            doc = json.loads(out.read_text())
        self.assertEqual(doc['metadata']['analysis'], 'wav2vec2-phoneme')
        self.assertGreaterEqual(result['phoneme_count'], 10)
        # "who touches me am I in bed": expect the bilabials (A) and rounded (F) shapes.
        shapes = {c['value'] for c in doc['mouthCues']}
        self.assertTrue({'A', 'F'} <= shapes, shapes)


if __name__ == '__main__':
    unittest.main()
