"""Regression: the actual monitor sampling block must not infer USB outages."""
from pathlib import Path
import os, subprocess, tempfile
src=Path(__file__).resolve().parents[2]/'vendor/MeshCore/examples/companion_radio'
source=(src/'RepeaterMonitor.cpp').read_text(encoding='utf-8')
start=source.index('void RepeaterMonitor::loop() {')+len('void RepeaterMonitor::loop() {')
sampling=source[start:source.index('  bool connected = WiFi.status()',start)]
code=r'''
#include <cstdint>
#include <cassert>
uint32_t ticks=0;uint32_t millis(){return ticks;}
bool elapsed(uint32_t now,uint32_t deadline){return (int32_t)(now-deadline)>=0;}
namespace BotPathLookup {bool inProgress(){return false;}}
struct Monitor {
 uint32_t nextBatterySample=0;
 struct Signature {unsigned samples=0;void add(uint32_t,uint16_t,bool){++samples;}}signature;
 Signature* batterySignature=nullptr;
 struct Mesh {unsigned reads=0;uint16_t sampleBatteryMillivolts(){++reads;return 4192;}}mesh;
 void sample();
};
void Monitor::sample(){
'''+sampling+r'''
}
int main(){
 Monitor m;
 for(ticks=0;ticks<3*86400000UL;ticks+=1000)m.sample();
 assert(m.mesh.reads==0); // No continuous ADC polling or voltage-based USB state.
 m.batterySignature=&m.signature;m.sample();assert(m.mesh.reads==1&&m.signature.samples==1);
 m.sample();assert(m.mesh.reads==1);
 ticks+=1000;m.sample();assert(m.mesh.reads==2&&m.signature.samples==2);
 m.batterySignature=nullptr;ticks+=1000;m.sample();assert(m.mesh.reads==2);
}
'''
with tempfile.TemporaryDirectory() as tmp:
    folder=Path(tmp);cpp=folder/'power.cpp';exe=folder/'power.exe';cpp.write_text(code)
    subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('PASS: no voltage-inferred USB alerts, no idle ADC polling, and CSV sampling preserved')
