#include "RepeaterMonitorCore.h"
#include <cassert>
#include <cstring>
using namespace MonitorCore;
int main(){
 uint8_t reply[64]{};uint32_t remote=1790600010;memcpy(reply,&remote,4);int64_t offset=0;uint32_t uncertainty=0;
 assert(loginClock(reply,16,1790600000,4000,offset,uncertainty));assert(offset==8 && uncertainty==3);
 remote=1790599950;memcpy(reply,&remote,4);assert(loginClock(reply,13,1790600000,2000,offset,uncertainty));assert(offset==-51);
 remote=4000000000;memcpy(reply,&remote,4);assert(loginClock(reply,16,1790600000,2000,offset,uncertainty));assert(offset>2000000000LL);
 assert(!loginClock(reply,64,1790600000,2000,offset,uncertainty));
 assert(!loginClock(reply,12,1790600000,2000,offset,uncertainty));
 assert(!loginClock(reply,16,1790600000,180001,offset,uncertainty));
 reply[4]=1;assert(!loginClock(reply,16,1790600000,2000,offset,uncertainty));
 assert(!loginClock(nullptr,16,1790600000,2000,offset,uncertainty));
}
