"""Execute patched ARM detour in Unicorn with a simulated Cobalt callee.
Validates instruction/stack behavior, not the real Cobalt ABI or Android loading.
"""
import json, pathlib, struct, sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/python'))
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import *
from elftools.elf.elffile import ELFFile
manifest=json.loads((ROOT/'build/native/patch-manifest.json').read_text())
elfpath=ROOT/'build/native/libcobalt.so'
data=elfpath.read_bytes()
entry=int(manifest['elfEntry'],16); new_va=int(manifest['newSegmentVa'],16)
uc=Uc(UC_ARCH_ARM,UC_MODE_ARM)
uc.mem_map(entry&~4095,4096)
uc.mem_map(new_va,((manifest['segmentSize']+4095)//4096)*4096)
off=int(manifest['newSegmentFileOffset'],16)
uc.mem_write(new_va,data[off:off+manifest['segmentSize']])
uc.mem_write(entry,data[int(manifest['entryFileOffset'],16):int(manifest['entryFileOffset'],16)+8])
stack=0x100000; heap=0x200000; stop=0x300000
uc.mem_map(stack,0x10000); uc.mem_map(heap,0x10000); uc.mem_map(stop,4096)
uc.mem_write(stop,b'\x00\x00\xa0\xe1')
source=heap+0x100; ref=heap+0x200; this=heap+0x300
uc.mem_write(source,struct.pack('<I',0x12345678)); uc.mem_write(ref,struct.pack('<I',source))
initial_sp=stack+0xf000
initial={UC_ARM_REG_R0:this,UC_ARM_REG_R1:ref,UC_ARM_REG_R2:0x2222,
 UC_ARM_REG_R3:0x3333,UC_ARM_REG_R12:0xcccc,UC_ARM_REG_LR:stop,
 UC_ARM_REG_SP:initial_sp,UC_ARM_REG_R4:0x4444,UC_ARM_REG_R5:0x5555,
 UC_ARM_REG_R6:0x6666,UC_ARM_REG_R7:0x7777,UC_ARM_REG_R8:0x8888,
 UC_ARM_REG_R9:0x9999,UC_ARM_REG_R10:0xaaaa,UC_ARM_REG_R11:0xbbbb}
for reg,val in initial.items(): uc.reg_write(reg,val)
calls=[]
def read_word(address): return struct.unpack('<I',uc.mem_read(address,4))[0]
def observe(machine,address,size,user):
 if address==entry+8:
  assert uc.reg_read(UC_ARM_REG_R0)==this
  passed_ref=uc.reg_read(UC_ARM_REG_R1)
  if not calls:
   fake=read_word(passed_ref)
   assert read_word(fake)==0x12345678
   assert read_word(fake+8)&1
   length=read_word(fake+12); pointer=read_word(fake+16)
   expected_payload=b''.join((ROOT/'patches/patch-source'/name).read_bytes() for name in ('response-filter.js','about-marker.js','loading-indicator.js'))
   assert bytes(uc.mem_read(pointer,length))==expected_payload
   assert read_word(fake+32)==1 and read_word(fake+36)==1
   assert bytes(uc.mem_read(fake+40,2))==b'\0\0'
   calls.append('injected source')
  else:
   assert passed_ref==ref
   for r in [UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R12]: assert uc.reg_read(r)==initial[r]
   calls.append('original source')
  # Simulate the rest of the original callee, including its AAPCS unwind/return.
  sp=uc.reg_read(UC_ARM_REG_SP)
  saved=struct.unpack('<8I',uc.mem_read(sp,32))
  regs=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,
        UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R11,UC_ARM_REG_LR]
  for r,v in zip(regs,saved): uc.reg_write(r,v)
  uc.reg_write(UC_ARM_REG_SP,sp+32)
  uc.reg_write(UC_ARM_REG_R0,0x1234 if len(calls)==1 else 0x5678)
  uc.reg_write(UC_ARM_REG_PC,saved[-1])
 elif address==stop:
  uc.emu_stop()
uc.hook_add(UC_HOOK_CODE,observe)
uc.emu_start(entry,stop+4,count=1000)
assert calls==['injected source','original source']
assert uc.reg_read(UC_ARM_REG_SP)==initial_sp and uc.reg_read(UC_ARM_REG_R0)==0x5678
for r in [UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,
          UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]: assert uc.reg_read(r)==initial[r]
print(json.dumps({'passed':True,'calls':calls,'stackRestored':True,'originalResultPreserved':True,
 'scope':'ARM hook emulation with simulated callee; real Cobalt and Android untested'},indent=2))
