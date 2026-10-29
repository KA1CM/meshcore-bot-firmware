from pathlib import Path
import os,subprocess,tempfile
r=Path(__file__).resolve().parents[2];s=r/'vendor/MeshCore/examples/companion_radio'
src=(s/'MyMesh.cpp').read_text(encoding='utf-8');method=src[src.index('void MyMesh::sendNextVoltageListPart()'):src.index('void MyMesh::recordBotCommandStats(')]
code=r'''
#include "BotVoltageList.h"
#include "BotScopedNameList.h"
#include "BotTypes.h"
#include "FirmwareBot.h"
#include <cassert>
#include <string>
uint32_t ticks=100;bool millisHasNowPassed(uint32_t t){return (int32_t)(ticks-t)>=0;}
bool commandAllowed=true;
namespace BotPrefsCodec {bool commandEnabled(const BotPrefs&,BotCommandId){return commandAllowed;}}
#define ESP32
#define BOT_REPEATER_MONITOR
struct BotAdminContacts {enum {Commands=1,Notifications=2};bool allowed=true;bool allows(const uint8_t*,int){return allowed;}};
struct Monitor {BotAdminContacts admins;BotAdminContacts& botAdmins(){return admins;}};
struct ContactInfo{};
bool botFormatResponseForChannel(const BotMessage& message,const char* text,size_t n,char* out,size_t cap,size_t* written){
 return FirmwareBot::writeResponseForChannel(message.channel_kind,true,text,n,out,cap,written)==BOT_WRITE_OK;
}
#define PUB_KEY_SIZE 32
struct MyMesh {
 struct PendingVoltageList {BotVoltageList::Snapshot snapshot;BotScopedNameList::Pointer scopedNames;BotCommandId command=BOT_COMMAND_LIST;bool notification=false,statusNotification=false;bool adminOnly=false;bool active=true;BotChannelKind kind=BOT_CHANNEL_DM;uint8_t channel=0,key[32]{};size_t next=0;unsigned part=1,failures=0;uint32_t deadline=100,expires=600000;} pending_voltage_list;
 struct {bool active=false;} pending_bot_dm_ack;
 struct {unsigned send_failures=0;} bot_stats;
 struct Clock {uint32_t getMillis(){return ticks;}} clock;Clock* _ms=&clock;
 Monitor monitor;Monitor* repeaterMonitor=&monitor;
 BotPrefs bot_prefs{};ContactInfo contact;bool missing=false,fail=false;unsigned sends=0;std::string lastBody;
 ContactInfo* lookupContactByPubKey(const uint8_t*,size_t){return missing?nullptr:&contact;}
 bool sendBotResponse(const BotMessage& m,ContactInfo*,uint8_t,const char* text,size_t n){lastBody.assign(text,n);assert(n<=(pending_voltage_list.command==BOT_COMMAND_USER ? FirmwareBot::maxResponseLenForChannel(m.channel_kind) : 120));++sends;if(!fail&&m.channel_kind==BOT_CHANNEL_DM)pending_bot_dm_ack.active=true;return !fail;}
 void sendNextVoltageListPart();
 MyMesh(){bot_prefs.enabled=true;pending_voltage_list.snapshot.count=3;for(auto& l:pending_voltage_list.snapshot.lines)memset(l,'a',60);for(auto& l:pending_voltage_list.snapshot.lines)l[60]=0;}
};
'''+method+r'''
int main(){
 // Exact boundaries: two complete rows fill 127 bytes; three fill 144.
 for(auto kind : {BOT_CHANNEL_DM,BOT_CHANNEL_BOT,BOT_CHANNEL_TESTING,BOT_CHANNEL_FAIRFIELD,BOT_CHANNEL_PUBLIC}) {
   MyMesh users;auto& q=users.pending_voltage_list;q.command=BOT_COMMAND_USER;q.kind=kind;q.snapshot.count=3;
   memset(q.snapshot.lines[0],'a',63);q.snapshot.lines[0][63]=0;
   memset(q.snapshot.lines[1],'b',63);q.snapshot.lines[1][63]=0;
   memset(q.snapshot.lines[2],'c',16);q.snapshot.lines[2][16]=0;
   users.sendNextVoltageListPart();
   assert(users.sends==1&&!q.active);
   assert(users.lastBody.size()==(kind==BOT_CHANNEL_DM ? 144 : 127));
   assert(users.lastBody.back()==(kind==BOT_CHANNEL_DM ? 'c' : 'b'));
   assert(users.pending_bot_dm_ack.active==(kind==BOT_CHANNEL_DM));
 }
 MyMesh stats;stats.pending_voltage_list.command=BOT_COMMAND_STATS;
 stats.sendNextVoltageListPart();assert(stats.lastBody.size()==60&&!stats.pending_voltage_list.active);
 MyMesh m;m.sendNextVoltageListPart();assert(m.sends==1&&m.pending_voltage_list.next==1);
 ticks+=5000;m.sendNextVoltageListPart();assert(m.sends==1); // wait for acknowledgement
 m.pending_bot_dm_ack.active=false;m.sendNextVoltageListPart();assert(m.sends==2);
 m.pending_bot_dm_ack.active=false;m.sendNextVoltageListPart();assert(m.sends==2); // pacing
 ticks+=5000;m.sendNextVoltageListPart();assert(m.sends==3&&!m.pending_voltage_list.active);
 MyMesh failed;failed.fail=true;for(int i=0;i<3;++i){failed.sendNextVoltageListPart();ticks+=5000;}assert(!failed.pending_voltage_list.active&&failed.bot_stats.send_failures==3&&failed.pending_voltage_list.next==0);
 MyMesh missing;missing.missing=true;missing.sendNextVoltageListPart();assert(!missing.pending_voltage_list.active&&!missing.sends);
 MyMesh disabled;disabled.bot_prefs.enabled=false;disabled.sendNextVoltageListPart();assert(!disabled.sends&&!disabled.pending_voltage_list.active);
 MyMesh report;report.pending_voltage_list.notification=true;
 for(int i=0;i<3;++i){report.pending_bot_dm_ack.active=false;ticks+=5000;report.sendNextVoltageListPart();assert(report.lastBody.find("Morning Reoprt:\n")==0);assert(report.lastBody.find(std::to_string(i+1)+"/3\n")!=std::string::npos);}
 assert(!report.pending_voltage_list.active&&report.sends==3);
 MyMesh health;health.pending_voltage_list.notification=true;health.pending_voltage_list.statusNotification=true;health.pending_voltage_list.snapshot.count=2;strcpy(health.pending_voltage_list.snapshot.lines[0],"Communication lost");strcpy(health.pending_voltage_list.snapshot.lines[1],"Wi-Fi : Lost since Oct 06 10:00");
 health.sendNextVoltageListPart();assert(health.lastBody.find("Morning Reoprt")==std::string::npos);assert(health.lastBody.find("1/")==std::string::npos);assert(health.sends==1 && !health.pending_voltage_list.active);
 MyMesh empty;empty.pending_voltage_list.notification=true;empty.pending_voltage_list.snapshot.count=1;strcpy(empty.pending_voltage_list.snapshot.lines[0],BotVoltageList::EMPTY_LOW);
 empty.sendNextVoltageListPart();assert(empty.lastBody==std::string("Morning Reoprt:\n")+BotVoltageList::EMPTY_LOW);assert(!empty.pending_voltage_list.active);
 commandAllowed=false;
 MyMesh help;help.pending_voltage_list.adminOnly=true;help.pending_voltage_list.command=BOT_COMMAND_HELP;help.sendNextVoltageListPart();assert(help.sends==1);
 help.monitor.admins.allowed=false;help.pending_bot_dm_ack.active=false;ticks+=5000;help.sendNextVoltageListPart();assert(help.sends==1&&!help.pending_voltage_list.active);
 MyMesh denied;denied.pending_voltage_list.adminOnly=true;denied.monitor.admins.allowed=false;denied.sendNextVoltageListPart();assert(!denied.sends&&!denied.pending_voltage_list.active);
 commandAllowed=true;
 MyMesh expired;expired.pending_voltage_list.expires=ticks;expired.sendNextVoltageListPart();assert(!expired.sends&&!expired.pending_voltage_list.active);
}
'''
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'test.cpp').write_text(code,encoding='utf-8');exe=p/'test.exe'
 subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror','-Wno-unused-function','-I',str(s),str(p/'test.cpp'),str(s/'FirmwareBot.cpp'),str(s/'BotCommandRegistry.cpp'),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
print('PASS: Users DM/channel byte budgets and complete rows; actual multipart sender waits for DM acknowledgements, spaces parts, bounds retries and stops on disable/expiry/missing recipient')
