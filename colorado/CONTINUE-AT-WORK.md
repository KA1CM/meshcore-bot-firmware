# Continue at work — October 7, 2026

Parent: KA1CM/meshcore-bot-firmware, branch `main`.
Firmware: KA1CM/MeshCore, branch `meshcore-bot-working`.
Firmware commit: `641ba5ae8388cb7441d8278cfe5799ab9e311006` (filled by the commit-and-push script).
The parent commit pins this firmware commit. Pull both repositories together.

## Resume safely

Inspect both working trees and remotes, preserve any work-laptop changes, then fetch the KA1CM forks. Fast-forward clean, non-diverged branches only. Verify fork URLs because remote names differ between machines. Do not reset, clean, force-push, or reapply old patch queues. If the submodule is detached, preserve the pinned commit and attach the intended branch only after checking local state.

Home paths: `C:/MeshCore/meshcore-bot-firmware` and its `vendor/MeshCore`.
Work parent was `C:/MeshCore/KA1CM-meshcore-bot-firmware`; locate and verify it.
Preserve each computer's ignored `platformio.local.ini`, `out/monitor-secrets.h`, node identity, Wi-Fi and private passwords. They are excluded from commits. Device lists/passwords/notes live in device storage and are not automatically replaced by these source updates.

## Current workflow

The user builds AND flashes manually. Do not build or flash automatically.
Environment: `heltec_v4_companion_radio_usb`; home hardware is Heltec V4.3 with an 18650 and normally a USB wall charger. Home dashboard is `http://192.168.0.103/`.
The desktop Fairfield flash launcher targets the HOME board (USB serial F8:5B:1B:BE:D8:C0). Do not use it unchanged for the work board (previous serial F8:5B:1B:BF:08:38, COM14). Verify the actual port/device before any user-requested upload. Preserve filesystem/settings.

The assistant has not built or flashed this checkpoint. The user has manually tested intermediate firmware, including internet alerts and three battery CSV experiments. The latest source changes still need the user's manual build/flash and live verification; do not infer deployment merely from passing host tests.

## Changes since the October 4 work checkpoint

- Admin help is a compact overview with detailed `help <command>` replies. Preserve the user's manually edited wording.
- Notes/password saved replies name the repeater. Raw note line breaks survive copy/paste. Password edits avoid a large stack copy and preserve saved credentials on failed storage/allocation.
- Structured notes: Enclosure, Antenna, Board, Firmware, RXPS. `notes set <rpt> | antenna | Alpha-915` edits one field; whole-note replacement remains available. Enclosure labels and live notes are saved in `colorado/repeater-notes.json`; local-device application was already completed at home.
- Short names: remove space-delimited FN31-prefixed words case-insensitively; stop at `- FN31` case-insensitively. Preserve other punctuation/UTF-8. Limit 20 characters / 32 bytes. If a multiword name exceeds the character limit, remove the whole word hit by character 20 and all following words. Single-word names keep the character cutoff; callers use a key when the result is empty.
- Path replies retain the first five hop positions and final hop before ellipsis. Compacted names become full hashes, never `~`. Online resolution only targets unknown first-five hops; later hops can use learned/local names. Lookup queue has four entries and a five-second successful-request interval.
- Path diagnostics keep the last 30 events with user/channel, cooldown ignores, full-queue fallback, memory and timing. The card is collapsed below command activity. Local names/cache remain available during confirmed internet loss; new online lookups are skipped until restored. Confirmed recovery clears the previous lookup failure backoff.
- Dashboard refresh pauses until the path queue is empty to prevent overlap with TLS memory use. Wi-Fi retries indefinitely, and reconnect resets the HTTP listener. Wi-Fi status is in the header with `0d 2h 30m` durations. Monitor activity is unified with repeater names.
- `users` returns as many of the top five users as fit in one message. Dashboard Top users shows up to ten based on available card height. Exact display names merge across companions/channels. Counts use rolling 24-hour accepted commands; tracking resets at reboot.
- Stats replies use one message: `<n> responses in the last 24h`, then command percentages. Dashboard charts have brighter colors. Removed tracking-limit and bucket captions requested by the user.
- Dashboard encoding repaired, with a generator check for corrupted UTF-8. Monitor status shows bot battery below IP and above Last advert.
- Every bot text reply, DM retry and notification is queued at least 300 ms before transmission. Direct/flood ACK timeout includes that delay; other companion sends keep their default timing.

