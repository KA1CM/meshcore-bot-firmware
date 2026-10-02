from pathlib import Path
import os,subprocess,tempfile
root=Path(__file__).resolve().parents[2];src=root/'vendor/MeshCore/examples/companion_radio'
s=(src/'RepeaterMonitor.cpp').read_text(encoding='utf-8')
methods=s[s.index('void RepeaterMonitor::scheduleSunriseNotification()'):s.index('void RepeaterMonitor::loop()')]
# Only full automatic completion schedules the notification, never per-entry finish.
next_entry=s[s.index('void RepeaterMonitor::nextEntry()'):s.index('void RepeaterMonitor::sendLogin()')]
assert 'if (automatic) scheduleSunriseNotification();' in next_entry
assert s.count('scheduleSunriseNotification();')==1
code=r"""
#include "BotVoltageList.h"
#include <cassert>
#include <vector>
#include <string>
using namespace MonitorCore;
uint32_t ticks=100;uint32_t millis(){return ticks;}
void strlcpy(char* d,const char* s,size_t n){strncpy(d,s,n-1);d[n-1]=0;}
struct BotAdminContacts {enum{Notifications=2};struct Record{uint8_t key[32]{};int permissions=2;}records[4];size_t count(){return 4;}const Record* at(size_t i){return &records[i];}};
struct RepeaterMonitor {
 BotAdminContacts adminContacts;BotVoltageList::Snapshot sunriseNotification;
 bool sunriseNotificationPending=false,occupied=false,empty=false;
 size_t sunriseRecipient=0;uint32_t sunriseNotificationDue=0,sunriseNotificationExpires=0;
 struct Mesh {bool occupied=false;std::vector<int> recipients;std::vector<std::string> bodies;
 void* lookupContactByPubKey(const uint8_t* key,int){return key[0]==9?nullptr:this;}
 bool queueSunriseNotification(const uint8_t* key,const BotVoltageList::Snapshot& s){if(occupied)return false;recipients.push_back(key[0]);bodies.emplace_back(s.lines[0]);occupied=true;return true;}}mesh;
 bool busy(){return occupied;}
 void voltageList(BotVoltageList::Snapshot& s,bool low){assert(low);s.count=empty?0:1;strcpy(s.lines[0],"Low 3.50V");}
 void scheduleSunriseNotification();void pollSunriseNotification();
 RepeaterMonitor(){for(int i=0;i<4;++i)adminContacts.records[i].key[0]=i+1;}
};
"""+methods+r"""
int main(){
 RepeaterMonitor m;m.scheduleSunriseNotification();ticks=60099;m.pollSunriseNotification();assert(m.mesh.recipients.empty());ticks=60100;
 m.occupied=true;m.pollSunriseNotification();assert(m.mesh.recipients.empty());m.occupied=false;
 m.pollSunriseNotification();assert(m.mesh.recipients.size()==1);m.pollSunriseNotification();assert(m.mesh.recipients.size()==1);
 for(int i=0;i<4;++i){m.mesh.occupied=false;m.pollSunriseNotification();}
 assert(m.mesh.recipients.size()==4&&!m.sunriseNotificationPending);for(auto& body:m.mesh.bodies)assert(body=="Low 3.50V");
 RepeaterMonitor e;e.empty=true;e.scheduleSunriseNotification();e.adminContacts.records[1].permissions=0;e.adminContacts.records[2].key[0]=9;ticks=e.sunriseNotificationDue;
 for(int i=0;i<5;++i){e.mesh.occupied=false;e.pollSunriseNotification();}assert(e.mesh.recipients.size()==2&&e.mesh.bodies[0]=="no repeaters with voltage lower than 3.6v or N/A");
 RepeaterMonitor expired;expired.scheduleSunriseNotification();ticks=expired.sunriseNotificationExpires;expired.pollSunriseNotification();assert(!expired.sunriseNotificationPending&&expired.mesh.recipients.empty());
 ticks=0xfffffff0;RepeaterMonitor wrap;wrap.scheduleSunriseNotification();ticks+=59999;wrap.pollSunriseNotification();assert(wrap.mesh.recipients.empty());++ticks;wrap.pollSunriseNotification();assert(wrap.mesh.recipients.size()==1);
}
"""
with tempfile.TemporaryDirectory() as folder:
 d=Path(folder);(d/'test.cpp').write_text(code);exe=d/'test.exe'
 subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-I',str(src),str(d/'test.cpp'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: automatic completion hook, 60-second delay, all opted-in admins, queue contention, none, missing contacts, expiry and timer rollover')
