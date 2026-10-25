# Build locally

Only the original YouTube Android TV **5.30.320 ARMv7** profile below is supported. Other versions, architectures and repackaged APKs are rejected. Obtain your own original APKs from your device; this project does not supply or download them.

| Input | SHA-256 |
| --- | --- |
| `base.apk` | `418826127ad7a1c0ebfc607d841f8998c91d2b660478e9959b3c70a705a07f3f` |
| `split_config.armeabi_v7a.apk` | `5ca175e0045ecc7e4aa567de4bebe2c83723dcb8833c4dd9b67868eeef2cc4da` |

## Tools

- Python 3.12 or newer and `python -m pip install -r requirements.txt`.
- Java 21, including `java` and `keytool` on PATH.
- [Apktool 3.0.3](https://github.com/iBotPeaches/Apktool/releases/tag/v3.0.3) JAR.
- [Android SDK Build Tools](https://developer.android.com/tools/releases/build-tools), tested with 36, including `zipalign` and `apksigner`.
- Clang and LLD. On Windows use WSL Ubuntu 24.04 with `sudo apt install clang lld`; native Windows Python runs the patcher and invokes those compiler tools through WSL. `--wsl-distro` selects another installed distribution. Linux execution is provided but not yet device-tested as a build host.
- Node.js to run the JavaScript checks.

The tools and Python dependencies are separate installations; none are bundled. The ARM hook has fixed offsets and hashes for this one version. Do not bypass those checks or run Python with `-O`.

## Windows example

Run from the repository using PowerShell. Replace input and tool paths with your own:

```powershell
python -m pip install -r requirements.txt
node patches/build-scripts/test-payload.cjs
node tests/about-marker.cjs
python patcher.py --base C:\APKs\base.apk --arm-split C:\APKs\split_config.armeabi_v7a.apk --apktool C:\Tools\apktool_3.0.3.jar --build-tools C:\Android\build-tools\36.0.0 --output out
```

The output is **`out/youtube-tv-noads-0.1.0.apk`**: one app with its own **YouTube TV NoAds** tile. No companion launcher is needed. The internal package stays `local.x90h.youtube.tv.experimental`, separately from official YouTube. A local `build-manifest.json` records the inputs and output hash.

The patcher creates a local development signing key and password under `out/.signing/`. Keep both private and back them up. Reuse the same key for future updates with `--keystore`, `--ks-password-file`, and `--key-alias`. A different signature cannot update an existing installation; do not clear or uninstall another installation to work around that without considering its data. Use a fresh `--output` directory for each build: the patcher refuses to delete or overwrite an existing work directory.

Building does not connect to a TV or install anything. Install your locally built APK yourself using Android TV's normal sideloading or ADB workflow, for example `adb -s YOUR_TV_ADDRESS install -r out/youtube-tv-noads-0.1.0.apk` on an already authorised device.

The app's minimum Android API is 24 and it requires 32-bit ARM compatibility. Those are prerequisites, not a guarantee of support on every qualifying TV.

## Mechanism and limits

The native Cobalt evaluator receives a small local JavaScript payload. Its `JSON.parse` wrapper filters recognised player ad metadata and browse ad renderers before the original frontend uses the parsed result. The original interface, decoding and content playback remain. The About marker starts only after frontend-response parsing to avoid accessing native DOM bindings too early.

A narrowly scoped Google service exception change reports a denied DroidGuard connection through the existing failure callback. It does not forge successful verification, signatures, tokens or account rights. Sign-in and Google-dependent features can still fail on a development-signed build.

The separate package protects the local APK from ordinary updates to official YouTube. YouTube's remotely delivered frontend and ad formats can change independently and break filtering. Unknown formats and server-inserted media may evade this filter. No DRM, TLS, firmware or Google service settings are modified.

The general parser-filter approach was researched in [TizenTube](https://github.com/reisxd/TizenTube) and [TizenTubeCobalt](https://github.com/reisxd/TizenTubeCobalt). This repository contains the independently written payload, patcher and hook; it does not bundle those applications or Google's code. Third-party tools retain their respective licenses. YouTube is a Google trademark; this project is unaffiliated.
