@echo off
cd /d "%~dp0flight_project"

echo Checking dependencies...
pip show waitress >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Installing waitress...
    pip install waitress
)

echo Installing requirements...
pip install -r requirements.txt -q

echo Starting Flight Search Server...
start "" http://localhost:5000
python -c "from run import app; app.run(host='0.0.0.0', port=5000)"
