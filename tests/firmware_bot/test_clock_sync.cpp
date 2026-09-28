#include "MeshCore.h"
#include <cassert>
struct Clock : mesh::RTCClock {
 uint32_t now=0;
 uint32_t getCurrentTime() override{return now;}
 void setCurrentTime(uint32_t t) override{now=t;}
};
int main(){
 Clock c;
 const uint32_t current=1790596800, future=3785634600;
 c.setCurrentTime(future);assert(c.getCurrentTimeUnique()==future);
 // Reproduce: correcting only wall time leaves the send timestamp in the future.
 c.setCurrentTime(current);assert(c.getCurrentTime()==current);assert(c.getCurrentTimeUnique()==future+1);
 c.setCurrentTimeFromSync(current);assert(c.getCurrentTimeUnique()==current);
 assert(c.getCurrentTimeUnique()==current+1);
 c.setCurrentTimeFromSync(current);assert(c.getCurrentTimeUnique()==current+2);
 c.setCurrentTimeFromSync(current+100);assert(c.getCurrentTimeUnique()==current+100);
 c.setCurrentTimeFromSync(current);assert(c.getCurrentTimeUnique()==current);
 Clock boundary;boundary.setCurrentTime(current+60);boundary.getCurrentTimeUnique();
 boundary.setCurrentTimeFromSync(current);assert(boundary.getCurrentTimeUnique()==current+61);
 boundary.setCurrentTimeFromSync(current);assert(boundary.getCurrentTimeUnique()==current);
}
