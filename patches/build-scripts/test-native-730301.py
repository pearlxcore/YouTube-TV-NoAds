"""Emulate the modified resource-span setup at multiple ASLR bases."""
import json
from pathlib import Path
import struct
from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2

ROOT = Path(__file__).resolve().parents[2]
out = ROOT / 'build/native'
record = json.loads((out / 'patch-manifest.json').read_text())
data = (out / 'libchrobalt.so').read_bytes()
instruction = list(Cs(CS_ARCH_ARM, CS_MODE_THUMB).disasm(data[record['sizeInstruction']:record['sizeInstruction'] + 4], record['sizeInstruction']))
assert len(instruction) == 1 and instruction[0].mnemonic == 'movw'
assert instruction[0].op_str == 'r2, #' + hex(record['payloadBytes'])
with (out / 'libchrobalt.so').open('rb') as stream:
    elf = ELFFile(stream)
    load = list(elf.iter_segments())[-1]
    assert load['p_type'] == 'PT_LOAD' and load['p_flags'] == 4 and load['p_align'] == 16384
    assert load['p_vaddr'] == record['newSegmentVa']
    assert load['p_filesz'] == record['segmentSize']
start = record['sizeInstruction'] - 2
for base in (0, 0x10000000, 0x70000000):
    emulator = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    page = (base + start) & ~4095
    emulator.mem_map(page, 8192)
    emulator.mem_write(base + start, data[start:start + 12])
    emulator.mem_write(base + record['literalOffset'], data[record['literalOffset']:record['literalOffset'] + 4])
    target = 0x80000000
    emulator.mem_map(target, 4096)
    emulator.reg_write(UC_ARM_REG_R0, target)
    emulator.emu_start((base + start) | 1, base + start + 12, count=4)
    pointer, size = struct.unpack('<II', emulator.mem_read(target, 8))
    assert pointer == base + record['payloadVa'] and size == record['payloadBytes']
print(json.dumps({'passed': True, 'aslrBases': 3, 'scope': 'Resource setup emulation; real script registration and Android loading untested'}))
