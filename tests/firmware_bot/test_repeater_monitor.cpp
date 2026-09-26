#include "RepeaterMonitorCore.h"
#include <cassert>
#include <cstdio>
using namespace MonitorCore;
static uint32_t utc(int y, unsigned m, unsigned d, int h=0, int minute=0) {
  return civilDay(y,m,d)*86400UL+h*3600+minute*60;
}
int main() {
  assert(civilDay(1970,1,1)==0);
  assert(civilDay(2024,3,1)-civilDay(2024,2,28)==2);
  assert(civilDay(2026,3,1)-civilDay(2026,2,28)==1);
  // Local calendar dates around both US DST transitions and midnight.
  assert(easternDay(utc(2026,3,8,4,59))==(uint32_t)civilDay(2026,3,7));
  assert(easternDay(utc(2026,3,8,5))==(uint32_t)civilDay(2026,3,8));
  assert(easternDay(utc(2026,3,9,4))==(uint32_t)civilDay(2026,3,9));
  assert(easternDay(utc(2026,11,1,4))==(uint32_t)civilDay(2026,11,1));
  assert(easternDay(utc(2026,11,2,4,59))==(uint32_t)civilDay(2026,11,1));
  assert(easternDay(utc(2026,11,2,5))==(uint32_t)civilDay(2026,11,2));
  assert(easternDay(utc(2027,1,1,2))==(uint32_t)civilDay(2026,12,31));
  uint32_t summer=sunrise(civilDay(2026,6,21)),winter=sunrise(civilDay(2026,12,21));
  assert(summer>utc(2026,6,21,9,10)&&summer<utc(2026,6,21,9,30));
  assert(winter>utc(2026,12,21,12,5)&&winter<utc(2026,12,21,12,25));
  Entry e;
  uint32_t day=civilDay(2026,9,26),rise=sunrise(day);
  assert(!due(e,0)&&!due(e,rise-1)&&due(e,rise));
  e.scheduledDay=day;
  assert(!due(e,rise+3600)); // reboot/late loop cannot repeat the sweep
  assert(due(e,sunrise(day+1)));
  e.enabled=false; assert(!due(e,sunrise(day+1)));
  // Exactly seven local dates, independent of 23/25 hour DST days.
  for (uint32_t age=0;age<10;++age) assert(retained(day-age,day)==(age<7));
  assert(!retained(day+1,day)&&!retained(0,day));
  for (uint32_t d=day;d<day+14;++d) { auto& r=e.readings[d%7];r.day=d;r.timestamp=sunrise(d);r.result=Ok;r.millivolts=3900; }
  for (const auto& r:e.readings) assert(retained(r.day,day+13));
  uint8_t key[32];char text[65];
  const char* example="BFA8321263F26B4E2927EF734486683C1F85F4A321335415C442F647D57E3139";
  assert(parseKey(example,key));formatKey(key,text);assert(strcmp(text,example)==0);
  assert(!parseKey("xyz",key));
  assert(!parseKey("0000000000000000000000000000000000000000000000000000000000000000",key));
  uint8_t packet[68]={};uint16_t mv=123;
  packet[0]=0x78;packet[1]=0x56;packet[2]=0x34;packet[3]=0x12;packet[4]=0x3c;packet[5]=0x0f;
  assert(voltage(packet,sizeof(packet),0x12345678,mv)&&mv==3900);
  assert(!voltage(packet,sizeof(packet),0x12345679,mv)); // stale/other request
  for (size_t len=0;len<52;++len) assert(!voltage(packet,len,0x12345678,mv));
  // Mesh::onPeerDataRecv receives full decrypted blocks; PATH replies strip
  // the path prefix without stripping encryption padding from the response.
  uint8_t login[32]={};
  for (size_t len=0;len<13;++len) assert(!loginOK(login,len));
  for (size_t padding=0;padding<16;++padding) assert(loginOK(login,13+padding));
  login[4]=1;assert(!loginOK(login,16)); // not LOGIN_OK
  login[4]='O';login[5]='K';
  for (size_t len=0;len<6;++len) assert(!loginOK(login,len));
  for (size_t padding=0;padding<16;++padding) assert(loginOK(login,6+padding));
  login[5]='X';assert(!loginOK(login,16));
  assert(elapsed(3,0xfffffff0)&&!elapsed(0xfffffff0,3)); // millis rollover
  assert(timeout(0)==30000&&timeout(60000)==60000&&timeout(999999)==180000);
  assert(crc32("123456789",9)==0xCBF43926UL);
  assert(crc32("settings",8)!=crc32("Settings",8));
  uint32_t header[] = {0x4D4F4E31, 1, 8, crc32("settings",8)};
  assert(validSnapshot(header,"settings",8));
  assert(!validSnapshot(header,"setting",7)); // interrupted write
  assert(!validSnapshot(header,"Settings",8)); // corruption
  header[0]=0; assert(!validSnapshot(header,"settings",8));
  std::puts("PASS: sunrise, DST, once-daily scheduling, seven-day retention, keys, response validation, timeouts and CRC");
}
