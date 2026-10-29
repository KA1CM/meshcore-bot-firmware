"""Exercise extracted nonblocking advert retry and observation methods on the host."""
from pathlib import Path
import os, subprocess, tempfile
root=Path(__file__).resolve().parents[2]
source=(root/'vendor/MeshCore/examples/companion_radio/RepeaterMonitor.cpp').read_text(encoding='utf-8')
methods=source[source.index('void RepeaterMonitor::finishRepeaterAdvert('):source.index('const char* RepeaterMonitor::startAdminCheck(')]
observed=source[source.index('void RepeaterMonitor::onVerifiedAdvert('):source.index('  // Only direct adverts:')]+ '\n}\n'
reply=source[source.index('bool RepeaterMonitor::onCommandResponse('):source.index('  if ((syncPhase != SyncReply')]+ '\n  return false;\n}\n'
code=r'''
#include <cstdint>
#include <cstddef>
#include <cstdio>
#include <cstring>
#include <cassert>
#include <vector>
#include <string>
#define OUT_PATH_UNKNOWN 255
#define MSG_SEND_FAILED -1
uint32_t ticks=100;uint32_t millis(){return ticks;}
bool elapsed(uint32_t now,uint32_t due){return (int32_t)(now-due)>=0;}
unsigned esp_random(){return 42;}
struct ContactInfo {uint8_t out_path_len=1;};
struct RepeaterMonitor {
 enum AdvertPhase {AdvertIdle,AdvertLogin,AdvertReady,AdvertReply,AdvertObserve,AdvertResult}advertPhase=AdvertIdle;
 uint8_t advertTargetKey[32]{},advertAdminKey[32]{};
 char advertTargetName[33]{"Hill"},advertPrefix[4]{},advertResult[96]{};
 uint32_t advertDeadline=0,advertStamp=0,advertBaseline=10;
 uint8_t advertPreFlood=0,advertLogins=0,advertPostAttempts=0;bool advertHeard=false;
 struct Admins {enum {Commands=1};bool allowed=true;bool allows(const uint8_t*,int){return allowed;}}adminContacts;
 struct Credentials {bool available(){return true;}const char* password(const uint8_t*){return "secret";}}credentials;
 struct Mesh {
   ContactInfo contact;unsigned logins=0;std::vector<uint32_t> stamps;std::vector<int> routes;std::string result;
   struct Clock {uint32_t getCurrentTimeUnique(){return 1000;}}clock;
   Clock* getRTCClock(){return &clock;}
   ContactInfo* lookupContactByPubKey(const uint8_t*,int){return &contact;}
   int sendCommandData(ContactInfo c,uint32_t stamp,int,const char* command,uint32_t& estimate){
     assert(!strcmp(command,"2A|advert"));stamps.push_back(stamp);routes.push_back(c.out_path_len);estimate=100;return 0;
   }
   int sendLogin(ContactInfo c,const char*,uint32_t& estimate){assert(c.out_path_len==255);++logins;estimate=100;return 0;}
   bool sendAdminCheckResult(const uint8_t*,const char* text){result=text;return true;}
 }mesh;
 bool syncTimeReady(){return true;}uint32_t now(){return 1000;}uint32_t timeout(uint32_t n){return n;}
 void finishRepeaterAdvert(const char*);void sendRepeaterAdvert(bool);void retryRepeaterAdvert();void pollRepeaterAdvert();
 void onVerifiedAdvert(const uint8_t*,uint32_t,uint8_t);
 bool onCommandResponse(const ContactInfo&,const char*);
};
'''
# The real response handler needs the authenticated sender's full public key.
code=code.replace('struct ContactInfo {','struct ContactInfo {struct {uint8_t pub_key[32]{};}id;')
code+=methods+observed+reply+r'''
void advance(RepeaterMonitor& m){ticks=m.advertDeadline+1;m.pollRepeaterAdvert();}
int main(){
 RepeaterMonitor m;m.sendRepeaterAdvert(false);
 assert(m.mesh.logins==0&&m.mesh.routes[0]==1);
 for(int i=0;i<3;++i){advance(m);assert(m.advertPhase==m.AdvertReady);advance(m);}
 assert(m.mesh.stamps.size()==4&&m.mesh.logins==0);
 for(auto stamp:m.mesh.stamps)assert(stamp==m.mesh.stamps[0]);
 advance(m);assert(m.advertPhase==m.AdvertLogin&&m.mesh.logins==1);
 advance(m);assert(m.advertPhase==m.AdvertLogin&&m.mesh.logins==2);
 advance(m);assert(m.advertPhase==m.AdvertResult);m.pollRepeaterAdvert();assert(m.advertPhase==m.AdvertIdle);
 RepeaterMonitor heard;heard.sendRepeaterAdvert(false);
 uint8_t other[32]{1};heard.onVerifiedAdvert(other,11,2);assert(!heard.advertHeard);
 heard.onVerifiedAdvert(heard.advertTargetKey,10,2);assert(!heard.advertHeard);
 heard.onVerifiedAdvert(heard.advertTargetKey,11,2);assert(heard.advertHeard);
 heard.pollRepeaterAdvert();assert(heard.advertPhase==heard.AdvertResult&&heard.mesh.logins==0);
 RepeaterMonitor wait;wait.sendRepeaterAdvert(false);ContactInfo sender;
 assert(!wait.onCommandResponse(sender,"XX|OK - Advert sent"));
 assert(wait.onCommandResponse(sender,"2A|OK - Advert sent")&&wait.advertPhase==wait.AdvertObserve);
 const size_t commands=wait.mesh.stamps.size();advance(wait);
 assert(strstr(wait.advertResult,"advert not heard")&&wait.mesh.stamps.size()==commands);
 RepeaterMonitor confirmed;confirmed.sendRepeaterAdvert(false);
 confirmed.onCommandResponse(sender,"2A|OK - Advert sent");
 confirmed.onVerifiedAdvert(confirmed.advertTargetKey,11,2);
 assert(confirmed.advertPhase==confirmed.AdvertResult&&strstr(confirmed.advertResult,"Advert heard"));
}
'''
with tempfile.TemporaryDirectory() as tmp:
    folder=Path(tmp);cpp=folder/'advert.cpp';exe=folder/'advert.exe';cpp.write_text(code)
    subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror','-Wno-unused-parameter',str(cpp),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('PASS: existing authorization first, bounded retries, duplicate timestamps, login fallback, verified adverts and observation timeout')
