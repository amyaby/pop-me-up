@echo off
setlocal EnableDelayedExpansion
echo.
echo   Installing Reminder Bubble to start automatically with Windows...
echo.

set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SRC=%~dp0app"
set "DST=%USERPROFILE%\popup-reminder\app"

if "%SRC:~0,2%"=="\\" goto :remote
if exist "%SRC%\node_modules\electron\dist\electron.exe" goto :local
echo   ERROR: Electron not installed yet.
echo   From the repo folder, run:  cd app   then   npm install
goto :fail

:remote
rem WSL/UNC source: reuse start_silent.vbs (it syncs then launches)
copy "%~dp0start_silent.vbs" "%STARTUP%\ReminderBubble.vbs" >nul 2>&1
if %ERRORLEVEL% EQU 0 ( goto :ok ) else ( goto :fail )

:local
rem Normal local clone: write a launcher pointing straight at this repo
> "%STARTUP%\ReminderBubble.vbs" (
  echo Set WshShell = CreateObject^("WScript.Shell"^)
  echo WshShell.Run """!SRC!\node_modules\electron\dist\electron.exe"" ""!SRC!"", 0, False
)
if %ERRORLEVEL% EQU 0 ( goto :ok ) else ( goto :fail )

:ok
echo   SUCCESS! Reminder Bubble will now appear every time you log in.
echo   To remove it later, run uninstall-autostart.bat
goto :end

:fail
echo   ERROR: Could not install auto-start.
echo   Try running this file as Administrator.
goto :end

:end
echo.
pause
endlocal