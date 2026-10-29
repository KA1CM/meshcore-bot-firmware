"""Host tests for received scope validation and the Fairfield command gate."""
from pathlib import Path
import os, subprocess, tempfile
root=Path(__file__).resolve().parents[2]
source=(root/'vendor/MeshCore/examples/companion_radio/MyMesh.cpp').read_text(encoding='utf-8')
helper=source[source.index('static bool botPacketUsesFairfieldScope('):source.index('void MyMesh::observeBotChannelMessage(')]
start=source.index('  if(message.channel_kind==BOT_CHANNEL_FAIRFIELD && !message.fairfield_scope_valid')
gate=source[start:source.index('  BotCommand command;',start)]
assert 'executeBotHelloCommand(message,notice,sizeof(notice))' in gate
code=r'''
#include <cassert>
#include <cstdint>
#include <cstring>
#include <string>
#include "BotScopeNotice.h"
namespace mesh {struct Packet {bool scoped=false;uint16_t transport_codes[2]{};uint16_t expected=0x1234;bool hasTransportCodes()const{return scoped;}};}
struct TransportKey {uint16_t calcTransportCode(const mesh::Packet* p)const{return p->expected;}};
struct TransportKeyStore {void getAutoKeyFor(int,const char* name,TransportKey&){assert(!strcmp(name,"#ct-ffc"));}};
struct Message {int channel_kind=BOT_CHANNEL_FAIRFIELD;bool fairfield_scope_valid=false;char sender_name[32]="Alice";};
struct Command {int id=BOT_COMMAND_PING;};
struct MyMesh {
 BotScopeNotice fairfield_scope_notices;
 struct Clock {uint32_t ticks=0;uint32_t getMillis(){return ticks;}}clock;Clock* _ms=&clock;
 struct Stats {int sent_messages=0,send_failures=0,ignored_messages=0;}bot_stats;
 int executed=0,notices=0;std::string notice;
 struct Result {size_t text_len;};
 Result executeBotHelloCommand(const Message&,char* out,size_t capacity){const char* text="Hello\nmore info on http://tiny.cc/ct-ffc";assert(strlen(text)<capacity);strcpy(out,text);return {strlen(text)};}
 bool sendBotGroupMessage(uint8_t,const char* text,size_t n,bool unscoped){assert(unscoped);assert(n<=127);notice.assign(text,n);++notices;return true;}
 void receive(Message message,Command command,uint8_t channel_idx=1);
};
'''+helper+'\nvoid MyMesh::receive(Message message,Command command,uint8_t channel_idx){\n'+gate+'\n++executed;\n}\n'+r'''
int main(){
 mesh::Packet packet;assert(!botPacketUsesFairfieldScope(nullptr));assert(!botPacketUsesFairfieldScope(&packet));
 packet.scoped=true;packet.transport_codes[1]=packet.expected;assert(!botPacketUsesFairfieldScope(&packet));
 packet.transport_codes[0]=packet.expected;assert(botPacketUsesFairfieldScope(&packet));
 packet.expected++;assert(!botPacketUsesFairfieldScope(&packet));
 MyMesh bot;Message message;Command command;bot.receive(message,command);
 assert(bot.notices==1&&bot.executed==0);
 assert(bot.notice=="Hello\nmore info on http://tiny.cc/ct-ffc");
 command.id=BOT_COMMAND_PATH;bot.clock.ticks=29999;bot.receive(message,command);assert(bot.notices==1&&!bot.executed);
 bot.clock.ticks=30000;bot.receive(message,command);assert(bot.notices==1&&!bot.executed);
 strcpy(message.sender_name,"Bob");bot.receive(message,command);assert(bot.notices==2&&!bot.executed);
 message.fairfield_scope_valid=true;bot.receive(message,command);assert(bot.executed==1&&bot.notices==2);
 message.fairfield_scope_valid=false;message.channel_kind=BOT_CHANNEL_BOT;bot.receive(message,command);assert(bot.executed==2);
 message.channel_kind=BOT_CHANNEL_DM;bot.receive(message,command);assert(bot.executed==3);
 message.channel_kind=BOT_CHANNEL_FAIRFIELD;command.id=BOT_COMMAND_UNKNOWN;
 bot.clock.ticks=60000;bot.receive(message,command);assert(bot.notices==2);
 strcpy(message.sender_name,"Alice");bot.clock.ticks=3599999;bot.receive(message,command);assert(bot.notices==2);
 bot.clock.ticks=3600000;bot.receive(message,command);assert(bot.notices==3);
 strcpy(message.sender_name,"Bob");bot.receive(message,command);assert(bot.notices==3);
 bot.clock.ticks=3630000;bot.receive(message,command);assert(bot.notices==4);
}
'''
with tempfile.TemporaryDirectory() as tmp:
    folder=Path(tmp);cpp=folder/'scope.cpp';exe=folder/'scope.exe';cpp.write_text(code)
    subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-I',str(root/'vendor/MeshCore/examples/companion_radio'),str(cpp),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('PASS: originating scope match, all-message gate, shared hello notice, per-user hourly pacing, and unaffected bot/DM commands')
