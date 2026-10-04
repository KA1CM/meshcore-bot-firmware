from pathlib import Path
import os, subprocess, tempfile
root=Path(__file__).resolve().parents[2];src=root/'vendor/MeshCore/examples/companion_radio'
s=(src/'MyMesh.cpp').read_text(encoding='utf-8');method=s[s.index('void MyMesh::exportBotStats('):s.index('\n#endif',s.index('void MyMesh::exportBotStats('))]
existing=Path(__file__).with_name('test_monitor_credentials.py').read_text(encoding='utf-8');mock=existing.split('mock = r"""',1)[1].split('"""',1)[0]
code=r"""
#include "MonitorBotStatsHistory.h"
#include "BotStatsWindow.h"
#include "RepeaterMonitorCore.h"
#include <ArduinoJson.h>
#include <cassert>
struct MyMesh {
 BotStatsWindow bot_stats_window;MonitorBotStatsHistory bot_stats_history;
 struct Clock{uint32_t utc=1791115200;uint32_t getCurrentTime(){return utc;}}clock;
 struct Millis{uint32_t getMillis(){return 10;}}ms;Millis* _ms=&ms;
 struct Monitor{bool ready=true;bool clockReady(){return ready;}}monitor;Monitor* repeaterMonitor=&monitor;
 Clock* getRTCClock(){return &clock;}
 void exportBotStats(JsonObject);
};
"""+method+r"""
int main(){
 MyMesh m;const uint32_t today=MonitorCore::easternDay(m.clock.utc);
 m.bot_stats_history.accepted(BOT_COMMAND_TEST,today-1,0);
 m.bot_stats_history.accepted(BOT_COMMAND_PASSWORD,today,0);
 m.bot_stats_window.accepted(BOT_COMMAND_TEST,0);m.bot_stats_window.accepted(BOT_COMMAND_NOTES,0);m.bot_stats_window.accepted(BOT_COMMAND_PASSWORD,0);
 JsonDocument doc;m.exportBotStats(doc.to<JsonObject>());
 assert(doc["today"]==today&&doc["startedDay"]==today-1&&doc["storageReady"].as<bool>());
 assert(doc["days"].size()==30);assert(doc["days"][0]["day"]==today-29);assert(!doc["days"][0]["available"].as<bool>());
 assert(doc["days"][28]["available"].as<bool>()&&doc["days"][29]["available"].as<bool>());
 auto categories=doc["categories"].as<JsonArray>();int admin=-1,test=-1,index=0;
 for(auto category:categories){const char* name=category.as<const char*>();if(!strcmp(name,"admin"))admin=index;if(!strcmp(name,"test"))test=index;assert(strcmp(name,"notes")&&strcmp(name,"password")&&strcmp(name,"advert"));++index;}
 assert(admin>=0&&test>=0);assert(doc["last24h"][admin]==2&&doc["last24h"][test]==1);
 assert(doc["days"][29]["counts"][admin]==1&&doc["days"][28]["counts"][test]==1);
 std::string json;serializeJson(doc,json);assert(json.find("password")==std::string::npos&&json.find("key")==std::string::npos);
 m.monitor.ready=false;doc.clear();m.exportBotStats(doc.to<JsonObject>());assert(doc["today"]==0&&doc["days"].size()==0&&doc["last24h"][admin]==2);
}
"""
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'Preferences.h').write_text(mock,encoding='utf-8');(p/'test.cpp').write_text(code,encoding='utf-8');exe=p/'test.exe'
 subprocess.run([os.environ.get('CXX','c++'),'-std=c++11','-Wall','-Wextra','-Werror','-Wno-unused-function','-I',str(p),'-I',str(src),'-I',str(root/'vendor/MeshCore/.pio/libdeps/heltec_v4_companion_radio_usb/ArduinoJson/src'),str(p/'test.cpp'),str(src/'BotCommandRegistry.cpp'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: real dashboard JSON export, matching category indices, 30 Eastern dates, unknown/empty days, admin grouping, clock readiness and no credentials')
