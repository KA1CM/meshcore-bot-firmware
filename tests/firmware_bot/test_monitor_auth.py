from pathlib import Path
import os, subprocess, tempfile
root=Path(__file__).resolve().parents[2]
src=root/'vendor/MeshCore/examples/companion_radio'
code=(src/'RepeaterMonitor.cpp').read_text()
method=code[code.index('bool RepeaterMonitor::authorized('):code.index('\nvoid RepeaterMonitor::routes()')]
# Each mutating route must authorize before reading data or taking any action.
for route in ['/api/list','/api/check','/api/check-one','/api/password','/api/sync-time']:
 marker='server.on("'+route+'", HTTP_POST, [this]() {'
 assert code.split(marker)[1].lstrip().startswith('if (!authorized(true)) return;')
assert 'doc["canManage"] = requestIsAdmin;' in code
harness=r'''
#include <cassert>
#include <string>
#define BOT_MONITOR_PASSWORD "test-admin-password"
#define DIGEST_AUTH 1
struct MockServer {
 std::string user, password, csrf="1"; int status=0;
 bool authenticate(const char* u,const char* p) { return user==u && password==p; }
 void requestAuthentication(int,const char*) { status=401; }
 void sendHeader(const char*,const char*) {}
 std::string header(const char*) { return csrf; }
 void send(int s,const char*,const char*) { status=s; }
};
struct RepeaterMonitor {
 MockServer server; bool requestIsAdmin=false;
 bool authorized(bool mutation=false);
};
'''+method+r'''
int main() {
 RepeaterMonitor m;
 m.server.user="admin"; m.server.password=BOT_MONITOR_PASSWORD;
 assert(m.authorized() && m.requestIsAdmin); assert(m.authorized(true));
 m.server.csrf=""; assert(!m.authorized(true) && m.server.status==403);
 m.server.csrf="1";
 m.server.user="gu3st";m.server.password="test-guest-password";
#ifdef BOT_MONITOR_GUEST_PASSWORD
 assert(m.authorized() && !m.requestIsAdmin);
 assert(!m.authorized(true) && m.server.status==403);
#else
 assert(!m.authorized() && !m.requestIsAdmin && m.server.status==401);
#endif
 m.server.password="wrong";assert(!m.authorized() && m.server.status==401);
 m.server.user="guest";m.server.password="test-guest-password";
 assert(!m.authorized() && m.server.status==401);
 m.server.user="";m.server.password="";
 assert(!m.authorized(true) && m.server.status==401);
}
'''
with tempfile.TemporaryDirectory() as temp:
 path=Path(temp); cpp=path/'auth.cpp';cpp.write_text(harness)
 for enabled in [False,True]:
  binary=path/'auth.exe'
  flags=['-DBOT_MONITOR_GUEST_PASSWORD="test-guest-password"'] if enabled else []
  subprocess.run([os.environ.get('CXX','c++'),'-std=c++17',*flags,str(cpp),'-o',str(binary)],check=True)
  subprocess.run([str(binary)],check=True)
print('PASS: admin, guest, invalid credentials, guest-disabled builds, CSRF and mutation route guards')
