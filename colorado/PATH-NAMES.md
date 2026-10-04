# Path names

`path` and `path <hashes>` reply with `@[sender]` on the first line and one hop
per line. Known repeaters use the same short-name rule as `list` and `snr`: preserve
the first space-delimited word including punctuation and UTF-8 symbols, then
allow letters, numbers, and spaces in later words until punctuation occurs.
Names are limited to 24 characters and trailing spaces are removed. Leading
spaces are ignored. Controls and invalid UTF-8 stop the name. The existing
32-byte name storage may shorten multibyte names sooner, at a UTF-8 boundary.
Message budgets still count bytes.
Unknown or ambiguous hops retain their full path hash. Only the `path` command
changes; `test` and `snr` keep their existing formats.

The first three repeater names and the final repeater name are protected.
If names exceed the channel message budget, only middle names are replaced
with hashes (largest savings first). If even hashes cannot fit, a contiguous
middle section after the first three hops is replaced by a standalone `...` line.
If the protected names alone exceed one message, the first three are abbreviated
with `~` as needed; the final short name stays intact. Protected hops are never
omitted or replaced with hashes merely to save space. Unknown or ambiguous hops
still use their hashes because no reliable name is available.

Local repeater contacts take priority. On ESP32 monitor builds, unknown 2-byte
and 3-byte prefixes are sent to analyzer.ctmesh.org/api/resolve-hops by a background
task, using certificate-verified HTTPS. No sender identity or message body is sent.
Only unique-prefix results with one candidate, no conflicts, and a matching full
public key are accepted; directory heuristic picks are ignored. A unique result
is only unique within the directory's current knowledge, not proof of identity.

RAM cache: 64 entries, positive names expire after 24 hours, misses/collisions
after 15 minutes. Network calls are at least 10 seconds apart; failures back off
for a minute. Replies fall back to local names/hashes after 28 seconds; pending
DM replies wait for the existing acknowledgement slot, up to 45 seconds total.
One internet lookup is allowed at a time; concurrent requests use local results.
The cache clears on reboot. Wi-Fi and valid system time are required for fresh
HTTPS lookups. Offline cached results can still be used. No contacts are imported.

The trust anchor is GTS Root R4 from Google’s official certificate repository,
verified against the current site using this root alone. This anchors the WE1
chain directly instead of relying on its cross-sign to GlobalSign. The ESP32
reported certificate verification flag 0x8 with the former GlobalSign anchor;
the direct-root change still requires a device test.
A future CA change or root expiration requires a trust-store update; failures
retain hash replies, never bypass certificate verification.

Validation: `python tests/firmware_bot/run_path_tests.py` covers formatting,
full message budgets, unknown/colliding names, omission, final-hop preservation,
malformed paths, 3-byte parsing, and resolver candidate validation. It uses the
ArduinoJson headers installed by PlatformIO for the USB companion environment. Device validation should check Wi-Fi loss,
lookup latency, free heap, radio responsiveness, and DM/group delivery before use.

The HTTPS reader accepts known-length, close-delimited, and HTTPClient-decoded
chunked responses. It caps decoded bodies at 32 KiB and rejects failed, oversized,
or truncated transfers. This includes the analyzer's response without a
Content-Length header, which the original firmware incorrectly skipped.

DNS uses the standard IPv4 socket resolver in the background worker, retaining
the analyzer hostname for TLS SNI and certificate validation. Diagnostics now
distinguish DNS failure, TCP connection failure, and TLS handshake failure.
One-byte paths reply `@[sender] 1-byte paths are not supported.` without an
internet lookup. Direct zero-hop paths still reply Direct.

TLS handshakes have a 15-second deadline. Diagnostics distinguish a completed
TCP connection whose TLS handshake times out, and report its elapsed milliseconds.
This change requires live testing; code 11 alone did not establish the cause.
