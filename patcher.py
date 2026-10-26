"""Build locally from exact user-supplied APKs. No downloads, network, or installation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

BASE_HASH = '418826127ad7a1c0ebfc607d841f8998c91d2b660478e9959b3c70a705a07f3f'
ARM_HASH = '5ca175e0045ecc7e4aa567de4bebe2c83723dcb8833c4dd9b67868eeef2cc4da'
NEW_BASE_HASH = 'c439440a636fabe0b202e2acbe29643b9e09327df797490441e1731a591fddc7'
PACKAGE = 'local.x90h.youtube.tv.experimental'
ROOT = Path(__file__).resolve().parent

def run(command, cwd=None):
    result = subprocess.run([str(value) for value in command], cwd=cwd, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout + result.stderr

def checked_input(path, digest):
    path = path.resolve(strict=True)
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError('Unsupported APK hash: ' + path.name + '. Select the matching supported source profile.')
    return path

def artwork(work):
    from PIL import Image, ImageDraw, ImageFont
    candidates = [Path('C:/Windows/Fonts/segoeuib.ttf'), Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')]
    font_file = next((path for path in candidates if path.exists()), None)
    def font(size):
        return ImageFont.truetype(str(font_file), size) if font_file else ImageFont.load_default(size=size)
    destination = work / 'res/drawable-nodpi'
    destination.mkdir(exist_ok=True)
    # Reuse artwork from the user's decoded original APK; none is distributed.
    banner_source = work / 'res/drawable/app_banner.png'
    icon_source = work / 'res/mipmap-xxxhdpi/ic_launcher.png'
    with Image.open(banner_source) as original:
        image = original.convert('RGBA')
    draw = ImageDraw.Draw(image)
    size = max(10, round(image.width * 14 / 320))
    label_font = font(size)
    width = draw.textbbox((0, 0), 'NoAds', font=label_font)[2]
    draw.text((round(image.width * 275 / 320) - width, round(image.height * 121 / 180)),
              'NoAds', font=label_font, fill='#333333')
    image.save(destination / 'noads_banner.png')
    with Image.open(icon_source) as original:
        image = original.convert('RGBA')
    draw = ImageDraw.Draw(image)
    label_font = font(max(10, round(image.width * 0.075)))
    box = draw.textbbox((0, 0), 'NoAds', font=label_font)
    draw.text(((image.width - (box[2] - box[0])) // 2, round(image.height * 0.76)),
              'NoAds', font=label_font, fill='#333333')
    image.save(destination / 'noads_icon.png')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True, type=Path)
    parser.add_argument('--profile', choices=['5.30.320', '7.30.301'], default='7.30.301', help='Source YouTube version; default 7.30.301, legacy 5.30.320 remains available')
    parser.add_argument('--arm-split', type=Path, help='Required for the 5.30.320 profile only')
    parser.add_argument('--apktool', required=True, type=Path, help='Existing Apktool 3.0.3 JAR')
    parser.add_argument('--build-tools', required=True, type=Path, help='Existing Android SDK Build Tools directory')
    parser.add_argument('--output', type=Path, default=Path('out'))
    parser.add_argument('--java', default='java')
    parser.add_argument('--keytool', default='keytool')
    parser.add_argument('--wsl-distro', default='Ubuntu-24.04')
    parser.add_argument('--keystore', type=Path)
    parser.add_argument('--ks-password-file', type=Path)
    parser.add_argument('--key-alias', default='youtube-tv-noads')
    args = parser.parse_args()
    if sys.flags.optimize:
        raise ValueError('Run without -O: native profile validation requires assertions.')
    newer = args.profile == '7.30.301'
    base = checked_input(args.base, NEW_BASE_HASH if newer else BASE_HASH)
    if not newer and not args.arm_split:
        raise ValueError('--arm-split is required for 5.30.320')
    if newer and args.arm_split:
        raise ValueError('7.30.301 expects the supported standalone ARMv7 APK, without --arm-split')
    arm = base if newer else checked_input(args.arm_split, ARM_HASH)
    apktool = args.apktool.resolve(strict=True)
    sdk = args.build_tools.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    workspace = output / 'work'
    if workspace.exists():
        raise ValueError('Output work directory already exists; use a fresh --output directory. Existing files are never deleted.')
    if bool(args.keystore) != bool(args.ks_password_file):
        raise ValueError('Supply both --keystore and --ks-password-file, or neither.')
    workspace.mkdir()
    for relative in ['original/splits', 'analysis/native/lib/armeabi-v7a', 'build', 'logs']:
        (workspace / relative).mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / 'patches', workspace / 'patches')
    shutil.copy2(base, workspace / 'original/base.apk')
    if not newer:
        shutil.copy2(arm, workspace / 'original/splits/split_config.armeabi_v7a.apk')
    with zipfile.ZipFile(arm) as archive:
        for name in archive.namelist():
            parts = name.split('/')
            if len(parts) == 3 and parts[:2] == ['lib', 'armeabi-v7a'] and parts[2].endswith('.so'):
                (workspace / 'analysis/native/lib/armeabi-v7a' / parts[2]).write_bytes(archive.read(name))
    os.environ['YT_NOADS_WSL_DISTRO'] = args.wsl_distro
    print('Decode original APK; compile and test the hash-bound native patch...', flush=True)
    run([args.java, '-jar', apktool, 'd', base, '-o', workspace / 'analysis/apktool/base'], workspace)
    scripts = (['build-native-730301.py', 'test-native-730301.py', 'prepare-apk.py', 'apply-java-730301.py'] if newer else
               ['build-native.py', 'test-hook.py', 'prepare-apk.py', 'apply-service-failure-fix.py', 'apply-primes-privacy.py'])
    for script in scripts:
        run([sys.executable, workspace / 'patches/build-scripts' / script], workspace)
    work = workspace / 'build/apk-work'
    android = '{http://schemas.android.com/apk/res/android}'
    ET.register_namespace('android', android[1:-1])
    manifest = work / 'AndroidManifest.xml'
    tree = ET.parse(manifest)
    app = tree.getroot().find('application')
    app.set(android + 'label', 'YouTube TV NoAds')
    app.set(android + 'banner', '@drawable/noads_banner')
    app.set(android + 'icon', '@drawable/noads_icon')
    app.set(android + 'logo', '@drawable/noads_icon')
    tree.write(manifest, encoding='utf-8', xml_declaration=True)
    metadata = work / 'apktool.yml'
    original_code, patched_code = ('730301320', '730301322') if newer else ('530320320', '530320323')
    metadata_text = metadata.read_text(encoding='utf-8')
    assert metadata_text.count('versionCode: ' + original_code) == 1
    metadata.write_text(metadata_text.replace('versionCode: ' + original_code, 'versionCode: ' + patched_code), encoding='utf-8')
    artwork(work)
    unsigned = output / 'unsigned.apk'
    aligned = output / 'aligned.apk'
    signed = output / ('youtube-tv-noads-7.30.301.apk' if newer else 'youtube-tv-noads-0.1.2.apk')
    print('Build, align, sign and verify the single APK...', flush=True)
    run([args.java, '-jar', apktool, 'b', work, '-o', unsigned], workspace)
    def tool(name):
        return sdk / (name + ('.bat' if name == 'apksigner' else '.exe') if os.name == 'nt' else name)
    run([tool('zipalign'), '-P', '16', '-f', '4', unsigned, aligned])
    if args.keystore:
        key = args.keystore.resolve(strict=True)
        password = args.ks_password_file.resolve(strict=True)
    else:
        signing = output / '.signing'
        signing.mkdir(exist_ok=True)
        key = signing / 'local.p12'
        password = signing / 'password.txt'
        if not key.exists():
            if password.exists():
                raise ValueError('Existing password without keystore; refusing to overwrite.')
            password.write_text(secrets.token_hex(24), encoding='ascii')
            if os.name != 'nt':
                password.chmod(0o600)
            run([args.keytool, '-genkeypair', '-keystore', key, '-storetype', 'PKCS12',
                 '-storepass:file', password, '-keypass:file', password, '-alias', args.key_alias,
                 '-keyalg', 'RSA', '-keysize', '3072', '-validity', '3650', '-dname', 'CN=YouTube TV NoAds Local Build'])
    run([tool('apksigner'), 'sign', '--ks', key, '--ks-key-alias', args.key_alias,
         '--ks-pass', 'file:' + str(password), '--out', signed, aligned])
    run([tool('apksigner'), 'verify', '--verbose', signed])
    run([tool('zipalign'), '-c', '-P', '16', '4', signed])
    raw = signed.read_bytes()
    with zipfile.ZipFile(signed) as archive:
        if archive.testzip() is not None:
            raise ValueError('APK CRC failure')
        if archive.getinfo('resources.arsc').compress_type != zipfile.ZIP_STORED:
            raise ValueError('resources.arsc must be uncompressed')
        native = [name for name in archive.namelist() if name.startswith('lib/') and name.endswith('.so')]
        if len(native) != (6 if newer else 8):
            raise ValueError('Unexpected original ARM library count for profile')
        for name in native:
            info = archive.getinfo(name)
            length, extra = struct.unpack_from('<HH', raw, info.header_offset + 26)
            if info.compress_type != zipfile.ZIP_STORED or (info.header_offset + 30 + length + extra) % 16384:
                raise ValueError('Native ZIP alignment failure')
        with zipfile.ZipFile(base) as original:
            for name in original.namelist():
                if name.startswith('assets/') and not name.endswith('/') and original.read(name) != archive.read(name):
                    raise ValueError('Original asset changed: ' + name)
    record = {'version': '7.30.301' if newer else '0.1.2', 'youtubeProfile': args.profile, 'package': PACKAGE, 'bytes': len(raw),
              'optionalPrimesDispatchDisabled': True,
              'sha256': hashlib.sha256(raw).hexdigest(), 'originalBaseSha256': NEW_BASE_HASH if newer else BASE_HASH,
              'originalArmSplitSha256': None if newer else ARM_HASH, 'signatureAndAlignmentVerified': True,
              'nativePatch': json.loads((workspace / 'build/native/patch-manifest.json').read_text()),
              'notice': 'Local build checks passed. Not a runtime or complete ad-suppression guarantee.'}
    record['javaPatches' if newer else 'primesPrivacyPatch'] = json.loads((workspace / ('build/java-730301-patches.json' if newer else 'build/primes-privacy-patch.json')).read_text())
    (output / 'build-manifest.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    print('Built ' + str(signed))
    print('SHA-256 ' + record['sha256'])
    print('Keep your signing files private and backed up. No installation performed.')

if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print('Build failed: ' + str(error), file=sys.stderr)
        sys.exit(1)
