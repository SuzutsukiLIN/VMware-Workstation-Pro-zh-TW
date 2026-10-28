"""Build test translation for VMware Workstation 26.0.1 using existing supported ES locale.
Keep ES resource IDs and resource directory in original .rsrc. Surgical addition inside the .rsrc
section, moving .reloc and adjusting PE header directory pointers. Does not patch executable code.
"""
from __future__ import annotations
import sys, os, zipfile, struct, hashlib, collections, json, pathlib
from locale_merge import PE, translate_dialog, translate_menu, translate_stringtable, parse_dialog, parse_stringtable, parse_menu, align
from pathlib import Path
OUT = Path(__file__).resolve().parent.parent / 'payload' / 'es'
OUT.mkdir(parents=True, exist_ok=True)

def u32(b,p):return struct.unpack_from('<I',b,p)[0]
def list_entries(pe:PE):
  """Yield key, resource data pointer, language entry pointer, data len and payload offset from vendor resource tree."""
  b=pe.b;root=pe.rscoff;items=[]
  def name(d):
    if d&0x80000000:
      t=root+(d&0x7fffffff);n=struct.unpack_from('<H',b,t)[0]
      return b[t+2:t+2+2*n].decode('utf-16-le')
    return d
  def walk(rel,path):
    a=root+rel;nn,ni=struct.unpack_from('<HH',b,a+12)
    for i in range(nn+ni):
      entry=a+16+i*8
      tag,ptr=struct.unpack_from('<II',b,entry);key=name(tag)
      if ptr&0x80000000:walk(ptr&0x7fffffff,path+[key])
      else:
        da=root+ptr
        rva,size,cp,_=struct.unpack_from('<IIII',b,da)
        items.append(dict(key=tuple(path+[key]), entry=entry, data_entry=da, rva=rva, size=size, cp=cp, off=pe.rvaoff(rva)))
  walk(0,[])
  assert len(items)==len(pe.resources()),(len(items),len(pe.resources()))
  assert len(set(x['key'] for x in items))==len(items)
  return items

def checksum(data):
  chk=0
  for i in range(0,len(data)-1,2):
    chk += data[i] | data[i+1]<<8
    chk=(chk&0xffff)+(chk>>16)
  if len(data)%2:chk+=data[-1]
  chk=(chk&0xffff)+(chk>>16)
  chk=(chk&0xffff)+(chk>>16)
  return (chk+len(data))&0xffffffff

