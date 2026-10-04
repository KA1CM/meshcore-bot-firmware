@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0flash-fairfield.ps1"
if errorlevel 1 echo Flash did not complete successfully.
pause
