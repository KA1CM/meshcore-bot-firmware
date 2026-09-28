#include "BotCommands.h"
#include "BotCommandRegistry.h"
#include "FirmwareBot.h"
#include <cassert>
#include <cstring>
int32_t FirmwareBot::easternUtcOffsetSeconds(uint32_t) { return -14400; }
int main() {
  const auto* meta = BotCommandRegistry::findByName("snr", 3);
  assert(meta && meta->id == BOT_COMMAND_SIG);
  assert(BotCommandRegistry::findByName("SNR", 3) == meta);
  assert(BotCommandRegistry::findByName("sig", 3) == nullptr);
  assert(strcmp(meta->usage, "snr") == 0);
  BotCommand help = {}; help.id = BOT_COMMAND_HELP;
  BotCommandContext help_ctx = {};
  char help_out[145];
  BotCommands::executeCommand(help, help_ctx, help_out, sizeof(help_out));
  assert(strstr(help_out, "  snr  ") && !strstr(help_out, "  sig  "));
  help.id = BOT_COMMAND_CMD;
  BotCommands::executeCommand(help, help_ctx, help_out, sizeof(help_out));
  assert(strstr(help_out, "  snr  ") && !strstr(help_out, "  sig  "));
  help.id = BOT_COMMAND_HELP; strcpy(help.args, "snr"); help.args_len = 3;
  BotCommands::executeCommand(help, help_ctx, help_out, sizeof(help_out));
  assert(strcmp(help_out, "Signal Report: hops count, last repeater, SNR, RSSI and noise floor. Usage: snr") == 0);
  BotCommand cmd = {}; cmd.id = BOT_COMMAND_SIG;
  BotCommandContext ctx = {}; ctx.path_hash_count = 4;
  ctx.path_snr_quarters = 19; ctx.last_rssi = -100; ctx.noise_floor = -112;
  strcpy(ctx.response_target, "user");
  char out[145];
  ctx.last_repeater_name = "Chestnut Hill - FN31jf";
  auto r = BotCommands::executeCommand(cmd, ctx, out, sizeof(out));
  assert(r.code == BOT_COMMAND_RESULT_OK);
  assert(strcmp(out, "@[user]\n4 hops\nLast hop from Chestnut Hill - FN31jf SNR 4.75 | RSSI -100 dBm | noise -112 dBm") == 0);
  ctx.last_repeater_name = "[1234]";
  BotCommands::executeCommand(cmd, ctx, out, sizeof(out));
  assert(strstr(out, "Last hop from [1234] SNR 4.75"));
  ctx.response_target[0] = 0;
  BotCommands::executeCommand(cmd, ctx, out, sizeof(out));
  assert(strncmp(out, "4 hops\nLast hop from [1234]", 26) == 0);
  ctx.path_hash_count = 0;
  BotCommands::executeCommand(cmd, ctx, out, sizeof(out));
  assert(strncmp(out, "Direct\nSNR", 10) == 0);
  ctx.path_hash_count = 1; ctx.last_repeater_name = nullptr;
  BotCommands::executeCommand(cmd, ctx, out, sizeof(out));
  assert(strstr(out, "1 hop\nLast hop SNR"));
  char tiny[8]; r = BotCommands::executeCommand(cmd, ctx, tiny, sizeof(tiny));
  assert(r.code == BOT_COMMAND_RESULT_TRUNCATED && tiny[7] == 0);
}
