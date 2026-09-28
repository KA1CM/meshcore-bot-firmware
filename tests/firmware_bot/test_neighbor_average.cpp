#include "BotTypes.h"
#include <cassert>
int main() {
 BotNeighbor n{};
 n.addSignalSample(-100,19);assert(n.rssi_dbm==-100 && n.snr_quarters==19 && n.sample_count==1);
 n.addSignalSample(-90,21);assert(n.rssi_dbm==-95 && n.snr_quarters==20);
 n=BotNeighbor{};n.addSignalSample(-100,-19);n.addSignalSample(-101,-20);
 assert(n.rssi_dbm==-101 && n.snr_quarters==-20);
 n=BotNeighbor{};
 for(int i=0;i<16;++i)n.addSignalSample(-100,20);
 n.addSignalSample(-84,4);assert(n.sample_count==16 && n.rssi_dbm==-99 && n.snr_quarters==19);
 for(int i=0;i<15;++i)n.addSignalSample(-84,4);
 assert(n.rssi_dbm==-84 && n.snr_quarters==4 && n.sample_count==16);
 for(int i=0;i<10000;++i)n.addSignalSample(-32768,-128);
 assert(n.rssi_dbm==-32768 && n.snr_quarters==-128);
 n=BotNeighbor{};n.addSignalSample(32767,127);assert(n.rssi_dbm==32767 && n.snr_quarters==127 && n.sample_count==1);
}
