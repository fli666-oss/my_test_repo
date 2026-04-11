@echo off
setlocal EnableDelayedExpansion
echo ========================================
echo   NSSM Windows Service Installer
echo ========================================
echo.

set "serviceName=FlightSearchServer"
set "projectPath=%~dp0flight_project"
set "pythonPath=C:\Users\fengl\AppData\Local\Programs\Python\Python313\python.exe"

if not exist "nssm.exe" (
    echo Downloading NSSM...
    powershell -Command "Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile 'nssm.zip'"
    powershell -Command "Expand-Archive -Path 'nssm.zip' -DestinationPath '.' -Force"
    copy /y nssm-2.24\win64\nssm.exe . >nul 2>&1
    rmdir /s /q nssm-2.24 >nul 2>&1
    del nssm.zip >nul 2>&1
)

echo Installing dependencies...
"%pythonPath%" -m pip install flask flask-sqlalchemy flask-swagger-ui serpapi -q

echo Uninstalling existing service if any...
nssm.exe remove "%serviceName%" confirm >nul 2>&1

echo Installing service: %serviceName%...
nssm.exe install "%serviceName%" "%pythonPath%"
nssm.exe set "%serviceName%" AppDirectory "%projectPath%"
nssm.exe set "%serviceName%" AppParameters "-c \"from run import app; app.run(host='0.0.0.0', port=5000)\""
nssm.exe set "%serviceName%" DisplayName "Flight Search Server"
nssm.exe set "%serviceName%" Description "Flight search Flask server"
nssm.exe set "%serviceName%" AppEnvironmentExtra "PATH=C:\Users\fengl\AppData\Local\Programs\Python\Python313;C:\Users\fengl\AppData\Local\Programs\Python\Python313\Scripts;%PATH%&SERPAPI_API_KEY=3a9aaedb965e62e9bbc50abf516f4bfbf1b84f3c3eb41db3b7b1062336f28d28&USE_SERPAPI=true"

echo.
echo Starting service...
net start "%serviceName%"
echo.
echo Service installed successfully!
echo To uninstall: nssm.exe remove "%serviceName%"
pause