## Power and connectivity notifications

See `CONNECTIVITY-NOTIFICATIONS.md` and `BATTERY-SIGNATURE-TEST.md`.

USB detection is now continuous: sample every second, average the previous 10 seconds, require a 25 mV change sustained for 20 seconds. Boot calibration lasts 60 seconds and ASSUMES USB IS CONNECTED. It uses under 200 bytes of fixed RAM, independent of the optional 10-minute CSV recorder. It is a voltage-signature heuristic, not a GPIO USB sensor. Booting on battery alone cannot establish the correct initial USB state. Brief dips, missing samples and invalid zero readings do not alone confirm transitions.

All three home CSVs replay with one loss/restoration each: two near-full-charge tests (~33–42 mV change) and one started near 3.90 V before charging (~180–210 mV change). Connected ADC readings near 4.174 V reflect charging conditions rather than resting battery voltage. No raw CSV or private credential is committed. Continuous alert delivery needs live verification after the latest manual build.

Admin DMs go to existing contacts with Notifications permission enabled, using the acknowledged radio queue. Reports fit one message, no page numbers:

- Power loss: `USB power lost`, loss timestamp, `Battery 4.03V`. Hourly: `USB power lost since`, original timestamp, current battery. Restore: `USB power restored`, `Total time xh ym`, current battery.
- Wi-Fi loss: `Wi-Fi disconnected`, loss timestamp. Hourly: `Wi-Fi disconnected since`, original timestamp. After reconnect, perform a fresh internet check before reporting. Success: `Wi-Fi: Restored`, `Internet: Restored`, `Total time xh ym`. Failure: `Wi-Fi: Restored`, `Internet: Lost since`, original internet loss timestamp.
- Internet-only loss: `Internet lost since`, first-failure timestamp. Hourly repeats that wording/timestamp. Restore: `Internet restored`, `Total time xh ym`.

Normal internet checks are five minutes apart, including confirmed outages. A successful ONLINE path lookup resets that timer; local/cached resolutions do not. After the first failed round, retry twice at 30-second intervals, confirming loss in about one minute plus probe/delivery time. A successful round cancels the failure streak. Ordinary internet restoration requires two successes; the immediate Wi-Fi reconnect check supplies a combined report from one fresh check.

Probes use bounded tiny plain-HTTP responses from Microsoft/Mozilla, in a worker that cannot overlap the path worker. A failed endpoint falls back to the second endpoint. Redirects/unexpected content fail. Deferred checks/allocation failures are not network failures. An in-flight path request may finish its existing timeout after an outage is declared.

Power, Wi-Fi and internet reminders have independent hourly timers. No duplicate internet-loss reminders while Wi-Fi is disconnected; a failed reconnect check starts internet-only reminders. Durations use monotonic elapsed time; timestamps use Eastern time or an honest unavailable-clock label. Queued events and outage tracking reset on reboot. The bounded queue and radio ACK/retry limits make delivery best effort.

## Validation

October 7: focused host checks passed for admin help/notes/passwords, list parsing/delivery, short names/path budgets, stats/dashboard export, top users/layout, dashboard refresh/activity, Wi-Fi recovery, battery recorder, continuous USB detection, connectivity scheduling/exact report formats, offline path cache behavior, response delays, path event history/FIFO, and sunrise notifications. All three measured CSVs were replayed against the actual continuous USB detector. No firmware build was run by the assistant.

Compiler: native g++ with CXX pointing at the installed MinGW compiler; Windows may need its bin directory on PATH. Tests are under `tests/firmware_bot/`; admin advert/help test is `vendor/MeshCore/tests/test_bot_advert.py`. The old broad `run_tests.py` references missing ResponseCoordinator.cpp; use the focused tests rather than claiming that runner passes.

## First checks at work

After preserving local configuration and fast-forwarding both repos: inspect this handoff and the pinned submodule, then continue the user's requested work. After the user's next manual build, verify USB loss/restoration and hourly reminder formats, boot with USB connected for calibration, internet failure confirmation at 30-second intervals, immediate Wi-Fi reconnect probe, and local/cached path replies during confirmed internet loss. Watch heap/dashboard reachability and radio delivery during lookups.
