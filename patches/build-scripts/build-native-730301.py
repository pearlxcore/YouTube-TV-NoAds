"""7.30.301 ARMv7: extend the existing document-start polyfill resource span.

Preserves the original polyfill and uses the existing script-registration path.
No evaluator detour, injected native executable code or changed DRM functions.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys
from elftools.elf.elffile import ELFFile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'patches/patch-source'
ORIGINAL = ROOT / 'analysis/native/lib/armeabi-v7a/libchrobalt.so'
EXPECTED = '12eeae53472694b2e38d727c24442d9d954c3a47f9543a550e48b93a32d344af'
RESOURCE = 0x75b4e8
RESOURCE_SIZE = 288
RESOURCE_HASH = 'fce27df3dfae15f71421385189b77e26b5845ae25cad21b26ad7fa1c12161dc1'
LITERAL = 0x203af30
PC_BASE = 0x203ab9c
SIZE_INSTRUCTION = 0x203ab94


def main():
    raw = bytearray(ORIGINAL.read_bytes())
    if hashlib.sha256(raw).hexdigest() != EXPECTED:
        raise ValueError('Unsupported 7.30.301 native binary')
    polyfill = bytes(raw[RESOURCE:RESOURCE + RESOURCE_SIZE])
    assert hashlib.sha256(polyfill).hexdigest() == RESOURCE_HASH
    assert raw[SIZE_INSTRUCTION - 2:SIZE_INSTRUCTION + 10] == bytes.fromhex('e7494ff490727944c0e90012')
    assert (struct.unpack_from('<I', raw, LITERAL)[0] + PC_BASE) & 0xffffffff == RESOURCE
    parts = {}
    for name in ('response-filter.js', 'about-marker.js', 'loading-indicator.js'):
        text = (SOURCE / name).read_bytes()
        if name == 'about-marker.js':
            assert text.count(b'5\\.30\\.320') == 1
            text = text.replace(b'5\\.30\\.320', b'7\\.30\\.301')
        parts[name] = text
    guard = (b"\n;(function(){try{if(typeof location==='undefined'||location.protocol!=='https:'||"
             b"!/(^|\\.)youtube\\.com$/.test(location.hostname))return;\n")
    payload = polyfill + guard + b'\n'.join(parts.values()) + b'\n}catch(ignored){}}());\n'
    assert len(payload) < 65536 and b'\0' not in payload
    with ORIGINAL.open('rb') as stream:
        elf = ELFFile(stream)
        assert elf['e_machine'] == 'EM_ARM' and elf['e_type'] == 'ET_DYN'
        headers = [dict(s.header) for s in elf.iter_segments()]
        loads = [s for s in headers if s['p_type'] == 'PT_LOAD']
        assert loads[0]['p_vaddr'] == loads[0]['p_offset'] == 0
        phoff, count = elf['e_phoff'], elf['e_phnum']
        assert elf['e_phentsize'] == 32
    align = lambda value: (value + 16383) & ~16383
    offset = align(len(raw))
    address = align(max(s['p_vaddr'] + s['p_memsz'] for s in loads))
    table_size = (count + 1) * 32
    payload_offset = (table_size + 15) & ~15
    payload_va = address + payload_offset
    table = bytearray(raw[phoff:phoff + count * 32])
    for i, segment in enumerate(headers):
        if segment['p_type'] == 'PT_PHDR':
            struct.pack_into('<8I', table, i * 32, 6, offset, address, address, table_size, table_size, 4, 4)
    segment_size = payload_offset + len(payload)
    table += struct.pack('<8I', 1, offset, address, address, segment_size, segment_size, 4, 16384)
    raw += bytes(offset - len(raw)) + table + bytes(payload_offset - len(table)) + payload
    # The existing Thumb LDR/ADD stores the resource address; only its literal changes.
    struct.pack_into('<I', raw, LITERAL, (payload_va - PC_BASE) & 0xffffffff)
    # Replace same-width MOV.W r2,#288 with non-flag-setting MOVW r2,#new_length.
    size = len(payload)
    struct.pack_into('<HH', raw, SIZE_INSTRUCTION,
                     0xf240 | ((size >> 12) & 15) | (((size >> 11) & 1) << 10),
                     (2 << 8) | (((size >> 8) & 7) << 12) | (size & 255))
    struct.pack_into('<I', raw, 28, offset)
    struct.pack_into('<H', raw, 44, count + 1)
    original = ORIGINAL.read_bytes()
    allowed = set(range(28, 32)) | set(range(44, 46)) | set(range(LITERAL, LITERAL + 4)) | set(range(SIZE_INSTRUCTION, SIZE_INSTRUCTION + 4))
    changed = [i for i, (a, b) in enumerate(zip(original, raw)) if a != b]
    assert set(changed) <= allowed
    out = ROOT / 'build/native'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'libchrobalt.so').write_bytes(raw)
    (out / 'document-start-payload.js').write_bytes(payload)
    record = {'status': 'LOCAL_BUILD_PENDING_DEVICE_VALIDATION', 'profile': '7.30.301',
              'nativeLibrary': 'libchrobalt.so', 'originalSha256': EXPECTED,
              'patchedSha256': hashlib.sha256(raw).hexdigest(), 'originalPolyfillSha256': RESOURCE_HASH,
              'literalOffset': LITERAL, 'pcBase': PC_BASE, 'sizeInstruction': SIZE_INSTRUCTION,
              'newSegmentFileOffset': offset, 'newSegmentVa': address, 'segmentSize': segment_size,
              'payloadOffset': payload_offset, 'payloadVa': payload_va, 'payloadBytes': len(payload),
              'payloadSha256': hashlib.sha256(payload).hexdigest(),
              'payloadParts': {name: hashlib.sha256(data).hexdigest() for name, data in parts.items()},
              'changedOriginalByteOffsets': changed,
              'scope': 'Existing document-start registration; playback and ad suppression untested'}
    (out / 'patch-manifest.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
