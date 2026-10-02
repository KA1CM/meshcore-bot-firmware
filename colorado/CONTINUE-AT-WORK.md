# Continue at work — October 2, 2026

Home firmware was built for `heltec_v4_companion_radio_usb`, flashed successfully,
and verified on the bot. All 15 repeater notes were saved and read back live.
`repeater-notes.json` contains the public-key mappings and latest notes, including
CoreBell/PeakMesh/FlexSolar headings, Sleeve Dipole names, and blank missing fields.
Notes live on the device; they are not automatically seeded by a firmware build.

## Get the checkpoint

First inspect both repositories for local changes. Preserve any work-laptop changes
before updating. Fetch KA1CM in both repositories. Fast-forward the parent `main`
and vendor `meshcore-bot-working` branches only when clean and not diverged.
The parent submodule pointer pins the matching vendor commit. Do not reset or clean
local work, and do not reapply the historical patch queue.

## Current behavior

- Dashboard notes: admin edits, guest reads, 512 Unicode characters, import/export.
- Admin contacts are separate permissions tied to full public keys and protected as
  favorites. Admin DM commands: help, advert, check <repeater>, sync <repeater>.
- Advert completion is confirmed after transmission; dashboard shows last advert.
- Sunrise low-voltage DM report goes to enabled admin notification recipients.
- Voltage checking: existing route/session, then up to three pre-login flood status
  attempts, two flood login attempts, a three-second pause after success, and up to
  four post-login flood status attempts. Login replies record available clock offsets.
- Time sync starts with fresh admin login; all sync traffic uses flood. Ahead clocks
  over 180 seconds may trigger up to three reboot cycles. Clock sync gets one initial
  attempt plus three retries without confirmation. Recent small offsets defer sunrise sync.
- list/list low omit disabled repeaters. neighbors all paginates. Neighbors sort by
  sample count then SNR. Dashboard sections collapse; Digest challenge reuse fixes
  repeated Safari login prompts.

## Local configuration and workflow

Wi-Fi and dashboard/repeater secrets remain in ignored local configuration and
`vendor/MeshCore/out/monitor-secrets.h`; transfer privately if needed. Never commit them.
Device passwords, admin permissions, notes, and history persist on the existing bot.
Do not build until requested. When asked, regenerate the embedded page with
`python scripts/build-monitor-page.py`, then build the USB companion environment.
Flash only `firmware.bin` at offset `0x10000`; preserve filesystem and settings.
After DFU flashing, tell the user to press RESET.

Latest verified build: work/build-repeater-notes.log on the home machine, 46 seconds.
Application image: 1,284,976 bytes. Notes and guest/API tests passed before flashing.
