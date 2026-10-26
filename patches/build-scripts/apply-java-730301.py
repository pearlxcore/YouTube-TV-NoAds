"""Hash-bound equivalents of the existing Java fixes for the 7.30.301 profile."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {
    'dov': 'c1dfe202f2d048b4bf1c9cb32b18a2cd1a6d3471da2138fe68a70973395f7d1b',
    'dsl': '0cb1603842fcfe4fbe4ec72f8941c4a4e6fdd32e9bc31c39d399a743fea069cb',
    'elf': 'adb1fbfa42051093fa76fda477f0cd9323a3b9df258419875275abc58fdb18ca',
    'igy': '003c077f8d7e5c2d4f7f3d79867bced1e32592de1d9af5ff01a2f3d9f835c2e6',
}
source = ROOT / 'analysis/apktool/base/smali_classes2'
target = ROOT / 'build/apk-work/smali_classes2'
texts = {}
for name, digest in EXPECTED.items():
    text = (source / (name + '.smali')).read_text(encoding='utf-8')
    if hashlib.sha256(text.encode()).hexdigest() != digest:
        raise ValueError('Unsupported 7.30.301 Java profile: ' + name)
    if (target / (name + '.smali')).read_text(encoding='utf-8') != text:
        raise ValueError('Refusing to overwrite changed Java target: ' + name)
    texts[name] = text

text = texts['dov']
method = '.method public final r(Ldpq;Ljava/util/Set;)V\n'
assert text.count(method) == 1
start = text.index(method) + len(method)
end = text.index('.end method', start)
body = text[start:end]
pattern = r'(?m)^    :catch_2\n    move-exception v0\n\n    \.line \d+\n    throw v0'
replacement = '''    :catch_2
    move-exception v0

    # Preserve denial as failure for the DroidGuard client, never forge success.
    instance-of v2, v1, Ldsl;
    if-eqz v2, :noads_rethrow_security
    goto :goto_4

    :noads_rethrow_security
    throw v0'''
patched, count = re.subn(pattern, replacement, body)
assert count == 1 and ':noads_rethrow_security' not in body
assert ':goto_4' in body and '.locals 19' in body
patched = text[:start] + patched + text[end:]
(target / 'dov.smali').write_text(patched, encoding='utf-8', newline='\n')

text = texts['elf']
method = '.method public final a(Lela;)Lcom/google/common/util/concurrent/ListenableFuture;\n'
assert text.count(method) == 1
start = text.index(method) + len(method)
end = text.index('.end method', start)
patched = text[:start] + '''    .locals 1

    # Discard optional Java Primes metric dispatch; complete listeners normally.
    sget-object v0, Ligy;->a:Lcom/google/common/util/concurrent/ListenableFuture;
    return-object v0
''' + text[end:]
(target / 'elf.smali').write_text(patched, encoding='utf-8', newline='\n')
record = {'profile': '7.30.301', 'originalNormalizedHashes': EXPECTED,
          'serviceFailure': 'dov.r: only dsl SecurityException goes to existing B(8,null,null,generation) failure',
          'optionalPrimesDispatchDisabled': True,
          'primesMethod': 'elf.a(ela): returns existing immediate-null igy.a future',
          'limits': 'No altered attestation or DRM. Web and separate crash reporting remain. Runtime untested.'}
(ROOT / 'build/java-730301-patches.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(record, indent=2))
