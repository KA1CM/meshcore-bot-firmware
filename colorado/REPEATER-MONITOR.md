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

## Read-only dashboard access

Set `BOT_MONITOR_GUEST_PASSWORD` in the ignored `vendor/MeshCore/platformio.local.ini` to enable the `gu3st` login. Guests can view readings, charts, history, and export the saved list. Only `admin` can run checks or modify/import the list. The server rejects guest POST requests with HTTP 403, even if dashboard controls are bypassed. Omit the flag to disable guest login.


## Private repeater passwords and manual clock sync

Repeater passwords live in a separate ESP32 NVS namespace (`monitor-private`), keyed by the full public key. Neither public list exports nor monitor history contain passwords. Dashboard state exposes only `passwordConfigured` to administrators. There is no endpoint for reading passwords. `POST /api/password` requires dashboard admin authentication and the existing mutation header; it sets/replaces or clears one saved key or all currently saved keys. It never changes the repeater's own password. Passwords are limited to 15 bytes by the MeshCore protocol. Removing a list member deletes its stored credential; newly added keys do not inherit credentials.

Optional first-boot provisioning is defined in the ignored local file `vendor/MeshCore/out/monitor-secrets.h` with `BOT_REPEATER_INITIAL_PASSWORD`. On the first boot with the private store absent, it binds that password only to the list loaded from the bot's saved settings. The persistent store prevents reseeding after a password is cleared or changed. Do not commit or distribute that local header or the resulting firmware binaries. NVS storage is not encrypted against physical flash extraction. Browser password entry uses the dashboard's existing HTTP transport, so it requires a trusted local network.

An administrator can use **Sync time** beside a repeater. `POST /api/sync-time` accepts only a saved public key, never an arbitrary CLI command. It requires a configured password, idle monitor, and NTP sync within six hours. Every time-sync process starts with a fresh admin password login, even when prior access was confirmed. Every login attempt uses flood, up to three attempts per login sequence. `clkreboot` and `clock sync` also always use flood, including retries. Outgoing calls use a contact copy so selecting flood does not overwrite the saved contact route. Exhaustion records “Admin login timeout”. A reply that explicitly does not grant admin access stops the operation. Successful admin login records the approximate clock offset and round-trip uncertainty before choosing the next action; the login timestamp may be influenced by the repeater's unique-message timestamp counter. No initial access reuse or extra login retry after an unconfirmed sync command is performed. Each reboot recovery starts a new bounded login sequence. Responses are matched to the full public key and an echoed CLI prefix. Battery checking, list edits, credential changes, and other clock operations cannot overlap it. Sunrise checks can also start this process under the automatic maintenance rules below.

After initial login, a negative offset schedules `clock sync`; an offset from zero through +180 seconds stops with “Clock is ahead, but close”. An offset above +180 seconds starts recovery: send `clkreboot`, wait the response timeout (30–180 seconds) plus 30 seconds, then perform fresh admin login and save a new offset. Recovery allows at most three reboot commands. After each reboot, a negative offset leaves recovery and schedules sync; a still-positive offset permits another reboot up to that limit, even if now below 180 seconds. Exactly zero stops without another reboot. Exhaustion records “Reset limit reached”. A reboot command reply does not itself prove a reboot; the bot still waits and rechecks through login.

A `clock sync` timeout permits three additional sends (four total), spaced by three seconds after each timeout. Each send uses a fresh echoed prefix; late replies from earlier attempts cannot confirm a later one. A matching success saves Last synced and reports “Successful sync”, including after recovery. Four unanswered sends report “No confirmation received”; the remote clock may have changed despite a lost response. Explicit backward refusal stops with “Clock sync refused” or “Sync refused after reset”; no separate wall-clock query is sent. Stale NTP, invalid login timestamps, missing admin permission, send failures, and storage failures stop the operation. The login offset is approximate and can include repeater timestamp-counter bias. Guest users can view results but cannot trigger sync.

The dashboard shows **Last synced** for each repeater, for both admin and guest. It records the bot’s time when a matching successful clock-sync confirmation arrives, including recovery after reboot, and persists it with monitor history. Failed, refused, and unconfirmed attempts do not replace it. Older saved settings show **Not recorded** until the next confirmed sync; earlier successes cannot be reconstructed. List imports cannot supply or overwrite sync history.

Clock replies from manual sync also persist an independent offset measurement, including when no reset is needed. The dashboard chooses the newest available clock sample and shows its measurement time. CLI wall-clock samples use the middle of the reported minute, with uncertainty of 31 seconds plus half the round-trip time rounded up. A confirmed clock adjustment replaces or clears the earlier offset so an old future-clock reading is not presented as current. This uses existing replies and adds no radio requests.

Learned repeater names are retained in monitor snapshots independently of the radio contact table. Current nonempty contact names take priority, followed by the saved learned name and then the manual name. Older snapshots migrate their displayName fallback on load. Newly heard names are checkpointed when changed, checked at ten-second intervals, so a restart or missing contact does not blank the dashboard unnecessarily.


## Sunrise clock maintenance

After each enabled repeater's scheduled sunrise battery check finishes (successful or failed), the bot uses the newest valid clock measurement at/after the last successful sync. An offset of at least +600 or at most -600 seconds triggers sync. A smaller offset counts as a clock verification: its measurement timestamp defers automatic sync until it is 30 days old, even if no successful sync is recorded. Without a relevant measurement, sync is due when the last successful sync is missing or at least 30 days old. Future-dated measurements are ignored. Older pre-sync samples cannot trigger maintenance, and a newer small offset supersedes an older large offset. Manual battery checks do not initiate automatic clock sync. This scheduling rule does not replace the last successful sync timestamp.

