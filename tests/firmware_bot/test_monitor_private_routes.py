from pathlib import Path
import os, subprocess, tempfile, runpy
root=Path(__file__).resolve().parents[2];repo=root/'vendor/MeshCore';src=repo/'examples/companion_radio'
# Reuse the Preferences fake, without invoking the other test suite.
mock_source=(Path(__file__).with_name('test_monitor_credentials.py')).read_text()
mock=mock_source.split('mock = r"""')[1].split('"""')[0]
code=(src/'RepeaterMonitor.cpp').read_text()
auth=code[code.index('bool RepeaterMonitor::authorized('):code.index('\nvoid RepeaterMonitor::routes()')]
def route(name):
 return code.split('  server.on("'+name+'", HTTP_POST, [this]() {',1)[1].split('\n  });',1)[0]
harness=r"""
#include <ArduinoJson.h>
#include "MonitorCredentials.h"
#include <cassert>
#include <string>
using namespace MonitorCore;
using String=std::string;
void strlcpy(char* d,const char* s,size_t n){strncpy(d,s,n-1);d[n-1]=0;}
#define BOT_MONITOR_PASSWORD "test-admin"
#define BOT_MONITOR_GUEST_PASSWORD "test-guest"
#define DIGEST_AUTH 1
#define MSG_SEND_FAILED 0
uint32_t millis(){return 1000;}
uint32_t esp_random(){return 42;}
#define OUT_PATH_UNKNOWN 255
struct ContactInfo { uint8_t out_path_len=2;};
struct Mesh {ContactInfo contact;int logins=0;bool present=true;
 ContactInfo* lookupContactByPubKey(const uint8_t*,int){return present?&contact:nullptr;}
 int sendLogin(const ContactInfo&,const char*,uint32_t& estimate){++logins;estimate=1000;return 1;}
};
struct Server {
 std::string user="admin",password="test-admin",csrf="1",body,reply;int status=0;
 bool authenticate(const char* u,const char* p){return user==u&&password==p;}
 void requestAuthentication(int,const char*){status=401;}
 void sendHeader(const char*,const char*){}
 std::string header(const char*){return csrf;}
 std::string arg(const char*){return body;}
 void send(int code,const char*,const char* text){status=code;reply=text;}
};
struct RepeaterMonitor {
 Server server;Mesh mesh;MonitorCredentials credentials;Entry entries[2]{};size_t count=2;
 bool adminCheckPending=false,adminCheckIsSync=false;char adminCheckReply[128]={},adminCheckName[48]={};
 bool running=false,automatic=false;uint32_t deadline=0;
 bool requestIsAdmin=false,storageOK=true,occupied=false,recent=true;
 bool adminConfirmed[2]{};uint8_t syncResetCount=0,syncCommandAttempts=0;uint8_t syncToken=0,syncLoginAttempt=0;uint32_t syncLoginSentUtc=0,syncLoginSentMillis=0;
 enum SyncPhase {SyncIdle,SyncLogin,SyncReady,SyncResetReady} syncPhase=SyncIdle;
 int syncTarget=-1;uint32_t syncDeadline=0;std::string syncResult;
 bool busy(){return occupied||syncPhase!=SyncIdle;}
 bool syncTimeReady(){return recent;}
 uint32_t now(){return 2000000000;}bool savesOK=true;bool save(){return savesOK;}
 bool startClockSync(int);bool startSyncLogin();void finishClockSync(const char*);void chooseSyncAction(int64_t);
 bool authorized(bool mutation=false);void passwordRoute();void syncRoute();void notesRoute();
};
"""+code[code.index('bool RepeaterMonitor::startClockSync('):code.index('void RepeaterMonitor::pollClockSync()')]+auth+'\nvoid RepeaterMonitor::notesRoute(){'+route('/api/notes')+'\n}\nvoid RepeaterMonitor::passwordRoute(){'+route('/api/password')+'\n}\nvoid RepeaterMonitor::syncRoute(){'+route('/api/sync-time')+r"""
}
int main(){
 RepeaterMonitor m;m.entries[0].key[0]=1;m.entries[1].key[0]=2;
 assert(m.credentials.begin(m.entries,m.count));
 m.server.body=R"({"key":"0100000000000000000000000000000000000000000000000000000000000000","notes":"Node: V4\nAntenna: test"})";
 m.server.user="gu3st";m.server.password="test-guest";m.notesRoute();assert(m.server.status==403);
 m.server.user="admin";m.server.password="test-admin";m.server.csrf="";m.notesRoute();assert(m.server.status==403);
 m.server.csrf="1";m.notesRoute();assert(m.server.status==200);assert(!strcmp(m.entries[0].notes,"Node: V4\nAntenna: test"));
 m.savesOK=false;m.server.body=R"({"key":"0100000000000000000000000000000000000000000000000000000000000000","notes":"changed"})";
 m.notesRoute();assert(m.server.status==507);assert(!strcmp(m.entries[0].notes,"Node: V4\nAntenna: test"));m.savesOK=true;

 m.server.body=R"({"all":true,"password":"private-test"})";
 m.server.user="gu3st";m.server.password="test-guest";
 m.passwordRoute();assert(m.server.status==403);assert(!m.credentials.password(m.entries[0].key)[0]);
 m.syncRoute();assert(m.server.status==403&&m.mesh.logins==0);
 m.server.user="admin";m.server.password="test-admin";m.server.csrf="";
 m.passwordRoute();assert(m.server.status==403);
 m.server.csrf="1";m.passwordRoute();assert(m.server.status==200);
 assert(!strcmp(m.credentials.password(m.entries[0].key),"private-test"));
 assert(!strcmp(m.credentials.password(m.entries[1].key),"private-test"));
 assert(m.server.reply.find("private-test")==std::string::npos);
 m.server.body=R"({"all":true,"password":"bad\u0000suffix"})";
 m.passwordRoute();assert(m.server.status==400);
 m.server.body=R"({"all":true,"password":"1234567890123456"})";
 m.passwordRoute();assert(m.server.status==400);
 char key[65];formatKey(m.entries[0].key,key);
 m.server.body=std::string("{\"key\":\"")+key+"\"}";
 m.recent=false;m.syncRoute();assert(m.server.status==409&&m.mesh.logins==0);
 m.recent=true;m.adminConfirmed[0]=true;m.syncRoute();
 assert(m.server.status==200&&m.mesh.logins==1&&m.syncPhase==RepeaterMonitor::SyncLogin);
 m.syncPhase=RepeaterMonitor::SyncIdle;m.adminConfirmed[0]=false;m.occupied=true;m.syncRoute();assert(m.server.status==409&&m.mesh.logins==1);
 m.occupied=false;m.syncRoute();assert(m.server.status==200&&m.mesh.logins==2);
 m.syncRoute();assert(m.server.status==409&&m.mesh.logins==2);
 m.server.body=R"({"all":true,"password":""})";
 m.passwordRoute();assert(m.server.status==409); // cannot edit credentials during sync
 m.syncPhase=RepeaterMonitor::SyncIdle;m.passwordRoute();assert(m.server.status==200);
 assert(!m.credentials.password(m.entries[0].key)[0]);
 m.server.body=std::string("{\"key\":\"")+key+"\"}";
 m.syncRoute();assert(m.server.status==409&&m.mesh.logins==2);
 m.server.user="gu3st";m.server.password="wrong";m.passwordRoute();assert(m.server.status==401);
}
"""
with tempfile.TemporaryDirectory() as temp:
 p=Path(temp);(p/'Preferences.h').write_text(mock);(p/'test.cpp').write_text(harness);exe=p/'test.exe'
 subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror','-I',str(p),'-I',str(src),'-I',str(repo/'.pio/libdeps/heltec_v4_companion_radio_usb/ArduinoJson/src'),str(p/'test.cpp'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: actual private API handlers deny guest/CSRF, validate passwords, serialize operations and require configured credentials/recent NTP')
