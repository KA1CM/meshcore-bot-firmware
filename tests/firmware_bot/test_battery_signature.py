import pathlib, subprocess, tempfile, os
root=pathlib.Path(__file__).resolve().parents[2]
source=r'''#include "BatterySignature.h"
#include <cassert>
int main(){
 BatterySignature t;
 assert(!t.due(0));t.start(0,123);
 assert(t.due(0));t.add(0,4100,false);assert(t.count==1);
 assert(!t.due(999));assert(!t.mark(2,1000));
 assert(t.mark(1,120000));t.add(120010,4000,true);
 assert(t.samples[1].elapsed==120010 && t.samples[1].phase==1 && t.samples[1].lookup);
 assert(!t.mark(1,120020));assert(t.mark(2,240000));
 t.add(240010,4110,false);assert(t.restoredAt==240000);
 assert(!t.due(600001));assert(!t.running);assert(t.count==3);
 t.start(0xfffffff0u,0);t.add(0xfffffff0u,4000,false);
 assert(t.due(984));t.add(984,3990,false);assert(t.samples[1].elapsed==1000);
 t.start(0,0);
 for(unsigned i=0;i<=90;++i)t.add(i*1000,4180,false);
 assert(t.detected==1);
 for(unsigned i=91;i<=95;++i)t.add(i*1000,4100,false);
 for(unsigned i=96;i<=130;++i)t.add(i*1000,4180,false);
 assert(t.detected==1); // brief load dip must not confirm loss
 for(unsigned i=131;i<=170;++i)t.add(i*1000,4140,false);
 assert(t.detected==2);
 for(unsigned i=171;i<=210;++i)t.add(i*1000,4180,false);
 assert(t.detected==3);
 t.start(0,0);for(unsigned i=0;i<=600;++i)t.add(i*1000,4000,false);
 assert(t.count==601 && !t.running);t.add(601000,4000,false);assert(t.count==601);
}
'''
with tempfile.TemporaryDirectory() as tmp:
 cpp=pathlib.Path(tmp)/'test.cpp';exe=pathlib.Path(tmp)/'test.exe';cpp.write_text(source)
 subprocess.run([os.environ.get('CXX','g++'),'-std=c++11','-I'+str(root/'vendor/MeshCore/examples/companion_radio'),str(cpp),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('Battery signature timing, markers, wraparound and capacity passed')
