from pathlib import Path
import os,subprocess,tempfile
root=Path(__file__).resolve().parents[2];src=root/'vendor/MeshCore/examples/companion_radio'
s=(src/'RepeaterMonitor.cpp').read_text(encoding='utf-8')
method=s[s.index('void RepeaterMonitor::pollConnectivityNotifications()'):s.index('void RepeaterMonitor::scheduleSunriseNotification()')]
code=r'''
#include "BotConnectivity.h"
#include "BotVoltageList.h"
#include <cassert>
#include <string>
#include <vector>
using String=std::string;
void strlcpy(char* d,const char* s,size_t n){snprintf(d,n,"%s",s);}
void connectivityTime(uint32_t utc,char* out,size_t n){snprintf(out,n,"Time %u",utc);}
struct BotAdminContacts {enum{Notifications=2};struct Record{uint8_t key[32]{};int permissions=2;}records[3];size_t count(){return 3;}const Record* at(size_t i){return &records[i];}};
struct RepeaterMonitor {
 BotConnectivity::Event connectivityEvents[16];uint8_t connectivityHead=0,connectivityCount=0;size_t connectivityRecipient=0;
 BotVoltageList::Snapshot connectivityMessage;bool connectivityMessageReady=false;
 BotAdminContacts adminContacts;bool occupied=false;bool busy(){return occupied;}
 struct Mesh {
 bool occupied=false;std::vector<BotVoltageList::Snapshot> messages;std::vector<int> recipients;
 void* lookupContactByPubKey(const uint8_t*,int){return this;}
 bool queueStatusNotification(const uint8_t* key,const BotVoltageList::Snapshot& s){if(occupied)return false;messages.push_back(s);recipients.push_back(key[0]);occupied=true;return true;}
 }mesh;
 void pollConnectivityNotifications();
 RepeaterMonitor(){for(int i=0;i<3;++i)adminContacts.records[i].key[0]=i+1;adminContacts.records[1].permissions=0;}
};
'''+method+r'''
int main(){
 using namespace BotConnectivity;
 const Kind kinds[]={PowerLost,PowerReminder,PowerRestored,WifiLost,WifiReminder,WifiRestoredOnline,WifiRestoredOffline,InternetLost,InternetReminder,InternetRestored};
 const char* expected[]={
 "USB power lost\nTime 200\nBattery 4.03V",
 "USB power lost since\nTime 100\nBattery 4.03V",
 "USB power restored\nTotal time 2h 3m\nBattery 4.03V",
 "Wi-Fi disconnected\nTime 200",
 "Wi-Fi disconnected since\nTime 100",
 "Wi-Fi: Restored\nInternet: Restored\nTotal time 2h 3m",
 "Wi-Fi: Restored\nInternet: Lost since\nTime 100",
 "Internet lost since\nTime 100",
 "Internet lost since\nTime 100",
 "Internet restored\nTotal time 2h 3m"};
 for(size_t i=0;i<10;++i){
  RepeaterMonitor m;m.connectivityCount=1;auto& e=m.connectivityEvents[0];
  e.kind=kinds[i];e.utc=200;e.since=100;e.durationMs=7380000;e.battery=4030;
  m.pollConnectivityNotifications();assert(m.mesh.messages.size()==1);
  m.pollConnectivityNotifications();assert(m.mesh.messages.size()==1);
  m.mesh.occupied=false;m.pollConnectivityNotifications();assert(m.mesh.messages.size()==2);
  m.pollConnectivityNotifications();assert(!m.connectivityCount);
  assert(m.mesh.recipients[0]==1 && m.mesh.recipients[1]==3);
  for(auto& report:m.mesh.messages){
   char body[121];assert(BotVoltageList::singleMessage(report,body,sizeof(body)));
   assert(std::string(body)==expected[i]);assert(strlen(body)<=120);
  }
 }
}

'''
# Arduino String exposes c_str/length, matching std::string for these operations.
with tempfile.TemporaryDirectory() as folder:
 d=Path(folder);(d/'test.cpp').write_text(code);exe=d/'test.exe'
 subprocess.run([os.environ.get('CXX','g++'),'-std=c++17','-I',str(src),str(d/'test.cpp'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS outage report text, partial restoration, battery snapshot, paging, permissions and queue contention')
