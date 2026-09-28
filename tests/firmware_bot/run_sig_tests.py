"""Run the focused snr command and formatter regression tests (set CXX to your compiler)."""
import os
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[2]
src = root / 'vendor' / 'MeshCore' / 'examples' / 'companion_radio'
out = root / 'out' / 'tests' / 'firmware_bot'
out.mkdir(parents=True, exist_ok=True)
binary = out / ('test_sig.exe' if os.name == 'nt' else 'test_sig')
subprocess.run([os.environ.get('CXX', 'c++'), '-std=c++17', '-I', str(src),
                str(Path(__file__).with_name('test_sig.cpp')),
                str(src / 'BotCommands.cpp'), str(src / 'BotCommandRegistry.cpp'),
                '-o', str(binary)], check=True)
subprocess.run([str(binary)], check=True)
print('snr command, help and response tests passed')
