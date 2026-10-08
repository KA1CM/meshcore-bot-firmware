#include "BotCommands.h"
#include "BotLookupBody.h"
#include "BotPathLookupResult.h"
#include "FirmwareBot.h"
int32_t FirmwareBot::easternUtcOffsetSeconds(uint32_t) { return -14400; }
#include <cassert>
#include <cstring>
#include <cstdio>

int main() {
  { BotPath::Route direct; direct.width=2; char reply[128];
    const auto result=BotPath::format(direct,"Celluoid Desktop",reply,sizeof(reply));
    assert(result.code==BOT_COMMAND_RESULT_OK);
    assert(!strcmp(reply,"@[Celluoid Desktop]\nDirect"));
  }

  BotPath::Route r; r.width=2; r.count=6;
  for(unsigned i=0;i<6;++i) {r.bytes[2*i]=0xa1; r.bytes[2*i+1]=i; snprintf(r.names[i],33,"Repeater %u",i+1);}
  char out[145];
  auto result=BotPath::format(r,"alice",out,sizeof(out));
  assert(result.code==BOT_COMMAND_RESULT_OK);
  assert(!strcmp(out,"@[alice]\nRepeater 1\nRepeater 2\nRepeater 3\nRepeater 4\nRepeater 5\nRepeater 6"));
  { BotPath::Route missing;missing.width=2;missing.count=6;
    for(int i=0;i<6;++i)missing.bytes[2*i+1]=i;
    char reply[80];auto result=BotPath::format(missing,nullptr,reply,sizeof(reply));
    assert(result.code==BOT_COMMAND_RESULT_OK&&!strcmp(reply,"0000.\n0001.\n0002.\n0003.\n0004.\n0005"));
    char exact[sizeof(reply)];const size_t capacity=strlen(reply)+1;
    assert(BotPath::format(missing,nullptr,exact,capacity).code==BOT_COMMAND_RESULT_OK);
    assert(strlen(exact)<capacity);
  }
  // Unknown/colliding hops retain the complete hash, never an arbitrary name.
  r.names[1][0]=0; r.ambiguous[2]=true;
  BotPath::format(r,"alice",out,sizeof(out));
  assert(strstr(out,"\na101.\na102\n"));
  for(unsigned i=0;i<6;++i) {snprintf(r.names[i],33,"Long repeater name number %u",i+1); r.ambiguous[i]=false;}
  result=BotPath::format(r,"alice",out,130);
  assert(result.code==BOT_COMMAND_RESULT_OK && result.text_len<130);
  assert(strstr(out,"\na10") && !strchr(out,'~'));
  assert(!strcmp(out+strlen(out)-strlen(r.names[5]),r.names[5]));
  r=BotPath::Route{}; r.width=2; r.count=32;
  for(unsigned i=0;i<32;++i) snprintf(r.names[i],33,"Repeater %u",i+1);
  result=BotPath::format(r,"alice",out,100);
  assert(result.code==BOT_COMMAND_RESULT_OK);
  assert(!strncmp(out,"@[alice]\nRepeater 1\nRepeater 2\nRepeater 3\n",strlen("@[alice]\nRepeater 1\nRepeater 2\nRepeater 3\n")));
  assert(strstr(out,"\n...\n") && !strstr(out,"hops omitted"));
  assert(strstr(out,"Repeater 5\n...")!=nullptr);
  assert(!strcmp(out+strlen(out)-strlen(r.names[31]),r.names[31]));
  // Exhaustive packet budgets and route lengths; protected hops cannot disappear.
  for(unsigned width=2;width<=4;++width) for(unsigned count=1;count<=64/width;++count) {
    r=BotPath::Route{}; r.width=width; r.count=count;
    for(unsigned i=0;i<count;++i) snprintf(r.names[i],33,"Repeater with a long name %u",i);
    for(unsigned capacity=100;capacity<=145;++capacity) {
      memset(out,'!',sizeof(out));
      result=BotPath::format(r,"abcdefghijklmnopqrstuvwxyz12345",out,capacity);
      assert(result.code==BOT_COMMAND_RESULT_OK);
      assert(result.text_len==strlen(out) && result.text_len<capacity);
      const char* line=strchr(out,'\n')+1;
      for(unsigned i=0;i<5 && i<count;++i) {
        const char* end=strchr(line,'\n');
        const size_t len=end ? (size_t)(end-line) : strlen(line);
        const size_t original=strlen(r.names[i]);
        assert(len>=4);
        if(len==original) assert(!strncmp(line,r.names[i],len));
        else { char expected[9];BotPath::hash(r,i,expected);assert(len==strlen(expected));assert(!strncmp(line,expected,len)); }
        assert(!memchr(line,'~',len));
        line=end ? end+1 : line+len;
      }
      const char* finalLine=strrchr(out,'\n');finalLine=finalLine?finalLine+1:out;
      char finalHash[9];BotPath::hash(r,count-1,finalHash);
      assert(!strcmp(finalLine,r.names[count-1])||!strcmp(finalLine,finalHash));
      if(capacity<sizeof(out)) assert(out[capacity]=='!');
    }
  }
  r=BotPath::Route{}; r.width=2;
  BotPath::format(r,"alice",out,sizeof(out)); assert(!strcmp(out,"@[alice]\nDirect"));
  r.width=1; r.count=2;
  result=BotPath::format(r,"alice",out,sizeof(out));
  assert(result.code==BOT_COMMAND_RESULT_OK && !strcmp(out,"@[alice] 1-byte paths are not supported."));
  result=BotPath::format(r,nullptr,out,sizeof(out));
  assert(result.code==BOT_COMMAND_RESULT_OK && !strcmp(out,"1-byte paths are not supported."));
  char tiny[10]; assert(BotPath::format(r,"alice",tiny,sizeof(tiny)).code==BOT_COMMAND_RESULT_NO_SPACE);
  r.count=0; BotPath::format(r,"alice",out,sizeof(out)); assert(!strcmp(out,"@[alice]\nDirect"));
  r.width=5; assert(BotPath::format(r,"alice",out,sizeof(out)).code==BOT_COMMAND_RESULT_NO_SPACE);
  char name[33]; BotPath::shortName("Hill Top\nFake hop",name); assert(!strcmp(name,"Hill Top"));
  BotPath::shortName("Repeater 1 [CT]",name); assert(!strcmp(name,"Repeater 1 [CT]"));
  BotPath::shortName("*Hilltop-Solar",name); assert(!strcmp(name,"*Hilltop-Solar"));
  BotPath::shortName("\xe2\x98\x80\xef\xb8\x8f Hilltop [CT]",name);
  assert(!strcmp(name,"\xe2\x98\x80\xef\xb8\x8f Hilltop [CT]"));
  BotPath::shortName("ABCDEFGHIJKLMNOPQRSTUVWXYZ",name); assert(!strcmp(name,"ABCDEFGHIJKLMNOPQRST"));
  BotPath::shortName("\xf0\x9f\x93\xa1" "ABCDEFGHIJKLMNOPQRSTUVWXY",name);
  assert(!strcmp(name,"\xf0\x9f\x93\xa1" "ABCDEFGHIJKLMNOPQRS"));
  BotPath::shortName("\nHilltop",name); assert(!name[0]);
  BotPath::shortName("\xf0\x9f",name); assert(!name[0]);
  BotPath::shortName("",name); assert(!name[0]);
  BotPath::shortName("[CT]/Hill-1 Repeater [FN31]",name); assert(!strcmp(name,"[CT]/Hill-1"));
  BotPath::shortName("Hilltop-Solar West-Side",name); assert(!strcmp(name,"Hilltop-Solar"));
  BotPath::shortName("  *Hill/Top* Ridge",name); assert(!strcmp(name,"*Hill/Top* Ridge"));
  BotPath::shortName("Hill West - FN31jf extra",name); assert(!strcmp(name,"Hill West"));
  BotPath::shortName("Hill West - FN32ab",name); assert(!strcmp(name,"Hill West - FN32ab"));
  BotPath::shortName("Hill West - fn31jf",name); assert(!strcmp(name,"Hill West"));
  BotPath::shortName("- FN31jf",name); assert(!name[0]);
  BotPath::shortName("Fn31jf Chestnut Hill",name); assert(!strcmp(name,"Chestnut Hill"));
  BotPath::shortName("Hill fn31AB Solar",name); assert(!strcmp(name,"Hill Solar"));
  BotPath::shortName("Hill FN31xyz fn31 Solar",name); assert(!strcmp(name,"Hill Solar"));
  BotPath::shortName("Hill xfn31 FN32ab",name); assert(!strcmp(name,"Hill xfn31 FN32ab"));
  BotPath::shortName("fn31",name); assert(!name[0]);
  BotPath::shortName("f",name); assert(!strcmp(name,"f"));
  BotPath::shortName("North Stamford Solar Repeater",name); assert(!strcmp(name,"North Stamford"));
  BotPath::shortName("1234567890 1234567890 more",name); assert(!strcmp(name,"1234567890"));
  BotPath::shortName("1234567890 1234567890",name); assert(!strcmp(name,"1234567890"));
  BotPath::shortName("123456789 1234567890",name); assert(!strcmp(name,"123456789 1234567890"));
  BotPath::shortName("123456789 1234567890 extra",name); assert(!strcmp(name,"123456789"));
  BotPath::shortName("1234567890 12345678 more",name); assert(!strcmp(name,"1234567890 12345678"));
  BotPath::shortName("123456789 1234567890 - FN31ab",name); assert(!strcmp(name,"123456789 1234567890"));
  BotPath::shortName("123456789 1234567890   ",name); assert(!strcmp(name,"123456789 1234567890"));
  BotPath::shortName("ABCDEFGHIJKLMNOPQRSTUV extra",name); assert(!name[0]);


  char bounded[35]; memset(bounded,'!',sizeof(bounded));
  BotPath::shortName("\xf0\x9f\x93\xa1\xf0\x9f\x93\xa1\xf0\x9f\x93\xa1\xf0\x9f\x93\xa1"
                     "\xf0\x9f\x93\xa1\xf0\x9f\x93\xa1\xf0\x9f\x93\xa1\xf0\x9f\x93\xa1\xf0\x9f\x93\xa1",bounded);
  assert(strlen(bounded)==32 && bounded[33]=='!');
  // User-supplied 3-byte paths, including explicit separators.
  BotCommand command{}; command.id=BOT_COMMAND_PATH;
  BotCommandContext context{}; context.path_hash_size=3;
  strcpy(command.args,"b431d2,17fdbb"); command.args_len=strlen(command.args);
  assert(BotCommands::pathRoute(command,context,r) && r.width==3 && r.count==2);
  result=BotCommands::executeCommand(command,context,out,sizeof(out));
  assert(!strcmp(out,"b431d2.\n17fdbb."));
  strcpy(command.args,"b431d217fdbb"); command.args_len=strlen(command.args);
  assert(BotCommands::pathRoute(command,context,r) && r.count==2);
  strcpy(command.args,"b431,17fd"); command.args_len=strlen(command.args);
  assert(!BotCommands::pathRoute(command,context,r));
  command.args_len=0; context.path_len=1; context.path_hash_count=30;
  assert(!BotCommands::pathRoute(command,context,r));
  // Reproduce the live analyzer's HTTP 200 response without Content-Length.
  using BotPathLookup::Body;
  assert(Body::accepts(200,-1));
  assert(Body::accepts(200,32768));
  assert(!Body::accepts(200,32769) && !Body::accepts(200,0) && !Body::accepts(500,-1));
  const char* json=R"({"resolved":{"b431":{"confidence":"unique_prefix","candidates":[{"name":"Amston Lake","pubkey":"b431d2c02e1f5484003622e2d4caf398e3e398208d72481daba900ea77ce6ed6"}],"conflicts":[]}}})";
  Body body;
  const size_t total=strlen(json);
  // Feed fragments, as HTTPClient does after transfer framing is decoded.
  assert(body.append((const uint8_t*)json,17)==17);
  assert(body.append((const uint8_t*)json+17,total-17)==total-17);
  assert(body.complete(-1,(int)total) && body.complete((int)total,(int)total));
  assert(!body.complete((int)total+1,(int)total) && !body.complete(-1,-1));
  JsonDocument live;
  assert(!deserializeJson(live,body.data(),body.size()));
  bool liveAmbiguous=false;
  assert(BotPathLookup::readEntry(live["resolved"]["b431"],"b431",name,liveAmbiguous));
  assert(!strcmp(name,"Amston Lake") && !liveAmbiguous);
  Body tooLarge;
  uint8_t block[1024]{};
  for(unsigned i=0;i<32;++i) assert(tooLarge.append(block,sizeof(block))==sizeof(block));
  assert(tooLarge.complete(-1,32768));
  assert(tooLarge.append(block,1)==0 && !tooLarge.complete(-1,32768));
  JsonDocument doc;
  auto entry=doc.to<JsonObject>();
  entry["confidence"]="unique_prefix";
  auto candidates=entry["candidates"].to<JsonArray>();
  auto candidate=candidates.add<JsonObject>();
  candidate["pubkey"]="b431d2c02e1f5484003622e2d4caf398e3e398208d72481daba900ea77ce6ed6";
  candidate["name"]="Amston Lake";
  entry["conflicts"].to<JsonArray>();
  bool ambiguous=false;
  assert(BotPathLookup::readEntry(entry,"b431",name,ambiguous));
  assert(!strcmp(name,"Amston Lake") && !ambiguous);
  BotPathLookup::readEntry(entry,"b4",name,ambiguous);
  assert(!strcmp(name,"Amston Lake") && !ambiguous);
  BotPathLookup::readEntry(entry,"b431d2",name,ambiguous);
  assert(!strcmp(name,"Amston Lake"));
  BotPathLookup::readEntry(entry,"b432",name,ambiguous); assert(!name[0]);
  entry["confidence"]="best_candidate";
  BotPathLookup::readEntry(entry,"b431",name,ambiguous); assert(!name[0]);
  entry["confidence"]="unique_prefix";
  candidates.add<JsonObject>()["name"]="Collision";
  BotPathLookup::readEntry(entry,"b431",name,ambiguous); assert(!name[0] && ambiguous);
  BotPathLookup::readEntry(entry,"b4",name,ambiguous); assert(!name[0] && ambiguous);
  candidates.remove(1);
  entry["conflicts"].as<JsonArray>().add("conflict");
  BotPathLookup::readEntry(entry,"b431",name,ambiguous); assert(!name[0] && ambiguous);
  entry["conflicts"].as<JsonArray>().clear();
  candidate["pubkey"]="b431";
  BotPathLookup::readEntry(entry,"b431",name,ambiguous); assert(!name[0]);
  doc.clear();
  assert(!BotPathLookup::readEntry(doc.as<JsonObjectConst>(),"b431",name,ambiguous));
  puts("Path formatting, packet budgets, 3-byte parsing, and resolver collision/malformed-result tests passed");
}
