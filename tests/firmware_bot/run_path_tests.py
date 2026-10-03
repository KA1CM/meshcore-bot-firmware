"""Focused path names and packet-size regression tests. Set CXX if needed."""
import os
import subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[2]
src=root/'vendor/MeshCore/examples/companion_radio'
out=root/'out/tests/firmware_bot'
out.mkdir(parents=True,exist_ok=True)
binary=out/('test_path_names.exe' if os.name=='nt' else 'test_path_names')
subprocess.run([os.environ.get('CXX','c++'),'-std=c++17','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-parameter',
    '-I',str(src),'-I',str(root/'vendor/MeshCore/.pio/libdeps/heltec_v4_companion_radio_usb/ArduinoJson/src'),str(Path(__file__).with_name('test_path_names.cpp')),
    str(src/'BotCommands.cpp'),str(src/'BotCommandRegistry.cpp'),'-o',str(binary)],check=True)
subprocess.run([str(binary)],check=True)
