from pathlib import Path
import os, subprocess, tempfile
root=Path(__file__).resolve().parents[2];repo=root/'vendor/MeshCore';src=repo/'examples/companion_radio'
code=(src/'RepeaterMonitor.cpp').read_text();method=code[code.index('void RepeaterMonitor::exportState('):code.index('\nbool RepeaterMonitor::importState(')]
method+=code[code.index('bool RepeaterMonitor::importState('):code.index('bool RepeaterMonitor::readSlot(')]
method+=code[code.index('void RepeaterMonitor::rememberNames('):code.index('void RepeaterMonitor::prune(')]
harness=r'''
#include <ArduinoJson.h>
#include "RepeaterMonitorCore.h"
#include "RepeaterOrder.h"
#include <cassert>
#include <cstring>
#include <memory>
size_t strlcpy(char* d,const char* s,size_t n){size_t len=strlen(s);if(n){size_t k=len<n-1?len:n-1;memcpy(d,s,k);d[k]=0;}return len;}
using namespace MonitorCore;
struct Contact { int32_t gps_lat=0,gps_lon=0; const char* name="Learned repeater"; };
struct Mesh { Contact c; Contact* lookupContactByPubKey(const uint8_t* key,int) { return key[0]==1?&c:nullptr; } };
struct RepeaterMonitor { bool storageOK=true;int saves=0;bool save(){++saves;return true;}void rememberNames(); Mesh mesh; bool synced=false; Entry entries[3]{}; size_t count=3; uint32_t now(){return 0;} void exportState(JsonDocument&,bool,bool=true); bool importState(JsonDocument&,bool); };
'''+method+r'''
int main(){
 assert(validNotes("line\nline\t",10));
 assert(!validNotes("bad\0suffix",10));
 std::string unicode;for(int i=0;i<512;++i)unicode+="\xf0\x9f\xa4\x96";
 assert(validNotes(unicode.c_str(),unicode.size()));unicode+="x";
 assert(!validNotes(unicode.c_str(),unicode.size()));
 assert(!validNotes("\xc0\x80",2));assert(!validNotes("\xed\xa0\x80",3));
 RepeaterMonitor m;m.entries[0].key[0]=1;m.entries[1].key[0]=1;m.entries[2].key[0]=2;
 strcpy(m.entries[0].name,"Custom name");m.entries[0].lastSynced=2000000000;m.entries[0].clockCheckedAt=2000000001;m.entries[0].clockOffset=-12;m.entries[0].clockUncertainty=35;
 JsonDocument exported;m.exportState(exported,false);
 assert(exported["repeaters"][0]["password"].isNull());
 assert(exported["repeaters"][0]["passwordConfigured"].isNull());
 assert(strcmp(exported["repeaters"][0]["name"],"Learned repeater")==0);
 assert(strcmp(exported["repeaters"][1]["name"],"Learned repeater")==0);
 assert(strcmp(exported["repeaters"][2]["name"],"")==0);
 m.mesh.c.name="";
 JsonDocument fallback;m.exportState(fallback,false);
 assert(strcmp(fallback["repeaters"][0]["name"],"Custom name")==0);
 m.mesh.c.name="Learned repeater";
 JsonDocument stored;m.exportState(stored,true);
 assert(stored["repeaters"][0]["password"].isNull());
 assert(stored["repeaters"][0]["passwordConfigured"].isNull());
 assert(strcmp(stored["repeaters"][1]["name"],"")==0);
 assert(strcmp(stored["repeaters"][1]["displayName"],"Learned repeater")==0);
 assert(stored["repeaters"][0]["lastSynced"].as<uint32_t>()==2000000000);
 assert(exported["repeaters"][0]["lastSynced"].isNull());
 // Make the fixture keys unique for a real load; the name tests above use shared lookup prefixes.
 m.entries[1].key[0]=3;
 m.entries[0].learnedLatitude=41150000;m.entries[0].learnedLongitude=-73332460;
 strcpy(m.entries[0].notes,"Node: V4\nAntenna: test <tag>");
 JsonDocument snapshot;m.exportState(snapshot,true);
 RepeaterMonitor restored;assert(restored.importState(snapshot,true));
 assert(restored.entries[0].learnedLatitude==41150000&&restored.entries[0].learnedLongitude==-73332460);
 assert(restored.entries[0].lastSynced==2000000000&&restored.entries[1].lastSynced==0);
 assert(restored.entries[0].clockCheckedAt==2000000001&&restored.entries[0].clockOffset==-12&&restored.entries[0].clockUncertainty==35);
 assert(!strcmp(restored.entries[0].notes,"Node: V4\nAntenna: test <tag>"));
 JsonDocument notesExport;restored.exportState(notesExport,false);
 assert(!strcmp(notesExport["repeaters"][0]["notes"],restored.entries[0].notes));
 notesExport["repeaters"][0].remove("notes");
 assert(restored.importState(notesExport,false));assert(restored.entries[0].notes[0]);
 notesExport["repeaters"][0]["notes"]=42;
 assert(!restored.importState(notesExport,false));assert(restored.entries[0].notes[0]);
 notesExport["repeaters"][0]["notes"]="";
 assert(restored.importState(notesExport,false));assert(!restored.entries[0].notes[0]);
 assert(restored.importState(snapshot,true));
 JsonDocument edit;restored.exportState(edit,false);
 edit["repeaters"][0]["learnedLongitude"]=1000000;
 edit["repeaters"][0]["lastSynced"]=2100000000; // list import cannot forge sync history
 assert(restored.importState(edit,false));assert(restored.entries[0].lastSynced==2000000000);
 assert(restored.entries[0].learnedLongitude==-73332460);
 snapshot["repeaters"][0].remove("lastSynced");
 assert(restored.importState(snapshot,true));assert(restored.entries[0].lastSynced==0);

 // Simulate a restart with empty radio-contact names: monitor cache preserves them.
 assert(!strcmp(restored.entries[0].learnedName,"Learned repeater"));
 restored.mesh.c.name="";
 JsonDocument cached;restored.exportState(cached,false);
 assert(!strcmp(cached["repeaters"][0]["name"],"Learned repeater"));
 // Older monitor files only had displayName. Recover it without overwriting manual names.
 snapshot["repeaters"][0].remove("learnedName");
 assert(restored.importState(snapshot,true));
 assert(!strcmp(restored.entries[0].learnedName,"Learned repeater"));
 restored.mesh.c.name="New advertised name";
 JsonDocument fresh;restored.exportState(fresh,false);
 assert(!strcmp(fresh["repeaters"][0]["name"],"New advertised name"));
 snapshot["repeaters"][0]["syncAttemptAt"]=2000000001;
 snapshot["repeaters"][0]["syncAttemptResult"]="In progress";
 assert(restored.importState(snapshot,true));
 assert(restored.entries[0].syncAttemptAt==2000000001);
 assert(strstr(restored.entries[0].syncAttemptResult,"Interrupted"));
 JsonDocument completed;restored.exportState(completed,true);
 assert(strstr(completed["repeaters"][0]["syncAttemptResult"].as<const char*>(),"Interrupted"));
 snapshot["repeaters"][0]["lastSynced"]="invalid";assert(!restored.importState(snapshot,true));
 RepeaterMonitor learning;learning.count=1;learning.entries[0].key[0]=1;
 learning.mesh.c.gps_lat=41150000;learning.mesh.c.gps_lon=-73400000;learning.rememberNames();
 assert(learning.saves==1&&learning.entries[0].learnedLongitude==-73400000);
 learning.mesh.c.gps_lat=0;learning.mesh.c.gps_lon=0;learning.rememberNames();
 assert(learning.saves==1&&learning.entries[0].learnedLongitude==-73400000);
 JsonDocument learned;learning.exportState(learned,true,false);RepeaterMonitor reboot;
 assert(reboot.importState(learned,true)&&reboot.entries[0].learnedLongitude==-73400000);
 learned["repeaters"][0]["learnedLatitude"]=91000000;assert(!reboot.importState(learned,true));
 RepeaterMonitor ordered;ordered.entries[0].key[0]=2;ordered.entries[1].key[0]=1;ordered.entries[2].key[0]=3;
 ordered.mesh.c.gps_lat=41000000;ordered.mesh.c.gps_lon=-73000000;
 JsonDocument display;ordered.exportState(display,true);
 assert(strncmp(display["repeaters"][0]["key"].as<const char*>(),"01",2)==0);
 JsonDocument saved;ordered.exportState(saved,true,false);
 assert(strncmp(saved["repeaters"][0]["key"].as<const char*>(),"02",2)==0);
 assert(ordered.entries[0].key[0]==2); // display sorting cannot retarget an active operation


}
'''
with tempfile.TemporaryDirectory() as temp:
 p=Path(temp);cpp=p/'export.cpp';cpp.write_text(harness);exe=p/'export.exe'
 subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-I',str(src),'-I',str(repo/'.pio/libdeps/heltec_v4_companion_radio_usb/ArduinoJson/src'),str(cpp),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: learned-name priority, manual fallback, unknown contacts and unchanged stored names')
