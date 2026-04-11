@echo off
echo ========================================
echo   NSSM Windows Service Installer
echo ========================================
echo.

set "serviceName=FlightSearchServer"
set "batPath=%~dp0start.bat"

if not exist "nssm.exe" (
    echo Downloading NSSM...
    powershell -Command "Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile 'nssm.zip'"
    powershell -Command "Expand-Archive -Path 'nssm.zip' -DestinationPath '.' -Force"
    copy /y nssm-2.24\win64\nssm.exe . >nul 2>&1
    rmdir /s /q nssm-2.24 >nul 2>&1
    del nssm.zip >nul 2>&1
)

echo Installing service: %serviceName%...
nssm.exe install "%serviceName%" "%batPath%"
nssm.exe set "%serviceName%" AppDirectory "%~dp0flight_project"
nssm.exe set "%serviceName%" DisplayName "Flight Search Server"
nssm.exe set "%serviceName%" Description "Flight search Flask server"

echo.
echo Starting service...
net start "%serviceName%"
echo.
echo Service installed successfully!
echo To uninstall: nssm.exe remove "%serviceName%"
pause