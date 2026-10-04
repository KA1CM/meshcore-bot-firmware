from pathlib import Path
import os, subprocess, tempfile
root=Path(__file__).resolve().parents[2];src=root/'vendor/MeshCore/examples/companion_radio'
s=(src/'RepeaterMonitor.cpp').read_text(encoding='utf-8')
method=s[s.index('const char* RepeaterMonitor::adminNotes('):s.index('const char* RepeaterMonitor::adminEditRepeater(')]
harness=r"""
#include "RepeaterMonitorCore.h"
#include "BotVoltageList.h"
#include "FirmwareBot.h"
#include "BotCommandRegistry.h"
#include <memory>
#include <cassert>
#include <strings.h>
using namespace MonitorCore;
struct BotAdminContacts {enum{Commands=1};bool allowed=true;bool allows(const uint8_t*,int){return allowed;}};
struct RepeaterMonitor {
 BotAdminContacts adminContacts;Entry entries[MAX_REPEATERS];size_t count=2;
 bool storageOK=true,adminCheckPending=false,occupied=false,saveOK=true;bool adminConfirmed[MAX_REPEATERS]{};
 int syncTarget=-1,active=-1,singleTarget=-1,protectedCount=0,saves=0;std::string syncResult,lastError;
 bool busy(){return occupied;}bool save(){++saves;return saveOK;}void protectListedContacts(){++protectedCount;}
 struct {bool ok=true;int calls=0;bool retain(Entry*,size_t){++calls;return ok;}}credentials;
 struct Mesh {struct Contact{char name[33]{};};Contact* lookupContactByPubKey(const uint8_t*,int){return nullptr;}}mesh;
 const char* adminNotes(const uint8_t*,const char*,BotVoltageList::Snapshot&);
};
"""+method+r"""
int main(){
 RepeaterMonitor m;uint8_t admin[32]{};BotVoltageList::Snapshot out;
 m.entries[0].key[0]=1;m.entries[1].key[0]=2;
 strcpy(m.entries[0].name,"Chestnut Hill");strcpy(m.entries[1].name,"Canoe Hill");m.entries[0].notes="Keep notes";
 assert(strstr(m.adminNotes(admin,"Hill",out),"Multiple"));assert(m.saves==0);
 assert(!m.adminNotes(admin,"chestnut",out));assert(out.count==2&&!strcmp(out.lines[1],"Keep notes"));
 assert(!m.adminNotes(admin,"0200",out));assert(!strcmp(out.lines[1],"No notes saved"));
 assert(strstr(m.adminNotes(admin,"set chestnut | Antenna: rooftop\nFirmware: test",out),"saved"));
 assert(m.entries[0].notes=="Antenna: rooftop\nFirmware: test");
 const auto previous=m.entries[0].notes;
 assert(strstr(m.adminNotes(admin,"set chestnut",out),"Usage"));
 assert(strstr(m.adminNotes(admin,"set chestnut |",out),"required"));assert(m.entries[0].notes==previous);
 m.adminContacts.allowed=false;assert(strstr(m.adminNotes(admin,"set chestnut | bad",out),"authorized"));m.adminContacts.allowed=true;
 m.occupied=true;assert(strstr(m.adminNotes(admin,"set chestnut | bad",out),"busy"));m.occupied=false;
 m.saveOK=false;assert(strstr(m.adminNotes(admin,"set chestnut | bad",out),"not applied"));assert(m.entries[0].notes==previous);m.saveOK=true;
 std::string tooLong="set chestnut | "+std::string(513,'x');assert(strstr(m.adminNotes(admin,tooLong.c_str(),out),"Invalid"));
 assert(strstr(m.adminNotes(admin,"missing",out),"No matching"));
 std::string unicode;for(int i=0;i<512;++i)unicode+="\xf0\x9f\x93\xa1";m.entries[0].notes=unicode;
 assert(!m.adminNotes(admin,"chestnut",out));assert(out.count<=40);
 std::string joined;for(size_t i=1;i<out.count;++i){assert(validNotes(out.lines[i],strlen(out.lines[i])));joined+=out.lines[i];}assert(joined==unicode);
 size_t next=0;unsigned part=1;while(next<out.count){char page[121];size_t old=next;assert(BotVoltageList::page(out,next,part++,page,sizeof(page)));assert(next>old&&strlen(page)<=120);}
 BotCommand command{};const char* input="notes set Chestnut | two  spaces\nnext line";
 assert(FirmwareBot::parseCommand(input,strlen(input),&command,true));assert(command.id==BOT_COMMAND_NOTES);
 assert(!strcmp(command.args,"set Chestnut | two  spaces\nnext line"));
 std::string longDM="notes set Chestnut | "+std::string(110,'x');assert(FirmwareBot::parseCommand(longDM.c_str(),longDM.size(),&command,true));assert(command.args_len==longDM.size()-6);
 assert(BotCommandRegistry::findById(BOT_COMMAND_NOTES)->visibility==BOT_COMMAND_VISIBILITY_HIDDEN);

}
"""
with tempfile.TemporaryDirectory() as temp:
 p=Path(temp);(p/'test.cpp').write_text(harness,encoding='utf-8');exe=p/'test.exe'
 subprocess.run([os.environ.get('CXX','c++'),'-std=c++11','-Wall','-Wextra','-Werror','-Wno-unused-function','-I',str(src),str(p/'test.cpp'),*[str(src/n) for n in ['FirmwareBot.cpp','BotCommandRegistry.cpp']],'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: notes matching, authorization, replacement, rollback, UTF-8 paging and lossless DM parsing')
