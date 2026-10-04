# Continue at home — October 4, 2026

Parent repository: KA1CM/meshcore-bot-firmware, branch `main`.
Firmware repository: KA1CM/MeshCore, branch `meshcore-bot-working`,
commit `f88d5541` (admin notes/passwords, named replies and dashboard charts).
The parent pins the firmware commit. Pull both together; do not reapply the old
patch queue. Internet problems at work prevented reliable live network testing.

## Resume safely

Inspect both working trees and preserve any home changes first. With clean trees:

```sh
git pull --ff-only origin main
git submodule sync --recursive
git submodule update --init --recursive
```

Submodule update normally leaves a detached HEAD. To continue editing, record the
pinned SHA, switch to `meshcore-bot-working`, and fast-forward that local branch to
the pinned SHA. If the branch has diverged, preserve/reconcile changes; do not reset
or force-push. Keep the home's own ignored `platformio.local.ini` and secrets.

## Work completed today

- Short repeater names preserve punctuation/UTF-8 throughout and remove exact,
  case-sensitive `- FN31` and everything after it. Existing 24-character/32-byte
  limits remain. Other grid prefixes and lowercase `fn31` remain unchanged.
- Admin DMs: `notes <rpt>` views paged notes; `notes set <rpt> | <text>` replaces
  notes. No append/clear commands; empty replacements are rejected. Text spaces
  and newlines are preserved. Notes use the same dashboard storage.
- Admin DM: `password <rpt> | <passwd>` adds/replaces the bot's private saved login
  password (1–15 bytes, no controls). It does not change the repeater's password,
  echo it, or export it. Empty input is rejected.
- Enable/disable replies use short names, including already-enabled/disabled
  replies. Add/remove replies also use short names, falling back to `Repeater`
  if unknown. Remove captures the name before deleting the entry.
- Stats now says `Last 24h: <n> responses`, followed by descending command
  percentages. Admin commands and authorized admin help share one `admin` line.
  Counts represent accepted commands once, regardless of pages/retries.
- Dashboard: 30 Eastern calendar-day stacked bars and a pie defaulting to the
  rolling last 24 hours. Clicking/keyboard-selecting a bar switches the pie to
  that day; the reset button restores last 24 hours. Selection survives refresh.
- Daily history uses a bounded private NVS store, saved hourly and restored after
  reboot. History begins after clock synchronization; it cannot backfill old
  activity. Power loss can lose up to an hour of unsaved daily totals. The rolling
  24-hour counters still reset at reboot.
- Latest layout revision aligns the two charts vertically with matching headings,
  removes the bar-only legend and pie-side table, and adds one horizontal shared
  legend beneath both charts with selected-period counts/percentages. It wraps
  on phones. HTML and generated embedded page header are both updated.

## Build and device checkpoint

The firmware before the final shared-legend layout revision built successfully
for `heltec_v4_companion_radio_usb` and was flashed with hash verification to the
work board on COM14 (USB serial F8:5B:1B:BF:08:38). Application only, at 0x10000;
saved settings were preserved. RESET was left to the user.

**The latest shared-legend layout is not built or flashed.** Build only when asked;
the user normally uploads manually. A DFU message alone does not authorize
assistant flashing. The work board and home Fairfield are different devices.
The Fairfield launcher targets home serial F8:5B:1B:BE:D8:C0, so it must not be used
unchanged for the work board. Work-specific Git Bash/PowerShell build+upload
commands are saved in CONTINUE-AT-WORK.md.

## Validation and remaining checks

Focused host tests passed for short names/path budgets, admin list/notes/password
commands, private credential persistence and rollback, rolling stats, daily
history retention/persistence/retry, real dashboard JSON export, and acknowledged
multipart delivery. Browser checks with synthetic data passed for click/keyboard
selection, reset, zero/missing history, single-slice pie, automatic refresh,
shared legend updates, chart alignment and phone layout. The firmware before the
last layout change built successfully. The old broad `run_tests.py` runner remains
blocked by its reference to missing `ResponseCoordinator.cpp`.

On device, validate the new admin DMs, stats, and real dashboard history after
building/uploading the latest layout. No live internet-name-lookup success was
verified at work today because of the connection problems.

The user observed a low-voltage report after manual `check <rpt>`. Current source
only schedules that report at the end of an automatic sunrise run. A pending
report waits until the monitor is idle, or unfinished scheduled checks may resume
after a manual check. Repeated reports after every check were not reproduced or
fixed; inspect running firmware/state at home before claiming a root cause.
