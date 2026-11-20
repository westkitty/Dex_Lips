"""Adversarial job and Rhubarb adapter tests; fake Rhubarb != real phoneme proof."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT),str(ROOT/'src'),str(ROOT/'scripts')]
READY = importlib.util.find_spec('PIL') is not None and shutil.which('ffmpeg') and shutil.which('ffprobe')

@unittest.skipUnless(READY, 'Requires Pillow/FFmpeg; not a verified media runtime')
class TestSpeechJobs(unittest.TestCase):
    def setUp(self):
        from proof_smoke import make_demo
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)
        self.example = make_demo(self.work)

    def rig_archive(self, name='rig.zip'):
        target = self.work / name
        with zipfile.ZipFile(target, 'w') as z:
            for shape in 'XDB':
                z.write(self.work/f'{shape}.png', arcname=f'{shape}.png')
        return target

    def test_explicit_user_approval_required(self):
        from dex_lips.jobs import unpack_user_rig
        from dex_lips.proof_render import ProofError
        with self.assertRaises(ProofError):
            unpack_user_rig(self.rig_archive(),self.example['still'],self.work/'blocked',
                            {'x':.5,'y':.5,'scale':1,'rotation_deg':0},user_approved=False)

    def test_user_art_rig_is_not_canon(self):
        from dex_lips.jobs import unpack_user_rig
        rig = unpack_user_rig(self.rig_archive(),self.example['still'],self.work/'approved',
                              {'x':.5,'y':.5,'scale':1,'rotation_deg':0},user_approved=True)
        config=json.loads(rig.read_text())
        self.assertEqual(config['authority'],'approved_user_rig')
        self.assertNotIn('canonical',config['authority'])

    def test_canonical_primary_source_rejected_even_when_approved(self):
        from dex_lips.jobs import unpack_user_rig
        from dex_lips.proof_render import ProofError
        with self.assertRaises(ProofError):
            unpack_user_rig(self.rig_archive(),ROOT/'assets/references/tiger_original_canonical.jpg',
                            self.work/'no_tiger',{'x':.5,'y':.2,'scale':1,'rotation_deg':0},user_approved=True)

    def test_zip_path_traversal_rejected(self):
        from dex_lips.jobs import unpack_user_rig
        from dex_lips.proof_render import ProofError
        z=self.work/'evil.zip'
        with zipfile.ZipFile(z,'w') as f:
            f.writestr('../../outside.png',b'data')
            f.write(self.work/'X.png','X.png')
            f.write(self.work/'D.png','D.png')
        with self.assertRaises(ProofError):
            unpack_user_rig(z,self.example['still'],self.work/'badzip',
                            {'x':.5,'y':.5,'scale':1,'rotation_deg':0},user_approved=True)
        self.assertFalse((self.work/'outside.png').exists())

    def test_missing_rhubarb_does_not_fake_speech(self):
        from dex_lips.speech import analyze
        from dex_lips.proof_render import ProofError
        with self.assertRaisesRegex(ProofError,'Rhubarb binary is not installed'):
            analyze(self.example['audio'],self.work/'missing.json',executable='missing_rhubarb_12345')
        self.assertFalse((self.work/'missing.json').exists())

    def test_rhubarb_adapter_invokes_binary_on_audio_and_validates_json(self):
        """Proves external command wiring, not recognizer correctness."""
        from dex_lips.speech import analyze
        fake = self.work/'rhubarb_stub'
        fake.write_text('''#!/usr/bin/env python3
import json,sys,wave
from pathlib import Path
args=sys.argv[1:]
assert args[-1].endswith('.wav')
assert '--exportFormat' in args and 'json' in args
assert '--recognizer' in args and 'pocketSphinx' in args
with wave.open(args[-1]) as audio: seconds=audio.getnframes()/audio.getframerate()
Path(args[args.index('--output')+1]).write_text(json.dumps({'mouthCues':[{'start':0,'end':round(seconds,2),'value':'X'}]}))
''')
        fake.chmod(0o755)
        out=self.work/'analyzed.json'
        result=analyze(self.example['audio'],out,dialog='Testing sound',executable=str(fake))
        self.assertEqual(result['cue_count'],1)
        self.assertTrue(out.is_file())
        self.assertEqual(json.loads(out.read_text())['metadata']['analysis'],'rhubarb')

    def test_spoken_voice_ui_source_to_mp4_with_manually_reviewed_cues(self):
        """Real speech audio, but manual timing; cannot prove automatic recognizer."""
        if not shutil.which('espeak'):
            self.skipTest('espeak unavailable for spoken test fixture')
        from app import render_uploaded
        audio=self.work/'spoken.wav'
        subprocess.run(['espeak','-w',str(audio),'Hello there'],check=True,timeout=10)
        c={'mouthCues':[{'start':0,'end':.2,'value':'X'}, {'start':.2,'end':.55,'value':'D'}, {'start':.55,'end':.75,'value':'B'}]}
        mp4, download, receipt, status=render_uploaded(str(self.example['still']),str(audio),str(self.rig_archive()),
              json.dumps(c),'',.5,.61,1,0,24,True,False)
        self.assertIn('Rendered and verified',status)
        self.assertEqual(mp4,download)
        subprocess.run(['ffmpeg','-v','error','-xerror','-i',mp4,'-f','null','-'],check=True,timeout=20)
        self.assertIn('USER_REVIEWED',json.loads(Path(receipt).read_text())['mouth_cue_provenance'])

    def test_video_requires_neutral_mouth_acknowledgement(self):
        from app import render_uploaded
        c=json.dumps({'mouthCues':[{'start':0,'end':.32,'value':'X'},{'start':.32,'end':.84,'value':'D'},{'start':.84,'end':2,'value':'B'}]})
        video,out,receipt,status=render_uploaded(str(self.example['moving']),str(self.example['audio']),str(self.rig_archive()),c,'',.5,.61,1,0,24,True,False)
        self.assertIsNone(video)
        self.assertIn('neutral or masked',status)

    def test_video_ui_with_approved_mouth_and_keyframes(self):
        from app import render_uploaded
        c=self.example['cues'].read_text()
        k=self.example['track'].read_text()
        video,out,receipt,status=render_uploaded(str(self.example['moving']),str(self.example['audio']),str(self.rig_archive()),
                   c,k,.5,.61,1,0,24,True,True)
        self.assertIn('Rendered and verified',status)
        self.assertEqual(json.loads(Path(receipt).read_text())['mode'],'video')
        subprocess.run(['ffmpeg','-v','error','-xerror','-i',video,'-f','null','-'],check=True,timeout=20)

if __name__ == '__main__':unittest.main()

@unittest.skipUnless(READY, 'Requires Pillow/FFmpeg')
class TestPortraitResize(unittest.TestCase):
    def test_original_portrait_dimensions_can_render_downscaled_without_mutation(self):
        from PIL import Image
        from dex_lips.proof_render import render, sha256
        from proof_smoke import make_demo
        with tempfile.TemporaryDirectory() as td:
            d=Path(td);example=make_demo(d)
            portrait=d/'portrait.png'
            with Image.open(example['still']) as photo:
                photo.resize((1024,1536)).save(portrait)
            before=sha256(portrait)
            rig_data=json.loads(example['still_rig'].read_text())
            rig_data['source_path']=portrait.name
            rig_data['source_sha256']=before
            rig=d/'portrait_rig.json'
            rig.write_text(json.dumps(rig_data))
            res=render(portrait,example['audio'],rig,example['cues'],d/'portrait.mp4')
            self.assertEqual(res['source_size'],[1024,1536])
            self.assertEqual(res['output_size'],[480,720])
            self.assertEqual(sha256(portrait),before)
            subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(d/'portrait.mp4'),'-f','null','-'],check=True,timeout=20)
