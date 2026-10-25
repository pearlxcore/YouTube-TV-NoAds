# Build from source

Just want to install the app? [Download the APK](https://github.com/pearlxcore/YouTube-TV-NoAds/releases/download/v0.1.0/youtube-tv-noads-0.1.0.apk) instead.

## Requirements

- Python 3.12+ and Java 21 (`java` and `keytool` on PATH).
- [Apktool 3.0.3](https://github.com/iBotPeaches/Apktool/releases/tag/v3.0.3) JAR and Android SDK Build Tools 36.
- On Windows: WSL **Ubuntu-24.04**, with Clang and LLD installed inside Ubuntu: `sudo apt install clang lld`.
- Original YouTube Android TV **5.30.320 ARMv7** files: `base.apk` and `split_config.armeabi_v7a.apk`. The patcher checks their hashes and rejects unsupported files.

## Build

Open PowerShell in the repository folder. Replace the paths below with your own:

```powershell
python -m pip install -r requirements.txt
python patcher.py --base C:\APKs\base.apk --arm-split C:\APKs\split_config.armeabi_v7a.apk --apktool C:\Tools\apktool_3.0.3.jar --build-tools C:\Android\build-tools\36.0.0 --output out
```

Your APK will be saved as **`out/youtube-tv-noads-0.1.0.apk`**. Building does not install it on your TV.

Keep **`out/.signing/`** private and backed up. Reuse that signing key for future app updates. Use a fresh output folder for each build; run `python patcher.py --help` for signing and other options.
