"""Hash-bound ARM experiment. Never writes the original ELF or touches a device."""
import hashlib, json, os, pathlib, struct, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/python'))
from elftools.elf.elffile import ELFFile
ORIGINAL = ROOT/'analysis/native/lib/armeabi-v7a/libcobalt.so'
OUT = ROOT/'build/native'; OUT.mkdir(parents=True, exist_ok=True)
SOURCE = ROOT/'patches/patch-source'
EXPECTED = 'a3bc2715219e534f7d06d2d36321d9e0d51133c6ff80f97ef5f4ae16d94a7719'
ENTRY = 0x1a92ec4
raw = bytearray(ORIGINAL.read_bytes())
assert hashlib.sha256(raw).hexdigest() == EXPECTED, 'Unsupported original binary'
with ORIGINAL.open('rb') as stream:
    elf = ELFFile(stream)
    assert elf['e_machine'] == 'EM_ARM' and elf['e_type'] == 'ET_DYN'
    headers = [dict(s.header) for s in elf.iter_segments()]
    loads = [s for s in headers if s['p_type'] == 'PT_LOAD']
    original_segment = next(s for s in loads if s['p_vaddr'] <= ENTRY < s['p_vaddr']+s['p_filesz'])
    entry_offset = original_segment['p_offset'] + ENTRY-original_segment['p_vaddr']
    assert raw[entry_offset:entry_offset+8] == bytes.fromhex('f04b2de918b08de2')
    old_phoff, entsize, count = elf['e_phoff'], elf['e_phentsize'], elf['e_phnum']
assert entsize == 32
align = lambda x: (x+4095)&~4095
new_offset = align(len(raw))
new_va = align(max(s['p_vaddr']+s['p_memsz'] for s in loads))
table_size = (count+1)*32
code_offset = (table_size+15)&~15
code_va = new_va+code_offset
def linux_path(path):
    if os.name != 'nt': return str(path)
    return '/mnt/'+path.drive[0].lower()+str(path)[2:].replace('\\','/')
common = ['wsl','-d',os.environ.get('YT_NOADS_WSL_DISTRO','Ubuntu-24.04'),'--'] if os.name == 'nt' else []
subprocess.run(common+['clang','--target=armv7a-linux-androideabi','-march=armv7-a','-marm',
    '-c',linux_path(SOURCE/'evaluate-hook.S'),'-I'+linux_path(SOURCE),'-o',linux_path(OUT/'hook.o')],check=True)
subprocess.run(common+['ld.lld','-m','armelf_linux_eabi','-Ttext='+hex(code_va),
    '--defsym=x90h_resume='+hex(ENTRY+8),'-e','x90h_hook',linux_path(OUT/'hook.o'),
    '-o',linux_path(OUT/'hook.elf')],check=True)
with (OUT/'hook.elf').open('rb') as stream:
    hook = ELFFile(stream)
    text_section = hook.get_section_by_name('.text')
    assert text_section['sh_addr'] == code_va
    code = text_section.data()
    assert not any(s['sh_type'] in ('SHT_REL','SHT_RELA') and s.num_relocations() for s in hook.iter_sections())
    symbols = {s.name:s['st_value'] for s in hook.get_section_by_name('.symtab').iter_symbols() if s.name}
assert symbols['x90h_hook'] == code_va
table = bytearray(raw[old_phoff:old_phoff+count*32])
for index,s in enumerate(headers):
    if s['p_type'] == 'PT_PHDR':
        struct.pack_into('<8I',table,index*32,6,new_offset,new_va,new_va,table_size,table_size,4,4)
segment_size = code_offset+len(code)
table += struct.pack('<8I',1,new_offset,new_va,new_va,segment_size,segment_size,5,4096)
raw += bytes(new_offset-len(raw))
raw += table+bytes(code_offset-len(table))+code
delta = code_va-(ENTRY+8)
assert delta%4 == 0 and -(1<<25) <= delta < (1<<25)
struct.pack_into('<I',raw,entry_offset,0xea000000|((delta//4)&0xffffff))
struct.pack_into('<I',raw,28,new_offset)
struct.pack_into('<H',raw,44,count+1)
output = OUT/'libcobalt.so'
output.write_bytes(raw)
changed = [i for i,(a,b) in enumerate(zip(ORIGINAL.read_bytes(),raw)) if a!=b]
assert set(changed) <= set(range(28,32))|set(range(44,46))|set(range(entry_offset,entry_offset+4))
with output.open('rb') as stream:
    check = ELFFile(stream)
    assert check.num_segments() == count+1
    new_load = list(check.iter_segments())[-1]
    assert new_load['p_flags'] == 5 and new_load['p_vaddr'] == new_va
record = {'status':'EXPERIMENTAL_UNTESTED_ON_ANDROID','originalSha256':EXPECTED,
    'patchedSha256':hashlib.sha256(raw).hexdigest(),'elfEntry':hex(ENTRY),
    'entryFileOffset':hex(entry_offset),'hookVa':hex(code_va),'newSegmentVa':hex(new_va),
    'newSegmentFileOffset':hex(new_offset),'segmentSize':segment_size,'codeOffset':code_offset,
    'symbols':{k:hex(v) for k,v in symbols.items()},'changedOriginalByteOffsets':changed,
    'payloadSha256':hashlib.sha256(b''.join((SOURCE/name).read_bytes() for name in ('response-filter.js','about-marker.js'))).hexdigest(),
    'payloadParts':{name:hashlib.sha256((SOURCE/name).read_bytes()).hexdigest() for name in ('response-filter.js','about-marker.js')}}
(OUT/'patch-manifest.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record,indent=2))
