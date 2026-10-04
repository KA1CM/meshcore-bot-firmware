from pathlib import Path
import os, subprocess, tempfile
root=Path(__file__).resolve().parents[2];src=root/'vendor/MeshCore/examples/companion_radio'
existing=Path(__file__).with_name('test_monitor_credentials.py').read_text(encoding='utf-8')
mock=existing.split('mock = r"""',1)[1].split('"""',1)[0]
code=r"""
#include "MonitorBotStatsHistory.h"
#include "BotStatsWindow.h"
#include <cassert>
int main(){
 BotStatsHistory h;assert(!h.accepted(BOT_COMMAND_TEST,0));assert(!h.at(20000));
 assert(h.observe(20000));assert(h.accepted(BOT_COMMAND_TEST,20000));
 for(auto id:{BOT_COMMAND_ADD,BOT_COMMAND_REMOVE,BOT_COMMAND_ENABLE,BOT_COMMAND_DISABLE,BOT_COMMAND_CHECK,BOT_COMMAND_SYNC,BOT_COMMAND_ADVERT,BOT_COMMAND_NOTES,BOT_COMMAND_PASSWORD})assert(h.accepted(id,20000));
 assert(h.at(20000)->counts[BOT_COMMAND_ADVERT]==9);assert(h.at(20000)->counts[BOT_COMMAND_TEST]==1);
 assert(h.observe(20001));assert(h.accepted(BOT_COMMAND_PATH,20001));
 assert(h.at(20000)&&h.at(20001));assert(h.observe(20029));assert(h.at(20000));
 assert(h.observe(20030));assert(!h.at(20000));assert(h.at(20001));
 assert(!h.accepted(BOT_COMMAND_TEST,20000));assert(!h.observe(20000));
 assert(h.accepted(BOT_COMMAND_TEST,20001));assert(h.store().latestDay==20030);
 BotStatsHistory restored;assert(restored.restore(h.store()));assert(restored.at(20001)->counts[BOT_COMMAND_PATH]==1);
 auto invalid=h.store();invalid.version=2;assert(!restored.restore(invalid));invalid=h.store();invalid.days[0].day=1;assert(!restored.restore(invalid));
 assert(h.observe(20100));assert(!h.at(20001));assert(!h.at(20030));
 MonitorBotStatsHistory saved;saved.accepted(BOT_COMMAND_TEST,20000,0);assert(saved.available());
 saved.poll(3599999);assert(Preferences::bytes.empty());saved.poll(3600000);assert(!Preferences::bytes.empty());
 MonitorBotStatsHistory restart;restart.begin(0);assert(restart.counters().at(20000)->counts[BOT_COMMAND_TEST]==1);
 saved.accepted(BOT_COMMAND_TEST,20000,3600001);Preferences::fail=true;saved.poll(7200000);
 MonitorBotStatsHistory failed;failed.begin(0);assert(failed.counters().at(20000)->counts[BOT_COMMAND_TEST]==1);
 Preferences::fail=false;saved.poll(10800000);MonitorBotStatsHistory retry;retry.begin(0);assert(retry.counters().at(20000)->counts[BOT_COMMAND_TEST]==2);
 Preferences::bytes[0]=2;MonitorBotStatsHistory corrupt;corrupt.begin(0);assert(!corrupt.available());
 BotStatsWindow rolling;rolling.accepted(BOT_COMMAND_PATH,0);uint64_t values[BotStatsHistory::COMMANDS]{};rolling.totals(0,values);assert(values[BOT_COMMAND_PATH]==1);rolling.totals(86400000,values);assert(values[BOT_COMMAND_PATH]==0);
 static_assert(sizeof(BotStatsHistory)<5000,"Bounded 30-day RAM");
}
"""
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'Preferences.h').write_text(mock,encoding='utf-8');(p/'test.cpp').write_text(code,encoding='utf-8');exe=p/'test.exe'
 subprocess.run([os.environ.get('CXX','c++'),'-std=c++11','-Wall','-Wextra','-Werror','-Wno-unused-function','-I',str(p),'-I',str(src),str(p/'test.cpp'),str(src/'BotCommandRegistry.cpp'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: 30-day retention, day rollover, admin grouping, persistence/reload, failed writes/retry, corrupt storage and rolling totals')
