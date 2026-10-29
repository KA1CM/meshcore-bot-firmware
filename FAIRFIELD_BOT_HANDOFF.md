# Fairfield Bot handoff

Prepared 2026-10-29 from the existing Mesh-Bot conversation. Confirm current source and live state before assuming a prior change is deployed.

## Project setup

- Requested project name: **Fairfield Bot**.
- Primary source folder: `C:\meshcore\meshcore-bot-firmware`.
- Firmware submodule: `C:\meshcore\meshcore-bot-firmware\vendor\MeshCore`.
- Keep the current local checkout, including its uncommitted source changes. Do not replace it with a fresh clone or reset it.
- Original chat and preserved diagnostics folder: `C:\Users\55tin\Documents\Codex\2026-10-13\referenced-chatgpt-conversation-this-is-an`.
- Preserve both `work` and `outputs` there; crash dumps, matching firmware images, packet observations, and exported device-state backups are local diagnostic evidence. They are not intended for Git publication.
- The existing **Mesh-Bot** chat was moved into Fairfield Bot on 2026-10-29, retaining its conversation history. Creating a new chat with this summary does not copy the full history.
- Repository access, shell execution, network access, and USB access are distinct. Do not assume that project creation grants or verifies them all.

## Publishing request and execution limitation

The user explicitly requested committing and pushing the accumulated working firmware changes. Attempts to run even `git status` failed before Git launched, with:

`windows unelevated restricted-token sandbox cannot enforce split writable root sets directly; refusing to run unsandboxed`

Git access was restored on 2026-10-29 through explicitly approved escalated command execution; ordinary sandbox execution still failed. Both repositories' current branches were confirmed in sync with their KA1CM remote branches before preparing the requested commits. Consult Git history for the resulting commits and remote publication state. Do not bypass the sandbox or assume project creation fixes shell execution. Inspect both repositories before publishing, never force-push, and do not include secrets or diagnostic dumps.

Firmware commit `b708093690f0a708e47d155b2cc800334709df3e` was pushed to `KA1CM/MeshCore`, branch `meshcore-bot-working`, on 2026-10-29. The wrapper commit records that exact submodule revision together with the host tests and these project instructions. Publication checks covered whitespace and credential patterns; no firmware build, host-test compilation, flash, or device operation was performed for publication.

## Recent radio and channel behavior

- `#fairfield-county` is the ct-ffc channel; normal bot responses use the `#ct-ffc` scope.
- `path` remains a compact single-message route response. `path all` resolves the full route and uses a paced multipart queue.
- Unknown/ambiguous hashes have a trailing dot. Known names intentionally shortened to hashes do not. Special two-byte `0883` maps to `SUPER_SQUIRREL 🐿️` and retains its dot.
- Ordinary `path` now checks cached names at every hop; internet lookups remain limited to the first five hops. `path all` can request all hops.
- The observed ct-ffc list holds at most 256 two-byte hashes from the last 30 days. Three-byte observations are reduced to two bytes. It is separate from the 24-hour neighbor list.
- In Fairfield, plain `list` sends all current ct-ffc hashes. `list <name>` performs a case-insensitive substring match on known local/contact-cache names and replies with full matching names, one per line. Unknown or ambiguous names are not guessed. No internet lookup is triggered by this search.
- Matching-name snapshots prefer PSRAM, cover up to 256 names, and reuse the existing bounded multipart queue, numbered parts, five-second pacing, command cooldown, and ct-ffc channel policy. While the TLS worker owns the cache, a name search asks the user to retry rather than returning a misleading incomplete list.
- Other channels and DM retain their existing voltage-list behavior.
- Fairfield `help list` now says, in one message:

  ```text
  list: all ct-ffc repeaters hashes heard in 30 days.
  list <name>: matching repeater names.
  use path<hash> to resolve name.
  ```

## Latest unscoped-message and greeting changes

