import sys,os,struct,zipfile,re,hashlib,json,collections
from pe_resource_inspect import PE
from pathlib import Path

# The public repository does not include VMware binary assets.
OUTDIR=Path(__file__).resolve().parent.parent / 'payload' / 'es'
OUTDIR.mkdir(exist_ok=True,parents=True)

# New message translations for keys that were not present in the legacy locale.
added_texts='''
button.guestArmFreeBSD16_64 = FreeBSD 16（ARM 64 位元）
button.guestArmOracle11_64 = Oracle Linux 11（ARM 64 位元）
button.guestArmRHEL11_64 = Red Hat Enterprise Linux 11（ARM 64 位元）
button.guestDarwin25_64 = macOS 26
button.guestDarwin26_64 = macOS 27
button.guestFreeBSD16_64 = FreeBSD 16（64 位元）
button.guestOracle11_64 = Oracle Linux 11（64 位元）
button.guestRHEL11_64 = Red Hat Enterprise Linux 11（64 位元）
button.guestWin2028srv_64 = Windows Server 2028
msg.bios.firmwareChangeNotAllowed = 只有在虛擬機器電源關閉時才能變更韌體。
msg.checkpoint.vhvNotCompatibleWithHost = 無法還原虛擬機器，因為主機 Hypervisor 支援的巢狀虛擬化與其他虛擬化平台不相容。|0A
msg.cpuid.guestOSMissingFeatures = 此虛擬機器缺少 %4$s 客體作業系統所需的功能：%1$s%2$s%3$s，因此無法開啟電源。
msg.cpuid.guestOSMissingFeaturesEVC = 目前的 EVC 模式遮蔽了 %4$s 客體作業系統所需的功能：%1$s%2$s%3$s。無法開啟此虛擬機器的電源。
msg.cui.createVM.noIDEonArm = ARM 虛擬機器不支援 IDE 裝置。
msg.cui.createVM.shortNoIDEonArm = ARM 虛擬機器不支援
msg.cui.downloadMgr.toolsInstallGuide = 此客體作業系統的 VMware Tools 不再隨 %1$s 一同提供。請參閱 %2$s 以安裝 open-vm-tools。
msg.cui.encryptedVM.oldEncryptionTypeFmt = 此虛擬機器使用舊版加密演算法。您可以將其升級為最新支援的加密模式，但升級可能影響向下相容性，使虛擬機器無法在舊版 %1$s 中使用。如需詳細資訊，請參閱以下知識庫文章：|0A|0A%2$s
msg.cui.hardwareVersion.vmHW22Desc = Workstation 25H2 或更新版本的虛擬機器
msg.cui.hardwareVersion.vmHW22Desc.fusion = Fusion 25H2 或更新版本的虛擬機器
msg.cui.ovftool.download.noThumbprint = 無法開始下載：無法取得 SSL 憑證指紋。
msg.cui.ovftool.upload.noThumbprint = 無法開始上傳：無法取得 SSL 憑證指紋。
msg.cui.truncatedMessageFormat = %1$s...
msg.disk.multiwriterDigestIncompat = 無法同時啟用磁碟摘要及多重寫入共用功能。
msg.disk.vigor.revert.parentOfLinkedClone = 無法還原磁碟鏈，因為一個或多個連結複製虛擬機器依賴快照 path='%1$s'。
msg.dumper.error.badMemory = 儲存虛擬機器記憶體時，在客體系統中偵測到記憶體錯誤（ECC 資料毀損）。建議檢查並更換故障記憶體。
msg.ehv.noValidLicense = 無法開啟虛擬機器的電源，因為目前的 %1$s 授權不支援加密硬體虛擬化（AMD SEV 或 Intel TDX）。
msg.gostable8.guest.arm-centos9-64 = CentOS 9（ARM 64 位元）
msg.gostable8.guest.arm-debian14-64 = Debian 14（ARM 64 位元）
msg.gostable8.guest.arm-freeBSD16-64 = FreeBSD 16（ARM 64 位元）
msg.gostable8.guest.arm-oraclelinux11-64 = Oracle Linux 11（ARM 64 位元）
msg.gostable8.guest.arm-rhel11-64 = Red Hat Enterprise Linux 11（ARM 64 位元）
msg.gostable8.guest.arm-sles15-64 = SUSE Linux Enterprise 15（ARM 64 位元）
msg.gostable8.guest.arm-sles16-64 = SUSE Linux Enterprise 16（ARM 64 位元）
msg.gostable8.guest.darwin25-64 = macOS 26
msg.gostable8.guest.darwin26-64 = macOS 27
msg.gostable8.guest.debian14-64 = Debian 14.x（64 位元）
msg.gostable8.guest.freeBSD16-64 = FreeBSD 16（64 位元）
msg.gostable8.guest.oraclelinux11-64 = Oracle Linux 11（64 位元）
msg.gostable8.guest.rhel11-64 = Red Hat Enterprise Linux 11（64 位元）
msg.gostable8.guest.windows2025srvNext-64 = Windows Server 2028
msg.guestVarCtl.cfgLimitExceeded = GuestVariable 存取控制設定超過上限（%1$u）。
msg.migrate.RPC.enable.failure = 無法在主機上啟用 RPC。|0A
msg.migrate.device.data.stream.failed = 無法傳輸裝置資料串流。
msg.migrate.stun.overtime.slow.diskclose = 由於磁碟關閉作業過慢，移轉作業逾時並失敗。|0A
msg.pAndM.insufficientHotplugMemorySize = 請將客體記憶體大小增加至至少 %1$u MB，以觸發熱插拔事件。
msg.pciPassthru.ignoreDmar = 已忽略此虛擬機器所有 PCI 裝置直通的 DMA 重新對應功能。此虛擬機器的資料不受保護，可能遭受 PCI 直通裝置的 DMA 攻擊。
msg.pciPassthru.initVMFailed = 無法初始化 PCI 裝置直通。
msg.pciPassthru.viommuWithP2P = 無法開啟虛擬機器的電源，因為虛擬 IOMMU 與點對點（P2P）通訊不相容。若要開啟電源，請停用虛擬 IOMMU 或停用 P2P。
msg.sev.init.esDisabled = 無法開啟 SEV-ES 虛擬機器的電源，因為 SEV-SNP 已啟用。
msg.sev.snp.finishLaunchFailure = 啟用 ID 區塊驗證時，無法完成 SEV-SNP 客體系統啟動。虛擬機器將關閉電源。
msg.snapshot.enc.safe = 存在快照時，無法變更虛擬機器的加密狀態。
msg.snapshot.enc.safeClone = 無法變更連結複製虛擬機器的加密狀態。
msg.snapshot.vigor.repairNativeCheck.error = 無法檢查虛擬機器的原生快照是否損毀：%1$s。
msg.snapshot.vigor.repairNativeRepair.error = 無法修復虛擬機器的原生快照損毀：%1$s。
msg.tdx.attestationRequired = 無法開啟虛擬機器的電源，因為虛擬機器設定為使用 TDX，但未啟用 SGX 記錄功能。
msg.tdx.hpetRequired = 無法開啟虛擬機器的電源，因為 TDX 需要高精確度事件計時器（HPET）裝置。
msg.timeTracker.computeBusMultiplier.tdxEnabled = 無法開啟虛擬機器的電源，因為 Intel TDX 不支援非預設匯流排倍頻。
msg.uefi.secureboot.lockdown.incorrectHWVersion = 已啟用 UEFI 安全開機鎖定模式，但目前的虛擬硬體版本不支援此功能。|0A虛擬機器即將關閉電源。
msg.uefi.secureboot.lockdown.noFv = 已為此虛擬機器啟用 UEFI 安全開機鎖定模式，但指定的 EFI 映像缺少必要區段。
msg.uefi.secureboot.lockdown.noMeasuredFv = 已為此機密虛擬機器啟用 UEFI 安全開機鎖定模式，但指定的 EFI 映像缺少測量變數區段。
msg.uefi.secureboot.lockdown.sbDisabled = 已啟用 UEFI 安全開機鎖定模式，但尚未啟用 UEFI 安全開機。|0A虛擬機器即將關閉電源。
msg.vmui.statusVM.vmCreateDate = 建立日期：
msg.vmui.statusVM.vmLastPowerRequestTimestamp = 上次要求開啟電源時間：
msg.vmui.vmuiStatusFolder.detail.notes = 備註
msg.vpmc.tdx = 啟用 TDX 的虛擬機器不支援虛擬化效能計數器。
msg.wui.dialog.USBIconPickerImpl.bluetooth = Bluetooth
msg.wui.ellipsizedText = %1$s...
msg.wui.proppage.advanced.memTrim = 允許釋放記憶體頁面(&M)
msg.wui.proppage.advanced.sideChannelMitigations = 針對啟用 Hyper-V 的主機啟用側通道緩解措施(&C)
msg.wui.proppage.metadata.PortTooLarge = 裝置連接埠號碼無效。連接埠號碼必須介於 %1$d 至 %2$d 之間。
msg.wui.proppage.metadata.dateTimeFormat = %1$s %2$s
msg.wui.proppage.metadata.lblAuthor = 作者(&A)：
msg.wui.proppage.metadata.lblCreatedOn = 建立日期(&C)：
msg.wui.proppage.metadata.lblVersion = 版本(&V)：
msg.wui.proppage.metadata.mainGroup = 中繼資料
msg.wui.proppage.metadata.noPort = 必須指定連接埠號碼。
msg.wui.proppage.metadata.notesGroup = 備註(&N)
msg.wui.proppage.metadata.portLabel = 虛擬機器內的虛擬裝置存取連接埠(&P)：
msg.wui.proppage.metadata.portLabelAcc = 連接埠號碼
msg.wui.proppage.metadata.summaryFmt = 連接埠：%1$u
msg.wui.proppage.metadata.title = 中繼資料
msg.wui.proppage.metadata.unknownDate = （未知）
msg.wui.proppage.usb.usb32 = USB 3.2
msg.wui.tooltip.title.generic = 應用程式訊息
msg.wui.wizard.encryption.description = 此客體作業系統需要虛擬信賴平台模組（TPM）。|0A|0A虛擬 TPM 的資料必須使用密碼加密。請務必妥善保存此密碼，否則將無法使用此虛擬機器。
'''

