"""Create separate derived build tree; no modifications to analyzed original tree."""
import json, pathlib, shutil, xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parents[2]
out=ROOT/'build/apk-work'
if out.exists(): raise SystemExit('Build tree already exists; reuse it or archive it explicitly.')
shutil.copytree(ROOT/'analysis/apktool/base',out)
android='{http://schemas.android.com/apk/res/android}'
ET.register_namespace('android',android[1:-1])
path=out/'AndroidManifest.xml'; tree=ET.parse(path); manifest=tree.getroot()
old='com.google.android.youtube.tv'; new='local.x90h.youtube.tv.experimental'
manifest.set('package',new)
for attr in ('requiredSplitTypes','splitTypes'): manifest.attrib.pop(android+attr,None)
app=manifest.find('application'); app.set(android+'label','YouTube TV (X90H experiment)')
for element in manifest.iter():
 for key in ('process','taskAffinity','authorities'):
  value=element.get(android+key)
  if value and old in value: element.set(android+key,value.replace(old,new))
 value=element.get(android+'name')
 if value==old+'.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION': element.set(android+'name',new+'.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION')
 if android+'autoVerify' in element.attrib: element.set(android+'autoVerify','false')
for element in list(app):
 if element.tag=='meta-data' and element.get(android+'name','').startswith(('com.android.vending.splits','com.android.stamp.','com.android.vending.derived.apk.id')):
  app.remove(element)
tree.write(path,encoding='utf-8',xml_declaration=True)
lib=out/'lib/armeabi-v7a'; lib.mkdir(parents=True,exist_ok=True)
for original in (ROOT/'analysis/native/lib/armeabi-v7a').glob('*.so'): shutil.copy2(original,lib/original.name)
native_name = json.loads((ROOT/'build/native/patch-manifest.json').read_text()).get('nativeLibrary', 'libcobalt.so')
shutil.copy2(ROOT/'build/native'/native_name,lib/native_name)
with (out/'apktool.yml').open('a') as stream: stream.write('\n- so\n')
print('Prepared '+str(out)+' package '+new)
