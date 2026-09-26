# Repeater battery monitor

This optional Heltec V4 USB feature hosts a local dashboard and checks an editable
list of up to 32 open MeshCore repeaters. Google Forms is not used.

## First use

1. Install the monitor firmware, keeping the existing filesystem and radio settings.
   Do not run a filesystem upload or a whole-chip erase.
2. Connect your phone or computer to the bot's Wi-Fi network. Open
   `http://mesh-bot.local/`, or the bot's IP address from the router's client list.
   Networks with client isolation may prevent access between devices.
3. Sign in as `admin`. The local build password is the `BOT_MONITOR_PASSWORD`
   value in `vendor/MeshCore/platformio.local.ini`. This file is ignored by Git.
4. Use **Import list**, select `colorado/repeater-monitor-initial.json`, review
   the ten keys, and choose **Save list**. Keys are data, not compiled into firmware.
   Blank labels use a known contact's name when available, or its key prefix.
5. Wait for internet time synchronization. If sunrise has already passed, the
   enabled entries are checked automatically. Otherwise choose **Check now**
   for an initial test. A complete sweep can take several minutes.

Add, rename, remove, or enable/disable repeaters in the dashboard. Changes are
applied with **Save list**; editing is held while a sweep is running. **Export
list** downloads a backup of keys, labels, and enabled settings. Removing a repeater
also removes its history from the active settings. Adding it again starts fresh.

The password gates both dashboard reads and changes using HTTP Digest authentication.
Mutating requests also require a custom header (no cross-origin access is enabled).
The dashboard uses local HTTP, not HTTPS; use it on a trusted LAN, not through
internet port forwarding. Wi-Fi stays on for dashboard access. USB remains the
MeshCore companion connection and the dashboard does not inject text into it.

## Schedule and history

- Sunrise is calculated locally for Bridgeport city-centre coordinates
  41.18 N, 73.19 W, using the [NOAA fractional-year equations](https://gml.noaa.gov/grad/solcalc/solareqns.PDF).
  It is an approximate sunrise time, not an elevation/terrain-adjusted forecast.
- The local date is America/New_York using current US daylight-saving rules.
- A sweep begins at sunrise, polling one repeater at a time. It first reuses existing access, falling back to empty-password flood login
  when needed (see Session reuse below). The battery reading is the repeater's
  reported millivolts; no battery percentage is inferred.
- Each phase waits 30–180 seconds according to the mesh's estimated timeout.
  Fallback steps wait 15 seconds, with at most two flood logins. There
  is a 10-second gap between repeaters. No-response/login-timeout/send/storage
  conditions are kept separate from a successful voltage, including a real zero.
- Full public keys and the status request tag match responses. Late, unrelated,
  and short replies cannot become a battery reading. Older repeater firmware
  that does not reflect status tags may time out and needs compatibility testing.
- Manual sweeps are limited to once per ten minutes. A manual check after
  sunrise also satisfies that repeater's scheduled check for the day.
- Seven calendar dates are retained: today and the preceding six dates, with
  one latest result per repeater/date. Manual checks replace that date's result.
  Failed readings have a status and timestamp, but no fabricated zero voltage.
- Settings, history, and each scheduled check's start marker are stored in two
  alternating files with version, sequence, length, and CRC validation. A failed
  write stops polling. Interrupted checks display as interrupted after reboot;
  already-started scheduled checks are not repeated automatically that date.
- After an outage, remaining checks for the current date run after time sync.
  Missing past days are not backfilled with current measurements. After initial
  sync, checks continue with the running clock during a Wi-Fi outage. Every reboot
  needs a fresh NTP sync before automatic or manual radio checks can run.

Existing contacts supply known radio paths. Keys without a contact get a repeater
contact and start with route discovery. The monitor does not change frequency,
bandwidth, spreading factor, or the bot's identity. It must already be configured
for the same mesh as the repeaters. Keep manual companion-app repeater sessions
separate from an active sweep; legacy login replies have no request identifier.

## Building and testing

The feature is compiled only when `BOT_REPEATER_MONITOR` is defined on ESP32.
The local `[cmesh_bot_ntp]` build flags supply `BOT_REPEATER_MONITOR=1`,
`BOT_NTP_SSID`, `BOT_NTP_PASSWORD`, and `BOT_MONITOR_PASSWORD`. The earlier
NTP-only Wi-Fi shutdown code is bypassed in this mode. No secrets belong in Git.

The monitor tries the primary Wi-Fi network first and allows 30 seconds to
connect. When `BOT_WIFI_SECONDARY_SSID` and `BOT_WIFI_SECONDARY_PASSWORD` are
configured in the ignored `platformio.local.ini`, it tries that network next.
It rotates for at most ten minutes while disconnected, then stops Wi-Fi until
the board restarts. After losing a working connection it starts a new ten-minute
window with the primary. It stays on a working fallback until that
connection is lost or the board restarts. Network attempts do not block radio
polling. These network settings currently require a firmware build to change.

After editing `RepeaterMonitorPage.html`, run `scripts/build-monitor-page.py` to
regenerate its embedded header. Build the `heltec_v4_companion_radio_usb` environment
and its `mergebin` target normally.

`tests/firmware_bot/test_repeater_monitor.cpp` is hardware-independent C++11. Compile
with the companion source directory on the include path. It covers sunrise bounds,
DST/calendar boundaries, once-daily scheduling, retention, public-key validation,
status/login response validation, timer rollover, timeout bounds, and corrupted or
truncated snapshot detection.

Login replies retain encryption padding after decryption, including replies
embedded in path-return packets. The monitor accepts the login response fields
with trailing padding rather than requiring exactly 6 or 13 bytes. Regression
tests cover both legacy and modern replies with all 0–15 padding lengths.

`scripts/preview-repeater-monitor.py` serves the real dashboard at
`http://127.0.0.1:8765` with clearly labelled sample readings. Preview edits exist
only in the preview server's memory. It sends nothing to the mesh.

The parent repository's existing bot test/safety scripts reference
`ResponseCoordinator.h/.cpp`, which are absent in the saved `cbc3afff` submodule.
They cannot validate this fork unchanged. This is a pre-existing test mismatch.

Before unattended operation, verify on the actual board: dashboard login, initial
list import, a successful real voltage, an unreachable repeater, saved settings
after reboot, and NTP/Wi-Fi recovery. Host tests and compilation do not establish
radio reachability or on-device filesystem behavior.

Session reuse: each check requests status on the saved route first, then tries
status by flood if that fails. When no saved route exists, it starts with flood
status and skips the redundant first step. If flood status fails, it tries a
blank-password flood login, with one further flood login retry. Successful login
is followed by status on the available route. Each request waits 30–180 seconds;
fallback steps wait 15 seconds, and status after login waits 3 seconds. Replies
must match the full repeater key, and status must match the current request tag.

Each saved repeater has a Check button for an individual request without the
ten-minute full-list cooldown. Disabled repeaters can also be checked manually.
Only one check or sweep runs at once; time sync and working storage are required.
The individual check ends immediately when its result is recorded. It uses the
same route/login fallback and daily history slot as a sweep, and does not change
the enabled setting or restart the full-list cooldown.
