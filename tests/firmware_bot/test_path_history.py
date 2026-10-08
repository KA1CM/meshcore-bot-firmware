from pathlib import Path
import os,subprocess,tempfile
root=Path(__file__).resolve().parents[2];src=root/'vendor/MeshCore/examples/companion_radio'
s=(src/'BotPathLookup.cpp').read_text()
impl=s[s.index('Status lastStatus;'):s.index('// Resolve in the worker')]
read=s[s.index('void recordEvent('):s.index('bool start(')]
code=r'''
#define ESP32 1
#define BOT_REPEATER_MONITOR 1
#include "BotPathLookup.h"
#include <cassert>
#include <ctime>
#include <cstdio>
#define portENTER_CRITICAL(x) ((void)0)
#define portEXIT_CRITICAL(x) ((void)0)
uint32_t ticks=0;uint32_t millis(){return ticks;}
struct {uint32_t heap=10000,block=8000;uint32_t getFreeHeap(){return heap;}uint32_t getMaxAllocHeap(){return block;}}ESP;
void mbedtls_x509_crt_verify_info(char* p,size_t n,const char*,uint32_t){snprintf(p,n,"test");}
namespace BotPathLookup {
'''+impl+read+r'''
}
int main(){using namespace BotPathLookup;HistoryEntry e;assert(!history(0,e));
 beginHistory("Alice","DM");ticks=10;ESP.heap=5000;ESP.block=2000;report("TLS failed",-1,true);ticks=20;finishHistory();
 assert(history(0,e)&&!strcmp(e.channel,"DM")&&!strcmp(e.requester,"Alice")&&e.finished&&e.elapsedMs==20&&e.minHeap==5000&&e.minBlock==2000&&!strcmp(e.failure,"TLS failed"));
 for(int i=0;i<35;++i){char user[33];snprintf(user,sizeof(user),"User%d",i);beginHistory(user);report("Using cached names");finishHistory();}
 assert(history(0,e)&&!strcmp(e.requester,"User34")&&!e.failure[0]);assert(history(29,e)&&!strcmp(e.requester,"User5"));assert(!history(30,e));
 BotPath::Route route;route.count=9;assert(lookupHopCount(route)==5);route.count=3;assert(lookupHopCount(route)==3);
 beginHistory("Worker");recordEvent("Ignored user","Ignored: path cooldown","Bot channel");report("Names resolved",2);finishHistory();
 assert(history(0,e)&&!strcmp(e.channel,"Bot channel")&&!strcmp(e.requester,"Ignored user")&&!strcmp(e.stage,"Ignored: path cooldown"));
 assert(history(1,e)&&!strcmp(e.requester,"Worker")&&!strcmp(e.stage,"Names resolved")&&e.finished);
 beginHistory("Evicted worker");for(int i=0;i<30;++i)recordEvent("New user","Queue full: local-only fallback");
 report("Late result");finishHistory();assert(history(29,e)&&!strcmp(e.stage,"Queue full: local-only fallback"));
 beginHistory("Bob");report("Connecting");assert(history(0,e)&&!e.finished);finishHistory();
}
'''
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'test.cpp').write_text(code);exe=p/'test.exe'
 subprocess.run([os.environ.get('CXX','c++'),'-std=c++11','-Wall','-Wextra','-Werror','-I',str(src),str(p/'test.cpp'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: lookup history names, ring eviction, timings, sampled memory minima, failure reset and active status')
