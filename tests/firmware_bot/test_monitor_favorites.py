from pathlib import Path
import subprocess,os,tempfile
root=Path(__file__).resolve().parents[2];src=root/'vendor/MeshCore/examples/companion_radio'
code=(src/'RepeaterMonitor.cpp').read_text();method=code[code.index('void RepeaterMonitor::protectListedContacts()'):code.index('ContactInfo* RepeaterMonitor::contact()')]
begin=code[code.index('void RepeaterMonitor::begin()'):code.index('bool RepeaterMonitor::startRun(')]
assert begin.index('load();') < begin.index('protectListedContacts();')
assert 'protectListedContacts();' in code.split('server.on("/api/list", HTTP_POST')[1].split('server.on("/api/check"')[0]
harness=r'''
#include <cstring>
#include <cstdint>
#include <string>
#include <vector>
#include <cassert>
#define ADV_TYPE_REPEATER 2
#define OUT_PATH_UNKNOWN 255
void strlcpy(char* d,const char* s,size_t n){strncpy(d,s,n-1);d[n-1]=0;}
struct ContactInfo { struct {uint8_t pub_key[32]{};} id; uint8_t type=2,flags=0,out_path_len=0;uint32_t lastmod=0;char name[32]{}; };
struct Entry {uint8_t key[32]{};char name[33]{},learnedName[33]{};bool enabled=false;};
struct Clock {uint32_t getCurrentTime(){return 1234;}};
struct Mesh {std::vector<ContactInfo> contacts;Clock clock;int saves=0;
 Clock* getRTCClock(){return &clock;}
 ContactInfo* lookupContactByPubKey(const uint8_t* k,int){for(auto& c:contacts)if(!memcmp(c.id.pub_key,k,32))return &c;return nullptr;}
 bool addContact(const ContactInfo& c){if(contacts.size()<2){contacts.push_back(c);return true;}for(auto& x:contacts)if(!(x.flags&1)){x=c;return true;}return false;}
 void saveMonitorContacts(){++saves;}
};
struct RepeaterMonitor {Mesh mesh;Entry entries[2];size_t count=2;std::string lastError;void protectListedContacts();};
'''+method+r'''
int main(){
 RepeaterMonitor m;m.entries[0].key[0]=1;m.entries[1].key[0]=2;
 ContactInfo listed;listed.id.pub_key[0]=2;listed.flags=4;strcpy(listed.name,"Learned");listed.out_path_len=3;
 ContactInfo other;other.id.pub_key[0]=9;m.mesh.contacts={listed,other};
 m.protectListedContacts();auto* c=m.mesh.lookupContactByPubKey(m.entries[1].key,32);
 assert(c && c->flags==5 && c->out_path_len==3 && !strcmp(c->name,"Learned"));
 assert(m.mesh.lookupContactByPubKey(m.entries[0].key,32)->flags==1);
 assert(m.mesh.saves==1 && m.lastError.empty());
 m.protectListedContacts();assert(m.mesh.saves==1);
 RepeaterMonitor full;full.entries[0].key[0]=1;full.count=1;listed.flags=1;other.flags=1;full.mesh.contacts={listed,other};
 full.protectListedContacts();assert(!full.lastError.empty());assert(full.mesh.saves==0);assert(full.mesh.contacts[0].id.pub_key[0]==2);
}
'''
with tempfile.TemporaryDirectory() as temp:
 p=Path(temp);cpp=p/'favorites.cpp';cpp.write_text(harness);exe=p/'favorites.exe'
 subprocess.run([os.environ.get('CXX','c++'),'-std=c++17',str(cpp),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: disabled members protected, flags/names/routes preserved, safe add ordering, persisted changes, full-favorites handling')
