from pathlib import Path
import os, subprocess, tempfile
root=Path(__file__).resolve().parents[2];src=root/'vendor/MeshCore/examples/companion_radio'
s=(src/'RepeaterMonitor.cpp').read_text(encoding='utf-8')
method=s[s.index('const char* RepeaterMonitor::adminNotes('):s.index('const char* RepeaterMonitor::adminEditRepeater(')]
receive=(src/'MyMesh.cpp').read_text(encoding='utf-8')
receive=receive[receive.index('  const size_t textLength = botBoundedStrLen'):receive.index('  recordBotObservation(message, &from, 0xFF);')]
harness=r"""
#include "RepeaterMonitorCore.h"
#include "BotNoteFields.h"
#include "BotVoltageList.h"
#include "FirmwareBot.h"
#include "BotCommandRegistry.h"
#include <memory>
#include <cassert>
#include <strings.h>
using namespace MonitorCore;
struct BotAdminContacts {enum{Commands=1};bool allowed=true;bool allows(const uint8_t*,int){return allowed;}};
struct RepeaterMonitor {
 BotAdminContacts adminContacts;Entry entries[MAX_REPEATERS];size_t count=2;char adminEditReply[128]{};
 bool storageOK=true,adminCheckPending=false,occupied=false,saveOK=true;bool adminConfirmed[MAX_REPEATERS]{};
 int syncTarget=-1,active=-1,singleTarget=-1,protectedCount=0,saves=0;std::string syncResult,lastError;
 bool busy(){return occupied;}bool save(){++saves;return saveOK;}void protectListedContacts(){++protectedCount;}
 struct {bool ok=true;int calls=0;bool retain(Entry*,size_t){++calls;return ok;}}credentials;
 struct Mesh {struct Contact{char name[33]{};};Contact* lookupContactByPubKey(const uint8_t*,int){return nullptr;}}mesh;
 const char* adminNotes(const uint8_t*,const char*,BotVoltageList::Snapshot&);
};
"""+method+r"""
static size_t botBoundedStrLen(const char* text,size_t limit){return text ? strnlen(text,limit) : 0;}
static BotMessage receiveDM(const char* text){BotMessage message{};
"""+receive+r"""
return message;
}
"""+r"""
int main(){
 RepeaterMonitor m;uint8_t admin[32]{};BotVoltageList::Snapshot out;
 m.entries[0].key[0]=1;m.entries[1].key[0]=2;
 strcpy(m.entries[0].name,"Chestnut Hill");strcpy(m.entries[1].name,"Canoe Hill");m.entries[0].notes="Keep notes";
 assert(strstr(m.adminNotes(admin,"Hill",out),"Multiple"));assert(m.saves==0);
 assert(!m.adminNotes(admin,"chestnut",out));assert(out.count==2&&!strcmp(out.lines[1],"Keep notes"));
 assert(!m.adminNotes(admin,"0200",out));assert(!strcmp(out.lines[1],"No notes saved"));
 assert(!strcmp(m.adminNotes(admin,"set chestnut | Antenna: rooftop\nFirmware: test",out),"Chestnut Hill notes saved"));
 assert(m.entries[0].notes=="Antenna: rooftop\nFirmware: test");
 m.entries[0].notes="Enclosure: CoreBell\nAntenna: old\nBoard: v4\nFirmware: test\nRXPS: M";
 assert(strstr(m.adminNotes(admin,"set chestnut | antenna | Alpha-915",out),"saved"));
 assert(m.entries[0].notes=="Enclosure: CoreBell\nAntenna: Alpha-915\nBoard: v4\nFirmware: test\nRXPS: M");
 assert(strstr(m.adminNotes(admin,"set chestnut | rXpS | B",out),"saved"));
 assert(m.entries[0].notes.find("RXPS: B")!=std::string::npos);
 const auto previous=m.entries[0].notes;
 assert(strstr(m.adminNotes(admin,"set chestnut | wrong | bad",out),"Unknown field"));assert(m.entries[0].notes==previous);
 assert(strstr(m.adminNotes(admin,"set chestnut | antenna | bad\nvalue",out),"one line"));assert(m.entries[0].notes==previous);

 assert(strstr(m.adminNotes(admin,"set chestnut",out),"Usage"));
 assert(strstr(m.adminNotes(admin,"set chestnut |",out),"required"));assert(m.entries[0].notes==previous);
 m.adminContacts.allowed=false;assert(strstr(m.adminNotes(admin,"set chestnut | bad",out),"authorized"));m.adminContacts.allowed=true;
 m.occupied=true;assert(strstr(m.adminNotes(admin,"set chestnut | bad",out),"busy"));m.occupied=false;
 m.saveOK=false;assert(strstr(m.adminNotes(admin,"set chestnut | bad",out),"not applied"));assert(m.entries[0].notes==previous);m.saveOK=true;
 const auto fieldBefore=m.entries[0].notes;m.saveOK=false;
 assert(strstr(m.adminNotes(admin,"set chestnut | rxps | X",out),"not applied"));assert(m.entries[0].notes==fieldBefore);m.saveOK=true;
 std::string edited;
 assert(!BotNoteFields::edit("Antenna: A\nBoard: B","enclosure | CoreBell",edited));assert(edited=="Enclosure: CoreBell\nAntenna: A\nBoard: B");
 assert(!BotNoteFields::edit("Enclosure: C","firmware | test",edited));assert(edited=="Enclosure: C\nFirmware: test");
 assert(!BotNoteFields::edit("RXPS: M\nBoard: v4","rxps |",edited));assert(edited=="RXPS:\nBoard: v4");
 assert(!BotNoteFields::edit("RXPS: M\r\nBoard: v4","rxps | B",edited));assert(edited=="RXPS: B\r\nBoard: v4");
 assert(BotNoteFields::edit("RXPS: M\nrxps: B","rxps | X",edited));
 std::string tooLong="set chestnut | "+std::string(513,'x');assert(strstr(m.adminNotes(admin,tooLong.c_str(),out),"Invalid"));
 assert(strstr(m.adminNotes(admin,"missing",out),"No matching"));

 m.entries[0].notes="CoreBell\nAntenna: Sleeve Dipole\nBoard: 114\nFirmware: PS17.1.3\nRXPS: B";
 assert(!m.adminNotes(admin,"chestnut",out));
 size_t cursor=0;char single[145];assert(BotVoltageList::page(out,cursor,1,single,sizeof(single),true));
 assert(cursor==out.count);assert(std::string(single)=="1/1\nChestnut Hill notes:\n"+m.entries[0].notes);
 m.entries[0].notes="line one\n\nline three\n";
 assert(!m.adminNotes(admin,"chestnut",out));cursor=0;
 assert(BotVoltageList::page(out,cursor,1,single,sizeof(single),true));
 assert(std::string(single)=="1/1\nChestnut Hill notes:\n"+m.entries[0].notes);
 std::string unicode;for(int i=0;i<512;++i)unicode+="\xf0\x9f\x93\xa1";m.entries[0].notes=unicode;
 assert(!m.adminNotes(admin,"chestnut",out));assert(out.count<=40);
 std::string joined;for(size_t i=1;i<out.count;++i){assert(validNotes(out.lines[i],strlen(out.lines[i])));joined+=out.lines[i];}assert(joined==unicode);
 size_t next=0;unsigned part=1;while(next<out.count){char page[121];size_t old=next;assert(BotVoltageList::page(out,next,part++,page,sizeof(page),true));assert(next>old&&strlen(page)<=120);}
 BotCommand command{};const char* input="notes set Chestnut | two  spaces\nnext line";
 auto received=receiveDM(input);
 assert(!received.text_truncated);
 assert(FirmwareBot::parseCommand(received.text,received.text_len,&command,true));assert(command.id==BOT_COMMAND_NOTES);
 assert(!strcmp(command.args,"set Chestnut | two  spaces\nnext line"));
 assert(!strcmp(m.adminNotes(admin,command.args,out),"Chestnut Hill notes saved"));
 assert(m.entries[0].notes=="two  spaces\nnext line");
 assert(!m.adminNotes(admin,"chestnut",out));cursor=0;
 assert(BotVoltageList::page(out,cursor,1,single,sizeof(single),true));
 assert(std::string(single)=="1/1\nChestnut Hill notes:\ntwo  spaces\nnext line");
 auto oversized=receiveDM(std::string(BOT_MAX_TEXT_LEN+1,'x').c_str());
 assert(oversized.text_truncated&&oversized.text_len==BOT_MAX_TEXT_LEN&&oversized.text[BOT_MAX_TEXT_LEN]==0);
 std::string longDM="notes set Chestnut | "+std::string(110,'x');assert(FirmwareBot::parseCommand(longDM.c_str(),longDM.size(),&command,true));assert(command.args_len==longDM.size()-6);
 assert(BotCommandRegistry::findById(BOT_COMMAND_NOTES)->visibility==BOT_COMMAND_VISIBILITY_HIDDEN);

}
"""
with tempfile.TemporaryDirectory() as temp:
 p=Path(temp);(p/'test.cpp').write_text(harness,encoding='utf-8');exe=p/'test.exe'
 subprocess.run([os.environ.get('CXX','c++'),'-std=c++11','-Wall','-Wextra','-Werror','-Wno-unused-function','-I',str(src),str(p/'test.cpp'),*[str(src/n) for n in ['FirmwareBot.cpp','BotCommandRegistry.cpp']],'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: notes matching, authorization, replacement, rollback, UTF-8 paging and lossless DM parsing')
