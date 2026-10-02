from pathlib import Path
import os, subprocess, tempfile
root=Path(__file__).resolve().parents[2];src=root/'vendor/MeshCore/examples/companion_radio'
code=(src/'RepeaterMonitor.cpp').read_text()
response=code[code.index('bool RepeaterMonitor::onResponse('):code.index('\nvoid RepeaterMonitor::poll()')]
sync=code[code.index('bool RepeaterMonitor::startClockSync('):code.index('void RepeaterMonitor::scheduleSunriseNotification()')]
finish=code[code.index('void RepeaterMonitor::finish('):code.index('bool RepeaterMonitor::onResponse(')]
harness=r"""
#include "RepeaterMonitorCore.h"
#include <cassert>
#include <cstring>
#include <cstdio>
#include <string>
#include <vector>
using namespace MonitorCore;
void strlcpy(char* d,const char* s,size_t n){strncpy(d,s,n-1);d[n-1]=0;}
uint32_t ticks=10000,wall=2000000000;
uint32_t millis(){return ticks;}
uint32_t esp_random(){return 42;}
#define MSG_SEND_FAILED 0
#define OUT_PATH_UNKNOWN 255
struct ContactInfo { uint8_t out_path_len=2; struct { uint8_t pub_key[32]{}; } id; };
struct Clock { uint32_t offset=0; uint32_t getCurrentTimeUnique(){return wall+offset;} };
struct Mesh { ContactInfo c; Clock clock; int sends=0,logins=0; bool fail=false; std::string command;std::vector<int> routes;
 ContactInfo* lookupContactByPubKey(const uint8_t* key,int){return !memcmp(key,c.id.pub_key,32)?&c:nullptr;}
 Clock* getRTCClock(){return &clock;}
 int sendLogin(const ContactInfo& target,const char*,uint32_t& estimate){++logins;assert(target.out_path_len==OUT_PATH_UNKNOWN);routes.push_back(target.out_path_len);estimate=1000;return fail?0:1;}
 int sendCommandData(const ContactInfo& target,uint32_t,uint8_t,const char* text,uint32_t& estimate){++sends;assert(target.out_path_len==OUT_PATH_UNKNOWN);command=text;estimate=1000;return fail?0:1;}
};
struct Credentials {bool available(){return true;}const char* password(const uint8_t*){return "test-only";}};
struct RepeaterMonitor {
 Mesh mesh;Credentials credentials;
 enum SyncPhase {SyncIdle,SyncLogin,SyncReady,SyncReply,SyncCheckReady,SyncCheckReply,SyncResetReady,SyncRebootWait} syncPhase=SyncIdle;
 enum Phase {Idle,Login,NeedStatus,Status,Next} phase=Idle;
 bool adminCheckPending=false,adminCheckIsSync=false;char adminCheckName[33]{},adminCheckReply[96]{};
 bool storageOK=true,automatic=false;int singleTarget=-1;uint32_t runDay=easternDay(wall);
 int syncTarget=0,active=-1;size_t count=1;
 Entry entries[1]{};uint32_t syncDeadline=0,deadline=0,clockSentUtc=0,clockSentMillis=0,clockUncertainty=0,tag=0;
 int64_t clockOffset=0;bool clockKnown=false,running=false,ready=true;
 bool adminConfirmed[1]{};uint8_t syncResetCount=0,syncCommandAttempts=0;uint8_t syncToken=0,syncLoginAttempt=0;uint32_t syncLoginSentUtc=0,syncLoginSentMillis=0;
 uint32_t syncCommandSentUtc=0,syncCommandSentMillis=0;void recordClockSample(uint32_t);void chooseSyncAction(int64_t);
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
void login(RepeaterMonitor& m,bool admin=true,int32_t offset=-120){uint8_t reply[16]{};uint32_t remote=wall+offset;memcpy(reply,&remote,4);reply[6]=admin?1:0;assert(m.onResponse(m.mesh.c,reply,16));}
bool reply(RepeaterMonitor& m,const char* text){return m.onCommandResponse(m.mesh.c,(std::string(m.syncPrefix)+text).c_str());}
std::string clockText(uint32_t stamp){time_t t=stamp;const tm c=*gmtime(&t);char text[40];snprintf(text,sizeof(text),"%02d:%02d - %d/%d/%d UTC",c.tm_hour,c.tm_min,c.tm_mday,c.tm_mon+1,c.tm_year+1900);return text;}
void sendSync(RepeaterMonitor& m){m.adminConfirmed[0]=true;m.syncPhase=RepeaterMonitor::SyncReady;m.syncDeadline=ticks;step(m);}
int main(){
 // Admin DM result mirrors final sync outcome, including failures.
 RepeaterMonitor dm;dm.adminCheckPending=true;dm.adminCheckIsSync=true;strcpy(dm.adminCheckName,"Chestnut Hill");
 dm.finishClockSync("Successful sync");assert(!strcmp(dm.adminCheckReply,"Chestnut Hill: Successful sync"));
 dm.adminCheckReply[0]=0;dm.finishClockSync("Admin login timeout");assert(!strcmp(dm.adminCheckReply,"Chestnut Hill: Admin login timeout"));
 // Every new process logs in, even if the old session was confirmed.
 RepeaterMonitor m;m.adminConfirmed[0]=true;assert(m.startClockSync(0));assert(m.mesh.logins==1&&m.mesh.sends==0&&m.mesh.c.out_path_len==2);
 login(m);assert(m.entries[0].clockOffset==-120&&m.entries[0].clockCheckedAt==wall);
 step(m);assert(m.mesh.command.substr(3)=="clock sync");
 assert(reply(m,"OK - clock set: 12:00"));assert(m.entries[0].lastSynced==wall&&m.syncResult=="Successful sync");
 for(int offset : {0,1,180}) {
  RepeaterMonitor close;assert(close.startClockSync(0));login(close,true,offset);
  assert(close.syncPhase==RepeaterMonitor::SyncIdle&&close.mesh.sends==0&&close.entries[0].clockOffset==offset);
  assert(close.syncResult=="Clock is ahead, but close"&&!close.entries[0].lastSynced);
 }
 // Three resets maximum; each is followed by a full fresh login and new measurement.
 RepeaterMonitor ahead;assert(ahead.startClockSync(0));login(ahead,true,181);
 for(int i=1;i<=3;++i) {
  assert(ahead.syncPhase==RepeaterMonitor::SyncResetReady);step(ahead);
  assert(ahead.syncResetCount==i&&ahead.mesh.command.substr(3)=="clkreboot");
  assert(ahead.syncDeadline-ticks==60000);step(ahead);assert(ahead.syncPhase==RepeaterMonitor::SyncLogin);
  login(ahead,true,20); // still ahead after recovery: repeat, even within initial 180-second band
 }
 assert(ahead.syncPhase==RepeaterMonitor::SyncIdle&&ahead.syncResult=="Reset limit reached"&&ahead.mesh.sends==3&&ahead.mesh.logins==4);
 RepeaterMonitor recovery;assert(recovery.startClockSync(0));login(recovery,true,400);step(recovery);
 // Unexpected reboot reply does not skip the fresh-login clock check.
 assert(reply(recovery,"ERR unsupported"));assert(recovery.syncPhase==RepeaterMonitor::SyncRebootWait);
 step(recovery);login(recovery,true,-10);step(recovery);assert(recovery.mesh.command.substr(3)=="clock sync");
 assert(reply(recovery,"OK - clock set: 12:00"));assert(recovery.syncResult=="Successful sync"&&recovery.entries[0].lastSynced==wall);
 // No confirmation: initial send plus exactly three retries, no new login/reboot.
 RepeaterMonitor missing;assert(missing.startClockSync(0));login(missing);step(missing);
 std::string old=missing.syncPrefix;
 for(int i=0;i<3;++i){step(missing);assert(missing.syncPhase==RepeaterMonitor::SyncReady);step(missing);}
 assert(missing.mesh.sends==4&&missing.mesh.logins==1);
 assert(!missing.onCommandResponse(missing.mesh.c,(old+"OK - clock set: 12:00").c_str()));
 step(missing);assert(missing.syncPhase==RepeaterMonitor::SyncIdle&&missing.syncResult=="No confirmation received"&&!missing.entries[0].lastSynced);
 RepeaterMonitor retrySuccess;assert(retrySuccess.startClockSync(0));login(retrySuccess);step(retrySuccess);step(retrySuccess);step(retrySuccess);
 assert(reply(retrySuccess,"OK - clock set: 12:00"));assert(retrySuccess.mesh.sends==2&&retrySuccess.syncResult=="Successful sync");
 RepeaterMonitor denied;assert(denied.startClockSync(0));login(denied,false);assert(denied.syncResult=="No admin permission"&&denied.mesh.sends==0);
 RepeaterMonitor timeout;assert(timeout.startClockSync(0));step(timeout);step(timeout);step(timeout);
 assert((timeout.mesh.routes==std::vector<int>{255,255,255})&&timeout.syncResult=="Admin login timeout");
 RepeaterMonitor flood;flood.mesh.c.out_path_len=255;assert(flood.startClockSync(0));step(flood);step(flood);step(flood);
 assert((flood.mesh.routes==std::vector<int>{255,255,255})&&flood.syncPhase==RepeaterMonitor::SyncIdle);
 RepeaterMonitor stale;assert(stale.startClockSync(0));stale.ready=false;login(stale);assert(stale.mesh.sends==0&&stale.syncPhase==RepeaterMonitor::SyncIdle);
 RepeaterMonitor disk;assert(disk.startClockSync(0));disk.saveOK=false;login(disk);assert(!disk.entries[0].clockCheckedAt&&disk.mesh.sends==0&&disk.syncPhase==RepeaterMonitor::SyncIdle);
 RepeaterMonitor poisoned;assert(poisoned.startClockSync(0));login(poisoned);poisoned.mesh.clock.offset=200;step(poisoned);assert(poisoned.mesh.sends==0);
 RepeaterMonitor refused;assert(refused.startClockSync(0));login(refused);step(refused);assert(reply(refused,"ERR: clock cannot go backwards"));assert(refused.syncPhase==RepeaterMonitor::SyncIdle&&refused.mesh.sends==1);
 // Padded replies from flood paths still supply the offset; malformed/wrong sender replies do not.
 for(size_t n=13;n<=28;++n){RepeaterMonitor padded;assert(padded.startClockSync(0));uint8_t data[29]{};uint32_t remote=wall-25;memcpy(data,&remote,4);data[6]=1;ContactInfo wrong;wrong.id.pub_key[0]=2;
  assert(!padded.onResponse(wrong,data,n));assert(padded.onResponse(padded.mesh.c,data,n));assert(padded.entries[0].clockOffset==-25&&padded.syncPhase==RepeaterMonitor::SyncReady);}
 uint8_t invalid[29]{};assert(!modernLoginOK(invalid,29));invalid[13]=1;assert(!modernLoginOK(invalid,24));
 // Battery-login measurements remain independent of the later voltage result.
 for(bool admin : {false,true}) {RepeaterMonitor battery;battery.running=true;battery.active=0;battery.phase=RepeaterMonitor::Login;battery.clockSentUtc=wall;battery.clockSentMillis=ticks;
  uint8_t data[24]{};uint32_t remote=wall+33;memcpy(data,&remote,4);data[6]=admin?1:0;
  assert(battery.onResponse(battery.mesh.c,data,24));assert(battery.saves==1&&battery.entries[0].clockOffset==33);battery.finish(NoResponse,0);assert(battery.entries[0].clockOffset==33&&!battery.entries[0].lastSynced);}
 // Automatic sync runs after saving a sunrise result, including failed battery reads.
 RepeaterMonitor sunrise;sunrise.running=true;sunrise.automatic=true;sunrise.active=0;
 sunrise.finish(Ok,4000);assert(sunrise.saves>=1&&sunrise.mesh.logins==1&&sunrise.syncPhase==RepeaterMonitor::SyncLogin);
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
 e.readings[1].clockKnown=true;e.readings[1].timestamp=wall+1;e.readings[1].clockOffset=1;assert(!timeSyncDue(e,wall+1));
 e.lastSynced=0;e.enabled=false;assert(!timeSyncDue(e,wall));
 // Fresh acceptable measurements defer maintenance without claiming a successful sync.
 Entry measured;measured.clockCheckedAt=wall;measured.clockOffset=33;
 assert(!timeSyncDue(measured,wall+86400));assert(measured.lastSynced==0);
 assert(!timeSyncDue(measured,wall+30*86400-1));assert(timeSyncDue(measured,wall+30*86400));
 measured.clockOffset=599;assert(!timeSyncDue(measured,wall));
 measured.clockOffset=-599;assert(!timeSyncDue(measured,wall));
 measured.clockOffset=600;assert(timeSyncDue(measured,wall));
 measured.clockOffset=-600;assert(timeSyncDue(measured,wall));
 measured.lastSynced=wall-31*86400;measured.clockOffset=0;assert(!timeSyncDue(measured,wall));
 measured.clockCheckedAt=wall+1;measured.lastSynced=0;assert(timeSyncDue(measured,wall));
 measured.clockCheckedAt=0;measured.readings[0].clockKnown=true;
 measured.readings[0].timestamp=wall;measured.readings[0].clockOffset=10;
 assert(!timeSyncDue(measured,wall+86400));
 RepeaterMonitor acceptable;acceptable.running=true;acceptable.automatic=true;acceptable.active=0;
 acceptable.entries[0].clockCheckedAt=wall-86400;acceptable.entries[0].clockOffset=33;
 acceptable.finish(Ok,4000);assert(acceptable.mesh.logins==0);
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
print('PASS: offset-driven sync, 180-second boundary, three reboot cycles, three sync retries, persistence and response guards')
