@echo off
echo Stopping Gunicorn...
taskkill /F /IM gunicorn.exe 2>nul
echo Server stopped
pause
