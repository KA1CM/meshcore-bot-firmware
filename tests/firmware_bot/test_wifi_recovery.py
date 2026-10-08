from pathlib import Path
import os,subprocess,tempfile
root=Path(__file__).resolve().parents[2];src=root/'vendor/MeshCore/examples/companion_radio'
s=(src/'RepeaterMonitor.cpp').read_text(encoding='utf-8');a=s.index('  bool connected = WiFi.status()',s.index('void RepeaterMonitor::loop()'));b=s.index('  wasConnected = connected;',a)+len('  wasConnected = connected;');logic=s[a:b]
code=r'''
#include <cstdint>
#include <cstddef>
#include <cassert>
uint32_t ticks=0;uint32_t millis(){return ticks;}
#define WL_CONNECTED 3
struct {int state=0;int status(){return state;}}WiFi;
struct {bool begin(const char*){return true;}void addService(const char*,const char*,int){}void end(){}}MDNS;
void configTime(int,int,const char*,const char*){}
struct Monitor{
 bool wasConnected=false,wifiEverConnected=false,mdnsStarted=false;
 uint32_t wifiReconnects=0,wifiDisconnects=0,wifiLastConnect=0,wifiLastDisconnect=0,wifiWindowStart=0,wifiAttempt=0;
 size_t wifiIndex=0;static const size_t wifiNetworkCount=2;int attempts=0;
 struct {int starts=0,stops=0;void begin(){++starts;}void stop(){++stops;}}server;
 void connectWifi(size_t index){++attempts;wifiIndex=index;wifiAttempt=millis();}
 void loop(){
'''+logic+r'''
 }
};
int main(){Monitor m;
 ticks=29999;m.loop();assert(!m.attempts);ticks=30000;m.loop();assert(m.attempts==1&&m.wifiIndex==1);
 ticks=600000;m.loop();assert(m.attempts==2);ticks=659999;m.loop();assert(m.attempts==2);ticks=660000;m.loop();assert(m.attempts==3);
 ticks=86400000;m.loop();assert(m.attempts==4); // still retries after a day offline
 WiFi.state=3;m.loop();assert(m.wifiEverConnected&&m.server.starts==1&&!m.wifiReconnects);
 m.loop();assert(m.server.starts==1);
 WiFi.state=0;++ticks;m.loop();assert(m.wifiDisconnects==1&&m.attempts==5&&!m.mdnsStarted);
 ticks+=30000;m.loop();assert(m.attempts==6); // fresh fast retry window
 WiFi.state=3;m.loop();assert(m.wifiReconnects==1&&m.server.starts==2&&m.mdnsStarted);
 WiFi.state=0;ticks=0xfffffff0;m.loop();auto attempts=m.attempts;ticks=30000;m.loop();assert(m.attempts==attempts+1);
}
'''
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'test.cpp').write_text(code);exe=p/'test.exe'
 subprocess.run([os.environ.get('CXX','c++'),'-std=c++11','-Wall','-Wextra','-Werror',str(p/'test.cpp'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: indefinite Wi-Fi retries, interval backoff, reconnect counters, stale HTTP reset, fresh outage and timer wrap')