def merged_vmsg(z1,z2):
 a=z1.read('zh_TW/vmware.vmsg').decode('utf-8-sig')
 b=z2.read('es/vmware.vmsg').decode('utf-8-sig')
 rx=re.compile(r'^(?P<k>[^\s#][^=]*?)\s*=\s*"(?P<v>.*)"\s*$')
 old={m['k'].strip():m['v'] for l in a.splitlines() if (m:=rx.match(l))}
 new={m['k'].strip():m['v'] for l in b.splitlines() if (m:=rx.match(l))}
 translations={}
 for line in added_texts.strip().splitlines():
  k,v=line.split(' = ',1)
  assert k not in translations,k
  translations[k]=v
 missing=set(new)-set(old)
 assert missing==set(translations),(len(missing),len(translations),missing^set(translations))
 args_rx=re.compile(r'(?<!%)%(?!%)(?:[1-9]\d*\$)?[-+ #0]*(?:\d+|\*)?(?:\.\d+)?(?:I64)?[a-zA-Z]')
 placeholder_updates={
  'msg.checkpoint.inConsistentCoresPerSocket':'暫停的映像包含 coresPerSocket 值（%1$u），與虛擬機器實際的 coresPerSocket 值（%2$u）不相符。',
  'msg.cui.VMTicketingVIM.queueTimeout':'佇列中的 MKS 憑證取得作業在 %1$I64d 毫秒後逾時。',
  'msg.cui.certificateCheck.errorMsg.otherError':'其他錯誤：%1$I64u。',
  'msg.cui.ovftool.manyErrors':'匯入作業發生超過 %1$I64u 個錯誤。您嘗試匯入的 OVF 可能已損毀，或使用不受支援的舊版本。前 %2$I64u 個錯誤如下：|0A|0A',
  'msg.cui.restrictedVM.errorMsg.unsupported':'不支援受限制的虛擬機器。',
  'msg.cui.vmCryptoVMDB.genericReencryptFail':'無法重新加密虛擬機器。請重新啟動 %1$s，稍後再試。',
  'msg.e.invalidCompressionLevel':'指定的壓縮等級（%1$d）無效。',
  'msg.vmui.library.remoteShortcutFmt':'%2$S 上的 %1$S',
  'msg.vmui.wsProFmt':'%1$s Pro',
  'msg.vvtd.dvxNotSupported':'無法開啟虛擬機器的電源，因為虛擬 VT-D 與目前虛擬機器版本「%1$d」的 Enhanced DirectPath I/O 不相容，至少需要版本「%2$d」。',
  'msg.wui.proppage.nicAdvanced.packetLossOutOfRangeFmt':'封包遺失百分比必須介於 %1$.1f 與 %2$.1f 之間。',
  'msg.dynmenu.remDevice.errorConnect':'無法連線 %1$s：|0A%s',
 }
 known_malformed_source={'msg.wui.proppage.nicAdvanced.packetLossOutOfRangeFmt'}
 args_diff=[]
 out=[]
 for k,v in new.items():
  if k in old:
   o=old[k]
   trans=placeholder_updates.get(k,o)
   if k not in placeholder_updates and ('%1$I64' in v):
    trans=re.sub(r'%(\d+\$)I([du])', r'%\1I64\2',trans)
   if collections.Counter(args_rx.findall(trans))!=collections.Counter(args_rx.findall(v)):
    args_diff.append((k,trans,v))
    if k not in known_malformed_source:
     trans=v
  else:trans=translations[k]
  if k in missing:
   assert collections.Counter(args_rx.findall(trans))==collections.Counter(args_rx.findall(v)),(k,trans,v)
  assert '"' not in k
  out.append(f'{k} = "{trans}"')
 (OUTDIR/'vmware.vmsg').write_bytes(b'\xef\xbb\xbf'+('\r\n'.join(out)+'\r\n').encode('utf-8'))
 print('VMSG: merged',len(out),'kept old',len(old.keys()&new.keys()),'newly translated',len(missing),'format-mismatches',len(args_diff))
 for x in args_diff[:30]:print('  placeholder mismatch',x)
 return args_diff

