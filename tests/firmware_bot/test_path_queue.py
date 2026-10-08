from pathlib import Path
import os,subprocess,tempfile
root=Path(__file__).resolve().parents[2]
s=(root/'vendor/MeshCore/examples/companion_radio/MyMesh.cpp').read_text(encoding='utf-8')
method=s[s.index('void MyMesh::pollBotPath()'):s.index('void MyMesh::scheduleBotLocalAdvert')]
h=(root/'vendor/MeshCore/examples/companion_radio/MyMesh.h').read_text()
a=h.index('  bool hasPendingPathReplies()');getter=h[a:h.index('\n',a)]
code=r'''
#include <cstdint>
#include <cstddef>
#include <cstring>
#include <cassert>
#include <vector>
#define ESP32 1
#define BOT_REPEATER_MONITOR 1
#define BOT_CHANNEL_DM 1
#define BOT_COMMAND_PATH 1
#define BOT_COMMAND_RESULT_OK 0
#define BOT_MAX_RESPONSE_LEN 144
#define PUB_KEY_SIZE 32
uint32_t ticks=0;bool millisHasNowPassed(uint32_t t){return (int32_t)(ticks-t)>0;}uint32_t futureMillis(uint32_t n){return ticks+n;}
struct BotMessage{int channel_kind=0;char sender_name[33]{};char channel_name[33]{};};
struct ContactInfo{};
namespace BotPath{struct Route{int id=0;};struct Result{int code=0;size_t text_len=1;};Result format(Route r,const char*,char* out,size_t){out[0]='0'+r.id;return {};}}
namespace BotPathLookup{bool running=false,complete=false;int id=0,starts=0;bool start(BotPath::Route r,const char*,const char*){assert(!running);running=true;id=r.id;++starts;return true;}bool take(BotPath::Route& r){if(!complete)return false;r.id=id;running=false;complete=false;return true;}}
namespace BotInternetProbe{bool active=false;bool busy(){return active;}}
namespace BotPrefsCodec{bool commandEnabled(int,int){return true;}}
namespace FirmwareBot{size_t maxResponseLenForChannel(int){return 120;}}
bool botFormatResponseForChannel(const BotMessage&,const char* in,size_t n,char* out,size_t,size_t* written){memcpy(out,in,n);*written=n;return true;}
struct MyMesh{
 struct Pending{bool active=false,ready=false,started=false,lookupRunning=false,sent=false;BotPath::Route route;BotMessage message;uint8_t key[32]{},channel=0;uint32_t lookupDeadline=0,expires=180000;}pending_bot_paths[4];
 size_t bot_path_head=0,bot_path_count=0;
 struct Prefs{bool enabled=true;operator int()const{return 0;}}bot_prefs;
 struct {bool active=false;}pending_bot_dm_ack,pending_voltage_list;
 struct {unsigned send_failures=0;}bot_stats;
 std::vector<int> replies;
 void resolveLocalPathNames(BotPath::Route&){}
 ContactInfo* lookupContactByPubKey(const uint8_t*,size_t){static ContactInfo c;return &c;}
 bool sendBotResponse(const BotMessage&,ContactInfo*,uint8_t,const char* t,size_t){replies.push_back(t[0]-'0');return true;}
'''+getter+r'''
 void pollBotPath();
 void enqueue(int id){assert(bot_path_count<4);auto& q=pending_bot_paths[(bot_path_head+bot_path_count++)%4];q=Pending{};q.active=true;q.route.id=id;}
};
'''+method+r'''
int main(){MyMesh m;assert(!m.hasPendingPathReplies());m.enqueue(1);assert(m.hasPendingPathReplies());m.enqueue(2);BotInternetProbe::active=true;m.pollBotPath();assert(BotPathLookup::starts==0);BotInternetProbe::active=false;m.pollBotPath();assert(BotPathLookup::starts==1&&m.replies.empty());
 BotPathLookup::complete=true;m.pollBotPath();assert(m.replies==std::vector<int>{1}&&m.bot_path_count==1);
 m.pollBotPath();assert(BotPathLookup::starts==2);ticks=28001;m.pollBotPath();assert(m.replies==std::vector<int>({1,2}));
 m.enqueue(3);m.pollBotPath();assert(BotPathLookup::starts==2); // late worker still owns slot
 BotPathLookup::complete=true;m.pollBotPath();assert(m.bot_path_count==1);m.pollBotPath();assert(BotPathLookup::id==3);
 BotPathLookup::complete=true;m.pending_bot_paths[m.bot_path_head].message.channel_kind=BOT_CHANNEL_DM;m.pending_bot_dm_ack.active=true;
 m.pollBotPath();assert(m.replies.size()==2);m.pending_bot_dm_ack.active=false;m.pollBotPath();assert(m.replies==std::vector<int>({1,2,3}));
 for(int i=0;i<4;++i){m.enqueue(i);}assert(m.bot_path_count==4);
 for(int i=0;i<4;++i){m.pollBotPath();BotPathLookup::complete=true;m.pollBotPath();}assert(!m.bot_path_count&&!m.hasPendingPathReplies());
}
'''
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'test.cpp').write_text(code);exe=p/'test.exe'
 subprocess.run([os.environ.get('CXX','c++'),'-std=c++11','-Wall','-Wextra','-Werror',str(p/'test.cpp'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: FIFO path replies, late lookup isolation, DM acknowledgement wait and queue wrap')
