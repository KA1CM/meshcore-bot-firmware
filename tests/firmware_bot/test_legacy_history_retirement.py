"""Host regression: filesystem history ignores legacy NVS without deleting it."""
from pathlib import Path
import os, subprocess, tempfile
src=Path(__file__).resolve().parents[2]/'vendor/MeshCore/examples/companion_radio'
source=(src/'MonitorBotStatsHistory.h').read_text(encoding='utf-8')
actual=source[source.index('class MonitorBotStatsHistory'):]
code=r'''
#include <cstdint>
#include <cstddef>
#include <cstring>
#include <memory>
#include <cassert>
using BotCommandId=int;
bool legacyPresent=true,cleanupFails=false;unsigned removals=0,writes=0;
class Preferences {
public:
 bool begin(const char* name,bool){assert(!strcmp(name,"bot-stats"));return true;}
 bool isKey(const char* key){assert(!strcmp(key,"daily"));return legacyPresent;}
 void end(){}
 bool remove(const char* key){assert(!strcmp(key,"daily"));++removals;if(cleanupFails)return false;legacyPresent=false;return true;}
};
class BotStatsHistory {
public:
 struct Store {uint32_t latestDay=0;};Store data;
 const Store& store()const{return data;}
 bool restore(const Store& saved){data=saved;return true;}
 bool observe(uint32_t day){const bool changed=data.latestDay!=day;data.latestDay=day;return changed;}
 bool accepted(int,uint32_t day){return observe(day);}
};
class BotSnapshotFile {
public:
 enum Load {Missing,Loaded,Invalid,Unavailable};static Load mode;
 BotSnapshotFile(const char* a,const char* b){assert(!strcmp(a,"/botstats0.bin")&&!strcmp(b,"/botstats1.bin"));}
 Load load(void* dest,size_t){if(mode==Loaded)static_cast<BotStatsHistory::Store*>(dest)->latestDay=20000;return mode;}
 bool save(const void*,size_t){++writes;return true;}
 const char* lastError(){return "snapshot invalid";}
};
BotSnapshotFile::Load BotSnapshotFile::mode=BotSnapshotFile::Missing;
'''+actual+r'''
int main(){
 MonitorBotStatsHistory fresh;fresh.begin(1);
 assert(fresh.available()&&legacyPresent&&removals==0);
 assert(fresh.saveNow(2,20000)&&writes==1);
 // Unusable legacy cleanup/storage has no effect on filesystem saves.
 legacyPresent=true;cleanupFails=true;MonitorBotStatsHistory cleanup;
 cleanup.begin(1);assert(cleanup.available());assert(cleanup.saveNow(2,20000)&&writes==2);assert(removals==0);
 // Existing new-format snapshots still restore and are never reset.
 BotSnapshotFile::mode=BotSnapshotFile::Loaded;MonitorBotStatsHistory restored;
 restored.begin(1);assert(restored.available()&&restored.counters().store().latestDay==20000);
 assert(restored.saveNow(2,20000)&&writes==3);
 // Invalid new snapshots remain protected; retiring legacy is not a full reset.
 BotSnapshotFile::mode=BotSnapshotFile::Invalid;MonitorBotStatsHistory invalid;
 invalid.begin(1);assert(!invalid.available()&&!invalid.saveNow(2,20000));assert(writes==3);
}
'''
with tempfile.TemporaryDirectory() as tmp:
    folder=Path(tmp);cpp=folder/'retire.cpp';exe=folder/'retire.exe';cpp.write_text(code)
    subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('PASS: legacy data untouched, fresh filesystem saves and existing history preserved')
