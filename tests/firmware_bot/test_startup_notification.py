"""Host regression for the actual startup notification polling method (no device needed)."""
from pathlib import Path
import os
import subprocess
import tempfile

root = Path(__file__).resolve().parents[2]
source = (root / 'vendor/MeshCore/examples/companion_radio/RepeaterMonitor.cpp').read_text(encoding='utf-8')
method = source[source.index('void RepeaterMonitor::pollStartupNotification()'):source.index('void RepeaterMonitor::pollSunriseNotification()')]
code = r'''
#include <cassert>
#include <cstdint>
#include <cstddef>
#include <cstdio>
#include <cstring>
#include <ctime>
#include <string>
#include <vector>
uint32_t ticks=0;
uint32_t millis(){return ticks;}
bool elapsed(uint32_t now,uint32_t deadline){return (int32_t)(now-deadline)>=0;}
namespace FirmwareBot { int32_t easternUtcOffsetSeconds(uint32_t){return -14400;} }
struct BotAdminContacts {
  enum {Notifications=2};
  struct Record {uint8_t key[32]{};uint8_t permissions=Notifications;} records[4];
  BotAdminContacts(){for(int i=0;i<4;++i)records[i].key[0]=i;records[1].permissions=0;}
  size_t count(){return 4;}
  const Record* at(size_t i){return &records[i];}
};
struct Mesh {
  bool advert=false,occupied=false;
  std::vector<int> recipients;std::vector<std::string> messages;
  bool hasSentBotAdvert(){return advert;}
  void* lookupContactByPubKey(const uint8_t* key,size_t){return key[0]==3 ? nullptr : this;}
  bool sendStartupNotification(const uint8_t* key,const char* text){
    if(occupied)return false;
    recipients.push_back(key[0]);messages.push_back(text);occupied=true;return true;
  }
};
struct RepeaterMonitor {
  Mesh mesh;BotAdminContacts adminContacts;
  bool synced=false,working=false;
  bool startupNotificationReady=false,startupNotificationDone=false;
  size_t startupRecipient=0;uint32_t startupNotificationDue=0;
  char startupNotification[144]{};
  bool startupNtpFailureDone=false;size_t startupNtpFailureRecipient=0;
  uint32_t startupBootMillis=0,startupNtpFailureDue=0;
  bool busy(){return working;}
  uint32_t now(){return 1791907200;}
  void pollStartupNotification();
};
''' + method + r'''
int main(){
  {
    RepeaterMonitor offline;
    ticks=299999;offline.pollStartupNotification();assert(offline.mesh.messages.empty());
    ticks=300000;offline.pollStartupNotification();
    assert(offline.mesh.messages.size()==1);
    assert(offline.mesh.messages[0]=="I'm up\nNTP Failed..\nretrying");
    offline.mesh.occupied=false;ticks=304999;offline.pollStartupNotification();assert(offline.mesh.messages.size()==1);
    ticks=305000;offline.pollStartupNotification();assert(offline.mesh.messages.size()==2);
    ticks=310000;offline.pollStartupNotification();assert(offline.startupNtpFailureDone);
    ticks=600000;offline.pollStartupNotification();assert(offline.mesh.messages.size()==2);
    offline.synced=true;offline.mesh.occupied=false;offline.pollStartupNotification();assert(offline.mesh.messages.size()==2);
    offline.mesh.advert=true;offline.pollStartupNotification();assert(offline.mesh.messages.size()==3);
    assert(offline.mesh.messages.back().find("NTP Synced\nAdvert Sent")!=std::string::npos);
  }
  ticks=0;
  RepeaterMonitor m;
  m.pollStartupNotification();assert(m.mesh.messages.empty());
  m.mesh.advert=true;m.pollStartupNotification();assert(m.mesh.messages.empty());
  m.synced=true;m.working=true;m.pollStartupNotification();assert(m.mesh.messages.empty());
  m.working=false;m.pollStartupNotification();assert(m.mesh.recipients==std::vector<int>{0});
  assert(m.mesh.messages[0].find("I'm up\n")==0);
  assert(m.mesh.messages[0].find(" EDT\nNTP Synced\nAdvert Sent")!=std::string::npos);
  m.mesh.occupied=false;ticks=4999;m.pollStartupNotification();assert(m.mesh.messages.size()==1);
  ticks=5000;m.mesh.occupied=true;m.pollStartupNotification();assert(m.mesh.messages.size()==1);
  m.mesh.occupied=false;ticks=10000;m.pollStartupNotification();
  assert(m.mesh.recipients==std::vector<int>({0,2}));
  assert(m.mesh.messages[0]==m.mesh.messages[1]);
  ticks=15000;m.pollStartupNotification();assert(m.startupNotificationDone);
  ticks=100000;m.pollStartupNotification();assert(m.mesh.messages.size()==2);
  RepeaterMonitor reboot;reboot.synced=true;reboot.mesh.advert=true;
  reboot.pollStartupNotification();assert(reboot.mesh.messages.size()==1);
}
'''
with tempfile.TemporaryDirectory() as tmp:
    folder = Path(tmp)
    cpp = folder / 'startup.cpp'
    exe = folder / 'startup.exe'
    cpp.write_text(code, encoding='utf-8')
    subprocess.run([os.environ.get('CXX', 'c++'), '-std=c++11', '-Wall', '-Wextra', '-Werror', str(cpp), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
print('PASS: startup advert/NTP gating, recipient permissions, pacing, ACK wait and once-per-boot delivery')
