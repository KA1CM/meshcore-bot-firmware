"""Host regression for the real restart-history class, with mocked hardware/storage."""
from pathlib import Path
import os, subprocess, tempfile
src=Path(__file__).resolve().parents[2]/'vendor/MeshCore/examples/companion_radio'
source=(src/'MonitorRestartHistory.h').read_text(encoding='utf-8')
actual=source[source.index('class MonitorRestartHistory'):]
code=r'''
#include <cstdint>
#include <cstddef>
#include <cstring>
#include <cassert>
#include <vector>
uint32_t ticks=5000;uint32_t millis(){return ticks;}
enum esp_reset_reason_t {ESP_RST_UNKNOWN,ESP_RST_POWERON,ESP_RST_EXT,ESP_RST_SW,ESP_RST_PANIC,ESP_RST_INT_WDT,ESP_RST_TASK_WDT,ESP_RST_WDT,ESP_RST_DEEPSLEEP,ESP_RST_BROWNOUT,ESP_RST_SDIO};
esp_reset_reason_t reason=ESP_RST_POWERON;
esp_reset_reason_t esp_reset_reason(){return reason;}
struct Esp {uint32_t getFreeHeap(){return 70000;}uint32_t getMaxAllocHeap(){return 60000;}}ESP;
std::vector<uint8_t> persisted;unsigned writes=0;bool fail=false;
struct BotSnapshotFile {
 enum Load {Missing,Loaded,Invalid,Unavailable};
 BotSnapshotFile(const char*,const char*){}
 Load load(void* dest,size_t size){if(persisted.empty())return Missing;assert(size==persisted.size());memcpy(dest,persisted.data(),size);return Loaded;}
 bool save(const void* source,size_t size){++writes;if(fail)return false;auto bytes=(const uint8_t*)source;persisted.assign(bytes,bytes+size);return true;}
 const char* lastError(){return "write failed";}
};
'''+actual+r'''
int main(){
 MonitorRestartHistory first;first.begin();assert(first.records().count==1&&writes==1);
 assert(first.records().entries[0].reason==ESP_RST_POWERON);
 first.begin();assert(first.records().count==1&&writes==1);
 first.poll(1792623882,false);assert(first.records().entries[0].bootUtc==0&&writes==1);
 first.poll(1792623882,true);assert(first.records().entries[0].bootUtc==1792623877&&writes==2);
 first.poll(1792623892,true);assert(writes==2);
 reason=ESP_RST_PANIC;MonitorRestartHistory second;second.begin();assert(second.records().count==2);
 assert(second.records().entries[0].reason==ESP_RST_PANIC&&second.records().entries[1].bootUtc==1792623877);
 for(int i=0;i<20;++i){MonitorRestartHistory restart;restart.begin();assert(restart.records().count<=16);}
 MonitorRestartHistory latest;latest.begin();assert(latest.records().count==16);
 fail=true;MonitorRestartHistory error;error.begin();assert(error.records().count==16&&error.lastError()[0]);
 unsigned before=writes;error.poll(0,false);assert(writes==before);
 ticks+=60000;fail=false;error.poll(0,false);assert(writes==before+1&&!error.lastError()[0]);
 assert(!strcmp(MonitorRestartHistory::reasonName(ESP_RST_BROWNOUT),"Brownout"));
}
'''
with tempfile.TemporaryDirectory() as tmp:
    folder=Path(tmp);cpp=folder/'restart.cpp';exe=folder/'restart.exe';cpp.write_text(code)
    subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('PASS: reset reasons, NTP boot timestamps, persisted history, 16-entry limit and bounded write retries')
