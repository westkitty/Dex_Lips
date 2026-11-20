"""Executable core proof tests. Skips are explicitly not proof of functionality."""
import importlib.util
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'src'))
READY=(importlib.util.find_spec('PIL') is not None and shutil.which('ffmpeg') is not None and shutil.which('ffprobe') is not None)

@unittest.skipUnless(READY,'Missing Pillow or FFmpeg/ffprobe; media path is UNVERIFIED')
class TestProofRender(unittest.TestCase):
    def test_end_to_end_still_and_moving(self):
        from proof_smoke import run_smoke
        with tempfile.TemporaryDirectory() as d:
            result=run_smoke(Path(d))
            self.assertEqual(result['status'],'PROOF_PASSED_WITH_LIMITATIONS')
            self.assertEqual(result['T3_synthetic_cue_compositor']['video_codec'],'h264')
            self.assertEqual(result['T4_synthetic_keyframe_video_compositor']['audio_codec'],'aac')
            self.assertTrue((Path(d)/'t3_still_proof.mp4').stat().st_size>2000)
            self.assertTrue((Path(d)/'t4_moving_proof.mp4').stat().st_size>2000)
    def test_unapproved_tiger_rig_rejected(self):
        from dex_lips.proof_render import load_rig, ProofError
        with self.assertRaises(ProofError):
            load_rig(ROOT/'examples/tiger_rig.unapproved.json',ROOT/'assets/references/tiger_original_canonical.jpg')
    def test_canonical_bytes_rejected_even_if_metadata_claims_synthetic(self):
        import json
        from dex_lips.proof_render import load_rig, ProofError
        original=ROOT/'assets/references/tiger_original_canonical.jpg'
        fake=json.loads((ROOT/'examples/tiger_rig.unapproved.json').read_text())
        fake['authority']='synthetic_demo'
        fake['approved']=True
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'rig.json'
            path.write_text(json.dumps(fake))
            with self.assertRaises(ProofError):
                load_rig(path,original)
    def test_overlap_cues_rejected(self):
        from dex_lips.proof_render import load_cues, ProofError
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'cues.json'
            p.write_text('{"mouthCues":[{"start":0,"end":1,"value":"D"},{"start":0.5,"end":1.5,"value":"X"}]}')
            with self.assertRaises(ProofError):
                load_cues(p,2.)
    def test_source_hash_gate(self):
        from proof_smoke import make_demo
        from dex_lips.proof_render import load_rig, ProofError
        with tempfile.TemporaryDirectory() as d:
            paths=make_demo(Path(d))
            with self.assertRaises(ProofError):
                load_rig(paths['still_rig'],paths['moving'])
if __name__=='__main__':unittest.main()
