"""Host checks for the actual automatic clock scheduler; no hardware needed."""
from pathlib import Path
import os, subprocess, tempfile
src=Path(__file__).resolve().parents[2]/'vendor/MeshCore/examples/companion_radio'
source=(src/'RepeaterMonitor.cpp').read_text(encoding='utf-8')
method=source[source.index('void RepeaterMonitor::pollAutomaticClockSync()'):source.index('bool RepeaterMonitor::startClockSync(')]
code=r'''
#include <cstdint>
#include <cstddef>
#include <cassert>
#include <vector>
uint32_t ticks=1000;uint32_t millis(){return ticks;}
bool elapsed(uint32_t now,uint32_t due){return (int32_t)(now-due)>=0;}
constexpr uint32_t VALID_TIME=1700000000;
uint32_t easternDay(uint32_t utc){return (utc-4*3600UL)/86400;}
namespace FirmwareBot {int32_t easternUtcOffsetSeconds(uint32_t){return -4*3600;}}
struct Entry {uint8_t key[32]{};uint32_t syncAttemptAt=0;bool due=true;};
bool timeSyncDue(const Entry& entry,uint32_t){return entry.due;}
struct RepeaterMonitor {
 bool fresh=true,storageOK=true,occupied=false,adminCheckPending=false;
 uint32_t utc=20000UL*86400+4*3600+3*3600+29*60+59,nextAutomaticSyncPoll=0;
 Entry entries[3];size_t count=3;std::vector<int> started;
 struct Credentials {bool ready=true;bool available(){return ready;}const char* password(const uint8_t*){return "saved";}}credentials;
 struct Mesh {void* lookupContactByPubKey(const uint8_t*,int){return this;}}mesh;
 bool syncTimeReady(){return fresh;}bool busy(){return occupied;}uint32_t now(){return utc;}
 bool startClockSync(int i){started.push_back(i);entries[i].syncAttemptAt=utc;occupied=true;return true;}
 void pollAutomaticClockSync();
};
'''+method+r'''
int main(){
 RepeaterMonitor m;m.entries[1].due=false;
 m.pollAutomaticClockSync();assert(m.started.empty());
 ++m.utc;m.fresh=false;m.pollAutomaticClockSync();assert(m.started.empty());
 m.fresh=true;m.occupied=true;m.pollAutomaticClockSync();assert(m.started.empty());
 m.occupied=false;m.adminCheckPending=true;m.pollAutomaticClockSync();assert(m.started.empty());
 m.adminCheckPending=false;m.pollAutomaticClockSync();assert(m.started==std::vector<int>{0});
 m.occupied=false;ticks+=10001;m.pollAutomaticClockSync();assert(m.started==std::vector<int>({0,2}));
 m.occupied=false;ticks+=10001;m.pollAutomaticClockSync();assert(m.started.size()==2);
 // A restart retains persisted attempt dates and cannot repeat today's jobs.
 RepeaterMonitor reboot;reboot.utc=m.utc;reboot.entries[1].due=false;
 reboot.entries[0].syncAttemptAt=m.utc;reboot.entries[2].syncAttemptAt=m.utc;
 reboot.pollAutomaticClockSync();assert(reboot.started.empty());
 reboot.utc+=86400;ticks+=10001;reboot.pollAutomaticClockSync();assert(reboot.started==std::vector<int>{0});
 // Late startup catches up after 03:30 rather than waiting another day.
 RepeaterMonitor late;late.utc+=3600;late.pollAutomaticClockSync();assert(late.started.size()==1);
}
'''
with tempfile.TemporaryDirectory() as tmp:
    folder=Path(tmp);cpp=folder/'schedule.cpp';exe=folder/'schedule.exe';cpp.write_text(code)
    subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('PASS: Eastern 03:30 start, NTP/busy gates, serial scheduling, same-day reboot protection and late-start catch-up')