- Every unscoped text message received in Fairfield is handled before command parsing, while retaining bot-enabled and NTP-ready gates.
- A notice is allowed once per hour per sender display name; channel text does not expose an authenticated sender key. The bounded 64-entry RAM table does not evict live entries, and cooldowns reset on restart.
- The notice is itself sent unscoped. Scoped messages keep normal command handling.
- The notice now reuses `executeBotHelloCommand`, rather than the older 'unscoped message. please use ct-ffc...' text.
- Both Fairfield hello and the notice include a time-dependent greeting and the full sender name, followed by an explanation and `more info on http://tiny.cc/ct-ffc`.
- The formatter first drops the welcome clause, then uses a shorter explanation when necessary so the full name and complete URL fit the 127-byte channel response budget.
- Source length checks covered all greeting variants and sender lengths 0–31 bytes. These most recent changes were not built or flashed by the agent; the user performs those steps.

## TLS, name cache, and storage

- Resolved name-cache capacity is 128. Positive entries live 100 hours; negative/ambiguous entries have shorter retry lifetimes (15 minutes).
- Positive entries persist in alternating checksummed `/pathnames0.bin` and `/pathnames1.bin` snapshots and retain their original UTC expiry across reboot.
- Admin `save` saves command activity, ct-ffc observations, and the name cache. If name-cache save is deferred for an active lookup, a later admin message reports completion.
- Cache count is displayed in the path lookup diagnostics heading.
- Dashboard ct-ffc background name lookups operate only while requested by the open card, in limited batches (up to five hashes, no more often than once per minute). Resolved cached names avoid repeated TLS work.
- Prior failures included internal-memory TLS allocation pressure and a TLS worker watchdog failure. Bulk response/cache buffers prefer PSRAM. The persistent 12KB static worker runs on the Arduino app core at idle priority plus one. Inspect current code before changing allocation hooks or scheduling.
- Occasional TLS failures are acceptable if later lookups recover and the bot remains responsive. Do not claim a clean bill of health without observation.
- Repeater-monitor history writes use PSRAM-backed JSON and serialization buffers with staged error diagnostics, verification before committing the active snapshot slot, and bounded retries after 30/60/120 seconds.
- Voltage polling uses StoreStart/StoreFinish/StoreLogin phases so failed persistence cannot cause endless radio request loops. Storage failures pause polling, notify admins, and attempt recovery; new TLS lookups are coordinated with saves.

## Startup, time, and device diagnostics

- NTP confirmation gates user-command responses and adverts. A phone-set RTC alone is insufficient.
- The first advert is shortly after successful NTP synchronization. Startup admin notification follows the first confirmed advert transmission.
- If NTP remains unconfirmed after five minutes, admins receive the startup/NTP-failed/retrying notice.
- Automatic repeater clock verification is scheduled after 03:30 Eastern for offsets of at least ten minutes or no acceptable verification for 30 days.
- Neighbor dashboard and radio lists include only neighbors heard within 24 hours.
- Existing restart history is persisted; it is not a substitute for a backtrace.
- Fairfield has used COM15 in application mode and COM14 in DFU. Always verify current port identity before any USB operation.
- Previously authorized crash-dump reads are completed actions, not continuing authorization to reset the bot.

## Important preserved diagnostic artifacts

Under the original chat workspace:

- `work/crash-2026-10-25/`: malformed PATH handling stack overflow evidence and preserved matching artifacts.
- `work/crash-2026-10-26/`: TLS watchdog evidence and preserved matching artifacts.
- `work/fairfield-check-observation-2026-10-28.jsonl`: monitor state observations.
- `work/fairfield-radio-observation-2026-10-28.jsonl`: read-only radio observations.
- `outputs/fairfield-storage-failure-2026-10-28.json`: device state at storage failure.
- `outputs/fairfield-repeater-list-backup-2026-10-28.json`: repeater configuration export.

The original conversation contains more context than this summary. Use app thread-reading tools when older decisions matter; do not publish private device observations or credentials to recover context.
