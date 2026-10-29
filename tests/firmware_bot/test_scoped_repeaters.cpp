#include "BotScopedRepeaters.h"
#include <cassert>
int main() {
  BotScopedRepeaters list;
  uint8_t path[]={0xab,0xcd,0x01,0x12,0x34,0x02,0xab,0xcd,0x03};
  list.observe(path,3,3,20000);
  assert(list.data.count==2);
  assert(list.data.entries[0].hash[0]==0xab && list.data.entries[0].hash[1]==0xcd);
  uint8_t shortPath[]={0xab,0xcd};list.observe(shortPath,1,2,20010);
  assert(list.data.count==2 && list.data.entries[0].lastDay==20010);
  list.prune(20029);assert(list.data.count==2);
  list.prune(20030);assert(list.data.count==1);
  list.prune(20040);assert(list.data.count==0);
  list.observe(path,3,1,20040);assert(list.data.count==0);
  list.observe(path,22,3,20040);assert(list.data.count==0);
  for(unsigned i=0;i<256;++i) {
    uint8_t hash[]={static_cast<uint8_t>(i),0};list.observe(hash,1,2,20040);
  }
  assert(list.data.count==256);
  uint8_t newest[]={0xff,0xff};list.observe(newest,1,2,20041);
  assert(list.data.count==256);
  bool found=false;
  for(size_t i=0;i<list.data.count;++i)
    if(list.data.entries[i].hash[0]==0xff && list.data.entries[i].hash[1]==0xff)
      {found=true;assert(list.data.entries[i].lastDay==20041);}
  assert(found);
}