The saved daily-check marker limits this to one automatic sync process per repeater per daily run, including after a bot restart. Sync still requires recent NTP, working storage, a saved password and a contact. The next repeater waits until sync/recovery ends, followed by a ten-second gap. Existing bounded admin-login retry and three-reset/reboot recovery apply; a sync failure does not change the battery result. Dashboard guests remain read-only.

Each started sync attempt also saves its latest outcome and attempt time, displayed beneath the last successful sync or offset. An interrupted attempt is reported as unconfirmed after a restart. Failed attempts preserve the last successful sync timestamp.

Passive clock measurements: verified zero-hop repeater adverts can update the saved offset without transmitting. Only enabled listed keys with fresh bot NTP are considered while the monitor is idle. Two increasing advert timestamps must advance with local reception time (30 seconds to one day apart, within ten seconds). Signature and existing contact replay checks run first; candidates are keyed by the full public key and reset on reboot. Relayed adverts are excluded. Accepted estimates are saved at most hourly, except crossings of the ±600-second threshold, and participate in the 30-day rule without changing Last synced. The ten-second uncertainty is an estimate: passive observations cannot prove freshness against a previously unseen or deliberately delayed sequence of signed adverts. Failed saves restore the previous measurement.

Modern login replies accept the 13-byte payload plus up to 15 zero-padding bytes retained after a PATH prefix is stripped. Time sync and login clock estimation use the same validation, including flood replies longer than 16 bytes.

A successful modern battery-check login immediately persists its clock estimate and measurement time (admin or guest access), independently of the later voltage response. A voltage timeout does not erase that estimate. Legacy logins without a usable timestamp leave prior clock measurements unchanged. Storage failure restores the prior measurement and stops the check.

The radio command `list` (also `!list` or `/list` under the normal bot channel rules) returns all configured repeaters' latest stored check results, including disabled entries. It does not poll repeaters. Names retain ASCII letters, digits and internal spaces up to the first punctuation/special character, trimming spaces before that character (for example, `Chestnut Hill - FN31jf` becomes `Chestnut Hill`); empty prefixes fall back to an eight-digit key prefix, and duplicate short names gain a key suffix. Voltages are rounded to two decimal places. The latest failed/missing reading is `N/A`, rather than silently showing an older voltage. Replies headed with the current page and total (for example, `1/3`, `2/3`, `3/3`) split only between entries and are sent at least five seconds apart; DM parts wait for the existing acknowledgement/retry flow. One list snapshot can be queued at a time, with bounded send failures and a ten-minute expiry. `help`, `cmd`, and `help list` include the command. Version-7 bot preferences migrate to version 8 with `list` enabled while retaining other settings and command choices.

Dashboard repeater rows, public list exports, and radio `list` replies sort west to east by learned contact GPS longitude. Missing, invalid, or unset (0,0) locations sort last; equal longitudes and unknown entries retain saved relative order. Sorting does not rearrange the live monitor entries or retarget an active check. Password flags and the active-row indicator are mapped by full key after sorting.

Learned GPS coordinates are now cached alongside learned names in monitor snapshots. Startup recovers valid coordinates from signed stored adverts after checking the public key, signature, payload lengths and advert age, even if the name already matches. The periodic contact scan persists newly learned or changed valid locations; missing/zero coordinates do not erase cached locations. Sorting prefers valid live coordinates and falls back to the cache. Public list imports cannot overwrite learned location history. If neither a valid saved advert nor a cached location exists, the repeater stays in the unknown-location group until a location is learned.

`list low` filters the same saved, geographically ordered list to latest successful readings strictly below 3600 mV plus all N/A entries. Exactly 3.6 V is excluded; filtering uses raw millivolts before display rounding. It never initiates radio checks. If nothing matches, the reply is “none”. `help list` sends these two lines in one message:
```text
list: list of all managed repeaters with last saved voltage
list low: list of repeaters with voltage below 3.6V or N/A
```
`help list low` sends only the second line.

## Admin DM repeater-list commands

- `add <full key>` adds a unique, nonzero 64-hex-character public key, enabled by
  default, and runs the existing favorite-contact protection. Set any new repeater
  password separately in the dashboard; no password is inherited.
- `remove <repeater>` removes the managed entry, its notes/history and saved
  password. The companion radio contact and favorite flag remain intact.
- `enable <repeater>` / `disable <repeater>` change the managed enabled flag while
  preserving notes and history. Disabled entries remain available for explicit
  manual checks but are excluded from scheduled checks and list/list low replies.

Name matching is case-insensitive and must identify exactly one repeater. A unique
key prefix of at least four hex digits can identify entries without names.
Only full-key-authorized admin DMs can mutate the list. Channel messages and
non-admin DMs cannot. Busy operations reject edits, ambiguous names reject edits,
and failed saves roll back the in-memory list. Admin help includes all four commands.

## Rolling stats

`stats` now uses a fixed snapshot sent through the paced multipart reply queue.
The summary (seen, accepted/ok, sent, fail, RF rx/tx/errors) and command breakdown
use the same 96-bucket quarter-hour window. Buckets older than the retained window
are discarded; the oldest partial quarter-hour is excluded, so precision is 15
minutes and no event older than 24 hours is included. The window uses monotonic
millisecond deltas, handles timer wrap, and is unaffected by NTP corrections.
It resets at reboot and does not write per-message statistics to flash.

Only commands with accepted requests appear, ordered by descending count. Each
percentage is the rounded share of all accepted requests, including admin commands
and the current stats request; rounded values need not sum to exactly 100%.
Aliases share a command's count; list low counts under list and neighbors all under
neighbors. Rejected/cooldown messages do not contribute to command shares. Sent
counts include each reply page and notifications, not confirmed reception.
The report's own replies occur after its snapshot and appear in later reports.
The existing status command and console counters remain lifetime-since-boot values.
