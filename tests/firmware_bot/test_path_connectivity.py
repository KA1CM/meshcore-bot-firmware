from pathlib import Path
import os,subprocess,tempfile
root=Path(__file__).resolve().parents[2];src=root/'vendor/MeshCore/examples/companion_radio'
s=(src/'BotPathLookup.cpp').read_text(encoding='utf-8')
a=s.index('struct Cached {');b=s.index('  // No radio, contact, or dashboard state',a)
prefix=s[a:b]+'}\n'
a=s.index('void setInternetAvailable(');b=s.index('uint32_t successSequence()',a);setter=s[a:b]
code=r'''#include <string>
#include <cstring>
#include <cstdio>
#include <cstdint>
#include <cassert>
#include <ctime>
#define BOT_MAX_PATH_BYTES 8
#define WL_CONNECTED 3
#define pdMS_TO_TICKS(x) (x)
using QueueHandle_t=void*;
uint32_t ticks=100;uint32_t millis(){return ticks;}
int statusMux=0;void portENTER_CRITICAL(int*){}void portEXIT_CRITICAL(int*){}
struct String:std::string{using std::string::operator+=;};
namespace BotPath{struct Route{size_t count=1;char names[8][33]{};bool ambiguous[8]{};};
 void hash(const Route&,size_t,char* out){strcpy(out,"1234");}}
size_t lookupHopCount(const BotPath::Route& r){return r.count<5?r.count:5;}
std::string stage;void report(const char* s,int=0,bool=false){stage=s;}
struct Wifi{int status(){return WL_CONNECTED;}}WiFi;
unsigned waits=0;void vTaskDelay(int n){++waits;ticks+=n;}
'''+prefix+setter+r'''
int main(){
 BotPath::Route r;
 setInternetAvailable(false);throttled=true;nextFetch=ticks+60000;
 resolve(&r);assert(stage=="Internet unavailable; using local/cached names" && waits==0 && !r.names[0][0]);
 strcpy(cache[0].prefix,"1234");strcpy(cache[0].name,"Cached repeater");cache[0].expires=ticks+60000;
 resolve(&r);assert(stage=="Using cached names" && !strcmp(r.names[0],"Cached repeater"));
 // Expired cache misses fall back without waiting or refreshing the network cache.
 r.names[0][0]=0;cache[0].expires=ticks;
 resolve(&r);assert(stage=="Internet unavailable; using local/cached names" && waits==0);
 setInternetAvailable(true);stage.clear();resolve(&r);
 assert(stage.empty() && !throttled && nextFetch==0 && workerRecovery==1);
 setInternetAvailable(true);assert(internetPolicy.recovery==1);
 setInternetAvailable(false);setInternetAvailable(true);assert(internetPolicy.recovery==2);
}
'''
with tempfile.TemporaryDirectory() as folder:
 d=Path(folder);(d/'test.cpp').write_text(code);exe=d/'test.exe'
 subprocess.run([os.environ.get('CXX','g++'),'-std=c++11','-I',str(src),str(d/'test.cpp'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS offline path fallback, cache use/expiry, no backoff wait, and recovery bypass of old failure delay')
