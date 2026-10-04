from pathlib import Path
import os, subprocess, tempfile
root=Path(__file__).resolve().parents[2];src=root/'vendor/MeshCore/examples/companion_radio'
s=(src/'RepeaterMonitor.cpp').read_text(encoding='utf-8')
method=s[s.index('const char* RepeaterMonitor::adminEditRepeater('):s.index('const char* RepeaterMonitor::startAdminCheck(')]
harness=r"""
#include "RepeaterMonitorCore.h"
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
 const char* adminEditRepeater(const uint8_t*,const char*,const char*);
};
"""+method+r"""
int main(){
 RepeaterMonitor m;uint8_t admin[32]{};m.entries[0].key[0]=1;m.entries[1].key[0]=2;
 strcpy(m.entries[0].name,"Chestnut Hill");strcpy(m.entries[1].name,"Canoe Hill");m.entries[0].notes="Keep notes";
 assert(strstr(m.adminEditRepeater(admin,"disable","Hill"),"Multiple"));assert(m.saves==0);
 assert(strstr(m.adminEditRepeater(admin,"disable","chestnut"),"disabled"));assert(!m.entries[0].enabled&&m.entries[0].notes=="Keep notes");
 assert(strstr(m.adminEditRepeater(admin,"enable","chestnut"),"enabled"));assert(m.entries[0].enabled);
 m.adminContacts.allowed=false;assert(strstr(m.adminEditRepeater(admin,"remove","Canoe"),"authorized"));assert(m.count==2);m.adminContacts.allowed=true;
 m.occupied=true;assert(strstr(m.adminEditRepeater(admin,"remove","Canoe"),"busy"));m.occupied=false;
 m.saveOK=false;assert(strstr(m.adminEditRepeater(admin,"remove","Chestnut"),"not applied"));assert(m.count==2&&m.entries[0].notes=="Keep notes");m.saveOK=true;
 assert(strstr(m.adminEditRepeater(admin,"remove","Canoe"),"removed"));assert(m.count==1&&m.credentials.calls==1);
 char key[65];uint8_t newkey[32]{};newkey[0]=3;formatKey(newkey,key);
 assert(strstr(m.adminEditRepeater(admin,"add",key),"added"));assert(m.count==2&&m.entries[1].enabled&&m.protectedCount==1);
 assert(strstr(m.adminEditRepeater(admin,"add",key),"already"));assert(m.count==2);
 assert(strstr(m.adminEditRepeater(admin,"disable","0300"),"disabled"));assert(!m.entries[1].enabled);
 assert(strstr(m.adminEditRepeater(admin,"add","bad"),"64-digit"));
 assert(strstr(m.adminEditRepeater(admin,"add","0000000000000000000000000000000000000000000000000000000000000000"),"64-digit"));
 assert(strstr(m.adminEditRepeater(admin,"remove",""),"Usage"));
 assert(strstr(m.adminEditRepeater(admin,"remove","unknown"),"No matching"));
 m.saveOK=false;newkey[0]=4;formatKey(newkey,key);assert(strstr(m.adminEditRepeater(admin,"add",key),"not applied"));assert(m.count==2);
 m.saveOK=true;m.count=MAX_REPEATERS;assert(strstr(m.adminEditRepeater(admin,"add",key),"full"));
}
"""
with tempfile.TemporaryDirectory() as temp:
 p=Path(temp);(p/'test.cpp').write_text(harness,encoding='utf-8');exe=p/'test.exe'
 subprocess.run([os.environ.get('CXX','c++'),'-std=c++11','-Wall','-Wextra','-Werror','-I',str(src),str(p/'test.cpp'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: admin list edits, matching, permission/busy gates, duplicate/full/invalid keys, notes preservation and save rollback')
