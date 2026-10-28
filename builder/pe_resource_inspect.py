from pathlib import Path
import struct, collections, zipfile

def u16(b,o):return struct.unpack_from('<H',b,o)[0]
def u32(b,o):return struct.unpack_from('<I',b,o)[0]
class PE:
 def __init__(self,b):
  self.b=b;self.peoff=u32(b,0x3c);o=self.peoff
  assert b[o:o+4]==b'PE\0\0';self.machine=u16(b,o+4);self.nsects=u16(b,o+6);self.timestamp=u32(b,o+8)
  self.opt=o+24;self.optsz=u16(b,o+20)
  self.mag=u16(b,self.opt);self.peplus=self.mag==0x20b
  self.imbase=struct.unpack_from('<Q' if self.peplus else '<I',b,self.opt+(24 if self.peplus else 28))[0]
  self.sectionalign=u32(b,self.opt+32);self.filealign=u32(b,self.opt+36)
  self.sizeofimage=u32(b,self.opt+56)
  self.cksum=u32(b,self.opt+64)
  self.ddstart=self.opt+(112 if self.peplus else 96)
  self.rscrva,self.rscsize=struct.unpack_from('<II',b,self.ddstart+8*2)
  self.sect=[]
  for i in range(self.nsects):
   p=self.opt+self.optsz+i*40;name=b[p:p+8].split(b'\0')[0].decode('ascii','replace');vs,va,fs,fo=struct.unpack_from('<IIII',b,p+8)
   self.sect.append((name,vs,va,fs,fo))
  self.rscoff=self.rvaoff(self.rscrva)
 def rvaoff(self,rva):
  for n,vs,va,fs,fo in self.sect:
   if va<=rva<va+max(vs,fs):return fo+rva-va
  raise Exception(f'invalid RVA {rva:x}')
 def resources(self):
  b=self.b; start=self.rscoff; ents=[];nodes=0
  def nm(v):
   if not v&0x80000000: return v
   pos=start+(v&0x7fffffff)
   return b[pos+2:pos+2+2*u16(b,pos)].decode('utf-16-le',errors='replace')
  def go(rel,ks):
   nonlocal nodes;nodes+=1
   if nodes>200000:raise Exception('huge resource recursion')
   a=start+rel;nc,ni=u16(b,a+12),u16(b,a+14)
   for i in range(nc+ni):
    kn,kd=struct.unpack_from('<II',b,a+16+i*8);k=nm(kn);ix=kd&0x7fffffff
    if kd&0x80000000:go(ix,ks+[k])
    else:
     x=start+ix;rva,size,code,rs=struct.unpack_from('<IIII',b,x)
     try: off=self.rvaoff(rva)
     except Exception:off=-1
     ents.append((tuple(ks+[k]),rva,size,code,off))
  if start:go(0,[])
  return ents
