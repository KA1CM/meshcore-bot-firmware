from pathlib import Path
import os,subprocess,tempfile
root=Path(__file__).resolve().parents[2];src=root/'vendor/MeshCore/examples/companion_radio'
s=(src/'RepeaterMonitor.cpp').read_text(encoding='utf-8')
methods=s[s.index('const char* RepeaterMonitor::startAdminCheck('):s.index('bool RepeaterMonitor::startRun(')]
code=r"""
#include "BotVoltageList.h"
#include <cassert>
#include <string>
#include <strings.h>
using namespace MonitorCore;
uint32_t ticks=100;uint32_t millis(){return ticks;}
struct BotAdminContacts {enum{Commands=1};bool allowed=true;bool allows(const uint8_t*,int){return allowed;}};
struct RepeaterMonitor {
 BotAdminContacts adminContacts;bool adminCheckIsSync=false;enum {SyncIdle,SyncLogin}syncPhase=SyncIdle;bool syncOK=true;int syncTarget=-1;
 bool startClockSync(int i){syncTarget=i;if(syncOK)syncPhase=SyncLogin;return syncOK;}
 bool synced=true,storageOK=true,occupied=false,adminCheckPending=false,running=false,automatic=true;
 char adminCheckName[33]{},adminCheckReply[96]{};uint8_t adminCheckRecipient[32]{};uint32_t adminCheckExpires=0,runDay=0,deadline=0;
 int singleTarget=-1,active=-1;enum {Next}phase=Next;
 Entry entries[3]{};size_t count=3;
 struct Mesh {bool busy=false;int sends=0;std::string reply;struct Contact{char name[33]{};};Contact* lookupContactByPubKey(const uint8_t*,int){return nullptr;}
 bool sendAdminCheckResult(const uint8_t*,const char* text){if(busy)return false;++sends;reply=text;return true;}}mesh;
 bool busy(){return occupied;}uint32_t now(){return 2000000000;}
 const char* startAdminCheck(const uint8_t*,const char*,bool sync=false);void pollAdminCheckReply();
};
"""+methods+r"""
int main(){
 RepeaterMonitor m;uint8_t admin[32]{1};strcpy(m.entries[0].name,"Chestnut Hill - FN31jf");strcpy(m.entries[1].learnedName,"Canoe Hill - FN31gd");strcpy(m.entries[2].name,"FlexSolar");
 assert(strstr(m.startAdminCheck(admin,"Hill"),"Multiple"));assert(!m.running&&!m.adminCheckPending);
 assert(strstr(m.startAdminCheck(admin,"unknown"),"No matching"));assert(strstr(m.startAdminCheck(admin,""),"Usage"));
 m.adminContacts.allowed=false;assert(m.startAdminCheck(admin,"Chestnut"));m.adminContacts.allowed=true;
 assert(!m.startAdminCheck(admin,"cHeStNuT"));assert(m.singleTarget==0&&m.running&&!m.automatic&&!strcmp(m.adminCheckName,"Chestnut Hill"));
 m.pollAdminCheckReply();assert(!m.mesh.sends);assert(strstr(m.startAdminCheck(admin,"Flex"),"busy"));
 m.running=false;strcpy(m.adminCheckReply,"Chestnut Hill 3.55V");m.mesh.busy=true;m.pollAdminCheckReply();assert(m.adminCheckPending&&!m.mesh.sends);
 m.mesh.busy=false;m.pollAdminCheckReply();assert(!m.adminCheckPending&&m.mesh.reply=="Chestnut Hill 3.55V");m.pollAdminCheckReply();assert(m.mesh.sends==1);
 assert(!m.startAdminCheck(admin,"Flex"));m.running=false;m.pollAdminCheckReply();assert(m.mesh.reply=="FlexSolar: check interrupted");
 m.syncOK=false;assert(m.startAdminCheck(admin,"Flex",true)&&!m.adminCheckPending);
 m.syncOK=true;assert(!m.startAdminCheck(admin,"Flex",true));assert(m.syncTarget==2&&m.adminCheckIsSync);
 m.pollAdminCheckReply();assert(m.mesh.sends==2);m.syncPhase=m.SyncIdle;strcpy(m.adminCheckReply,"FlexSolar: Successful sync");m.pollAdminCheckReply();assert(m.mesh.reply=="FlexSolar: Successful sync"&&m.mesh.sends==3);
 assert(!m.startAdminCheck(admin,"Canoe"));m.adminContacts.allowed=false;m.running=false;m.pollAdminCheckReply();assert(!m.adminCheckPending&&m.mesh.sends==3);
}
"""
with tempfile.TemporaryDirectory() as folder:
 d=Path(folder);(d/'test.cpp').write_text(code);exe=d/'test.exe'
 subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-I',str(src),str(d/'test.cpp'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: unique case-insensitive name matching, ambiguous/missing names, permission/busy gates, delayed DM and interruption')
