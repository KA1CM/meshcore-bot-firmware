from pathlib import Path
import os, subprocess, tempfile
root=Path(__file__).resolve().parents[2];src=root/'vendor/MeshCore/examples/companion_radio'
code=(src/'RepeaterMonitor.cpp').read_text()
response=code[code.index('bool RepeaterMonitor::onResponse('):code.index('\nvoid RepeaterMonitor::poll()')]
sync=code[code.index('bool RepeaterMonitor::startClockSync('):code.index('void RepeaterMonitor::loop()')]
finish=code[code.index('void RepeaterMonitor::finish('):code.index('bool RepeaterMonitor::onResponse(')]
harness=r"""
#include "RepeaterMonitorCore.h"
#include <cassert>
#include <cstring>
#include <cstdio>
#include <string>
using namespace MonitorCore;
uint32_t ticks=10000,wall=2000000000;
uint32_t millis(){return ticks;}
uint32_t esp_random(){return 42;}
#define MSG_SEND_FAILED 0
struct ContactInfo { struct { uint8_t pub_key[32]{}; } id; };
struct Clock { uint32_t offset=0; uint32_t getCurrentTimeUnique(){return wall+offset;} };
struct Mesh { ContactInfo c; Clock clock; int sends=0,logins=0; bool fail=false; std::string command;
 ContactInfo* lookupContactByPubKey(const uint8_t* key,int){return !memcmp(key,c.id.pub_key,32)?&c:nullptr;}
 Clock* getRTCClock(){return &clock;}
 int sendLogin(const ContactInfo&,const char*,uint32_t& estimate){++logins;estimate=1000;return fail?0:1;}
 int sendCommandData(const ContactInfo&,uint32_t,uint8_t,const char* text,uint32_t& estimate){++sends;command=text;estimate=1000;return fail?0:1;}
};
struct Credentials {bool available(){return true;}const char* password(const uint8_t*){return "test-only";}};
struct RepeaterMonitor {
 Mesh mesh;Credentials credentials;
 enum SyncPhase {SyncIdle,SyncLogin,SyncReady,SyncReply,SyncCheckReady,SyncCheckReply,SyncResetReady,SyncRebootWait} syncPhase=SyncIdle;
 enum Phase {Idle,Login,NeedStatus,Status,Next} phase=Idle;
 bool storageOK=true,automatic=false;int singleTarget=-1;uint32_t runDay=easternDay(wall);
 int syncTarget=0,active=-1;size_t count=1;
 Entry entries[1]{};uint32_t syncDeadline=0,deadline=0,clockSentUtc=0,clockSentMillis=0,clockUncertainty=0,tag=0;
 int64_t clockOffset=0;bool clockKnown=false,running=false,ready=true;
 bool adminConfirmed[1]{},syncLoginAttempted=false,syncResetAttempted=false;uint8_t syncToken=0;
 uint32_t syncCommandSentUtc=0,syncCommandSentMillis=0;void recordClockSample(uint32_t);
 char syncPrefix[4]{};std::string syncResult;
 bool syncTimeReady(){return ready;}uint32_t now(){return wall;}
 bool saveOK=true;int saves=0;bool save(){++saves;return saveOK;}
 void finish(uint8_t,uint16_t);
 bool startClockSync(int);bool startSyncLogin();void finishClockSync(const char*);
 void pollClockSync();bool onCommandResponse(const ContactInfo&,const char*);bool onResponse(const ContactInfo&,const uint8_t*,size_t);
 RepeaterMonitor(){entries[0].key[0]=1;mesh.c.id.pub_key[0]=1;}
};
"""+finish+response+sync+r"""
void step(RepeaterMonitor& m){ticks=m.syncDeadline;m.pollClockSync();}
void login(RepeaterMonitor& m,bool admin=true){uint8_t reply[16]{};reply[6]=admin?1:0;assert(m.onResponse(m.mesh.c,reply,16));}
bool reply(RepeaterMonitor& m,const char* text){return m.onCommandResponse(m.mesh.c,(std::string(m.syncPrefix)+text).c_str());}
std::string clockText(uint32_t stamp){time_t t=stamp;const tm c=*gmtime(&t);char text[40];snprintf(text,sizeof(text),"%02d:%02d - %d/%d/%d UTC",c.tm_hour,c.tm_min,c.tm_mday,c.tm_mon+1,c.tm_year+1900);return text;}
void sendSync(RepeaterMonitor& m){m.adminConfirmed[0]=true;m.syncPhase=RepeaterMonitor::SyncReady;m.syncDeadline=ticks;step(m);}
void futureRefusal(RepeaterMonitor& m){
 assert(reply(m,"ERR: clock cannot go backwards"));assert(m.syncPhase==RepeaterMonitor::SyncCheckReady);
 step(m);assert(m.mesh.command.substr(3)=="clock");
 assert(reply(m,clockText(wall+3600).c_str()));assert(m.syncPhase==RepeaterMonitor::SyncResetReady);
}
int main(){
 // Unknown access must be confirmed as admin; guests and wrong senders cannot authorize.
 RepeaterMonitor m;assert(m.startSyncLogin());
 uint8_t data[16]{};data[6]=1;ContactInfo wrong;wrong.id.pub_key[0]=2;
 assert(!m.onResponse(wrong,data,16));assert(!m.onResponse(m.mesh.c,data,12));
 login(m,false);assert(m.syncPhase==RepeaterMonitor::SyncIdle&&!m.adminConfirmed[0]&&m.mesh.sends==0);
 assert(m.startSyncLogin());login(m);assert(m.adminConfirmed[0]);
 m.pollClockSync();assert(m.mesh.sends==0);step(m);assert(m.mesh.command.substr(3)=="clock sync");
 assert(!m.onCommandResponse(wrong,(std::string(m.syncPrefix)+"OK - clock set: 12:00").c_str()));
 assert(!m.onCommandResponse(m.mesh.c,"FF|OK - clock set: 12:00"));
 assert(reply(m,"OK - clock set: 12:00"));assert(m.syncPhase==RepeaterMonitor::SyncIdle&&m.adminConfirmed[0]);
 assert(m.entries[0].lastSynced==wall&&m.saves==1);
 // The existing battery login also learns admin permission; guest/legacy replies clear it.
 m.running=true;m.active=0;m.phase=RepeaterMonitor::Login;assert(m.onResponse(m.mesh.c,data,16));assert(m.adminConfirmed[0]);
 m.phase=RepeaterMonitor::Login;data[6]=0;assert(m.onResponse(m.mesh.c,data,16));assert(!m.adminConfirmed[0]);
 // Cached access avoids login. Missing response falls back to just one fresh login/retry.
 RepeaterMonitor cached;sendSync(cached);assert(cached.mesh.logins==0);
 step(cached);assert(cached.mesh.logins==1&&cached.syncPhase==RepeaterMonitor::SyncLogin);
 login(cached);step(cached);step(cached);assert(cached.syncPhase==RepeaterMonitor::SyncIdle&&cached.mesh.logins==1);
 assert(cached.syncResult.find("may have changed")!=std::string::npos);
 // A verified future wall clock gets one reboot, bounded wait, explicit login and sync.
 RepeaterMonitor future;sendSync(future);futureRefusal(future);
 std::string oldPrefix=future.syncPrefix;step(future);
 assert(future.mesh.command.substr(3)=="clkreboot"&&future.syncResetAttempted);
 assert(future.syncPhase==RepeaterMonitor::SyncRebootWait&&future.syncDeadline-ticks==60000);
 assert(!future.onCommandResponse(future.mesh.c,(oldPrefix+clockText(wall+3600)).c_str()));
 future.pollClockSync();assert(future.mesh.logins==0);
 step(future);assert(future.mesh.logins==1&&future.syncPhase==RepeaterMonitor::SyncLogin);
 login(future);step(future);assert(future.mesh.command.substr(3)=="clock sync");
 assert(reply(future,"OK - clock set: 12:00"));assert(future.syncResult.find("after reset/reboot")!=std::string::npos);
 assert(future.entries[0].lastSynced==wall&&future.saves==2);
 // A second backward refusal must never cause another reset.
 future.syncPhase=RepeaterMonitor::SyncReady;future.syncDeadline=ticks;step(future);
 int sent=future.mesh.sends;assert(reply(future,"ERR: clock cannot go backwards"));
 assert(future.syncPhase==RepeaterMonitor::SyncIdle&&future.mesh.sends==sent);
 // Refusal alone, a close clock, malformed date, or missing clock reply cannot reboot.
 RepeaterMonitor close;sendSync(close);assert(reply(close,"ERR: clock cannot go backwards"));step(close);
 assert(reply(close,clockText(wall).c_str()));assert(close.syncPhase==RepeaterMonitor::SyncIdle&&!close.syncResetAttempted);
 RepeaterMonitor malformed;sendSync(malformed);assert(reply(malformed,"ERR: clock cannot go backwards"));step(malformed);
 assert(reply(malformed,"12:00 - 31/2/2089 UTC"));assert(!malformed.syncResetAttempted&&malformed.syncPhase==RepeaterMonitor::SyncIdle);
 RepeaterMonitor missing;sendSync(missing);assert(reply(missing,"ERR: clock cannot go backwards"));step(missing);step(missing);
 assert(!missing.syncResetAttempted&&missing.syncPhase==RepeaterMonitor::SyncIdle);
 // Stale NTP or a poisoned local unique timestamp stops all outgoing clock commands.
 RepeaterMonitor stale;stale.ready=false;sendSync(stale);assert(stale.mesh.sends==0);
 RepeaterMonitor poisoned;poisoned.mesh.clock.offset=200;sendSync(poisoned);assert(poisoned.mesh.sends==0);
 RepeaterMonitor late;sendSync(late);ticks=late.syncDeadline;assert(!reply(late,"ERR: clock cannot go backwards"));
 assert(close.entries[0].lastSynced==0&&close.saves==1);
 RepeaterMonitor diskFailure;diskFailure.entries[0].lastSynced=wall-86400;diskFailure.saveOK=false;sendSync(diskFailure);
 assert(reply(diskFailure,"OK - clock set: 12:00"));
 assert(diskFailure.entries[0].lastSynced==wall-86400&&diskFailure.syncResult.find("could not be saved")!=std::string::npos);
assert(close.entries[0].clockCheckedAt==wall);
 assert(close.entries[0].clockUncertainty>=31&&close.entries[0].clockUncertainty<=61);
 assert(close.entries[0].clockOffset>=-30&&close.entries[0].clockOffset<=30);
 RepeaterMonitor synced;sendSync(synced);
 assert(reply(synced,(std::string("OK - clock set: ")+clockText(wall)).c_str()));
 assert(synced.entries[0].lastSynced==wall&&synced.entries[0].clockCheckedAt==wall);
 RepeaterMonitor noStorage;sendSync(noStorage);assert(reply(noStorage,"ERR: clock cannot go backwards"));step(noStorage);
 noStorage.saveOK=false;assert(reply(noStorage,clockText(wall+3600).c_str()));
 assert(noStorage.syncPhase==RepeaterMonitor::SyncIdle&&!noStorage.syncResetAttempted&&noStorage.entries[0].clockCheckedAt==0);
 // Automatic sync runs after saving a sunrise result, including failed battery reads.
 RepeaterMonitor sunrise;sunrise.running=true;sunrise.automatic=true;sunrise.active=0;
 sunrise.finish(Ok,4000);assert(sunrise.saves==1&&sunrise.mesh.logins==1&&sunrise.syncPhase==RepeaterMonitor::SyncLogin);
 assert(sunrise.phase==RepeaterMonitor::Next&&sunrise.running);
 RepeaterMonitor manual;manual.running=true;manual.active=0;manual.finish(Ok,4000);
 assert(manual.mesh.logins==0&&manual.syncPhase==RepeaterMonitor::SyncIdle);
 RepeaterMonitor failedBattery;failedBattery.running=true;failedBattery.automatic=true;failedBattery.active=0;
 failedBattery.finish(NoResponse,0);assert(failedBattery.mesh.logins==1);
 RepeaterMonitor freshClock;freshClock.running=true;freshClock.automatic=true;freshClock.active=0;freshClock.entries[0].lastSynced=wall-100;
 freshClock.finish(Ok,4000);assert(freshClock.mesh.logins==0);
 Entry e;e.lastSynced=0;assert(timeSyncDue(e,wall));
 e.lastSynced=wall-30*86400+1;assert(!timeSyncDue(e,wall));
 e.lastSynced--;assert(timeSyncDue(e,wall));
 e.lastSynced=wall-100;e.clockCheckedAt=wall;e.clockOffset=599;assert(!timeSyncDue(e,wall));
 e.clockOffset=600;assert(timeSyncDue(e,wall));e.clockOffset=-600;assert(timeSyncDue(e,wall));
 e.clockOffset=-599;assert(!timeSyncDue(e,wall));
 e.clockOffset=1000;e.clockCheckedAt=e.lastSynced-1;assert(!timeSyncDue(e,wall));
 e.readings[0].clockKnown=true;e.readings[0].timestamp=wall;e.readings[0].clockOffset=-600;assert(timeSyncDue(e,wall));
 e.readings[1].clockKnown=true;e.readings[1].timestamp=wall+1;e.readings[1].clockOffset=1;assert(!timeSyncDue(e,wall));
 e.lastSynced=0;e.enabled=false;assert(!timeSyncDue(e,wall));
 uint32_t utc;
 assert(parseClockReply("00:00 - 1/1/1970 UTC",utc)&&utc==0);
 assert(parseClockReply("12:00 - 29/2/2028 UTC",utc));
 assert(!parseClockReply("12:00 - 29/2/2027 UTC",utc));
 assert(!parseClockReply("24:00 - 1/1/2089 UTC",utc));
 assert(!parseClockReply("12:00 - 1/1/2089 UTC trailing",utc));
 assert(!parseClockReply("12:00 - 31/12/2106 UTC",utc));
}
"""
with tempfile.TemporaryDirectory() as temp:
 p=Path(temp);(p/'test.cpp').write_text(harness);exe=p/'test.exe'
 subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror','-I',str(src),str(p/'test.cpp'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: admin reuse/recovery, future-clock verification, one reset/reboot, bounded retry, stale/malformed/late response guards')
