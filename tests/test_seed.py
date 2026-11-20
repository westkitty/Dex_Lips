import json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class TestSeed(unittest.TestCase):
 def test_source_references_unchanged(self):
  cp=subprocess.run([sys.executable,str(ROOT/'scripts/verify_seed.py')],cwd=ROOT,text=True,capture_output=True)
  self.assertEqual(cp.returncode,0,cp.stdout+cp.stderr)
 def test_schema_files_parse(self):
  for name in ['rig','job']:
   data=json.loads((ROOT/f'schemas/{name}.schema.json').read_text())
   self.assertIn('$schema',data)
 def test_manifest_authority_order(self):
  m=json.loads((ROOT/'assets/references/SOURCE_MANIFEST.json').read_text())
  self.assertEqual([a['role'] for a in m['assets']], ['CANONICAL_PRIMARY', 'PROVISIONAL_NOT_CANON'])
 def test_no_approved_tiger_rig(self):
  rig=json.loads((ROOT/'examples/tiger_rig.unapproved.json').read_text())
  self.assertFalse(rig['approved'])
  self.assertEqual(rig['shapes'],{})
if __name__=='__main__':unittest.main()