def patch_original_pe(b, updates):
  pe=PE(b);e=list_entries(pe);kmap={x['key'][:2]:x for x in e}
  assert len(kmap)==len(e), 'resource with more than one language under same name'
  assert all(k in kmap for k in updates)
  assert len(pe.sect)>=2 and pe.sect[-2][0]=='.rsrc' and pe.sect[-1][0]=='.reloc'
  rsc=pe.sect[-2];reloc=pe.sect[-1]
  assert rsc[4]+rsc[3]==reloc[4] and (pe.rscoff==rsc[4]);assert rsc[2]==pe.rscrva
  secpos=pe.ddstart+4*8; certoffset,certsz=struct.unpack_from('<II',b,secpos)
  assert certsz>0 and certoffset+certsz==len(b)
  assert certoffset>=reloc[4]+reloc[3]
  # Keep PE code and all current version 26.0.1 resource data untouched unless translated.
  section=bytearray(b[rsc[4]:rsc[4]+rsc[3]])
  larger=0;inplace=0;entries_changed=[]
  for k,t in updates.items():
    x=kmap[k];oldsize=x['size'];off_relative=x['off']-rsc[4]
    assert off_relative>=0 and off_relative+oldsize<=len(section)
    if len(t)<=oldsize:
      section[off_relative:off_relative+len(t)]=t
      # Leave dead tail bytes unreferenced, resource data entry size shrinks as necessary.
      new_rva=x['rva'];inplace+=1
    else:
      append_off=align(len(section),4)
      section.extend(b'\x00'*(append_off-len(section)))
      section.extend(t)
      new_rva=rsc[2]+append_off;larger+=1
    entry_rel=x['data_entry']-rsc[4]
    struct.pack_into('<II',section,entry_rel,new_rva,len(t))
    entries_changed.append((k,new_rva,len(t)))
  newvsize=len(section)
  newrawsz=align(newvsize,pe.filealign)
  section+=b'\x00'*(newrawsz-newvsize)
  new_reloc_va=align(rsc[2]+newvsize,pe.sectionalign)
  new_reloc_raw=rsc[4]+newrawsz
  prefix=bytearray(b[:rsc[4]])
  tail=b[reloc[4]:reloc[4]+reloc[3]]
  output=prefix+section+tail
  # In vendor image, no other section is after .reloc and .reloc is pure base reloc data.
  rsc_header=pe.opt+pe.optsz+(pe.nsects-2)*40
  reloc_header=pe.opt+pe.optsz+(pe.nsects-1)*40
  assert b[rsc_header:rsc_header+5]==b'.rsrc' and b[reloc_header:reloc_header+6]==b'.reloc'
  struct.pack_into('<I',output,rsc_header+8,newvsize)
  struct.pack_into('<I',output,rsc_header+16,newrawsz)
  struct.pack_into('<I',output,reloc_header+12,new_reloc_va)
  struct.pack_into('<I',output,reloc_header+20,new_reloc_raw)
  # Update .reloc data directory and image size. Resource directory stays at original vendor RVA.
  directory_count=struct.unpack_from('<I',output,pe.ddstart-4)[0]
  assert directory_count>5
  old_reloc_va,old_reloc_len=struct.unpack_from('<II',output,pe.ddstart+5*8)
  assert reloc[2]<=old_reloc_va<reloc[2]+max(reloc[1],reloc[3])
  struct.pack_into('<I',output,pe.ddstart+5*8,old_reloc_va+new_reloc_va-reloc[2])
  struct.pack_into('<I',output,pe.ddstart+2*8+4,newvsize)
  struct.pack_into('<I',output,pe.opt+56,align(new_reloc_va+max(reloc[1],reloc[3]),pe.sectionalign))
  # SizeOfInitializedData increases by new mapped .rsrc growth.
  sid=u32(output,pe.opt+8)
  struct.pack_into('<I',output,pe.opt+8,sid+(newrawsz-rsc[3]))
  # Authenticode signature is invalidated; explicitly clear existing security directory.
  struct.pack_into('<II',output,secpos,0,0)
  struct.pack_into('<I',output,pe.opt+64,0)
  struct.pack_into('<I',output,pe.opt+64,checksum(output))
  final=bytes(output)
  newpe=PE(final);verify=list_entries(newpe)
  b_before={(i['key']):b[i['off']:i['off']+i['size']] for i in e}
  b_after={i['key']:final[i['off']:i['off']+i['size']] for i in verify}
  assert set(b_before)==set(b_after)
  for key,content in b_after.items():
    assert content==updates.get(key[:2],b_before[key]), ('bad content',key)
  assert newpe.machine==pe.machine==0x8664 and newpe.nsects==pe.nsects
  assert newpe.rscrva==pe.rscrva
  assert len(final)<len(b)+500000
  # All original language IDs, including English PNG and Spanish dialogs, retained.
  assert [i['key'] for i in verify]==[i['key'] for i in e]
  # All non-resource code and relocation bytes kept byte-for-byte.
  for a in pe.sect[:-2]:
    n,vs,va,fs,fo=a
    assert final[fo:fo+fs]==b[fo:fo+fs]
  nr=newpe.sect[-1]
  assert final[nr[4]:nr[4]+nr[3]]==tail
  return final,dict(larger=larger,inplace=inplace,patched=len(entries_changed),total_resources=len(e),res_size_before=rsc[3],res_size_after=newrawsz,
                    original_size=len(b),patched_size=len(final),original_languages=dict(collections.Counter(x['key'][-1] for x in e)),
                    patched_languages=dict(collections.Counter(x['key'][-1] for x in verify)))

# QA for English vs Chinese text anchors
def check_text(blob, rid, expected):
  p=PE(blob)
  re=[x for x in p.resources() if x[0][0]==5 and x[0][1]==rid]
  assert len(re)==1
  x=re[0]
  d=parse_dialog(blob[x[4]:x[4]+x[2]])
  s='\n'.join(t['title'][1] for t in d['items'] if t['title'][0]=='string')
  for needle in expected:assert needle in s,(rid,needle,s)