# Dialog template parser and safe string merger for Win32 std/ex dialog resources
class Reader:
 def __init__(self,b):self.b=b;self.p=0
 def read(self,n):
  q=self.b[self.p:self.p+n];assert len(q)==n;self.p+=n;return q
 def word(self):return struct.unpack('<H',self.read(2))[0]
 def dword(self):return struct.unpack('<I',self.read(4))[0]
 def align(self,a=4):self.p=(self.p+a-1)//a*a
 def field(self):
  a=self.word()
  if a==0:return ('none',None)
  if a==0xffff:return ('ordinal',self.word())
  words=[a]
  while True:
   x=self.word()
   if x==0:break
   words.append(x)
  return ('string',struct.pack('<'+'H'*len(words),*words).decode('utf-16-le'))

def enc_field(a):
 t,v=a
 if t=='none':return b'\0\0'
 if t=='ordinal':return struct.pack('<HH',0xffff,v)
 if t=='string':return v.encode('utf-16-le')+b'\0\0'
 raise Exception('invalid field')

def parse_dialog(b):
 r=Reader(b);ext=b[:4]==b'\x01\x00\xff\xff'; fixedsize=26 if ext else 18
 header=r.read(fixedsize)
 style=struct.unpack_from('<I',header,12 if ext else 0)[0]
 cdit=struct.unpack_from('<H',header,16 if ext else 8)[0]
 menu=r.field();cls=r.field();title=r.field()
 font=None
 if style & 0x40:
  h=r.read(6 if ext else 2)
  ff=r.field();assert ff[0]=='string';font=h+enc_field(ff)
 firstitems=[]
 for idx in range(cdit):
  r.align()
  head=r.read(24 if ext else 18)
  icls=r.field();ititle=r.field();esize=r.word();extra=r.read(esize)
  id_=struct.unpack_from('<I' if ext else '<H',head,20 if ext else 16)[0]
  if id_==0xffff:id_=0xffffffff
  firstitems.append({'head':head,'cls':icls,'title':ititle,'extra':extra,'id':id_})
 assert r.p==len(b),(r.p,len(b),ext,cdit)
 return {'header':header,'extended':ext,'menu':menu,'cls':cls,'title':title,'font':font,'items':firstitems}

