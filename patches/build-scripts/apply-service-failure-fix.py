"""Propagate denied DroidGuard service connection as failure, never success.
Does not change GMS verification, tokens, signatures or attestation responses.
"""
import hashlib,json,pathlib
root=pathlib.Path(__file__).resolve().parents[2]
original=root/'analysis/apktool/base/smali/bwh.smali'
target=root/'build/apk-work/smali/bwh.smali'
text=original.read_text(encoding='utf-8')
start=text.index('.method public final p(Lbww;Ljava/util/Set;)V')
end=text.index('.end method',start)
method=text[start:end]
old='''    :catch_2
    move-exception v0

    .line 260
    throw v0'''
new='''    :catch_2
    move-exception v0

    # Only this denied DroidGuard connection becomes the existing error callback.
    # Other SecurityException behavior is preserved.
    instance-of v2, v1, Lbyh;
    if-eqz v2, :x90h_rethrow_security
    goto :goto_4

    :x90h_rethrow_security
    .line 260
    throw v0'''
assert method.count(old)==1
patched=text[:start]+method.replace(old,new)+text[end:]
target.write_text(patched,encoding='utf-8')
manifest={'method':'bwh.p(bww, Set)','scope':'byh DroidGuard client only',
 'behavior':'existing error callback y(8, null, null, generation); never success or generated attestation',
 'originalSmaliSha256':hashlib.sha256(original.read_bytes()).hexdigest(),
 'patchedSmaliSha256':hashlib.sha256(target.read_bytes()).hexdigest()}
(root/'build/service-failure-patch.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
