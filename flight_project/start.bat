@echo off
cd /d "%~dp0flight_project"

echo Checking dependencies...
pip show gunicorn >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Installing gunicorn...
    pip install gunicorn
)

echo Installing requirements...
pip install -r requirements.txt -q

echo Starting Flight Search Server...
gunicorn -w 4 -b 0.0.0.0:5000 --daemon "run:app"
echo Server started on http://localhost:5000
timeout /t 2 >nul