def translate_dialog(new,old):
 n=parse_dialog(new);o=parse_dialog(old)
 if len(n['items'])!=len(o['items']):return None,'different_control_count'
 for a,b in zip(n['items'],o['items']):
  if a['id']!=b['id'] or a['cls']!=b['cls']:
   return None,'different_control_identity'
 def translation(f,e):
  if f[0]=='string' and e[0]=='string' and e[1] and f[1]:return e
  return f
 output=bytearray(n['header']);output+=enc_field(n['menu'])+enc_field(n['cls'])+enc_field(translation(n['title'],o['title']))
 if n['font'] is not None:output+=n['font']
 changed=0
 if n['title']!=o['title'] and n['title'][0]=='string':changed+=1
 for ni,oi in zip(n['items'],o['items']):
  output.extend(b'\0' * ((-len(output))%4))
  output+=ni['head']+enc_field(ni['cls'])+enc_field(translation(ni['title'],oi['title']))+struct.pack('<H',len(ni['extra']))+ni['extra']
  if ni['title']!=oi['title'] and ni['title'][0]=='string' and oi['title'][0]=='string':changed+=1
 x=bytes(output)
 try:assert parse_dialog(x)['items'][0]['id']==n['items'][0]['id'] if n['items'] else True
 except Exception as e:return None,f'repack_failed:{e}'
 return x,f'ok:{changed}'

