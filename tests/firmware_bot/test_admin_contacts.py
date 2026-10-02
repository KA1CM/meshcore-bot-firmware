from pathlib import Path
import os,subprocess,tempfile
root=Path(__file__).resolve().parents[2];src=root/'vendor/MeshCore/examples/companion_radio'
mock=(Path(__file__).with_name('test_monitor_credentials.py')).read_text().split('mock = r"""')[1].split('"""')[0]
code=(src/'RepeaterMonitor.cpp').read_text(encoding='utf-8')
auth=code[code.index('bool RepeaterMonitor::authorized('):code.index('void RepeaterMonitor::routes()')]
route=code.split('server.on("/api/admin-contact", HTTP_POST, [this]() {',1)[1].split('\n  });',1)[0]
harness=r"""
#include <ArduinoJson.h>
#include "RepeaterMonitorCore.h"
#include "BotAdminContacts.h"
#include <cassert>
#include <string>
using namespace MonitorCore;
#define BOT_MONITOR_PASSWORD "adminpass"
#define BOT_MONITOR_GUEST_PASSWORD "guestpass"
#define DIGEST_AUTH 1
struct Server {
 std::string user="admin",password="adminpass",csrf="1",body;int status=0;
 bool authenticate(const char* u,const char* p){return user==u&&password==p;}
 void requestAuthentication(int,const char*){status=401;}
 void sendHeader(const char*,const char*){}
 std::string header(const char*){return csrf;}
 std::string arg(const char*){return body;}
 void send(int c,const char*,const char*){status=c;}
};
#define ADV_TYPE_CHAT 1
struct Mesh {struct Contact {int type=1;}contact;bool exists=true;Contact* lookupContactByPubKey(const uint8_t*,int){return exists?&contact:nullptr;}};
struct RepeaterMonitor {Mesh mesh;bool sunriseNotificationPending=false;size_t sunriseRecipient=0;int protectedCount=0;void protectListedContacts(){++protectedCount;}Server server;BotAdminContacts adminContacts;bool requestIsAdmin=false;bool authorized(bool mutation=false);void edit();};
"""+auth+'void RepeaterMonitor::edit(){'+route+r"""
}
int main(){
 RepeaterMonitor m;assert(m.adminContacts.begin()&&m.adminContacts.count()==4);
 uint8_t key[32];memcpy(key,m.adminContacts.at(0)->key,32);
 for(size_t i=0;i<4;++i){auto k=m.adminContacts.at(i)->key;assert(m.adminContacts.allows(k,BotAdminContacts::Commands)&&m.adminContacts.allows(k,BotAdminContacts::Notifications));}
 uint8_t unknown[32];memcpy(unknown,key,32);unknown[31]^=1;
 assert(!m.adminContacts.allows(unknown,BotAdminContacts::Commands));assert(!m.adminContacts.set(unknown,true,true));
 char hex[65];formatKey(key,hex);
 m.server.body=std::string("{\"key\":\"")+hex+"\",\"commands\":false,\"notifications\":true}";
 m.server.user="gu3st";m.server.password="guestpass";m.edit();assert(m.server.status==403&&m.adminContacts.allows(key,BotAdminContacts::Commands));
 m.server.user="admin";m.server.password="adminpass";m.server.csrf="";m.edit();assert(m.server.status==403);
 m.server.csrf="1";m.edit();assert(m.server.status==200&&!m.adminContacts.allows(key,BotAdminContacts::Commands)&&m.adminContacts.allows(key,BotAdminContacts::Notifications));
 BotAdminContacts reboot;assert(reboot.begin()&&!reboot.allows(key,BotAdminContacts::Commands));
 assert(reboot.set(key,true,false));assert(reboot.allows(key,BotAdminContacts::Commands)&&!reboot.allows(key,BotAdminContacts::Notifications));
 Preferences::fail=true;assert(!reboot.set(key,false,true));assert(reboot.allows(key,BotAdminContacts::Commands));Preferences::fail=false;
 assert(reboot.set(key,false,false));BotAdminContacts revoked;assert(revoked.begin()&&!revoked.allows(key,BotAdminContacts::Commands)&&!revoked.allows(key,BotAdminContacts::Notifications));
 m.server.body="{}";m.edit();assert(m.server.status==400);
 // Add/remove API enforces admin access, companion existence, and persistence.
 uint8_t extra[32]{};extra[0]=77;char extraHex[65];formatKey(extra,extraHex);
 m.server.body=std::string("{\"action\":\"add\",\"key\":\"")+extraHex+"\",\"commands\":true,\"notifications\":false}";
 m.server.user="gu3st";m.server.password="guestpass";m.edit();assert(m.server.status==403);
 m.server.user="admin";m.server.password="adminpass";m.mesh.exists=false;m.edit();assert(m.server.status==400);
 m.mesh.exists=true;m.edit();assert(m.server.status==200&&m.protectedCount==1&&m.adminContacts.allows(extra,BotAdminContacts::Commands));
 m.edit();assert(m.server.status==400); // no duplicates
 m.server.body=std::string("{\"action\":\"remove\",\"key\":\"")+extraHex+"\"}";
 m.server.user="gu3st";m.server.password="guestpass";m.edit();assert(m.server.status==403);
 m.server.user="admin";m.server.password="adminpass";m.edit();assert(m.server.status==200&&!m.adminContacts.allows(extra,BotAdminContacts::Commands));
 BotAdminContacts removed;assert(removed.begin()&&removed.count()==4&&!removed.allows(extra,BotAdminContacts::Commands));
 // Removing every seed survives reboot without reprovisioning.
 while(removed.count()){uint8_t k[32];memcpy(k,removed.at(0)->key,32);assert(removed.remove(k));}
 BotAdminContacts empty;assert(empty.begin()&&empty.count()==0);
 for(int i=1;i<=16;++i){extra[0]=i;assert(empty.add(extra,true,true));}
 extra[0]=17;assert(!empty.add(extra,true,true));
 Preferences::fail=true;assert(!empty.remove(empty.at(0)->key));assert(empty.count()==16);Preferences::fail=false;
 Preferences::bytes[0]=99;BotAdminContacts corrupt;assert(!corrupt.begin()&&!corrupt.allows(key,BotAdminContacts::Commands)&&corrupt.count()==0);
}
"""
with tempfile.TemporaryDirectory() as folder:
 d=Path(folder);(d/'Preferences.h').write_text(mock);(d/'test.cpp').write_text(harness);exe=d/'test.exe'
 subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror','-I',str(d),'-I',str(src),'-I',str(root/'vendor/MeshCore/.pio/libdeps/heltec_v4_companion_radio_usb/ArduinoJson/src'),str(d/'test.cpp'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: four-key seed, full-key matching, independent permissions, reboot/revocation persistence, failed writes, corrupt storage, guest and CSRF rejection')
