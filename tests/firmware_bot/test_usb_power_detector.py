from pathlib import Path
import os,subprocess,tempfile
root=Path(__file__).resolve().parents[2];src=root/'vendor/MeshCore/examples/companion_radio'
code=r'''#include "UsbPowerDetector.h"
#include <cassert>
int main(){
 UsbPowerDetector d;unsigned calibrated=0,lost=0,restored=0;
 for(uint32_t ms=0;ms<=90000;ms+=1000){auto e=d.add(ms,4180);calibrated+=e==UsbPowerDetector::Calibrated;}
 assert(calibrated==1 && d.state()==UsbPowerDetector::Connected);
 for(uint32_t ms=91000;ms<=95000;ms+=1000)assert(d.add(ms,4100)!=UsbPowerDetector::PowerLost);
 for(uint32_t ms=96000;ms<=130000;ms+=1000)assert(d.add(ms,4180)!=UsbPowerDetector::PowerLost);
 for(uint32_t ms=131000;ms<=170000;ms+=1000)lost+=d.add(ms,4140)==UsbPowerDetector::PowerLost;
 assert(lost==1 && d.state()==UsbPowerDetector::Lost);
 for(uint32_t ms=171000;ms<=210000;ms+=1000)restored+=d.add(ms,4180)==UsbPowerDetector::PowerRestored;
 assert(restored==1 && d.state()==UsbPowerDetector::Connected);
 for(uint32_t ms=211000;ms<=250000;ms+=1000)lost+=d.add(ms,3980)==UsbPowerDetector::PowerLost;
 assert(lost==2);
 for(uint32_t ms=251000;ms<=290000;ms+=1000)restored+=d.add(ms,4180)==UsbPowerDetector::PowerRestored;
 assert(restored==2);
 // Continuous operation is independent of the 10-minute test recorder.
 for(uint32_t ms=291000;ms<=86400000;ms+=1000)assert(d.add(ms,4180+(ms/1000%3-1)*10)==UsbPowerDetector::None);
 UsbPowerDetector gap;
 for(uint32_t ms=0;ms<=90000;ms+=1000)gap.add(ms,4180);
 for(uint32_t ms=91000;ms<=106000;ms+=1000)assert(gap.add(ms,3980)!=UsbPowerDetector::PowerLost);
 assert(gap.add(130000,3980)==UsbPowerDetector::None);
 for(uint32_t ms=131000;ms<=155000;ms+=1000)assert(gap.add(ms,3980)==UsbPowerDetector::None);
 assert(gap.add(156000,3980)==UsbPowerDetector::PowerLost);
 UsbPowerDetector wrap;
 const uint32_t start=0xfffffff0u;
 for(uint32_t i=0;i<=90;++i)wrap.add(start+i*1000,4180);
 assert(wrap.state()==UsbPowerDetector::Connected);
 unsigned events=0;for(uint32_t i=91;i<=130;++i)events+=wrap.add(start+i*1000,4140)==UsbPowerDetector::PowerLost;
 assert(events==1);
 UsbPowerDetector invalid;
 for(uint32_t i=0;i<=90;++i)invalid.add(i*1000,4180);
 for(uint32_t i=91;i<=150;++i)assert(invalid.add(i*1000,0)==UsbPowerDetector::None);
 assert(invalid.state()==UsbPowerDetector::Connected);
}
'''
with tempfile.TemporaryDirectory() as folder:
 d=Path(folder);(d/'test.cpp').write_text(code);exe=d/'test.exe'
 subprocess.run([os.environ.get('CXX','g++'),'-std=c++11','-I',str(src),str(d/'test.cpp'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS continuous power detection, repeated cycles, brief dips, 24-hour operation, gaps, rollover and invalid readings')
