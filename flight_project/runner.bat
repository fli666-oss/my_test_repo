@echo off
cd /d "%~dp0"

set USE_SERPAPI=true

echo Checking dependencies...
pip show serpapi >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Installing serpapi...
    pip install serpapi
)

echo Installing requirements...
pip install -r requirements.txt -q

echo Starting Flight Search Server...
python -c "from run import app; app.run(host='0.0.0.0', port=5000)"