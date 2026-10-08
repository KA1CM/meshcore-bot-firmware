from pathlib import Path
import os,subprocess,tempfile
root=Path(__file__).resolve().parents[2];src=root/'vendor/MeshCore/examples/companion_radio'
code=r'''
#include "BotTopUsers.h"
#include "FirmwareBot.h"
#include "BotCommandRegistry.h"
#include <cassert>
#include <cstring>
int main(){
 static_assert(sizeof(BotTopUsers)<9000,"RAM bound");
 BotTopUsers users;BotMessage a{};strcpy(a.sender_name,"Alice");BotMessage b{};strcpy(b.sender_name,"Bob");
 users.accepted(a,0);users.accepted(b,1);users.accepted(b,2);
 const BotTopUsers::User* top[5];uint32_t counts[5];assert(users.top(2,top,counts)==2&&!strcmp(top[0]->name,"Bob")&&counts[0]==2);
 BotVoltageList::Snapshot snapshot;users.snapshot(2,snapshot);char body[121];
 assert(BotVoltageList::singleMessage(snapshot,body,sizeof(body)));
 assert(!strcmp(body,"Top 5 users in the last 24h\n@[Bob] 2\n@[Alice] 1"));
 BotCommand command{};assert(FirmwareBot::parseCommand("users",5,&command,true)&&command.id==BOT_COMMAND_USER);
 assert(BotCommandRegistry::isDiscoverable(BOT_COMMAND_USER));
 assert(users.top(86400000,top,counts)==0);
 b.sender_key_prefix_len=1;b.sender_key_prefix[0]=1;users.accepted(b,86400001);strcpy(b.sender_name,"Renamed");users.accepted(b,86400002);
 assert(users.top(86400002,top,counts)==2&&counts[0]==1); // A changed displayed name is a new group.
 BotTopUsers combined;BotMessage ka{};strcpy(ka.sender_name,"KA1CM");ka.channel_kind=BOT_CHANNEL_BOT;
 combined.accepted(ka,0);ka.channel_kind=BOT_CHANNEL_DM;ka.sender_key_prefix_len=4;ka.sender_key_prefix[0]=1;
 combined.accepted(ka,1);ka.sender_key_prefix[0]=2;combined.accepted(ka,2);
 assert(combined.top(2,top,counts)==1&&counts[0]==3&&!strcmp(top[0]->name,"KA1CM"));
 combined.snapshot(2,snapshot);assert(BotVoltageList::singleMessage(snapshot,body,sizeof(body)));
 assert(!strcmp(body,"Top 5 users in the last 24h\n@[KA1CM] 3"));
 BotTopUsers many;for(int i=0;i<33;++i){BotMessage m{};snprintf(m.sender_name,sizeof(m.sender_name),"User%02d",i);many.accepted(m,0);}
 assert(many.limited()&&many.top(0,top,counts)==5);assert(!strcmp(top[0]->name,"User00"));
 many.top(86400000,top,counts);assert(!many.limited());many.accepted(a,86400001);assert(many.top(86400001,top,counts)==1);
 const BotTopUsers::User* ten[10];uint32_t tenCounts[10];
 BotTopUsers tenUsers;for(int i=0;i<12;++i){BotMessage m{};snprintf(m.sender_name,sizeof(m.sender_name),"User%02d",i);tenUsers.accepted(m,0);}
 assert(tenUsers.top(0,ten,tenCounts,10)==10&&!strcmp(ten[9]->name,"User09"));
 assert(tenUsers.top(0,top,counts)==5);
 BotTopUsers longNames;for(int i=0;i<5;++i){BotMessage m{};memset(m.sender_name,'a'+i,sizeof(m.sender_name)-1);longNames.accepted(m,0);}
 longNames.snapshot(0,snapshot);assert(BotVoltageList::singleMessage(snapshot,body,sizeof(body)));assert(strlen(body)<=120);
 assert(strstr(body,"@[aaaa")&&strstr(body,"@[bbbb")&&!strstr(body,"@[cccc"));assert(body[strlen(body)-1]=='1');
 BotTopUsers wrap;wrap.accepted(a,0xfffffff0);assert(wrap.top(32,top,counts)==1);assert(wrap.top(86400032,top,counts)==0);
}
'''
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'test.cpp').write_text(code);exe=p/'test.exe'
 subprocess.run([os.environ.get('CXX','c++'),'-std=c++11','-Wall','-Wextra','-Werror','-Wno-unused-function','-I',str(src),str(p/'test.cpp'),str(src/'FirmwareBot.cpp'),str(src/'BotCommandRegistry.cpp'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: user ranking, counts, expiration, display-name grouping across channels and devices, capacity recovery and timer wrap')
