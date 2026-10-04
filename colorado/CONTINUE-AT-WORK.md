# Continue at work — October 4, 2026

Latest work checkpoint: firmware `f88d5541` on `meshcore-bot-working`. See
CONTINUE-AT-HOME.md for the complete October 4 handoff, tests and deployment
status. The chart shared-legend layout is newer than the last work-board flash
and still needs a requested build/upload. The earlier morning checkpoint below
is retained as background.


## Checkpoint and deployment

Both repositories should be pushed together: parent `main`, vendor
`meshcore-bot-working`, on the KA1CM remotes. The parent pins the vendor commit.
Inspect both working trees, preserve local changes, fetch the KA1CM forks, and
fast-forward only if clean and not diverged. Remote names differ between machines;
verify URLs before pulling. Never reapply the historical patch queue or reset work.

**Latest source is NOT yet built or flashed.** Admin list commands and rolling
stats were added October 4 and have passed focused host tests only.

The home Fairfield bot currently runs the October 3 clickable-path-mention build.
The user confirmed lookup was working. The successful lookup diagnostics reported
three internet-resolved names and about 108 KB free memory. Earlier certificate
and timeout failures were addressed with these changes together; no isolated
experiment established which change resolved each failure:

- GTS Root R4 from Google's official repository, verified against the analyzer.
- TLS certificate verification flags captured before connection cleanup.
- Notes stored as actual-length strings instead of fixed buffers, reducing static
  RAM by 64,752 bytes. Copies and rollback use proper object copying.
- TLS handshake allowance 15 seconds; path wait 28 seconds, DM expiry 45 seconds.
- Path mentions use `@[name]` like test, with adjusted message budgets.

## New source work to validate on device

Authorized admin DMs now support:

```
add <full key>
remove <repeater>
enable <repeater>
disable <repeater>
```

Adds start enabled, use favorite protection, and do not inherit passwords.
Remove deletes the managed entry/history/notes and saved password, leaving the
radio contact/favorite intact. Enable/disable preserves saved data. Case-insensitive
partial names must match exactly one entry; unique key prefixes of at least four
hex digits also work. Busy operations reject edits; failed saves roll back.
Admin help includes all four commands.

`stats` now pages a rolling summary and command counts/percentages, sorted by
frequency. It uses 96 fifteen-minute buckets, dropping the oldest partial bucket,
so it includes no records older than 24 hours but has 15-minute precision.
Counters reset on reboot. RF totals and bot summary share the window. Percentages
count accepted requests (including stats itself); aliases and command arguments
share the parent command's count. It uses about 16 KB additional static RAM.
After building, check free heap and TLS again, and verify real multipart DM and
channel delivery. Status/console counters remain lifetime values.

## User workflow preferences

**Do not build until asked. User flashes manually from now on.** After a requested
build, provide the firmware path and point to the desktop Flash-Fairfield launcher.
The launcher calls `scripts/flash-fairfield.cmd` and `.ps1`, identifies the home
board by its USB serial, and flashes application only at 0x10000. It never builds,
erases the filesystem, or resets the board. Press RESET after flashing.
It is specific to Fairfield and must not be used for a different work test board
without intentionally adapting device identity. A DFU message alone no longer
requests assistant flashing.

Credentials remain in ignored local configuration and monitor-secrets.h. Preserve
the work laptop's own configuration and node identity. Never commit secrets.
Repeater notes and settings persist on the device; exported October 2 notes are
in colorado/repeater-notes.json, not automatically applied at build time.

## Tests

Focused host tests: test_admin_list.py, test_stats_window.py,
test_path_tls_diagnostics.py, test_monitor_export.py,
test_monitor_private_routes.py, test_monitor_sync.py, test_list_delivery.py,
run_path_tests.py, and vendor/MeshCore/tests/test_bot_advert.py.
Use a native C++ compiler for these tests. Firmware environment:
heltec_v4_companion_radio_usb. No October 4 firmware build has been requested.

The suggestion to move lookup diagnostics into a collapsed admin-only section
has NOT been implemented or explicitly approved yet.

## Work PC manual build and upload command

For Git Bash on this work PC, use the `Ting` user directory and explicitly select
`vendor/MeshCore`, where `platformio.ini` lives. This command builds and uploads;
run it only when you intend both actions. COM14 is the work board's current DFU
port (USB serial F8:5B:1B:BF:08:38); check the port if Windows assigns another.

```bash
/c/Users/Ting/.platformio/penv/Scripts/platformio.exe run \
  --project-dir /c/MeshCore/KA1CM-meshcore-bot-firmware/vendor/MeshCore \
  -e heltec_v4_companion_radio_usb \
  -t upload \
  --upload-port COM14
```

For PowerShell, use its continuation character (backtick), or this one-line form:

```powershell
& "$env:USERPROFILE\.platformio\penv\Scripts\platformio.exe" run --project-dir "C:\MeshCore\KA1CM-meshcore-bot-firmware\vendor\MeshCore" -e heltec_v4_companion_radio_usb -t upload --upload-port COM14
```
