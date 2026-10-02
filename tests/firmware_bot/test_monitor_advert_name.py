from pathlib import Path
import os,subprocess,tempfile
root=Path(__file__).resolve().parents[2]
s=(root/'vendor/MeshCore/examples/companion_radio/MyMesh.cpp').read_text()
method=s[s.index('bool MyMesh::restoreMonitorContactName('):s.index('\n#endif',s.index('bool MyMesh::restoreMonitorContactName('))]
harness=r"""
#include <cstdint>
#include <cstring>
#include <cassert>
#define PUB_KEY_SIZE 32
#define SIGNATURE_SIZE 64
#define MAX_ADVERT_DATA_SIZE 64
#define PAYLOAD_TYPE_ADVERT 4
void strlcpy(char* d,const char* s,size_t n){strncpy(d,s,n-1);d[n-1]=0;}
bool validSignature=true;
namespace mesh {
struct Packet {uint8_t payload[200]{};size_t payload_len=0;uint8_t getPayloadType(){return 4;}bool readFrom(const uint8_t*,uint8_t);};
Packet fixture;
bool Packet::readFrom(const uint8_t*,uint8_t){*this=fixture;return true;}
}
struct Contact {int32_t gps_lat=0,gps_lon=0;struct Identity {bool verify(const uint8_t*,const uint8_t*,size_t){return validSignature;}} id;char name[32]{};uint32_t last_advert_timestamp=0,lastmod=0;};
struct Clock {uint32_t getCurrentTime(){return 100;}};
struct MyMesh {Contact contact;Clock clock;Contact* lookupContactByPubKey(const uint8_t*,int){return &contact;}uint8_t exportContact(const Contact&,uint8_t*){return 1;}Clock* getRTCClock(){return &clock;}bool restoreMonitorContactName(const uint8_t*);};
"""+method+r"""
int main(){
 uint8_t key[32]{};key[0]=1;auto& p=mesh::fixture;p.payload[0]=1;uint32_t stamp=50;memcpy(p.payload+32,&stamp,4);
 p.payload[100]=0x82;const char* name="North Stamford - FN31fd";memcpy(p.payload+101,name,strlen(name));p.payload_len=101+strlen(name);
 MyMesh m;strcpy(m.contact.name,"No<!");
 validSignature=false;assert(!m.restoreMonitorContactName(key));assert(!strcmp(m.contact.name,"No<!"));
 validSignature=true;m.contact.last_advert_timestamp=51;assert(!m.restoreMonitorContactName(key));
 m.contact.last_advert_timestamp=50;key[0]=2;assert(!m.restoreMonitorContactName(key));key[0]=1;
 assert(m.restoreMonitorContactName(key));assert(!strcmp(m.contact.name,name));assert(m.contact.lastmod==100);
 assert(!m.restoreMonitorContactName(key));
 // Recover coordinates even when the contact name already matches.
 p.payload[100]=0x92;int32_t lat=41150000,lon=-73332460;
 memcpy(p.payload+101,&lat,4);memcpy(p.payload+105,&lon,4);
 memcpy(p.payload+109,name,strlen(name));p.payload_len=109+strlen(name);
 validSignature=false;assert(!m.restoreMonitorContactName(key));assert(m.contact.gps_lat==0);
 validSignature=true;assert(m.restoreMonitorContactName(key));
 assert(m.contact.gps_lat==lat&&m.contact.gps_lon==lon);
 assert(!m.restoreMonitorContactName(key));
 lat=91000000;memcpy(p.payload+101,&lat,4);assert(!m.restoreMonitorContactName(key));
 assert(m.contact.gps_lat==41150000);
 strcpy(m.contact.name,"Keep this");p.payload[100]=0xf2;p.payload_len=102;assert(!m.restoreMonitorContactName(key));
 p.payload_len=200;assert(!m.restoreMonitorContactName(key));assert(!strcmp(m.contact.name,"Keep this"));
}
"""
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'test.cpp').write_text(harness);exe=p/'test.exe'
 subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',str(p/'test.cpp'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: advert name recovery rejects bad signatures, mismatched keys, stale adverts and malformed lengths')
