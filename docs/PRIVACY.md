# Performance metrics

Starting with v0.1.2, the app discards one optional Java Primes performance-metrics
dispatch operation. It returns the existing completed future so callers can
finish normally. The patcher applies this change by default and rejects
unsupported source profiles.

Playback, seeking, loading feedback and navigation were reported working on the
Sony Bravia X90H. Reduced network traffic has not been verified.

Other reporting remains, including web analytics and separate crash-reporting
paths. Local metric collection, recommendations, account requests and playback
requests are unchanged. This is not a telemetry-free build and does not prevent
Google from detecting modified clients or ad blocking.

The player, DRM and Google verification are unchanged by this metrics patch.
Previous releases remain available for rollback.
