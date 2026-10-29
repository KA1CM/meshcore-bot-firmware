"""Host-only Stage 1 cooldown regression tests; no firmware build required."""
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "vendor/MeshCore/examples/companion_radio"
CODE = r"""
#include "FirmwareBot.h"
#include "BotCommandRegistry.h"
#include <cassert>
#include <cstring>
#include <cstdio>
#include <initializer_list>

int main() {
  const BotCommandId exempt[] = {
    BOT_COMMAND_PING, BOT_COMMAND_TEST, BOT_COMMAND_SIG, BOT_COMMAND_HELP,
    BOT_COMMAND_CMD, BOT_COMMAND_HELLO, BOT_COMMAND_ABOUT, BOT_COMMAND_STATUS,
    BOT_COMMAND_CHANNELS, BOT_COMMAND_VERSION, BOT_COMMAND_TIME,
    BOT_COMMAND_LORA, BOT_COMMAND_ID, BOT_COMMAND_AIR
  };
  const BotCommandId throttled[] = {
    BOT_COMMAND_PATH, BOT_COMMAND_STATS, BOT_COMMAND_USER, BOT_COMMAND_LIST,
    BOT_COMMAND_NEIGHBORS, BOT_COMMAND_ADVERT, BOT_COMMAND_CHECK,
    BOT_COMMAND_SYNC, BOT_COMMAND_ADD, BOT_COMMAND_REMOVE, BOT_COMMAND_ENABLE,
    BOT_COMMAND_DISABLE, BOT_COMMAND_NOTES, BOT_COMMAND_PASSWORD,
    BOT_COMMAND_UNKNOWN, BOT_COMMAND_UNSUPPORTED
  };
  static_assert(BOT_COMMAND_COOLDOWN_MILLIS == 5000UL, "Keep 5-second cooldown");
  for (auto id : exempt) {
    // Even a previously populated slot cannot suppress an exempt command.
    BotCommandCooldown slots[2] = {{id, 6000}, {BOT_COMMAND_PATH, 9000}};
    BotCommandCooldown before[2];
    memcpy(before, slots, sizeof(slots));
    assert(!FirmwareBot::isCommandOnCooldown(slots, 2, id, 1000));
    for (unsigned burst = 0; burst < 4; ++burst) {
      FirmwareBot::recordCommandCooldown(slots, 2, id, 1000 + burst, 5000);
      assert(!FirmwareBot::isCommandOnCooldown(slots, 2, id, 1001 + burst));
      assert(memcmp(before, slots, sizeof(slots)) == 0);
    }
    // With all slots occupied, an exempt response must not evict Path/Stats.
    slots[0] = {BOT_COMMAND_STATS, 7000};
    memcpy(before, slots, sizeof(slots));
    FirmwareBot::recordCommandCooldown(slots, 2, id, 1000, 5000);
    assert(memcmp(before, slots, sizeof(slots)) == 0);
  }
  for (auto id : throttled) {
    BotCommandCooldown slots[2] = {};
    assert(!FirmwareBot::isCommandOnCooldown(slots, 2, id, 1000));
    FirmwareBot::recordCommandCooldown(slots, 2, id, 1000, 5000);
    assert(FirmwareBot::isCommandOnCooldown(slots, 2, id, 5999));
    assert(!FirmwareBot::isCommandOnCooldown(slots, 2, id, 6000));
    slots[0] = {}; slots[1] = {};
    FirmwareBot::recordCommandCooldown(slots, 2, id, 0xFFFFFFF0UL, 32);
    assert(FirmwareBot::isCommandOnCooldown(slots, 2, id, 0xFFFFFFF8UL));
    assert(FirmwareBot::isCommandOnCooldown(slots, 2, id, 0x0000000FUL));
    assert(!FirmwareBot::isCommandOnCooldown(slots, 2, id, 0x00000010UL));
  }
  BotCommandCooldown slots[2] = {};
  for (auto id : exempt) {
    FirmwareBot::recordCommandCooldown(slots, 2, id, 1000, 5000);
    assert(slots[0].command_id == BOT_COMMAND_NONE);
    assert(slots[1].command_id == BOT_COMMAND_NONE);
  }
  FirmwareBot::recordCommandCooldown(slots, 2, BOT_COMMAND_PATH, 1000, 5000);
  assert(!FirmwareBot::isCommandOnCooldown(slots, 2, BOT_COMMAND_STATS, 2000));
  auto before = slots[0];
  FirmwareBot::recordCommandCooldown(slots, 2, BOT_COMMAND_NONE, 2000, 5000);
  FirmwareBot::recordCommandCooldown(slots, 2, BOT_COMMAND_PATH, 2000, 0);
  assert(slots[0].command_id == before.command_id);
  assert(slots[0].expires_at_millis == before.expires_at_millis);
  assert(!FirmwareBot::isCommandOnCooldown(nullptr, 0, BOT_COMMAND_PATH, 1000));
  FirmwareBot::recordCommandCooldown(nullptr, 0, BOT_COMMAND_PATH, 1000, 5000);
  // Exercise the actual parser for prefixed, prefixless and mixed-case input.
  for (const char* text : {"ping", "!TeSt", "/SNR", "help path"}) {
    BotCommand command = {};
    assert(FirmwareBot::parseCommand(text, strlen(text), &command, true));
    assert(!FirmwareBot::isCommandOnCooldown(slots, 2, command.id, 1001));
  }
  puts("PASS Stage 1: 14 exemptions, 16 retained cooldowns, bursts, slot preservation, expiry and rollover");
}
"""

with tempfile.TemporaryDirectory() as folder:
    source = Path(folder) / "test.cpp"
    binary = Path(folder) / "test.exe"
    source.write_text(CODE)
    subprocess.run([
        os.environ.get("CXX", "g++"), "-std=c++17", "-Wall", "-Wextra", "-Werror",
        # Existing FirmwareBot.cpp contains unused hashing helpers.
        "-Wno-unused-function", "-I", str(SRC), str(source),
        str(SRC / "FirmwareBot.cpp"), str(SRC / "BotCommandRegistry.cpp"),
        "-o", str(binary)
    ], check=True)
    subprocess.run([str(binary)], check=True)
