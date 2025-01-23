@echo off
setlocal

REM Define the path to the JSON manifest file
set "JSON_PATH=C:\\path\\to\\com.yourcompany.open_in_safari.json"

REM Create the registry entry
reg add "HKEY_LOCAL_MACHINE\SOFTWARE\Google\Chrome\NativeMessagingHosts\com.yourcompany.open_in_safari" /ve /t REG_SZ /d "%JSON_PATH%" /f

echo Native messaging host registered successfully.
endlocal
pause