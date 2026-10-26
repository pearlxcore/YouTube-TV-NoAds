# Supported source profiles

The default profile is YouTube Android TV **7.30.301 ARMv7**. Initial Sony X90H
checks passed for user-reported startup/playback, the About marker and no ads
across several videos. Prolonged playback, sign-in and other TVs remain unverified.

Use the standalone, Google-signed APK with SHA-256
`c439440a636fabe0b202e2acbe29643b9e09327df797490441e1731a591fddc7`.
It declares minimum Android 7.0. Bundles and other variants are not accepted.
Build it using the [README instructions](../README.md#build-instructions).
Do not supply `--arm-split` for this profile.

The original document-start polyfill is preserved, with the ad filter, About
marker and loading feedback appended through the engine's registration path.
Native script-pointer/length and Java patch points are hash-bound to this APK.
Other telemetry remains. Video frame rates are unchanged.

## Legacy 5.30.320

Select `--profile 5.30.320` and supply the original `base.apk` plus
`--arm-split C:\APKs\split_config.armeabi_v7a.apk`. Its hashes remain restricted
to the originally supported files. This profile reproduces the previous
`youtube-tv-noads-0.1.2.apk` packaging.

The legacy profile also requires Clang and LLD. On Windows use WSL Ubuntu-24.04
with `sudo apt install clang lld` inside Ubuntu. These tools are not needed for
the default 7.30.301 data-resource patch.

Both profiles use the same package identity. Updating from the older engine can
require data migration; rollback may require uninstalling and clearing app data.
Keep the previous release available.
