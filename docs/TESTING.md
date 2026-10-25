# Test results

Test date: **2026-10-26**. Device: **Sony Bravia X90H / Android TV 12**, ARMv7. YouTube base version: **5.30.320**. GitHub release classification: **normal release**. This label does not extend the test coverage described here.

## Build checks

- Public patcher completed two full builds from the matching original base and ARM split: one with an existing development key, one with automatic local key generation.
- Both passed APK signature, ZIP CRC, resource storage and native library alignment checks. All 1,014 non-signature APK entries matched the installed test candidate byte-for-byte, including DEX code, native libraries, manifest, resources and assets. ZIP/signature container bytes and resulting APK hashes can differ between builds and signing keys.
- Nine JavaScript filter fixtures passed. Deferred About bootstrap, repeat injection, page gating and revisit fixtures passed. ARM detour emulation passed with a simulated Cobalt callee; this is not a full Android emulator test.
- Unsupported input hashes and optimized Python are rejected before a build is started.

## TV checks

The single-APK candidate was installed as an update to the experimental package. Official YouTube was retained and its data was not cleared. The existing experimental account profile remained visible; credentials were not accessed.

| Check | Observation |
| --- | --- |
| Standalone tile | **YouTube TV NoAds** banner displayed in the Apps menu and launched the experimental MainActivity directly. No companion launcher is needed. |
| Navigation/search | D-pad, OK, Back/Home, on-screen search keyboard, query entry and search results worked. |
| Playback | Content frames were observed on two videos, including a second video selected from search. |
| Quality/captions | 720p selection continued playing. Caption selection and preview rendered; restored Quality Auto and Captions Off afterward. |
| Pause/resume | Paused and playing states were observed following media-button inputs; playback was resumed afterward. |
| Cold restart | Experimental app force-stopped, then cold-launched successfully in 1,562 ms. Existing profile remained available. |
| About marker | `pearlxcore was here` displayed below the original version after cold restart. |

The mixed playback/functionality run lasted **900.3 seconds (15 minutes)** with **31 samples** at 30-second intervals. The same app process survived the entire sampled session, with zero command-sampling errors and no fatal exception/signal entries in the bounded process-log samples. There were 24 playing-state samples, three paused-state samples and four without an active app media session during deliberate launcher/search navigation. Sampled process PSS ranged from about 92 to 254 MiB across playback and navigation; this is not a memory-leak test.

One pause of unknown cause occurred before the deliberate functionality checks. It was resumed; later pause/resume inputs were also exercised and a playing state was confirmed afterward. Cold restart was performed after this sampled session, so its intentional process change is not counted as a crash.

## Limits

This is a device smoke test, not long-term stability certification. One pause of unknown cause occurred during the initial playback portion and was resumed manually; no crash was observed with it. The test later included intentional navigation and player-setting operations, so it is not an uninterrupted playback run. Media-session positions can remain unchanged between state updates even while content advances; captures were used to observe content at separate points.

No YouTube-served ad was identified in the inspected playback frames, but sampling does not establish complete suppression or prove every ad opportunity was reached. Mid-roll coverage, overlays, live streams and future frontend formats remain unproven. Creator sponsorships embedded in videos are not filtered by this patch.

Fresh Google sign-in, Cast, subscriptions/playlists, sleep/resume and other TV models were not independently certified for this release. Existing profile retention is not proof that a fresh login works. Audio output was not independently listened to during this session. Older X90H testing confirmed picture/audio, seeking, captions, autoplay and restart in selected paths; that history does not replace testing on another device.

Device screenshots, account details, IP addresses, raw logs and private signing files are kept out of the repository and release assets. The precompiled patched APK is distributed as a release asset, alongside the source archive and checksums; APKs are not committed to the source tree.

## Same-version artwork refresh

The v0.1.0 source release was refreshed to reuse the user's original YouTube banner and icon with a small **NoAds** label, replacing the previous custom artwork and its EXPERIMENTAL text. Package identity, version code, native patch and app logic remain unchanged. The refreshed APK passed a full local build, signing/alignment checks and byte comparisons for DEX, native libraries and original assets. Its new artwork was inspected locally; the installed TV tile was not updated or retested for this cosmetic refresh. The device results above refer to the initially tested v0.1.0 candidate. The refreshed tag and source archive replace the earlier v0.1.0 snapshot; use the new release checksum.
