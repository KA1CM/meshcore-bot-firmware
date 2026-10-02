from pathlib import Path
import os,subprocess,tempfile
root=Path(__file__).resolve().parents[2];src=root/'vendor/MeshCore/examples/companion_radio'
code=r'''
#include "RepeaterOrder.h"
#include "BotVoltageList.h"
#include <cassert>
#include <cstring>
struct Contact {int32_t gps_lat=41000000,gps_lon=0;};
struct Mesh {Contact contacts[7];Contact* lookupContactByPubKey(const uint8_t* key,int){return key[0]<7?&contacts[key[0]]:nullptr;}};
int main(){
 MonitorCore::Entry e[8]{};Mesh m;char names[8][33]{};
 for(size_t i=0;i<8;++i){e[i].key[0]=i;snprintf(names[i],33,"Repeater%u",(unsigned)i);e[i].readings[0].timestamp=2000000000;e[i].readings[0].result=MonitorCore::Ok;e[i].readings[0].millivolts=4000+100*i;}
 m.contacts[0]={0,0};m.contacts[1].gps_lon=-73000000;m.contacts[2].gps_lon=-74000000;
 m.contacts[3].gps_lon=-73000000;m.contacts[4].gps_lon=12000000;
 m.contacts[5].gps_lon=181000000;m.contacts[6].gps_lon=0; // Greenwich is valid with nonzero latitude
 size_t order[8];RepeaterOrder::westToEast(e,8,m,order);
 size_t expected[]={2,1,3,6,4,0,5,7};for(size_t i=0;i<8;++i){assert(order[i]==expected[i]);assert(e[i].key[0]==i);}
 BotVoltageList::Snapshot out;BotVoltageList::build(e,names,8,out,order);
 assert(!strcmp(out.lines[0],"Repeater2 4.20V"));assert(!strcmp(out.lines[7],"Repeater7 4.70V"));
 e[7].learnedLatitude=41000000;e[7].learnedLongitude=-76000000;
 RepeaterOrder::westToEast(e,8,m,order);assert(order[0]==7); // cache survives missing live contact
 e[7].learnedLatitude=0;e[7].learnedLongitude=0;
 m.contacts[7-1].gps_lon=-75000000;RepeaterOrder::westToEast(e,8,m,order);assert(order[0]==6);
}
'''
with tempfile.TemporaryDirectory() as temp:
 p=Path(temp);(p/'test.cpp').write_text(code,encoding='utf-8');exe=p/'test.exe'
 subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror','-I',str(src),str(p/'test.cpp'),'-o',str(exe)],check=True);subprocess.run([str(exe)],check=True)
print('PASS: west/east ordering, stable ties, missing/invalid locations last, updated positions and voltage/name association')
