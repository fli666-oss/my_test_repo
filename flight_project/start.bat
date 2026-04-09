@echo off
cd /d "%~dp0flight_project"
echo Starting Flight Search Server...
gunicorn -w 4 -b 0.0.0.0:5000 --daemon "run:app"
echo Server started on http://localhost:5000
timeout /t 2 >nul
