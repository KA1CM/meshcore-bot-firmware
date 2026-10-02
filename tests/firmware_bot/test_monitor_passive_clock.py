from pathlib import Path
import os, subprocess, tempfile
root=Path(__file__).resolve().parents[2];src=root/'vendor/MeshCore/examples/companion_radio'
code=(src/'RepeaterMonitor.cpp').read_text(encoding='utf-8')
method=code[code.index('void RepeaterMonitor::onVerifiedAdvert('):code.index('bool RepeaterMonitor::startClockSync(')]
harness=r'''
#include "RepeaterMonitorCore.h"
#include <cstdlib>
#include <cassert>
using namespace MonitorCore;
struct RepeaterMonitor {
 Entry entries[1];size_t count=1;bool ready=true,storageOK=true,occupied=false,saveOK=true;int saves=0;
 uint32_t utc=2000000000;
 struct AdvertClockCandidate {uint8_t key[32]{};uint32_t remote=0,received=0;};
 AdvertClockCandidate advertClocks[1]{};
 bool syncTimeReady(){return ready;}bool busy(){return occupied;}uint32_t now(){return utc;}
 bool save(){++saves;return saveOK;}
 void onVerifiedAdvert(const uint8_t*,uint32_t,uint8_t);
 void advert(int64_t offset=33,uint8_t hops=0){onVerifiedAdvert(entries[0].key,utc+offset,hops);}
 RepeaterMonitor(){entries[0].key[0]=1;}
};
'''+method+r'''
int main(){
 RepeaterMonitor m;m.advert();assert(!m.saves);m.utc+=3600;m.advert();
 assert(m.saves==1&&m.entries[0].clockOffset==33&&m.entries[0].clockCheckedAt==m.utc);
 assert(!m.entries[0].lastSynced&&!timeSyncDue(m.entries[0],m.utc+86400));
 m.advert();assert(m.saves==1); // duplicate
 m.utc+=60;m.advert();assert(m.saves==1); // rate limit
 m.utc+=3600;m.advert();assert(m.saves==2);
 RepeaterMonitor relayed;relayed.advert(33,1);relayed.utc+=3600;relayed.advert(33,1);assert(!relayed.saves);
 RepeaterMonitor drift;drift.advert(800);drift.utc+=3600;drift.advert(800);
 assert(drift.saves==1&&timeSyncDue(drift.entries[0],drift.utc));
 RepeaterMonitor stale;stale.advert();stale.utc+=3600;stale.advert(-3000);assert(!stale.saves);
 RepeaterMonitor ntp;ntp.ready=false;ntp.advert();ntp.utc+=3600;ntp.advert();assert(!ntp.saves);
 RepeaterMonitor busy;busy.occupied=true;busy.advert();busy.utc+=3600;busy.advert();assert(!busy.saves);
 RepeaterMonitor disabled;disabled.entries[0].enabled=false;disabled.advert();disabled.utc+=3600;disabled.advert();assert(!disabled.saves);
 RepeaterMonitor failure;failure.advert();failure.utc+=3600;failure.saveOK=false;failure.advert();assert(!failure.entries[0].clockCheckedAt);
 RepeaterMonitor key;key.advert();key.utc+=3600;key.entries[0].key[0]=2;key.advert();assert(!key.saves);
 key.utc+=3600;key.advert();assert(key.saves==1);
}
'''
with tempfile.TemporaryDirectory() as temp:
 p=Path(temp);(p/'test.cpp').write_text(harness,encoding='utf-8');exe=p/'test.exe'
 subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror','-I',str(src),str(p/'test.cpp'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS: passive clock progression, duplicates, relay exclusion, NTP/idle gates, persistence failure and scheduling')
