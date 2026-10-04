param([switch]$DryRun)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$pioRoot = Join-Path $env:USERPROFILE '.platformio'
$python = Join-Path $pioRoot 'penv/Scripts/python.exe'
$esptool = Join-Path $pioRoot 'packages/tool-esptoolpy/esptool.py'
$firmware = Join-Path $repoRoot 'vendor/MeshCore/.pio/build/heltec_v4_companion_radio_usb/firmware.bin'
foreach ($file in @($python,$esptool,$firmware)) {
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Missing file: $file" }
}
$info = Get-Item -LiteralPath $firmware
Write-Host "Firmware: $firmware"
Write-Host "Built: $($info.LastWriteTime) | Size: $($info.Length) bytes"
Write-Host "SHA256: $((Get-FileHash -LiteralPath $firmware -Algorithm SHA256).Hash)"
$scan = @"
import json
from serial.tools import list_ports
print(json.dumps([p.device for p in list_ports.comports() if p.vid == 0x303A and p.pid == 0x1001 and (p.serial_number or '').replace(':','').upper() == 'F85B1BBED8C0']))
"@
$rawPorts = & $python -c $scan
if ($LASTEXITCODE -ne 0) { throw 'Could not inspect USB ports.' }
$ports = @($rawPorts | ConvertFrom-Json)
if ($DryRun) {
    Write-Host "Dry run: detected $($ports.Count) matching DFU device(s). Nothing flashed."
    exit 0
}
if ($ports.Count -ne 1) { throw 'Put Fairfield into DFU mode, then run this script again. Expected exactly one matching board.' }
Write-Host "Flashing Fairfield on $($ports[0]). Saved settings and notes are preserved."
& $python $esptool --chip esp32s3 --port $ports[0] --baud 460800 --before no_reset --after no_reset write_flash 0x10000 $firmware
if ($LASTEXITCODE -ne 0) { throw 'Flash failed. Review the output above before retrying.' }
Write-Host 'Flash finished successfully. Press RESET on the board now.' -ForegroundColor Green
