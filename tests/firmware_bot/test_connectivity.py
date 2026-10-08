import os,pathlib,subprocess,tempfile
root=pathlib.Path(__file__).resolve().parents[2]
source=r'''#include "BotConnectivity.h"
#include <cassert>
using namespace BotConnectivity;
int main(){
 Monitor m;m.begin(0);assert(!m.setWifi(true,100,0));
 assert(!m.due(299999));assert(m.due(300000));
 assert(!m.result(false,300000,400));assert(!m.due(329999));assert(m.due(330000));
 assert(!m.result(false,330000,430));assert(!m.due(359999));assert(m.due(360000));
 assert(m.result(false,360000,460));assert(m.internet.since==400);
 assert(!m.due(659999));assert(m.due(660000)); // confirmed outage returns to five-minute checks
 assert(!m.result(false,660000,760));assert(!m.due(959999));assert(m.due(960000));
 auto e=m.event(360000,460,InternetLost);assert(e.utc==400 && e.since==400);
 assert(!m.result(true,1200000,1300));assert(m.result(true,1500000,1600));
 e=m.event(1500000,1600,InternetRestored);assert(e.durationMs==1200000);
 assert(!m.result(true,1600000,1700));assert(!m.due(1899999));assert(m.due(1900000));
 assert(m.setWifi(false,2000,2000000));assert(!m.setWifi(false,2100,2100000));
 e=m.event(2000000,2000,WifiLost);assert(e.utc==2000);
 assert(!m.reminder(5599999,WifiReminder));assert(m.reminder(5600000,WifiReminder));
 assert(!m.reminder(6000000,InternetReminder)); // no duplicate internet reminders during Wi-Fi outage
 assert(m.setWifi(true,2200,5700000));assert(m.wifiRestorePending);
 assert(!m.reminder(9999999,InternetReminder));assert(m.result(true,5720000,2300));
 e=m.event(5720000,2300,WifiRestoredOnline);assert(e.durationMs==3700000);
 assert(!m.outage());
 assert(m.setWifi(false,2400,6000000));assert(m.setWifi(true,2500,6100000));
 assert(m.result(false,6120000,2600));assert(m.internet.since==2400);
 e=m.event(6120000,2600,WifiRestoredOffline);assert(e.since==2400 && e.durationMs==100000);
 assert(!m.reminder(9719999,InternetReminder));assert(m.reminder(9720000,InternetReminder));
 assert(!m.result(true,9800000,2900));assert(m.result(true,10100000,3200));
 e=m.event(10100000,3200,InternetRestored);assert(e.durationMs==4100000);
 assert(m.setPower(false,3300,11000000));m.event(11000000,3300,PowerLost);
 assert(!m.reminder(14599999,PowerReminder));assert(m.reminder(14600000,PowerReminder));
 m.event(14700000,3400,InternetLost);assert(m.reminder(18200000,PowerReminder));
 assert(m.setPower(true,3500,18300000));e=m.event(18300000,3500,PowerRestored);assert(e.durationMs==7300000);
 Monitor transient;transient.begin(0);transient.setWifi(true,100,0);
 assert(!transient.result(false,300000,400));assert(transient.nextProbe==330000);
 assert(!transient.result(true,330000,430));assert(transient.failures==0 && transient.nextProbe==630000);
 assert(!transient.result(false,630000,730));assert(transient.firstFailure==730 && transient.nextProbe==660000);
 Monitor retryWrap;retryWrap.begin(0xffff0000u);retryWrap.setWifi(true,100,0xffff0000u);
 retryWrap.result(false,0xfffffff0u,200);assert(!retryWrap.due(0xfffffff0u+29999u));assert(retryWrap.due(0xfffffff0u+30000u));
 Monitor wrap;wrap.begin(0xffff0000u);wrap.setWifi(true,1,0xffff0000u);
 assert(!wrap.due(0xffff0000u+299999u));assert(wrap.due(0xffff0000u+300000u));
 wrap.setPower(false,2,0xffff0000u);wrap.setPower(true,3,0xffff0000u+60000u);
 assert(wrap.event(0xffff0000u+60000u,3,PowerRestored).durationMs==60000);
}

'''
with tempfile.TemporaryDirectory() as d:
 cpp=pathlib.Path(d)/'test.cpp';exe=pathlib.Path(d)/'test.exe';cpp.write_text(source)
 subprocess.run([os.environ.get('CXX','g++'),'-std=c++11','-I'+str(root/'vendor/MeshCore/examples/companion_radio'),str(cpp),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS connectivity schedule, outage confirmation, restoration, reminders, Wi-Fi and wraparound')
