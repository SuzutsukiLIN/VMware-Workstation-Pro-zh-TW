#!/usr/bin/env python3
"""Create a *local-use* VMware Workstation 26.0.1 ES-compatible Traditional Chinese payload.

Input materials must be obtained by the user under their own VMware license.
No VMware binary or full localized .vmsg is stored in this public source tree.
"""
from __future__ import annotations
import argparse, contextlib, hashlib, json, os, re, sys, tempfile, zipfile
from pathlib import Path
import locale_merge
import patch_es

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'payload' / 'es'
VM26 = {
 'vmappsdk-es.dll': 'e4439165a3b9b11b3321297c0a55d4d92bf832b5f03a10ee7e00063ac0014b20',
 'vmui-es.dll': 'fd5154dbbcf04eeca18eb3928319c3479427edb33b615820a65624f198dea73d',
 'vmware.vmsg': 'acf2c68d3dc38c5476b8874f5728c014810c66fc964e858fbcce4c9de717ebab',
}
VM_OLD = {
 'vmappsdk-zh_TW.dll': '78aec90040f7702b16889564c1b34ed358b845f8682760389cadf4904a9ea422',
 'vmui-zh_TW.dll': '6a23432cd62a4e06c31bb99e98aca434a2a6fe8463b8b644f700f6f46d295dbe',
 'vmware.vmsg': 'ee973d8dffb1de0c75c41e0ff94ee385c10258ff6ebf60fa109cda0dce60568d',
}
EXPECTED_OUT = {
 'vmappsdk-es.dll': '3f19def65c3eae70620aa31deecedc74ae7bf334e88bbe35e0b1f9479b0a52dc',
 'vmui-es.dll': '320cb4ccbcf7f8118e4855ab7352d9fc6ccf03599f459333fbc0fe3e458fe0b8',
 'vmware.vmsg': '895d68bbbdf1701b4526ed831bdc5d61a3f47fd21896455fe8d6ce9c48748798',
}

def sha(b: bytes) -> str: return hashlib.sha256(b).hexdigest()

def verify_zip(z: zipfile.ZipFile, prefix: str, hashes: dict[str,str]):
 for name,want in hashes.items():
  key=f'{prefix}/{name}'
  if key not in z.namelist():raise RuntimeError(f'Missing input: {key}')
  actual=sha(z.read(key))
  if actual!=want:raise RuntimeError(f'Unsupported source {key}, SHA256={actual}; expected {want}')

def replace_vmsg_for_v12(data:bytes)->bytes:
 text=data.decode('utf-8-sig')
 updates=[
  ('msg.cui.wizard.vm.descriptionTypical','通過幾個簡單的步驟建立 %1$s 虛擬機。','建立 %1$s 虛擬機。'),
  ('msg.cui.wizard.vm.guestid.subtitle','虛擬機如同物理機，需要作業系統。您將如何安裝虛擬機作業系統?','虛擬機需要作業系統。請選擇安裝方式。'),
 ]
 for key,old,new in updates:
  rx=r'(?m)^'+re.escape(key+' = "'+old+'"')+r'(?=\r?$)'
  text,n=re.subn(rx,lambda m:key+' = "'+new+'"',text)
  if n!=1:raise RuntimeError(f'Unexpected translation source: {key} ({n} matches)')
 return b'\xef\xbb\xbf'+text.replace('\r\n','\n').encode('utf-8')

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--old',type=Path,required=True,help='Locally owned VM legacy zh_TW ZIP (zh_TW/*.dll and vmsg)')
 parser.add_argument('--new',type=Path,help='Locally owned 26.0.1 ES ZIP (es/*.dll and vmsg); default: read installed VMware')
 a=parser.parse_args()
 if not a.old.is_file():parser.error('Old locale ZIP not found')
 tmpdir=None
 if a.new is None:
  # Running locally on Windows with the correct VMware version installed.
  pf=os.environ.get('ProgramFiles','C:/Program Files')
  es=Path(pf)/'VMware'/'VMware Workstation'/'messages'/'es'
  if not es.is_dir():parser.error('26.0.1 Spanish language files not found. Use --new path.zip')
  tmpdir=tempfile.TemporaryDirectory()
  a.new=Path(tmpdir.name)/'native_es.zip'
  with zipfile.ZipFile(a.new,'w',compression=zipfile.ZIP_STORED) as z:
   for n in VM26:z.write(es/n,'es/'+n)
 try:
  with zipfile.ZipFile(a.old) as zold,zipfile.ZipFile(a.new) as znew:
   verify_zip(zold,'zh_TW',VM_OLD)
   verify_zip(znew,'es',VM26)
   OUT.mkdir(parents=True,exist_ok=True)
   locale_merge.OUTDIR=OUT
   patch_es.OUT=OUT
   print('[1/4] Merge localized string keys and validate format placeholders...')
   locale_merge.merged_vmsg(zold,znew)
   print('[2/4] Create 26.0.1 ES-compatible translated resource DLLs...')
   for typ in ('vmappsdk','vmui'):
    qa=patch_es.process(zold,znew,typ)
    print(' ',typ,qa['patched'], 'resource entries updated')
   print('[3/4] Apply v1.2 text refinements...')
   (OUT/'vmware.vmsg').write_bytes(replace_vmsg_for_v12((OUT/'vmware.vmsg').read_bytes()))
   print('[4/4] Verify exact reproducibility...')
   for name,want in EXPECTED_OUT.items():
    actual=sha((OUT/name).read_bytes())
    if actual!=want:raise RuntimeError(f'Output integrity check failed: {name} / {actual}')
   print('OK. Local-use payload prepared at:',OUT)
 except Exception:
  # Never leave a partial payload that could be accidentally installed.
  for name in EXPECTED_OUT:(OUT/name).unlink(missing_ok=True)
  raise
 finally:
  if tmpdir:tmpdir.cleanup()

if __name__=='__main__':main()
