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
 assert(report(w,0).find("Last 24h: 0 responses")!=std::string::npos);
 for(int i=0;i<12;++i)w.accepted(BOT_COMMAND_PING,1);
 for(int i=0;i<18;++i)w.accepted(BOT_COMMAND_TEST,1);
 counters.observed_messages=40;counters.eligible_messages=30;counters.sent_messages=29;counters.send_failures=1;
 w.sample(1,counters,100,50,2);
 auto text=report(w,1);assert(text.find("ping 40%")!=std::string::npos);assert(text.find("test 60%")!=std::string::npos);
 assert(text.find("Last 24h: 30 responses\n")==0);assert(text.find("test 60%")<text.find("ping 40%"));
 assert(text.find("RF ")==std::string::npos&&text.find(" seen ")==std::string::npos);
 assert(report(w,86399999).find("ping 40%")!=std::string::npos);
 w.sample(86400000,counters,100,50,2);text=report(w,86400000);
 assert(text.find("Last 24h: 0 responses")!=std::string::npos);assert(text=="Last 24h: 0 responses\n");
 w.accepted(BOT_COMMAND_PATH,86400001);++counters.eligible_messages;w.sample(86400001,counters,101,50,2);
 assert(report(w,86400001).find("path 100%")!=std::string::npos);
 BotStatsWindow wrap;wrap.sample(0xfffffff0,counters,0,0,0);wrap.accepted(BOT_COMMAND_PING,0xfffffff0);
 assert(report(wrap,32).find("ping 100%")!=std::string::npos);
 assert(report(wrap,86400032).find("Last 24h: 0 responses")!=std::string::npos);
 BotStatsWindow all;for(unsigned i=1;i<=36;++i)all.accepted((BotCommandId)i,0);
 BotVoltageList::Snapshot s;all.snapshot(0,s);assert(s.count<=40);
 size_t next=0;unsigned part=1;while(next<s.count){char body[121];auto old=next;assert(BotVoltageList::page(s,next,part++,body,sizeof(body)));assert(next>old&&strlen(body)<=120);}
 BotStatsWindow admin;
 const BotCommandId ids[]={BOT_COMMAND_ADVERT,BOT_COMMAND_CHECK,BOT_COMMAND_SYNC,BOT_COMMAND_ADD,BOT_COMMAND_REMOVE,BOT_COMMAND_ENABLE,BOT_COMMAND_DISABLE,BOT_COMMAND_NOTES,BOT_COMMAND_PASSWORD};
 for(auto id:ids)admin.accepted(id,0);
 for(int i=0;i<9;++i)admin.accepted(BOT_COMMAND_TEST,0);
 auto grouped=report(admin,0);assert(grouped.find("Last 24h: 18 responses\n")==0);
 assert(grouped.find("admin 50%")!=std::string::npos&&grouped.find("test 50%")!=std::string::npos);
 assert(grouped.find("password")==std::string::npos&&grouped.find("notes")==std::string::npos&&grouped.find("advert")==std::string::npos);
 BotStatsWindow restart;assert(report(restart,0).find("Last 24h: 0 responses")!=std::string::npos);
}
"""
with tempfile.TemporaryDirectory() as temp:
 p=Path(temp);(p/'test.cpp').write_text(code,encoding='utf-8');exe=p/'test.exe'
 subprocess.run([os.environ.get('CXX','c++'),'-std=c++11','-Wall','-Wextra','-Werror','-I',str(src),str(p/'test.cpp'),str(src/'BotCommandRegistry.cpp'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: rolling expiration, response totals, sorted percentages, combined admin commands, timer wrap, reboot reset and pagination')
