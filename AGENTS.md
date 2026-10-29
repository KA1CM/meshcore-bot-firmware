# Fairfield Bot working instructions

## Repository and device

- This is the KA1CM MeshCore bot wrapper repository. Firmware lives in the Git submodule `vendor/MeshCore`; respect both repositories and their separate commits/remotes.
- Primary device: Fairfield Bot. Dashboard: `http://192.168.0.103` or `http://mesh-bot.local`.
- Companion USB target: `heltec_v4_companion_radio_usb`.
- Stamford is a separate bot; do not confuse its state with Fairfield.

## User preferences and authorization

- The user builds and flashes manually. Do not build firmware or flash, erase, reset, or operate a connected device unless the user explicitly authorizes that action.
- Commit and push only with explicit user authorization. Existing authorization in the current conversation counts; do not repeatedly ask for the same approval.
- Preserve unrelated uncommitted changes. Inspect changes and both Git remotes before publishing; do not blindly stage diagnostics, credentials, or build artifacts.
- Never store dashboard passwords or other credentials in source, project instructions, handoffs, or commits.
- Prefer small maintainable changes, nonblocking work, paced radio queues, and limited internal RAM use. Use PSRAM for appropriate bulk buffers.
- When compilation is not authorized, clearly label source checks as source checks; do not claim build or device validation.

## Continuity

- Read `FAIRFIELD_BOT_HANDOFF.md` before resuming work in a new chat.
- Original Codex chat: `Mesh-Bot`, ID `01a13534-f36c-7901-b0ff-8e3304345c0a`.
- Earlier referenced ChatGPT conversation: `MeshCore Bot Setup`, ID `6aafc882-6c38-83ea-9a35-668ff338b6fc`.
- Keep the original chat for its actual conversation history. The handoff is a summary, not a complete transcript or a substitute for inspecting current source and Git state.
