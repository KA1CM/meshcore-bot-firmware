# Continue at home

Pull the parent project and its pinned firmware submodule:

```sh
git pull --ff-only
git submodule update --init --recursive
```

The firmware work is on `meshcore-bot-working` in KA1CM/MeshCore. The parent
repository pins the exact commit; submodule update normally leaves a detached
HEAD. Create a working branch before making further firmware commits. Do not
reapply the historical patch queue to this already-modified firmware.

Copy `colorado/platformio.monitor.example.ini` to
`vendor/MeshCore/platformio.local.ini`, then replace every placeholder locally.
The real local file and all compiled images are intentionally excluded from Git.
Use the credentials from this chat or transfer the existing local file privately.
For Windows builds, a password containing an apostrophe can be represented as
`-D BOT_MONITOR_PASSWORD='((const char[]){65,39,66,0})'` (example password A'B).
The trailing zero terminates the string. Do not commit the real credentials.

```sh
python scripts/build-monitor-page.py
pio run -d vendor/MeshCore -e heltec_v4_companion_radio_usb -t mergebin
```

Use the application image `firmware.bin` at offset `0x10000` when updating the
existing board, preserving its filesystem and radio settings. Do not erase flash
or upload a filesystem. The user manually resets after flashing; report verified
flash completion immediately so they can do that.

## Current checkpoint

The latest flashed application includes the individual Check buttons with no
cooldown, the saved-path reuse -> flood reuse -> flood login -> flood login retry
sequence, and the full dashboard. It also includes primary/secondary Wi-Fi
fallback with 30 seconds per attempt and a ten-minute cutoff until reboot.
The dashboard uses seven-day history, EST/EDT with 24-hour timestamps, a combined
chart, bulk selection, NEXT SUNRISE, and the bot name in the header.

Native core checks, mocked sequence/individual-check checks, JavaScript syntax,
and the final firmware build passed. Flash was hash-verified. A previous live
BFA8 check returned 3.790 V. The latest individual-check flow and full fallback
sequence still need live verification after reset. Long-term sunrise scheduling
and a complete physical ten-minute Wi-Fi timeout remain to be verified.

The saved repeater list/history live on the board, not in Git. The initial ten-key
list is included, but may differ from the user's latest enabled selections.
See REPEATER-MONITOR.md for behavior, build instructions, and the pre-existing
parent test-runner mismatch involving missing ResponseCoordinator files.
