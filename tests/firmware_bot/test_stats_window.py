from pathlib import Path
import os,subprocess,tempfile
r=Path(__file__).resolve().parents[2];src=r/'vendor/MeshCore/examples/companion_radio'
code=r"""
#include "BotStatsWindow.h"
#include <cassert>
#include <string>
std::string report(BotStatsWindow& w,uint32_t now){BotVoltageList::Snapshot s;w.snapshot(now,s);std::string out;for(size_t i=0;i<s.count;++i){out+=s.lines[i];out+='\n';}return out;}
int main(){
 static_assert(sizeof(BotStatsWindow)<17000,"Bounded RAM budget");
 BotStatsWindow w;BotStats counters{};
 assert(report(w,0).find("No accepted commands")!=std::string::npos);
 for(int i=0;i<12;++i)w.accepted(BOT_COMMAND_PING,1);
 for(int i=0;i<18;++i)w.accepted(BOT_COMMAND_TEST,1);
 counters.observed_messages=40;counters.eligible_messages=30;counters.sent_messages=29;counters.send_failures=1;
 w.sample(1,counters,100,50,2);
 auto text=report(w,1);assert(text.find("ping 12 | 40%")!=std::string::npos);assert(text.find("test 18 | 60%")!=std::string::npos);
 assert(text.find("40 seen | 30 ok")!=std::string::npos);assert(text.find("29 sent | 1 fail")!=std::string::npos);
 assert(text.find("RF 100 rx | 50 tx | 2 err")!=std::string::npos);
 assert(report(w,86399999).find("ping 12")!=std::string::npos);
 w.sample(86400000,counters,100,50,2);text=report(w,86400000);
 assert(text.find("No accepted commands")!=std::string::npos);assert(text.find("0 seen | 0 ok")!=std::string::npos);
 w.accepted(BOT_COMMAND_PATH,86400001);++counters.eligible_messages;w.sample(86400001,counters,101,50,2);
 assert(report(w,86400001).find("path 1 | 100%")!=std::string::npos);
 BotStatsWindow wrap;wrap.sample(0xfffffff0,counters,0,0,0);wrap.accepted(BOT_COMMAND_PING,0xfffffff0);
 assert(report(wrap,32).find("ping 1")!=std::string::npos);
 assert(report(wrap,86400032).find("No accepted commands")!=std::string::npos);
 BotStatsWindow all;for(unsigned i=1;i<=34;++i)all.accepted((BotCommandId)i,0);
 BotVoltageList::Snapshot s;all.snapshot(0,s);assert(s.count<=40);
 size_t next=0;unsigned part=1;while(next<s.count){char body[121];auto old=next;assert(BotVoltageList::page(s,next,part++,body,sizeof(body)));assert(next>old&&strlen(body)<=120);}
 BotStatsWindow restart;assert(report(restart,0).find("No accepted commands")!=std::string::npos);
}
"""
with tempfile.TemporaryDirectory() as temp:
 p=Path(temp);(p/'test.cpp').write_text(code,encoding='utf-8');exe=p/'test.exe'
 subprocess.run([os.environ.get('CXX','c++'),'-std=c++11','-Wall','-Wextra','-Werror','-I',str(src),str(p/'test.cpp'),str(src/'BotCommandRegistry.cpp'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: rolling expiration, command shares, send/RF totals, timer wrap, reboot reset and pagination')
