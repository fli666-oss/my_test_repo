@echo off
echo ========================================
echo   Windows Task Scheduler Installer
echo ========================================
echo.

set "serviceName=FlightSearchServer"

echo Uninstalling existing service if any...
sc delete FlightSearchServer >nul 2>&1

echo Creating startup task...
schtasks /delete /tn "%serviceName%" /f >nul 2>&1

echo Creating startup task...
schtasks /create /tn "%serviceName%" /tr "\"%~dp0runner.bat\"" /sc onstart /rl limited /f

echo.
echo Starting task...
schtasks /run /tn "%serviceName%"
echo.
echo Task installed successfully!
echo To uninstall: schtasks /delete /tn "%serviceName%" /f
pause