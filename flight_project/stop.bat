@echo off
echo Stopping Waitress server...
taskkill /F /IM python.exe 2>nul
echo Server stopped
pause
