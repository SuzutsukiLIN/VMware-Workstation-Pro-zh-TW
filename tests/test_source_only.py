import pathlib, unittest, subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]

class TestReleaseSafety(unittest.TestCase):
 def test_no_proprietary_payload_tracked_in_git(self):
  ignore=(ROOT/'.gitignore').read_text(encoding='utf-8')
  self.assertIn('/payload/es/*',ignore)
  self.assertIn('!/payload/es/.gitkeep',ignore)
  if (ROOT/'.git').is_dir():
   result=subprocess.run(['git','ls-files','--','payload/es'],cwd=ROOT,capture_output=True,text=True,check=True)
   self.assertEqual(result.stdout.strip(),'payload/es/.gitkeep')
 def test_cmd_files_are_ascii_without_bom(self):
  for p in ROOT.glob('*.cmd'):
   b=p.read_bytes()
   self.assertEqual(b[:1],b'@',p)
   b.decode('ascii')
 def test_powershell_is_utf8_bom(self):
  self.assertTrue((ROOT/'scripts'/'LocaleInstaller.ps1').read_bytes().startswith(b'\xef\xbb\xbf'))
 def test_installer_has_guards_and_shortcut(self):
  content=(ROOT/'scripts'/'LocaleInstaller.ps1').read_text(encoding='utf-8-sig')
  for t in ['25688693','--locale=es','Get-FileHash','Find-LegacyNativeBackup','Copy-Three','CreateShortcut','Remove-Shortcut','Get-VMwareRoot']:
   self.assertIn(t,content)

if __name__=='__main__':unittest.main()