def process(zold,znew,typ):
  oldb=zold.read(f'zh_TW/{typ}-zh_TW.dll');newb=znew.read(f'es/{typ}-es.dll')
  op=PE(oldb);np=PE(newb)
  oldr={tuple(x[0][:2]):oldb[x[4]:x[4]+x[2]] for x in op.resources()}
  updates={};c=collections.Counter();failed=[]
  for ent in np.resources():
    key=tuple(ent[0][:2]);kind=key[0]
    if key not in oldr:continue
    src=newb[ent[4]:ent[4]+ent[2]];older=oldr[key]
    try:
      if kind==5:res,why=translate_dialog(src,older)
      elif kind==4:res,why=translate_menu(src,older)
      elif kind==6:res,why=translate_stringtable(src,older)
      else:continue
      if res is None:
        failed.append((str(key),why));continue
      c[str(kind)]+=1
      if res!=src:
        updates[key]=res
    except Exception as ee:
      failed.append((str(key),str(ee)))
  assert not failed,failed
  # Manual quality correction for four wizard screens (also checks legacy typos).
  if typ=='vmappsdk':
    k=(5,9020)
    d=parse_dialog(updates[k]);changes=0
    for ctrl in d['items']:
      if ctrl['title'][0]!='string':continue
      s=ctrl['title'][1]
      swap={
        '選擇加密類型(&T)':'選擇加密範圍',
        '此虛擬機的所有檔案 (.vmdk、.vmx 等) 均已加密。':'加密此虛擬機的所有檔案（.vmdk、.vmx 等）',
        '只有支援 TPM 所需的檔案已加密。(.nvram、.vmss、.vmem、.vmx、.vmsn)':'僅加密支援虛擬 TPM 所需的檔案（.nvram、.vmss、.vmem、.vmx、.vmsn）',
        '確認密碼{(&M):':'確認密碼(&C)：',
        '密碼':'密碼(&P)：',
        '在此電腦上的憑據管理器中記住密碼(&R)':'在認證管理員中記住此虛擬機的密碼(&R)',
      }
      if s in swap:ctrl['title']=('string',swap[s]);changes+=1
    # encode same original dialog, replacing only template text (same structure/IDs/font/style)
    from locale_merge import enc_field
    b=bytearray(d['header']);b+=enc_field(d['menu'])+enc_field(d['cls'])+enc_field(d['title']);
    if d['font'] is not None:b+=d['font']
    for ni in d['items']:
      b.extend(b'\x00'*((-len(b))%4));b+=ni['head']+enc_field(ni['cls'])+enc_field(ni['title'])+struct.pack('<H',len(ni['extra']))+ni['extra']
    assert parse_dialog(bytes(b))['items'][0]['id']==d['items'][0]['id']
    updates[k]=bytes(b)
    print('Wizard 9020 terms corrected',changes)
  if typ=='vmappsdk':
    # Use the known-good 26.0.1 ES resource structures. Change only captions,
    # retaining control IDs, class, style, coordinates, and localized LANGIDs.
    fixes={
      9130: {
        '您希望使用什麼類型的配置?':'您想使用哪一種設定方式？',
        '典型(建議)(&T)':'典型（建議）(&T)',
        '自訂(進階)(&C)':'自訂（進階）(&C)',
        '建立帶有 SCSI 控制器類型、虛擬磁碟類型以及與舊版 VMware 產品相容性等進階選項的虛擬機。': '可設定 SCSI 控制器、虛擬磁碟類型，以及與舊版 VMware 產品的相容性。',
      },
      9060: {
        '虛擬機名稱(&V):':'虛擬機名稱(&V)：',
        '位置(&L):':'位置(&L)：',
        '在「編輯」>「選項」中可變更預設位置。':'可至「編輯」→「偏好設定」變更預設位置。',
      },
      9220: {
        '安裝來源:':'安裝來源：',
        '安裝程式光碟(&D):':'安裝光碟(&D)：',
        '安裝程式光碟映像檔案(iso)(&M):':'安裝光碟映像檔（ISO）(&M)：',
        '稍後安裝作業系統(&S)。':'稍後再安裝作業系統(&S)',
        '建立的虛擬機將包含一個空白硬盤。':'虛擬機將建立一顆空白虛擬硬碟。',
      },
      9020: {
        '僅加密支援虛擬 TPM 所需的檔案（.nvram、.vmss、.vmem、.vmx、.vmsn）': '僅加密 TPM 必要檔案（.nvram、.vmss、.vmem、.vmx、.vmsn）',
        '確認密碼(&C)：':'確認(&C)：',
      },
    }
    for dlg_id, mapping in fixes.items():
      k=(5,dlg_id)
      assert k in updates, ('missing dialog',k)
      dialog=parse_dialog(updates[k])
      seen={}
      for item in dialog['items']:
        if item['title'][0]=='string':
          before=item['title'][1]
          if before in mapping:
            assert before not in seen, (dlg_id,before)
            item['title']=('string',mapping[before])
            seen[before]=mapping[before]
      assert set(seen)==set(mapping),('Not found',dlg_id,set(mapping)-set(seen))
      from locale_merge import enc_field
      blob=bytearray(dialog['header'])
      blob+=enc_field(dialog['menu'])+enc_field(dialog['cls'])+enc_field(dialog['title'])
      if dialog['font'] is not None:blob+=dialog['font']
      for item in dialog['items']:
        blob.extend(b'\x00'*((-len(blob))%4))
        blob+=item['head']+enc_field(item['cls'])+enc_field(item['title'])+struct.pack('<H',len(item['extra']))+item['extra']
      restored=parse_dialog(bytes(blob))
      assert [(x['id'],x['cls'],x['head']) for x in restored['items']]==[(x['id'],x['cls'],x['head']) for x in dialog['items']]
      updates[k]=bytes(blob)
      print('Dialog QA improved',dlg_id,len(seen))
  output,qa=patch_original_pe(newb,updates)
  if typ=='vmappsdk':
    check_text(output,9130,['歡迎使用新增虛擬機精靈','典型（建議）','自訂（進階）'])
    check_text(output,9220,['安裝來源：','安裝光碟'])
    check_text(output,9060,['虛擬機名稱','位置'])
    check_text(output,9020,['選擇加密範圍','加密此虛擬機的所有檔案','確認(&C)'])
  path=OUT/f'{typ}-es.dll';path.write_bytes(output)
  qa.update(filename=path.name,sha256=hashlib.sha256(output).hexdigest(),original_sha256=hashlib.sha256(newb).hexdigest(),type_count=dict(c),failures=failed)
  return qa
