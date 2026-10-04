from pathlib import Path
import os, subprocess, tempfile
root=Path(__file__).resolve().parents[2];src=root/'vendor/MeshCore/examples/companion_radio'
s=(src/'RepeaterMonitor.cpp').read_text(encoding='utf-8')
method=s[s.index('const char* RepeaterMonitor::adminPassword('):s.index('const char* RepeaterMonitor::adminNotes(')]
existing=Path(__file__).with_name('test_monitor_credentials.py').read_text(encoding='utf-8')
mock=existing.split('mock = r"""',1)[1].split('"""',1)[0]
harness=r"""
#include "MonitorCredentials.h"
#include "FirmwareBot.h"
#include "BotCommandRegistry.h"
#include <cassert>
#include <strings.h>
using namespace MonitorCore;
struct BotAdminContacts {enum{Commands=1};bool allowed=true;bool allows(const uint8_t*,int){return allowed;}};
struct RepeaterMonitor {
 BotAdminContacts adminContacts;Entry entries[MAX_REPEATERS];size_t count=2;
 bool storageOK=true,adminCheckPending=false,occupied=false;bool adminConfirmed[MAX_REPEATERS]{};
 MonitorCredentials credentials;
 bool busy(){return occupied;}
 struct Mesh {struct Contact{char name[33]{};};Contact* lookupContactByPubKey(const uint8_t*,int){return nullptr;}}mesh;
 const char* adminPassword(const uint8_t*,const char*);
};
"""+method+r"""
int main(){
 RepeaterMonitor m;uint8_t admin[32]{};m.entries[0].key[0]=1;m.entries[1].key[0]=2;
 strcpy(m.entries[0].name,"Chestnut Hill");strcpy(m.entries[1].name,"Canoe Hill");
 assert(m.credentials.begin(m.entries,m.count));
 assert(strstr(m.adminPassword(admin,"Chestnut | First!"),"saved"));
 assert(!strcmp(m.credentials.password(m.entries[0].key),"First!"));
 m.adminConfirmed[0]=true;
 assert(strstr(m.adminPassword(admin,"0100 | New  pass|!"),"saved"));
 assert(!strcmp(m.credentials.password(m.entries[0].key),"New  pass|!"));assert(!m.adminConfirmed[0]);
 const std::string previous=m.credentials.password(m.entries[0].key);
 assert(strstr(m.adminPassword(admin,"Hill | bad"),"Multiple"));
 assert(strstr(m.adminPassword(admin,"unknown | bad"),"No matching"));
 assert(strstr(m.adminPassword(admin,"Chestnut"),"Usage"));
 assert(strstr(m.adminPassword(admin," | bad"),"Usage"));
 assert(strstr(m.adminPassword(admin,"Chestnut |"),"1-15"));
 assert(strstr(m.adminPassword(admin,"Chestnut | 1234567890123456"),"1-15"));
 assert(strstr(m.adminPassword(admin,"Chestnut | bad\npass"),"control"));
 m.adminContacts.allowed=false;assert(strstr(m.adminPassword(admin,"Chestnut | bad"),"authorized"));m.adminContacts.allowed=true;
 m.occupied=true;assert(strstr(m.adminPassword(admin,"Chestnut | bad"),"busy"));m.occupied=false;
 m.adminCheckPending=true;assert(strstr(m.adminPassword(admin,"Chestnut | bad"),"busy"));m.adminCheckPending=false;
 m.storageOK=false;assert(strstr(m.adminPassword(admin,"Chestnut | bad"),"storage"));m.storageOK=true;
 Preferences::fail=true;m.adminConfirmed[0]=true;
 assert(strstr(m.adminPassword(admin,"Chestnut | bad"),"not applied"));
 assert(previous==m.credentials.password(m.entries[0].key));assert(m.adminConfirmed[0]);Preferences::fail=false;
 m.entries[1].enabled=false;assert(strstr(m.adminPassword(admin,"Canoe | 123456789012345"),"saved"));
 MonitorCredentials reload;assert(reload.begin(m.entries,m.count));assert(previous==reload.password(m.entries[0].key));
 assert(!strcmp(reload.password(m.entries[1].key),"123456789012345"));
 BotCommand command{};const char* input="password Chestnut | a  b|c ";
 assert(FirmwareBot::parseCommand(input,strlen(input),&command,true));assert(command.id==BOT_COMMAND_PASSWORD);
 assert(!strcmp(command.args,"Chestnut | a  b|c "));
 assert(FirmwareBot::parseCommand("!password Canoe | Test!",22,&command,false));assert(command.id==BOT_COMMAND_PASSWORD);
 assert(BotCommandRegistry::findById(BOT_COMMAND_PASSWORD)->visibility==BOT_COMMAND_VISIBILITY_HIDDEN);
}
"""
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'Preferences.h').write_text(mock,encoding='utf-8');(p/'test.cpp').write_text(harness,encoding='utf-8');exe=p/'test.exe'
 subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror','-Wno-unused-function','-I',str(p),'-I',str(src),str(p/'test.cpp'),*[str(src/n) for n in ['FirmwareBot.cpp','BotCommandRegistry.cpp']],'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: password add/replace, persistent reload, save rollback, matching, permissions, busy gates, length/control validation and lossless parsing')
