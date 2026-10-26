# YouTube TV NoAds

YouTube Android TV with ad-filter patches, the original interface, and its own TV tile.

- **YouTube version:** 7.30.301, ARMv7 (`armeabi-v7a`)
- **Release:** [v7.30.301](https://github.com/pearlxcore/YouTube-TV-NoAds/releases/tag/v7.30.301). Complete ad blocking and compatibility with other TVs are not guaranteed.

[Download the APK](https://github.com/pearlxcore/YouTube-TV-NoAds/releases/download/v7.30.301/youtube-tv-noads-7.30.301.apk) and install it on your TV. No separate launcher or original YouTube installation is required.

## Compatibility

Reported results for the versions and TVs tested.

<table>
  <thead>
    <tr><th>YouTube version</th><th>TV model</th><th>Android TV</th><th>Status</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><a href="https://github.com/pearlxcore/YouTube-TV-NoAds/releases/tag/v7.30.301">7.30.301</a></td>
      <td>Sony Bravia X90H</td><td>12</td>
      <td>Working</td>
    </tr>
    <tr>
      <td rowspan="2" valign="top"><a href="https://github.com/pearlxcore/YouTube-TV-NoAds/releases/tag/v0.1.2">5.30.320</a></td>
      <td>Sony Bravia X90H</td><td>12</td>
      <td>Working</td>
    </tr>
    <tr>
      <td>TCL P8L</td><td>14</td>
      <td>Working</td>
    </tr>
  </tbody>
</table>

Disables one optional performance-metrics reporting path. Other telemetry remains; [privacy details](docs/PRIVACY.md).

## Build instructions

Just want to install the app? [Download the APK](https://github.com/pearlxcore/YouTube-TV-NoAds/releases/download/v7.30.301/youtube-tv-noads-7.30.301.apk) instead.

### Requirements

- Python 3.12+ and Java 21 (`java` and `keytool` on PATH).
- [Apktool 3.0.3](https://github.com/iBotPeaches/Apktool/releases/tag/v3.0.3) JAR and Android SDK Build Tools 36.
- Original standalone YouTube Android TV **7.30.301 ARMv7** APK. The patcher checks its hash and rejects unsupported variants. [Source profiles](docs/PORTING.md).

### Build

Open PowerShell in the repository folder. Replace the paths below with your own:

```powershell
python -m pip install -r requirements.txt
python patcher.py --base C:\APKs\youtube-tv-7.30.301-armv7.apk --apktool C:\Tools\apktool_3.0.3.jar --build-tools C:\Android\build-tools\36.0.0 --output out
```

Your APK will be saved as **`out/youtube-tv-noads-7.30.301.apk`**. Building does not install it on your TV.

Keep **`out/.signing/`** private and backed up. Reuse that signing key for future app updates. Use a fresh output folder for each build; run `python patcher.py --help` for signing and other options.

## ❤️ Support My Work
[![ko-fi](https://github.com/user-attachments/assets/93da7a03-e740-4f79-9add-8b3741239b2f)](https://ko-fi.com/R6R524N7X)

[![paypal](https://user-images.githubusercontent.com/36906814/102657760-39d1ce00-41b1-11eb-96fe-c10e2d9b3f39.png)](https://www.paypal.com/paypalme/pearlxcoree)
