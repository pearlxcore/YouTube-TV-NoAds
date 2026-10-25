"""Discard optional Java Primes metric dispatch, retaining its Future API.

Does not disable Cobalt/web analytics, direct crash transmitters, or detection.
"""
import hashlib
import json
from pathlib import Path

METHOD = '.method public final b(Lcsb;)Lcom/google/common/util/concurrent/ListenableFuture;'
CSE_HASH = '4dc2851036d1a0f08178566eb76352bb5867a32d54750b3e2e44d7a9421ea532'
GDB_HASH = '10607967037de7ec658210d646611aeea67a2b8f75693f53f0d393b065fdb160'
BODY = '''    .locals 1

    # Optional Primes metrics are discarded locally. Complete listeners normally.
    sget-object v0, Lgdb;->a:Lcom/google/common/util/concurrent/ListenableFuture;

    return-object v0
'''


def require_profile(text, expected):
    if hashlib.sha256(text.encode('utf-8')).hexdigest() != expected:
        raise ValueError('Unsupported Primes profile; no privacy patch written.')


def replace_dispatch(text):
    marker = METHOD + '\n'
    if text.count(marker) != 1:
        raise ValueError('Expected exactly one Primes dispatch method.')
    start = text.index(marker) + len(marker)
    end = text.index('.end method', start)
    return text[:start] + BODY + text[end:]


def apply(root):
    original = root / 'analysis/apktool/base/smali/cse.smali'
    immediate = root / 'analysis/apktool/base/smali/gdb.smali'
    target = root / 'build/apk-work/smali/cse.smali'
    # Universal-newline reads make the guards portable across Apktool platforms.
    source = original.read_text(encoding='utf-8')
    require_profile(source, CSE_HASH)
    require_profile(immediate.read_text(encoding='utf-8'), GDB_HASH)
    if target.read_text(encoding='utf-8') != source:
        raise ValueError('Primes target already changed; refusing to overwrite.')
    patched = replace_dispatch(source)
    target.write_text(patched, encoding='utf-8', newline='\n')
    record = {'optionalPrimesDispatchDisabled': True,
              'method': 'cse.b(csb): ListenableFuture',
              'behavior': 'Discard metric dispatch locally; return existing immediate-null future gdb.a.',
              'originalNormalizedSha256': CSE_HASH,
              'immediateFutureNormalizedSha256': GDB_HASH,
              'patchedNormalizedSha256': hashlib.sha256(patched.encode('utf-8')).hexdigest(),
              'limitations': ['Not a complete telemetry removal or detection countermeasure.',
                              'Web reporting, direct crash transmitters and local metric collection remain.',
                              'Runtime safety and traffic reduction require device testing.']}
    (root / 'build/primes-privacy-patch.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    return record


if __name__ == '__main__':
    print(json.dumps(apply(Path(__file__).resolve().parents[2]), indent=2))
