from pathlib import Path
import os,subprocess,tempfile
src=Path(__file__).resolve().parents[2]/'vendor/MeshCore/examples/companion_radio'
s=(src/'MyMesh.cpp').read_text(encoding='utf-8')
method=s[s.index('BotCommandResult MyMesh::executeBotNeighborsCommand('):s.index('bool MyMesh::enqueueEmergencyForward(')]
code=r"""
#include "BotTypes.h"
#include "BotVoltageList.h"
#include <cassert>
#include <string>
namespace FirmwareBot {size_t maxResponseLenForChannel(BotChannelKind){return 120;}}
BotCommandResult botCommandResult(BotCommandResultCode c,size_t n){return {c,n};}
BotCommandResult botWriteText(char* o,size_t n,const char* t){snprintf(o,n,"%s",t);return {BOT_COMMAND_RESULT_OK,strlen(o)};}
void botFormatQuarters(int q,char* o,size_t n){snprintf(o,n,"%.2f",q/4.0);}
struct ContactInfo {char name[33]{};};
struct MyMesh {
 BotNeighbor bot_neighbors[BOT_NEIGHBOR_SLOTS]{};
 ContactInfo* lookupContactByPubKey(const uint8_t*,size_t){return nullptr;}
 BotCommandResult executeBotNeighborsCommand(const BotMessage&,char*,size_t,BotVoltageList::Snapshot*);
};
"""+method+r"""
int main(){
 MyMesh m;BotMessage msg{};char unused[1];BotVoltageList::Snapshot snapshot;
 for(int i=0;i<BOT_NEIGHBOR_SLOTS;++i){auto& n=m.bot_neighbors[i];n.active=true;n.pub_key_prefix[0]=i;n.snr_quarters=i-8;n.rssi_dbm=-100;}
 m.executeBotNeighborsCommand(msg,unused,sizeof(unused),&snapshot);
 assert(snapshot.count==BOT_NEIGHBOR_SLOTS);
 for(int i=0;i<BOT_NEIGHBOR_SLOTS;++i){char prefix[9];snprintf(prefix,sizeof(prefix),"%02x000000",BOT_NEIGHBOR_SLOTS-1-i);assert(!strncmp(snapshot.lines[i],prefix,8));}
 size_t next=0;unsigned part=1;char page[121];std::string all;
 while(BotVoltageList::page(snapshot,next,part++,page,sizeof(page))){assert(strlen(page)<=120);all+=page;all+='\n';}
 assert(next==BOT_NEIGHBOR_SLOTS&&part>2);
 m.bot_neighbors[0].sample_count=16;m.bot_neighbors[1].sample_count=16;
 m.executeBotNeighborsCommand(msg,unused,sizeof(unused),&snapshot);
 assert(!strncmp(snapshot.lines[0],"01000000",8));assert(!strncmp(snapshot.lines[1],"00000000",8));
 // Equal samples and SNR are ordered by recency.
 m.bot_neighbors[0].snr_quarters=m.bot_neighbors[1].snr_quarters;m.bot_neighbors[0].last_heard_millis=100;
 m.executeBotNeighborsCommand(msg,unused,sizeof(unused),&snapshot);assert(!strncmp(snapshot.lines[0],"00000000",8));
 for(auto& n:m.bot_neighbors)n.active=false;
 char empty[121];m.executeBotNeighborsCommand(msg,empty,sizeof(empty),&snapshot);assert(!snapshot.count&&!strcmp(empty,"No repeaters heard directly"));
}
"""
with tempfile.TemporaryDirectory() as folder:
 d=Path(folder);(d/'test.cpp').write_text(code);exe=d/'test.exe'
 subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-I',str(src),str(d/'test.cpp'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: all 16 neighbors retained, SNR descending, bounded numbered pages, empty list')
