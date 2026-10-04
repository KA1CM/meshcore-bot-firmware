from pathlib import Path
import os, subprocess, tempfile
root = Path(__file__).resolve().parents[2]
src = root/'vendor/MeshCore/examples/companion_radio'
mock = r"""
#pragma once
#include <vector>
#include <cstring>
class Preferences {
public:
 static std::vector<unsigned char> bytes;
 static bool fail;
 bool begin(const char*, bool) { return true; }
 bool isKey(const char*) { return !bytes.empty(); }
 size_t getBytesLength(const char*) { return bytes.size(); }
 size_t getBytes(const char*, void* p, size_t n) { if(n!=bytes.size())return 0;memcpy(p,bytes.data(),n);return n; }
 size_t putBytes(const char*, const void* p, size_t n) { if(fail)return 0;const auto* b=(const unsigned char*)p;bytes.assign(b,b+n);return n; }
};
std::vector<unsigned char> Preferences::bytes;
bool Preferences::fail=false;
"""
harness = r"""
#include "MonitorCredentials.h"
#include <cassert>
int main() {
 MonitorCore::Entry entries[3]{};
 for(int i=0;i<3;++i)entries[i].key[0]=i+1;
 MonitorCredentials store;
 assert(store.begin(entries,2,"initial-secret"));
 assert(!strcmp(store.password(entries[0].key),"initial-secret"));
 assert(!strcmp(store.password(entries[1].key),"initial-secret"));
 assert(!store.password(entries[2].key)[0]);
 MonitorCredentials reboot;
 assert(reboot.begin(entries,3,"different"));
 assert(!reboot.password(entries[2].key)[0]); // no automatic assignment to newly added repeaters
 assert(reboot.set(entries,3,entries[0].key,"replacement"));
 assert(!strcmp(reboot.password(entries[1].key),"initial-secret"));
 assert(!reboot.set(entries,3,entries[0].key,"sixteen-letters!!"));
 Preferences::fail=true;
 assert(!reboot.set(entries,3,entries[0].key,"failed"));
 assert(!strcmp(reboot.password(entries[0].key),"replacement"));
 Preferences::fail=false;
 assert(reboot.set(entries,3,nullptr,"all-three"));
 assert(!strcmp(reboot.password(entries[2].key),"all-three"));
 assert(reboot.set(entries,3,entries[1].key,""));
 assert(!reboot.password(entries[1].key)[0]);
 MonitorCredentials afterClear;
 assert(afterClear.begin(entries,3,"initial-secret"));
 assert(!afterClear.password(entries[1].key)[0]); // clearing survives reboots and seed
 assert(afterClear.retain(entries+1,2));
 assert(!afterClear.password(entries[0].key)[0]);
 assert(!afterClear.set(entries+1,2,entries[0].key,"not-listed"));
 MonitorCredentials afterRemove;
 assert(afterRemove.begin(entries,3));
 assert(!afterRemove.password(entries[0].key)[0]); // removed then re-added does not recover password
 Preferences::fail=true;
 assert(!afterRemove.retain(entries,1));
 assert(!afterRemove.available());
 assert(!afterRemove.password(entries[2].key)[0]); // fail closed on failed cleanup
 Preferences::fail=false;
 Preferences::bytes[0]=99;
 MonitorCredentials corrupt;
 assert(!corrupt.begin(entries,3,"initial-secret"));
 assert(!corrupt.available() && !corrupt.password(entries[0].key)[0]);
}
"""
with tempfile.TemporaryDirectory() as temp:
 p=Path(temp);(p/'Preferences.h').write_text(mock);(p/'test.cpp').write_text(harness)
 exe=p/'test.exe'
 subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror','-I',str(p),'-I',str(src),str(p/'test.cpp'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: private credential provisioning, key binding, replacement, clear, persistence, failed writes and corrupt storage')