def parse_menu(b):
 r=Reader(b);version=r.word();offset=r.word();assert version==0,version
 prefix=r.read(offset);items=[]
 def node():
  start=r.p;flags=r.word();popup=bool(flags&0x10);end=bool(flags&0x80)
  cmd=None if popup else r.word()
  title=r.field();assert title[0] in ['none','string']
  child=[]
  if popup:
   while True:
    it=node();child.append(it)
    if it['end']:break
  return dict(flags=flags,popup=popup,end=end,id=cmd,title=title,children=child)
 while r.p<len(b):
  m=node();items.append(m)
  if m['end']:break
 assert r.p==len(b),(r.p,len(b))
 return version,offset,prefix,items

def translate_menu(new,old):
 try:
  v,off,pre,ns=parse_menu(new);_,_,_,os=parse_menu(old)
  def check(ns,os):
   if len(ns)!=len(os):return False
   for n,o in zip(ns,os):
    if n['popup']!=o['popup'] or n['id']!=o['id'] or n['end']!=o['end']:return False
    if n['popup'] and not check(n['children'],o['children']):return False
   return True
  if not check(ns,os):return None,'different_menu_structure'
  output=bytearray(struct.pack('<HH',v,off)+pre)
  def dump(ns,os):
   for n,o in zip(ns,os):
    output.extend(struct.pack('<H',n['flags']))
    if not n['popup']:output.extend(struct.pack('<H',n['id']))
    title = o['title'] if o['title'][0]=='string' and o['title'][1] and n['title'][0]=='string' else n['title']
    output.extend(enc_field(title))
    if n['popup']:dump(n['children'],o['children'])
  dump(ns,os);x=bytes(output);assert len(parse_menu(x)[-1])==len(ns)
  return x,'ok'
 except Exception as e:return None,f'error:{e}'

def parse_stringtable(b):
 r=Reader(b);z=[]
 for i in range(16):
  ln=r.word();z.append(r.read(ln*2).decode('utf-16-le'))
 assert r.p==len(b)
 return z

def translate_stringtable(new,old):
 try:
  aa=parse_stringtable(old);bb=parse_stringtable(new);z=[]
  for i in range(16):z.append(aa[i] if aa[i] and bb[i] else bb[i])
  out=b''.join(struct.pack('<H',len(x.encode('utf-16-le'))//2)+x.encode('utf-16-le') for x in z)
  assert len(parse_stringtable(out))==16
  return out,'ok'
 except Exception as e:return None,f'error:{e}'

def align(v,a):return (v+a-1)//a*a
