from pathlib import Path
import os,subprocess,tempfile
r=Path(__file__).resolve().parents[2];s=r/'vendor/MeshCore/examples/companion_radio'
code=r'''
#include "BotVoltageList.h"
#include "BotCommands.h"
#include "FirmwareBot.h"
#include "BotPrefs.h"
#include <cassert>
#include <cstring>
#include <string>
int main(){
 BotCommand cmd{};assert(FirmwareBot::parseCommand("list",4,&cmd,true)&&cmd.id==BOT_COMMAND_LIST);
 assert(FirmwareBot::parseCommand("!list",5,&cmd,false)&&cmd.id==BOT_COMMAND_LIST);
 BotCommandContext ctx{};char text[145];cmd.id=BOT_COMMAND_HELP;
 BotCommands::executeCommand(cmd,ctx,text,sizeof(text));assert(strstr(text,"list"));
 strcpy(cmd.args,"list");cmd.args_len=4;BotCommands::executeCommand(cmd,ctx,text,sizeof(text));
 assert(strstr(text,"list: list of all managed repeaters")&&strstr(text,"list low:"));
 MonitorCore::Entry entries[32]{};char names[32][33]{};
 const char* full[]={"Chestnut Hill - FN31jf","FlexSolar","North-Stamford","North-Stamford - FN31ab","!Symbol"};
 for(size_t i=0;i<32;++i){entries[i].enabled=true;entries[i].key[0]=i+1;BotVoltageList::shortName(i<5?full[i]:"LongRepeaterNameWith32CharactersX suffix",entries[i].key,names[i]);entries[i].readings[0].timestamp=2000000000;entries[i].readings[0].result=MonitorCore::Ok;entries[i].readings[0].millivolts=4199;}
 assert(!strcmp(names[0],"Chestnut Hill")&&!strcmp(names[2],"North-Stamford")&&!strcmp(names[4],"!Symbol"));
 char readable[33];BotVoltageList::shortName("North Stamford   - FN31fd",entries[0].key,readable);assert(!strcmp(readable,"North Stamford"));
 BotVoltageList::shortName("Trumbull Mall",entries[0].key,readable);assert(!strcmp(readable,"Trumbull Mall"));
 BotVoltageList::shortName("ABCDEFGHIJKLMNOPQRSTUVWXYZ",entries[0].key,readable);assert(!strcmp(readable,"ABCDEFGHIJKLMNOPQRST"));
 entries[1].readings[1].timestamp=2000000010;entries[1].readings[1].result=MonitorCore::NoResponse;
 BotVoltageList::Snapshot snapshot;BotVoltageList::build(entries,names,32,snapshot);
 assert(!strcmp(snapshot.lines[0],"Chestnut Hill 4.20V")&&!strcmp(snapshot.lines[1],"FlexSolar N/A"));
 assert(strstr(snapshot.lines[2],"North-Stamford[03000000]")&&strstr(snapshot.lines[3],"North-Stamford[04000000]"));
 size_t next=0;unsigned part=1;std::string joined;
 while(next<snapshot.count){size_t old=next;char body[121];assert(BotVoltageList::page(snapshot,next,part++,body,sizeof(body)));assert(next>old&&strlen(body)<=120);size_t written=0;auto result=FirmwareBot::writeResponseForChannel(BOT_CHANNEL_BOT,true,body,strlen(body),text,sizeof(text),&written);assert(result==BOT_WRITE_OK&&written==strlen(body));joined+=body;joined+='\n';}
 char heading[24];snprintf(heading,sizeof(heading),"1/%u\n",part-1);assert(joined.find(heading)==0);
 for(unsigned i=1;i<part;++i){snprintf(heading,sizeof(heading),"%u/%u\n",i,part-1);assert(joined.find(heading)!=std::string::npos);}
 for(size_t i=0;i<32;++i){auto pos=joined.find(snapshot.lines[i]);assert(pos!=std::string::npos&&joined.find(snapshot.lines[i],pos+1)==std::string::npos);}
 // Filtering uses unrounded millivolts, includes missing/failed readings, and preserves order.
 entries[0].readings[0].millivolts=3599;
 entries[2].readings[0].millivolts=3600;
 entries[3].readings[0].millivolts=3500;
 entries[4].readings[0].timestamp=0;
 BotVoltageList::Snapshot low;BotVoltageList::build(entries,names,32,low,nullptr,true);
 assert(low.count==4&&strstr(low.lines[0],"Chestnut Hill")&&strstr(low.lines[1],"FlexSolar N/A")&&strstr(low.lines[2],"North-Stamford[04000000]")&&strstr(low.lines[3],"N/A"));
 // Disabled low-voltage and N/A repeaters are excluded from both commands.
 entries[1].enabled=false;entries[3].enabled=false;
 BotVoltageList::build(entries,names,32,snapshot);assert(snapshot.count==30);
 for(size_t i=0;i<snapshot.count;++i)assert(!strstr(snapshot.lines[i],"FlexSolar")&&!strstr(snapshot.lines[i],"North-Stamford[04000000]"));
 assert(!strcmp(snapshot.lines[1],"North-Stamford 3.60V")); // disabled duplicate needs no suffix
 BotVoltageList::build(entries,names,32,low,nullptr,true);assert(low.count==2);
 size_t order[32];for(size_t i=0;i<32;++i)order[i]=31-i;
 BotVoltageList::build(entries,names,32,low,order,true);assert(low.count==2&&strstr(low.lines[1],"Chestnut Hill"));
 for(auto& e:entries)e.enabled=false;
 BotVoltageList::build(entries,names,32,snapshot);assert(snapshot.count==0);
 BotVoltageList::build(entries,names,32,low,nullptr,true);assert(low.count==0);
 for(auto& e:entries)e.enabled=true;
 for(auto& entry:entries){for(auto& reading:entry.readings)reading={};entry.readings[0].timestamp=2000000000;entry.readings[0].result=MonitorCore::Ok;entry.readings[0].millivolts=3600;}
 BotVoltageList::build(entries,names,32,low,nullptr,true);assert(low.count==0);
 strcpy(cmd.args,"list");cmd.args_len=4;BotCommands::executeCommand(cmd,ctx,text,sizeof(text));
 assert(!strcmp(text,"list: list of all managed repeaters with last saved voltage\nlist low: list of repeaters with voltage below 3.6V or N/A"));
 assert(strlen(text)<=BOT_MAX_GROUP_RESPONSE_LEN);
 strcpy(cmd.args,"list low");cmd.args_len=8;BotCommands::executeCommand(cmd,ctx,text,sizeof(text));assert(!strcmp(text,"list low: list of repeaters with voltage below 3.6V or N/A"));
 BotPrefs p,loaded;BotPrefsCodec::defaults(p);p.enabled=true;BotPrefsCodec::setCommandEnabled(p,BOT_COMMAND_PING,false);BotPrefsCodec::setCommandEnabled(p,BOT_COMMAND_LIST,false);
 uint8_t bytes[BOT_PREFS_SERIALIZED_SIZE];assert(BotPrefsCodec::serialize(p,bytes,sizeof(bytes)));
 assert(BotPrefsCodec::deserialize(bytes,sizeof(bytes),loaded)&&!BotPrefsCodec::commandEnabled(loaded,BOT_COMMAND_LIST));
 bytes[4]=7;bytes[5]=0;assert(BotPrefsCodec::deserialize(bytes,sizeof(bytes),loaded));
 assert(loaded.enabled&&BotPrefsCodec::commandEnabled(loaded,BOT_COMMAND_LIST)&&!BotPrefsCodec::commandEnabled(loaded,BOT_COMMAND_PING));
}
'''
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);(p/'test.cpp').write_text(code,encoding='utf-8');exe=p/'test.exe'
 subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-I',str(s),str(p/'test.cpp'),*[str(s/n) for n in ['BotCommands.cpp','BotCommandRegistry.cpp','FirmwareBot.cpp','BotPrefs.cpp']],'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: list parsing/help, short names, duplicates, failed readings, all 32 entries across bounded pages, and preference migration')
