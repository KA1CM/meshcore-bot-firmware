# Continue at home — October 3, 2026

Today's firmware is pushed to KA1CM/MeshCore, branch `meshcore-bot-working`,
commit `dab98c39`. The parent KA1CM/meshcore-bot-firmware `main` pins that commit.
Do not reapply the historical patch queue.

## Resume safely

Inspect both working trees before updating:

```sh
git status
git -C vendor/MeshCore status
git fetch origin
git -C vendor/MeshCore fetch origin
```

Preserve any home changes before proceeding. With clean working trees:

```sh
git pull --ff-only origin main
git submodule sync --recursive
git submodule update --init --recursive
```

The submodule uses the KA1CM fork configured in `.gitmodules`. Updating normally
leaves a detached HEAD at the parent-pinned commit. To continue firmware work,
record that pinned SHA, switch to the existing `meshcore-bot-working` branch,
and fast-forward it to the pinned SHA with `git merge --ff-only <pinned-SHA>`.
If the branch does not exist, create it at the pinned SHA. If it has diverged,
stop and preserve/reconcile the home work; do not reset or force-push.

Keep the existing home `vendor/MeshCore/platformio.local.ini`. If missing, copy
`colorado/platformio.monitor.example.ini` there and fill in placeholders locally.
Real credentials and compiled images are excluded from Git. Windows passwords
may be represented as C character arrays; a helper that reads these as literal
strings will fail dashboard authentication. Do not change the password to fix that.
The saved repeater list, history, and radio settings live on the device.

## Today's changes

- Preserved the user's admin help, advert, check, and sync response edits.
- Added named path replies using local contacts, then verified HTTPS lookups
  against analyzer.ctmesh.org for unknown 2-byte and 3-byte prefixes.
- Names use the first word including special characters, then letters, numbers,
  and spaces until punctuation; limit 24 characters (existing storage is 32 bytes).
- First three and last names are protected. Middle hops use hashes when needed,
  then an explicit `...` if necessary. See PATH-NAMES.md for exact budget handling.
- One-byte paths reply `@sender 1-byte paths are not supported.`
- Added persistent last-failure dashboard diagnostics, bounded HTTP body reading
  without requiring Content-Length, and a socket DNS resolver retaining TLS
  hostname/certificate verification.

## Device checkpoint — live test still needed

Stamford Bot is the work test unit at `192.168.0.101` / `mesh-bot.local`.
Fairfield at home remains yesterday's reference firmware; these are different
radios/routes. Do not assume Fairfield already contains today's changes.

The latest application was built and flashed to Stamford successfully with
checksum verification. The user must press RESET after DFU flashing. No successful
live internet name lookup has yet been confirmed after the final DNS change.
Clock synchronization was confirmed by the user. Earlier diagnostics showed
HTTP connection failed, code -1. DNS failure was inferred from library behavior,
not proven on the device; the new diagnostics distinguish DNS, TCP, and TLS errors.

Known Stamford path: `ce65,f0d0,b2d9,bfa8`. The directory returned unique names;
expected reply:

```text
@jim
Stratford Ctr
TheWatcherInTheWater
Canoe Hill
North Stamford
```

Next: test a 2-byte path after reset and inspect Path lookup diagnostics if hashes
remain. One-byte requests intentionally reject and do not test internet lookup.
The RAM cache clears at reboot; failures back off for 60 seconds. Preserve the
last-failure stage/code when reporting results. Automated dashboard reads received
401; the user's dashboard access works.

Latest flashed application: `meshcore-bot-heltec-v4-usb-dns-fix-v2.bin`
(1,446,208 bytes), SHA256:
`b67ff2e2c3b110bb8a8ec6306bf2f4e65f960786e914b1330e7f5130ec4313cd`.
Binaries are not committed; rebuild from this checkpoint and local configuration.

```sh
python scripts/build-monitor-page.py
pio run -d vendor/MeshCore -e heltec_v4_companion_radio_usb
```

Flash only the application `firmware.bin` at offset `0x10000` on the existing
ESP32-S3 board, preserving filesystem/settings. Do not erase flash or upload a
filesystem. Work-laptop ports were DFU COM14 and application COM15; rediscover
ports at home. Report flash verification and ask the user to press RESET.

## Validation

Full USB firmware build, dashboard JavaScript syntax check, path tests,
signal tests, list tests, and Git whitespace checks passed. Focused test commands:

```sh
python tests/firmware_bot/run_path_tests.py
python tests/firmware_bot/run_sig_tests.py
python tests/firmware_bot/test_list_command.py
```

Host tests require a C++ compiler; path tests use the PlatformIO-installed
ArduinoJson headers. The older broad runner has a pre-existing
ResponseCoordinator/expectation mismatch and is not claimed to pass.
End-to-end name lookup, radio responsiveness during lookup, and DM/group behavior
still require live verification. Prior dashboard/check-flow and long-duration
Wi-Fi/sunrise validation caveats remain documented in REPEATER-MONITOR.md.

## Flashing preference (October 3 update)

Build only when requested. After a successful build, provide the firmware and
`scripts/flash-fairfield.cmd`; the user flashes manually. Do not automatically
flash on a DFU message unless the user explicitly requests assistant flashing.
The launcher detects Fairfield by USB serial, writes only the application at
0x10000, checks esptool success, and prompts for RESET. It never rebuilds.
