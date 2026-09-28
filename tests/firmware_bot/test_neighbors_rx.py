from pathlib import Path
import os, subprocess,tempfile
root=Path(__file__).resolve().parents[2]
code=(root/'vendor/MeshCore/examples/companion_radio/MyMesh.cpp').read_text()
method=code[code.index('void MyMesh::logRx('):code.index('void MyMesh::logRxRaw(')]
harness=r'''
#include <cassert>
#include <cstdint>
#include <cstring>
#include <vector>
#define CMESH_BOT_ENABLED 1
#define PUB_KEY_SIZE 32
#define ADV_TYPE_REPEATER 2
namespace mesh {struct Packet {
 uint16_t path_len=2;uint8_t path[64]={9,1};bool flood=true;float snr=4.75;
 bool isRouteFlood(){return flood;}
 static bool isValidPathLen(uint8_t n){return (n>>6)!=3 && (n&63)*((n>>6)+1)<=64;}
 uint8_t getPathHashSize(){return (path_len>>6)+1;}
 uint8_t getPathHashCount(){return path_len&63;}
 float getSNR(){return snr;}
};}
struct ContactInfo { struct {uint8_t pub_key[32]{};} id;uint8_t type=2;};
struct Radio {float getLastRSSI(){return -100;}} radio_driver;
struct MyMesh;
struct ContactsIterator {size_t i=0;bool hasNext(MyMesh*,ContactInfo&);};
struct MyMesh {
 std::vector<ContactInfo> contacts;int seen=0;uint8_t key=0;int16_t rssi=0;int8_t snr=0;
 void recordBotNeighbor(const uint8_t* k,int16_t r,int8_t s){++seen;key=k[0];rssi=r;snr=s;}
 void logRx(mesh::Packet*,int,float);
};
bool ContactsIterator::hasNext(MyMesh* m,ContactInfo& c){if(i>=m->contacts.size())return false;c=m->contacts[i++];return true;}
'''+method+r'''
int main(){
 MyMesh m;ContactInfo a;a.id.pub_key[0]=1;a.id.pub_key[1]=2;m.contacts.push_back(a);
 mesh::Packet p;m.logRx(&p,10,0);assert(m.seen==1 && m.key==1 && m.rssi==-100 && m.snr==19);
 m.logRx(&p,10,0);assert(m.seen==2); // Repeated receptions refresh the neighbor.
 p.flood=false;m.logRx(&p,10,0);assert(m.seen==2);
 p.flood=true;p.path_len=0;m.logRx(&p,10,0);assert(m.seen==2);
 p.path_len=2;p.path[1]=8;m.logRx(&p,10,0);assert(m.seen==2);
 p.path[1]=1;m.contacts.push_back(a);m.logRx(&p,10,0);assert(m.seen==2);
 m.contacts.pop_back();m.contacts[0].type=1;m.logRx(&p,10,0);assert(m.seen==2);
 m.contacts[0].type=2;p.path_len=65;p.path[0]=1;p.path[1]=2;m.logRx(&p,10,0);assert(m.seen==3);
 p.path_len=129;p.path[2]=p.path[3]=0;m.logRx(&p,10,0);assert(m.seen==4);
 p.path_len=255;m.logRx(&p,10,0);p.path_len=256;m.logRx(&p,10,0);m.logRx(nullptr,10,0);assert(m.seen==4);
}
'''
with tempfile.TemporaryDirectory() as temp:
 p=Path(temp);cpp=p/'neighbors.cpp';cpp.write_text(harness);exe=p/'neighbors.exe'
 subprocess.run([os.environ.get('CXX','c++'),'-std=c++17',str(cpp),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: last-hop selection, signal metrics, repeats, 1/2/3-byte hashes, direct/empty/invalid paths, unknown/ambiguous/non-repeater contacts')
